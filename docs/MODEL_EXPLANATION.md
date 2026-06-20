# Traffic Prediction Model — How It Works & How the 4 CSV Files Are Generated

This document explains, end to end, how the traffic forecasting model in this repository
works and exactly how it produces the four CSV files the frontend consumes:

- `A8easttraffic.csv`   — A8 corridor, **East / outbound** (Munich → Salzburg)
- `A8westtraffic.csv`   — A8 corridor, **West / inbound** (→ Munich)
- `A93southtraffic.csv` — A93 corridor, **South / outbound** (→ Kufstein)
- `A93northtraffic.csv` — A93 corridor, **North / inbound** (→ Rosenheim)

---

## 1. The big picture

```
data/raw/          scripts/                data/processed/          models/                       scripts/                data/export/
(CSV, not in git)  clean_data.py     →     cleaned_traffic_hourly   train_model.py  →  bundle  →  export_frontend_csv.py  →  A8easttraffic.csv
                   build_features.py →     features.csv                .joblib                                                A8westtraffic.csv
                                           *_thresholds.json                                                                  A93southtraffic.csv
                                           baselines.json                                                                     A93northtraffic.csv
```

The system is built around **one key design decision**:

> A single regression model predicts the **number of vehicles** in a time slot.
> The traffic **colour/category (1–5)** is *not* predicted directly — it is **derived**
> from the predicted vehicle count using percentile thresholds.

This guarantees the colour shown to the user is always consistent with the vehicle
count shown next to it, and it lets us tune the colour distribution (how many green vs.
red days) independently of the model.

---

## 2. What the model actually is

The trained artifact `models/prediction_pipeline.joblib` is **not a bare estimator** — it
is a **bundle dict** with these keys (see `scripts/train_model.py`):

| Key | Type | Purpose |
|-----|------|---------|
| `regressor` | sklearn `Pipeline` (`StandardScaler` → `GradientBoostingRegressor`) | Predicts slot **volume** (vehicles in a slot) |
| `slot_thresholds` | `{ "A8E\|outbound\|4": [p40, p60, p80, p95], ... }` | Per-slot volume → category 1–5 |
| `daily_thresholds` | `{ "A8E\|outbound": [p40, p60, p80, p95], ... }` | Per-day **total** volume → daily category |
| `baselines` | dict of historical averages | Feed historical features when forecasting future dates |
| `training_info` | metadata | Date range, sample count, year-ahead eval metrics |

The regressor is a **`GradientBoostingRegressor`** (`n_estimators=400`, `max_depth=5`,
`learning_rate=0.05`, `subsample=0.8`) wrapped in a `StandardScaler`. Its target is
`kfz_h_slot` — the total vehicle count in one time slot. It does **not** see the corridor
or direction as strings; those are encoded as the binary flags `is_outbound` and `is_a93`.

If the `.joblib` is missing, `traffic_analyzer.py` logs a warning and serves
**deterministic mock data** (`_mock_predict`) so the API and CSV export still work.

---

## 3. The features the model sees (25 columns)

The single source of truth is `FEATURE_COLUMNS` in
`backend/app/processors/feature_builder.py`. The same module is imported by **both** the
training scripts and the live inference path, so training and inference can never drift.

The 25 features fall into four groups:

**Calendar** (computed purely from the date)
`month`, `day_of_week`, `week_of_year`, `time_slot`, `is_weekend`

**Holidays & special periods** (hardcoded German/Bavarian calendars, 2023–2026)
`is_public_holiday_de`, `is_public_holiday_bavaria`, `is_bridge_day`, `is_long_weekend`,
`is_school_holiday_bavaria`, `is_school_holiday_bw`, `school_holiday_overlap`,
`days_until_school_holiday`, `days_since_school_holiday`, `is_summer_season`,
`is_winter_sports_season`, `is_easter_period`, `is_christmas_period`

> Note: Bavaria **and** Baden-Württemberg school holidays are both tracked, because when
> they overlap the departure pressure on these Alpine corridors is much higher.

**Direction & corridor** (binary flags)
`is_outbound`, `is_a93`

