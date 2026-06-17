# 👨‍💼 TEAM LEAD INSTRUCTIONS - Git Setup (15 minutes)
## ОБНОВЛЕНО: Универсальная структура для любой темы хакатона

**ЭТО ИНСТРУКЦИЯ ДЛЯ ТЕБЯ (team lead). Делай это ВСЁ САМ, один раз.**

После того как ты выполнишь эти шаги, каждый член команды будет следовать его собственный чек-лист.

---

## ⚠️ ВАЖНО: Универсальная структура

Мы пока не знаем точную тему хакатона. Поэтому эта структура работает для **ЛЮБОЙ** темы:
- Traffic forecasting (Autobahn)
- Building control (LBenergy)
- Autonomous rover (MTU)
- Board pay analysis (TUM Finance)
- Student platform (Würth)
- Privacy AI (TUM Network)

**Главное:** Независимо от темы - мы ВСЕГДА:
1. Получаем датасеты (CSV, JSON, XLSX)
2. Обрабатываем их в backend
3. Выводим результаты через frontend (Lovable)

---

## 📋 ШАГ 0: Проверь предусловия (2 минуты)

На твоём компе должно быть:
- [ ] Git установлен (`git --version` в терминале)
- [ ] GitHub аккаунт создан (https://github.com)
- [ ] Node.js установлен (`node --version`)
- [ ] VS Code установлен
- [ ] Claude Pro подписка ($20/месяц)

Если что-то не установлено — установи перед началом.

---

## 📝 ШАГ 1: Создай репозиторий на GitHub (3 минуты)

### 1.1 Зайди на GitHub

- Открой https://github.com
- Залогинься
- Нажми зелёную кнопку **"New"** (вверху слева, может быть под иконкой меню)

### 1.2 Заполни форму создания репо

```
Repository name: hackathon-project
Description: AI-powered hackathon project (flexible for any challenge)
Public или Private: (выбери Public если хочешь чтобы все видели)

✅ Initialize this repository with:
   ☑ Add a README file
   ☑ Add .gitignore (выбери "Node")
   ☑ Choose a license (выбери "MIT")
```

Нажми **"Create repository"**

✅ **Результат:** у тебя есть GitHub репо с одной веткой main

---

## 💻 ШАГ 2: Клонируй репо на свой компьютер (2 минуты)

### 2.1 Копируй ссылку репо

На странице репо (https://github.com/YOUR_USERNAME/hackathon-project) нажми зелёную кнопку **"Code"**

Копируй HTTPS ссылку (например: `https://github.com/your-username/hackathon-project.git`)

### 2.2 Клонируй через терминал

Открой терминал (Mac: Terminal, Windows: PowerShell):

```bash
cd ~/Desktop
git clone https://github.com/YOUR_USERNAME/hackathon-project.git
cd hackathon-project
```

Замени `YOUR_USERNAME` на своё имя пользователя GitHub.

✅ **Проверка:**
```bash
git status
# должно быть: On branch main, Your branch is up to date with 'origin/main'
```

Ты на main ветке.

---

## 🌿 ШАГ 3: Создай develop ветку (2 минуты)

```bash
# Создай ветку develop
git checkout -b develop

# Пушь на GitHub
git push -u origin develop
```

✅ **Проверка на GitHub:**

Зайди на страницу репо → вверху нажми на кнопку "main" → должна быть ветка develop

---

## 📂 ШАГ 4: Создай УНИВЕРСАЛЬНУЮ структуру проекта (3 минуты)

Эта структура подходит для ЛЮБОЙ темы:

```bash
# Убедись что ты в корне проекта
pwd  # должно быть /path/to/hackathon-project

# ===== BACKEND: Датасеты и обработка =====
mkdir -p backend/src/{api,processors,models}
mkdir -p backend/data/{raw,processed}
mkdir -p backend/uploads

# ===== CONFIGS: Общие настройки =====
mkdir -p config
mkdir -p .claude

# ===== DOCS: Документация =====
mkdir -p docs

# ===== Создай пустые маркеры для git =====
touch backend/data/raw/.gitkeep
touch backend/data/processed/.gitkeep
touch backend/uploads/.gitkeep

# ===== Создай файлы для backend =====
echo "// API routes - будут заполнены в зависимости от темы" > backend/src/api/routes.js
echo "// Data processors - будут заполнены в зависимости от темы" > backend/src/processors/analyzer.js
echo "// ML Models - опционально" > backend/src/models/predictor.js

# ===== Создай основной server файл =====
echo "// Main Express server" > backend/server.js

echo "✅ Структура создана!"
```

**Результат: вот как выглядит твоя папка**

```
hackathon-project/
├── .git/                          (git скрытая папка)
├── .github/
├── node_modules/                  (создастся после npm install)
│
├── backend/                       ← BACKEND (обработка данных + API)
│   ├── src/
│   │   ├── api/
│   │   │   └── routes.js          ← API endpoints
│   │   │
│   │   ├── processors/
│   │   │   └── analyzer.js        ← Обработка датасетов
│   │   │
│   │   └── models/
│   │       └── predictor.js       ← ML модели (опционально)
│   │
│   ├── data/                      ← ДАТАСЕТЫ (НЕ В ГИТ!)
│   │   ├── raw/                  ← Исходные файлы
│   │   ├── processed/            ← Обработанные результаты
│   │
│   ├── uploads/                   ← Загруженные файлы (НЕ В ГИТ!)
│   │
│   ├── server.js                  ← Express server
│   └── package.json
│
├── frontend/                      ← LOVABLE (генерируется через Lovable)
│   └── [выгружается из Lovable]
│
├── config/                        ← Конфигурация
│   └── database.config.js
│
├── docs/                          ← Документация
│   ├── API.md
│   ├── DATA_STRUCTURE.md
│   └── THEME_SPECIFIC.md          ← Заполнится когда узнаешь тему
│
├── .claude/
│   └── settings.json              ← разрешения для Claude Code
│
├── CLAUDE.md                      ← инструкции для Claude
├── .env.example
├── .gitignore                     ← ВАЖНО! Исключает датасеты
├── .prettierrc.json
├── .eslintrc.json
├── package.json
├── README.md
└── LICENSE
```

---

## 📄 ШАГ 5: Создай конфигурационные файлы (5 минут)

Для каждого файла ниже:
1. Открой VS Code: `code .`
2. Создай новый файл (File → New)
3. Скопируй содержимое
4. Сохрани

### 5.1 Файл: `CLAUDE.md`

```markdown
# Hackathon Project - Claude Code Guide

## 🎯 Mission
Analyze datasets and build AI solution for TUM Science Hackathon 2026.

## 🏗️ Architecture

```
Data Layer → Processing Layer → API Layer → Frontend (Lovable)

backend/data/raw/        → backend/src/processors/     → backend/src/api/     → frontend/
(CSV, JSON, XLSX)         (analyzer.js)                (routes.js)           (UI components)
```

## 📂 Folder Structure & Team Domains

```
backend/
├── src/api/           ← ПЕТЯ: API endpoints, routes
├── src/processors/    ← ПЕТЯ: Dataset processing
├── data/raw/          ← Исходные датасеты (НЕ в гит)
└── data/processed/    ← Результаты анализа
```

## ✅ Rules for Claude Code

### DO ✅
- ✅ Edit in `backend/src/api/` и `backend/src/processors/`
- ✅ Create API endpoints that process datasets
- ✅ Write processors to handle CSV/JSON/XLSX files
- ✅ Return JSON responses for frontend
- ✅ Test with sample datasets locally

### DON'T ❌
- ❌ Never push dataset files to git (they're in .gitignore)
- ❌ Don't commit API keys or credentials
- ❌ Don't modify main branch before end of hackathon
- ❌ Don't send large files via git (anything >100MB)

## 💻 Essential Commands

### Setup (First Time Only)
```bash
npm install
npm run dev  # Start backend on http://localhost:3000
```

### Daily Workflow
```bash
# Start of day
git checkout develop
git pull origin develop
npm install  # if dependencies changed

# During work
git status
git add .
git commit -m "feat: [what you added]"
git push origin develop
```

## 🔄 API Specification (Will be filled based on theme)

### Dataset Analysis Endpoint (Template)
```
POST /api/analyze

Request: { "filename": "dataset.csv", "analysisType": "summary|detailed" }
Response: { "success": true, "results": { "stats": {...}, "insights": [...] } }
```

### Get Results
```
GET /api/results

Response: { "timestamp": "...", "data": {...}, "statistics": {...} }
```

## 🚀 When You Know The Theme

Update these sections:
1. `docs/THEME_SPECIFIC.md` - what to analyze
2. `backend/src/processors/` - specific processing logic
3. `backend/src/api/` - theme-specific endpoints
4. `CLAUDE.md` - update "Mission" section
```

### 5.2 Файл: `.claude/settings.json`

```json
{
  "allowedTools": [
    "CreateFile",
    "EditFile",
    "ReadFile",
    "DeleteFile",
    "Bash(npm install:*)",
    "Bash(npm run dev:*)",
    "Bash(npm test:*)",
    "Bash(npm run lint:*)",
    "Bash(git status:*)",
    "Bash(git add:*)",
    "Bash(git commit:*)",
    "Bash(git push:*)",
    "Bash(git pull:*)",
    "Bash(git log:*)"
  ],
  "bypassPermissions": false,
  "defaultMode": "ask"
}
```

### 5.3 Файл: `package.json`

```json
{
  "name": "hackathon-project",
  "version": "0.1.0",
  "type": "module",
  "description": "AI-powered hackathon project with dataset analysis",
  "scripts": {
    "dev": "node --watch backend/server.js",
    "start": "node backend/server.js",
    "test": "vitest",
    "lint": "eslint backend/src/"
  },
  "keywords": ["hackathon", "claude", "ai", "dataset", "analysis"],
  "author": "Hackathon Team",
  "license": "MIT",
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "multer": "^1.4.5-lts.1",
    "csv-parser": "^3.0.0",
    "xlsx": "^0.18.5",
    "dotenv": "^16.3.1",
    "sqlite3": "^5.1.6"
  },
  "devDependencies": {
    "vitest": "^1.0.0",
    "eslint": "^8.55.0"
  }
}
```

### 5.4 Файл: `.prettierrc.json`

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "useTabs": false,
  "trailingComma": "es5",
  "printWidth": 100
}
```

### 5.5 Файл: `.eslintrc.json`

```json
{
  "env": {
    "browser": true,
    "es2021": true,
    "node": true
  },
  "extends": [
    "eslint:recommended"
  ],
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "module"
  },
  "rules": {
    "no-console": "warn",
    "no-unused-vars": "warn"
  }
}
```

### 5.6 Файл: `.env.example`

```
# Backend Server
PORT=3000
NODE_ENV=development

