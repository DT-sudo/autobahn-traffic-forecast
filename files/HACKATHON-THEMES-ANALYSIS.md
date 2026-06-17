# TUM Hackathon 2026 — Theme Analysis

All six themes share the same architecture:

```
data/raw/          →  backend/app/processors/  →  backend/app/api/  →  frontend/
(dataset file)        (theme-specific Python)      (FastAPI JSON)       (Lovable React)
```

The only things that change between themes are the processor logic, the API endpoints,
and the frontend visualizations. The project structure, git workflow, and scripts stay identical.

---

## Theme 1 — Autobahn GmbH: Traffic Forecasting

**Goal:** Predict traffic volume on highways A8 East and A93 South, with focus on weekends and Alpine holiday corridors.

**Datasets:**
- Historical traffic data (CSV/JSON) — datetime, location, volume, speed
- Public holiday calendar (CSV)
- Weather data (optional)

**Processor — `backend/app/processors/traffic_analyzer.py`:**
```python
# - Parse traffic CSV
# - Detect weekly/holiday patterns
# - Forecast next day / next weekend
# - Time-series analysis (moving averages, trend decomposition)
```

**API endpoints:**
```
POST /api/analyze   → traffic forecast for given date range
GET  /api/forecast  → next weekend prediction
GET  /api/patterns  → detected traffic patterns
```

**Frontend visualizations:**
- Timeline chart: hourly traffic volume
- Heatmap: intensity by day of week
- Prediction table: next-day forecast
- Alert banner: expected congestion peaks

**Data layout:**
```
data/raw/
├── traffic_data.csv        (datetime, location, volume, speed)
├── holidays.csv            (date, name)
└── weather.json            (optional)

data/processed/
├── patterns.json           (detected regularities)
└── forecast.json           (predictions)
```

---

## Theme 2 — LBenergy GmbH: Intelligent Building Control

**Goal:** Optimize heating in tents and temporary structures — predict when to switch on, detect failures, visualize savings.

**Datasets:**
- Temperature sensor data (JSON/CSV) — timestamp, temperature, humidity
- Event schedule — when people arrive and leave
- Historical energy consumption

**Processor — `backend/app/processors/temperature_optimizer.py`:**
```python
# - Parse sensor data
# - Correlate with event schedule
# - Predict optimal heater activation time
# - Detect anomalies (sensor failure, heater fault)
# - Calculate energy savings in kWh and EUR
```

**API endpoints:**
```
POST /api/predict    → when to activate heater
GET  /api/anomalies  → detected faults
GET  /api/savings    → energy saved (kWh / EUR)
```

**Frontend visualizations:**
- Temperature timeline (past + current)
- Heater schedule with predicted on/off times
- Anomaly alerts (red flags)
- ROI dashboard: energy saved

**Data layout:**
```
data/raw/
├── sensor_data.json        (timestamp, temperature, humidity)
├── heater_logs.csv         (on/off events, energy, timestamp)
└── schedule.json           (event calendar)

data/processed/
├── predictions.json        (activation schedule)
└── anomalies.json          (detected faults)
```

---

## Theme 3 — MTU Aero Engines: Autonomous Rover + Person Detection

**Goal:** Robot inspects a work zone for safety — detect personnel, verify PPE compliance, navigate with SLAM, fuse sensors.

**Datasets:**
- Video files from robot camera (MP4 or frames)
- LiDAR point clouds (JSON)
- Sensor telemetry (distance, temperature)

**Processors:**
```python
# backend/app/processors/person_detector.py
# - Load video frames / images
# - Run YOLOv8 object detection
# - Verify PPE compliance (helmet, gloves, suit)
# - Track individuals to avoid duplicates
# - Generate safety compliance report

# backend/app/processors/slam_processor.py
# - Process LiDAR point clouds
# - Detect obstacles
# - Generate occupancy map
```

**API endpoints:**
```
POST /api/analyze         → analyze video / sensor data
GET  /api/persons         → detected person count + timestamps
GET  /api/safety-report   → PPE compliance status
GET  /api/map             → robot path + obstacle map
```

**Frontend visualizations:**
- Video player with bounding boxes around detected persons
- Compliance table: person ID, PPE status (pass / fail)
- 2D map: robot path + obstacles
- Alert: person detected without required PPE

