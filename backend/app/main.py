from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

from app.api.routes import router

load_dotenv()

app = FastAPI(
    title="Hackathon API",
    description="AI-powered dataset analysis for TUM Science Hackathon 2026",
    version="0.1.0",
)

origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

# Serve the generated traffic CSV files as static files. The frontend fetches
# them from /api/data/<road>.csv (e.g. /api/data/A8easttraffic.csv).
# Files are produced by scripts/export_frontend_csv.py into data/export/.
EXPORT_DIR = Path(__file__).resolve().parents[2] / "data" / "export"
app.mount("/api/data", StaticFiles(directory=EXPORT_DIR), name="data")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}
