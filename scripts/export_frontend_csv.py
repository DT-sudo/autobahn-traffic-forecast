"""
Export the 4 frontend traffic CSV files from the trained model.

Generates one CSV per corridor/direction (written to data/export/) in the exact
format the frontend parses:
    day,traffic,1 part,2 part,3 part,4 part,5 part,6 part
    20.06.2026,heavy,heavy,heavy,heavy,moderate,increased,heavy
    ...

- day      : DD.MM.YYYY
- traffic  : overall daily traffic level = average of the 6 part levels
- N part   : traffic level for time slot N (1=00-06 ... 6=22-24)

Traffic level strings map from the model's 1-5 category:
    1 low | 2 increased | 3 moderate | 4 heavy | 5 extreme

Run from repo root (model + processed data must already exist):
    PYTHONPATH=backend backend/.venv/bin/python scripts/export_frontend_csv.py
"""
from __future__ import annotations

import csv
import sys
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.processors.traffic_analyzer import get_analyzer  # noqa: E402

# Forecast horizon (matches the example files: ~1 year ahead from today)
DATE_FROM = date(2026, 6, 20)
DATE_TO = date(2027, 6, 30)

OUTPUT_DIR = REPO_ROOT / "data" / "export"

HEADER = ["day", "traffic", "1 part", "2 part", "3 part", "4 part", "5 part", "6 part"]

# filename -> (corridor, direction)
FILES: dict[str, tuple[str, str]] = {
    "A8easttraffic.csv": ("A8E", "outbound"),   # A8 East  → Salzburg
    "A8westtraffic.csv": ("A8E", "inbound"),    # A8 West  → Munich
    "A93southtraffic.csv": ("A93S", "outbound"),  # A93 South → Kufstein
    "A93northtraffic.csv": ("A93S", "inbound"),   # A93 North → Rosenheim
}

# model category (1-5) -> frontend traffic level string
CATEGORY_TO_LEVEL = {
    1: "low",
    2: "increased",
    3: "moderate",
    4: "heavy",
    5: "extreme",
}


def _iso_to_ddmmyyyy(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def _daily_from_parts(part_cats: list[int]) -> int:
    """Daily traffic category = average of the 6 slot categories (round half up, clamp 1-5)."""
    avg = sum(part_cats) / len(part_cats)
    return min(5, max(1, int(avg + 0.5)))


# analyzer.forecast() caps a single call at 366 days, so split longer ranges.
CHUNK_DAYS = 365


def _forecast_range(analyzer, corridor: str, direction: str) -> list[dict]:
    """Forecast [DATE_FROM, DATE_TO] in <=366-day chunks and concatenate."""
    out: list[dict] = []
    start = DATE_FROM
    while start <= DATE_TO:
        end = min(start + timedelta(days=CHUNK_DAYS - 1), DATE_TO)
        out.extend(analyzer.forecast(corridor, direction, start, end))
        start = end + timedelta(days=1)
    return out


def export_file(analyzer, filename: str, corridor: str, direction: str) -> int:
    forecast = _forecast_range(analyzer, corridor, direction)
    out_path = OUTPUT_DIR / filename

    with out_path.open("w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(HEADER)
        for day in forecast:
            slots = {s["slot"]: s["category"] for s in day["time_slots"]}
            part_cats = [slots[i] for i in range(1, 7)]
            daily_cat = _daily_from_parts(part_cats)
            row = [
                _iso_to_ddmmyyyy(day["date"]),
                CATEGORY_TO_LEVEL[daily_cat],
                *[CATEGORY_TO_LEVEL[c] for c in part_cats],
            ]
            writer.writerow(row)

    return len(forecast)


def main() -> None:
    analyzer = get_analyzer()
    if not analyzer.is_loaded:
        print(
            "[WARN] Model not loaded — output will be mock data. "
            "Run scripts/train_model.py first for accurate forecasts.",
            file=sys.stderr,
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, (corridor, direction) in FILES.items():
        n = export_file(analyzer, filename, corridor, direction)
        print(f"  wrote {filename:24s} {corridor}/{direction:8s} {n} days")

    print(f"\nDone. 4 files written to {OUTPUT_DIR}/ ({DATE_FROM} -> {DATE_TO})")


if __name__ == "__main__":
    main()
