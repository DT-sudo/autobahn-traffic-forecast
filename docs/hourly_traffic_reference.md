# Data Skill: A8/A93 Hourly Traffic Count Data (`FG1_Lang_*_agg1h_*.csv`) + Detector Locations

## Purpose

Use this skill when loading, parsing, or building features from any CSV file
matching the pattern:

```
FG1_Lang_<id>_<site_name>,<DE_list>_agg1h_2023-01-01_bis_2026-01-01.csv
```

or the companion detector-locations file `A8_A93_MQ_locations.csv`. This is
the **primary/core dataset** for the TUM Hackathon traffic forecasting
project — the actual historical traffic volume to be forecast.

---

## 1. File-Level Format

| Property     | Value                                                                                                                                                                                                                                                                              |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Delimiter    | `;` (semicolon)                                                                                                                                                                                                                                                                    |
| Line endings | CRLF (`\r\n`)                                                                                                                                                                                                                                                                      |
| Encoding     | **UTF-8 with BOM** (byte order mark) — use `encoding="utf-8-sig"` in pandas, or the BOM will get glued onto the first column name (`devices` → `\ufeffdevices`)                                                                                                                    |
| Header row   | Yes, single header line, but with **trailing junk**: the real header is `devices;datum;t_start;wochentag;tagestyp;kfz_h;sv_h` followed by 4 stray literal commas (`,,,,`) before the line break. Pandas will fold these into the last column name as `sv_h,,,,` unless cleaned up. |
| Aggregation  | Hourly (`agg1h` in filename)                                                                                                                                                                                                                                                       |
| Date range   | 2023-01-01 to 2026-01-01 (3 full years) — matches the project's stated historical window and the temperature data range                                                                                                                                                            |

```python
import pandas as pd

df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
df.columns = [c.split(",")[0] for c in df.columns]  # strip trailing comma junk from header
```

---

## 2. Columns

| Column      | Type          | Meaning                                                                                                                                                                                                                                                                                                                                                                                                               | Example                          |
| ----------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| `devices`   | string        | Detector/station identifier, repeats the filename's site+DE-channel info on every row                                                                                                                                                                                                                                                                                                                                 | `9171_MQB25_Mch_H,DE33,34,35,36` |
| `datum`     | string → date | Date, **German format `DD.MM.YYYY`**                                                                                                                                                                                                                                                                                                                                                                                  | `01.01.2023`                     |
| `t_start`   | string → time | Start of the hourly interval, `HH:MM:SS`                                                                                                                                                                                                                                                                                                                                                                              | `00:00:00`                       |
| `wochentag` | int           | Day of week, **ISO weekday numbering: Monday=1 ... Sunday=7** (confirmed: 2023-01-01 was a Sunday → value `7`; 2024-01-01 was a Monday → value `1`)                                                                                                                                                                                                                                                                   | `7`                              |
| `tagestyp`  | string        | **Day-type classification. RESOLVED — three codes** (verified on the full 3-year MQB25 file): `w` = normal working weekday ("Werktag"), `u` = school-holiday-period weekday ("Urlaub/Ferientag" — ~91% fall inside Bavarian school-holiday ranges), `s` = Sunday or public holiday ("Sonn-/Feiertag" — all wochentag-7 days plus every Bavarian public holiday regardless of weekday). See §3b for the full decoding. | `w`                              |
| `kfz_h`     | int           | **Total vehicle count for the hour** ("Kraftfahrzeuge pro Stunde"). This is the main traffic volume target variable.                                                                                                                                                                                                                                                                                                  | `5029`                           |
| `sv_h`      | int           | **Heavy vehicle count for the hour** ("Schwerverkehr pro Stunde") — a subset of `kfz_h`, confirmed always ≤ `kfz_h` in the sample, observed ratio up to ~9%. Matches the project context's mention of heavy-vehicle classification (lane/speed restrictions).                                                                                                                                                         | `121`                            |

