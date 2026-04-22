"""Incident management endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
import os, json

from auth import require_role

router = APIRouter()
BQ_PROJECT = os.environ.get("GCP_PROJECT_ID", "")
BQ_DATASET = os.environ.get("BQ_DATASET", "fairlens")
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true" or os.getenv("FAIRLENS_DEV_MODE", "") == "true"

# ── Mock Data ──────────────────────────────────────────────────────────────
MOCK_INCIDENTS = [
    {"incident_id": "INC-8921", "model_id": "loan-approval-v2", "model_name": "Loan Origination v4.2",
     "model_category": "Retail Banking", "metric_name": "False Positive Rate",
     "sub_metric": "Demographic Parity", "current_value": 0.184, "threshold": 0.100,
     "severity": "Critical", "status": "In-Progress", "detected_at": "2024-10-24T12:30:00Z",
     "sensitive_col": "race", "playbook_id": None},
    {"incident_id": "INC-8914", "model_id": "resume-screen-v3", "model_name": "Candidate Screening",
     "model_category": "HR Systems", "metric_name": "Selection Rate",
     "sub_metric": "80% Rule (Disparate Impact)", "current_value": 0.72, "threshold": 0.80,
     "severity": "High", "status": "Open", "detected_at": "2024-10-23T18:45:00Z",
     "sensitive_col": "gender", "playbook_id": None},
    {"incident_id": "INC-8890", "model_id": "icu-triage-v1", "model_name": "ICU Triage Priority",
     "model_category": "Healthcare", "metric_name": "Equal Opportunity Diff",
     "sub_metric": "True Positive Rate", "current_value": 0.34, "threshold": 0.05,
     "severity": "Critical", "status": "Open", "detected_at": "2024-10-22T06:15:00Z",
     "sensitive_col": "race", "playbook_id": None},
    {"incident_id": "INC-8876", "model_id": "credit-scoring-v5", "model_name": "Credit Limit Assignment",
     "model_category": "Financial Services", "metric_name": "Predictive Equality",
     "sub_metric": "False Negative Rate", "current_value": 0.08, "threshold": 0.05,
     "severity": "Medium", "status": "Open", "detected_at": "2024-10-20T14:00:00Z",
     "sensitive_col": "age", "playbook_id": None},
    {"incident_id": "INC-8862", "model_id": "content-rec-v2", "model_name": "Content Feed Ranking",
     "model_category": "Tech Platform", "metric_name": "Disparate Impact Ratio",
     "sub_metric": "Selection Rate Ratio", "current_value": 0.74, "threshold": 0.80,
     "severity": "High", "status": "Resolved", "detected_at": "2024-10-18T09:30:00Z",
     "sensitive_col": "region", "playbook_id": "pb-8862"},
]

MOCK_PLAYBOOK = {
    "playbook_id": "pb-generated-001",
    "incident_id": "",
    "strategies": [
        {"title": "Post-hoc Threshold Adjustment", "type": "Calibration",
         "effort": "Low", "steps": [
             "Compute group-specific ROC curves from validation data",
             "Select thresholds that equalize FPR across groups",
             "Apply thresholds to production scoring pipeline",
             "Monitor FPR disparity for 7 days post-deployment",
         ]},
        {"title": "Data Reweighting & Retrain", "type": "Pre-processing",
         "effort": "Medium", "steps": [
             "Compute sample weights inversely proportional to group error rates",
             "Retrain model with weighted loss function",
             "Run full audit suite on retrained model",
             "A/B test retrained model against production baseline",
         ]},
        {"title": "Feature Excision", "type": "Feature Engineering",
         "effort": "High", "steps": [
             "Identify proxy features via mutual information analysis",
             "Remove top proxy features (zip_code, neighborhood)",
             "Retrain and evaluate AUC impact vs. fairness improvement",
             "Document trade-off analysis for compliance report",
         ]},
    ],
    "human_approved": False,
    "created_at": "2024-10-24T14:00:00Z",
    "root_cause_analysis": "The model exhibits disparate false positive rates across racial groups, primarily driven by proxy features (zip_code, neighborhood) that correlate with protected attributes.",
    "status": "pending_approval",
}


@router.get("/")
async def list_incidents(
    severity: str = Query(None),
    status: str = Query(None),
    limit: int = Query(50, le=200),
    _=Depends(require_role(["viewer", "auditor", "admin", "owner"])),
):
    """List incidents with optional severity and status filters."""
    if DEV_MODE:
        result = MOCK_INCIDENTS
        if severity:
            result = [i for i in result if i["severity"] == severity]
        if status:
            result = [i for i in result if i["status"] == status]
        return result[:limit]

    from google.cloud import bigquery
    client = bigquery.Client(project=BQ_PROJECT)
    conditions = []
    params = []
    if severity:
        conditions.append("severity = @severity")
        params.append(bigquery.ScalarQueryParameter("severity", "STRING", severity))
    if status:
        conditions.append("status = @status")
        params.append(bigquery.ScalarQueryParameter("status", "STRING", status))
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
        SELECT * FROM `{BQ_PROJECT}.{BQ_DATASET}.bias_incidents`
        {where} ORDER BY detected_at DESC LIMIT {limit}
    """
    cfg = bigquery.QueryJobConfig(query_parameters=params)
    rows = list(client.query(query, job_config=cfg).result())
    return [dict(r) for r in rows]


@router.post("/{incident_id}/playbook")
async def generate_playbook(
    incident_id: str,
    _=Depends(require_role(["auditor", "admin", "owner"])),
):
    """Generate a remediation playbook for an incident."""
    if DEV_MODE:
        playbook = dict(MOCK_PLAYBOOK)
        playbook["incident_id"] = incident_id
        playbook["playbook_id"] = f"pb-{incident_id}"
        return playbook

    from google.cloud import pubsub_v1
    publisher = pubsub_v1.PublisherClient()
    topic = f"projects/{BQ_PROJECT}/topics/fairlens-bias-incidents"
    data = json.dumps({"incident_id": incident_id, "action": "generate_playbook"}).encode()
    future = publisher.publish(topic, data)
    return {"incident_id": incident_id, "status": "playbook_requested", "msg_id": future.result()}


@router.post("/{incident_id}/status")
async def update_status(
    incident_id: str,
    body: dict = {},
    _=Depends(require_role(["auditor", "admin", "owner"])),
):
    """Update incident status."""
    new_status = body.get("status", "Open")
    if DEV_MODE:
        return {"incident_id": incident_id, "status": new_status, "updated": True}
    # In production, update BigQuery or Firestore
    return {"incident_id": incident_id, "status": new_status, "updated": True}
