# TUM Science Hackathon 2026 — Automated Traffic Forecasting

**Challenge:** Automated Traffic Forecasting for Alpine Holiday Corridors A8 East & A93 South  
**Host:** Die Autobahn GmbH des Bundes  
**Version:** medium

Color-coded daily traffic forecasts (green → dark red) for up to one year ahead — replacing the manual expert-driven Traffic Calendar with a data-driven ML system.

---

## What's Built

| Component | Status | Description |
|-----------|--------|-------------|
| ML model | ✅ Done | GradientBoosting classifier + regressor, 25 features, ratio-based categories |
| Backend API | ✅ Done | FastAPI — `/forecast`, `/calendar`, `/peak-days`, `/recommendations`, `/historical` |
| Frontend | ✅ Done | React/TanStack calendar UI, fetches live from backend |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

Download the pre-trained model (2.9 MB):

```bash
pip install gdown
gdown "1mThbkhkYqZW3lDtkB7e5-t2w5yGNlqGB" -O models/prediction_pipeline.joblib
```

Or manually from: **https://drive.google.com/file/d/1mThbkhkYqZW3lDtkB7e5-t2w5yGNlqGB/view**

Start the backend:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m uvicorn backend.app.main:app --port 8000
```

Verify: `curl http://localhost:8000/api/health`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

---

## ML Model — How It Works In Detail

### Step 1: Raw Data

Highway loop detectors on A8 and A93 record vehicle counts every hour (`kfz_h` = vehicles/hour, `sv_h` = heavy trucks/hour). The dataset covers **2023–2025**, from 12 detector stations across two corridors and two directions.

Raw data is cleaned: negative counts removed, outliers above the 99.9th percentile dropped, files from multiple detector stations merged.

### Step 2: Aggregation into Time Slots

Each day is divided into **6 time slots**:

| Slot | Window | Duration |
|------|--------|----------|
| 1 | 00:00–06:00 | 6 h (night) |
| 2 | 06:00–10:00 | 4 h |
| 3 | 10:00–14:00 | 4 h |
| 4 | 14:00–18:00 | 4 h |
| 5 | 18:00–22:00 | 4 h |
| 6 | 22:00–24:00 | 2 h (late night) |

Hourly vehicle counts are **summed** within each slot (not averaged), then averaged across detector stations on the same corridor/direction. Incomplete slots (fewer than 75% of expected hours recorded) are dropped.

### Step 3: Historical Baselines

Three sets of historical averages are computed from the training data and stored in the model bundle:

- **`by_dow_slot`**: average vehicles per (corridor, direction, day-of-week, slot) — weekly rhythm
- **`by_month_slot`**: average vehicles per (corridor, direction, month, slot) — seasonality
- **`by_slot`**: average vehicles per (corridor, direction, slot) across ALL months — annual average per slot

### Step 4: Traffic Category Labels

Each training row is assigned a category 1–5 using **ratio-based thresholds**:

```
ratio = kfz_h_slot / hist_kfz_month_slot
```

This compares each slot's actual count to the historical monthly average for that (corridor, direction, month, slot). A ratio of 1.0 means exactly average for that time of year. Thresholds are computed from the distribution of all ratios across the full training set:

| Category | Color | Threshold | Meaning |
|----------|-------|-----------|---------|
| 1 | 🟢 Green | ratio < 0.955 | Below average for this month/slot |
| 2 | 🟡 Yellow | 0.955 – 1.077 | Slightly above average |
| 3 | 🟠 Orange | 1.077 – 1.273 | Noticeably above average |
| 4 | 🔴 Red | 1.273 – 1.615 | Top 12% of days |
| 5 | ⬛ Dark red | > 1.615 | Top 3% — extreme days |

Because thresholds are computed on ratios rather than raw counts, a night slot with 4,000 vehicles and a daytime slot with 10,000 vehicles are fairly compared — each is judged relative to what is normal for that exact time of day and month.

### Step 5: The 25 Features

For every future date and slot, 25 features are computed from the calendar alone — no real-time sensor data needed:

**Calendar basics**
| Feature | Description |
|---------|-------------|
| `month` | 1–12 |
| `day_of_week` | 0 = Monday, 6 = Sunday |
| `week_of_year` | 1–53 |
| `time_slot` | 1–6 |
| `is_weekend` | 1 if Saturday or Sunday |

**Public holidays**
| Feature | Description |
|---------|-------------|
| `is_public_holiday_de` | German national holiday |
| `is_public_holiday_bavaria` | Bavarian-specific holiday |
| `is_bridge_day` | Workday between a holiday and a weekend (Brückentag) |
| `is_long_weekend` | Part of a 3+ consecutive day off block |

**School holidays**
| Feature | Description |
|---------|-------------|
| `is_school_holiday_bavaria` | Bavarian school holidays active |
| `is_school_holiday_bw` | Baden-Württemberg school holidays active |
| `school_holiday_overlap` | Sum of the two (0, 1, or 2) — overlap = extreme departure pressure |
| `days_until_school_holiday` | Days until next Bavarian holiday starts (capped at 30) |
| `days_since_school_holiday` | Days since last one ended (capped at 30) |

**Seasons and events**
| Feature | Description |
|---------|-------------|
| `is_summer_season` | June–September |
| `is_winter_sports_season` | December–March |
| `is_easter_period` | ±4 days around Easter Sunday |
| `is_christmas_period` | 22 Dec – 6 Jan |

