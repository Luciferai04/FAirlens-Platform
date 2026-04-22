import json
import random
from datetime import datetime, timedelta

now = datetime.utcnow()

MODELS = [
    {"model_id": "loan-approval-v2", "name": "Loan Approval Engine",
     "protected_cols": ["race", "gender"], "equity_score": 0.72, "passed": False},
    {"model_id": "resume-screen-v3", "name": "Resume Screening — Engineering",
     "protected_cols": ["age", "gender"], "equity_score": 0.92, "passed": True},
    {"model_id": "icu-triage-v1", "name": "ICU Triage Priority",
     "protected_cols": ["race", "age", "insurance_type"], "equity_score": 0.58, "passed": False},
    {"model_id": "credit-scoring-v5", "name": "Credit Scorer Baseline",
     "protected_cols": ["age", "income_bracket"], "equity_score": 0.88, "passed": True},
    {"model_id": "content-rec-v2", "name": "Content Feed Ranking",
     "protected_cols": ["gender", "region"], "equity_score": 0.79, "passed": False},
]

AUDIT_REPORTS = []
for m in MODELS:
    base = m["equity_score"]
    trend = [round(base + random.uniform(-0.04, 0.04), 4) for _ in range(30)]
    trend[-1] = base

    AUDIT_REPORTS.append({
        "report_id": f"rpt-{m['model_id']}-latest",
        "model_id": m["model_id"],
        "created_at": (now - timedelta(days=random.randint(0, 7))).isoformat() + "Z",
        "protected_cols": m["protected_cols"],
        "metrics": json.dumps({
            "demographic_parity_difference": {"White": 0.82, "Black": 0.71, "Hispanic": 0.76},
            "equalized_odds_difference": {"White": 0.91, "Black": 0.84, "Hispanic": 0.88},
            "disparate_impact_ratio": {"White": 1.0, "Black": 0.74, "Hispanic": 0.82},
        }),
        "passed": m["passed"],
        "triggered_by": random.choice(["scheduled", "ci_gate", "manual"]),
        "threshold_policy": "eeoc_default",
        "trend": trend,
    })

INCIDENTS = [
    {"incident_id": "INC-8921", "model_id": "loan-approval-v2",
     "metric_name": "False Positive Rate", "current_value": 0.184, "threshold": 0.100,
     "severity": "Critical", "status": "In-Progress", "sensitive_col": "race",
     "detected_at": (now - timedelta(hours=random.randint(2, 72))).isoformat() + "Z"},
    {"incident_id": "INC-8914", "model_id": "resume-screen-v3",
     "metric_name": "Selection Rate", "current_value": 0.72, "threshold": 0.80,
     "severity": "High", "status": "Open", "sensitive_col": "gender",
     "detected_at": (now - timedelta(hours=random.randint(2, 72))).isoformat() + "Z"},
    {"incident_id": "INC-8890", "model_id": "icu-triage-v1",
     "metric_name": "Equal Opportunity Diff", "current_value": 0.34, "threshold": 0.05,
     "severity": "Critical", "status": "Open", "sensitive_col": "race",
     "detected_at": (now - timedelta(hours=random.randint(2, 72))).isoformat() + "Z"},
    {"incident_id": "INC-8876", "model_id": "credit-scoring-v5",
     "metric_name": "Predictive Equality", "current_value": 0.08, "threshold": 0.05,
     "severity": "Medium", "status": "Open", "sensitive_col": "age",
     "detected_at": (now - timedelta(hours=random.randint(2, 72))).isoformat() + "Z"},
    {"incident_id": "INC-8862", "model_id": "content-rec-v2",
     "metric_name": "Disparate Impact Ratio", "current_value": 0.74, "threshold": 0.80,
     "severity": "High", "status": "Resolved", "sensitive_col": "region",
     "detected_at": (now - timedelta(hours=random.randint(2, 72))).isoformat() + "Z"},
]

PLAYBOOKS = [
    {"playbook_id": "playbook-INC-8921", "incident_id": "INC-8921", 
     "human_approved": False, "created_at": now.isoformat() + "Z",
     "strategies": [
         {"title": "Remove Proxy Variables", "type": "Data Mitigation", "effort": "Low", 
          "steps": ["Identify columns highly correlated with 'race' (e.g. zip_code).", "Drop from training set."]},
         {"title": "Synthetic Minority Oversampling (SMOTE)", "type": "Data Mitigation", "effort": "Medium",
          "steps": ["Apply SMOTE to balance the minority race distribution.", "Re-evaluate False Positive Rate."]}
     ]},
    {"playbook_id": "playbook-INC-8914", "incident_id": "INC-8914", 
     "human_approved": False, "created_at": now.isoformat() + "Z",
     "strategies": [
         {"title": "Threshold Calibration", "type": "Model Mitigation", "effort": "Low", 
          "steps": ["Adjust the classification threshold for the disadvantaged gender to equalize Selection Rate."]}
     ]},
    {"playbook_id": "playbook-INC-8890", "incident_id": "INC-8890", 
     "human_approved": True, "created_at": now.isoformat() + "Z",
     "strategies": [
         {"title": "Adversarial Debiasing", "type": "In-processing", "effort": "High", 
          "steps": ["Train a discriminator network to predict 'race'.", "Update primary model to reduce discriminator accuracy."]}
     ]},
    {"playbook_id": "playbook-INC-8876", "incident_id": "INC-8876", 
     "human_approved": False, "created_at": now.isoformat() + "Z",
     "strategies": [
         {"title": "Feature Re-weighting", "type": "Data Mitigation", "effort": "Medium", 
          "steps": ["Apply higher sample weights to underrepresented 'age' groups during training."]}
     ]},
    {"playbook_id": "playbook-INC-8862", "incident_id": "INC-8862", 
     "human_approved": True, "created_at": now.isoformat() + "Z",
     "strategies": [
         {"title": "Reject Option Classification", "type": "Post-processing", "effort": "Low", 
          "steps": ["Give favorable outcomes to unprivileged groups near the decision boundary."]}
     ]},
]

# Create dictionaries for fast lookup
DB_MODELS = {m["model_id"]: m for m in MODELS}
DB_AUDIT_REPORTS = {r["report_id"]: r for r in AUDIT_REPORTS}
DB_INCIDENTS = {i["incident_id"]: i for i in INCIDENTS}
DB_PLAYBOOKS = {p["playbook_id"]: p for p in PLAYBOOKS}

def update_incident_status(incident_id: str, status: str):
    if incident_id in DB_INCIDENTS:
        DB_INCIDENTS[incident_id]["status"] = status
        return True
    return False

def add_playbook(playbook_id: str, data: dict):
    DB_PLAYBOOKS[playbook_id] = data
