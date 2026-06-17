# Data Structure

## Directory Layout

```
data/
├── raw/          ← Original files received at hackathon (NOT in git)
├── processed/    ← Cleaned and feature-engineered outputs (NOT in git)
└── examples/     ← Small representative samples (can commit, max ~1 MB each)
```

## Supported Input Formats

| Format | Extension | Loaded with |
|--------|-----------|-------------|
| CSV    | `.csv`    | `pd.read_csv()` |
| JSON   | `.json`   | `pd.read_json()` |
| Excel  | `.xlsx` / `.xls` | `pd.read_excel()` (requires `openpyxl`) |

## How to Add a Dataset

1. Copy the file to `data/raw/`  — it will not be committed (excluded by `.gitignore`)
2. Call `POST /api/analyze` with `{ "filename": "your_file.csv" }`
3. Or run `python scripts/clean_data.py` for full preparation pipeline

## Processing Pipeline

```
data/raw/dataset.csv
    ↓  scripts/clean_data.py
data/processed/cleaned_dataset.csv
    ↓  scripts/build_features.py
data/processed/features.csv
    ↓  scripts/train_model.py
models/prediction_pipeline.joblib
```

## Dataset from Google Drive

Large prepared datasets are stored as a zip archive on Google Drive.

```bash
bash scripts/download_data.sh <GOOGLE_DRIVE_FILE_ID>
```

This places files into the expected `data/` directories.

## Theme-Specific Structure

Fill this section once the theme is known. See `docs/THEME_SPECIFIC.md`.
