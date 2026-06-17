"""
Model training and export script.
Run ONCE before starting the application. Generates models/prediction_pipeline.joblib.

Usage: python scripts/train_model.py

This script must NOT be run by the application at startup.
The application only loads the already-generated .joblib file.
"""
import pandas as pd
import joblib
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

PROCESSED = Path("data/processed")
MODELS = Path("models")
MODELS.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
MODEL_PATH = MODELS / "prediction_pipeline.joblib"


def train_and_export() -> Pipeline:
    df = pd.read_csv(PROCESSED / "features.csv")

    # Update TARGET_COLUMN and feature list for the specific theme
    TARGET_COLUMN = "target"
    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED)),
    ])

    pipeline.fit(X_train, y_train)

    print("=== Evaluation ===")
    print(classification_report(y_test, pipeline.predict(X_test)))

    joblib.dump(pipeline, MODEL_PATH)
    print(f"Pipeline saved → {MODEL_PATH}")

    return pipeline


if __name__ == "__main__":
    train_and_export()
