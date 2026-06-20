# TUM Science Hackathon 2026 — Automated Traffic Forecasting

**Challenge:** Automated Traffic Forecasting for Alpine Holiday Corridors A8 East & A93 South
**Host:** Die Autobahn GmbH des Bundes

Color-coded daily traffic forecasts (green → dark red) for up to one year ahead — replacing the manual expert-driven Traffic Calendar with a data-driven ML system.

---

## What's Built

| Component | Status | Description |
|-----------|--------|-------------|
| ML model | ✅ Done | GradientBoosting regressor + percentile thresholds, 25 features, trained 2023–2025 |
| Backend API | ✅ Done | FastAPI — static CSV feed `/api/data/*.csv` + JSON `/forecast`, `/calendar`, `/peak-days`, `/recommendations` |
| Data export | ✅ Done | 4 per-road traffic CSVs in `data/export/`, served to the frontend |
| Frontend | 🔌 External | Consumes the `/api/data/*.csv` files (parses CSV → calendar UI) |

---

## Quick Start — Run the Project

### Prerequisites

- Python 3.11+
- (Optional) Node.js 18+ — only if you add a frontend that consumes the CSV feed

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

The pre-trained model (0.7 MB, v2.0.0) is stored on Google Drive (not in git).
Download it and place it at `models/prediction_pipeline.joblib`:

```bash
pip install gdown
gdown "1dnAvcgApUMZQ03NfQzAhNHIaldAgArxI" -O models/prediction_pipeline.joblib
```

Or download manually from:
**https://drive.google.com/file/d/1dnAvcgApUMZQ03NfQzAhNHIaldAgArxI/view**
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

### 5. Generate the traffic CSV files

```bash
PYTHONPATH=backend backend/.venv/bin/python scripts/export_frontend_csv.py
```

This writes the 4 per-road CSVs into `data/export/`. They are then served by the running backend at
`http://localhost:8000/api/data/<file>.csv`. Verify:

```bash
curl http://localhost:8000/api/data/A8easttraffic.csv | head -3
```

### 6. Connect a frontend

