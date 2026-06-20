"""
Step 3: Train traffic forecasting model and export as .joblib bundle.
Run from repo root: python scripts/train_model.py

Reads:
  data/processed/features.csv
  data/processed/category_thresholds.json
  data/processed/baselines.json

Outputs:
  models/prediction_pipeline.joblib

The application loads this file at runtime — it does NOT train.
See docs/MODEL_CONTRACT.md for the full interface.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.app.processors.feature_builder import FEATURE_COLUMNS

PROCESSED = Path("data/processed")
MODELS = Path("models")
MODELS.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
MODEL_PATH = MODELS / "prediction_pipeline.joblib"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    features_file = PROCESSED / "features.csv"
    if not features_file.exists():
        print(f"[ERROR] {features_file} not found. Run build_features.py first.")
        sys.exit(1)

    df = pd.read_csv(features_file, parse_dates=["date"])
    print(f"Loaded {len(df):,} rows from {features_file}")

    # Validate all expected feature columns are present
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        print(f"[ERROR] Missing feature columns: {missing}")
        sys.exit(1)

    X = df[FEATURE_COLUMNS].copy()
    y_cat = df["traffic_category"].astype(int)
    y_vol = df["kfz_h_slot"].astype(float)

    return df, X, y_cat, y_vol


def train_classifier(X_train, y_train) -> Pipeline:
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", GradientBoostingClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            random_state=RANDOM_SEED,
            verbose=0,
        )),
    ])
    print("Training classifier (traffic_category 1–5)...")
    pipeline.fit(X_train, y_train)
    return pipeline


def train_regressor(X_train, y_train) -> Pipeline:
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("reg", GradientBoostingRegressor(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            random_state=RANDOM_SEED,
            verbose=0,
        )),
    ])
    print("Training regressor (kfz_h_slot vehicle count)...")
    pipeline.fit(X_train, y_train)
    return pipeline


def print_feature_importance(pipeline: Pipeline, label: str) -> None:
    try:
        estimator = pipeline.named_steps.get("clf") or pipeline.named_steps.get("reg")
        importances = estimator.feature_importances_
        pairs = sorted(zip(FEATURE_COLUMNS, importances), key=lambda x: -x[1])
        print(f"\nTop 10 feature importances ({label}):")
        for name, imp in pairs[:10]:
            bar = "█" * int(imp * 100)
            print(f"  {name:<35} {imp:.4f}  {bar}")
    except Exception:
        pass


if __name__ == "__main__":
    print("=" * 60)
    print("Step 3: Train model")
    print("=" * 60)

    df, X, y_cat, y_vol = load_data()

    # Stratified split (keep class balance across train/test)
    X_train, X_test, y_cat_train, y_cat_test, y_vol_train, y_vol_test = train_test_split(
        X, y_cat, y_vol, test_size=0.2, random_state=RANDOM_SEED, stratify=y_cat
    )
    print(f"\nTrain: {len(X_train):,} rows  Test: {len(X_test):,} rows")

    # --- Classifier ---
    clf_pipeline = train_classifier(X_train, y_cat_train)
    y_pred_cat = clf_pipeline.predict(X_test)
    print("\n=== Classifier Evaluation (traffic_category) ===")
    print(classification_report(
        y_cat_test, y_pred_cat,
        target_names=["green", "yellow", "orange", "red", "dark_red"],
        zero_division=0,
    ))
    print_feature_importance(clf_pipeline, "classifier")

    # --- Regressor ---
    reg_pipeline = train_regressor(X_train, y_vol_train)
    y_pred_vol = reg_pipeline.predict(X_test)
    mae = mean_absolute_error(y_vol_test, y_pred_vol)
    r2 = r2_score(y_vol_test, y_pred_vol)
    print(f"\n=== Regressor Evaluation (kfz_h_slot) ===")
    print(f"  MAE: {mae:,.0f} vehicles   R²: {r2:.3f}")
    print_feature_importance(reg_pipeline, "regressor")

    # --- Load supplementary data for the bundle ---
    thresholds_path = PROCESSED / "category_thresholds.json"
    baselines_path  = PROCESSED / "baselines.json"

    category_thresholds = {}
    if thresholds_path.exists():
        with open(thresholds_path) as f:
            category_thresholds = json.load(f)

    baselines = {}
    if baselines_path.exists():
        with open(baselines_path) as f:
            raw = json.load(f)
        # Convert string keys back to tuple keys for fast lookup
        baselines["by_dow_slot"]   = {eval(k): v for k, v in raw.get("by_dow_slot", {}).items()}
        baselines["by_month_slot"] = {eval(k): v for k, v in raw.get("by_month_slot", {}).items()}
        baselines["sv_share"]      = {eval(k): v for k, v in raw.get("sv_share", {}).items()}

        # Compute climatological temperature and frost risk from baselines data for inference
        df2 = df.copy()
        df2["month"] = pd.to_datetime(df2["date"]).dt.month
        if "clim_air_temp_c" in df2.columns:
            clim_air = df2.groupby("month")["clim_air_temp_c"].mean().to_dict()
        else:
            clim_air = {1: 1, 2: 2, 3: 6, 4: 11, 5: 15, 6: 19, 7: 21, 8: 20, 9: 16, 10: 11, 11: 5, 12: 2}

        if "is_frost_risk_month" in df2.columns:
            frost_months = set(int(m) for m, v in df2.groupby("month")["is_frost_risk_month"].mean().items() if v > 0.3)
        else:
            frost_months = {1, 2, 11, 12}

        baselines["clim_air_temp"] = {int(k): float(v) for k, v in clim_air.items()}
        baselines["frost_risk_months"] = frost_months

    # --- Pack the model bundle ---
    model_bundle = {
        "classifier": clf_pipeline,
        "regressor": reg_pipeline,
        "category_thresholds": category_thresholds,
        "baselines": baselines,
        "feature_columns": FEATURE_COLUMNS,
        "training_info": {
            "date_range": f"{df['date'].min().date()} → {df['date'].max().date()}",
            "n_samples": len(df),
            "corridors": df["corridor"].unique().tolist(),
            "version": "1.0.0",
        },
    }

    joblib.dump(model_bundle, MODEL_PATH, compress=3)
    size_mb = MODEL_PATH.stat().st_size / 1e6
    print(f"\nModel bundle saved → {MODEL_PATH}  ({size_mb:.1f} MB)")
    print("\nTraining info:")
    for k, v in model_bundle["training_info"].items():
        print(f"  {k}: {v}")
    print("\nDone. Start the backend with: uvicorn backend.app.main:app --reload --port 8000")
