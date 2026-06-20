"""
Step 2: Build model-ready features from cleaned traffic data.
Run from repo root: python scripts/build_features.py

Reads:
  data/processed/cleaned_traffic_hourly.csv
  data/processed/cleaned_weather_hourly.csv   (optional)

Outputs:
  data/processed/features.csv                 — one row per (date, time_slot, corridor, direction)
  data/processed/category_thresholds.json     — percentile thresholds used to label categories
  data/processed/baselines.json               — historical averages for inference on future dates
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Allow importing from backend package (run from repo root)
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

    Slot durations vary (slot 1 = 6h, slots 2-5 = 4h, slot 6 = 2h) so we
    sum hours within each slot (not average) to get total vehicles per slot period.
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["time_slot"] = df["hour"].map(hour_to_slot)

    # Sum per (site, date, slot) to get total vehicles in that slot window
    per_site = (
        df.groupby(["site", "corridor", "direction", "date", "time_slot"], as_index=False)
        .agg(kfz_h_slot=("kfz_h", "sum"), sv_h_slot=("sv_h", "sum"), n_hours=("kfz_h", "count"))
    )

    # Keep only complete slots (expected hours: 6, 4, 4, 4, 4, 2)
    expected = {1: 6, 2: 4, 3: 4, 4: 4, 5: 4, 6: 2}
    per_site["expected_hours"] = per_site["time_slot"].map(expected)
    per_site = per_site[per_site["n_hours"] >= per_site["expected_hours"] * 0.75]  # allow 25% gaps

    # Average across detector sites for the same corridor/direction
    # (multiple sites measure different km-points but same vehicles — mean is representative)
    corridor_slot = (
        per_site.groupby(["corridor", "direction", "date", "time_slot"], as_index=False)
        .agg(kfz_h_slot=("kfz_h_slot", "mean"), sv_h_slot=("sv_h_slot", "mean"))
    )

    corridor_slot["date"] = pd.to_datetime(corridor_slot["date"])
    corridor_slot["sv_share"] = (
        corridor_slot["sv_h_slot"] / corridor_slot["kfz_h_slot"].replace(0, np.nan)
    ).fillna(0.08)  # default 8% heavy vehicle share

    return corridor_slot


# ---------------------------------------------------------------------------
# 2. Traffic category labels (percentile-based per corridor/direction/slot)
# ---------------------------------------------------------------------------

def compute_category_thresholds(df: pd.DataFrame) -> dict:
    """
    For each (corridor, direction, time_slot): compute percentile thresholds
    that define the 5 traffic categories.
    """
    thresholds: dict[str, list[float]] = {}
    for (corridor, direction, slot), group in df.groupby(["corridor", "direction", "time_slot"]):
        key = f"{corridor}|{direction}|{slot}"
        vals = group["kfz_h_slot"].dropna()
        if len(vals) < 20:
            # Not enough data — use simple quantiles of all available data
            vals = df["kfz_h_slot"].dropna()
        thresholds[key] = [
            float(vals.quantile(0.40)),  # p40 → green/yellow boundary
            float(vals.quantile(0.60)),  # p60 → yellow/orange boundary
            float(vals.quantile(0.80)),  # p80 → orange/red boundary
            float(vals.quantile(0.95)),  # p95 → red/dark-red boundary
        ]
    return thresholds


def assign_category(kfz: float, thresholds: list[float]) -> int:
    if kfz < thresholds[0]:
        return 1
    elif kfz < thresholds[1]:
        return 2
    elif kfz < thresholds[2]:
        return 3
    elif kfz < thresholds[3]:
        return 4
    return 5


def compute_daily_thresholds(df: pd.DataFrame) -> dict:
    """
    For each (corridor, direction): compute percentile thresholds on the
    DAILY TOTAL volume (sum of all 6 slots). The daily traffic-calendar color
    is derived from these — NOT from the max of per-slot categories, which
    would over-inflate the number of red days.
    """
    daily = (
        df.groupby(["corridor", "direction", "date"], as_index=False)["kfz_h_slot"]
        .sum()
        .rename(columns={"kfz_h_slot": "daily_vol"})
    )
    thresholds: dict[str, list[float]] = {}
    for (corridor, direction), group in daily.groupby(["corridor", "direction"]):
        key = f"{corridor}|{direction}"
        vals = group["daily_vol"].dropna()
        thresholds[key] = [
            float(vals.quantile(0.40)),
            float(vals.quantile(0.60)),
            float(vals.quantile(0.80)),
            float(vals.quantile(0.95)),
        ]
    return thresholds


# ---------------------------------------------------------------------------
# 3. Calendar / holiday features
# ---------------------------------------------------------------------------

def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Append all calendar + holiday features to each row."""
    rows = []
    for _, row in df.iterrows():
        cal = compute_calendar_features(row["date"].date())
        rows.append(cal)
    cal_df = pd.DataFrame(rows)
    return pd.concat([df.reset_index(drop=True), cal_df.reset_index(drop=True)], axis=1)


