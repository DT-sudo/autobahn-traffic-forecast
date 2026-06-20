"""
Step 1: Load and clean all raw traffic + temperature files.
Run from repo root: python scripts/clean_data.py

Outputs:
  data/processed/cleaned_traffic_hourly.csv   — all 12 hourly detector files stacked
  data/processed/cleaned_weather_hourly.csv   — FBT/LT temperature data, hourly averages
"""
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Site → corridor + direction mapping
# Parse from filename: FG1_Lang_{site},DE{channels}_agg1h_..._bis_....csv
# ---------------------------------------------------------------------------

def _parse_site_info(filepath: Path) -> tuple[str, str, str]:
    """
    Returns (site_id, corridor, direction) from an FG1_Lang_* filename.
    corridor ∈ {'A8E', 'A93S'}
    direction ∈ {'outbound', 'inbound'}

    A93S direction codes confirmed by organizers:
      _Kff → outbound (toward Kufstein / Austria)
      _Ro  → inbound  (toward Rosenheim / Germany)
    """
    stem = filepath.stem  # remove .csv
    # Strip prefix FG1_Lang_
    after = stem.replace("FG1_Lang_", "")
    # Split on ',DE' to drop channel list and date suffix
    site_id = after.split(",DE")[0]

    # Determine corridor by recognisable site-name tokens
    a8_tokens = {"MQB25", "MQQ37", "MQQ209", "MQQ213", "MQQ245"}
    a93_tokens = {"Inntal", "Kiefersfelden", "Gletschergarten", "MQDZ"}
    if any(t in site_id for t in a8_tokens):
        corridor = "A8E"
    elif any(t in site_id for t in a93_tokens):
        corridor = "A93S"
    else:
        corridor = "UNKNOWN"
        print(f"  [WARN] Could not determine corridor for: {filepath.name}")

    # Direction suffix mapping (all confirmed by Die Autobahn GmbH organizers)
    if "_Mch" in site_id:
        direction = "inbound"    # toward Munich
    elif "_Sbg" in site_id:
        direction = "outbound"   # toward Salzburg
    elif "_Kff" in site_id:
        direction = "outbound"   # toward Kufstein (Austria)
    elif "_Ro" in site_id:
        direction = "inbound"    # toward Rosenheim (Germany)
    else:
        direction = "UNKNOWN"
        print(f"  [WARN] Could not determine direction for: {filepath.name}")

    return site_id, corridor, direction


def load_hourly_file(filepath: Path) -> pd.DataFrame:
    """
    Load one FG1_Lang_*_agg1h_*.csv file.
    Handles: UTF-8-BOM encoding, semicolon delimiter, German date format,
             trailing comma junk in header row.
    """
    df = pd.read_csv(filepath, sep=";", encoding="utf-8-sig")
    # Strip trailing comma junk from header (safe even when not present)
    df.columns = [c.split(",")[0] for c in df.columns]

    # Parse date + time into a single timestamp
    df["datum"] = pd.to_datetime(df["datum"], format="%d.%m.%Y")
    df["timestamp"] = df["datum"] + pd.to_timedelta(df["t_start"])
    df = df.drop(columns=["datum", "t_start"]).sort_values("timestamp")

    return df


def clean_traffic_files() -> pd.DataFrame:
    """Load all 12 FG1_Lang_* hourly files, tag with corridor/direction, stack."""
    pattern = "FG1_Lang_*_agg1h_*.csv"
    files = sorted(RAW.rglob(pattern))  # rglob = recursive, finds files in any subdirectory

    if not files:
        print(f"[ERROR] No files matching '{pattern}' found in {RAW}/")
        print("        Place the Die Autobahn GmbH dataset files there and retry.")
        sys.exit(1)

    print(f"Found {len(files)} hourly traffic file(s).")
    frames: list[pd.DataFrame] = []

    for fp in files:
        site_id, corridor, direction = _parse_site_info(fp)
        print(f"  Loading {fp.name}  →  {corridor} / {direction}")

        df = load_hourly_file(fp)
        df["site"] = site_id
        df["corridor"] = corridor
        df["direction"] = direction

        # Basic cleaning
        df = df.dropna(subset=["kfz_h"])          # drop rows with no vehicle count
        df = df[df["kfz_h"] >= 0]                 # remove negative counts

        # Remove extreme outliers (> 99.9th percentile per corridor/direction)
        p999 = df["kfz_h"].quantile(0.999)
        outliers = df["kfz_h"] > p999
        if outliers.any():
            print(f"    Removing {outliers.sum()} outlier rows (kfz_h > {p999:.0f})")
            df = df[~outliers]

        # sv_h nulls always co-occur with kfz_h nulls (verified on full MQB25 file).
        # After dropna(kfz_h) above, sv_h should never be null — but clip to be safe.
        df["sv_h"] = df["sv_h"].clip(lower=0)

        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(["corridor", "direction", "site", "timestamp"])

    out = PROCESSED / "cleaned_traffic_hourly.csv"
    combined.to_csv(out, index=False)
    print(f"\nSaved {len(combined):,} rows → {out}")
    print(f"Date range: {combined['timestamp'].min()} → {combined['timestamp'].max()}")
    print(f"Corridors: {combined['corridor'].unique().tolist()}")
    print(f"Directions: {combined['direction'].unique().tolist()}")
    return combined


