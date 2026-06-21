"""
Shared feature engineering for traffic forecasting.
Used by both scripts/build_features.py (training) and traffic_analyzer.py (inference).

All feature functions are pure: they take a date and return a dict.
No I/O, no model loading. Safe to import anywhere.
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any

# ---------------------------------------------------------------------------
# Holiday calendars (hardcoded, covers 2023-2026)
# ---------------------------------------------------------------------------

# Bavaria (Bayern) school holiday periods (start inclusive, end inclusive)
BAVARIAN_SCHOOL_HOLIDAYS: list[tuple[str, str]] = [
    # 2023
    ("2023-01-01", "2023-01-06"),   # New Year / Christmas carryover
    ("2023-02-20", "2023-02-24"),   # Winter
    ("2023-04-03", "2023-04-14"),   # Easter
    ("2023-05-30", "2023-06-09"),   # Pentecost
    ("2023-07-31", "2023-09-11"),   # Summer (6 weeks) ★
    ("2023-10-28", "2023-11-03"),   # Autumn
    ("2023-12-23", "2024-01-05"),   # Christmas
    # 2024
    ("2024-02-12", "2024-02-16"),   # Winter
    ("2024-03-25", "2024-04-06"),   # Easter
    ("2024-05-21", "2024-06-01"),   # Pentecost
    ("2024-07-29", "2024-09-09"),   # Summer ★
    ("2024-10-28", "2024-11-01"),   # Autumn
    ("2024-12-23", "2025-01-04"),   # Christmas
    # 2025
    ("2025-02-17", "2025-02-21"),   # Winter
    ("2025-04-14", "2025-04-26"),   # Easter (Easter Sun Apr 20)
    ("2025-06-10", "2025-06-20"),   # Pentecost
    ("2025-07-28", "2025-09-08"),   # Summer ★
    ("2025-10-27", "2025-10-31"),   # Autumn
    ("2025-12-22", "2026-01-03"),   # Christmas
    # 2026 (forecast year — extrapolated from pattern)
    ("2026-02-02", "2026-02-06"),   # Winter
    ("2026-03-30", "2026-04-11"),   # Easter (Easter Sun Apr 5)
    ("2026-06-02", "2026-06-13"),   # Pentecost (approx)
    ("2026-07-27", "2026-09-07"),   # Summer ★
    ("2026-10-26", "2026-10-30"),   # Autumn
    ("2026-12-21", "2027-01-02"),   # Christmas
]

# Baden-Württemberg school holidays (important: BW+BY overlap = extreme pressure)
BW_SCHOOL_HOLIDAYS: list[tuple[str, str]] = [
    # 2023
    ("2023-01-01", "2023-01-07"),
    ("2023-04-06", "2023-04-21"),   # Easter (BW = 2 weeks)
    ("2023-05-30", "2023-06-09"),   # Pentecost
    ("2023-07-27", "2023-09-09"),   # Summer (starts 4 days before Bavaria)
    ("2023-10-30", "2023-11-03"),   # Autumn
    ("2023-12-23", "2024-01-05"),   # Christmas
    # 2024
    ("2024-04-02", "2024-04-13"),   # Easter
    ("2024-05-21", "2024-06-01"),   # Pentecost
    ("2024-07-25", "2024-09-07"),   # Summer (starts before Bavaria again)
    ("2024-10-28", "2024-11-01"),   # Autumn
    ("2024-12-23", "2025-01-04"),   # Christmas
    # 2025
    ("2025-04-25", "2025-05-09"),   # Easter
    ("2025-07-31", "2025-09-13"),   # Summer
    ("2025-10-27", "2025-10-31"),   # Autumn
    ("2025-12-22", "2026-01-03"),   # Christmas
    # 2026
    ("2026-04-09", "2026-04-18"),   # Easter
    ("2026-07-30", "2026-09-12"),   # Summer
    ("2026-12-21", "2027-01-02"),   # Christmas
]


def _parse_ranges(pairs: list[tuple[str, str]]) -> list[tuple[date, date]]:
    return [(date.fromisoformat(s), date.fromisoformat(e)) for s, e in pairs]


_BY_RANGES = _parse_ranges(BAVARIAN_SCHOOL_HOLIDAYS)
_BW_RANGES = _parse_ranges(BW_SCHOOL_HOLIDAYS)


def _in_school_holiday(d: date, ranges: list[tuple[date, date]]) -> bool:
    return any(s <= d <= e for s, e in ranges)


def _days_until_next_holiday_start(d: date, ranges: list[tuple[date, date]]) -> int:
    """Positive = days until next holiday starts; 0 if holiday starts today or already in one."""
    future_starts = [s for s, e in ranges if s > d]
    if not future_starts:
        return 99
    return (min(future_starts) - d).days


def _days_since_last_holiday_end(d: date, ranges: list[tuple[date, date]]) -> int:
    """Positive = days since last holiday ended; 0 if in holiday now."""
    past_ends = [e for s, e in ranges if e < d]
    if not past_ends:
        return 99
    return (d - max(past_ends)).days


# ---------------------------------------------------------------------------
# German/Bavarian public holidays (import here to keep it optional)
# ---------------------------------------------------------------------------

def _get_de_public_holidays(years: list[int]) -> set[date]:
    try:
        import holidays as hlib
        result: set[date] = set()
        for y in years:
            result.update(hlib.country_holidays("DE", years=y).keys())
        return result
    except ImportError:
        return set()


def _get_bavaria_public_holidays(years: list[int]) -> set[date]:
    try:
        import holidays as hlib
        result: set[date] = set()
        for y in years:
            result.update(hlib.country_holidays("DE", subdiv="BY", years=y).keys())
        return result
    except ImportError:
        return set()


# Precompute for 2023-2026 at module load (fast, done once)
_YEARS = list(range(2023, 2027))
_DE_HOLIDAYS: set[date] = _get_de_public_holidays(_YEARS)
_BY_HOLIDAYS: set[date] = _get_bavaria_public_holidays(_YEARS)


# ---------------------------------------------------------------------------
# Time slot helpers
# ---------------------------------------------------------------------------

SLOT_HOURS: dict[int, tuple[int, int]] = {
    1: (0, 6),
    2: (6, 10),
    3: (10, 14),
    4: (14, 18),
    5: (18, 22),
    6: (22, 24),
}

SLOT_LABELS: dict[int, str] = {
    1: "00:00–06:00",
    2: "06:00–10:00",
    3: "10:00–14:00",
    4: "14:00–18:00",
    5: "18:00–22:00",
    6: "22:00–24:00",
}

SLOT_HOURS_DURATION: dict[int, int] = {k: v[1] - v[0] for k, v in SLOT_HOURS.items()}


def hour_to_slot(hour: int) -> int:
    for slot, (start, end) in SLOT_HOURS.items():
        if start <= hour < end:
            return slot
    return 6  # midnight edge case


# ---------------------------------------------------------------------------
# Traffic color mapping
# ---------------------------------------------------------------------------

CATEGORY_META: dict[int, dict[str, str]] = {
    1: {"label": "green",    "hex": "#2ECC71", "description": "Free-flowing / low traffic"},
    2: {"label": "yellow",   "hex": "#F1C40F", "description": "Moderate traffic"},
    3: {"label": "orange",   "hex": "#E67E22", "description": "Increased traffic"},
    4: {"label": "red",      "hex": "#E74C3C", "description": "Heavy traffic"},
    5: {"label": "dark_red", "hex": "#8B0000", "description": "Very heavy / critical congestion"},
}


# ---------------------------------------------------------------------------
# Core feature computation
# ---------------------------------------------------------------------------

def compute_calendar_features(d: date) -> dict[str, Any]:
    """Return calendar-only features for date d (no external data needed)."""
    dow = d.weekday()          # 0=Mon, 6=Sun
    month = d.month
    is_weekend = int(dow >= 5)
    is_pub_de = int(d in _DE_HOLIDAYS)
    is_pub_by = int(d in _BY_HOLIDAYS)
    is_bridge = _is_bridge_day(d)
    is_long_wknd = _is_long_weekend(d)

    is_school_by = int(_in_school_holiday(d, _BY_RANGES))
    is_school_bw = int(_in_school_holiday(d, _BW_RANGES))
    days_until_school = _days_until_next_holiday_start(d, _BY_RANGES)
    days_since_school = _days_since_last_holiday_end(d, _BY_RANGES)

    # Clip to useful range
    days_until_school_clipped = min(30, days_until_school) if not is_school_by else 0
    days_since_school_clipped = min(30, days_since_school) if not is_school_by else 0

    is_summer = int(6 <= month <= 9)
    is_winter_sports = int(month in (12, 1, 2, 3))
    is_easter = _is_easter_period(d)
    is_xmas = int(
        (month == 12 and d.day >= 22) or (month == 1 and d.day <= 6)
    )

    return {
        "month": month,
        "day_of_week": dow,             # 0=Mon, 6=Sun (sklearn-friendly)
        "week_of_year": d.isocalendar()[1],
        "is_weekend": is_weekend,
        "is_public_holiday_de": is_pub_de,
        "is_public_holiday_bavaria": is_pub_by,
        "is_bridge_day": int(is_bridge),
        "is_long_weekend": int(is_long_wknd),
        "is_school_holiday_bavaria": is_school_by,
        "is_school_holiday_bw": is_school_bw,
        "school_holiday_overlap": is_school_by + is_school_bw,
        "days_until_school_holiday": days_until_school_clipped,
        "days_since_school_holiday": days_since_school_clipped,
        "is_summer_season": is_summer,
        "is_winter_sports_season": is_winter_sports,
        "is_easter_period": int(is_easter),
        "is_christmas_period": is_xmas,
    }


def _is_bridge_day(d: date) -> bool:
    """True if d is a workday sandwiched between a holiday and a weekend."""
    if d.weekday() >= 5 or d in _BY_HOLIDAYS:
        return False
    yesterday = d - timedelta(days=1)
    tomorrow = d + timedelta(days=1)
    yesterday_off = yesterday.weekday() >= 5 or yesterday in _BY_HOLIDAYS
    tomorrow_off = tomorrow.weekday() >= 5 or tomorrow in _BY_HOLIDAYS
    return yesterday_off and tomorrow_off


def _is_long_weekend(d: date) -> bool:
    """True if d is part of a run of 3+ consecutive non-workdays."""
    off_days = {
        d + timedelta(days=i)
        for i in range(-2, 3)
        if (d + timedelta(days=i)).weekday() >= 5
        or (d + timedelta(days=i)) in _BY_HOLIDAYS
    }
    return len(off_days) >= 3 and (d.weekday() >= 5 or d in _BY_HOLIDAYS)


def _is_easter_period(d: date) -> bool:
    """±4 days around Easter Sunday."""
    y = d.year
    # Anonymous Gregorian algorithm
    a = y % 19
    b = y // 100
    c = y % 100
    d2 = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d2 - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    easter = date(y, month, day)
    delta = abs((d - easter).days)
    return delta <= 4


# ---------------------------------------------------------------------------
# Build a complete feature row for model input
# ---------------------------------------------------------------------------

def build_feature_row(
    d: date,
    time_slot: int,
    corridor: str,
    direction: str,
    baselines: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build one feature row for the model.
    baselines: dict with keys like ('A8E','outbound',5,3) -> mean kfz_h_slot
               (corridor, direction, day_of_week, slot) -> float
    """
    row = compute_calendar_features(d)
    row["time_slot"] = time_slot
    row["is_outbound"] = int(direction == "outbound")
    row["is_a93"] = int(corridor == "A93S")

    # Cyclic encoding: December adjacent to January, Sunday adjacent to Monday
    row["month_sin"] = math.sin(2 * math.pi * d.month / 12)
    row["month_cos"] = math.cos(2 * math.pi * d.month / 12)
    row["dow_sin"]   = math.sin(2 * math.pi * d.weekday() / 7)
    row["dow_cos"]   = math.cos(2 * math.pi * d.weekday() / 7)

    # Historical baseline features
    key_dow = (corridor, direction, d.weekday(), time_slot)
    key_month = (corridor, direction, d.month, time_slot)
    if baselines:
        row["hist_kfz_dow_slot"] = baselines.get("by_dow_slot", {}).get(key_dow, 0.0)
        row["hist_kfz_month_slot"] = baselines.get("by_month_slot", {}).get(key_month, 0.0)
        row["hist_sv_share"] = baselines.get("sv_share", {}).get(key_dow[:2], 0.08)
        row["clim_air_temp_c"] = baselines.get("clim_air_temp", {}).get(d.month, 10.0)
        row["is_frost_risk_month"] = int(
            baselines.get("frost_risk_months", set()).__contains__(d.month)
        )
    else:
        row["hist_kfz_dow_slot"] = 0.0
        row["hist_kfz_month_slot"] = 0.0
        row["hist_sv_share"] = 0.08
        row["clim_air_temp_c"] = 10.0
        row["is_frost_risk_month"] = 0

    return row


