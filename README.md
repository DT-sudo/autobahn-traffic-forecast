# Automated Traffic Forecasting for Alpine Holiday Corridors

**A machine-learning replacement for the manually produced German motorway Traffic Calendar (*Fahrkalender*) — generating colour-coded daily congestion forecasts up to one year ahead for the A8 East and A93 South corridors.**

---

## Project Context

| | |
|---|---|
| **Event** | TUM Science Hackathon 2026 |
| **Host institution** | Technical University of Munich (TUM) — one of Europe's leading technical universities |
| **Challenge partner** | **Die Autobahn GmbH des Bundes** — the German federal motorway operator, responsible for the entire ~13,000 km Autobahn network |
| **Challenge** | Automated Traffic Forecasting for Alpine Holiday Corridors A8 East & A93 South |
| **Data** | Proprietary loop-detector measurements, 2023–2025, provided by the challenge partner |
| **Pitch deck** | [`presentation/presentation.pdf`](presentation/presentation.pdf) — the five slides presented at the hackathon |

Die Autobahn GmbH publishes an annual **Traffic Calendar** that tells millions of travellers which days on the Alpine holiday routes will be congested. It is compiled **by hand, by domain experts**, every year.

This project replaces that manual process with a reproducible, data-driven system: a model trained on three years of real detector data that produces the same colour-coded forecast automatically, for any date up to a year ahead, in both travel directions and at six-slot daily resolution.

The corridors matter because they carry the whole of southern Germany's holiday traffic into Austria and the Alps — the **A8 East** (Munich → Salzburg) and the **A93 South** (Inntal → Kufstein). On peak departure weekends these routes are among the most congested in the country.

---

## What the System Does

Given a corridor, a direction and a date range, it returns for every day:

- a **traffic category from 1 to 5**, rendered green → yellow → orange → red → dark red,
- an **estimated vehicle volume**,
- a **breakdown across six time slots**, so a traveller can see that Saturday morning is jammed while Saturday evening is clear,
- a **human-readable explanation** of *why* — school holidays, bridge days, Easter, winter-sports season, and so on.

It needs **no real-time sensor feed**. Every prediction is derived from the calendar alone, which is what makes a twelve-month horizon possible.

---

## Quick Start

Requires **Python 3.11 or 3.12** (see note below), **Node.js 18+**, and `make`.

```bash
git clone git@github.com:DT-sudo/TUM-Hackathon.git
cd TUM-Hackathon

make quickstart     # installs dependencies, downloads the dataset, trains the model
make run            # starts the API and the web UI together
```

Then open **http://localhost:8080**.

That is the whole setup. `make quickstart` takes roughly 5–10 minutes, most of it the 154 MB dataset download and the model training.

### Available commands

| Command | What it does |
|---------|--------------|
| `make quickstart` | Full setup from a fresh clone: dependencies + data + trained model |
| `make run` | Start backend (`:8000`) and frontend (`:8080`) together; Ctrl-C stops both |
| `make install` | Python virtualenv, backend dependencies, `npm install` |
| `make data` | Download and unpack the raw detector dataset into `data/raw/` |
| `make train` | Run the four-step pipeline and write `models/prediction_pipeline.joblib` |
| `make backend` | Start only the API, with autoreload |
| `make frontend` | Start only the web UI |
| `make check` | Verify the API is up and the model is loaded |
| `make stop` | Stop whatever is still listening on either port |
| `make clean` | Remove generated data, model and caches |
| `make distclean` | Also remove the virtualenv and `node_modules` |

### A note on the Python version

The project pins `numpy 1.26` and `scikit-learn 1.3`, which publish **no wheels for Python 3.13 or newer**. The Makefile automatically prefers `python3.12` or `python3.11` if either is on your `PATH`, and stops with a clear message if the virtualenv ends up on an unsupported interpreter. To point it at a specific interpreter:

```bash
make distclean
make install PYTHON=/usr/local/bin/python3.12
```

### Running it manually

If you would rather not use `make`:

```bash
# 1. Backend environment
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt gdown

# 2. Dataset  (~154 MB, extracts to the repo root, then move into data/raw/)
backend/.venv/bin/gdown "1Z1Icu2xuuuYB9pNRG6fOnGBT5MjY3wPC" -O hackathon-dataset.zip
unzip -o hackathon-dataset.zip -d . && rm -rf __MACOSX hackathon-dataset.zip
mkdir -p data/raw && mv "DAUZ_2+0_1h_2023-2026" "2023-2025_1min_2+0_v" "lt und fbt" A8_A93_MQ_locations.csv data/raw/

# 3. Build the model  (four steps, in order)
PYTHONPATH=backend backend/.venv/bin/python scripts/clean_data.py
PYTHONPATH=backend backend/.venv/bin/python scripts/build_features.py
PYTHONPATH=backend backend/.venv/bin/python scripts/train_model.py
PYTHONPATH=backend backend/.venv/bin/python scripts/process_historical.py

# 4. Run  (two terminals)
PYTHONPATH=backend backend/.venv/bin/python -m uvicorn backend.app.main:app --port 8000
cd frontend && npm install && npm run dev
```

The frontend dev server runs on **port 8080** (configured by the Lovable Vite preset), and the API on **8000**.

---

## How the Model Works

### 1. From raw detectors to time slots

Twelve loop-detector stations across the two corridors and both directions record vehicle counts every hour (`kfz_h` = all vehicles, `sv_h` = heavy goods vehicles). Cleaning drops negative counts and per-hour outliers above the 99.9th percentile, then stacks all stations into **283,160 hourly rows** covering 2023-01-01 → 2025-12-31.

Each day is then divided into six slots — `00–06`, `06–10`, `10–14`, `14–18`, `18–22`, `22–24` — with counts **summed** inside a slot and averaged across stations on the same corridor and direction. Slots missing more than 25% of their hours are dropped. Result: **25,740 slot-level rows**.

### 2. Historical baselines

Three averages are computed from training data only and stored inside the model bundle:

- `by_dow_slot` — mean volume per (corridor, direction, day-of-week, slot): the weekly rhythm
- `by_month_slot` — mean volume per (corridor, direction, month, slot): seasonality
- `by_slot` — mean volume per (corridor, direction, slot) across all months

### 3. Features

**21 features**, all derivable from a calendar date — which is precisely why the model can forecast a year ahead without any live data:

| Group | Features |
|-------|----------|
| **Cyclical calendar** | `month_sin`, `month_cos`, `dow_sin`, `dow_cos`, `week_of_year`, `time_slot` |
| **Public holidays** | `is_public_holiday_de`, `is_public_holiday_bavaria`, `is_bridge_day`, `is_long_weekend` |
| **School holidays** | `is_school_holiday_bavaria`, `is_school_holiday_bw`, `days_until_school_holiday`, `days_since_school_holiday` |
| **Seasonal events** | `is_easter_period`, `is_christmas_period` |
| **Road context** | `is_outbound`, `is_a93` |
| **Historical baselines** | `hist_kfz_dow_slot`, `hist_kfz_month_slot` |
| **Weather proxy** | `clim_air_temp_c` |

Month and weekday are encoded as sine/cosine pairs so the model understands that December is adjacent to January and Sunday is adjacent to Monday, rather than treating them as distant integers.

### 4. Training and honest validation

A **Gradient Boosting regressor** (`StandardScaler → GradientBoostingRegressor`) predicts raw vehicle volume per slot.

Validation is **out-of-time, not a random split**: the model trains on **2023–2024** and is tested on the entirely unseen **2025**. This is the harder and more honest evaluation — it measures exactly what the system is asked to do in production, namely forecast a year it has never observed.

| Metric | Value |
|--------|-------|
| Training rows | 17,507 (2023–2024) |
| Test rows | 8,233 (2025, held out entirely) |
| MAE | 558 vehicles per slot |
| RMSE | 938 |
| MAPE | 13.0% |
| R² | **0.923** |

Feature importance is dominated by the two historical baselines — `hist_kfz_month_slot` (57%) and `hist_kfz_dow_slot` (38%) — with the calendar and holiday features supplying the corrections that matter on exactly the days the Traffic Calendar exists to warn about.

### 5. Turning volume into a colour