# Database (optional)
DATABASE_URL=sqlite:./data/database.db

# API Configuration
API_TIMEOUT=30000
MAX_FILE_SIZE=104857600

# Dataset Processing
DATA_PATH=./backend/data/raw/
OUTPUT_PATH=./backend/data/processed/
```

### 5.7 Файл: `.gitignore` (MOST IMPORTANT!)

```
# ========================================
# 🚫 ДАТАСЕТЫ - НИКОГДА НЕ КОММИТИМ!
# ========================================
backend/data/raw/**/*.csv
backend/data/raw/**/*.json
backend/data/raw/**/*.xlsx
backend/data/raw/**/*.xls
backend/data/raw/**/*.parquet
backend/data/raw/**/*.tsv
backend/data/processed/**/*.csv
backend/data/processed/**/*.json
backend/uploads/**/*

# But keep folders with .gitkeep
!backend/data/raw/.gitkeep
!backend/data/processed/.gitkeep
!backend/uploads/.gitkeep

# ========================================
# Node.js / npm
# ========================================
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
package-lock.json
yarn.lock

# ========================================
# Environment Variables
# ========================================
.env
.env.local
.env.*.local

# ========================================
# Build Output
# ========================================
dist/
build/
.next/

# ========================================
# IDE & Editor
# ========================================
.vscode/
.idea/
*.swp
*.swo
.DS_Store
Thumbs.db

