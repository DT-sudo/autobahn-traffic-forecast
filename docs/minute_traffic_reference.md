# Data Skill: A8/A93 Minute-Level Traffic Count Data (`FG1_Kurz_*_agg1min_*.csv`)

## Purpose

Use this skill when loading, parsing, or building features from any CSV file
matching the pattern:

```
FG1_Kurz_<site_name>,<DE_list>_agg1min_2023-01-01_bis_2026-01-01.csv
```

This is the **minute-level companion** to the hourly traffic dataset
(`FG1_Lang_*_agg1h_*.csv` — see separate skill doc for that file family).
Same underlying detectors, same sites, same 3-year date range, but at much
finer time resolution and with extra columns (vehicle class split, speed).

> ⚠️ **Large files — do not load naively.** Per the user, real files are
> **80–110 MB each**, 12 files total (~1–1.3 GB combined). My size estimate
> from the sample (~98 MB for 3 years at 1-min resolution) lines up with
> this, so treat the full dataset as genuinely large. See §5 for required
> handling strategy — do not `pd.read_csv()` all 12 files fully into memory
> at once without a clear reason and enough RAM headroom.

---

## 1. File-Level Format

| Property           | Value                                                                                                                                                                  |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Delimiter          | `;`                                                                                                                                                                    |
| Line endings       | CRLF (`\r\n`)                                                                                                                                                          |
| Encoding           | UTF-8 with BOM — use `encoding="utf-8-sig"`                                                                                                                            |
| Header row         | Yes, with the same **trailing-comma junk** seen in the hourly files: real header is `devices;datum;t_start;wochentag;q_kfz;q_lkw;q_pkw;v_kfz` followed by stray `,,,,` |
| Aggregation        | 1-minute (`agg1min` in filename)                                                                                                                                       |
| Date range         | 2023-01-01 to 2026-01-01 (3 years) — same as hourly files                                                                                                              |
| Est. size per file | ~80–110 MB (confirmed by user; matches my estimate from sample)                                                                                                        |
| Est. rows per file | ~1.55–1.58 million (3 years × ~525,960 minutes/year)                                                                                                                   |

```python
import pandas as pd
df = pd.read_csv(path, sep=";", encoding="utf-8-sig", nrows=1000)  # ALWAYS test with nrows first
df.columns = [c.split(",")[0] for c in df.columns]
```

---

## 2. Columns (different schema from the hourly file — do not assume parity)

| Column      | Type            | Meaning                                                                                                                 | Notes                                                                                                                                                                                                                                                                                                                                                                                                          |
| ----------- | --------------- | ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `devices`   | string          | Detector/site identifier                                                                                                | **Format differs from the hourly file**: no leading numeric ID prefix here. Hourly file: `9171_MQB25_Mch_H,DE33,34,35,36`. Minute file: `MQB25_Mch_H,DE33,34,35,36` (no `9171_`). Confirmed consistent with filename: hourly files are prefixed `FG1_Lang_<id>_<site>`, minute files are `FG1_Kurz_<site>` (no id). If joining the two datasets, **match on the site name portion only**, not the full string. |
| `datum`     | string → date   | `DD.MM.YYYY`                                                                                                            | Same format as hourly                                                                                                                                                                                                                                                                                                                                                                                          |
| `t_start`   | string → time   | `HH:MM:SS`, minute-level                                                                                                |                                                                                                                                                                                                                                                                                                                                                                                                                |
| `wochentag` | int             | ISO weekday, Mon=1...Sun=7                                                                                              | Same encoding confirmed as hourly file                                                                                                                                                                                                                                                                                                                                                                         |
| `q_kfz`     | int             | Total vehicle count in this minute ("Kfz" = Kraftfahrzeug)                                                              | Equivalent role to `kfz_h` in the hourly file, but per-minute                                                                                                                                                                                                                                                                                                                                                  |
| `q_lkw`     | int             | Truck/heavy-vehicle count in this minute ("Lkw" = Lastkraftwagen)                                                       | **Confirmed**: `q_kfz = q_lkw + q_pkw` exactly, every row in the sample — this is an exact decomposition, not an independent estimate                                                                                                                                                                                                                                                                          |
| `q_pkw`     | int             | Passenger car count in this minute ("Pkw" = Personenkraftwagen)                                                         | Confirmed complementary to `q_lkw`                                                                                                                                                                                                                                                                                                                                                                             |
| `v_kfz`     | float or `null` | Average vehicle speed in this minute (km/h, inferred — unit not explicitly stated, plausible given values 90–180 range) | **Confirmed pattern**: `v_kfz` is `null` if and only if `q_kfz == 0` (no vehicles passed → no speed to average); never null when `q_kfz > 0`. Pandas auto-parses the literal string `null` in the CSV to `NaN` — no special handling needed beyond normal `read_csv`.                                                                                                                                          |

