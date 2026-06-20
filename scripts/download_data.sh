#!/bin/bash
# Download the dataset archive from Google Drive.
#
# Usage (with default file ID baked in):
#   bash scripts/download_data.sh
#
# Or override with a different file ID:
#   bash scripts/download_data.sh <GOOGLE_DRIVE_FILE_ID>
#
# Requires: pip install gdown
#
# Dataset URL: https://drive.google.com/file/d/1Z1Icu2xuuuYB9pNRG6fOnGBT5MjY3wPC/view
# Note: the file must be shared as "Anyone with the link" for gdown to work.
#       If it is restricted, download manually from the browser and place as hackathon-dataset.zip.

set -e

DEFAULT_FILE_ID="1Z1Icu2xuuuYB9pNRG6fOnGBT5MjY3wPC"
FILE_ID="${1:-$DEFAULT_FILE_ID}"

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
