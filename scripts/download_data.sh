#!/bin/bash
# Download prepared dataset archive from Google Drive.
# Usage: bash scripts/download_data.sh <GOOGLE_DRIVE_FILE_ID>
#
# Before running: pip install gdown

set -e

FILE_ID="${1:-YOUR_GOOGLE_DRIVE_FILE_ID}"
ARCHIVE="hackathon-dataset.zip"

echo "Creating directories..."
mkdir -p data/raw data/processed data/examples

echo "Downloading dataset (file ID: $FILE_ID)..."
python -m gdown "$FILE_ID" -O "$ARCHIVE"

echo "Extracting..."
unzip -o "$ARCHIVE" -d .

echo "Cleaning up archive..."
rm -f "$ARCHIVE"

echo ""
echo "Done. Files in data/raw/:"
ls data/raw/
