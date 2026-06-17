"""
Data cleaning script. Run before build_features.py.
Usage: python scripts/clean_data.py
"""
import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)


def clean(filename: str) -> None:
    """Add theme-specific cleaning logic here."""
    df = pd.read_csv(RAW / filename)

    # Drop empty rows
    df = df.dropna(how="all")

    # Strip whitespace from string columns
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda c: c.str.strip())

    out = PROCESSED / f"cleaned_{filename}"
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows → {out}")


if __name__ == "__main__":
    # Update with actual dataset filename on hackathon day
    clean("dataset.csv")
