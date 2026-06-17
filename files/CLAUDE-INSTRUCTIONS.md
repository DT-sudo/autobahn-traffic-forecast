# Claude Code Instructions — TUM Hackathon 2026

Read this before starting any Claude Code session on this project.

---

## Project Summary

AI-powered dataset analysis platform for TUM Science Hackathon 2026.

The architecture is theme-independent:
- **Backend**: Python · FastAPI · pandas · scikit-learn · joblib
- **Frontend**: Lovable-generated React (TypeScript · TanStack · shadcn/ui · Recharts)
- **Data**: local only, never committed to git
- **Model**: pre-trained `.joblib` pipeline, loaded at runtime

## Run the Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
# Interactive API docs: http://localhost:8000/docs
```

## Files to Adapt Per Theme

| File | Purpose |
|------|---------|
| `backend/app/processors/analyzer.py` | Replace the placeholder with theme-specific logic |
| `backend/app/api/routes.py` | Add theme-specific endpoints |
| `scripts/train_model.py` | Set TARGET_COLUMN and feature list for the theme |
| `docs/THEME_SPECIFIC.md` | Dataset structure, columns, success criteria |
| `docs/MODEL_CONTRACT.md` | Model input/output interface |
| `CLAUDE.md` — Mission | One sentence describing the specific task |

## Files to Never Modify

- `.gitignore` — keeps datasets and models out of git
- `backend/app/main.py` — only change if adding new middleware
- `.claude/settings.json` — Claude Code permissions
- Directory structure under `data/` and `models/`

## Coding Patterns

### Add a New API Endpoint

```python
# backend/app/api/routes.py
from pydantic import BaseModel

class MyRequest(BaseModel):
    filename: str
    param: str = "default"

@router.post("/my-endpoint")
async def my_endpoint(request: MyRequest):
    try:
        result = my_processor(request.filename, request.param)
        return {"success": True, "result": result}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Add a New Processor

```python
# backend/app/processors/my_processor.py
import pandas as pd
from pathlib import Path

RAW_DATA_PATH = Path(__file__).parents[4] / "data" / "raw"

def my_processor(filename: str, param: str = "default") -> dict:
    file_path = RAW_DATA_PATH / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {filename}")
    df = pd.read_csv(file_path)
    # Theme-specific logic here
    return {"row_count": len(df), "result": []}
```

### Load and Use the .joblib Model

```python
import joblib
import pandas as pd
from pathlib import Path

MODEL_PATH = Path("models/prediction_pipeline.joblib")

def predict(input_data: dict) -> dict:
    model = joblib.load(MODEL_PATH)
    df = pd.DataFrame([input_data])
    prediction = model.predict(df)
    confidence = model.predict_proba(df).max()
    return {"prediction": prediction[0], "confidence": float(confidence)}
```

### Frontend Fetches (TypeScript / TanStack React Query)

```typescript
// Using TanStack Query in a Lovable component
import { useQuery, useMutation } from "@tanstack/react-query";

const { data } = useQuery({
  queryKey: ["results"],
  queryFn: async () => {
    const res = await fetch("http://localhost:8000/api/results");
    return res.json();
  },
});

const analyzeMutation = useMutation({
  mutationFn: async (filename: string) => {
    const res = await fetch("http://localhost:8000/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename, analysis_type: "detailed" }),
    });
    return res.json();
  },
});
```

## Data Preparation Commands

```bash
# 1. Download prepared dataset from Google Drive
bash scripts/download_data.sh <GOOGLE_DRIVE_FILE_ID>

# 2. Clean raw data
python scripts/clean_data.py

# 3. Build features
python scripts/build_features.py

# 4. Train and export model (generates models/prediction_pipeline.joblib)
python scripts/train_model.py
```

## Rules

**Always:**
- Write all code, comments, and variable names in English
- Return JSON from every API endpoint
- Reference the docs/MODEL_CONTRACT.md before touching model loading code

**Never:**
- Commit files from `data/raw/`, `data/processed/`, or `models/`
- Commit `.env`
- Run model training inside the application (scripts/train_model.py is offline-only)
- Push to `main` directly (use `dev` branch)

## Claude Usage Guidelines (from INFO.md)

- Use **Sonnet 4.6** for architecture decisions, key implementation, debugging
- Use **Haiku** for research, drafts, simple questions
- Avoid unnecessary retries on network errors — switch chat tab and check if the response arrived
- Keep all prompts in English for consistency

## Git Workflow

```bash
git checkout dev
git pull origin dev

# work...
git add backend/app/ docs/
git commit -m "feat: [what you implemented]"
git push origin dev
```
