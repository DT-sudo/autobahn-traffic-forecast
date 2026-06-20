"""
Traffic forecasting inference engine.
Loads the pre-trained model bundle and generates forecasts for any future date range.

Usage (in FastAPI routes):
  from app.processors.traffic_analyzer import TrafficAnalyzer
  analyzer = TrafficAnalyzer()          # loads model once at startup
  result = analyzer.forecast("A8E", "outbound", date(2026,7,1), date(2026,8,31))
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.processors.feature_builder import (
    CATEGORY_META,
    FEATURE_COLUMNS,
    SLOT_LABELS,
    build_feature_row,
    build_explanation,
)

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parents[3] / "models" / "prediction_pipeline.joblib"
MAX_FORECAST_DAYS = 366

VALID_CORRIDORS = {"A8E", "A93S"}
VALID_DIRECTIONS = {"outbound", "inbound"}

PATTERN_MAP = {
    # (is_outbound, dow, is_school_holiday, is_summer) → pattern label
    (1, 5, 1, 1): "holiday_departure_peak",
    (0, 6, 1, 1): "holiday_return_peak",
    (1, 5, 0, 0): "weekend_leisure",
    (0, 6, 0, 0): "weekend_leisure",
    (1, 4, 1, 0): "pre_holiday_departure",  # Friday + school holiday
}


class TrafficAnalyzer:
    """Singleton-style inference class. Instantiate once; call forecast() many times."""

    def __init__(self) -> None:
        self._bundle: dict | None = None
        self._load_model()

    def _load_model(self) -> None:
        if not MODEL_PATH.exists():
            logger.warning(
                "Model file not found at %s. "
                "Run python scripts/train_model.py to generate it. "
                "Forecast will return mock data until the model is available.",
                MODEL_PATH,
            )
            return
        try:
            self._bundle = joblib.load(MODEL_PATH)
            info = self._bundle.get("training_info", {})
            logger.info("Model loaded from %s. Training range: %s", MODEL_PATH, info.get("date_range"))
        except Exception as exc:
            logger.error("Failed to load model: %s", exc)
            self._bundle = None

    @property
    def is_loaded(self) -> bool:
        return self._bundle is not None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def forecast(
        self,
        corridor: str,
        direction: str,
        date_from: date,
        date_to: date,
    ) -> list[dict]:
        """
        Generate slot-level forecast for every date in [date_from, date_to].
        Returns list of daily forecast dicts, each containing a 'time_slots' list.
        """
        _validate(corridor, direction, date_from, date_to)

        days = _date_range(date_from, date_to)
        results: list[dict] = []

        for d in days:
            day_slots = []
            for slot in range(1, 7):
                slot_result = self._predict_slot(d, slot, corridor, direction)
                day_slots.append(slot_result)

            # Day-level summary: use the maximum category across slots (worst bottleneck)
            max_cat = max(s["category"] for s in day_slots)
            daily_vol = sum(s["estimated_vehicles"] for s in day_slots)
            dominant_pattern = _get_dominant_pattern(day_slots)

            results.append({
                "date": d.isoformat(),
                "day_of_week": d.strftime("%A"),
                "daily_category": max_cat,
                "daily_color": CATEGORY_META[max_cat]["label"],
                "daily_color_hex": CATEGORY_META[max_cat]["hex"],
                "estimated_daily_vehicles": int(daily_vol),
                "pattern_type": dominant_pattern,
                "time_slots": day_slots,
            })

        return results

    def get_peak_days(
        self,
        corridor: str,
        direction: str,
        top_n: int = 10,
        year: int | None = None,
    ) -> list[dict]:
        """Return the top_n highest-risk days in the next 12 months (or given year)."""
        if year:
            date_from = date(year, 1, 1)
            date_to = date(year, 12, 31)
        else:
            today = date.today()
            date_from = today
            date_to = today.replace(year=today.year + 1)

        all_days = self.forecast(corridor, direction, date_from, date_to)

        # Score by daily_category then estimated_daily_vehicles
        scored = sorted(
            all_days,
            key=lambda d: (d["daily_category"], d["estimated_daily_vehicles"]),
            reverse=True,
        )
        top = scored[:top_n]

        return [
            {
                "date": d["date"],
                "day_of_week": d["day_of_week"],
                "category": d["daily_category"],
                "color": d["daily_color"],
                "color_hex": d["daily_color_hex"],
                "estimated_vehicles": d["estimated_daily_vehicles"],
                "risk_score": round(d["daily_category"] / 5, 2),
                "explanation": d["time_slots"][0].get("explanation", []),
            }
            for d in top
        ]

    def get_recommendations(
        self,
        d: date,
        corridor: str,
        direction: str,
        user_type: str = "tourist",
    ) -> dict:
        """Generate user-type-specific travel recommendations for a single day."""
        slots = [self._predict_slot(d, s, corridor, direction) for s in range(1, 7)]
        max_cat = max(s["category"] for s in slots)

        avoid = [s["slot"] for s in slots if s["category"] >= 4]
        prefer = [s["slot"] for s in slots if s["category"] <= 2]

        slot_labels = {s["slot"]: s["label"] for s in slots}

        message = _build_user_message(user_type, avoid, prefer, slot_labels, max_cat)

        return {
            "date": d.isoformat(),
            "corridor": corridor,
            "direction": direction,
            "user_type": user_type,
            "traffic_category": max_cat,
            "traffic_color": CATEGORY_META[max_cat]["label"],
            "recommendation": message,
            "avoid_slots": avoid,
            "preferred_slots": prefer,
            "severity": ["", "low", "low", "moderate", "high", "very_high"][max_cat],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _predict_slot(
        self,
        d: date,
        slot: int,
        corridor: str,
        direction: str,
    ) -> dict:
        baselines = self._bundle.get("baselines") if self._bundle else None
        row = build_feature_row(d, slot, corridor, direction, baselines)

        if not self._bundle:
            category, volume = _mock_predict(row)
            confidence = 0.5
        else:
            X = pd.DataFrame([[row[c] for c in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
            category = int(self._bundle["classifier"].predict(X)[0])
            proba = self._bundle["classifier"].predict_proba(X)[0]
            confidence = float(proba.max())

            raw_vol = float(self._bundle["regressor"].predict(X)[0])
            volume = max(0, round(raw_vol))

        explanation = build_explanation(row, category)
        meta = CATEGORY_META[category]

        return {
            "slot": slot,
            "label": SLOT_LABELS[slot],
            "category": category,
            "color": meta["label"],
            "color_hex": meta["hex"],
            "estimated_vehicles": volume,
            "confidence": round(confidence, 2),
            "explanation": explanation,
        }


# ------------------------------------------------------------------
# Module-level singleton (created on first import by FastAPI)
# ------------------------------------------------------------------

_analyzer: TrafficAnalyzer | None = None


def get_analyzer() -> TrafficAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = TrafficAnalyzer()
    return _analyzer


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def _validate(corridor: str, direction: str, date_from: date, date_to: date) -> None:
    if corridor not in VALID_CORRIDORS:
        raise ValueError(f"corridor must be one of {VALID_CORRIDORS}, got '{corridor}'")
    if direction not in VALID_DIRECTIONS:
        raise ValueError(f"direction must be one of {VALID_DIRECTIONS}, got '{direction}'")
    if date_to < date_from:
        raise ValueError("date_to must be >= date_from")
    if (date_to - date_from).days > MAX_FORECAST_DAYS:
        raise ValueError(f"date range exceeds {MAX_FORECAST_DAYS} days")


def _date_range(start: date, end: date) -> list[date]:
    days = (end - start).days + 1
    return [start + timedelta(days=i) for i in range(days)]


def _get_dominant_pattern(slots: list[dict]) -> str:
    """Pick the most descriptive pattern label from the slot explanations."""
    peak_slot = max(slots, key=lambda s: s["category"])
    explanations = peak_slot.get("explanation", [])
    if any("departure" in e.lower() for e in explanations):
        return "holiday_departure_peak"
    if any("return" in e.lower() for e in explanations):
        return "holiday_return_peak"
    cat = peak_slot["category"]
    if cat >= 4:
        return "all_day_high"
    if cat <= 1:
        return "low_demand"
    return "weekend_leisure" if peak_slot["slot"] in (3, 4, 5) else "normal_weekday"


def _mock_predict(row: dict) -> tuple[int, int]:
    """Fallback deterministic prediction when no model is loaded."""
    score = 0
    score += row.get("is_school_holiday_bavaria", 0) * 2
    score += row.get("is_weekend", 0) * 1
    score += row.get("is_summer_season", 0) * 1
    score += row.get("is_outbound", 0) * 0.5
    if row.get("time_slot", 1) in (3, 4):
        score += 0.5
    category = min(5, max(1, int(score) + 1))
    volume = 5000 + score * 4000
    return category, int(volume)


def _build_user_message(
    user_type: str,
    avoid: list[int],
    prefer: list[int],
    slot_labels: dict[int, str],
    max_cat: int,
) -> str:
    avoid_str = ", ".join(slot_labels[s] for s in avoid) if avoid else "none"
    prefer_str = ", ".join(slot_labels[s] for s in prefer) if prefer else "any time"

    msgs = {
        "tourist": (
            f"Avoid traveling during {avoid_str}. "
            f"Better windows: {prefer_str}."
        ) if avoid else "Traffic is expected to be manageable throughout the day.",
        "logistics": (
            f"High delay risk during {avoid_str}. "
            f"Preferred dispatch windows: {prefer_str}."
        ) if avoid else "No major congestion windows expected. Normal scheduling applies.",
        "local_resident": (
            f"Avoid regional trips near the corridor during {avoid_str}. "
            f"Lower-pressure periods: {prefer_str}."
        ) if avoid else "No significant motorway pressure expected to affect local roads.",
        "tourism_business": (
            f"Expect delayed guest arrivals during {avoid_str}. "
            f"Lower-pressure check-in periods: {prefer_str}. Increase staffing accordingly."
        ) if avoid else "Normal arrival patterns expected. Standard staffing levels should suffice.",
    }
    return msgs.get(user_type, msgs["tourist"])
