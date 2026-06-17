# Hackathon Project

AI-powered dataset analysis platform for TUM Science Hackathon 2026.

## Quick Start

### Prerequisites
- Node.js 16+
- npm
- Git

### Installation

```bash
git clone https://github.com/DT-sudo/TUM-Hackathon.git
cd TUM-Hackathon
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

## Architecture

```
Data Layer → Processing Layer → API Layer → Frontend (Lovable)

backend/data/raw/   →  backend/src/processors/  →  backend/src/api/  →  frontend/
(CSV, JSON, XLSX)      (analyzer.js)               (routes.js)          (Lovable UI)
```

## Themes Supported

This flexible structure works for any hackathon theme:
- Traffic forecasting (Autobahn)
- Building control (LBenergy)
- Autonomous systems (MTU)
- Financial analysis (TUM Finance)
- Student platforms (Würth)
- Privacy-preserving AI (TUM Network)

## Team Roles

- **Backend Dev**: Dataset processing & API (`backend/src/`)
- **Frontend Dev**: Lovable UI & visualization (`frontend/`)
- **Data Eng**: Dataset management (`backend/data/raw/`)

## Git Workflow

```bash
# Working branch
git checkout dev
git pull origin dev

# After changes
git add .
git commit -m "feat: description"
git push origin dev

# End of hackathon: merge dev → main
```

## Documentation

- [docs/API.md](docs/API.md) - API specification
- [docs/DATA_STRUCTURE.md](docs/DATA_STRUCTURE.md) - Dataset structure
- [docs/THEME_SPECIFIC.md](docs/THEME_SPECIFIC.md) - Theme details (filled at hackathon)
- [CLAUDE.md](CLAUDE.md) - Claude Code instructions

## License

MIT