```python
df["datum"] = pd.to_datetime(df["datum"], format="%d.%m.%Y")
df["t_start"] = pd.to_datetime(df["t_start"], format="%H:%M:%S").dt.time
df["timestamp"] = pd.to_datetime(
    df["datum"].dt.strftime("%Y-%m-%d") + " " + df["t_start"].astype(str)
)
```

---

## 3. Confirmed Daily Pattern (sanity check from sample)

The sample (Jan 1, 2023 — a Sunday/holiday) shows a textbook single-peak
leisure-traffic day: very low overnight (~200-600 veh/h from 00:00–06:00),
ramping up through the morning, peaking in the **early-to-mid afternoon**
(~5,000 veh/h between 14:00–17:00), then declining through the evening. This
is a useful reference shape to validate any new file load against — if a
parsed file doesn't show a low-overnight/midday-peak shape on a similar day
type, something went wrong in parsing.

---

## 3a. Data Quality & Completeness (VERIFIED on full MQB25 file)

Validated on the complete 3-year file
`FG1_Lang_9171_MQB25_Mch_H...` (26,304 rows, 2023-01-01 to 2025-12-31):

- **Coverage is on a fixed 24-hour-per-day local-wall-clock grid.** Every
  one of the 1,096 days has **exactly 24 rows**, including DST transition
  days. There are **no missing rows and no duplicate timestamps** at the row
  level — the time index is a perfectly continuous hourly grid.
- **But 80 rows have null `kfz_h` AND `sv_h`** (both null together, always).
  These are the real data gaps — present as rows, but with null values.
  - Most are **short sensor outages**: isolated single hours or 2–5 hour
    blocks scattered across the 3 years (e.g. 2023-05-29 18:00–22:00 was a
    5-hour gap). ~0.3% of all hours.
  - **Some null rows sit exactly on DST transitions** — see §3c.
- **Value sanity (MQB25)**: `kfz_h` ranged 72–6,941 (mean ~2,259), `sv_h`
  ranged 8–1,034 (mean ~279). No negatives, no zeros, and `sv_h ≤ kfz_h`
  in every row (confirms the subset relationship). No obvious fault/sentinel
  values like `-999` — gaps are represented as proper nulls, not magic
  numbers. (These ranges are for this one busy A8 site; quieter A93 sites
  will differ.)

**Handling recommendation:** treat null `kfz_h`/`sv_h` as missing data to be
imputed or excluded — do not fill with 0 (zero traffic is physically
distinct from a sensor outage, and this file never legitimately records 0).

---

## 3b. `tagestyp` Decoded (VERIFIED)

The full file contains exactly **three** `tagestyp` values, distribution:
`w` = 16,176 rows, `u` = 5,448, `s` = 4,680. Cross-referenced against
weekday and the Bavarian holiday/school calendar:

| Code | Meaning                                                    | Evidence                                                                                                                                                                                                                 |
| ---- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `w`  | **Werktag** — normal working weekday                       | The default for regular Mon–Sat days outside holidays                                                                                                                                                                    |
| `u`  | **School-holiday-period weekday** (likely "Urlaub"/Ferien) | ~91% of `u` days fall inside Bavarian school-holiday date ranges (Christmas, Winter, Easter, Pentecost, Summer, Autumn breaks); near-misses were all explained by approximate range boundaries + Buß-und-Bettag          |
| `s`  | **Sonn-/Feiertag** — Sunday or public holiday              | Every `wochentag==7` (Sunday) day is `s`, PLUS every Bavarian public holiday falling on a weekday is also `s` (Neujahr, Karfreitag, Ostermontag, Fronleichnam, etc. — all verified against the Bavaria holiday calendar) |

**This is a very useful built-in feature**: `tagestyp` already encodes the
working-day / school-holiday / Sunday-or-public-holiday distinction that the
project would otherwise have to reconstruct from external calendars. Note it
reflects the **Bavarian** calendar specifically. It does NOT capture
_destination-country_ or _other-Bundesland_ school holidays (which the
project context §18.1 says also drive traffic), so external holiday
calendars are still needed for those — but for the local Bavarian baseline,
`tagestyp` is ready-made.