**Historical baselines** (looked up from `baselines`, the model's "memory" of the past)
`hist_kfz_dow_slot` (avg volume for this corridor/direction/weekday/slot),
`hist_kfz_month_slot` (avg for this month/slot), `hist_sv_share` (heavy-vehicle share),
`clim_air_temp_c` (climatological air temp), `is_frost_risk_month`

These historical baselines are what let the model forecast a date one year ahead: even
for a future date it has never seen, it knows the typical volume for "A8E outbound,
Saturday, slot 4, in August".

---

## 4. How a model is built (the offline pipeline)

These scripts are run **once**, in order, from the repo root. They are never run inside
the app.

### Step 1 — `scripts/clean_data.py`
Reads the raw semicolon-separated detector CSVs from `data/raw/` and produces
`data/processed/cleaned_traffic_hourly.csv` (hourly vehicle counts per detector site,
tagged with corridor + direction) and optionally `cleaned_weather_hourly.csv`.

### Step 2 — `scripts/build_features.py`
1. **Aggregate hourly → 6 time slots.** Hours are bucketed into the 6 slots, vehicle
   counts are *summed* within each slot window (slots have different lengths), then
   *averaged* across detector sites for the same corridor/direction/date/slot. Slots with
   too many missing hours (<75% coverage) are dropped.

   | Slot | Hours | Label |
   |------|-------|-------|
   | 1 | 00–06 | overnight |
   | 2 | 06–10 | morning |
   | 3 | 10–14 | midday |
   | 4 | 14–18 | afternoon |
   | 5 | 18–22 | evening |
   | 6 | 22–24 | late night |

2. **Compute percentile thresholds.** For every `corridor|direction|slot` it takes the
   p40/p60/p80/p95 of historical slot volume → `category_thresholds.json`. It does the
   same on **daily totals** per `corridor|direction` → `daily_thresholds.json`. These
   percentiles define the category boundaries (see §6).

3. **Add calendar/holiday features** and **compute historical baselines**
   (`baselines.json`) — the per-weekday/per-month averages described above.

4. Writes `features.csv`: one row per `(date, time_slot, corridor, direction)` with the
   target `kfz_h_slot` plus all 25 feature columns.

### Step 3 — `scripts/train_model.py`
1. **Honest year-ahead evaluation** (`evaluate_temporal`): trains on the earliest years,
   tests on the *last* year only — this simulates real "predict next year" use and reports
   volume MAE/R² and category accuracy.
2. **Trains the final regressor on all data** (`regressor.fit(df[FEATURE_COLUMNS],
   df["kfz_h_slot"])`).
3. **Packs the bundle** (regressor + thresholds + baselines + training_info) and saves it
   with `joblib.dump(..., compress=3)` → `models/prediction_pipeline.joblib`.

---

## 5. How a forecast is produced at runtime

`backend/app/processors/traffic_analyzer.py` (`TrafficAnalyzer`) is a lazy singleton that
loads the bundle once. The core method is `forecast(corridor, direction, date_from,
date_to)`, which loops over every day and every slot:

For **each slot of each day** (`_predict_slot`):
1. `build_feature_row(date, slot, corridor, direction, baselines)` builds the 25-feature
   row (calendar features computed live, historical features looked up from baselines).
2. The row is passed to the regressor → predicted **volume** (clamped to ≥ 0).
3. `assign_category(volume, slot_thresholds)` → slot **category 1–5**.
4. `category_confidence(...)` scores how far the volume sits from a category boundary,
   and `build_explanation(...)` produces human-readable reasons ("Bavaria school holidays
   active", "Saturday outbound — peak departure", etc.).

For **each day**:
- The 6 slot volumes are **summed** into a daily total.
- The daily category comes from the **daily total vs. `daily_thresholds`** — *not* the max
  of the slot categories. (Max-of-slots over-inflated the count of red days; using the
  daily total gives a realistic ~40/20/20/15/5 spread.)

The result is a list of per-day dicts, each holding a nested `time_slots[]` array.

---

## 6. From vehicle count to colour (the category mapping)

`assign_category(volume, thresholds)` simply counts how many thresholds the volume meets
or exceeds:

```
category = 1 + (#thresholds the volume is ≥)
```

With thresholds `[p40, p60, p80, p95]`:

| Volume range | Category | Colour (backend) | Frontend level (CSV) |
|--------------|----------|------------------|----------------------|
| below p40 | 1 | green   | `low` |
| p40–p60   | 2 | yellow  | `increased` |
| p60–p80   | 3 | orange  | `increased` ⟵ folded |
| p80–p95   | 4 | red     | `heavy` |
| above p95 | 5 | dark_red| `extreme` |

The percentile-based design means roughly 40% of slots are green, 20% yellow, 20% orange,
15% red, 5% dark red — by construction.

> **The model has 5 internal categories, but the CSV exposes only 4 levels.** The frontend
> works with exactly four colours, so the exporter folds category 3 ("moderate") into
> `increased` (see §7). Internally the model and the JSON API still use all 5 categories;
> the collapse to 4 happens only at CSV-export time.

---

## 7. How the 4 CSV files are generated

The exporter is **`scripts/export_frontend_csv.py`**. Run it after the model exists:

```bash
PYTHONPATH=backend backend/.venv/bin/python scripts/export_frontend_csv.py
```

It calls the **same** `TrafficAnalyzer.forecast()` the API uses, so the CSV files and the
live API always agree.

### Mapping files → (corridor, direction)

| File | Corridor | Direction |
|------|----------|-----------|
| `A8easttraffic.csv`   | `A8E`  | `outbound` |
| `A8westtraffic.csv`   | `A8E`  | `inbound` |
| `A93southtraffic.csv` | `A93S` | `outbound` |
| `A93northtraffic.csv` | `A93S` | `inbound` |

### Process per file
1. Forecast a horizon of **exactly one year starting today** (`DATE_FROM = date.today()`,
   `DATE_TO` = the day before the same date next year → 365 days, 366 in a leap year).
   Because `forecast()` caps a single call at 366 days, the exporter splits the range into
   ≤365-day chunks (`_forecast_range`) and concatenates.
2. For each day, pull the 6 slot categories (`1 part` … `6 part`).
3. Take the **daily `traffic` column** straight from the analyzer's `daily_category`
   (`day["daily_category"]`) — the **daily-total volume vs. `daily_thresholds`** rule
   from §5.

   > ✅ The CSV daily value and the API's `daily_category` are now the **same value**,
   > computed once in `traffic_analyzer.forecast()`. This is the category that best
   > represents how heavy the whole day is: it is driven by the day's *total* volume, so a
   > day with one sharp peak slot isn't mislabelled as heavy, and a day that is busy across
   > many slots isn't understated.
4. Map each category to one of the **4 frontend levels** via `CATEGORY_TO_LEVEL`
   (`1=low, 2=increased, 3=increased, 4=heavy, 5=extreme`). Category 3 folds into
   `increased` so the CSV only ever contains `low`, `increased`, `heavy`, `extreme`.
5. Format the date as `DD.MM.YYYY` and write the row.

### Output format

```
day,traffic,1 part,2 part,3 part,4 part,5 part,6 part
20.06.2026,heavy,heavy,heavy,heavy,increased,increased,heavy
21.06.2026,increased,heavy,increased,heavy,increased,increased,increased
```

- `day` — date, `DD.MM.YYYY`
- `traffic` — overall daily level (analyzer `daily_category`: daily total vs daily thresholds)
- `1 part` … `6 part` — level for each of the 6 time slots
- every cell is one of the 4 levels: `low`, `increased`, `heavy`, `extreme`

Files are written to `data/export/`. The committed reference copies live in
`data/examples/`. (The frontend lives in a separate Lovable project and is no longer part
of this repo; it fetches the CSVs from the backend's `/api/data/<file>.csv` endpoint.)

---

## 8. Why a forecast for a specific day comes out the way it does

A day lands in a high category because of features the model learned to associate with
high volume — surfaced in the `explanation` field. Strong drivers (see feature importance
in `train_model.py` output and the holiday logic in `feature_builder.py`):

- **School holidays** (especially Bavaria + Baden-Württemberg overlapping)
- **Summer season** (Jun–Sep tourism peak)
- **Saturdays outbound** (departure peak) and **Sundays inbound** (return peak)
- **Bridge days / long weekends** around public holidays
- **Easter and Christmas** travel periods
- The **historical baseline** for that corridor/direction/weekday/month/slot

---

## 9. One-line summary

> Hourly detector counts are aggregated to 6 daily slots, percentile thresholds define the
> 5 colour categories, and a gradient-boosting regressor learns slot **volume** from
> calendar/holiday/baseline features. To produce the 4 frontend CSVs,
> `export_frontend_csv.py` forecasts a year of slot volumes per corridor/direction,
> converts each volume to a 1–5 category via the thresholds, maps categories to
> `low…extreme` strings, and writes one row per day with the 6 slot levels plus a daily
> level taken from the analyzer's `daily_category` (daily total vs daily thresholds) so the
> CSV and the API always agree.
