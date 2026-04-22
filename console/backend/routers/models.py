"""Model registry and audit endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
import os
from datetime import datetime, timedelta
import random

from auth import require_role

router = APIRouter()
BQ_PROJECT = os.environ.get("GCP_PROJECT_ID", "")
BQ_DATASET = os.environ.get("BQ_DATASET", "fairlens")
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true" or os.getenv("FAIRLENS_DEV_MODE", "") == "true"

# ── Mock Data ──────────────────────────────────────────────────────────────
MOCK_MODELS = [
    {"model_id": "loan-approval-v2", "name": "Loan Approval Engine", "version": "v4.2.1",
     "provider": "sklearn", "sensitive_cols": ["race", "gender"], "equity_score": 0.72,
     "passed": False, "violations_count": 2, "last_audited": "2024-10-24T14:30:00Z",
     "triggered_by": "scheduled"},
    {"model_id": "resume-screen-v3", "name": "Resume Screening — Engineering", "version": "v3.1.0",
     "provider": "Vertex AI", "sensitive_cols": ["age", "gender"], "equity_score": 0.92,
     "passed": True, "violations_count": 0, "last_audited": "2024-10-24T12:00:00Z",
     "triggered_by": "ci_gate"},
    {"model_id": "icu-triage-v1", "name": "ICU Triage Priority", "version": "v1.0.3",
     "provider": "TensorFlow", "sensitive_cols": ["race", "age", "insurance_type"], "equity_score": 0.58,
     "passed": False, "violations_count": 4, "last_audited": "2024-10-23T09:15:00Z",
     "triggered_by": "manual"},
    {"model_id": "credit-scoring-v5", "name": "Credit Scorer Baseline", "version": "v5.0.0",
     "provider": "Vertex AI", "sensitive_cols": ["age", "income_bracket"], "equity_score": 0.88,
     "passed": True, "violations_count": 0, "last_audited": "2024-10-22T16:45:00Z",
     "triggered_by": "scheduled"},
    {"model_id": "content-rec-v2", "name": "Content Feed Ranking", "version": "v2.1.0",
     "provider": "AWS Sagemaker", "sensitive_cols": ["gender", "region"], "equity_score": 0.79,
     "passed": False, "violations_count": 1, "last_audited": "2024-10-17T08:30:00Z",
     "triggered_by": "ci_gate"},
]

def _mock_audit(model_id: str) -> dict:
    model = next((m for m in MOCK_MODELS if m["model_id"] == model_id), MOCK_MODELS[0])
    base = model["equity_score"]
    trend = [round(base + random.uniform(-0.05, 0.05), 3) for _ in range(30)]
    trend[-1] = base  # last point is current
    return {
        "report_id": f"rpt-{model_id}-latest",
        "model_id": model_id,
        "created_at": model["last_audited"],
        "protected_cols": model["sensitive_cols"],
        "metrics": {
            "demographic_parity_difference": {"White": 0.82, "Black": 0.71, "Hispanic": 0.76},
            "equalized_odds_difference": {"White": 0.91, "Black": 0.84, "Hispanic": 0.88},
            "disparate_impact_ratio": {"White": 1.0, "Black": 0.74, "Hispanic": 0.82},
            "calibration_error": {"White": 0.03, "Black": 0.08, "Hispanic": 0.05},
            "theil_index": {"White": 0.02, "Black": 0.11, "Hispanic": 0.06},
            "statistical_parity_difference": {"White": 0.0, "Black": -0.12, "Hispanic": -0.07},
            "average_odds_difference": {"White": 0.0, "Black": 0.09, "Hispanic": 0.04},
            "equal_opportunity_difference": {"White": 0.0, "Black": 0.07, "Hispanic": 0.03},
        },
        "violations": [
            {"col": "race", "metric": "disparate_impact_ratio", "value": 0.74, "threshold": 0.80},
            {"col": "race", "metric": "demographic_parity_difference", "value": 0.11, "threshold": 0.10},
        ] if not model["passed"] else [],
        "passed": model["passed"],
        "triggered_by": model["triggered_by"],
        "threshold_policy": "eeoc_default",
        "trend": trend,
    }


@router.get("/")
async def list_models(
    limit: int = Query(50, le=200),
    _=Depends(require_role(["viewer", "auditor", "admin", "owner"])),
):
    """List all registered models with current fairness status."""
    if DEV_MODE:
        return MOCK_MODELS[:limit]

    from google.cloud import bigquery
    client = bigquery.Client(project=BQ_PROJECT)
    query = f"""
        SELECT model_id, MAX(created_at) AS last_audited,
               LOGICAL_AND(passed) AS currently_passing, COUNT(*) AS total_audits
        FROM `{BQ_PROJECT}.{BQ_DATASET}.audit_reports`
        GROUP BY model_id ORDER BY last_audited DESC LIMIT {limit}
    """
    rows = list(client.query(query).result())
    return [dict(r) for r in rows]


@router.get("/{model_id}/audit")
async def get_latest_audit(
    model_id: str,
    _=Depends(require_role(["viewer", "auditor", "admin", "owner"])),
):
    """Retrieve latest AuditReport for a specific model."""
    if DEV_MODE:
        return _mock_audit(model_id)

    from google.cloud import bigquery
    client = bigquery.Client(project=BQ_PROJECT)
    query = f"""
        SELECT * FROM `{BQ_PROJECT}.{BQ_DATASET}.audit_reports`
        WHERE model_id = @model_id ORDER BY created_at DESC LIMIT 1
    """
    cfg = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("model_id", "STRING", model_id)]
    )
    rows = list(client.query(query, job_config=cfg).result())
    if not rows:
        raise HTTPException(status_code=404, detail=f"No audit found for model {model_id}")
    return dict(rows[0])


@router.post("/{model_id}/scan")
async def trigger_scan(
    model_id: str,
    _=Depends(require_role(["admin", "owner"])),
):
    """Trigger an on-demand bias scan for a model."""
    if DEV_MODE:
        return {"job_id": f"dev-scan-{model_id}", "model_id": model_id, "status": "queued"}

    from google.cloud import pubsub_v1
    import json
    publisher = pubsub_v1.PublisherClient()
    topic = f"projects/{BQ_PROJECT}/topics/fairlens-scan-requests"
    data = json.dumps({"model_id": model_id, "triggered_by": "manual"}).encode()
    future = publisher.publish(topic, data)
    return {"job_id": future.result(), "model_id": model_id, "status": "queued"}