> ⚠️ Decoded empirically on one site's 3-year file. The logic is consistent
> and calendar-grounded, but the exact German words behind `w`/`u`/`s` are
> inferred — worth a one-line confirmation with the organizers if precise
> labels matter for documentation.

---

## 3c. DST Handling (VERIFIED — important)

Timestamps are **local German wall-clock time** (CET/CEST), kept on a rigid
24-row-per-day grid. The DST transitions are handled as follows:

- **Spring forward** (e.g. 2023-03-26, clocks 02:00→03:00, so 02:00–03:00
  local time does not exist): the file **still has a 02:00 row, but its
  values are null**. The non-existent hour is a null placeholder, not
  omitted.
- **Fall back** (e.g. 2023-10-29, 02:00–03:00 occurs twice): the file does
  **not** create a 25th row or duplicate the hour — it keeps 24 rows, with
  null values around the 03:00–05:00 area on that date.

**Consequences:**

- If you build a timestamp index naïvely as "local date + local time", it is
  **not** a true monotonic UTC timeline across DST boundaries — there's a
  phantom null hour each spring and a folded hour each autumn. For most
  daily/seasonal forecasting this is negligible (a handful of null hours per
  year), but **do not** localize these timestamps to a tz-aware index
  expecting them to round-trip cleanly — `tz_localize('Europe/Berlin')` will
  error or need `nonexistent`/`ambiguous` handling on exactly these rows.
- Simplest safe approach: treat timestamps as **tz-naive local clock time**
  and accept the ~2 null DST hours/year as part of the normal ~0.3% gap rate.

---

## 4. The 12 Traffic Count Files

| Filename (site portion)                   | Road    | Direction suffix                       | BAB-Km | Locations file match                                               |
| ----------------------------------------- | ------- | -------------------------------------- | ------ | ------------------------------------------------------------------ |
| `9171_MQB25_Mch_H,DE33,34,35,36`          | A8-Ost  | `_Mch_H` → towards Munich (inbound)    | 20.09  | High — exact name match (`MQB25_Mch_H`)                            |
| `9171_MQQ37_Sbg_H,DE1,2,3,4`              | A8-Ost  | `_Sbg_H` → towards Salzburg (outbound) | 20.165 | High — matches `MQQ37_Sbg_H` exactly                               |
| `9192_MQQ209_Mch_H,DE33,34`               | A8-Ost  | towards Munich                         | 93.384 | High — matches `MQQ209_Mch_H` exactly                              |
| `9192_MQQ213_Sbg_H,DE1,2`                 | A8-Ost  | towards Salzburg                       | 94.745 | High — matches `MQQ213_Sbg_H` exactly                              |
| `9194_MQQ245_Mch_H,DE33,34`               | A8-Ost  | towards Munich                         | 106.27 | High — matches `MQQ245_Mch_H` exactly                              |
| `9194_MQQ245_Sbg_H,DE1,2`                 | A8-Ost  | towards Salzburg                       | 106.27 | High — matches `MQQ245_Sbg_H` exactly                              |
| `9190_MQDZ_AD Inntal_(S)_Kff,DE33,34`     | A93-Süd | `_Kff`                                 | 1.882  | ✅ **CONFIRMED by organizers** — device `81389190`, `A93-Sued_Kff` |
| `9190_MQDZ_AD Inntal_(S)_Ro,DE1,2`        | A93-Süd | `_Ro`                                  | 1.882  | ✅ **CONFIRMED** — device `81389190`, `A93-Sued_Ros`               |
| `9191_MQDZ_Kiefersfelden_(S)_Kff,DE33,34` | A93-Süd | `_Kff`                                 | 25.06  | ✅ **CONFIRMED** — device `83399191`, `A93-Sued_Kff`               |
| `9191_MQDZ_Kiefersfelden_(S)_Ro,DE1,2`    | A93-Süd | `_Ro`                                  | 25.06  | ✅ **CONFIRMED** — device `83399191`, `A93-Sued_Ros`               |
| `9629_MQ_Gletschergarten_Kff,DE33,34`     | A93-Süd | `_Kff`                                 | 12.26  | ✅ **CONFIRMED** — device `82389192`, `A93-Sued_Kff`               |
| `9629_MQ_Gletschergarten_Ro,DE1,2`        | A93-Süd | `_Ro`                                  | 12.397 | ✅ **CONFIRMED** — device `82389192`, `A93-Sued_Ros`               |

