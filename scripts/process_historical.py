#!/usr/bin/env python3
"""
Aggregate raw hourly detector CSVs into daily 6-slot traffic levels.
Outputs: data/processed/historical_<CORRIDOR>_<DIRECTION>.json
Keys are DD.MM.YYYY strings matching the frontend's row map format.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path(__file__).parent.parent / "data" / "raw" / "DAUZ_2+0_1h_2023-2026"
OUT_DIR = Path(__file__).parent.parent / "data" / "processed"

# filename substring → (corridor, direction)
FILE_MAP = {
    "_Sbg_H,": ("A8E",  "outbound"),
    "_Mch_H,": ("A8E",  "inbound"),
    "_Kff,":   ("A93S", "outbound"),
    "_Ro,":    ("A93S", "inbound"),
}

LEVELS = ["low", "increased", "moderate", "heavy", "extreme"]
LEVEL_IDX = {l: i for i, l in enumerate(LEVELS)}


def hour_to_slot(h: int) -> int:
    if h < 6:  return 1
    if h < 10: return 2
    if h < 14: return 3
    if h < 18: return 4
    if h < 22: return 5
    return 6


def to_level(val: float, thresholds: list[float]) -> str:
    for i, t in enumerate(thresholds):
        if val <= t:
            return LEVELS[i]
    return LEVELS[-1]


def process_road(corridor: str, direction: str, files: list[Path]) -> dict:
    frames = []
    for f in files:
        df = pd.read_csv(f, sep=";", usecols=["datum", "t_start", "kfz_h"],
                         dtype={"datum": str, "t_start": str, "kfz_h": str})
        df["kfz_h"] = pd.to_numeric(df["kfz_h"], errors="coerce").fillna(0)
        df["hour"] = df["t_start"].str[:2].astype(int)
        frames.append(df[["datum", "hour", "kfz_h"]])

    data = pd.concat(frames, ignore_index=True)

    # Average across detectors for same (date, hour), then sum into slots
    hourly = data.groupby(["datum", "hour"])["kfz_h"].mean().reset_index()
    hourly["slot"] = hourly["hour"].map(hour_to_slot)
    slot_sums = hourly.groupby(["datum", "slot"])["kfz_h"].sum().reset_index()

    # Percentile thresholds on slot-level sums
    vals = slot_sums["kfz_h"].values
    thresholds = [np.percentile(vals, p) for p in (40, 60, 75, 90)]
    print(f"  {corridor} {direction}: thresholds {[round(t) for t in thresholds]} "
          f"(n={len(slot_sums)} slot-days)")

    slot_sums["level"] = slot_sums["kfz_h"].apply(lambda x: to_level(x, thresholds))

    result: dict[str, dict] = {}
    for datum, grp in slot_sums.groupby("datum"):
        grp = grp.sort_values("slot")
        slots = grp["level"].tolist()
        while len(slots) < 6:
            slots.append("low")
        avg_idx = max(0, min(len(LEVELS) - 1, round(sum(LEVEL_IDX[l] for l in slots) / len(slots))))
        daily = LEVELS[avg_idx]
        result[datum] = {"daily": daily, "slots": slots[:6]}

    return result


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    road_files: dict[tuple, list[Path]] = {}
    for fpath in sorted(RAW_DIR.glob("*.csv")):
        for keyword, road_key in FILE_MAP.items():
            if keyword in fpath.name:
                road_files.setdefault(road_key, []).append(fpath)
                break

    if not road_files:
        print(f"No files found in {RAW_DIR}", file=sys.stderr)
        sys.exit(1)

    for (corridor, direction), files in sorted(road_files.items()):
        print(f"\n{corridor} {direction}: {len(files)} detector file(s)")
        result = process_road(corridor, direction, files)
        out = OUT_DIR / f"historical_{corridor}_{direction}.json"
        out.write_text(json.dumps(result))
        print(f"  → {out}  ({len(result)} days)")

    print("\nDone.")


if __name__ == "__main__":
    main()
