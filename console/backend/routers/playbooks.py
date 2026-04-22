"""Playbook management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
import os

from auth import require_role

router = APIRouter()
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true" or os.getenv("FAIRLENS_DEV_MODE", "") == "true"


@router.post("/{playbook_id}/approve")
async def approve_playbook(
    playbook_id: str,
    _=Depends(require_role(["admin", "owner"])),
):
    """Approve a remediation playbook and queue execution."""
    if DEV_MODE:
        return {
            "playbook_id": playbook_id,
            "status": "approved",
            "execution_status": "queued",
            "message": "Playbook approved. Remediation strategies queued for execution.",
        }

    try:
        from google.cloud import firestore
        db = firestore.Client()
        doc_ref = db.collection("playbooks").document(playbook_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(404, f"Playbook {playbook_id} not found")
        doc_ref.update({
            "human_approved": True,
            "status": "approved",
        })
        return {
            "playbook_id": playbook_id,
            "status": "approved",
            "execution_status": "queued",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to approve playbook: {e}")


@router.get("/{playbook_id}")
async def get_playbook(
    playbook_id: str,
    _=Depends(require_role(["viewer", "auditor", "admin", "owner"])),
):
    """Retrieve a specific playbook."""
    if DEV_MODE:
        return {
            "playbook_id": playbook_id,
            "incident_id": "INC-8921",
            "strategies": [
                {"title": "Post-hoc Threshold Adjustment", "type": "Calibration",
                 "effort": "Low", "steps": [
                     "Compute group-specific ROC curves",
                     "Select thresholds that equalize FPR across groups",
                     "Apply thresholds to production scoring pipeline",
                     "Monitor FPR disparity for 7 days",
                 ]},
            ],
            "human_approved": False,
            "status": "pending_approval",
            "root_cause_analysis": "Disparate false positive rates driven by proxy features.",
        }

    try:
        from google.cloud import firestore
        db = firestore.Client()
        doc = db.collection("playbooks").document(playbook_id).get()
        if not doc.exists:
            raise HTTPException(404, f"Playbook {playbook_id} not found")
        return doc.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to retrieve playbook: {e}")
