# ELI5: How the Traffic Prediction Model Works

This document explains — in plain language — how the model goes from a date you type in to a colored square on the calendar.

---

## The Big Picture

Imagine you want to guess how busy a motorway will be on a random future day — say, Saturday 1 August 2026. You don't have a crystal ball. But you do have three years of real measurements from road sensors (2023–2025), and you've noticed patterns: summers are busy, Saturdays heading toward Salzburg are packed, school holidays make things worse, etc.

The model is basically a very systematic way of capturing all those patterns from historical data and applying them to future dates.

---

## Step 1 — What the sensors recorded (raw data)

The motorways A8 and A93 have physical **loop detectors** buried in the road surface. Every hour, they count how many vehicles passed over them (`kfz_h` = Kraftfahrzeuge pro Stunde = vehicles per hour) and how many were heavy trucks (`sv_h`).

There are 12 detector files covering 2023–2026, one per detector station per direction. The pipeline stacks all of them, removes nonsense values (negatives, extreme outliers above the 99.9th percentile), and averages across detector stations on the same corridor/direction to get one representative number per hour.

---

## Step 2 — Squashing hours into 6 time slots

Nobody wants a prediction for every single hour of the day. The day is cut into **6 slots**:

| Slot | Hours | Why this cut |
|------|-------|--------------|
| 1 | 00:00 – 06:00 | Night, almost no traffic |
| 2 | 06:00 – 10:00 | Morning rush / early departure |
| 3 | 10:00 – 14:00 | Mid-morning wave |
| 4 | 14:00 – 18:00 | Afternoon peak |
| 5 | 18:00 – 22:00 | Evening return |
| 6 | 22:00 – 24:00 | Late night |

For each slot, the hourly counts inside that window are summed (not averaged — a 4-hour slot should count 4 hours of vehicles, not average them). The result is one number per slot per day per corridor/direction: total vehicles in that time window.

---

## Step 3 — Turning vehicle counts into categories (labels)

A raw vehicle count like "12,483 vehicles in slot 3" is hard to communicate. So each count is converted to a category 1–5 using **percentile thresholds** computed from the historical data:

| Category | Label | Threshold | Meaning |
|----------|-------|-----------|---------|
| 1 | Low / Green | below p50 | Bottom half of all observed days |
| 2 | Increased / Yellow | p50 – p70 | Above average but not bad |
| 3 | Moderate / Orange | p70 – p88 | Noticeably busy |
| 4 | Heavy / Red | p88 – p97 | Top 12% of days |
| 5 | Extreme / Dark Red | above p97 | Top 3% — worst days |

These thresholds are computed **separately for each combination of (corridor, direction, time slot)** — because what counts as "heavy" on A8 outbound at 14:00 is a different number than on A93 inbound at 06:00.

For example, A8 inbound slot 3 (10:00–14:00) thresholds are roughly: 9,010 / 10,608 / 12,284 / 13,560 vehicles. So a day with 13,000 vehicles in that slot gets category 4 (Heavy).

This is how the training data gets its **labels**: every historical slot row ends up with a category 1–5 attached.

---

## Step 4 — The 25 features (what the model reads)

For every future date you ask about, the model needs to know something about that day. It can't see into the future — but it can see **what kind of day it is**. These are called features.

There are 25 of them, split into groups:

### Calendar basics
| Feature | What it is |
|---------|-----------|
| `month` | January = 1, December = 12 |
| `day_of_week` | Monday = 0, Sunday = 6 |
| `week_of_year` | 1–53 |
| `time_slot` | 1–6 (which of the 6 daily windows) |
| `is_weekend` | 1 if Saturday or Sunday |

### Public holidays
| Feature | What it is |
|---------|-----------|
| `is_public_holiday_de` | German national holiday |
| `is_public_holiday_bavaria` | Bavarian-specific holiday (e.g. Epiphany, Assumption Day) |
| `is_bridge_day` | Workday sandwiched between a holiday and a weekend (Brückentag) |
| `is_long_weekend` | Part of a 3+ consecutive day off block |

### School holidays
| Feature | What it is |
|---------|-----------|
| `is_school_holiday_bavaria` | Bavarian school holidays active |
| `is_school_holiday_bw` | Baden-Württemberg school holidays active |
| `school_holiday_overlap` | Sum of the two (0, 1, or 2) — overlap = more departure pressure |
| `days_until_school_holiday` | How many days until the next Bavarian holiday starts (capped at 30) |
| `days_since_school_holiday` | How many days since the last one ended (capped at 30) |

