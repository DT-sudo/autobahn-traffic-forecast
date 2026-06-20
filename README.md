# TUM Science Hackathon 2026 — Automated Traffic Forecasting

**Challenge:** Automated Traffic Forecasting for Alpine Holiday Corridors A8 East & A93 South
**Host:** Die Autobahn GmbH des Bundes

Color-coded daily traffic forecasts (green → dark red) for up to one year ahead — replacing the manual expert-driven Traffic Calendar with a data-driven ML system.

---

## What's Built

| Component | Status | Description |
|-----------|--------|-------------|
| ML model | ✅ Done | GradientBoosting classifier + regressor, 25 features, trained 2023–2025 |
| Backend API | ✅ Done | FastAPI — `/forecast`, `/calendar`, `/peak-days`, `/recommendations` |
| Frontend | ✅ Done | React/TanStack calendar UI, fetches live from backend |

---

## Quick Start — Run the Project

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm

---

### 1. Clone the repo

```bash
git clone https://github.com/DT-sudo/TUM-Hackathon.git
cd TUM-Hackathon
```

---

### 2. Backend — Python environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

---

### 3. Download the trained model

The pre-trained model (2.9 MB) is stored on Google Drive (not in git).
Download it and place it at `models/prediction_pipeline.joblib`:

```bash
pip install gdown
gdown "1mThbkhkYqZW3lDtkB7e5-t2w5yGNlqGB" -O models/prediction_pipeline.joblib
```

Or download manually from:
**https://drive.google.com/file/d/1mThbkhkYqZW3lDtkB7e5-t2w5yGNlqGB/view**
→ save the file as `models/prediction_pipeline.joblib`

---

### 4. Start the backend

```bash
PYTHONPATH=backend backend/.venv/bin/python -m uvicorn backend.app.main:app --port 8000
```

Verify it works:
```bash
curl http://localhost:8000/api/health
# → {"status":"ok","model_loaded":true,...}
```

API docs available at: **http://localhost:8000/docs**

---

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:8081** (or whichever port Vite picks — check the terminal output).

The calendar loads immediately with today's date range. Select a road, pick dates, click **Search**.

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
│   ├── requirements.txt
│   └── .venv/                             ← Python virtualenv (not in git)
├── frontend/                              ← React/TanStack app (Lovable)
│   ├── src/
│   │   ├── routes/index.tsx               ← Main calendar page
│   │   └── lib/traffic.ts                 ← API client + types
│   └── package.json
├── data/
│   ├── raw/                               ← Original CSVs (NOT in git)
│   ├── processed/                         ← Pipeline outputs (NOT in git)
│   └── examples/
├── models/
│   └── prediction_pipeline.joblib         ← Trained model (NOT in git)
├── scripts/
│   ├── clean_data.py                      ← Step 1: parse raw CSVs
│   ├── build_features.py                  ← Step 2: feature engineering
│   └── train_model.py                     ← Step 3: train + export model
├── docs/
│   ├── API.md                             ← Endpoint reference
│   ├── MODEL_CONTRACT.md                  ← Model input/output interface
│   ├── DATA_STRUCTURE.md                  ← Dataset column schemas
│   └── THEME_SPECIFIC.md                  ← Challenge details
└── CLAUDE.md                              ← Claude Code instructions
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check + model status |
| `POST` | `/api/forecast` | Forecast for a corridor/direction/date range |
| `GET` | `/api/calendar` | Full year grouped by month (calendar grid) |
| `GET` | `/api/peak-days` | Top N highest-traffic days |
| `POST` | `/api/recommendations` | User-type-tailored travel advice |

Example:

```bash
curl -X POST http://localhost:8000/api/forecast \
  -H "Content-Type: application/json" \
  -d '{"corridor":"A8E","direction":"outbound","date_from":"2026-07-01","date_to":"2026-07-31"}'
```

---

## Road Mapping

| Frontend label | Corridor | Direction | Meaning |
|---------------|----------|-----------|---------|
| A8 East (→ Salzburg) | A8E | outbound | Munich → Salzburg |
| A8 West (→ Munich) | A8E | inbound | Salzburg → Munich |
| A93 South (→ Kufstein) | A93S | outbound | Rosenheim → Kufstein/Austria |
| A93 North (→ Rosenheim) | A93S | inbound | Kufstein → Rosenheim |

---

## Traffic Categories

| Category | Color | Meaning |
|----------|-------|---------|
| 1 | 🟢 Green | Free-flowing |
| 2 | 🟡 Yellow | Increased |
| 3 | 🟠 Orange | Moderate congestion |
| 4 | 🔴 Red | Heavy |
| 5 | ⬛ Dark Red | Critical / congestion risk |

---

## Retrain the Model from Scratch (optional)

Only needed if you have access to the raw dataset from Die Autobahn GmbH.

### Download the raw dataset

The dataset zip is on Google Drive:
**https://drive.google.com/file/d/1Z1Icu2xuuuYB9pNRG6fOnGBT5MjY3wPC/view**

> The file must be shared as "Anyone with the link" for the command below to work.
> If access is restricted, download it manually from the browser and place it at the repo root as `hackathon-dataset.zip`.

```bash
pip install gdown
gdown "1Z1Icu2xuuuYB9pNRG6fOnGBT5MjY3wPC" -O hackathon-dataset.zip
unzip -o hackathon-dataset.zip -d .
```

Expected structure after extraction:
```
data/raw/
├── DAUZ_2+0_1h_2023-2026/          ← 12 hourly traffic CSVs
├── 2023-2025_1min_2+0_v/           ← 12 minute-level CSVs (large)
├── lt und fbt/                      ← temperature CSVs
└── A8_A93_MQ_locations.csv
```

### Run the pipeline

```bash
# Run from repo root, in order:
PYTHONPATH=backend backend/.venv/bin/python scripts/clean_data.py
PYTHONPATH=backend backend/.venv/bin/python scripts/build_features.py
PYTHONPATH=backend backend/.venv/bin/python scripts/train_model.py
# → generates models/prediction_pipeline.joblib
```

Each step prints progress. Step 3 takes ~2–3 minutes.

---

## Git Workflow

```bash
# Always work on dev
git checkout dev

git add <files>
git commit -m "feat: description"
git push origin dev

# To update main:
git checkout main
git merge dev
git push origin main
```

---

## Documentation

| File | Purpose |
|------|---------|
| [CLAUDE.md](CLAUDE.md) | Claude Code context for AI-assisted development |
| [docs/API.md](docs/API.md) | Full endpoint request/response schemas |
| [docs/MODEL_CONTRACT.md](docs/MODEL_CONTRACT.md) | 25 model features, bundle structure |
| [docs/DATA_STRUCTURE.md](docs/DATA_STRUCTURE.md) | Raw CSV schemas, parsing quirks |
| [docs/THEME_SPECIFIC.md](docs/THEME_SPECIFIC.md) | Challenge brief + success criteria |

---

## License

MIT
