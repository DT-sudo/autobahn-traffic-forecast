from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, field_validator

from app.processors.traffic_analyzer import get_analyzer

PROCESSED_DIR = Path(__file__).parents[3] / "data" / "processed"

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class ForecastRequest(BaseModel):
    corridor: Literal["A8E", "A93S"]
    direction: Literal["outbound", "inbound"]
    date_from: date
    date_to: date

    @field_validator("date_to")
    @classmethod
    def date_to_after_from(cls, v, info):
        if "date_from" in info.data and v < info.data["date_from"]:
            raise ValueError("date_to must be >= date_from")
        if "date_from" in info.data and (v - info.data["date_from"]).days > 366:
            raise ValueError("date range must not exceed 366 days")
        return v


class RecommendationRequest(BaseModel):
    date: date
    corridor: Literal["A8E", "A93S"]
    direction: Literal["outbound", "inbound"]
    user_type: Literal["tourist", "logistics", "local_resident", "tourism_business"] = "tourist"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health():
    analyzer = get_analyzer()
    return {
        "status": "ok",
        "version": "1.0.0",
        "model_loaded": analyzer.is_loaded,
        "corridors": ["A8E", "A93S"],
        "directions": ["outbound", "inbound"],
    }


# ---------------------------------------------------------------------------
# Core forecast
# ---------------------------------------------------------------------------

