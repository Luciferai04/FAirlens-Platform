"""Pydantic models for the FairLens API."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ModelRegistry(BaseModel):
    model_id: str
    name: str = ""
    description: str = ""
    created_at: Optional[datetime] = None
    current_fairness_status: str = "unknown"  # passing | failing | unknown


class ModelSummary(BaseModel):
    model_id: str
    last_audited: Optional[datetime] = None
    currently_passing: Optional[bool] = None
    total_audits: int = 0


class AuditSummary(BaseModel):
    report_id: str
    model_id: str
    created_at: Optional[datetime] = None
    passed: Optional[bool] = None
    bias_risk_score: float = 0.0
    metric_summaries: dict = {}


class AuditReportResponse(BaseModel):
    report_id: str
    model_id: str
    created_at: Optional[datetime] = None
    protected_cols: list[str] = []
    metrics: dict = {}
    threshold_policy: Optional[str] = None
    passed: Optional[bool] = None
    triggered_by: Optional[str] = None


class BiasIncident(BaseModel):
    incident_id: str
    model_id: str
    detected_at: Optional[datetime] = None
    metric_name: Optional[str] = None
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None  # Critical | High | Medium | Low
    status: Optional[str] = "Open"  # Open | In-Progress | Resolved
    sensitive_col: Optional[str] = None
    playbook_id: Optional[str] = None


class RemediationPlaybook(BaseModel):
    playbook_id: str
    incident_id: str
    strategies: list[dict] = []
    created_at: Optional[datetime] = None
    status: str = "pending_approval"
    root_cause_analysis: str = ""


class ComplianceRequest(BaseModel):
    framework: str = "eu_ai_act"  # eu_ai_act | eeoc | rbi_sebi
    model_id: str = ""
