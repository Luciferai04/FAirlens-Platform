"""Remediation playbook execution endpoints."""
from fastapi import APIRouter, Depends, HTTPException
import os

from auth import require_role
from db import db

router = APIRouter()

@router.post("/{playbook_id}/approve")
async def approve_playbook(
    playbook_id: str,
    _=Depends(require_role(["auditor", "admin", "owner"])),
):
    """Approve a playbook for execution."""
    updated = db.approve_playbook(playbook_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return {"playbook_id": playbook_id, "status": "Approved", "human_approved": True}