# ========================================
# Runtime & Temp
# ========================================
.cache
logs
*.log
*.tmp

# ========================================
# Database
# ========================================
*.db
*.sqlite
```

### 5.8 Файл: `README.md`

```markdown
# Hackathon Project

AI-powered dataset analysis platform for TUM Science Hackathon 2026.

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- npm or yarn
- Git

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/hackathon-project.git
cd hackathon-project
npm install
```

### Development

```bash
npm run dev
# Backend starts on http://localhost:3000
```

### Testing

```bash
npm test
```

## 🏗️ Architecture

- **Backend**: Express.js API + Dataset processors
- **Frontend**: Lovable-generated React UI
- **Data**: Local storage (not in git)

## 📊 Themes Supported

This flexible structure works for any hackathon theme:
- Traffic forecasting
- Building control
- Autonomous systems
- Financial analysis
- Student platforms
- Privacy-preserving AI

## 👥 Team Roles

- **Backend Dev**: Dataset processing & API
- **Frontend Dev**: Lovable UI & visualization
- **Data Eng**: Dataset management & quality

## 🔗 Documentation

- `docs/API.md` - API specification
- `docs/DATA_STRUCTURE.md` - Dataset structure
- `docs/THEME_SPECIFIC.md` - Theme-specific details (filled during hackathon)
- `CLAUDE.md` - Claude Code instructions

## 📄 License

MIT
```