The frontend fetches the static CSV feed and renders the calendar. See
[Traffic Data CSV Files](#traffic-data-csv-files) for the column structure and the
file ↔ road mapping it should expect.

---

## Project Structure

```
TUM-Hackathon/
├── backend/
│   ├── app/
│   │   ├── main.py                        ← FastAPI entry point (mounts /api/data CSV feed)
│   │   ├── api/routes.py                  ← All API endpoints
│   │   └── processors/
│   │       ├── traffic_analyzer.py        ← Forecast engine (loads .joblib)
│   │       └── feature_builder.py         ← Shared feature engineering
│   ├── requirements.txt
│   └── .venv/                             ← Python virtualenv (not in git)
├── data/
│   ├── raw/                               ← Original CSVs (NOT in git)
│   ├── processed/                         ← Pipeline outputs (NOT in git)
│   ├── export/                            ← Generated per-road CSVs, served at /api/data (NOT in git)
│   └── examples/                          ← CSV format reference samples
├── models/
│   └── prediction_pipeline.joblib         ← Trained model (NOT in git)
├── scripts/
│   ├── clean_data.py                      ← Step 1: parse raw CSVs
│   ├── build_features.py                  ← Step 2: feature engineering
│   ├── train_model.py                     ← Step 3: train + export model
│   └── export_frontend_csv.py             ← Generate the 4 per-road CSVs → data/export/
├── docs/
│   ├── API.md                             ← Endpoint reference
│   ├── MODEL_CONTRACT.md                  ← Model input/output interface
│   ├── DATA_STRUCTURE.md                  ← Dataset column schemas
│   └── THEME_SPECIFIC.md                  ← Challenge details
└── CLAUDE.md                              ← Claude Code instructions
```

---

## API Endpoints

### Static traffic data (for the frontend)

The frontend consumes ready-to-parse **CSV files** served as static files — one per road. This is
the primary data feed; see [Traffic Data CSV Files](#traffic-data-csv-files) for the column layout.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/data/A8easttraffic.csv` | A8 East — Munich → Salzburg (A8E outbound) |
| `GET` | `/api/data/A8westtraffic.csv` | A8 West — Salzburg → Munich (A8E inbound) |
| `GET` | `/api/data/A93southtraffic.csv` | A93 South — Rosenheim → Kufstein (A93S outbound) |
| `GET` | `/api/data/A93northtraffic.csv` | A93 North — Kufstein → Rosenheim (A93S inbound) |

```bash
curl http://localhost:8000/api/data/A8easttraffic.csv
# day,traffic,1 part,2 part,3 part,4 part,5 part,6 part
# 20.06.2026,heavy,heavy,heavy,heavy,increased,increased,heavy
# ...
```

```js
// Frontend fetch example
const res = await fetch("http://localhost:8000/api/data/A8easttraffic.csv");
const csv = await res.text();   // parse with PapaParse, d3-dsv, etc.
```

### Dynamic JSON API (model inference)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check + model status |
| `POST` | `/api/forecast` | Forecast for a corridor/direction/date range |
| `GET` | `/api/calendar` | Full year grouped by month (calendar grid) |
| `GET` | `/api/peak-days` | Top N highest-traffic days |
| `POST` | `/api/recommendations` | User-type-tailored travel advice |

```bash
curl -X POST http://localhost:8000/api/forecast \
  -H "Content-Type: application/json" \
  -d '{"corridor":"A8E","direction":"outbound","date_from":"2026-07-01","date_to":"2026-07-31"}'
```

---

## Traffic Data CSV Files

The four CSV files are the deliverable the frontend parses. They are generated from the trained
model into `data/export/` and served at `/api/data/<file>.csv` (see above).

### Generate / refresh the files

```bash
PYTHONPATH=backend backend/.venv/bin/python scripts/export_frontend_csv.py
# → writes 4 CSVs into data/export/ (forecast horizon: today → +1 year)
```

### File ↔ road mapping

| File | Corridor | Direction | Route |
|------|----------|-----------|-------|
| `A8easttraffic.csv` | A8E | outbound | Munich → Salzburg |
| `A8westtraffic.csv` | A8E | inbound | Salzburg → Munich |
| `A93southtraffic.csv` | A93S | outbound | Rosenheim → Kufstein |
| `A93northtraffic.csv` | A93S | inbound | Kufstein → Rosenheim |

### Column layout

Header (exact): `day,traffic,1 part,2 part,3 part,4 part,5 part,6 part`

| Column | Type | Description |
|--------|------|-------------|
| `day` | `DD.MM.YYYY` | Calendar date (one row per day) |
| `traffic` | level string | **Overall daily level** — the analyzer's `daily_category` (daily total volume vs daily thresholds), the same value the JSON API returns |
| `1 part` | level string | Time slot 1 — `00:00–06:00` |
| `2 part` | level string | Time slot 2 — `06:00–10:00` |
| `3 part` | level string | Time slot 3 — `10:00–14:00` |
| `4 part` | level string | Time slot 4 — `14:00–18:00` |
| `5 part` | level string | Time slot 5 — `18:00–22:00` |
| `6 part` | level string | Time slot 6 — `22:00–24:00` |

### Level values

The frontend works with **4 levels only**. Each cell is one of these four strings — the
model's 5 internal [traffic categories](#traffic-categories) are folded to 4 at export time
(category 3 "moderate" → `increased`):

| Level string | From category | Color |
|--------------|---------------|-------|
| `low` | 1 | 🟢 Green |
| `increased` | 2 + 3 | 🟡 Yellow |
| `heavy` | 4 | 🔴 Red |
| `extreme` | 5 | ⬛ Dark Red |

> **Notes for frontend parsing:** UTF-8, LF line endings, comma-separated, no quoting.
> Only the 4 level strings above ever appear (no `moderate`). The `traffic` column is the
> analyzer's daily category, so it matches the JSON API and never needs to be recomputed
> client-side. Each file covers a rolling one-year window starting from the day it was
> generated.

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
