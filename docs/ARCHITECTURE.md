# Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  USER BROWSER                                                   │
│  Frontend (Lovable React)                                       │
│  TypeScript · TanStack · Recharts · shadcn/ui · Tailwind CSS    │
│  Running on: http://localhost:5173                              │
└───────────────────────┬────────────────────────────────────────┘
                        │  HTTP/JSON (fetch)
                        │  CORS enabled
┌───────────────────────▼────────────────────────────────────────┐
│  BACKEND (FastAPI · Python)                                     │
│  Running on: http://localhost:8000                              │
│  Docs:       http://localhost:8000/docs                        │
│                                                                 │
│  backend/app/api/routes.py        ← API endpoints              │
│  backend/app/processors/          ← Dataset processing logic   │
│  backend/app/main.py              ← CORS · routing · startup   │
└──────────┬──────────────────────────────────┬──────────────────┘
           │                                  │
┌──────────▼──────────┐          ┌────────────▼─────────────────┐
│  data/raw/          │          │  models/                     │
│  data/processed/    │          │  prediction_pipeline.joblib  │
│  (local only,       │          │  (local only, not in git,    │
│   not in git)       │          │   download from Google Drive │
└─────────────────────┘          │   or run scripts/train_model)│
                                 └──────────────────────────────┘
```

## Data Flow

```
1. PREPARATION (run once before hackathon demo)
   data/raw/traffic_hourly.csv
       ↓ scripts/clean_data.py
   data/processed/cleaned_traffic.csv
       ↓ scripts/build_features.py  (adds holiday/calendar/historical features)
   data/processed/features.csv
       ↓ scripts/train_model.py
   models/prediction_pipeline.joblib

2. RUNTIME — Traffic Forecasting
   Frontend (user selects corridor + direction + date range)
       ↓ POST /api/forecast
   FastAPI → processors/traffic_analyzer.py
       ↓ load .joblib, build feature vector per date×slot, run prediction
   JSON: [{ date, time_slot, category 1–5, color, estimated_vehicles, explanation }]
       ↓
   Frontend renders color-coded Traffic Calendar + Peak Day alerts
```

## Technology Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.104 |
| Runtime | Python 3.11+ · uvicorn |
| Data processing | pandas · numpy |
| ML | scikit-learn · joblib |
| Validation | Pydantic v2 |

### Frontend (Lovable-generated)
| Layer | Technology |
|-------|-----------|
| Language | TypeScript 5.8 |
| Framework | React 19 |
| Router | TanStack Router |
| Data fetching | TanStack React Query |
| Build | Vite 8 · Bun |
| UI | shadcn/ui · Radix UI · Tailwind CSS 4 |
| Charts | Recharts |
| Forms | React Hook Form · Zod |
| Animation | Framer Motion |
| Icons | Lucide React |

## Branch Strategy

```
main      ← final deliverable (merge at end of hackathon)
dev       ← active development (all team members commit here)
```

## Theme: Traffic Forecasting (A8 East / A93 South)

```
2. RUNTIME — Traffic Forecasting
   Frontend (user selects corridor + direction + date range)
       ↓ POST /api/forecast
   FastAPI → processors/traffic_analyzer.py
       ↓ load .joblib, build feature vector per date×slot, run prediction
   JSON response: [{ date, time_slot, category 1–5, color, estimated_vehicles, explanation }]
       ↓
   Frontend renders color-coded Traffic Calendar + Peak Day alerts
```

## Theme-Specific Files

| File | What it does |
|------|-------------|
| `backend/app/processors/traffic_analyzer.py` | Builds feature vectors, calls model, formats output |
| `backend/app/api/routes.py` | `/api/forecast`, `/api/calendar`, `/api/peak-days`, `/api/recommendations` |
| `scripts/train_model.py` | Trains GradientBoosting classifier (category 1–5) + volume regressor |
| `docs/THEME_SPECIFIC.md` | Full dataset structure, feature list, success criteria |
| `docs/MODEL_CONTRACT.md` | Model input/output contract with field types |
| `docs/DATA_STRUCTURE.md` | Raw CSV columns, processing pipeline, aggregation logic |
| `CLAUDE.md` | Mission + traffic-specific patterns and examples |

## What Never Changes

- Project directory structure
- `.gitignore` rules (datasets and models stay local)
- Backend/frontend communication pattern (JSON over HTTP)
- Git workflow (dev → main)
- Script execution order (clean → features → train)
