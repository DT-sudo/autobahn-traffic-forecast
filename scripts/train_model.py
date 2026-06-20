"""
Step 3: Train traffic forecasting model and export as .joblib bundle.
Run from repo root: python scripts/train_model.py

Reads:
  data/processed/features.csv
  data/processed/category_thresholds.json   (per-slot thresholds)
  data/processed/daily_thresholds.json      (per-corridor/direction daily thresholds)
  data/processed/baselines.json

Outputs:
  models/prediction_pipeline.joblib

Design
------
A single GradientBoosting REGRESSOR predicts slot volume (kfz_h_slot).
All traffic categories (colours) are then DERIVED from predicted volume via
percentile thresholds:
  * per-slot category  → slot volume    vs per-slot thresholds
  * daily category     → daily total    vs per-corridor/direction thresholds
This keeps the displayed colour perfectly consistent with the displayed
vehicle count, and gives the daily calendar a realistic 40/20/20/15/5 spread
(the old max-of-slots classifier marked ~45% of days red).

See docs/MODEL_CONTRACT.md for the full interface.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.app.processors.feature_builder import FEATURE_COLUMNS, assign_category

PROCESSED = Path("data/processed")
MODELS = Path("models")
MODELS.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
MODEL_PATH = MODELS / "prediction_pipeline.joblib"

REG_PARAMS = dict(
    n_estimators=400,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    random_state=RANDOM_SEED,
)


def build_regressor() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("reg", GradientBoostingRegressor(**REG_PARAMS)),
    ])


def load_features() -> pd.DataFrame:
    features_file = PROCESSED / "features.csv"
    if not features_file.exists():
        print(f"[ERROR] {features_file} not found. Run build_features.py first.")
        sys.exit(1)
    df = pd.read_csv(features_file, parse_dates=["date"])
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        print(f"[ERROR] Missing feature columns: {missing}")
        sys.exit(1)
    print(f"Loaded {len(df):,} rows from {features_file}")
    return df


def load_json(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def derive_categories(volumes, frame, slot_thr, daily_thr):
    """Return (slot_cats, daily_cat_per_day_frame) from predicted slot volumes."""
    frame = frame.copy()
    frame["pred_vol"] = volumes
    slot_cats = frame.apply(
        lambda r: assign_category(
            r["pred_vol"],
            slot_thr.get(f"{r['corridor']}|{r['direction']}|{int(r['time_slot'])}",
                         [5000, 10000, 20000, 35000]),
        ),
        axis=1,
    )
    daily = frame.groupby(["date", "corridor", "direction"], as_index=False)["pred_vol"].sum()
    daily["pred_daily_cat"] = daily.apply(
        lambda r: assign_category(
            r["pred_vol"],
            daily_thr.get(f"{r['corridor']}|{r['direction']}", [20000, 40000, 60000, 90000]),
        ),
        axis=1,
    )
    return slot_cats, daily


def evaluate_temporal(df, slot_thr, daily_thr) -> dict:
    """Honest year-ahead evaluation: train on earliest years, test on the last year."""
    years = sorted(df["date"].dt.year.unique())
    if len(years) < 2:
        print("[INFO] Not enough distinct years for a temporal holdout — skipping.")
        return {}

    test_year = years[-1]
    tr = df[df["date"].dt.year < test_year]
    te = df[df["date"].dt.year == test_year].copy()
    print(f"\nTemporal holdout: train {years[0]}-{test_year-1} ({len(tr):,})  →  test {test_year} ({len(te):,})")

    reg = build_regressor()
    reg.fit(tr[FEATURE_COLUMNS], tr["kfz_h_slot"])
    te_pred = reg.predict(te[FEATURE_COLUMNS])

    mae = mean_absolute_error(te["kfz_h_slot"], te_pred)
    r2 = r2_score(te["kfz_h_slot"], te_pred)

    # Actual categories on the test year (using train-derived thresholds)
    act_slot, act_daily = derive_categories(te["kfz_h_slot"].values, te, slot_thr, daily_thr)
    prd_slot, prd_daily = derive_categories(te_pred, te, slot_thr, daily_thr)

    slot_acc = accuracy_score(act_slot, prd_slot)
    slot_w1 = float(np.mean(np.abs(act_slot.values - prd_slot.values) <= 1))
    merged = act_daily.merge(prd_daily, on=["date", "corridor", "direction"], suffixes=("_act", "_prd"))
    daily_acc = accuracy_score(merged["pred_daily_cat_act"], merged["pred_daily_cat_prd"])
    daily_w1 = float(np.mean(np.abs(merged["pred_daily_cat_act"] - merged["pred_daily_cat_prd"]) <= 1))

    print(f"\n=== Year-ahead holdout metrics (test {test_year}) ===")
    print(f"  Slot volume   : MAE={mae:,.0f} veh   R²={r2:.3f}")
    print(f"  Slot category : acc={slot_acc:.3f}   within-1={slot_w1:.3f}")
    print(f"  Daily category: acc={daily_acc:.3f}   within-1={daily_w1:.3f}")
    print(f"  Predicted daily distribution (%):")
    dist = (prd_daily["pred_daily_cat"].value_counts(normalize=True).sort_index() * 100).round(1)
    print("    " + dist.to_string().replace("\n", "\n    "))

    return {
        "test_year": int(test_year),
        "slot_volume_mae": round(float(mae), 1),
        "slot_volume_r2": round(float(r2), 3),
        "slot_category_accuracy": round(float(slot_acc), 3),
        "slot_category_within_1": round(slot_w1, 3),
        "daily_category_accuracy": round(float(daily_acc), 3),
        "daily_category_within_1": round(daily_w1, 3),
    }


def print_feature_importance(pipeline: Pipeline) -> None:
    try:
        reg = pipeline.named_steps["reg"]
        pairs = sorted(zip(FEATURE_COLUMNS, reg.feature_importances_), key=lambda x: -x[1])
        print("\nTop 10 feature importances (regressor):")
        for name, imp in pairs[:10]:
            print(f"  {name:<35} {imp:.4f}  {'█' * int(imp * 60)}")
    except Exception:
        pass


if __name__ == "__main__":
    print("=" * 60)
    print("Step 3: Train model")
    print("=" * 60)

    df = load_features()
    slot_thr = load_json(PROCESSED / "category_thresholds.json")
    daily_thr = load_json(PROCESSED / "daily_thresholds.json")

    # 1) Honest year-ahead evaluation (does not affect the final model)
    eval_metrics = evaluate_temporal(df, slot_thr, daily_thr)

    # 2) Final model — train the regressor on ALL available data
    print("\nTraining final regressor on all data...")
    regressor = build_regressor()
    regressor.fit(df[FEATURE_COLUMNS], df["kfz_h_slot"])
    print_feature_importance(regressor)

    # 3) Baselines (string keys → tuple keys for fast runtime lookup)
    raw = load_json(PROCESSED / "baselines.json")
    baselines: dict = {}
    if raw:
        baselines["by_dow_slot"]   = {eval(k): v for k, v in raw.get("by_dow_slot", {}).items()}
        baselines["by_month_slot"] = {eval(k): v for k, v in raw.get("by_month_slot", {}).items()}
        baselines["sv_share"]      = {eval(k): v for k, v in raw.get("sv_share", {}).items()}

        df2 = df.copy()
        df2["month"] = df2["date"].dt.month
        if "clim_air_temp_c" in df2.columns:
            clim_air = df2.groupby("month")["clim_air_temp_c"].mean().to_dict()
        else:
            clim_air = {1: 1, 2: 2, 3: 6, 4: 11, 5: 15, 6: 19, 7: 21, 8: 20, 9: 16, 10: 11, 11: 5, 12: 2}
        if "is_frost_risk_month" in df2.columns:
            frost = set(int(m) for m, v in df2.groupby("month")["is_frost_risk_month"].mean().items() if v > 0.3)
        else:
            frost = {1, 2, 11, 12}
        baselines["clim_air_temp"] = {int(k): float(v) for k, v in clim_air.items()}
        baselines["frost_risk_months"] = frost

    # 4) Pack the bundle
    model_bundle = {
        "regressor": regressor,
        "slot_thresholds": slot_thr,
        "daily_thresholds": daily_thr,
        "category_thresholds": slot_thr,   # backward-compat alias
        "baselines": baselines,
        "feature_columns": FEATURE_COLUMNS,
        "training_info": {
            "date_range": f"{df['date'].min().date()} → {df['date'].max().date()}",
            "n_samples": len(df),
            "corridors": df["corridor"].unique().tolist(),
            "version": "2.0.0",
            "approach": "regressor + percentile thresholds (slot & daily)",
            "evaluation": eval_metrics,
        },
    }

    joblib.dump(model_bundle, MODEL_PATH, compress=3)
    size_mb = MODEL_PATH.stat().st_size / 1e6
    print(f"\nModel bundle saved → {MODEL_PATH}  ({size_mb:.1f} MB)")
    print("\nTraining info:")
    for k, v in model_bundle["training_info"].items():
        print(f"  {k}: {v}")
    print("\nDone. Start the backend with: uvicorn backend.app.main:app --reload --port 8000")