This is a **richer schema than the hourly file** — note there's no direct
equivalent of `sv_h` (heavy vehicle count) by that name. **`q_lkw` is NOT the
same as `sv_h`** — see §3a, this was empirically tested and they differ.
There is no `tagestyp` column here (present in hourly file, absent here).

```python
df["datum"] = pd.to_datetime(df["datum"], format="%d.%m.%Y")
df["timestamp"] = df["datum"] + pd.to_timedelta(df["t_start"])
# v_kfz null values are already NaN after standard read_csv — no extra step needed
```

---

## 3a. ⭐ Empirical Reconciliation: minute vs hourly (VERIFIED)

Tested directly on site **`MQB25_Mch_H`** (A8-Ost, Munich direction —
high-confidence name-matched site) using the full hourly file and a 7-day /
168-hour overlapping slice of the minute file. Results:

**Total vehicles reconcile perfectly:**

- `sum(q_kfz)` aggregated per clock hour **== `kfz_h`** exactly, in **all
  168 hours**, zero difference. The minute and hourly files are fully
  consistent on total volume — confirmed you can trust either as the volume
  source, and can rebuild hourly totals from minute data losslessly.

**Heavy-vehicle columns do NOT match — `q_lkw` ≠ `sv_h`:**

- `sum(q_lkw)` per hour is **always ≥ `sv_h`** (162/168 hours strictly
  greater, 6 equal, never less).
- Ratio `sv_h / sum(q_lkw)` averaged **~0.88**, ranging from **1.0 down to
  ~0.40** — the gap is largest during daytime/leisure-peak hours (e.g. ~0.40
  at 17:00 on Jan 1, a holiday with heavy leisure traffic).
- `sum(q_lkw) − sv_h` is **always ≥ 0** (confirmed), i.e. `q_lkw` strictly
  contains `sv_h` plus something extra.

**Interpretation (matches the TLS vehicle-class definitions exactly):**

- **`q_lkw` = the "LKW-ähnlich" category** = SV + cars-with-trailer
  (Pkw mit Anhänger).
- **`sv_h` = the stricter "SV" category** = heavy vehicles >3.5t + buses,
  _excluding_ cars-with-trailer.
- The difference `q_lkw − sv_h` ≈ the **cars-with-trailer count**, which
  naturally spikes during leisure travel periods (caravans, boat/trailer
  towing on holidays) — explaining why the ratio dips exactly when leisure
  traffic peaks.

**Practical consequences for modeling:**

1. **Do not treat `q_lkw` (minute) and `sv_h` (hourly) as the same
   variable.** They measure different things. If you need a true heavy-
   traffic (`SV`) figure at minute resolution, `q_lkw` will **overstate** it
   by the cars-with-trailer count.
2. The two files give you a **free extra feature**: `q_lkw − sv_h` (per hour)
   is effectively a **cars-with-trailer / caravan count**, which is itself a
   strong _leisure-travel_ signal — potentially very useful for the holiday-
   traffic forecasting goal (caravans towing on holiday departure days).
3. To get strict `SV` at minute level you'd need the underlying 8-class
   breakdown (not provided) — or just use the hourly `sv_h` directly, since
   the project output is daily/time-slot anyway.
4. `q_pkw` (minute) = `q_kfz − q_lkw`, so `q_pkw` here = "Pkw-ähnlich" =
   cars/vans/motorcycles **without** trailer (since cars-with-trailer are
   bundled into `q_lkw`). Keep this in mind: `q_pkw` is _not_ "all passenger
   cars" — it excludes those towing trailers.

> ⚠️ This was verified on **one site, 168 hours**. The relationship is
> theoretically grounded (TLS definitions) and held perfectly, so it almost
> certainly generalizes — but a quick re-check on a second site and a wider
> date range is cheap insurance before relying on it heavily.

---

## 4-prelude. Confirmed Relationships (validated against minute sample, n=46 rows)

- `q_kfz == q_lkw + q_pkw` — **always true**, exact identity.
- `v_kfz` is `NaN` **exactly when** `q_kfz == 0`, and **never** `NaN`
  otherwise — clean, logical, no edge cases in the sample.
- Even at 1-minute granularity during a quiet overnight period (Jan 1,
  00:00–00:46), roughly **13% of minutes had zero vehicles** (6 of 46 rows)
  — useful baseline for expecting sparse/zero-inflated data overnight,
  especially on minor corridors or quiet hours. Daytime/peak data will look
  much denser.

---

## 4. The 12 Files & Site Mapping

Same 12 logical sites as the hourly dataset, same naming ambiguity for the
A93 South sites. Filenames here use `FG1_Kurz_` prefix and drop the leading
numeric ID that the hourly (`FG1_Lang_`) files have:

