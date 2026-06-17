# Theme-Specific Details

Fill this file as soon as the hackathon theme is announced (takes ~10 minutes).

---

## Theme Name

[To be filled]

## Problem Statement

[What specific problem are we solving? Who is the target user?]

## Dataset

### Source
[Where does the dataset come from? How large is it?]

### Structure
| Column | Type | Description |
|--------|------|-------------|
| [col]  | [type] | [description] |

### Google Drive Archive
```bash
bash scripts/download_data.sh <FILE_ID_HERE>
```

## API Endpoints

[Document the theme-specific endpoints here once implemented]

```
POST /api/[action]   → [description]
GET  /api/[result]   → [description]
```

## Processor Logic

[Describe what `backend/app/processors/analyzer.py` should do]

1. [Step 1]
2. [Step 2]
3. [Step 3]

## Model

See `docs/MODEL_CONTRACT.md` for the .joblib interface.

Target variable: [name]  
Prediction type: [classification / regression]  
Key features: [list]

## Frontend Visualizations

[Describe what the Lovable UI should show — charts, tables, alerts]

## Success Criteria

[How will the judges evaluate our solution?]
