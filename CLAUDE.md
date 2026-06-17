# Hackathon Project - Claude Code Guide

## Mission
Analyze datasets and build AI solution for TUM Science Hackathon 2026.

## Architecture

```
Data Layer → Processing Layer → API Layer → Frontend (Lovable)

backend/data/raw/        → backend/src/processors/     → backend/src/api/     → frontend/
(CSV, JSON, XLSX)         (analyzer.js)                (routes.js)           (UI components)
```

## Folder Structure & Team Domains

```
backend/
├── src/api/           ← Backend Dev: API endpoints, routes
├── src/processors/    ← Backend Dev: Dataset processing
├── data/raw/          ← Raw datasets (NOT in git)
└── data/processed/    ← Analysis results (NOT in git)
```

## Rules for Claude Code

### DO
- Edit in `backend/src/api/` and `backend/src/processors/`
- Create API endpoints that process datasets
- Write processors to handle CSV/JSON/XLSX files
- Return JSON responses for frontend
- Test with sample datasets locally

### DON'T
- Never push dataset files to git (they're in .gitignore)
- Don't commit API keys or credentials
- Don't modify main branch before end of hackathon
- Don't send large files via git (anything >100MB)

## Essential Commands

### Setup (First Time Only)
```bash
npm install
npm run dev  # Start backend on http://localhost:3000
```

### Daily Workflow
```bash
# Start of day
git checkout dev
git pull origin dev
npm install  # if dependencies changed

# During work
git status
git add .
git commit -m "feat: [what you added]"
git push origin dev
```

## API Specification (Template - will be filled based on theme)

### Dataset Analysis Endpoint
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

## When You Know The Theme

Update these sections:
1. `docs/THEME_SPECIFIC.md` - what to analyze
2. `backend/src/processors/` - specific processing logic
3. `backend/src/api/` - theme-specific endpoints
4. `CLAUDE.md` - update "Mission" section above