**Status: RESOLVED.** User confirmed the mapping directly with the
hackathon organizers. All 12 files now map cleanly to physical locations.
The earlier geographic hypothesis (km ~1.9 = Inntal nearest the A93 start
by Rosenheim, km ~12.3 = Gletschergarten in the middle, km ~25 =
Kiefersfelden nearest the Austrian border) turned out to be **exactly
correct** — confirms the A93 runs Rosenheim → Kiefersfelden/Austria in
increasing km order.

**`Kff`/`Ro` direction codes**: the locations file uses `A93-Sued_Kff` and
`A93-Sued_Ros` (note "Ros", not "Ro") for the two directions — same two
directions as the traffic filenames' `_Kff`/`_Ro` suffixes, just a minor
spelling difference between the two source files. The literal meaning
(Kufstein-bound vs. Rosenheim-bound) is still **not formally confirmed by
the organizers' wording**, but is the obvious reading given "Kff" and "Ro"
visibly abbreviate "Kufstein" and "Rosenheim" — low-risk to treat as
confirmed in practice, though the formal question (organizer script Q2)
can stay open if you want it spelled out explicitly.

---

## 5. A93 South Mapping — ✅ RESOLVED (organizer-confirmed)

The full confirmed site table for A93-Süd:

| Named site (filename) | Direction | Device ID  | `Strecke`    | BAB-Km | Lon       | Lat       |
| --------------------- | --------- | ---------- | ------------ | ------ | --------- | --------- |
| AD Inntal             | Kff       | `81389190` | A93-Sued_Kff | 1.882  | 12.089935 | 47.794097 |
| AD Inntal             | Ro        | `81389190` | A93-Sued_Ros | 1.882  | 12.090098 | 47.794100 |
| Gletschergarten       | Kff       | `82389192` | A93-Sued_Kff | 12.26  | 12.150545 | 47.711418 |
| Gletschergarten       | Ro        | `82389192` | A93-Sued_Ros | 12.397 | 12.151715 | 47.710466 |
| Kiefersfelden         | Kff       | `83399191` | A93-Sued_Kff | 25.06  | 12.195144 | 47.606010 |
| Kiefersfelden         | Ro        | `83399191` | A93-Sued_Ros | 25.06  | 12.195249 | 47.605929 |

Geographic ordering (by increasing BAB-Km, south along the A93 from
Rosenheim towards the Austrian border at Kufstein):
**AD Inntal (km 1.9) → Gletschergarten (km 12.3) → Kiefersfelden (km 25.1)**
— this matches the original geographic hypothesis exactly, and confirms the
A93 South corridor's km numbering increases from Rosenheim towards Austria.

`Kff` = `A93-Sued_Kff` and `Ro` = `A93-Sued_Ros` are confirmed as the two
opposite-direction labels at each site (same site/device ID, different
direction suffix and slightly different coordinates ~10-150m apart,
consistent with the two carriageways of a divided motorway). The literal
expansion (Kufstein-bound / Rosenheim-bound) remains the natural reading
but wasn't spelled out verbatim by the organizers — low-risk to treat as
given.

```python
A93_SITE_MAP = {
    ("AD Inntal", "Kff"):        {"device": "81389190", "km": 1.882,  "lon": 12.089935, "lat": 47.794097},
    ("AD Inntal", "Ro"):         {"device": "81389190", "km": 1.882,  "lon": 12.090098, "lat": 47.794100},
    ("Gletschergarten", "Kff"):  {"device": "82389192", "km": 12.26,  "lon": 12.150545, "lat": 47.711418},
    ("Gletschergarten", "Ro"):   {"device": "82389192", "km": 12.397, "lon": 12.151715, "lat": 47.710466},
    ("Kiefersfelden", "Kff"):    {"device": "83399191", "km": 25.06,  "lon": 12.195144, "lat": 47.606010},
    ("Kiefersfelden", "Ro"):     {"device": "83399191", "km": 25.06,  "lon": 12.195249, "lat": 47.605929},
}
```

