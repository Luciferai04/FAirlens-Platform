"""FairLens API — FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os, sys

# Ensure the backend directory is in the path for both standalone and package imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from routers import models, incidents, reports, playbooks

app = FastAPI(
    title="FairLens API",
    version="1.0.0",
    description="Enterprise AI Bias Governance Platform API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        os.getenv("CONSOLE_URL", "*"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models.router, prefix="/v1/models", tags=["models"])
app.include_router(incidents.router, prefix="/v1/incidents", tags=["incidents"])
app.include_router(reports.router, prefix="/v1/reports", tags=["reports"])
app.include_router(playbooks.router, prefix="/v1/playbooks", tags=["playbooks"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "fairlens-api", "version": "1.0.0"}