The BW holidays matter because Baden-Württemberg is directly north of Bavaria. When both states are on holiday simultaneously, traffic spikes dramatically — families from Stuttgart and Munich all head to the Alps at the same time.

### Seasonal flags
| Feature | What it is |
|---------|-----------|
| `is_summer_season` | June–September |
| `is_winter_sports_season` | December–March |
| `is_easter_period` | ±4 days around Easter Sunday |
| `is_christmas_period` | 22 Dec – 6 Jan |

### Road-specific context
| Feature | What it is |
|---------|-----------|
| `is_outbound` | 1 if traveling away from Munich (toward Salzburg/Kufstein) |
| `is_a93` | 1 if corridor is A93 (vs A8) |

### Historical baselines (the model's memory)
These are the most powerful features. They are averages computed from the 2023–2025 data and stored in the model bundle.

| Feature | What it is |
|---------|-----------|
| `hist_kfz_dow_slot` | Average vehicle count for this (corridor, direction, day-of-week, slot) across all historical data. E.g. "on average, A8 outbound on a Saturday in slot 4 had 14,200 vehicles." |
| `hist_kfz_month_slot` | Same but grouped by month instead of day-of-week. Captures seasonality. |
| `hist_sv_share` | Fraction of vehicles that were heavy trucks on this corridor/direction historically (~8%). |

### Weather proxy
| Feature | What it is |
|---------|-----------|
| `clim_air_temp_c` | Climatological (long-term average) air temperature for the month. Jan ≈ 1°C, Jul ≈ 21°C. |
| `is_frost_risk_month` | 1 for December, January, February, November |

Real measured temperature was used if available (from the road sensor station at AD Rosenheim). Otherwise these monthly averages are used as a stand-in.

---

## Step 5 — Training the model

With 3 years × 4 corridor/direction combos × 365 days × 6 slots ≈ **~26,000 rows** of labeled training data, two models are trained:

### Model A: the Classifier
- **Input:** the 25 features above
- **Output:** category 1, 2, 3, 4, or 5
- **Algorithm:** Gradient Boosting — builds 300 decision trees one after another, each one learning to fix the mistakes of the previous one
- **What it answers:** "What color should this day-slot be?"

### Model B: the Regressor
- **Same input**, same algorithm
- **Output:** a raw vehicle count (e.g. 11,400 vehicles)
- **What it answers:** "How many cars will actually pass through?"

Both models are wrapped with a `StandardScaler` that normalizes the features to similar scales before the trees see them (not strictly necessary for tree models, but harmless).

Training takes 2–3 minutes. The result is saved as a single file: `models/prediction_pipeline.joblib`.

---

## Step 6 — Making a prediction for a future date

When you search "A8 East, 1 August 2026" in the UI, this is what happens:

1. **Build feature row** — `feature_builder.py` computes all 25 features for 1 Aug 2026 (a Saturday in summer, Bavarian school holidays active, outbound direction, slot 4 = 14:00–18:00, historical baseline for Saturday/slot 4 on A8 outbound = ~14,200 vehicles, etc.)

2. **Classifier predicts** — feeds the 25 numbers into the trained classifier → outputs category 4 (Heavy), with e.g. 72% confidence

3. **Regressor predicts** — same 25 numbers → outputs e.g. 13,800 vehicles

4. **Repeat for all 6 slots** → 6 predictions per day

5. **Day summary** — average the 6 slot categories, round to nearest integer → daily category

6. **Color** — category 4 → red (#D83528)

7. **Return to frontend** → the calendar square for 1 Aug 2026 turns red

---

## Why this works (and its limits)

**Why it works:** Traffic on Alpine corridors is almost entirely driven by calendar effects — when people are on holiday, when school starts, which direction they go. These patterns repeat very consistently year over year. The model has seen three years of them.

**Limits:**
- It knows nothing about accidents, road works, weather events (storms closing passes), or large events (concerts, football matches)
- Its school holiday calendar is hardcoded up to 2026 — predictions beyond that degrade gracefully but become less accurate
- It has no concept of economic trends or population growth — it assumes 2026 looks like 2023–2025
- The forecasts are probabilistic: the "72% confidence" means the model has seen many similar days labeled as category 4, but ~28% of such days turned out differently

---

## What the static CSVs in `frontend/public/data/` are

The 4 files (`A8easttraffic.csv`, etc.) are pre-generated exports — someone ran the model for every day from today through ~376 days ahead and saved the results as CSV. The frontend currently ignores them and calls the backend live instead, but the data is identical: it's just the model's output cached into a file.