Rather than classifying colours directly, the system predicts volume and then compares it to what is *normal* for that exact corridor, direction, month and slot:

```
ratio = predicted_volume / hist_kfz_month_slot
```

Thresholds derived from the training distribution map that ratio onto the five categories:

| Category | Colour | Ratio | Meaning |
|----------|--------|-------|---------|
| 1 | 🟢 Green | < 0.96 | Below normal |
| 2 | 🟡 Yellow | 0.96 – 1.08 | Slightly above normal |
| 3 | 🟠 Orange | 1.08 – 1.27 | Noticeably above normal |
| 4 | 🔴 Red | 1.27 – 1.60 | Top ~12% of days |
| 5 | ⬛ Dark red | > 1.60 | Top ~3% — extreme |

Normalising by ratio rather than raw count is what makes the scale fair across slots: a 6-hour night window and a 4-hour afternoon window are each judged against their own norm.

---

## API

Interactive documentation is served at **http://localhost:8000/docs**.

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/health` | Service status and whether the model is loaded |
| `POST` | `/api/forecast` | Forecast for a corridor, direction and date range |
| `GET` | `/api/calendar` | A full year, grouped by month |
| `GET` | `/api/peak-days` | The N busiest days of a year |
| `POST` | `/api/recommendations` | Travel advice tailored to a user type |
| `GET` | `/api/historical` | Real measured values from 2023–2025 |

```bash
curl -X POST http://localhost:8000/api/forecast \
  -H 'Content-Type: application/json' \
  -d '{"corridor":"A8E","direction":"outbound","date_from":"2026-08-01","date_to":"2026-08-03"}'
```

Corridors are `A8E` and `A93S`; directions are `outbound` (toward Salzburg / Kufstein / the Alps) and `inbound` (toward Munich / Rosenheim).

Full reference in [`docs/API.md`](docs/API.md).

---

## Technology

**Backend** — Python 3.12 · FastAPI · scikit-learn · pandas · joblib
**Frontend** — TypeScript · React 19 · TanStack Start & Router · TanStack Query · Vite 8 · Tailwind CSS 4 · shadcn/ui · Recharts
**Model** — Gradient Boosting regressor with ratio-based category thresholds, shipped as a single `.joblib` bundle containing the pipeline, the baselines and the thresholds

---

## Project Structure

```
.
├── Makefile                  ← every workflow in this README
├── backend/
│   ├── app/
│   │   ├── main.py                       FastAPI entry point
│   │   ├── api/routes.py                 all endpoints
│   │   └── processors/
│   │       ├── traffic_analyzer.py       forecast engine
│   │       └── feature_builder.py        shared feature engineering
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── routes/index.tsx              calendar page
│       └── lib/traffic.ts                API client and types
├── scripts/
│   ├── clean_data.py                     step 1 — clean raw detector files
│   ├── build_features.py                 step 2 — slot aggregation + features
│   ├── train_model.py                    step 3 — train and export the bundle
│   └── process_historical.py             step 4 — export measured history
├── data/
│   ├── raw/                              source dataset (not in git)
│   └── processed/                        pipeline output (not in git)
├── models/
│   └── prediction_pipeline.joblib        trained bundle (not in git)
└── docs/                                 API, model contract, data structure
```

Datasets and trained models are deliberately kept out of version control; `make quickstart` reproduces both from scratch.

---

## Known Limitations

- **No incident awareness.** Accidents, roadworks and one-off closures are invisible to the model, which forecasts the *typical* day for a given date.
- **School-holiday calendar is hardcoded through 2026.** Forecasts beyond that degrade gradually rather than failing.
- **No growth trend.** 2026 is assumed to resemble 2023–2025; no traffic-growth or population term is modelled.
- **Unequal slot lengths.** Slot 1 spans six hours and slot 6 only two, so raw counts are not directly comparable across slots. Ratio normalisation compensates, but uniform four-hour slots would be cleaner.
- **Weather is climatological, not forecast.** `clim_air_temp_c` is a monthly average, not a real prediction — a genuine forecast feed would likely improve winter accuracy.

---

## License

MIT — see [LICENSE](LICENSE).
