# Hackathon Project — Claude Code Guide

## Mission

Build an AI-powered data analysis solution for TUM Science Hackathon 2026.
Update this section when the theme is announced.

## Architecture

```
data/raw/          →  scripts/          →  backend/app/     →  frontend/
(CSV / JSON /         clean_data.py        processors/          (Lovable React)
 XLSX — not in git)   build_features.py    analyzer.py
                       train_model.py    →  models/
                                            prediction_pipeline.joblib
```

**Frontend stack (Lovable-generated):**
TypeScript 5.8 · React 19 · TanStack Start/Router · TanStack React Query ·
Vite 8 · Tailwind CSS 4 · shadcn/ui · Radix UI · Recharts · Zod · Framer Motion

**Backend:** Python 3.11+ · FastAPI · pandas · scikit-learn · joblib

## Folder Structure

```
TUM-Hackathon/
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI entry point
│   │   ├── api/routes.py        ← API endpoints  ← ADAPT FOR THEME
│   │   └── processors/
│   │       └── analyzer.py      ← Dataset logic  ← ADAPT FOR THEME
│   ├── tests/
│   └── requirements.txt
├── frontend/                    ← Lovable React app (committed)
├── data/
│   ├── raw/                     ← Datasets (NOT in git)
│   ├── processed/               ← Processing output (NOT in git)
│   └── examples/                ← Small sample files (can commit)
├── models/
│   └── prediction_pipeline.joblib  ← NOT in git; download or generate
├── scripts/
│   ├── download_data.sh         ← Pull dataset from Google Drive
│   ├── clean_data.py            ← Step 1: clean raw data
│   ├── build_features.py        ← Step 2: feature engineering
│   └── train_model.py           ← Step 3: train + export .joblib
├── docs/
│   ├── MODEL_CONTRACT.md        ← Model input/output contract
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── THEME_SPECIFIC.md        ← Fill when theme is announced
└── presentation/
```

## Rules

### DO
- Edit `backend/app/processors/analyzer.py` for theme-specific processing
- Edit `backend/app/api/routes.py` for theme-specific endpoints
- Return JSON from all API endpoints (frontend consumes it)
- Write all code, comments, and docstrings in English
- Keep scripts/ files runnable independently (not imported by the app)

### DON'T
- Never commit anything from `data/raw/` or `data/processed/`
- Never commit `.env` (only `.env.example`)
- Never commit `.joblib` model files (> 100 MB limit; store on Google Drive)
- Never run model training inside the app — load the pre-built `.joblib` only
- Never push to `main` directly — use `dev` branch

## Essential Commands

### Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run backend
```bash
uvicorn backend.app.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### Data preparation (run once, in order)
```bash
bash scripts/download_data.sh <GOOGLE_DRIVE_FILE_ID>
python scripts/clean_data.py
python scripts/build_features.py
python scripts/train_model.py
```

### Tests
```bash
pytest backend/tests/
```

## API Pattern

```python
# backend/app/api/routes.py — adding a new endpoint
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class MyRequest(BaseModel):
    filename: str
    param: str = "default"

@router.post("/my-endpoint")
async def my_endpoint(request: MyRequest):
    try:
        result = some_processor(request.filename)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Model Loading Pattern

```python
import joblib
import pandas as pd
from pathlib import Path

model = joblib.load(Path("models/prediction_pipeline.joblib"))

input_df = pd.DataFrame([{"feature_1": 1.0, "feature_2": "category"}])
prediction = model.predict(input_df)
```

## Frontend → Backend Connection

The Lovable frontend calls the backend via fetch. CORS is already configured.

```typescript
// In any Lovable component
const res = await fetch("http://localhost:8000/api/analyze", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ filename: "dataset.csv", analysis_type: "detailed" }),
});
const { success, results } = await res.json();
```

## When the Theme is Announced

1. Fill `docs/THEME_SPECIFIC.md` with dataset structure and success criteria
2. Update `CLAUDE.md` Mission section
3. Implement `backend/app/processors/analyzer.py` with theme-specific logic
4. Add theme-specific endpoints to `backend/app/api/routes.py`
5. Fill `docs/MODEL_CONTRACT.md` with actual model input/output
6. Commit and push: `git commit -m "feat: implement [theme] processor"`