---

## 5a. Unconfirmed Hypotheses — historical record (now resolved, kept for context)

The items below were the open hypotheses before organizer confirmation.
Kept here only as a record of how the resolved mapping in §5 was derived;
no longer actionable.

- **Site-name mapping**: km ~1.882 = "AD Inntal" (closest to A93 start near
  Rosenheim), km ~12.3 = "Gletschergarten" (middle), km ~25.06 =
  "Kiefersfelden" (closest to the Austria border) — geographically
  plausible (south-to-north / increasing km would run from Rosenheim
  towards Kiefersfelden at the border) but **not confirmed**.
- **Direction codes**: `Kff` (possibly "Kufstein", an Austrian town just
  over the border — would imply outbound/southbound) and `Ro` (possibly
  "Rosenheim" — would imply inbound/northbound) — plausible given the
  `DE33/34` vs `DE1/2` channel split mirrors the `Kff`/`Mch`/`Sbg` direction
  pattern seen on the confirmed A8 files, but **not confirmed**.
- Numeric filename prefixes (`9171`, `9190`, `9191`, `9192`, `9194`, `9629`)
  do not cleanly correspond to the `81389190`/`82389192`/`83399191` device
  numbers in the locations file (the last-4-digit match works for 2 of 3 but
  collides with an already-used A8 ID for the third) — **do not rely on
  numeric ID pattern-matching to join these two files**; matching must be
  done via the road segment name + BAB-Km instead, once confirmed.

**Action item:** ask Die Autobahn GmbH / hackathon organizers to confirm (a)
the Inntal/Gletschergarten/Kiefersfelden ↔ BAB-Km mapping, and (b) the
Kff/Ro direction meaning, before finalizing any direction-aware modeling or
labeling for A93 South.

---

## 6. Detector Locations File (`A8_A93_MQ_locations.csv`)

| Property          | Value                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------- |
| Delimiter         | `;`                                                                                         |
| Decimal separator | `,` (German locale) — use `decimal=","`                                                     |
| Line endings      | CRLF                                                                                        |
| Columns           | `site`, `unit`, `Funktionsgruppe`, `Strecke`, `BAB-Km`, `Longitude_WGS84`, `Latitude_WGS84` |

```python
loc = pd.read_csv("A8_A93_MQ_locations.csv", sep=";", decimal=",")
```

- `Funktionsgruppe` = `1` for all rows (vs. `3` for the Rosenheim weather
  station file) — likely a category distinguishing traffic detectors (1)
  from weather stations (3).
- `Strecke` values seen: `A8-Ost_Mch`, `A8-Ost_Sbg`, `A93-Sued_Ros`,
  `A93-Sued_Kff` — i.e. corridor + direction combined into one field. Note
  `A93-Sued_Ros`/`A93-Sued_Kff` use "Ros"/"Kff" while the traffic filenames
  use "Ro"/"Kff" — likely the same Rosenheim/Kufstein direction labels,
  reinforcing (but not proving) the §5 hypothesis.
- Each physical `site` has 2–4 `unit` rows (individual lane detectors at the
  same cross-section) sharing the same coordinates and Km marker — i.e. the
  hourly traffic CSVs are **already aggregated across lanes** at a given
  site (the `devices` column lists multiple `DE` channel numbers together,
  e.g. `DE33,34,35,36`), since `kfz_h`/`sv_h` are single combined hourly
  totals, not per-lane.

---

## 7. Suggested Loading Code

```python
import pandas as pd
from pathlib import Path

def load_traffic_file(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    df.columns = [c.split(",")[0] for c in df.columns]  # strip header junk
    df["datum"] = pd.to_datetime(df["datum"], format="%d.%m.%Y")
    df["timestamp"] = df["datum"] + pd.to_timedelta(df["t_start"])
    df = df.drop(columns=["datum", "t_start"]).sort_values("timestamp")
    return df

def load_locations(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", decimal=",")

def load_all_traffic_files(file_paths: list[str]) -> pd.DataFrame:
    """Load and tag all 12 site files with a clean site label parsed
    from the filename, for easy filtering by corridor/direction later."""
    frames = []
    for p in file_paths:
        df = load_traffic_file(p)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)
```

