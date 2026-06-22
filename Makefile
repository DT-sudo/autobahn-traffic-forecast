# Automated Traffic Forecasting - A8 East / A93 South
# TUM Science Hackathon 2026 - challenge by Die Autobahn GmbH des Bundes
#
# List every target:              make help

SHELL := /bin/bash

VENV          := backend/.venv
PY            := $(VENV)/bin/python

# The pinned numpy/scikit-learn versions ship no wheels for Python 3.13+,
# so prefer an interpreter we know builds. Override with: make PYTHON=/path/to/python3.12
PYTHON ?= $(shell command -v python3.12 || command -v python3.11 || command -v python3)

.DEFAULT_GOAL := help
.PHONY: help install venv deps frontend-deps

help:
	@echo ''
	@echo 'Automated Traffic Forecasting - available targets'
	@echo ''
	@echo '  make install      Create the Python venv and install all dependencies'
	@echo ''

install: venv deps frontend-deps

venv:
	@test -d $(VENV) || { echo "Creating venv with $(PYTHON)..."; $(PYTHON) -m venv $(VENV); }
	@$(PY) -c 'import sys; v=sys.version_info; exit(0 if (3,10)<=(v.major,v.minor)<(3,13) else 1)' || { echo ''; echo "ERROR: $(VENV) runs $$($(PY) -V), but this project pins numpy 1.26 / scikit-learn 1.3, which have no wheels for 3.13+."; echo 'Install Python 3.12 and rerun:  make distclean && make install PYTHON=/path/to/python3.12'; exit 1; }

deps: venv
	@echo 'Installing Python dependencies...'
	@$(PY) -m pip install --quiet --upgrade pip
	@$(PY) -m pip install --quiet -r backend/requirements.txt

frontend-deps:
	@test -d frontend/node_modules || { echo 'Installing frontend dependencies...'; cd frontend && npm install; }