### 5.9 Файл: `docs/API.md`

```markdown
# API Specification

Will be updated based on the specific hackathon theme.

## Endpoints (Template)

### Analyze Dataset
```
POST /api/analyze

Request:
{
  "filename": "dataset.csv",
  "analysisType": "summary" | "detailed" | "custom"
}

Response:
{
  "success": true,
  "results": {
    "rowCount": 1000,
    "columns": ["col1", "col2"],
    "statistics": {...},
    "insights": [...]
  }
}
```

### Get Results
```
GET /api/results

Response:
{
  "timestamp": "...",
  "datasetName": "...",
  "analysis": {...}
}
```

### Health Check
```
GET /api/health

Response:
{
  "status": "ok",
  "version": "0.1.0"
}
```
```

---

## 📤 ШАГ 6: Первый коммит и пуш (1 минута)

```bash
# Убедись что ты в папке проекта
pwd  # должно быть /path/to/hackathon-project

# Добавь все файлы
git add .

# Коммит
git commit -m "chore: initial project setup with universal structure"

# Пушь в develop
git push origin develop
```

✅ **Проверка на GitHub:**

Зайди на https://github.com/YOUR_USERNAME/hackathon-project
- Переключись на ветку `develop` (кнопка вверху)
- Должны видны все твои файлы и папки

---

## 👥 ШАГ 7: Добавь членов команды как collaborators (3 минуты)

### 7.1 Зайди в Settings репо

На странице репо:
- Нажми **Settings** (правая верхняя часть)
- В левом меню найди **Collaborators** (может быть под "Access")

### 7.2 Добавь каждого члена команды

Нажми **"Add people"** (или зелёная кнопка "Invite a collaborator")

Для каждого члена команды (Петя, Саша, Маша):
1. Введи его GitHub username
2. Выбери role: **Maintain** или **Push access**
3. Нажми **Add**

