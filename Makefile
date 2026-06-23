# Automated Traffic Forecasting - A8 East / A93 South
# TUM Science Hackathon 2026 - challenge by Die Autobahn GmbH des Bundes
#
# Quick start on a fresh clone:   make quickstart && make run
# List every target:              make help

SHELL := /bin/bash

VENV          := backend/.venv
PY            := $(VENV)/bin/python
BACKEND_PORT  := 8000
FRONTEND_PORT := 8080
DATASET_ID    := 1Z1Icu2xuuuYB9pNRG6fOnGBT5MjY3wPC
ARCHIVE       := hackathon-dataset.zip
MODEL         := models/prediction_pipeline.joblib

# The pinned numpy/scikit-learn versions ship no wheels for Python 3.13+,
# so prefer an interpreter we know builds. Override with: make PYTHON=/path/to/python3.12
PYTHON ?= $(shell command -v python3.12 || command -v python3.11 || command -v python3)

.DEFAULT_GOAL := help
.PHONY: help quickstart install venv deps frontend-deps data train run backend frontend

help:
	@echo ''
	@echo 'Automated Traffic Forecasting - available targets'
	@echo ''
	@echo '  make quickstart   Full setup from a fresh clone (install + data + train)'
	@echo '  make run          Start backend and frontend together'
	@echo ''
	@echo '  make install      Create the Python venv and install all dependencies'
	@echo '  make data         Download and unpack the raw detector dataset'
	@echo '  make train        Run the 4-step pipeline and build the model'
	@echo ''
	@echo '  make backend      Start only the API      (http://localhost:$(BACKEND_PORT))'
	@echo '  make frontend     Start only the web UI   (http://localhost:$(FRONTEND_PORT))'
	@echo ''

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

quickstart: install data train
	@echo ''
	@echo 'Setup complete. Start the app with:  make run'

install: venv deps frontend-deps

venv:
	@test -d $(VENV) || { echo "Creating venv with $(PYTHON)..."; $(PYTHON) -m venv $(VENV); }
	@$(PY) -c 'import sys; v=sys.version_info; exit(0 if (3,10)<=(v.major,v.minor)<(3,13) else 1)' || { echo ''; echo "ERROR: $(VENV) runs $$($(PY) -V), but this project pins numpy 1.26 / scikit-learn 1.3, which have no wheels for 3.13+."; echo 'Install Python 3.12 and rerun:  make distclean && make install PYTHON=/path/to/python3.12'; exit 1; }

deps: venv
	@echo 'Installing Python dependencies...'
	@$(PY) -m pip install --quiet --upgrade pip
	@$(PY) -m pip install --quiet -r backend/requirements.txt
	@$(PY) -m pip install --quiet gdown

frontend-deps:
	@test -d frontend/node_modules || { echo 'Installing frontend dependencies...'; cd frontend && npm install; }

# ---------------------------------------------------------------------------
# Data and model
# ---------------------------------------------------------------------------

data: deps
	@if [ -d 'data/raw/DAUZ_2+0_1h_2023-2026' ]; then echo 'Raw data already present, skipping download.'; else \
	  echo 'Downloading dataset (~154 MB)...'; \
	  $(VENV)/bin/gdown '$(DATASET_ID)' -O $(ARCHIVE); \
	  echo 'Extracting...'; \
	  mkdir -p data/raw; \
	  unzip -o -q $(ARCHIVE) -d .; \
	  rm -rf __MACOSX $(ARCHIVE); \
	  mv -f 'DAUZ_2+0_1h_2023-2026' '2023-2025_1min_2+0_v' 'lt und fbt' A8_A93_MQ_locations.csv data/raw/ 2>/dev/null || true; \
	  echo 'Raw data ready in data/raw/'; \
	fi

train: deps
	@test -d 'data/raw/DAUZ_2+0_1h_2023-2026' || { echo 'No raw data found. Run: make data'; exit 1; }
	@echo 'Step 1/4  cleaning raw detector files...'
	@PYTHONPATH=backend $(PY) scripts/clean_data.py
	@echo 'Step 2/4  building features...'
	@PYTHONPATH=backend $(PY) scripts/build_features.py
	@echo 'Step 3/4  training the model...'
	@PYTHONPATH=backend $(PY) scripts/train_model.py
	@echo 'Step 4/4  exporting historical series...'
	@PYTHONPATH=backend $(PY) scripts/process_historical.py
	@echo ''
	@echo 'Model written to $(MODEL)'

# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------

run:
	@test -f $(MODEL) || { echo 'No trained model found. Run: make quickstart'; exit 1; }
	@test -d frontend/node_modules || { echo 'Frontend dependencies missing. Run: make install'; exit 1; }
	@echo 'Starting backend on :$(BACKEND_PORT) and frontend on :$(FRONTEND_PORT)  (Ctrl-C to stop both)'
	@trap 'kill 0' EXIT INT TERM; \
	  PYTHONPATH=backend $(PY) -m uvicorn backend.app.main:app --port $(BACKEND_PORT) & \
	  ( cd frontend && npm run dev ) & \
	  wait

backend:
	@test -f $(MODEL) || { echo 'No trained model found. Run: make quickstart'; exit 1; }
	PYTHONPATH=backend $(PY) -m uvicorn backend.app.main:app --port $(BACKEND_PORT) --reload

frontend:
	cd frontend && npm run dev

