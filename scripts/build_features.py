"""
Step 2: Build model-ready features from cleaned traffic data.
Run from repo root: python scripts/build_features.py

Reads:
  data/processed/cleaned_traffic_hourly.csv
  data/processed/cleaned_weather_hourly.csv   (optional)

Outputs:
  data/processed/features_raw.csv   — one row per (date, time_slot, corridor, direction)
                                       WITHOUT baselines or categories.
                                       train_model.py adds those after the temporal split
                                       so baselines are computed from train data only.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.app.processors.feature_builder import (
    compute_calendar_features,
    hour_to_slot,
    FEATURE_COLUMNS,
    SLOT_HOURS_DURATION,
)

PROCESSED = Path("data/processed")


# ---------------------------------------------------------------------------
# 1. Aggregate hourly data → time slots
# ---------------------------------------------------------------------------

def aggregate_to_slots(df: pd.DataFrame) -> pd.DataFrame:
    """
    From hourly records: sum kfz_h and sv_h across hours within each time slot,
    then average across detector sites for the same (corridor, direction, date, slot).
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["time_slot"] = df["hour"].map(hour_to_slot)

    per_site = (
        df.groupby(["site", "corridor", "direction", "date", "time_slot"], as_index=False)
        .agg(kfz_h_slot=("kfz_h", "sum"), sv_h_slot=("sv_h", "sum"), n_hours=("kfz_h", "count"))
    )

    expected = {1: 6, 2: 4, 3: 4, 4: 4, 5: 4, 6: 2}
    per_site["expected_hours"] = per_site["time_slot"].map(expected)
    per_site = per_site[per_site["n_hours"] >= per_site["expected_hours"] * 0.75]

    corridor_slot = (
        per_site.groupby(["corridor", "direction", "date", "time_slot"], as_index=False)
        .agg(kfz_h_slot=("kfz_h_slot", "mean"), sv_h_slot=("sv_h_slot", "mean"))
    )

    corridor_slot["date"] = pd.to_datetime(corridor_slot["date"])
    corridor_slot["sv_share"] = (
        corridor_slot["sv_h_slot"] / corridor_slot["kfz_h_slot"].replace(0, np.nan)
    ).fillna(0.08)

    return corridor_slot


# ---------------------------------------------------------------------------
# 2. Calendar / holiday features
# ---------------------------------------------------------------------------

def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        cal = compute_calendar_features(row["date"].date())
        rows.append(cal)
    cal_df = pd.DataFrame(rows)
    return pd.concat([df.reset_index(drop=True), cal_df.reset_index(drop=True)], axis=1)


# ---------------------------------------------------------------------------
# 3. Historical baseline computation (called from train_model.py after split)
# ---------------------------------------------------------------------------

def compute_baselines(df: pd.DataFrame) -> dict:
    """
    Compute historical average kfz_h_slot per grouping.
    IMPORTANT: always call this on TRAIN data only to avoid leakage.
    Returns a dict with Python tuple keys (not JSON-serializable — use
    baselines_to_json() / json_to_baselines() for file storage).
    """
    baselines: dict = {}
    df2 = df.copy()
    df2["day_of_week"] = pd.to_datetime(df2["date"]).dt.dayofweek
    df2["month"] = pd.to_datetime(df2["date"]).dt.month

    by_dow = (
        df2.groupby(["corridor", "direction", "day_of_week", "time_slot"])["kfz_h_slot"]
        .mean().to_dict()
    )
    baselines["by_dow_slot"] = by_dow

    by_month = (
        df2.groupby(["corridor", "direction", "month", "time_slot"])["kfz_h_slot"]
        .mean().to_dict()
    )
    baselines["by_month_slot"] = by_month

    sv = df2.groupby(["corridor", "direction"])["sv_share"].mean().to_dict()
    baselines["sv_share"] = sv

    return baselines


