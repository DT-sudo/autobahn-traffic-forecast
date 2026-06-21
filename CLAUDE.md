# Hackathon Project — Claude Code Guide

## Mission

Build an **automated traffic forecasting system** for Alpine motorway corridors **A8 East** and **A93 South** (TUM Science Hackathon 2026, challenge by **Die Autobahn GmbH des Bundes**).

Goal: Replace the manual expert-driven Traffic Calendar (Fahrkalender) with a data-driven system that automatically generates daily traffic forecasts (color-coded green → dark red) for up to one year ahead, covering both travel directions and multiple time slots per day.

## Architecture

```
data/raw/          →  scripts/          →  backend/app/     →  frontend/
(CSV / JSON /         clean_data.py        processors/          (Lovable React)
 XLSX — not in git)   build_features.py    traffic_analyzer.py
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
│   │   ├── main.py                    ← FastAPI entry point
│   │   ├── api/routes.py              ← API endpoints
│   │   └── processors/
│   │       └── traffic_analyzer.py   ← Traffic forecasting logic
│   ├── tests/
│   └── requirements.txt
├── frontend/                          ← Lovable React app (committed)
├── data/
│   ├── raw/                           ← Datasets (NOT in git)
│   │   ├── traffic_hourly.csv         ← Hourly detector counts
│   │   ├── traffic_minute.csv         ← Per-minute counts
│   │   └── surface_temp.csv           ← Road surface temperature
│   ├── processed/                     ← Processing output (NOT in git)
│   └── examples/                      ← Small sample files (can commit)
├── models/
│   └── prediction_pipeline.joblib    ← NOT in git; download or generate
├── scripts/
│   ├── download_data.sh              ← Pull dataset from Google Drive
│   ├── clean_data.py                 ← Step 1: clean raw data
│   ├── build_features.py             ← Step 2: feature engineering
│   └── train_model.py                ← Step 3: train + export .joblib
├── docs/
│   ├── MODEL_CONTRACT.md             ← Model input/output contract
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DATA_STRUCTURE.md
│   └── THEME_SPECIFIC.md             ← Traffic forecasting details
└── presentation/
```

## Theme: Traffic Forecasting Key Concepts

**Corridors:** A8 East (Munich → Salzburg) and A93 South (Munich → Innsbruck/Kufstein)
**Directions:** Outbound (→ Austria/Alps) and Inbound (→ Germany)
**Forecast horizon:** Up to 1 year ahead (e.g. predict June 2026 using June 2023–2025 data)
**Output:** Daily traffic category (1–5: green/yellow/orange/red/dark red) + estimated volume + time-slot breakdown
**Time slots:** 00–06, 06–10, 10–14, 14–18, 18–22, 22–24

**Key feature groups:**
- Calendar: day_of_week, month, week_number, is_weekend, is_public_holiday, is_bridge_day
- Holidays: school_holiday_bavaria, days_until_holiday_start, days_since_holiday_end
- Seasonal: is_summer_season, is_winter_sports_season, is_easter_period
- Directional: direction (outbound/inbound), corridor (A8E/A93S)
- Historical: avg_volume_same_weekday_last_year, same_holiday_period_avg

## Rules

### DO
- Edit `backend/app/processors/traffic_analyzer.py` for forecasting logic
- Edit `backend/app/api/routes.py` for traffic-specific endpoints
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
# backend/app/api/routes.py — traffic forecasting endpoint example
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import date

router = APIRouter()

class ForecastRequest(BaseModel):
    corridor: str           # "A8E" or "A93S"
    direction: str          # "outbound" or "inbound"
    date_from: date
    date_to: date

@router.post("/forecast")
async def get_forecast(request: ForecastRequest):
    try:
        result = traffic_analyzer.forecast(
            request.corridor, request.direction,
            request.date_from, request.date_to
        )
        return {"success": True, "forecast": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Model Loading Pattern

```python
import joblib
import pandas as pd
from pathlib import Path

model = joblib.load(Path("models/prediction_pipeline.joblib"))

input_df = pd.DataFrame([{
    "corridor": "A8E",
    "direction": "outbound",
    "day_of_week": 5,          # Saturday
    "month": 8,
    "is_school_holiday_bavaria": 1,
    "days_until_holiday_start": 0,
    "is_summer_season": 1,
    "is_weekend": 1,
    "is_public_holiday": 0,
}])
prediction = model.predict(input_df)   # returns traffic category 1–5
```

## Frontend → Backend Connection

```typescript
// Fetch traffic calendar for a date range
const res = await fetch("http://localhost:8000/api/forecast", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    corridor: "A8E",
    direction: "outbound",
    date_from: "2026-07-01",
    date_to: "2026-08-31",
  }),
});
const { success, forecast } = await res.json();
// forecast: [{ date, time_slot, category, volume, color, explanation }, ...]
```

## When Working on This Project

1. Consult `docs/THEME_SPECIFIC.md` for dataset structure and success criteria
2. Consult `docs/MODEL_CONTRACT.md` for model input/output interface
3. Consult `docs/API.md` for endpoint reference
4. Consult `tum_hackathon_traffic_forecasting_context.md` for full challenge context
