"""Incident management endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
import os, json

from auth import require_role
from db import db

router = APIRouter()

@router.get("/")
async def list_incidents(
    severity: str = Query(None),
    status: str = Query(None),
    limit: int = Query(50, le=200),
    _=Depends(require_role(["viewer", "auditor", "admin", "owner"])),
):
    """List incidents with optional severity and status filters."""
    incidents = db.get_incidents(status=status, severity=severity)
    return incidents[:limit]

@router.post("/{incident_id}/playbook")
async def generate_playbook(
    incident_id: str,
    _=Depends(require_role(["auditor", "admin", "owner"])),
):
    """Generate a remediation playbook for an incident."""
    playbook = db.get_playbook(incident_id)
    if not playbook:
        raise HTTPException(status_code=404, detail="Incident not found")
    return playbook

@router.patch("/{incident_id}/status")
async def update_status(
    incident_id: str,
    body: dict = {},
    _=Depends(require_role(["auditor", "admin", "owner"])),
):
    """Update incident status."""
    new_status = body.get("status", "Open")
    updated = db.update_incident_status(incident_id, new_status)
    return {"incident_id": incident_id, "status": new_status, "updated": updated}
