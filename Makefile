# Automated Traffic Forecasting - A8 East / A93 South
# TUM Science Hackathon 2026 - challenge by Die Autobahn GmbH des Bundes
#
# List every target:              make help

SHELL := /bin/bash

VENV          := backend/.venv
PY            := $(VENV)/bin/python

PYTHON ?= python3

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

deps: venv
	@echo 'Installing Python dependencies...'
	@$(PY) -m pip install --quiet --upgrade pip
	@$(PY) -m pip install --quiet -r backend/requirements.txt

frontend-deps:
	@test -d frontend/node_modules || { echo 'Installing frontend dependencies...'; cd frontend && npm install; }

