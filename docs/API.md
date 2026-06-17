# API Specification

Will be updated based on the specific hackathon theme.

## Endpoints (Template)

### Health Check
```
GET /api/health

Response:
{
  "status": "ok",
  "version": "0.1.0"
}
```

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
