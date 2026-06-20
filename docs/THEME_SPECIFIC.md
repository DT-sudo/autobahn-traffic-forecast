# Theme-Specific Details — Traffic Forecasting

**Challenge:** Automated Traffic Forecasting for Alpine Holiday Corridors A8 East & A93 South
**Host:** Die Autobahn GmbH des Bundes

---

## Problem Statement

Die Autobahn GmbH currently produces a manual Traffic Calendar (Fahrkalender) — a color-coded (green → dark red) forward-looking assessment of expected traffic conditions on A8 East and A93 South. This manual process is time-consuming, hard to scale, and cannot easily generate forecasts more than ~2 months ahead.

**We automate it:** given historical traffic detector data and calendar/holiday features, the system generates daily traffic forecasts with time-slot granularity for up to one year ahead — replacing expert judgment with a reproducible, data-driven model.

**Target users:**
- Private travelers / tourists — when to leave to avoid congestion
- Local residents — when to avoid regional roads
- Logistics / freight / bus companies — shift departure windows
- Tourism businesses (hotels, ski resorts) — predict arrival peaks
- Traffic management authorities — explainable, reproducible forecasts

---

## Corridors and Scope

| Corridor | Route | Key destinations |
|----------|-------|-----------------|
| A8 East | Munich → Salzburg (border) | Austria, Italy, Croatia, Slovenia |
| A93 South | Munich → Kufstein (border) | Innsbruck, Brenner, Tyrol |

Both directions:
- **Outbound** — toward Austria / Alps / south-east Europe (peaks at holiday start, Friday evenings)
- **Inbound** — toward Germany (peaks at holiday end, Sunday afternoons)

---

## Dataset

### Source

Provided by Die Autobahn GmbH des Bundes. Place files in `data/raw/` (never committed to git).

### Files

| File | Content |
|------|---------|
| `traffic_hourly.csv` | Hourly vehicle counts per detector |
| `traffic_minute.csv` | Per-minute vehicle counts per detector |
| `detector_locations.csv` / PDF | GPS coordinates, corridor, direction, lane info |
| `vehicle_classes.csv` / PDF | Vehicle class definitions (cars vs. heavy vehicles) |
| `surface_temp.csv` | Road surface temperature readings |
| `heatmaps/` | PNG heatmaps of traffic per detector per hour |
| `current_predictions.pdf` | Existing manual Fahrkalender (benchmark) |

### Key Columns (hourly traffic CSV)

| Column | Type | Description |
|--------|------|-------------|
| `datetime` | datetime | Timestamp (hourly) |
| `detector_id` | string | Unique detector identifier |
| `corridor` | string | `"A8E"` or `"A93S"` |
| `direction` | string | `"outbound"` or `"inbound"` |
| `vehicle_count` | int | Vehicles passing per hour |
| `vehicle_class` | string | `"car"`, `"truck"`, `"bus"`, etc. |
| `speed_avg_kmh` | float | Average speed (km/h) |
| `lane_id` | int | Lane number |

### Google Drive Archive
```bash
bash scripts/download_data.sh <GOOGLE_DRIVE_FILE_ID>
```

---

## Forecasting Period

- **Horizon:** Up to 1 year ahead
- **Approach:** Calendar-based (seasonal patterns, holidays) rather than short-term real-time
- **Example:** Use June 2023, 2024, 2025 data → predict June 2026
- **Time resolution:** 6 time slots per day

| Slot | Hours | Label |
|------|-------|-------|
| 1 | 00:00–06:00 | Night |
| 2 | 06:00–10:00 | Morning |
| 3 | 10:00–14:00 | Midday |
| 4 | 14:00–18:00 | Afternoon |
| 5 | 18:00–22:00 | Evening |
| 6 | 22:00–24:00 | Late evening |

---

## Traffic Categories (Output)

| Category | Color | Label |
|----------|-------|-------|
| 1 | Green | Free-flowing / low traffic |
| 2 | Yellow | Moderate traffic |
| 3 | Orange | Increased traffic |
| 4 | Red | Heavy traffic |
| 5 | Dark red | Very heavy / critical congestion risk |

