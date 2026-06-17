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
   data/raw/dataset.csv
       ↓ scripts/clean_data.py
   data/processed/cleaned_dataset.csv
       ↓ scripts/build_features.py
   data/processed/features.csv
       ↓ scripts/train_model.py
   models/prediction_pipeline.joblib

2. RUNTIME
   Frontend (user input)
       ↓ POST /api/analyze
   FastAPI → processors/analyzer.py
       ↓ load .joblib, run prediction
   JSON response
       ↓
   Frontend renders charts/tables/alerts
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

## What Changes Per Theme

| File | What to change |
|------|----------------|
| `backend/app/processors/analyzer.py` | Theme-specific processing logic |
| `backend/app/api/routes.py` | Theme-specific API endpoints |
| `scripts/train_model.py` | Target variable, features, model type |
| `docs/THEME_SPECIFIC.md` | Dataset description, success criteria |
| `docs/MODEL_CONTRACT.md` | Model input/output interface |
| `CLAUDE.md` | Mission section |

## What Never Changes

- Project directory structure
- `.gitignore` rules (datasets and models stay local)
- Backend/frontend communication pattern (JSON over HTTP)
- Git workflow (dev → main)
- Script execution order (clean → features → train)