def add_baseline_features(df: pd.DataFrame, baselines: dict) -> pd.DataFrame:
    """
    Look up baseline features for each row.
    baselines must have Python tuple keys (as returned by compute_baselines).
    Uses ast.literal_eval-safe key format — never eval().
    """
    by_dow   = baselines["by_dow_slot"]
    by_month = baselines["by_month_slot"]
    sv_share = baselines["sv_share"]

    df = df.copy()
    df["_dow"]   = pd.to_datetime(df["date"]).dt.dayofweek
    df["_month"] = pd.to_datetime(df["date"]).dt.month

    df["hist_kfz_dow_slot"] = df.apply(
        lambda r: by_dow.get(
            (r["corridor"], r["direction"], int(r["_dow"]), int(r["time_slot"])), 0.0
        ), axis=1,
    )
    df["hist_kfz_month_slot"] = df.apply(
        lambda r: by_month.get(
            (r["corridor"], r["direction"], int(r["_month"]), int(r["time_slot"])), 0.0
        ), axis=1,
    )
    df["hist_sv_share"] = df.apply(
        lambda r: sv_share.get((r["corridor"], r["direction"]), 0.08), axis=1,
    )

    clim_air = {1: 1, 2: 2, 3: 6, 4: 11, 5: 15, 6: 19, 7: 21, 8: 20, 9: 16, 10: 11, 11: 5, 12: 2}
    df["clim_air_temp_c"] = df["_month"].map(clim_air)
    df["is_frost_risk_month"] = df["_month"].apply(lambda m: int(m in {1, 2, 11, 12}))

    return df.drop(columns=["_dow", "_month"])


def baselines_to_json(baselines: dict) -> dict:
    """Convert tuple-keyed dicts to string-keyed for JSON serialization."""
    result: dict = {
        "by_dow_slot":   {str(k): v for k, v in baselines["by_dow_slot"].items()},
        "by_month_slot": {str(k): v for k, v in baselines["by_month_slot"].items()},
    }
    if "sv_share" in baselines:
        result["sv_share"] = {str(k): v for k, v in baselines["sv_share"].items()}
    return result


def json_to_baselines(raw: dict) -> dict:
    """Convert string-keyed JSON dicts back to tuple keys. Uses ast.literal_eval — safe."""
    return {
        "by_dow_slot":   {ast.literal_eval(k): v for k, v in raw.get("by_dow_slot", {}).items()},
        "by_month_slot": {ast.literal_eval(k): v for k, v in raw.get("by_month_slot", {}).items()},
        "sv_share":      {ast.literal_eval(k): v for k, v in raw.get("sv_share", {}).items()},
    }


# ---------------------------------------------------------------------------
# 4. Category thresholds (called from train_model.py after split)
# ---------------------------------------------------------------------------

def compute_category_thresholds(df: pd.DataFrame) -> dict:
    """
    Compute ratio-based thresholds from TRAINING DATA ONLY.
    Requires df to already have hist_kfz_month_slot column.
    """
    ratio = (
        df["kfz_h_slot"] / df["hist_kfz_month_slot"].replace(0, np.nan)
    ).dropna().clip(0.05, 10.0)

    return {
        "ratio": [
            float(ratio.quantile(0.50)),
            float(ratio.quantile(0.70)),
            float(ratio.quantile(0.88)),
            float(ratio.quantile(0.97)),
        ]
    }


def assign_category(ratio: float, thresholds: list[float]) -> int:
    if ratio < thresholds[0]:
        return 1
    elif ratio < thresholds[1]:
        return 2
    elif ratio < thresholds[2]:
        return 3
    elif ratio < thresholds[3]:
        return 4
    return 5


# ---------------------------------------------------------------------------
# 5. Merge optional weather features
# ---------------------------------------------------------------------------

