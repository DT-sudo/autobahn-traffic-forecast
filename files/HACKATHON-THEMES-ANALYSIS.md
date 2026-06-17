# 🎯 Анализ тем TUM Hackathon 2026 + Universal Architecture

## Твоя Архитектура ИДЕАЛЬНО подходит для ВСЕХ тем!

```
┌─────────────────┐
│  Любая ТЕМА     │
├─────────────────┤
│ Датасет        │ ← Каждая тема получает датасет
│ (CSV/JSON/     │   (15 лет данных / 1000+ записей / видео / сенсоры)
│  XLSX)         │
└────────┬────────┘
         │
         ▼ (backend/data/raw/)
┌─────────────────┐
│  BACKEND        │  ← Петя обрабатывает
│ - Processors    │    данные в зависимости от темы
│ - API endpoints │
│ - ML/stats      │
└────────┬────────┘
         │
         ▼ (JSON response)
┌─────────────────┐
│  FRONTEND       │  ← Саша показывает
│  (Lovable UI)   │    результаты красиво
│ - Visualize     │
│ - Charts        │
│ - Dashboard     │
└─────────────────┘
```

---

## 📊 ВСЕ ТЕМЫ РАЗОБРАНЫ

### 1️⃣ **Autobahn GmbH** - Traffic Forecasting
**Что:**
- Прогнозирование трафика на автобанах A8 East & A93 South
- Анализ паттернов в выходные и праздники (Alpine holiday corridors)

**Датасеты:**
- Исторические данные трафика (CSV/JSON)
- Календарь праздников
- Погодные данные (опционально)

**Backend (Петя):**
```
processors/trafficAnalyzer.js:
- Parse датасет трафика
- Detect паттерны (выходные vs рабочие дни)
- Forecast трафик на следующий день/неделю
- Time-series analysis

api/routes.js:
POST /api/analyze → прогноз трафика
GET /api/forecast → prediction для выходных
GET /api/patterns → выявленные паттерны
```

**Frontend (Саша через Lovable):**
```
- Timeline chart: трафик по часам
- Heatmap: интенсивность по дням
- Prediction table: прогноз на следующий день
- Alert system: когда ожидается пик
```

**Структура данных:**
```
backend/data/raw/
├── traffic_data.csv  (datetime, location, volume, speed)
├── weather.json      (optional)
└── holidays.csv      (dates, names)

backend/data/processed/
├── patterns.json     (выявленные закономерности)
└── forecast.json     (прогнозы)
```

---

### 2️⃣ **LBenergy GmbH** - Intelligent Building Control
**Что:**
- Оптимизация отопления в палатках и временных сооружениях
- PREDICT (когда включать), DETECT (сбои), VISUALIZE (экономия)

**Датасеты:**
- Данные датчиков температуры (JSON/CSV)
- Расписание мероприятий (когда люди приходят/уходят)
- Историческое потребление энергии

**Backend (Петя):**
```
processors/temperatureOptimizer.js:
- Parse sensor data
- Correlate с расписанием
- Predict когда включать heater
- Detect аномалии (сбой датчика или heater'а)
- Calculate energy savings

api/routes.js:
POST /api/predict → когда включить
GET /api/anomalies → обнаруженные проблемы
GET /api/savings → сэкономлено энергии/€
```

**Frontend (Саша):**
```
- Temperature timeline: прошлые + текущие значения
- Heater schedule: когда должен включиться
- Anomaly alerts: красные флаги
- ROI dashboard: сколько сэкономили
```

**Структура данных:**
```
backend/data/raw/
├── sensor_data.json  (timestamp, temperature, humidity)
├── heater_logs.csv   (on/off, energy, timestamp)
└── schedule.json     (event calendar)

backend/data/processed/
├── predictions.json  (когда включать)
└── anomalies.json    (сбои)
```

---

### 3️⃣ **MTU Aero Engines** - Autonomous Rover + Person Detection
**Что:**
- Робот проверяет рабочую зону на безопасность
- DETECT персоны и проверяет что они в защите (PPE)
- SLAM навигация
- Sensor fusion и visualization

**Датасеты:**
- Видеофайлы с камер робота (MP4 или frames)
- LiDAR данные (point clouds, JSON)
- Sensor telemetry (距離, temperature)

**Backend (Петя):**
```
processors/personDetector.js:
- Load video frames / images
- Run YOLOv8 для detection человека
- Check PPE compliance (hat, gloves, suit)
- Track personas (avoid duplicates)
- Generate safety report

processors/slamProcessor.js:
- Process LiDAR point clouds
- Detect obstacles
- Generate map

api/routes.js:
POST /api/analyze → analyze video
GET /api/persons → count людей
GET /api/safety-report → compliance
GET /api/map → robot path + obstacles
```

**Frontend (Саша):**
```
- Video player: show detected persons (bounding boxes)
- Safety compliance table: имя, PPE status (✓ или ✗)
- Live map: robot location + obstacles
- Alert: если кто-то без защиты
```

**Структура данных:**
```
backend/data/raw/
├── video_feed.mp4        (robot camera)
├── lidar_data.json       (point clouds)
└── sensor_telemetry.csv  (distance, temp)

backend/data/processed/
├── detected_persons.json (count, timestamps)
├── ppe_report.json       (compliance status)
└── map.json              (obstacles, path)
```

---

### 4️⃣ **TUM Finance** - Executive Compensation Analysis
**Что:**
- Анализ зарплат CEO/CFO против peer companies
- Обнаружение аномалий в компенсации
- Benchmarking

**Датасеты:**
- 15 лет данных о зарплатах (CSV)
- Финансовые показатели компаний (размер, сектор, прибыль)
- Peer group данные

