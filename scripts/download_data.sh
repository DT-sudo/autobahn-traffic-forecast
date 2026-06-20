#!/bin/bash
# Download the dataset archive from Google Drive.
#
# Usage:
#   bash scripts/download_data.sh <GOOGLE_DRIVE_FILE_ID>
#
# The FILE_ID is the long string in the Google Drive share URL:
#   https://drive.google.com/file/d/FILE_ID_HERE/view
#
# Requires: pip install gdown
#
# What this script expects on Google Drive:
#   A single zip file containing the data/raw/ folder structure, e.g.:
#     data/raw/DAUZ_2+0_1h_2023-2026/FG1_Lang_*.csv
#     data/raw/2023-2025_1min_2+0_v/FG1_Kurz_*.csv
#     data/raw/lt und fbt/FG3_WUD_*.csv
#     data/raw/A8_A93_MQ_locations.csv

set -e

FILE_ID="${1:-}"

if [ -z "$FILE_ID" ]; then
  echo "Usage: bash scripts/download_data.sh <GOOGLE_DRIVE_FILE_ID>"
  echo ""
  echo "Get the file ID from the Google Drive share URL:"
  echo "  https://drive.google.com/file/d/FILE_ID_HERE/view"
  exit 1
fi

ARCHIVE="hackathon-dataset.zip"

echo "Creating directories..."
mkdir -p data/raw data/processed data/examples models

echo "Downloading from Google Drive (file ID: $FILE_ID)..."
python -m gdown "$FILE_ID" -O "$ARCHIVE"

echo "Extracting..."
unzip -o "$ARCHIVE" -d .

echo "Cleaning up archive..."
rm -f "$ARCHIVE"

echo ""
echo "Done. Files found in data/raw/:"
find data/raw -type f | sort
