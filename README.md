# Automated Traffic Forecasting for Alpine Holiday Corridors

**A machine-learning replacement for the manually produced German motorway Traffic Calendar (*Fahrkalender*) — generating colour-coded daily congestion forecasts up to one year ahead for the A8 East and A93 South corridors.**

---

## Project Context

| | |
|---|---|
| **Event** | TUM Science Hackathon 2026 |
| **Host institution** | Technical University of Munich (TUM) — one of Europe's leading technical universities |
| **Challenge partner** | **Die Autobahn GmbH des Bundes** — the German federal motorway operator, responsible for the entire ~13,000 km Autobahn network |
| **Challenge** | Automated Traffic Forecasting for Alpine Holiday Corridors A8 East & A93 South |
| **Data** | Proprietary loop-detector measurements, 2023–2025, provided by the challenge partner |

Die Autobahn GmbH publishes an annual **Traffic Calendar** that tells millions of travellers which days on the Alpine holiday routes will be congested. It is compiled **by hand, by domain experts**, every year.

This project replaces that manual process with a reproducible, data-driven system: a model trained on three years of real detector data that produces the same colour-coded forecast automatically, for any date up to a year ahead, in both travel directions and at six-slot daily resolution.

The corridors matter because they carry the whole of southern Germany's holiday traffic into Austria and the Alps — the **A8 East** (Munich → Salzburg) and the **A93 South** (Inntal → Kufstein). On peak departure weekends these routes are among the most congested in the country.

---

## What the System Does

Given a corridor, a direction and a date range, it returns for every day:

- a **traffic category from 1 to 5**, rendered green → yellow → orange → red → dark red,
- an **estimated vehicle volume**,
- a **breakdown across six time slots**, so a traveller can see that Saturday morning is jammed while Saturday evening is clear,
- a **human-readable explanation** of *why* — school holidays, bridge days, Easter, winter-sports season, and so on.

It needs **no real-time sensor feed**. Every prediction is derived from the calendar alone, which is what makes a twelve-month horizon possible.

---

## Quick Start

Requires **Python 3.11 or 3.12** (see note below), **Node.js 18+**, and `make`.

```bash
git clone git@github.com:DT-sudo/TUM-Hackathon.git
cd TUM-Hackathon

make quickstart     # installs dependencies, downloads the dataset, trains the model
make run            # starts the API and the web UI together
```

Then open **http://localhost:8080**.

That is the whole setup. `make quickstart` takes roughly 5–10 minutes, most of it the 154 MB dataset download and the model training.

### Available commands

| Command | What it does |
|---------|--------------|
| `make quickstart` | Full setup from a fresh clone: dependencies + data + trained model |
| `make run` | Start backend (`:8000`) and frontend (`:8080`) together; Ctrl-C stops both |
| `make install` | Python virtualenv, backend dependencies, `npm install` |
| `make data` | Download and unpack the raw detector dataset into `data/raw/` |
| `make train` | Run the four-step pipeline and write `models/prediction_pipeline.joblib` |
| `make backend` | Start only the API, with autoreload |
| `make frontend` | Start only the web UI |
| `make check` | Verify the API is up and the model is loaded |
| `make stop` | Stop whatever is still listening on either port |
| `make clean` | Remove generated data, model and caches |
| `make distclean` | Also remove the virtualenv and `node_modules` |

### A note on the Python version

The project pins `numpy 1.26` and `scikit-learn 1.3`, which publish **no wheels for Python 3.13 or newer**. The Makefile automatically prefers `python3.12` or `python3.11` if either is on your `PATH`, and stops with a clear message if the virtualenv ends up on an unsupported interpreter. To point it at a specific interpreter:

```bash
make distclean
make install PYTHON=/usr/local/bin/python3.12
```

### Running it manually

If you would rather not use `make`:

```bash
# 1. Backend environment
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt gdown

# 2. Dataset  (~154 MB, extracts to the repo root, then move into data/raw/)
backend/.venv/bin/gdown "1Z1Icu2xuuuYB9pNRG6fOnGBT5MjY3wPC" -O hackathon-dataset.zip
unzip -o hackathon-dataset.zip -d . && rm -rf __MACOSX hackathon-dataset.zip
mkdir -p data/raw && mv "DAUZ_2+0_1h_2023-2026" "2023-2025_1min_2+0_v" "lt und fbt" A8_A93_MQ_locations.csv data/raw/

# 3. Build the model  (four steps, in order)
PYTHONPATH=backend backend/.venv/bin/python scripts/clean_data.py
PYTHONPATH=backend backend/.venv/bin/python scripts/build_features.py
PYTHONPATH=backend backend/.venv/bin/python scripts/train_model.py
PYTHONPATH=backend backend/.venv/bin/python scripts/process_historical.py

# 4. Run  (two terminals)
PYTHONPATH=backend backend/.venv/bin/python -m uvicorn backend.app.main:app --port 8000
cd frontend && npm install && npm run dev
```

The frontend dev server runs on **port 8080** (configured by the Lovable Vite preset), and the API on **8000**.

---

## License

MIT — see [LICENSE](LICENSE).