| Minute filename (site portion)       | Road    | Direction suffix | Maps to hourly file                   | Locations file match                            |
| ------------------------------------ | ------- | ---------------- | ------------------------------------- | ----------------------------------------------- |
| `MQB25_Mch_H,DE33,34,35,36`          | A8-Ost  | towards Munich   | `9171_MQB25_Mch_H,...`                | High — exact name match (`MQB25_Mch_H`)         |
| `MQQ37_Sbg_H,DE1,2,3,4`              | A8-Ost  | towards Salzburg | `9171_MQQ37_Sbg_H,...`                | High — exact match                              |
| `MQQ209_Mch_H,DE33,34`               | A8-Ost  | towards Munich   | `9192_MQQ209_Mch_H,...`               | High — exact match                              |
| `MQQ213_Sbg_H,DE1,2`                 | A8-Ost  | towards Salzburg | `9192_MQQ213_Sbg_H,...`               | High — exact match                              |
| `MQQ245_Mch_H,DE33,34`               | A8-Ost  | towards Munich   | `9194_MQQ245_Mch_H,...`               | High — exact match                              |
| `MQQ245_Sbg_H,DE1,2`                 | A8-Ost  | towards Salzburg | `9194_MQQ245_Sbg_H,...`               | High — exact match                              |
| `MQDZ_AD Inntal_(S)_Kff,DE33,34`     | A93-Süd | `_Kff`           | `9190_MQDZ_AD Inntal_(S)_Kff,...`     | ✅ **CONFIRMED** — device `81389190`, km 1.882  |
| `MQDZ_AD Inntal_(S)_Ro,DE1,2`        | A93-Süd | `_Ro`            | `9190_MQDZ_AD Inntal_(S)_Ro,...`      | ✅ **CONFIRMED** — device `81389190`, km 1.882  |
| `MQDZ_Kiefersfelden_(S)_Kff,DE33,34` | A93-Süd | `_Kff`           | `9191_MQDZ_Kiefersfelden_(S)_Kff,...` | ✅ **CONFIRMED** — device `83399191`, km 25.06  |
| `MQDZ_Kiefersfelden_(S)_Ro,DE1,2`    | A93-Süd | `_Ro`            | `9191_MQDZ_Kiefersfelden_(S)_Ro,...`  | ✅ **CONFIRMED** — device `83399191`, km 25.06  |
| `MQ_Gletschergarten_Kff,DE33,34`     | A93-Süd | `_Kff`           | `9629_MQ_Gletschergarten_Kff,...`     | ✅ **CONFIRMED** — device `82389192`, km 12.26  |
| `MQ_Gletschergarten_Ro,DE1,2`        | A93-Süd | `_Ro`            | `9629_MQ_Gletschergarten_Ro,...`      | ✅ **CONFIRMED** — device `82389192`, km 12.397 |

**Status: RESOLVED.** Organizer-confirmed mapping (see hourly traffic skill
doc §5 for the full table and lookup dict). AD Inntal (km 1.9, nearest
Rosenheim) → Gletschergarten (km 12.3, middle) → Kiefersfelden (km 25.1,
nearest the Austrian border) — confirms the original geographic hypothesis
exactly.

Use `A8_A93_MQ_locations.csv` for coordinates/km-markers exactly as
described in the hourly traffic skill doc — no new location file was
provided for the minute-level data; it's the same physical detectors.

---

## 5. Required Handling Strategy for Large Files

With 12 files at 80–110 MB each (~1.1 GB total), and the project likely
running in a memory-constrained hackathon environment, **do not** do this:

```python
# AVOID: loads ~1.55M rows × 8 columns per file, all 12 files, into RAM at once
all_data = [pd.read_csv(f, sep=";", encoding="utf-8-sig") for f in all_12_files]
combined = pd.concat(all_data)
```

Prefer one of these, depending on the actual task:

**A. If the end goal is hourly/daily aggregates** (most likely, given the
project needs daily/time-slot forecasts, not minute-level output):
aggregate each file down immediately after loading, then discard the raw
minute rows. Don't keep raw 1-minute data resident in memory across files.

```python
def load_and_aggregate_to_hourly(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    df.columns = [c.split(",")[0] for c in df.columns]
    df["datum"] = pd.to_datetime(df["datum"], format="%d.%m.%Y")
    df["timestamp"] = df["datum"] + pd.to_timedelta(df["t_start"])
    df = df.set_index("timestamp")
    hourly = df.resample("1h").agg(
        q_kfz=("q_kfz", "sum"),
        q_lkw=("q_lkw", "sum"),
        q_pkw=("q_pkw", "sum"),
        v_kfz_mean=("v_kfz", "mean"),
    )
    return hourly  # ~26K rows instead of ~1.55M — orders of magnitude smaller
```

