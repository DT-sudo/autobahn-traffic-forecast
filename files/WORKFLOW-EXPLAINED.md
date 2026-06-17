# Project Workflow — File Roles and Team Guide

Using the Alpine traffic forecasting theme (Autobahn A8/A93) as a concrete example.

---

## Why API Endpoints / Routes Exist — Core Idea in 3 Lines

**Problem:** The React frontend runs in the browser. The browser cannot run Python.
**Solution:** Python starts a small server. The frontend sends HTTP requests to it. The server responds with JSON.
**routes.py** is the list of addresses on that server: "at this URL I respond with this data."

```
Browser (Lovable React)              Python (FastAPI)
───────────────────────              ────────────────
fetch("POST /api/analyze")  →→→      routes.py receives the request
                                     calls traffic_analyzer.py
                                     reads traffic_data.csv
                                     calculates forecast
                            ←←←      returns JSON: { forecast: [...] }
Recharts renders chart ✓
```

---

## Every File — One-Line Purpose (traffic theme: A8 / A93)

```
backend/
├── app/
│   ├── main.py
│   │   └─ Starts the server, enables CORS (so the browser can reach Python),
│   │      connects routes.py. No need to change this file.
│   │
│   ├── api/routes.py
│   │   └─ LIST OF SERVER ADDRESSES.
│   │      Example: "when the frontend sends POST /api/analyze —
│   │      take the file from data/raw/, pass it to traffic_analyzer.py,
│   │      return JSON with the forecast."
│   │      ← Participant 2 adapts this for the theme.
│   │
│   └── processors/analyzer.py  (→ traffic_analyzer.py for this theme)
│       └─ ALL THE LOGIC: open CSV, find patterns, compute forecast,
│          return a dict with results.
│          ← Participant 2 writes the main work here.
│
├── requirements.txt
│   └─ List of Python libraries: fastapi, pandas, scikit-learn, joblib.
│      pip install -r requirements.txt — everything is ready.

data/
├── raw/traffic_data.csv          ← Participant 4 places the dataset here (not in git)
└── processed/forecast.json       ← processor writes results here (not in git)

models/
└── prediction_pipeline.joblib    ← trained ML pipeline (not in git)

scripts/
├── clean_data.py                 ← Step 1: clean CSV (remove empty rows, fix types)
├── build_features.py             ← Step 2: build features (hour, day_of_week, is_holiday)
├── train_model.py                ← Step 3: train model, export .joblib
└── download_data.sh              ← download dataset from Google Drive in one command

frontend/                         ← Lovable React — Participant 3 generates here
                                     fetch → http://localhost:8000/api/analyze

docs/
├── ARCHITECTURE.md               ← system diagram (for orientation)
├── API.md                        ← what server addresses exist and what they accept
├── MODEL_CONTRACT.md             ← what the model takes as input and what it returns
├── THEME_SPECIFIC.md             ← filled on hackathon day: dataset columns, goal
└── DATA_STRUCTURE.md             ← file formats and how to process them
```

---

## Workflow — Traffic Theme, All Participants Work via Claude Code

### 9:00 AM — Theme Announced (Participant 1, ~10 minutes)

```bash
# Fill two files and push
# docs/THEME_SPECIFIC.md — dataset structure, columns, success criteria
# CLAUDE.md → Mission — one sentence describing the specific task
git commit -m "docs: traffic theme details"
git push origin dev
```

---

### 10:00 AM — Participant 2 (Backend + ML) works via Claude Code

**Participant 2 tells Claude:**

> "I have `traffic_data.csv` with columns: datetime, location_id, volume, speed.
> I need to:
> 1. detect weekly and holiday patterns
> 2. predict traffic for the next 7 days
> Write `backend/app/processors/traffic_analyzer.py` and update
> `backend/app/api/routes.py` with endpoints `POST /api/analyze` and `GET /api/forecast`."

**Claude writes** `traffic_analyzer.py`:

```python
# Reads traffic_data.csv with pandas
# Finds patterns (df.groupby(['dayofweek', 'hour'])['volume'].mean())
# Trains or loads .joblib pipeline
# Returns dict with forecast
```

**Claude writes** `routes.py`:

```python
@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    result = analyze_traffic(req.filename)
    return {"success": True, "forecast": result}

@router.get("/forecast")
async def forecast():
    # returns already-computed forecast
```

**Participant 2 runs:**

```bash
uvicorn backend.app.main:app --reload --port 8000
# http://localhost:8000/docs — see all endpoints, test them interactively
```

---

### 10:00 AM — Participant 3 (Frontend) works in Lovable

**Participant 3 tells Lovable:**

> "Create a traffic dashboard:
> - Timeline chart (hourly traffic volume) using Recharts
> - Prediction table: next 7 days traffic forecast
> - Alert banner when peak traffic is expected
>
> Data comes from `POST http://localhost:8000/api/analyze`
> with body `{ "filename": "traffic_data.csv" }`.
>
> Use TanStack Query for fetching, shadcn/ui for components,
> Tailwind CSS 4 for styling."

Lovable generates the React component. Participant 3 copies it into `frontend/` and verifies the fetch works.

---

### 10:00 AM — Participant 4 (Data / ML) works via Claude Code

**Participant 4 tells Claude:**

> "Update `scripts/clean_data.py` for a traffic CSV with columns:
> datetime, location_id, volume, speed.
> Handle missing values and parse datetime properly.
> Then update `scripts/build_features.py` to add: hour, day_of_week, is_holiday."

```bash
# Place dataset
cp ~/Downloads/traffic_data.csv data/raw/

# Run pipeline in order
python scripts/clean_data.py
python scripts/build_features.py    # adds: hour, dayofweek, is_holiday
python scripts/train_model.py       # creates models/prediction_pipeline.joblib
```

---

## Who Is Responsible for What

| Participant | Files | What to tell Claude |
|-------------|-------|---------------------|
| Participant 1 | `docs/THEME_SPECIFIC.md` `CLAUDE.md` | Fill manually — 10 minutes |
| Participant 2 | `backend/app/processors/` `backend/app/api/routes.py` | "Write processor that reads CSV and returns forecast JSON. Add FastAPI endpoints." |
| Participant 3 | `frontend/` (via Lovable) | "Create React dashboard with Recharts that fetches from POST /api/analyze" |
| Participant 4 | `scripts/clean_data.py` `scripts/build_features.py` `scripts/train_model.py` | "Update scripts for traffic CSV with these columns: ..." |

---

## Key Point

Participant 2 and Participant 3 work **in parallel and independently** because `routes.py`
defines the contract — Participant 3 knows the URL and JSON format in advance from `docs/API.md`
without waiting for Participant 2 to finish the processing logic.

```
Participant 2 builds the engine   Participant 3 builds the dashboard
both know: POST /api/analyze returns { "forecast": [...] }
they connect at the end — it just works
```
