"""
Step 3: Train traffic forecasting model and export as .joblib bundle.
Run from repo root: python scripts/train_model.py

Reads:
  data/processed/features_raw.csv   — output of build_features.py

Outputs:
  models/prediction_pipeline.joblib
  data/processed/baselines.json         — train-only baselines (reference)
  data/processed/category_thresholds.json

Design decisions:
  - Temporal split: train on years < TEST_YEAR, test on TEST_YEAR.
    This reflects real deployment (predict future, not random past dates).
  - Baselines computed AFTER split, from TRAIN DATA ONLY.
    hist_kfz_month_slot is the dominant feature (>60% importance) — computing
    it from all data (including test) would leak the answer into training.
  - Only a regressor is trained. Categories are assigned via ratio-based
    thresholds computed on train ratios, consistent with inference.
  - No StandardScaler: GradientBoosting is invariant to monotone scaling.
  - Metrics: MAE, RMSE, MAPE, R² on TEST YEAR — honest out-of-sample estimates.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.processors.feature_builder import FEATURE_COLUMNS
from build_features import (
    compute_baselines,
    add_baseline_features,
    baselines_to_json,
    compute_category_thresholds,
    assign_category,
)

PROCESSED = Path("data/processed")
MODELS = Path("models")
MODELS.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
MODEL_PATH = MODELS / "prediction_pipeline.joblib"
TEST_YEAR = 2025  # train on years < TEST_YEAR, evaluate on TEST_YEAR


# ---------------------------------------------------------------------------
# Feature engineering (applied after split to avoid leakage)
# ---------------------------------------------------------------------------

def add_cyclic_features(df: pd.DataFrame) -> pd.DataFrame:
    """Sine/cosine encoding for month and day-of-week (fixes Dec→Jan discontinuity)."""
    df = df.copy()
    month = pd.to_datetime(df["date"]).dt.month
    dow   = pd.to_datetime(df["date"]).dt.dayofweek
    df["month_sin"] = np.sin(2 * np.pi * month / 12)
    df["month_cos"] = np.cos(2 * np.pi * month / 12)
    df["dow_sin"]   = np.sin(2 * np.pi * dow / 7)
    df["dow_cos"]   = np.cos(2 * np.pi * dow / 7)
    return df


# ---------------------------------------------------------------------------
# Temporal split
# ---------------------------------------------------------------------------

def temporal_split(df: pd.DataFrame, test_year: int = TEST_YEAR):
    """
    Split by year: train = all years strictly before test_year, test = test_year.
    This ensures no future data influences training — matching real deployment.
    """
    years = pd.to_datetime(df["date"]).dt.year
    train = df[years < test_year].copy()
    test  = df[years == test_year].copy()

    if len(train) == 0:
        print(f"[ERROR] No training data for years < {test_year}.")
        sys.exit(1)
    if len(test) == 0:
        print(f"[WARN] No data for test year {test_year}. Metrics will not be computed.")

    print(f"  Train: {len(train):,} rows  "
          f"({pd.to_datetime(train['date']).min().date()} → {pd.to_datetime(train['date']).max().date()})")
    print(f"  Test:  {len(test):,} rows   "
          f"({pd.to_datetime(test['date']).min().date()} → {pd.to_datetime(test['date']).max().date()})"
          if len(test) else "  Test:  0 rows")
    return train, test


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_mape(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 10.0) -> float:
    """Mean Absolute Percentage Error. Skips near-zero true values to avoid division issues."""
    mask = y_true > epsilon
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def print_metrics(y_true: np.ndarray, y_pred: np.ndarray, label: str) -> None:
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2   = r2_score(y_true, y_pred)
    mape = compute_mape(y_true, y_pred)
    print(f"\n=== {label} ===")
    print(f"  MAE:  {mae:,.0f} vehicles")
    print(f"  RMSE: {rmse:,.0f} vehicles")
    print(f"  MAPE: {mape:.1f}%")
    print(f"  R²:   {r2:.3f}")
    return {"mae": mae, "rmse": rmse, "mape": mape, "r2": r2}


def print_feature_importance(model: GradientBoostingRegressor) -> None:
    pairs = sorted(zip(FEATURE_COLUMNS, model.feature_importances_), key=lambda x: -x[1])
    print("\nTop 10 feature importances (regressor):")
    for name, imp in pairs[:10]:
        bar = "█" * int(imp * 100)
        print(f"  {name:<35} {imp:.4f}  {bar}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Step 3: Train model")
    print(f"  Strategy: temporal split — train < {TEST_YEAR}, test = {TEST_YEAR}")
    print(f"  Features:  {len(FEATURE_COLUMNS)} (cyclic + calendar + train-only baselines)")
    print("=" * 60)

    # 1. Load raw features (no baselines, no categories yet)
    raw_file = PROCESSED / "features_raw.csv"
    if not raw_file.exists():
        print(f"[ERROR] {raw_file} not found. Run build_features.py first.")
        sys.exit(1)

    df = pd.read_csv(raw_file, parse_dates=["date"])
    df = df[df["corridor"].isin(["A8E", "A93S"])]
    df = df[df["direction"].isin(["outbound", "inbound"])]
    df = df.dropna(subset=["kfz_h_slot"])
    print(f"\nLoaded {len(df):,} rows from {raw_file}")

    # 2. Temporal split — BEFORE any data-derived computation
    print("\n--- Temporal split ---")
    train_df, test_df = temporal_split(df, TEST_YEAR)

    # 3. Compute baselines from TRAIN ONLY — prevents leakage of dominant features
    print("\n--- Baselines from TRAIN data only ---")
    baselines = compute_baselines(train_df)

    # Add climatological temperature (hardcoded — no leakage)
    clim_air = {1: 1, 2: 2, 3: 6, 4: 11, 5: 15, 6: 19, 7: 21, 8: 20, 9: 16, 10: 11, 11: 5, 12: 2}
    baselines["clim_air_temp"]     = clim_air
    baselines["frost_risk_months"] = {1, 2, 11, 12}

    # Save train-only baselines for reference (safe: ast.literal_eval, not eval)
    with open(PROCESSED / "baselines.json", "w") as f:
        json.dump(baselines_to_json(baselines), f, indent=2)
    print(f"  Saved → {PROCESSED / 'baselines.json'}")

    # 4. Add baseline features — test set uses train baselines (correct: no future data)
    print("--- Adding baseline lookup features ---")
    train_df = add_baseline_features(train_df, baselines)
    test_df  = add_baseline_features(test_df,  baselines)

    # 5. Add cyclic features (computed from date, no data leakage)
    print("--- Adding cyclic features ---")
    train_df = add_cyclic_features(train_df)
    test_df  = add_cyclic_features(test_df)

    # 6. Compute category thresholds from TRAIN ratios only
    print("--- Category thresholds from TRAIN data ---")
    thresholds = compute_category_thresholds(train_df)
    ratio_t = thresholds["ratio"]
    print(f"  Ratio thresholds (p50/p70/p88/p97): {[round(x, 3) for x in ratio_t]}")
    with open(PROCESSED / "category_thresholds.json", "w") as f:
        json.dump(thresholds, f, indent=2)

    # Assign categories for distribution inspection
    for split_df in (train_df, test_df):
        split_df["kfz_ratio"] = (
            split_df["kfz_h_slot"] / split_df["hist_kfz_month_slot"].replace(0, np.nan)
        ).fillna(1.0).clip(0.05, 10.0)
        split_df["traffic_category"] = split_df["kfz_ratio"].apply(
            lambda r: assign_category(r, ratio_t)
        )

    print("  Train category distribution:")
    print(train_df["traffic_category"].value_counts().sort_index().to_string())

    # 7. Build feature matrices
    missing = [c for c in FEATURE_COLUMNS if c not in train_df.columns]
    if missing:
        print(f"[ERROR] Missing feature columns: {missing}")
        sys.exit(1)

    X_train = train_df[FEATURE_COLUMNS].copy()
    y_train = train_df["kfz_h_slot"].astype(float)
    X_test  = test_df[FEATURE_COLUMNS].copy() if len(test_df) else None
    y_test  = test_df["kfz_h_slot"].astype(float) if len(test_df) else None

    print(f"\nTrain: {len(X_train):,} rows  |  Test: {len(X_test) if X_test is not None else 0:,} rows")

    # 8. Train regressor — no StandardScaler (GBM is scale-invariant)
    print("\nTraining GradientBoostingRegressor...")
    reg = GradientBoostingRegressor(
        n_estimators=300,
        max_depth=4,        # one level shallower than before to reduce overfitting risk
        learning_rate=0.05,
        subsample=0.8,
        random_state=RANDOM_SEED,
        verbose=0,
    )
    reg.fit(X_train, y_train)
    print("  Done.")

    # 9. Evaluation — honest metrics on TEST YEAR (unseen data)
    metrics = {}
    if X_test is not None and len(X_test) > 0:
        y_pred = reg.predict(X_test)
        metrics = print_metrics(y_test.values, y_pred, f"Evaluation on TEST YEAR {TEST_YEAR}")

        # Monthly breakdown: reveals seasonal accuracy variation
        test_df = test_df.copy()
        test_df["pred"] = y_pred
        monthly = (
            test_df.groupby(pd.to_datetime(test_df["date"]).dt.month)
            .apply(lambda g: pd.Series({
                "MAE":  round(mean_absolute_error(g["kfz_h_slot"], g["pred"]), 0),
                "MAPE": round(compute_mape(g["kfz_h_slot"].values, g["pred"].values), 1),
                "n":    len(g),
            }))
        )
        print(f"\nMonthly breakdown (test year {TEST_YEAR}):")
        print(monthly.to_string())
    else:
        print("[WARN] No test data — skipping evaluation.")

    print_feature_importance(reg)

    # 10. Pack model bundle
    bundle = {
        "regressor":           reg,
        "category_thresholds": thresholds,
        "baselines":           baselines,   # Python dict with tuple keys — stored in joblib
        "feature_columns":     FEATURE_COLUMNS,
        "training_info": {
            "date_range":    f"{pd.to_datetime(train_df['date']).min().date()} → "
                             f"{pd.to_datetime(train_df['date']).max().date()}",
            "test_year":     TEST_YEAR,
            "n_train":       len(X_train),
            "n_test":        len(X_test) if X_test is not None else 0,
            "test_mae":      round(metrics.get("mae", float("nan")), 1),
            "test_rmse":     round(metrics.get("rmse", float("nan")), 1),
            "test_mape_pct": round(metrics.get("mape", float("nan")), 2),
            "test_r2":       round(metrics.get("r2", float("nan")), 3),
            "corridors":     train_df["corridor"].unique().tolist(),
            "version":       "2.0.0",
        },
    }

    joblib.dump(bundle, MODEL_PATH, compress=3)
    size_mb = MODEL_PATH.stat().st_size / 1e6
    print(f"\nModel bundle saved → {MODEL_PATH}  ({size_mb:.1f} MB)")
    print("\nTraining info:")
    for k, v in bundle["training_info"].items():
        print(f"  {k}: {v}")
    print("\nDone. Start the backend: uvicorn backend.app.main:app --reload --port 8000")