# ---------------------------------------------------------------------------
# 4. Historical baseline features
# ---------------------------------------------------------------------------

def compute_baselines(df: pd.DataFrame) -> dict:
    """
    Compute historical average kfz_h_slot per grouping.
    These are stored in the model bundle and used for future-date inference.
    """
    baselines: dict = {}

    # (corridor, direction, day_of_week, time_slot) → mean kfz_h_slot
    df2 = df.copy()
    df2["day_of_week"] = pd.to_datetime(df2["date"]).dt.dayofweek
    by_dow = (
        df2.groupby(["corridor", "direction", "day_of_week", "time_slot"])["kfz_h_slot"]
        .mean()
        .to_dict()
    )
    baselines["by_dow_slot"] = {str(k): v for k, v in by_dow.items()}

    # (corridor, direction, month, time_slot) → mean kfz_h_slot
    df2["month"] = pd.to_datetime(df2["date"]).dt.month
    by_month = (
        df2.groupby(["corridor", "direction", "month", "time_slot"])["kfz_h_slot"]
        .mean()
        .to_dict()
    )
    baselines["by_month_slot"] = {str(k): v for k, v in by_month.items()}

    # (corridor, direction) → mean sv_share
    sv = (
        df2.groupby(["corridor", "direction"])["sv_share"]
        .mean()
        .to_dict()
    )
    baselines["sv_share"] = {str(k): v for k, v in sv.items()}

    return baselines


