# Data Structure — Traffic Forecasting (A8 East / A93 South)

## Directory Layout

```
data/
├── raw/                               ← Original files from Die Autobahn GmbH (NOT in git)
│   ├── FG1_Lang_*_agg1h_*.csv        ← 12 hourly traffic detector files (PRIMARY)
│   ├── FG1_Kurz_*_agg1min_*.csv      ← 12 minute-level files (supplementary, 80–110 MB each)
│   ├── A8_A93_MQ_locations.csv       ← Detector GPS coordinates and corridor mapping
│   ├── FG3_WUD_FBT_*_agg1min_*.csv  ← Road surface temperature (3 yearly files)
│   ├── FG3_WUD_LT_*_agg1min_*.csv   ← Air temperature (3 yearly files)
│   └── Location_LT_und_FBT_AD_Rosenheim_B15n.csv ← Weather station metadata
├── processed/                         ← Pipeline outputs (NOT in git)
│   ├── cleaned_traffic_hourly.csv    ← After clean_data.py
│   ├── cleaned_weather_hourly.csv    ← After clean_data.py (optional)
│   ├── features.csv                  ← After build_features.py (model-ready)
│   ├── category_thresholds.json      ← Percentile thresholds for categories 1–5
│   └── baselines.json                ← Historical averages for future-date inference
└── examples/                          ← Small representative samples (can commit)
```

---

## Primary Dataset: Hourly Traffic Counts (`FG1_Lang_*`)

### Filename Pattern

```
FG1_Lang_{numeric_id}_{site_name},{DE_channels}_agg1h_2023-01-01_bis_2026-01-01.csv
```

### The 12 Files and Their Corridor/Direction

| File (site portion) | Road | Direction | Confidence |
|---------------------|------|-----------|------------|
| `9171_MQB25_Mch_H,DE33,34,35,36` | A8-Ost | **inbound** (→ Munich) | ✅ High |
| `9171_MQQ37_Sbg_H,DE1,2,3,4` | A8-Ost | **outbound** (→ Salzburg) | ✅ High |
| `9192_MQQ209_Mch_H,DE33,34` | A8-Ost | **inbound** | ✅ High |
| `9192_MQQ213_Sbg_H,DE1,2` | A8-Ost | **outbound** | ✅ High |
| `9194_MQQ245_Mch_H,DE33,34` | A8-Ost | **inbound** | ✅ High |
| `9194_MQQ245_Sbg_H,DE1,2` | A8-Ost | **outbound** | ✅ High |
| `9190_MQDZ_AD Inntal_(S)_Kff,DE33,34` | A93-Süd | **outbound** (→ Kufstein) | ✅ Confirmed (organizers) |
| `9190_MQDZ_AD Inntal_(S)_Ro,DE1,2` | A93-Süd | **inbound** (→ Rosenheim) | ✅ Confirmed (organizers) |
| `9191_MQDZ_Kiefersfelden_(S)_Kff,DE33,34` | A93-Süd | **outbound** | ✅ Confirmed (organizers) |
| `9191_MQDZ_Kiefersfelden_(S)_Ro,DE1,2` | A93-Süd | **inbound** | ✅ Confirmed (organizers) |
| `9629_MQ_Gletschergarten_Kff,DE33,34` | A93-Süd | **outbound** | ✅ Confirmed (organizers) |
| `9629_MQ_Gletschergarten_Ro,DE1,2` | A93-Süd | **inbound** | ✅ Confirmed (organizers) |

**A93 South — confirmed by organizers:** `_Kff` = toward Kufstein (Austria, outbound); `_Ro` = toward Rosenheim (Germany, inbound). Geographic order by BAB-Km: AD Inntal (km 1.9) → Gletschergarten (km 12.3) → Kiefersfelden (km 25.1).

### Parsing Quirks (critical — do not skip)

| Issue | Solution |
|-------|----------|
| Encoding: UTF-8 with BOM | `pd.read_csv(..., encoding="utf-8-sig")` |
| Delimiter: semicolon | `sep=";"` |
| Header trailing junk: `sv_h,,,,` | `df.columns = [c.split(",")[0] for c in df.columns]` |
| Date format: `DD.MM.YYYY` | `pd.to_datetime(df["datum"], format="%d.%m.%Y")` |
| Line endings: CRLF | Handled automatically by pandas |

### Columns