---

## 8. Relevance to the Traffic Forecasting Challenge

This **is** the core target dataset (project context §17, §9): `kfz_h`
(total hourly vehicle count) is the primary variable to forecast, and
`sv_h` (heavy vehicle count) supports the heavy-vehicle-specific angle
mentioned in the project context (speed/lane restrictions for trucks/buses
— relevant to the logistics/freight user group, §11.3).

- **6 confirmed A8-Ost sites** (3 cross-sections × 2 directions: Munich-bound
  vs Salzburg-bound) at km 20.09/20.165, 93.384/94.745, 106.27 — good
  geographic spread along the corridor (near Munich, mid-corridor, near the
  Austrian border).
- **6 A93-Süd sites** (3 cross-sections × 2 directions, direction labels
  unconfirmed) at km 1.882, ~12.3, 25.06.
- Hourly granularity directly matches the project's required time-slot
  output (§14: 6 daily time slots) — slots can be built by grouping
  consecutive hours.
- `wochentag` and `tagestyp` are pre-computed calendar features already
  present in the source data — useful starting features, though
  supplementary public/school holiday calendars (project context §18.1,
  §18.2) will still be needed since `tagestyp` alone (only one value `s`
  seen so far) won't distinguish holiday types.
- 3 years of hourly history (2023–2025) per site is enough to build
  day-of-week / week-of-year / holiday-period historical baselines for the
  1-year-ahead forecast target (June 2026), per the project's stated
  approach (§12).

---

## 9. Open Questions / Follow-ups

- [ ] Confirm the Inntal/Gletschergarten/Kiefersfelden ↔ BAB-Km mapping for
      A93 South (§5).
- [ ] Confirm whether `Kff`/`Ro` (and `Kff`/`Ros` in the locations file) mean
      Kufstein-direction (outbound) / Rosenheim-direction (inbound) (§5).
- [x] **RESOLVED** (§3b): `tagestyp` has 3 codes — `w` working weekday,
      `u` school-holiday weekday, `s` Sunday/public-holiday. Decoded from full
      file + Bavarian calendar. (Exact German wording still worth a 1-line
      organizer confirm, but meaning is clear.)
- [x] **RESOLVED** (§3a, §3c): Full MQB25 file is a complete 24h/day grid,
      zero missing rows / zero duplicates, but 80 rows (~0.3%) have null
      values (sensor outages + DST phantom hours). DST = local wall-clock on a
      fixed 24-row grid; spring-forward hour is a null placeholder, fall-back
      hour is not duplicated.
- [x] **RESOLVED**: `kfz_h` includes `sv_h` (subset confirmed). Verified via
      minute-file reconciliation: `sum(q_kfz)` per hour == `kfz_h` exactly, and
      `sv_h` is always a fraction of `kfz_h`. `sv_h` is a "of which heavy
      vehicles" subset, not additive.
- [x] **RESOLVED — `sv_h` = TLS "SV" category** (heavy vehicles >3.5t +
      buses, excluding cars-with-trailer), per the vehicle-class definition
      image. Note this is **narrower** than the minute file's `q_lkw` column —
      see the minute-traffic skill doc §3a; do not equate the two.
- [ ] NOTE on header junk: the trailing `,,,,` in the header was present in
      the **sample** files but NOT in the full hourly file
      (`FG1_Lang_9171_MQB25...` full file had a clean
      `devices;datum;t_start;wochentag;tagestyp;kfz_h;sv_h` header). The
      `c.split(",")[0]` cleanup is still safe to keep (harmless when no junk
      present), but be aware full files may already be clean.
- [ ] Determine whether other `Funktionsgruppe` values exist (only `1` seen
      here, `3` in the weather station file) and what they represent overall.
