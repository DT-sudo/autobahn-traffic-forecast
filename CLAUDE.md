# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

The frontend job is to parse the data like the following 4 files into a nice UI
- ./data/examples/A8easttraffic.csv  
- ./data/examples/A8westtraffic.csv
- ./data/examples/A93northtraffic.csv
- ./data/examples/A93southtraffic.csv

Your job is to generate generate those 4 files with accurate data. 

# Hackathon Project — Claude Code Guide

## Mission

Build an **automated traffic forecasting system** for Alpine motorway corridors **A8 East** and **A93 South** (TUM Science Hackathon 2026, challenge by **Die Autobahn GmbH des Bundes**).

Goal: Replace the manual expert-driven Traffic Calendar (Fahrkalender) with a data-driven system that automatically generates daily traffic forecasts (color-coded green → dark red) for up to one year ahead, covering both travel directions and multiple time slots per day.

## Architecture

```
data/raw/        →  scripts/          →  data/processed/   →  models/            →  backend/app/        →  frontend/
(CSV — not in git)  clean_data.py        cleaned_*.csv        prediction_         api/routes.py          src/lib/traffic.ts
                    build_features.py    features.csv         pipeline.joblib     processors/            (Lovable React,
                    train_model.py       *_thresholds.json    (bundle, not        traffic_analyzer.py     calls localhost:8000)
                                         baselines.json        in git)            feature_builder.py
```

**Single source of truth for features:** `backend/app/processors/feature_builder.py` is
imported by BOTH the training scripts (`scripts/build_features.py`, `scripts/train_model.py`)
AND the live inference path (`traffic_analyzer.py`). `FEATURE_COLUMNS` defines the exact 25
columns and order the model expects — training and inference cannot drift because they share
this one module. Change a feature here and you must retrain the model. The scripts add
`repo_root` to `sys.path` and import it as `backend.app.processors.feature_builder`.

**Model = a bundle dict, not a bare estimator.** `prediction_pipeline.joblib` deserializes to
`{regressor, slot_thresholds, daily_thresholds, baselines, training_info}`. A single
`GradientBoostingRegressor` predicts slot *volume* (vehicles); all 1–5 traffic categories
(colors) are then DERIVED from that volume via percentile thresholds (`assign_category`).
Slot category = slot volume vs per-slot thresholds; **daily** category = daily *total* vs
per-corridor/direction `daily_thresholds` (NOT max-of-slots — that over-inflated red days).
This keeps the displayed color consistent with the displayed vehicle count. If the .joblib is
missing, `traffic_analyzer` logs a warning and serves deterministic mock data (`_mock_predict`)
so the API still works without the model.

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
│   │   ├── api/routes.py              ← API endpoints (mounted under /api)
│   │   └── processors/
│   │       ├── feature_builder.py    ← Shared feature engine (FEATURE_COLUMNS, holidays, categories)
│   │       └── traffic_analyzer.py   ← Inference: loads bundle, builds rows, derives categories
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
- Never force-push / rebase / amend already-pushed commits: `frontend/` is connected to **Lovable**
  (see `frontend/AGENTS.md`); rewriting pushed history corrupts the user's Lovable project history.
  Commits pushed to the connected branch sync back to Lovable — keep the branch in a working state.

## Essential Commands

### Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run backend
`main.py` uses absolute imports (`from app.api.routes ...`), so `backend/` must be on the
Python path — run from the repo root with `PYTHONPATH=backend`:
```bash
PYTHONPATH=backend backend/.venv/bin/python -m uvicorn backend.app.main:app --reload --port 8000
# Equivalent: cd backend && uvicorn app.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### Run frontend (Lovable React app — uses bun; npm also works)
```bash
cd frontend
bun install          # or: npm install  (both bun.lock and package-lock.json are committed)
bun run dev          # Vite dev server on http://localhost:5173
bun run lint         # eslint .
bun run format       # prettier --write .
bun run build        # production build
```
The frontend hardcodes the backend URL as `API_URL = "http://localhost:8000"` in
`src/lib/traffic.ts` — change it there, not via env var.

### Data preparation (run once, in order — all scripts run from repo root)
```bash
bash scripts/download_data.sh <GOOGLE_DRIVE_FILE_ID>   # → data/raw/ (semicolon-separated CSVs)
python scripts/clean_data.py        # data/raw/ → data/processed/cleaned_traffic_hourly.csv, cleaned_weather_hourly.csv
python scripts/build_features.py    # → features.csv, category_thresholds.json, daily_thresholds.json, baselines.json
python scripts/train_model.py       # → models/prediction_pipeline.joblib (the bundle dict)
```

### Tests
```bash
pytest backend/tests/        # NOTE: tests/ currently holds only .gitkeep — no tests written yet
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
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))   # validation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

All routes are mounted under the `/api` prefix (`app.include_router(router, prefix="/api")`).
Endpoints accept/return `corridor` ∈ {A8E, A93S}, `direction` ∈ {outbound, inbound}; max range 366 days.

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/api/health` | status + `model_loaded` flag |
| POST | `/api/forecast` | slot-level forecast for a date range (6 slots/day) |
| GET  | `/api/calendar?year=&corridor=&direction=` | full-year daily categories grouped by month (calendar grid) |
| GET  | `/api/peak-days?corridor=&direction=&top_n=&year=` | top-N highest-risk days |
| POST | `/api/recommendations` | per-day advice tailored to `user_type` (tourist/logistics/local_resident/tourism_business) |
| GET  | `/api/analysis/summary?corridor=&direction=` | historical averages from bundled baselines (503 if model not loaded) |

The shared analyzer is a lazy module-level singleton: always get it via `get_analyzer()` (don't
construct `TrafficAnalyzer()` directly) so the model loads once.

## Model Loading Pattern

The .joblib is a **bundle dict** loaded once by `TrafficAnalyzer`; you don't call
`model.predict()` on it directly. The regressor predicts volume; categories are derived. To add
inputs, change `feature_builder.FEATURE_COLUMNS` and retrain — `traffic_analyzer` builds the
feature row through the same module so the two stay in lockstep.

```python
import joblib
from pathlib import Path

bundle = joblib.load(Path("models/prediction_pipeline.joblib"))
# bundle keys: regressor, slot_thresholds, daily_thresholds, baselines, training_info
regressor = bundle["regressor"]            # GradientBoostingRegressor → predicts slot VOLUME

from app.processors.feature_builder import FEATURE_COLUMNS, assign_category, build_feature_row
from datetime import date
import pandas as pd

row = build_feature_row(date(2026, 8, 1), time_slot=4, corridor="A8E",
                        direction="outbound", baselines=bundle["baselines"])
X = pd.DataFrame([[row[c] for c in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
volume = max(0, round(float(regressor.predict(X)[0])))
category = assign_category(volume, bundle["slot_thresholds"]["A8E|outbound|4"])  # 1–5
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
// forecast: one entry PER DAY, each with a nested time_slots[] array:
// [{ date, day_of_week, daily_category, daily_color, daily_color_hex,
//    estimated_daily_vehicles, pattern_type,
//    time_slots: [{ slot, label, category, color, color_hex,
//                   estimated_vehicles, confidence, explanation:[...] }, ...] }]
```
Frontend API calls live in `src/lib/traffic.ts`, which maps the backend's 1–5 category to its
own `TrafficLevel` union (low/increased/moderate/heavy/extreme). The single route is
`src/routes/index.tsx`.

## When Working on This Project

1. Consult `docs/THEME_SPECIFIC.md` for dataset structure and success criteria
2. Consult `docs/MODEL_CONTRACT.md` for model input/output interface
3. Consult `docs/API.md` for endpoint reference
4. Consult `tum_hackathon_traffic_forecasting_context.md` for full challenge context