def merge_weather(df: pd.DataFrame) -> pd.DataFrame:
    weather_file = PROCESSED / "cleaned_weather_hourly.csv"
    if not weather_file.exists():
        print("[INFO] No weather file found — using climatological defaults.")
        return df

    weather = pd.read_csv(weather_file, parse_dates=["timestamp"])
    weather["date"] = weather["timestamp"].dt.date
    daily_weather = (
        weather.groupby("date")
        .agg(
            air_temp_c_mean=("air_temp_c_mean", "mean"),
            surface_temp_c_min=("surface_temp_c_min", "min"),
        )
        .reset_index()
    )
    daily_weather["date"] = pd.to_datetime(daily_weather["date"])

    df = df.merge(daily_weather, on="date", how="left")

    if "clim_air_temp_c" in df.columns:
        has_air = df["air_temp_c_mean"].notna()
        df.loc[has_air, "clim_air_temp_c"] = df.loc[has_air, "air_temp_c_mean"]
    if "is_frost_risk_month" in df.columns:
        has_frost = df["surface_temp_c_min"].notna()
        df.loc[has_frost, "is_frost_risk_month"] = (df.loc[has_frost, "surface_temp_c_min"] < 2).astype(int)

    return df.drop(columns=["air_temp_c_mean", "surface_temp_c_min"], errors="ignore")


# ---------------------------------------------------------------------------
# Entry point — outputs features_raw.csv WITHOUT baselines or categories.
# Baselines and categories are computed by train_model.py after temporal split.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Step 2: Build raw features (no baselines, no categories)")
    print("=" * 60)

    traffic_file = PROCESSED / "cleaned_traffic_hourly.csv"
    if not traffic_file.exists():
        print(f"[ERROR] {traffic_file} not found. Run clean_data.py first.")
        sys.exit(1)

    print("Loading cleaned traffic data...")
    traffic = pd.read_csv(traffic_file, parse_dates=["timestamp"])
    print(f"  {len(traffic):,} hourly rows, {traffic['site'].nunique()} sites")

    print("\nAggregating to 6 time slots per day...")
    slot_df = aggregate_to_slots(traffic)
    print(f"  {len(slot_df):,} slot-level rows")

    print("\nAdding calendar + holiday features...")
    features_df = add_calendar_features(slot_df)

    print("\nMerging weather features (if available)...")
    features_df = merge_weather(features_df)

    # Binary flags for corridor and direction
    features_df["is_outbound"] = (features_df["direction"] == "outbound").astype(int)
    features_df["is_a93"] = (features_df["corridor"] == "A93S").astype(int)

    features_df = features_df[features_df["corridor"].isin(["A8E", "A93S"])]
    features_df = features_df[features_df["direction"].isin(["outbound", "inbound"])]

    # Columns to keep: raw traffic + calendar + flags (NO baselines, NO categories)
    # train_model.py adds hist_kfz_*, month_sin/cos, dow_sin/cos after the temporal split
    raw_calendar_cols = [
        "month", "day_of_week", "week_of_year", "is_weekend",
        "is_public_holiday_de", "is_public_holiday_bavaria",
        "is_bridge_day", "is_long_weekend",
        "is_school_holiday_bavaria", "is_school_holiday_bw",
        "school_holiday_overlap",
        "days_until_school_holiday", "days_since_school_holiday",
        "is_summer_season", "is_winter_sports_season",
        "is_easter_period", "is_christmas_period",
    ]
    keep_cols = (
        ["date", "time_slot", "corridor", "direction", "kfz_h_slot", "sv_h_slot", "sv_share"]
        + [c for c in raw_calendar_cols if c in features_df.columns]
        + ["is_outbound", "is_a93"]
    )
    features_df = features_df[keep_cols].dropna(subset=["kfz_h_slot"])

    out = PROCESSED / "features_raw.csv"
    features_df.to_csv(out, index=False)
    print(f"\nSaved {len(features_df):,} raw feature rows → {out}")
    print("Baselines and categories will be computed by train_model.py from train data only.")
    print("\nDone. Run python scripts/train_model.py next.")
