# Data Structure

Will be filled based on the specific hackathon theme and dataset provided.

## General Structure

```
backend/data/
├── raw/          ← Original dataset files (NOT in git)
│   └── .gitkeep
└── processed/    ← Output of analysis (NOT in git)
    └── .gitkeep
```

## Supported Formats

| Format | Extension | Parser |
|--------|-----------|--------|
| CSV    | .csv      | csv-parser |
| JSON   | .json     | JSON.parse |
| Excel  | .xlsx/.xls | xlsx |

## How to Add a Dataset

1. Copy the file to `backend/data/raw/`
2. It will NOT be committed to git (excluded by .gitignore)
3. Call `POST /api/analyze` with the filename