| Column | Type | Meaning |
|--------|------|---------|
| `devices` | string | Detector ID (site name + DE channels) — repeats per row |
| `datum` | string → date | Date in `DD.MM.YYYY` format |
| `t_start` | string → time | Hourly interval start `HH:MM:SS` |
| `wochentag` | int | Day of week **ISO: Mon=1, Sun=7** |
| `tagestyp` | string | **Day type — 3 codes (verified on full 3-year file):** `w` = Werktag (normal working weekday); `u` = school-holiday-period weekday (~91% match Bavarian holiday ranges); `s` = Sonn-/Feiertag (every Sunday + every Bavarian public holiday regardless of weekday) |
| `kfz_h` | int | **Total vehicles per hour** — primary target variable. Never legitimately 0; null means sensor outage |
| `sv_h` | int | **Heavy vehicles per hour** — SV = trucks >3.5t + lorries + buses; excludes cars-with-trailer. Nulls always co-occur with null `kfz_h` (verified). Do NOT fill with 0 — null = outage, not zero traffic |

### Loading Code

```python
import pandas as pd

def load_hourly_file(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    df.columns = [c.split(",")[0] for c in df.columns]   # strip header junk
    df["datum"] = pd.to_datetime(df["datum"], format="%d.%m.%Y")
    df["timestamp"] = df["datum"] + pd.to_timedelta(df["t_start"])
    return df.drop(columns=["datum", "t_start"]).sort_values("timestamp")
```

### Sanity Check Shape (verified on full MQB25 file)
- Exactly 24 rows/day, every day — no missing rows, no duplicates
- 80 null rows (~0.3%) across 3 years: sensor outages + DST phantom hours
- DST: spring-forward hour has null values (placeholder row kept); fall-back does NOT add a 25th row
- kfz_h range: 72–6,941; sv_h range: 8–1,034 (no zeros, no negatives)
- Sunday/holiday midday peak: ~5,000 veh/h on A8E; overnight: ~200–600 veh/h

---

## Vehicle Classification (TLS Standard)

| Column | TLS concept | What it includes |
|--------|-------------|-----------------|
| `kfz_h` (hourly) | **Kfz** — all motor vehicles | Everything |
| `sv_h` (hourly) | **SV** — Schwerverkehr | Trucks >3.5t (with/without trailer) + articulated lorries + **buses** |
| `q_kfz` (minute) | Kfz total | Same as kfz_h (verified: `sum(q_kfz)` per hour == `kfz_h` exactly) |
| `q_lkw` (minute) | **LKW-ähnlich** = SV + cars-with-trailer | **Broader than `sv_h`** — do not equate |
| `q_pkw` (minute) | **Pkw-ähnlich** = cars/vans/motorcycles WITHOUT trailer | `q_kfz − q_lkw` exactly |

**Key:** `q_lkw − sv_h` ≈ cars-with-trailer count. This difference spikes during leisure travel (caravans on holiday weekends) — a free bonus feature for holiday pattern detection.

---

## Minute-Level Traffic (`FG1_Kurz_*`)

Same 12 sites, same date range, finer resolution. **80–110 MB per file (~1.1 GB total).**

| Difference from hourly | Detail |
|------------------------|--------|
| Filename prefix | `FG1_Kurz_` (no numeric ID prefix in the site name) |
| `devices` column | No leading `9171_` etc. — strip this when joining to hourly |
| Extra column | `v_kfz` = average speed (km/h); **null when `q_kfz == 0`** (no vehicles → no speed) |
| No `tagestyp` column | Absent in minute files |
| Size | ~1.55M rows per file |

**Recommended handling:** Aggregate to hourly immediately after loading (strategy A):

```python
def load_and_aggregate_to_hourly(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", chunksize=200_000)
    # Process in chunks to avoid RAM exhaustion
    frames = []
    for chunk in df:
        chunk.columns = [c.split(",")[0] for c in chunk.columns]
        chunk["datum"] = pd.to_datetime(chunk["datum"], format="%d.%m.%Y")
        chunk["timestamp"] = chunk["datum"] + pd.to_timedelta(chunk["t_start"])
        chunk = chunk.set_index("timestamp")
        hourly = chunk.resample("1h").agg(
            q_kfz=("q_kfz", "sum"),
            q_lkw=("q_lkw", "sum"),
            v_kfz_mean=("v_kfz", "mean"),
        )
        frames.append(hourly)
    return pd.concat(frames).groupby(level=0).sum()
```

---

## Temperature Data (`FG3_WUD_FBT/LT_*`)