✅ **Результат:** каждый получит приглашение (emailом или в GitHub notifications)

---

## 📧 ШАГ 8: Пошли инструкции команде (2 минуты)

Отправь в чат/email каждому члену команды сообщение:

```
Привет!

Репо готов к работе. Вот что вам нужно сделать:

1. Примите приглашение от GitHub (если пришло письмо)

2. Клонируйте репо:
   git clone https://github.com/YOUR_USERNAME/hackathon-project.git
   cd hackathon-project

3. Переходите на develop:
   git checkout develop

4. Устанавливайте зависимости:
   npm install

5. Открываете в VS Code:
   code .

6. Устанавливаете Claude Code extension в VS Code

СТРУКТУРА РЕПО:

backend/src/api/         ← Петя: API endpoints
backend/src/processors/  ← Петя: Dataset processing
backend/data/raw/        ← Датасеты (локально, НЕ в гит)
frontend/                ← Саша: Lovable UI

КОГДА УЗНАЕМ ТЕМУ:

Мы обновим:
- docs/THEME_SPECIFIC.md (что анализировать)
- backend/src/processors/ (специфичная логика)
- backend/src/api/ (специфичные endpoints)
- CLAUDE.md (Mission раздел)

Git workflow на день:
1. Утро: git pull origin develop
2. Работаете с Claude Code
3. Коммитите: git commit -m "feat: что вы добавили"
4. Пушите: git push origin develop

Вопросы? Звоните!
```

---

## ✅ ФИНАЛЬНЫЙ ЧЕКЛИСТ (Проверь себя)

- [ ] GitHub репо создан (main + develop ветки)
- [ ] Структура папок создана (backend/, data/, docs/)
- [ ] CLAUDE.md добавлен
- [ ] .claude/settings.json добавлен
- [ ] package.json обновлён
- [ ] .gitignore добавлен (исключает датасеты!)
- [ ] Все конфиги добавлены (.prettierrc, .eslintrc, .env.example)
- [ ] README.md обновлён
- [ ] Первый коммит запушен в develop
- [ ] Все члены команды добавлены как collaborators
- [ ] Каждый получил приглашение и инструкции

---

## 🎬 День хакатона (утро 9:00 AM)

Когда ВСЕ готовы и знаете ТЕМУ:

1. **Ты (Team Lead):**
   - Создаёшь `docs/THEME_SPECIFIC.md` с деталями темы
   - Обновляешь `CLAUDE.md` (Mission раздел)
   - Пушишь обновления: `git commit -m "chore: theme details added" && git push origin develop`

2. **Петя (Backend):**
   ```bash
   git checkout develop && git pull origin develop
   npm install
   npm run dev  # Backend listening on :3000
   # Создаёт endpoint для анализа датасетов
   # Создаёт processor для обработки CSV/JSON/XLSX
   ```

3. **Саша (Frontend):**
   - Заходит на https://lovable.dev
   - Создаёт новый проект
   - Генерирует React UI для:
     - Upload датасета
     - Display результатов анализа
     - Charts/tables visualization
   - Интегрирует fetch к backend API

4. **Маша (Data/QA):**
   - Кладёт датасет в `backend/data/raw/` (локально!)
   - Тестирует workflow
   - Помогает с debugging

---

## 🚀 Когда всё готово

```bash
# Финальная синхронизация
git checkout develop
git pull origin develop

# Мержим в main (ты делаешь)
git checkout main
git pull origin main
git merge develop
git push origin main

# Готово к демо! 🎉
```

---

**Ты готов! Кидай ссылку команде.** 🚀

---

**Дата:** [Заполни свою дату хакатона]
**Ссылка на репо:** https://github.com/YOUR_USERNAME/hackathon-project
**Ветка для работы:** develop
**Ветка для сдачи:** main
```

Сохрани файл (Ctrl+S или Cmd+S).