# ---------------------------------------------------------------------------
# Ordered feature columns (must match training order)
# ---------------------------------------------------------------------------

FEATURE_COLUMNS: list[str] = [
    # Cyclic calendar (replaces raw month/dow integers — avoids Dec→Jan gap)
    "month_sin",
    "month_cos",
    "dow_sin",
    "dow_cos",
    "week_of_year",
    "time_slot",
    # Public holidays
    "is_public_holiday_de",
    "is_public_holiday_bavaria",
    "is_bridge_day",
    "is_long_weekend",
    # School holidays
    "is_school_holiday_bavaria",
    "is_school_holiday_bw",
    "days_until_school_holiday",
    "days_since_school_holiday",
    # Seasonal events
    "is_easter_period",
    "is_christmas_period",
    # Road context
    "is_outbound",
    "is_a93",
    # Historical baselines (computed from train data only — dominant features)
    "hist_kfz_dow_slot",
    "hist_kfz_month_slot",
    # Climate proxy (hardcoded monthly averages — no leakage)
    "clim_air_temp_c",
]
# Removed: month, day_of_week (replaced by cyclic pairs), is_weekend (= dow>=5),
# is_summer_season/is_winter_sports_season/is_frost_risk_month (= f(month)),
# school_holiday_overlap (= by+bw sum), hist_sv_share (~8% constant)


