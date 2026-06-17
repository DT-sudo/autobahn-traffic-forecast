from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from app.processors.analyzer import analyze_dataset

router = APIRouter()


class AnalyzeRequest(BaseModel):
    filename: str
    analysis_type: str = "summary"


@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """Analyze a dataset file from data/raw/. Adapt for the specific theme."""
    try:
        results = analyze_dataset(request.filename, request.analysis_type)
        return {"success": True, "results": results}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results")
async def get_results():
    """Return latest processed results. Extend for theme-specific output."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "data": {},
        "statistics": {},
    }