Single station: **Rosenheim B15n, A8-Ost (Salzburg direction), km 54.6**

| File pattern | Measurement | Unit |
|-------------|-------------|------|
| `FG3_WUD_FBT_*_agg1min_*.csv` | Road surface temperature | °C |
| `FG3_WUD_LT_*_agg1min_*.csv` | Air temperature | °C |

Six files total: 2 types × 3 yearly files (2023, 2024, 2025).

**Format:** `sep=";"`, no BOM, columns: `t_start` (ISO datetime), value column (float °C, may be named `fbt` in both file types — check first).

```python
df = pd.read_csv(path, sep=";")
df["t_start"] = pd.to_datetime(df["t_start"])
```

**Coverage:** One station on A8 East only. Used as a proxy for corridor-wide weather. For long-term (2026) forecasts, use historical monthly averages from 2023–2025.

---

## Detector Locations (`A8_A93_MQ_locations.csv`)

```python
loc = pd.read_csv("A8_A93_MQ_locations.csv", sep=";", decimal=",")
```

| Column | Meaning |
|--------|---------|
| `site` | Parent station ID |
| `unit` | Specific lane detector within that site |
| `Funktionsgruppe` | `1` = traffic detector, `3` = weather station |
| `Strecke` | Corridor + direction: `A8-Ost_Mch`, `A8-Ost_Sbg`, `A93-Sued_Ros`, `A93-Sued_Kff` |
| `BAB-Km` | Motorway kilometer marker |
| `Longitude_WGS84` / `Latitude_WGS84` | GPS coordinates (decimal separator = `,`) |

**A93S confirmed device IDs:** AD Inntal = `81389190`, Gletschergarten = `82389192`, Kiefersfelden = `83399191`. Do NOT join on numeric filename prefix — match by road segment name + BAB-Km.

---

## Processing Pipeline

```
data/raw/FG1_Lang_*_agg1h_*.csv  (12 files)
    ↓  python scripts/clean_data.py
        • Load all 12 files: UTF-8-BOM, sep=";", fix header, parse datum+t_start → timestamp
        • Tag each row: corridor (A8E/A93S), direction (outbound/inbound)
        • Drop null kfz_h rows (sensor outages + DST phantom hours, ~0.3%)
        • sv_h nulls always co-occur with kfz_h nulls — handled by dropna above
data/processed/cleaned_traffic_hourly.csv

    ↓  python scripts/build_features.py
        • Aggregate hours → 6 time slots per (date, corridor, direction)
        • Average across detector sites in same corridor/direction
        • Add calendar features (month, day_of_week, is_weekend, is_public_holiday)
        • Add Bavarian + BW school holiday features (hardcoded 2023–2026)
        • Compute traffic_category 1–5 via percentile thresholds
        • Compute historical baselines for future-date inference
data/processed/features.csv
data/processed/category_thresholds.json
data/processed/baselines.json

    ↓  python scripts/train_model.py
        • Train GradientBoostingClassifier → traffic_category 1–5
        • Train GradientBoostingRegressor → kfz_h_slot (total vehicles per slot)
        • Package with baselines + thresholds into model bundle
models/prediction_pipeline.joblib
```

---

## Time Slot Aggregation

Hours are grouped into 6 daily slots. `kfz_h` values are **summed** within each slot (total vehicles, not rate):

| Slot | Hours | Duration | Notes |
|------|-------|----------|-------|
| 1 | 00:00–06:00 | 6 h | Night |
| 2 | 06:00–10:00 | 4 h | Morning rush |
| 3 | 10:00–14:00 | 4 h | Midday peak (holiday departure) |
| 4 | 14:00–18:00 | 4 h | Afternoon (return traffic) |
| 5 | 18:00–22:00 | 4 h | Evening |
| 6 | 22:00–24:00 | 2 h | Late night |

---

## Traffic Category Thresholds

Derived per `(corridor, direction, time_slot)` group using percentiles of historical `kfz_h_slot`:

| Category | Percentile range | Color | Meaning |
|----------|-----------------|-------|---------|
| 1 | < 40th | Green | Free-flowing |
| 2 | 40th–60th | Yellow | Moderate |
| 3 | 60th–80th | Orange | Increased |
| 4 | 80th–95th | Red | Heavy |
| 5 | > 95th | Dark red | Critical / congestion risk |

Stored in `data/processed/category_thresholds.json` and packed into the `.joblib` bundle.