# ---------------------------------------------------------------------------
# Explanation builder
# ---------------------------------------------------------------------------

def build_explanation(row: dict[str, Any], category: int) -> list[str]:
    """Generate human-readable explanation bullets for a forecast."""
    reasons: list[str] = []

    dow_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow = int(row.get("day_of_week", 0))

    if row.get("is_school_holiday_bavaria"):
        reasons.append("Bavaria school holidays active")
        if row.get("is_school_holiday_bw"):
            reasons.append("Baden-Württemberg also on school holiday — combined departure pressure")
    elif int(row.get("days_until_school_holiday", 30)) <= 3:
        reasons.append(f"Bavaria school holidays start in {row['days_until_school_holiday']} day(s)")
    elif int(row.get("days_since_school_holiday", 30)) <= 3:
        reasons.append("Bavaria school holidays just ended — return traffic wave")

    if row.get("is_public_holiday_bavaria"):
        reasons.append("Bavarian public holiday")
    elif row.get("is_public_holiday_de"):
        reasons.append("German public holiday")

    if row.get("is_bridge_day"):
        reasons.append("Bridge day (Brückentag) — extended long weekend")
    elif row.get("is_long_weekend"):
        reasons.append("Long weekend")

    if dow == 5 and row.get("is_outbound"):
        reasons.append("Saturday outbound — peak holiday departure direction")
    elif dow == 6 and not row.get("is_outbound"):
        reasons.append("Sunday inbound — peak holiday return direction")
    elif dow == 5:
        reasons.append(f"{dow_names[dow]} travel pattern")

    if row.get("is_summer_season"):
        reasons.append("Summer season (Jun–Sep) — tourism and leisure traffic peak")
    elif row.get("is_winter_sports_season") and row.get("is_outbound"):
        reasons.append("Winter sports season — Alpine resort traffic")

    if row.get("is_easter_period"):
        reasons.append("Easter travel period")
    if row.get("is_christmas_period"):
        reasons.append("Christmas / New Year period")

    if not reasons:
        if category <= 2:
            reasons.append("Normal traffic day — no major holiday or event drivers")
        else:
            reasons.append(f"{dow_names[dow]} with seasonal volume elevation")

    return reasons
