import pandas as pd
from pathlib import Path

# Resolves to data/raw/ at repo root regardless of where uvicorn is launched
RAW_DATA_PATH = Path(__file__).parents[4] / "data" / "raw"


def analyze_dataset(filename: str, analysis_type: str = "summary") -> dict:
    """
    Analyze a dataset file from data/raw/.
    Replace this function body with theme-specific logic on hackathon day.
    """
    file_path = RAW_DATA_PATH / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found in data/raw/: {filename}")

    ext = file_path.suffix.lower()

    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext == ".json":
        df = pd.read_json(file_path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return _build_result(df, ext.lstrip("."), analysis_type)


def _build_result(df: pd.DataFrame, fmt: str, analysis_type: str) -> dict:
    result = {
        "format": fmt,
        "row_count": len(df),
        "columns": list(df.columns),
        "statistics": df.describe(include="all").fillna("").to_dict() if analysis_type == "detailed" else {},
        "sample": df.head(5).to_dict(orient="records") if analysis_type == "detailed" else [],
        "insights": [],
    }
    return result