@router.post("/forecast")
async def get_forecast(request: ForecastRequest):
    """
    Generate slot-level traffic forecast for a date range.
    Returns one entry per day, each with 6 time-slot predictions.
    """
    analyzer = get_analyzer()
    try:
        forecast = analyzer.forecast(
            request.corridor,
            request.direction,
            request.date_from,
            request.date_to,
        )
        return {
            "success": True,
            "corridor": request.corridor,
            "direction": request.direction,
            "date_from": request.date_from.isoformat(),
            "date_to": request.date_to.isoformat(),
            "model_loaded": analyzer.is_loaded,
            "forecast": forecast,
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Full calendar view
# ---------------------------------------------------------------------------

@router.get("/calendar")
async def get_calendar(
    year: int = Query(default=2026, ge=2024, le=2030),
    corridor: Literal["A8E", "A93S"] = Query(default="A8E"),
    direction: Literal["outbound", "inbound"] = Query(default="outbound"),
):
    """
    Full-year traffic calendar: one category per day, grouped by month.
    Optimised for a calendar grid UI (color square per day).
    """
    analyzer = get_analyzer()
    date_from = date(year, 1, 1)
    date_to = date(year, 12, 31)

    try:
        forecast = analyzer.forecast(corridor, direction, date_from, date_to)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Group by month
    calendar: dict[str, list[dict]] = {}
    for day in forecast:
        month_key = day["date"][:7]  # "2026-01"
        calendar.setdefault(month_key, []).append({
            "date": day["date"],
            "day_of_week": day["day_of_week"],
            "category": day["daily_category"],
            "color": day["daily_color"],
            "color_hex": day["daily_color_hex"],
            "estimated_daily_vehicles": day["estimated_daily_vehicles"],
            "pattern_type": day["pattern_type"],
        })

    return {
        "success": True,
        "year": year,
        "corridor": corridor,
        "direction": direction,
        "model_loaded": analyzer.is_loaded,
        "calendar": calendar,
    }


# ---------------------------------------------------------------------------
# Critical peak days
# ---------------------------------------------------------------------------

@router.get("/peak-days")
async def get_peak_days(
    corridor: Literal["A8E", "A93S"] = Query(default="A8E"),
    direction: Literal["outbound", "inbound"] = Query(default="outbound"),
    top_n: int = Query(default=10, ge=1, le=50),
    year: int | None = Query(default=None, ge=2024, le=2030),
):
    """
    Return the top N highest-risk days in the next 12 months (or a given year).
    Used for the 'Critical Peak Days' alert panel in the UI.
    """
    analyzer = get_analyzer()
    try:
        peaks = analyzer.get_peak_days(corridor, direction, top_n=top_n, year=year)
        return {
            "success": True,
            "corridor": corridor,
            "direction": direction,
            "top_n": top_n,
            "model_loaded": analyzer.is_loaded,
            "peak_days": peaks,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# User-type-specific recommendations
# ---------------------------------------------------------------------------

@router.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """
    Return actionable travel advice for a specific date, corridor, and user type.
    Tailors the message for tourist / logistics / local_resident / tourism_business.
    """
    analyzer = get_analyzer()
    try:
        result = analyzer.get_recommendations(
            request.date,
            request.corridor,
            request.direction,
            request.user_type,
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Historical data analysis (for data exploration tab)
# ---------------------------------------------------------------------------

@router.get("/analysis/summary")
async def analysis_summary(
    corridor: Literal["A8E", "A93S"] = Query(default="A8E"),
    direction: Literal["outbound", "inbound"] = Query(default="outbound"),
):
    """
    Quick statistical summary derived from historical data baselines.
    No file I/O at runtime — uses baselines stored in the model bundle.
    """
    analyzer = get_analyzer()
    if not analyzer.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run python scripts/train_model.py first.",
        )

    bundle = analyzer._bundle
    baselines = bundle.get("baselines", {})
    by_dow = baselines.get("by_dow_slot", {})
    by_month = baselines.get("by_month_slot", {})

    dow_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Daily average by day-of-week (sum across all slots)
    daily_by_dow: dict[str, float] = {}
    for dow_i, dow_name in enumerate(dow_names):
        total = sum(
            by_dow.get((corridor, direction, dow_i, slot), 0.0)
            for slot in range(1, 7)
        )
        daily_by_dow[dow_name] = round(total)

    # Monthly average total daily volume
    daily_by_month: dict[str, float] = {}
    for m in range(1, 13):
        total = sum(
            by_month.get((corridor, direction, m, slot), 0.0)
            for slot in range(1, 7)
        )
        daily_by_month[month_names[m]] = round(total)

    return {
        "success": True,
        "corridor": corridor,
        "direction": direction,
        "training_info": bundle.get("training_info", {}),
        "avg_daily_vehicles_by_day_of_week": daily_by_dow,
        "avg_daily_vehicles_by_month": daily_by_month,
        "avg_sv_share": round(
            baselines.get("sv_share", {}).get((corridor, direction), 0.08) * 100, 1
        ),
    }


# ---------------------------------------------------------------------------
# Historical data (real detector measurements 2023-2025)
# ---------------------------------------------------------------------------

@router.get("/historical")
async def get_historical(
    corridor: Literal["A8E", "A93S"] = Query(...),
    direction: Literal["outbound", "inbound"] = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
):
    """
    Return real measured traffic for past dates (2023-01-01 → today).
    Reads pre-processed JSON generated by scripts/process_historical.py.
    Response format mirrors /forecast for drop-in frontend use.
    """
    json_path = PROCESSED_DIR / f"historical_{corridor}_{direction}.json"
    if not json_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Historical data not available. Run scripts/process_historical.py first.",
        )

    all_data: dict[str, dict] = json.loads(json_path.read_text())

    LEVEL_TO_CAT = {"low": 1, "increased": 2, "moderate": 3, "heavy": 4, "extreme": 5}
    COLORS = {
        1: {"label": "low",       "hex": "#AFCCAA"},
        2: {"label": "increased", "hex": "#FADC81"},
        3: {"label": "moderate",  "hex": "#E67E22"},
        4: {"label": "heavy",     "hex": "#D83528"},
        5: {"label": "extreme",   "hex": "#A01919"},
    }
    SLOT_LABELS = ["00:00–06:00", "06:00–10:00", "10:00–14:00",
                   "14:00–18:00", "18:00–22:00", "22:00–24:00"]

    results = []
    cur = date_from
    while cur <= date_to:
        key = cur.strftime("%d.%m.%Y")
        entry = all_data.get(key)
        if entry:
            daily_cat = LEVEL_TO_CAT[entry["daily"]]
            time_slots = [
                {
                    "slot": i + 1,
                    "label": SLOT_LABELS[i],
                    "category": LEVEL_TO_CAT[lvl],
                    "color": COLORS[LEVEL_TO_CAT[lvl]]["label"],
                    "color_hex": COLORS[LEVEL_TO_CAT[lvl]]["hex"],
                    "estimated_vehicles": 0,
                    "confidence": 1.0,
                    "explanation": ["Historical measurement"],
                }
                for i, lvl in enumerate(entry["slots"])
            ]
            results.append({
                "date": cur.isoformat(),
                "day_of_week": cur.strftime("%A"),
                "daily_category": daily_cat,
                "daily_color": COLORS[daily_cat]["label"],
                "daily_color_hex": COLORS[daily_cat]["hex"],
                "estimated_daily_vehicles": 0,
                "pattern_type": "historical",
                "time_slots": time_slots,
            })
        cur += timedelta(days=1)

    return {
        "success": True,
        "corridor": corridor,
        "direction": direction,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "historical": True,
        "forecast": results,
    }
