"""Firestore document schema as Pydantic model."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Strategy(BaseModel):
    name: str
    description: str
    technique: str  # reweighting|resampling|feature_removal|threshold_adjustment|retraining|augmentation
    code_snippet: str = ""
    estimated_effort: str = "medium"  # low|medium|high


class PlaybookDocument(BaseModel):
    """Schema for Firestore 'playbooks' collection documents."""
    playbook_id: str
    incident_id: str
    model_id: str = ""
    created_at: str = ""
    pending_approval: bool = True
    status: str = "pending_approval"  # pending_approval|approved|executed|rejected
    strategies: list[Strategy] = []
    root_cause_analysis: str = ""
    priority_order: list[str] = []
    generation_time_seconds: float = 0.0
    version: int = 1
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