---

## Feature Engineering

### Calendar Features
- `date`, `year`, `month`, `week_number`
- `day_of_week` (0=Mon, 6=Sun)
- `is_weekend`, `is_public_holiday`, `is_bridge_day`, `is_long_weekend`
- `days_until_holiday_start`, `days_since_holiday_start`
- `days_until_holiday_end`, `days_since_holiday_end`

### Holiday Features (per federal state)
- `school_holiday_bavaria`, `school_holiday_bw`, `school_holiday_nrw`
- `holiday_overlap_count` — how many German states share holidays
- `holiday_departure_pressure` — high when Bavaria + BW overlap

### Seasonal Features
- `is_summer_season` (Jun–Sep), `is_winter_sports_season` (Dec–Mar)
- `is_easter_period`, `is_pentecost_period`, `is_christmas_period`

### Directional Features
- `corridor` (`A8E` / `A93S`), `direction` (`outbound` / `inbound`)
- `is_departure_peak_day` — holiday start + outbound
- `is_return_peak_day` — holiday end + inbound

### Historical Features
- `avg_volume_same_weekday_last_year`
- `avg_volume_same_holiday_period`
- `seasonal_baseline_volume`

### Weather Features (where available)
- `precipitation_mm`, `snowfall_cm`, `temperature_c`
- For far-future dates: use historical averages by month

---

## API Endpoints

```
POST /api/forecast          → Generate forecast for a date range + corridor + direction
GET  /api/calendar          → Full traffic calendar (color-coded, all corridors)
GET  /api/peak-days         → Top critical peak days for the next 12 months
POST /api/analyze           → Analyze an uploaded traffic CSV for patterns
GET  /api/health            → Service health check
```

See `docs/API.md` for full request/response schemas.

---

## Processor Logic

`backend/app/processors/traffic_analyzer.py`:

1. Load pre-built `.joblib` pipeline from `models/prediction_pipeline.joblib`
2. Accept a forecast request (corridor, direction, date range)
3. Build feature vector for each date × time_slot combination
4. Run model prediction → traffic category (1–5) + estimated volume
5. Return structured JSON with category, volume, color hex, explanation text

---

## Model

See `docs/MODEL_CONTRACT.md` for the full `.joblib` interface.

| Property | Value |
|----------|-------|
| Target variable (primary) | `traffic_category` (int 1–5) |
| Prediction type | Multi-class classification |
| Secondary target | `vehicle_count` (regression) |
| Key features | day_of_week, school_holiday_bavaria, direction, month, is_weekend, days_until_holiday_start |
| Training data | Historical hourly CSV, aggregated to time-slot level per corridor/direction |

---

## Frontend Visualizations

The Lovable React UI should show:

1. **Traffic Calendar View** — monthly grid, each day colored green → dark red (per direction)
2. **Day Detail** — 6 time-slot breakdown for a selected day with estimated volumes
3. **Peak Days Alert Panel** — top 10 critical days in the next year with explanation text
4. **Forecast Explanation** — bullet list of factors driving each day's category
5. **User-Group View Toggle** — reword recommendations for Tourist / Logistics / Local Resident
6. **Corridor Selector** — A8 East vs A93 South, outbound vs inbound tabs

---

## Success Criteria

The judges will evaluate the solution on:

1. **Correctness** — does the model produce reasonable forecasts that match known high-traffic periods (summer Saturdays, holiday starts)?
2. **Coverage** — full year ahead, both corridors, both directions, 6 time slots
3. **Explainability** — can the system explain why a day is red? (holiday start + Saturday + Bavaria + outbound)
4. **Usability** — is the output clear for non-technical users? Color coding, actionable advice
5. **Automation** — does it eliminate manual expert judgment?
6. **Benchmark** — how do the predictions compare to the existing manual Fahrkalender PDFs?

**Winning angle:** Emphasize that the system replaces unpredictable, hard-to-scale expert manual work with a transparent, reproducible model that any operator can re-run with new data.
