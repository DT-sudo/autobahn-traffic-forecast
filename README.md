# TUM Science Hackathon 2026 — Automated Traffic Forecasting

**Challenge:** Automated Traffic Forecasting for Alpine Holiday Corridors A8 East & A93 South
**Host:** Die Autobahn GmbH des Bundes

Replaces the manual expert-driven Traffic Calendar (Fahrkalender) with a data-driven ML system that generates daily color-coded forecasts (green → dark red) for up to one year ahead.

---

## Current Status

| Component | Status |
|-----------|--------|
| Data cleaning (`clean_data.py`) | Done — 283,375 rows, 2023–2025 |
| Feature engineering (`build_features.py`) | Done — 25,753 slot-level rows |
| ML model (`train_model.py`) | Done — `models/prediction_pipeline.joblib` (2.9 MB) |
| Backend API (`backend/app/`) | Done — FastAPI + all endpoints |
| Frontend (`frontend/`) | Pending — Lovable app to be added |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 · FastAPI · uvicorn |
| ML | scikit-learn GradientBoosting · joblib |
| Data | pandas · numpy · holidays |
| Frontend | React 19 · TypeScript 5.8 (Lovable) |
| UI | shadcn/ui · Tailwind CSS 4 · Recharts · TanStack |

---

## Quick Start

### Backend (already has trained model — just run it)

```bash
# From repo root
backend/.venv/bin/uvicorn backend.app.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
# Health:   http://localhost:8000/api/health
```

### If you need to retrain (e.g. new data)

```bash
# Set up venv (once)
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Run pipeline (in order)
backend/.venv/bin/python scripts/clean_data.py        # Step 1: clean raw CSVs
backend/.venv/bin/python scripts/build_features.py    # Step 2: build features
backend/.venv/bin/python scripts/train_model.py       # Step 3: train → models/prediction_pipeline.joblib
```

### Frontend (once Lovable files are added)

```bash
cd frontend
bun install
bun dev
# UI: http://localhost:5173
```

---

## Project Structure

```
TUM-Hackathon/
├── backend/
│   ├── app/
│   │   ├── main.py                        ← FastAPI entry point
│   │   ├── api/routes.py                  ← All API endpoints
│   │   └── processors/
│   │       ├── traffic_analyzer.py        ← Forecast engine (loads .joblib)
│   │       └── feature_builder.py         ← Shared feature engineering
│   ├── tests/
│   └── requirements.txt
├── frontend/                              ← Lovable React app (add here)
├── data/
│   ├── raw/                               ← Original CSVs (NOT in git)
│   ├── processed/                         ← Pipeline output (NOT in git)
│   └── examples/                          ← Small sample files
├── models/
│   └── prediction_pipeline.joblib         ← Trained model (NOT in git)
├── scripts/
│   ├── download_data.sh                   ← Pull raw data from Google Drive
│   ├── clean_data.py                      ← Step 1
│   ├── build_features.py                  ← Step 2
│   └── train_model.py                     ← Step 3
├── docs/
│   ├── API.md                             ← Endpoint reference
│   ├── ARCHITECTURE.md                    ← System overview
│   ├── DATA_STRUCTURE.md                  ← Dataset column schemas
│   ├── MODEL_CONTRACT.md                  ← Model input/output interface
│   └── THEME_SPECIFIC.md                  ← Challenge details + success criteria
├── presentation/
├── CLAUDE.md                              ← Claude Code instructions (read every session)
└── .env.example
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check + model status |
| `POST` | `/api/forecast` | Forecast for a date range |
| `GET` | `/api/calendar` | Full year grouped by month (for calendar UI) |
| `GET` | `/api/peak-days` | Top N highest-traffic days |
| `POST` | `/api/recommendations` | User-type-tailored travel advice |
| `GET` | `/api/analysis/summary` | Historical stats from training data |

Example forecast request:

```bash
curl -X POST http://localhost:8000/api/forecast \
  -H "Content-Type: application/json" \
  -d '{"corridor":"A8E","direction":"outbound","date_from":"2026-07-01","date_to":"2026-07-31"}'
```

---

## Frontend → Backend Connection

The Lovable frontend should point to `http://localhost:8000/api`. See [docs/API.md](docs/API.md) for the full response shapes.

Key integration points:
- **Calendar grid** → `GET /api/calendar?year=2026&corridor=A8E&direction=outbound`
- **Day detail** → `POST /api/forecast` with specific date range
- **Peak days widget** → `GET /api/peak-days?corridor=A8E&direction=outbound&top_n=10`

---

## Documentation

| File | Purpose |
|------|---------|
| [CLAUDE.md](CLAUDE.md) | Claude Code context — model architecture, rules |
| [docs/API.md](docs/API.md) | All endpoint request/response shapes |
| [docs/MODEL_CONTRACT.md](docs/MODEL_CONTRACT.md) | 25 model features, bundle structure, examples |
| [docs/DATA_STRUCTURE.md](docs/DATA_STRUCTURE.md) | Raw CSV schemas, parsing quirks |
| [docs/THEME_SPECIFIC.md](docs/THEME_SPECIFIC.md) | Challenge brief + success criteria |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design overview |

---

## Git Workflow

```bash
git checkout dev
# ... make changes ...
git add <files>
git commit -m "feat: description"
git push origin dev
# Never push directly to main
```

## License

MIT