This effectively **reconstructs (or cross-validates) the existing hourly
file** — useful as a data-quality check (do independently-aggregated minute
sums match the provided `FG1_Lang` hourly file's `kfz_h`/`sv_h`?), and gives
access to the speed (`v_kfz`) feature, which the hourly file doesn't have at
all.

**B. If minute-level granularity is genuinely needed for some analysis**
(e.g. detailed speed/congestion-onset patterns for a specific day): load
with `usecols`, chunk with `chunksize`, or filter by date range immediately
rather than reading the whole file.

```python
# Process in chunks, only keep what's needed
for chunk in pd.read_csv(path, sep=";", encoding="utf-8-sig", chunksize=200_000):
    chunk.columns = [c.split(",")[0] for c in chunk.columns]
    # filter / aggregate chunk here, discard the rest
```

**C. Consider converting to Parquet once after first load** to avoid
re-parsing the slow CSV format repeatedly during iterative development:

```python
df.to_parquet(f"{site_name}_minute.parquet")  # much faster to re-read later
```

**Recommendation for this project**: given the forecasting target is
daily/time-slot level (project context §14), **default to strategy A**
(aggregate to hourly immediately) for all 12 files as the standard pipeline
step, and only drop into minute-level raw data for targeted exploratory
analysis (e.g. validating speed/congestion onset patterns for a handful of
known peak days).

---

## 6. Relationship to the Hourly Dataset

This minute-level data is a **strict superset of information** relative to
the hourly `FG1_Lang` files for the same site:

- `q_kfz` summed over each clock hour should reconstruct `kfz_h` from the
  hourly file (recommend validating this directly once full files are
  available — good first data-quality check).
- `q_lkw` summed over each hour should reconstruct `sv_h` — **but note**:
  the hourly file's `sv_h` is described as "heavy vehicle" count, and this
  minute file's breakdown is `q_lkw` (trucks) + `q_pkw` (cars) summing to
  `q_kfz`. If `sv_h ≈ sum(q_lkw)` per hour, that confirms `sv_h` means
  trucks specifically (Lkw), narrowing the earlier ambiguity in the hourly
  skill doc about what "heavy vehicle" precisely includes (buses? trailers?
  just Lkw?). **Worth checking once both full files are loaded.**
- The minute file adds **speed** (`v_kfz`), which the hourly file lacks
  entirely — this is new information, useful for congestion-severity
  features (e.g. flagging minutes/hours where volume is high AND speed is
  low = real congestion, vs. high volume but free-flowing).

---

## 7. Relevance to the Traffic Forecasting Challenge

- Primary value: **cross-validation of the hourly dataset**, and **speed as
  a congestion indicator** the hourly file can't provide.
- Minute-level granularity itself is finer than anything the project's
  output needs (project context §14: 6 time slots/day is the target
  resolution) — so this is best treated as a richer **input/feature
  source**, aggregated up, rather than used at native resolution in the
  final model or output.
- Speed (`v_kfz`) could support a more sophisticated "true congestion"
  signal distinct from raw volume — e.g. a day could have high volume but
  still flow freely (good capacity), vs. high volume with low speed (actual
  congestion) — directly relevant to the color-coded severity categories
  in the project's Traffic Calendar output (context §16.1).

---

## 8. Open Questions / Follow-ups

- [x] **RESOLVED**: A93 South site/device/km mapping confirmed by organizers
      (see hourly traffic skill doc §5).
- [x] **RESOLVED**: `sum(q_kfz)` per hour reconstructs `kfz_h` **exactly**
      (verified on 168 overlapping hours for MQB25_Mch_H — perfect match, zero
      difference in every hour). Total vehicle counts reconcile perfectly
      between the minute and hourly files.
- [x] **RESOLVED — and the answer is NO**: `sum(q_lkw)` per hour does **not**
      equal `sv_h`. `q_lkw` is **always ≥ `sv_h`** (in the test: 162/168 hours
      q_lkw was strictly larger, 6 equal, never smaller; ratio sv_h/q_lkw
      averaged ~0.88, dipping to ~0.40 during leisure peaks). See §3a below —
      this means **`q_lkw` and `sv_h` are different metrics and must NOT be
      treated as interchangeable.**
- [ ] Confirm units for `v_kfz` (assumed km/h based on plausible value
      range 90–180, but not explicitly labeled in the file).
- [ ] Check missing-minute patterns and DST transition handling across the
      full 3-year range (same DST question as the hourly file, but minute
      granularity makes gaps easier to detect precisely).
- [ ] Confirm available memory/compute environment for the hackathon so the
      large-file strategy (§5) can be tuned appropriately (e.g. is there a
      shared server with ample RAM, or are people working on laptops?).
