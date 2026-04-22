"""Model registry and audit endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
import os
from datetime import datetime, timedelta
import random

from auth import require_role
from db import db

router = APIRouter()
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true" or os.getenv("FAIRLENS_DEV_MODE", "") == "true"

@router.get("/")
async def list_models(
    limit: int = Query(50, le=200),
    _=Depends(require_role(["viewer", "auditor", "admin", "owner"])),
):
    """List all registered models with current fairness status."""
    models = db.get_models()
    return models[:limit]

@router.get("/{model_id}/audit")
async def get_latest_audit(
    model_id: str,
    _=Depends(require_role(["viewer", "auditor", "admin", "owner"])),
):
    """Retrieve latest AuditReport for a specific model."""
    audit = db.get_model_audit(model_id)
    if not audit:
        raise HTTPException(status_code=404, detail=f"No audit found for model {model_id}")
    return audit

@router.get("/{model_id}/bias-index")
async def get_bias_index(
    model_id: str,
    _=Depends(require_role(["viewer", "auditor", "admin", "owner"])),
):
    """Retrieve Enterprise Bias Index for a specific model."""
    index = db.get_bias_index(model_id)
    if not index:
        raise HTTPException(status_code=404, detail=f"Bias Index not found for model {model_id}")
    return index

@router.post("/{model_id}/scan")
async def trigger_scan(
    model_id: str,
    _=Depends(require_role(["admin", "owner"])),
):
    """Trigger an on-demand bias scan for a model."""
    # In local mode, we just return a mock job ID
    return {"job_id": f"scan-{model_id}-{int(datetime.utcnow().timestamp())}", "model_id": model_id, "status": "queued"}