# ---------------------------------------------------------------------------
# Temperature data (FBT = road surface, LT = air)
# ---------------------------------------------------------------------------

def load_temp_file(filepath: Path, value_col_name: str) -> pd.DataFrame:
    """Load one FG3_WUD_FBT/LT_*_agg1min_*.csv file."""
    df = pd.read_csv(filepath, sep=";")
    df["t_start"] = pd.to_datetime(df["t_start"])
    # The value column may be 'fbt' in both FBT and LT files (copy-pasted export)
    value_col = [c for c in df.columns if c != "t_start"][0]
    df = df.rename(columns={value_col: value_col_name}).sort_values("t_start")
    return df


def clean_weather_files() -> pd.DataFrame | None:
    """
    Load all FBT (road surface temp) + LT (air temp) files for the
    Rosenheim B15n station on A8 East.
    Aggregates minute readings → hourly mean/min/max.
    """
    fbt_files = sorted(RAW.rglob("FG3_WUD_FBT_*_agg1min_*.csv"))
    lt_files  = sorted(RAW.rglob("FG3_WUD_LT_*_agg1min_*.csv"))

    if not fbt_files and not lt_files:
        print("[INFO] No temperature files found — weather features will use climatological defaults.")
        return None

    dfs_fbt: list[pd.DataFrame] = []
    for fp in fbt_files:
        print(f"  Loading {fp.name}")
        dfs_fbt.append(load_temp_file(fp, "surface_temp_c"))

    dfs_lt: list[pd.DataFrame] = []
    for fp in lt_files:
        print(f"  Loading {fp.name}")
        dfs_lt.append(load_temp_file(fp, "air_temp_c"))

    def concat_and_resample(dfs: list[pd.DataFrame], col: str, resample_hz: str = "1h") -> pd.DataFrame | None:
        if not dfs:
            return None
        combined = pd.concat(dfs, ignore_index=True)
        combined = combined.drop_duplicates("t_start").sort_values("t_start")
        hourly = (
            combined.set_index("t_start")[col]
            .resample(resample_hz)
            .agg(["mean", "min", "max"])
            .rename(columns=lambda c: f"{col}_{c}")
            .reset_index()
        )
        return hourly

    fbt_hourly = concat_and_resample(dfs_fbt, "surface_temp_c")
    lt_hourly  = concat_and_resample(dfs_lt, "air_temp_c")

    if fbt_hourly is None and lt_hourly is None:
        return None

    if fbt_hourly is not None and lt_hourly is not None:
        weather = fbt_hourly.merge(lt_hourly, on="t_start", how="outer")
    else:
        weather = fbt_hourly or lt_hourly

    weather = weather.rename(columns={"t_start": "timestamp"})
    weather = weather.sort_values("timestamp")

    out = PROCESSED / "cleaned_weather_hourly.csv"
    weather.to_csv(out, index=False)
    print(f"\nSaved {len(weather):,} hourly weather rows → {out}")
    return weather


# ---------------------------------------------------------------------------
# Detector locations
# ---------------------------------------------------------------------------

def load_detector_locations() -> None:
    candidates = list(RAW.rglob("A8_A93_MQ_locations.csv"))
    if not candidates:
        print("[INFO] A8_A93_MQ_locations.csv not found — skipping.")
        return
    loc_file = candidates[0]
    loc = pd.read_csv(loc_file, sep=";", decimal=",")
    out = PROCESSED / "detector_locations.csv"
    loc.to_csv(out, index=False)
    print(f"Saved {len(loc)} detector locations → {out}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Step 1: Clean traffic data")
    print("=" * 60)
    clean_traffic_files()

    print("\n" + "=" * 60)
    print("Step 1b: Clean weather data (optional)")
    print("=" * 60)
    clean_weather_files()

    print("\n" + "=" * 60)
    print("Step 1c: Copy detector locations")
    print("=" * 60)
    load_detector_locations()

    print("\nDone. Run python scripts/build_features.py next.")
