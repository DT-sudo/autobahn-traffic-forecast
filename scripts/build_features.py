"""
Feature engineering script. Run after clean_data.py.
Usage: python scripts/build_features.py
"""
import pandas as pd
from pathlib import Path

PROCESSED = Path("data/processed")


def build_features(input_filename: str) -> pd.DataFrame:
    """Add theme-specific feature engineering here."""
    df = pd.read_csv(PROCESSED / input_filename)

    # Example: extract time features if a datetime column exists
    # for col in df.select_dtypes(include="datetime").columns:
    #     df[f"{col}_hour"] = df[col].dt.hour
    #     df[f"{col}_dayofweek"] = df[col].dt.dayofweek

    return df


if __name__ == "__main__":
    df = build_features("cleaned_dataset.csv")
    out = PROCESSED / "features.csv"
    df.to_csv(out, index=False)
    print(f"Features saved → {out}  ({len(df.columns)} columns)")