**Road context**
| Feature | Description |
|---------|-------------|
| `is_outbound` | 1 = toward Salzburg/Kufstein |
| `is_a93` | 1 = A93 corridor |

**Historical baselines** (from model bundle)
| Feature | Description |
|---------|-------------|
| `hist_kfz_dow_slot` | Average vehicles for this (corridor, direction, day-of-week, slot) |
| `hist_kfz_month_slot` | Average vehicles for this (corridor, direction, month, slot) |
| `hist_sv_share` | Historical heavy truck share (~8%) |

**Weather proxy**
| Feature | Description |
|---------|-------------|
| `clim_air_temp_c` | Monthly average air temperature (Jan=1°C, Jul=21°C) |
| `is_frost_risk_month` | 1 for December, January, February, November |

### Step 6: Training

Two **Gradient Boosting** models trained on ~25,700 rows (3 years × 4 corridor/direction combos × ~365 days × 6 slots):

**Classifier** → predicts traffic category 1–5  
**Regressor** → predicts raw vehicle count (for display)

Both use a `StandardScaler → GradientBoostingClassifier/Regressor` scikit-learn pipeline with 300 estimators, max depth 5, learning rate 0.05, subsample 0.8. Training split: 80/20 stratified by category. Regressor achieves MAE ~480 vehicles, R² = 0.948.

Feature importance: `hist_kfz_month_slot` (62%) and `hist_kfz_dow_slot` (28%) dominate — the remaining 23 features provide fine-grained corrections for holidays, school breaks, and events.

Everything is packed into a single `models/prediction_pipeline.joblib` bundle containing both pipelines, all baselines, and the ratio thresholds.

### Step 7: Inference (Runtime)

When a user searches a date range:

1. For each (date, slot): build 25 features from the calendar
2. Regressor predicts raw vehicle count
3. Look up `hist_kfz_month_slot` baseline from the bundle
4. `ratio = predicted_count / hist_kfz_month_slot`
5. Compare ratio against stored thresholds → category 1–5
6. Daily category = average of 6 slot categories, rounded
7. Return color + vehicle count to frontend

---

## Known Limitations and Proposed Improvements

### Issue: Summer months appear low traffic

The current normalization uses `hist_kfz_month_slot` — the monthly average for that slot. This means an "average August afternoon" always appears green/yellow because it is being compared only to other August afternoons. As a result, summer and winter months look equally busy in the color scale, even though July/August carry 30–40% more vehicles than November/December.

**Proposed fix:** Normalize by `hist_kfz_slot` — the **annual** average for that slot across all months. Then:
- An August afternoon (11,000 vehicles) vs annual average (9,500) → ratio 1.16 → orange ✓
- A November afternoon (8,000 vehicles) vs annual average (9,500) → ratio 0.84 → green ✓

This change would make summer genuinely red/orange across the board, accurately reflecting that it is the busiest period of year in absolute terms.

### Other known limitations

- No awareness of accidents, road closures, or large one-off events
- School holiday calendar hardcoded through 2026; forecasts beyond that degrade gracefully
- No economic growth or population trend modelling — 2026 assumed to mirror 2023–2025
- Unequal slot sizes (slot 1 = 6 h, slot 6 = 2 h) mean raw vehicle counts are not directly comparable across slots; ratio normalization mitigates this but equal 4-hour slots would be cleaner

---

## Project Structure

```
TUM-Hackathon/
├── backend/
│   ├── app/
│   │   ├── main.py                        ← FastAPI entry point
│   │   ├── api/routes.py                  ← All API endpoints
│   │   └── processors/
│   │       ├── traffic_analyzer.py        ← Forecast engine
│   │       └── feature_builder.py         ← Shared feature engineering
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── routes/index.tsx               ← Main calendar page
│   │   └── lib/traffic.ts                 ← API client + types
│   └── package.json
├── data/
│   ├── raw/                               ← Original CSVs (NOT in git)
│   └── processed/
│       ├── historical_A8E_outbound.json
│       ├── historical_A8E_inbound.json
│       ├── historical_A93S_outbound.json
│       └── historical_A93S_inbound.json
├── models/
│   └── prediction_pipeline.joblib         ← Trained model bundle
├── scripts/
│   ├── clean_data.py                      ← Step 1
│   ├── build_features.py                  ← Step 2
│   ├── train_model.py                     ← Step 3
│   └── process_historical.py              ← Step 4
└── docs/
    ├── API.md
    ├── MODEL_CONTRACT.md
    ├── DATA_STRUCTURE.md
    └── explanation.md
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check + model status |
| `POST` | `/api/forecast` | Forecast for a corridor/direction/date range |
| `GET` | `/api/calendar` | Full year grouped by month |
| `GET` | `/api/peak-days` | Top N highest-traffic days |
| `POST` | `/api/recommendations` | User-type-tailored travel advice |
| `GET` | `/api/historical` | Real 2023–2025 measurements |

---

## Retrain from Scratch (optional)

Requires the raw dataset from Die Autobahn GmbH:

```bash
pip install gdown
gdown "1Z1Icu2xuuuYB9pNRG6fOnGBT5MjY3wPC" -O hackathon-dataset.zip
unzip -o hackathon-dataset.zip -d .

PYTHONPATH=backend python3 scripts/clean_data.py
PYTHONPATH=backend python3 scripts/build_features.py
PYTHONPATH=backend python3 scripts/train_model.py
PYTHONPATH=backend python3 scripts/process_historical.py
```

---

## License

MIT