**Backend (Петя):**
```
processors/compensationAnalyzer.js:
- Parse compensation data (base salary, bonuses, stock options)
- Group по peer companies
- Calculate median/mean/percentiles
- Detect outliers (ML: isolation forest)
- Benchmark against peers

api/routes.js:
POST /api/analyze → analyze compensation
GET /api/benchmarks → compare vs peers
GET /api/anomalies → unusual structures
GET /api/trends → как менялось за годы
```

**Frontend (Саша):**
```
- Company search: find and analyze
- Compensation breakdown: базовая/бонусы/опции
- Peer comparison: box plot vs peers
- Red flags: аномалии подсвечены красным
- Trend chart: как менялось за 15 лет
```

**Структура данных:**
```
backend/data/raw/
├── compensation_data.csv (company, year, CEO_salary, bonus, stock, ...)
└── company_metrics.csv   (company, revenue, sector, employees)

backend/data/processed/
├── benchmarks.json       (peer group stats)
├── anomalies.json        (unusual cases)
└── analysis.json         (detailed stats)
```

---

### 5️⃣ **Würth Elektronik** - Student-Industry Platform
**Что:**
- Scalable communication platform
- Связь студентов ↔ компании ↔ educators
- Follow-up после hackathon

**Датасеты:**
- Student profiles (CSV)
- Company representatives (JSON)
- Event data (who attended, interests)

**Backend (Петя):**
```
processors/networkAnalyzer.js:
- Parse student/company data
- Match interests
- Track engagement

api/routes.js:
POST /api/users → register студент или компания
POST /api/connect → match студента с компанией
GET /api/recommendations → suggestions
POST /api/followup → stay in touch
```

**Frontend (Саша):**
```
- Student profile: skills, interests
- Company search: find opportunities
- Recommendations: "you might like..."
- Follow-up: resources, documents, contacts
```

**Структура данных:**
```
backend/data/raw/
├── students.csv   (name, skills, interests, contact)
└── companies.json (company, reps, opportunities)

backend/data/processed/
├── matches.json   (student-company recommendations)
└── engagement.json (who connected with whom)
```

---

### 6️⃣ **TUM Network** - Privacy-Preserving AI (TEEs)
**Что:**
- Confidential AI tutor для студентов
- Multiple parties, no data sharing
- TEEs (Trusted Execution Environments)

**Датасеты:**
- Student learning data (encrypted, JSON)
- Course materials
- Assessment results

**Backend (Петя):**
```
processors/privacyAnalyzer.js:
- Process encrypted student data
- Generate insights без sharing raw data
- Aggregate statistics

api/routes.js:
POST /api/analyze → analyze (encrypted)
GET /api/insights → aggregate insights only
GET /api/recommendations → learning suggestions
```

**Frontend (Саша):**
```
- Student dashboard: progress (без sensitive data)
- Learning recommendations
- Aggregated class stats (no individual data exposed)
```

**Структура данных:**
```
backend/data/raw/
├── student_data_encrypted.json
└── course_materials.json

backend/data/processed/
├── aggregate_stats.json  (only aggregates, no PII)
└── insights.json
```

---

## 🎯 ВЫВОД: Твоя структура идеальна!

Все 6 тем используют одинаковую архитектуру:

```
┌─────────────────────────────────────────────────┐
│  UNIVERSAL STRUCTURE (подходит для ВСЕХ тем)   │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. backend/data/raw/                          │
│     └─ Получаешь датасет в любом формате       │
│                                                  │
│  2. backend/src/processors/                    │
│     └─ Обрабатываешь его (специфично для темы) │
│                                                  │
│  3. backend/src/api/                           │
│     └─ Exponируешь результаты через API        │
│                                                  │
│  4. frontend/ (Lovable)                        │
│     └─ Показываешь красиво                      │
│                                                  │
└─────────────────────────────────────────────────┘
```

**Различия между темами:**
- ✅ ДА: какой датасет, как анализировать, какой output
- ❌ НЕТ: структура кода, архитектура, git workflow

---

## 🚀 ЧТО ДЕЛАТЬ ПОСЛЕ УЗНАВАНИЯ ТЕМЫ

Как только узнаешь тему (9:00 AM день хакатона):

1. **Обнови `docs/THEME_SPECIFIC.md`:**
   ```markdown
   # [НАЗВАНИЕ ТЕМЫ]
   
   ## Что анализируем?
   ...
   
   ## Датасет структура
   ...
   
   ## API endpoints
   ...
   
   ## Как оценивают успех?
   ...
   ```

2. **Обнови `CLAUDE.md`:**
   - Mission раздел с конкретной целью
   - API endpoints (специфичные для темы)

3. **Петя начинает:**
   ```bash
   # backend/src/processors/analyzer.js
   # Специфичная логика для темы
   
   # backend/src/api/routes.js
   # API endpoints для темы
   ```

4. **Саша начинает:**
   - Lovable UI для входных данных
   - Visualization для результатов

---

## 📋 ФИНАЛЬНЫЙ ЧЕКЛИСТ

Перед хакатоном:
- [ ] Прочитал все 6 тем
- [ ] Понял что структура подходит для всех
- [ ] Создал универсальный репо (TEAM-LEAD-SETUP-UPDATED.md)
- [ ] Все готово к быстрому обновлению когда узнаем тему

День хакатона:
- [ ] Узнали тему
- [ ] Обновили docs/THEME_SPECIFIC.md
- [ ] Обновили CLAUDE.md
- [ ] Петя начал писать processors/
- [ ] Саша начал создавать UI в Lovable
- [ ] Маша положила датасет в backend/data/raw/
- [ ] PROFIT! 🚀

---

**Ты готов к ЛЮБОЙ теме!** 💪