**Data layout:**
```
data/raw/
├── video_feed.mp4           (robot camera)
├── lidar_data.json          (point clouds)
└── sensor_telemetry.csv     (distance, temperature)

data/processed/
├── detected_persons.json    (count, timestamps)
├── ppe_report.json          (compliance status per person)
└── map.json                 (obstacles, path)
```

---

## Theme 4 — TUM Finance: Executive Compensation Analysis

**Goal:** Analyze CEO/CFO compensation against peer companies, detect anomalies, provide benchmarking over 15 years.

**Datasets:**
- 15 years of compensation data (CSV) — base salary, bonus, stock options
- Company financial metrics — revenue, sector, headcount
- Peer group definitions

**Processor — `backend/app/processors/compensation_analyzer.py`:**
```python
# - Parse compensation CSV
# - Group by peer companies
# - Calculate median, mean, percentiles
# - Detect outliers (Isolation Forest)
# - Benchmark individual company vs peer group
```

**API endpoints:**
```
POST /api/analyze      → full compensation analysis
GET  /api/benchmarks   → company vs peer comparison
GET  /api/anomalies    → unusual compensation structures
GET  /api/trends       → 15-year trend for a company
```

**Frontend visualizations:**
- Company search and selector
- Compensation breakdown: base / bonus / stock options
- Peer comparison: box plot vs peer group
- Red-flag highlights: detected anomalies
- Trend line chart: 15-year compensation history

**Data layout:**
```
data/raw/
├── compensation_data.csv   (company, year, CEO_salary, bonus, stock)
└── company_metrics.csv     (company, revenue, sector, employees)

data/processed/
├── benchmarks.json         (peer group statistics)
├── anomalies.json          (flagged cases)
└── analysis.json           (detailed stats)
```

---

## Theme 5 — Würth Elektronik: Student–Industry Platform

**Goal:** Scalable communication platform connecting students, companies, and educators after the hackathon.

**Datasets:**
- Student profiles (CSV) — name, skills, interests, contact
- Company representatives (JSON) — company, open positions, interests
- Event attendance data

**Processor — `backend/app/processors/network_analyzer.py`:**
```python
# - Parse student and company data
# - Match based on skills / interests
# - Track engagement and connections
```

**API endpoints:**
```
POST /api/users           → register student or company
POST /api/connect         → match student with company
GET  /api/recommendations → suggested connections
POST /api/followup        → save follow-up action
```

**Frontend visualizations:**
- Student profile card: skills, interests
- Company search and opportunity list
- Recommendations: "you might be interested in..."
- Follow-up tracker: saved contacts and resources

**Data layout:**
```
data/raw/
├── students.csv            (name, skills, interests, contact)
└── companies.json          (company, reps, opportunities)

data/processed/
├── matches.json            (student–company recommendations)
└── engagement.json         (who connected with whom)
```

---

## Theme 6 — TUM Network: Privacy-Preserving AI (TEEs)

**Goal:** Confidential AI tutor for students using Trusted Execution Environments — analyze learning data without exposing raw records.

**Datasets:**
- Student learning data (encrypted JSON)
- Course materials
- Assessment results

**Processor — `backend/app/processors/privacy_analyzer.py`:**
```python
# - Process encrypted/sensitive student data
# - Produce aggregate insights only (no PII in output)
# - Generate learning recommendations per cohort
```

**API endpoints:**
```
POST /api/analyze        → analyze (with privacy constraints)
GET  /api/insights       → aggregate stats only (no individual records)
GET  /api/recommendations → cohort-level learning suggestions
```

**Frontend visualizations:**
- Student progress dashboard (aggregated only, no raw scores)
- Class-level statistics (no individual exposure)
- Learning path recommendations

**Data layout:**
```
data/raw/
├── student_data_encrypted.json
└── course_materials.json

data/processed/
├── aggregate_stats.json    (cohort-level aggregates, no PII)
└── insights.json
```

---

## Summary

All six themes use the identical project structure. The only theme-specific work is:

| File | What to adapt |
|------|---------------|
| `backend/app/processors/analyzer.py` | Processing and prediction logic |
| `backend/app/api/routes.py` | Endpoint names and request/response shapes |
| `scripts/train_model.py` | Target variable, features, algorithm |
| `docs/THEME_SPECIFIC.md` | Dataset columns, success criteria |
| `docs/MODEL_CONTRACT.md` | Model input/output interface |
| `CLAUDE.md` — Mission | Theme description |

Everything else — structure, scripts, git workflow, frontend connection — stays the same.