def add_baseline_features(df: pd.DataFrame, baselines: dict) -> pd.DataFrame:
    """Look up baseline features for each row in the training dataframe."""
    by_dow = {eval(k): v for k, v in baselines["by_dow_slot"].items()}
    by_month = {eval(k): v for k, v in baselines["by_month_slot"].items()}
    sv_share = {eval(k): v for k, v in baselines["sv_share"].items()}

    df = df.copy()
    df["day_of_week_int"] = pd.to_datetime(df["date"]).dt.dayofweek

    df["hist_kfz_dow_slot"] = df.apply(
        lambda r: by_dow.get((r["corridor"], r["direction"], int(r["day_of_week"]), int(r["time_slot"])), 0.0),
        axis=1,
    )
    df["hist_kfz_month_slot"] = df.apply(
        lambda r: by_month.get((r["corridor"], r["direction"], int(r["month"]), int(r["time_slot"])), 0.0),
        axis=1,
    )
    df["hist_sv_share"] = df.apply(
        lambda r: sv_share.get((r["corridor"], r["direction"]), 0.08),
        axis=1,
    )

    # Climatological air temp placeholder (no real weather loaded here; use monthly avg if available)
    df["clim_air_temp_c"] = df["month"].map(
        {1: 1, 2: 2, 3: 6, 4: 11, 5: 15, 6: 19, 7: 21, 8: 20, 9: 16, 10: 11, 11: 5, 12: 2}
    )
    df["is_frost_risk_month"] = df["month"].apply(lambda m: int(m in {1, 2, 11, 12}))

    df = df.drop(columns=["day_of_week_int"], errors="ignore")
    return df


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

    # Override climatological defaults with real observations
    df["clim_air_temp_c"] = df["clim_air_temp_c"].astype(float)
    has_air = df["air_temp_c_mean"].notna()
    df.loc[has_air, "clim_air_temp_c"] = df.loc[has_air, "air_temp_c_mean"]
    has_frost = df["surface_temp_c_min"].notna()
    df.loc[has_frost, "is_frost_risk_month"] = (df.loc[has_frost, "surface_temp_c_min"] < 2).astype(int)

    df = df.drop(columns=["air_temp_c_mean", "surface_temp_c_min"], errors="ignore")
    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Step 2: Build features")
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

    print("\nComputing per-slot category thresholds...")
    thresholds = compute_category_thresholds(slot_df)
    with open(PROCESSED / "category_thresholds.json", "w") as f:
        json.dump(thresholds, f, indent=2)
    print(f"  {len(thresholds)} slot threshold groups saved.")

    print("\nComputing daily-total category thresholds...")
    daily_thresholds = compute_daily_thresholds(slot_df)
    with open(PROCESSED / "daily_thresholds.json", "w") as f:
        json.dump(daily_thresholds, f, indent=2)
    print(f"  {len(daily_thresholds)} daily threshold groups saved.")

    def lookup_thresh(row):
        key = f"{row['corridor']}|{row['direction']}|{int(row['time_slot'])}"
        t = thresholds.get(key, [5000, 10000, 20000, 35000])
        return assign_category(row["kfz_h_slot"], t)

    slot_df["traffic_category"] = slot_df.apply(lookup_thresh, axis=1)
    cat_dist = slot_df["traffic_category"].value_counts(normalize=True).sort_index() * 100
    print(f"  Slot category distribution (%):\n{cat_dist.round(1).to_string()}")

    # Daily total + daily category (for reference / honest distribution check)
    daily_tot = (
        slot_df.groupby(["corridor", "direction", "date"], as_index=False)["kfz_h_slot"]
        .sum()
        .rename(columns={"kfz_h_slot": "daily_vol"})
    )

    def lookup_daily(row):
        key = f"{row['corridor']}|{row['direction']}"
        t = daily_thresholds.get(key, [20000, 40000, 60000, 90000])
        return assign_category(row["daily_vol"], t)

    daily_tot["daily_category"] = daily_tot.apply(lookup_daily, axis=1)
    daily_dist = daily_tot["daily_category"].value_counts(normalize=True).sort_index() * 100
    print(f"  Daily category distribution (%):\n{daily_dist.round(1).to_string()}")
    slot_df = slot_df.merge(
        daily_tot[["corridor", "direction", "date", "daily_vol", "daily_category"]],
        on=["corridor", "direction", "date"], how="left",
    )

    print("\nAdding calendar + holiday features...")
    features_df = add_calendar_features(slot_df)

    print("\nComputing historical baselines...")
    baselines = compute_baselines(features_df)
    with open(PROCESSED / "baselines.json", "w") as f:
        json.dump(baselines, f, indent=2)

    features_df = add_baseline_features(features_df, baselines)

    print("\nMerging weather features (if available)...")
    features_df = merge_weather(features_df)

    # Encode categorical corridor/direction as binary flags
    features_df["is_outbound"] = (features_df["direction"] == "outbound").astype(int)
    features_df["is_a93"] = (features_df["corridor"] == "A93S").astype(int)

    # Drop rows with unknown corridor/direction from the A93S unconfirmed files
    features_df = features_df[features_df["corridor"].isin(["A8E", "A93S"])]
    features_df = features_df[features_df["direction"].isin(["outbound", "inbound"])]

    # Final feature set for training
    keep_cols = (
        ["date", "time_slot", "corridor", "direction", "kfz_h_slot", "sv_h_slot",
         "traffic_category", "daily_vol", "daily_category"]
        + FEATURE_COLUMNS
    )
    keep_cols = [c for c in keep_cols if c in features_df.columns]
    features_df = features_df[keep_cols].dropna(subset=["traffic_category"])

    out = PROCESSED / "features.csv"
    features_df.to_csv(out, index=False)
    print(f"\nSaved {len(features_df):,} feature rows → {out}")
    print(f"Feature columns: {FEATURE_COLUMNS}")
    print("\nDone. Run python scripts/train_model.py next.")
