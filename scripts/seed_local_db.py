import sqlite3
import json
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path
from local_db import init_db

DB_PATH = Path("local_data/fairlens.db")

MODELS = [
    {
        "model_id": "model-loan-001",
        "name": "Loan Approval — Tier 2",
        "version": "v4.2",
        "provider": "Vertex AI",
        "sensitive_cols": ["race", "gender", "age"],
        "equity_score": 0.71,
        "passed": 0,
        "violations_count": 3,
        "triggered_by": "ci_gate",
        "intended_purpose": "Financial Services",
    },
    {
        "model_id": "model-resume-002",
        "name": "Resume Screening — Engineering",
        "version": "v2.1",
        "provider": "sklearn",
        "sensitive_cols": ["gender", "ethnicity"],
        "equity_score": 0.63,
        "passed": 0,
        "violations_count": 4,
        "triggered_by": "monitor",
        "intended_purpose": "HR Screening",
    },
    {
        "model_id": "model-icu-003",
        "name": "ICU Triage Priority",
        "version": "v1.0",
        "provider": "Vertex AI",
        "sensitive_cols": ["race", "insurance_type"],
        "equity_score": 0.58,
        "passed": 0,
        "violations_count": 5,
        "triggered_by": "monitor",
        "intended_purpose": "Healthcare",
    },
    {
        "model_id": "model-credit-004",
        "name": "Credit Limit Assignment",
        "version": "v5.3",
        "provider": "Vertex AI",
        "sensitive_cols": ["age", "gender"],
        "equity_score": 0.88,
        "passed": 1,
        "violations_count": 0,
        "triggered_by": "sdk",
        "intended_purpose": "Financial Services",
    },
    {
        "model_id": "model-content-005",
        "name": "Content Feed Ranking",
        "version": "v3.7",
        "provider": "sklearn",
        "sensitive_cols": ["age", "location"],
        "equity_score": 0.79,
        "passed": 0,
        "violations_count": 1,
        "triggered_by": "sdk",
        "intended_purpose": "Recommendation",
    },
]

def seed_db():
    conn = init_db()
    c = conn.cursor()
    now = datetime.utcnow()
    # 1. Audit Reports
    for m in MODELS:
        base = m["equity_score"]
        trend = [round(base + random.uniform(-0.04, 0.04), 4) for _ in range(30)]
        trend[-1] = base
        
        metrics = {
            "demographic_parity_difference": {"White": 0.08, "Black": 0.21, "Hispanic": 0.15} if m["model_id"] == "model-loan-001" else {"group_A": 0.05, "group_B": 0.05},
            "equalized_odds_difference": {"White": 0.05, "Black": 0.18, "Hispanic": 0.12} if m["model_id"] == "model-loan-001" else {"group_A": 0.05, "group_B": 0.05},
            "disparate_impact_ratio": {"White": 1.0, "Black": 0.72, "Hispanic": 0.81} if m["model_id"] == "model-loan-001" else {"group_A": 0.9, "group_B": 0.9},
            "calibration_error": {"overall": 0.03},
            "theil_index": {"overall": 0.02},
        }

        c.execute("""
            INSERT OR REPLACE INTO audit_reports VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            f"rpt-{m['model_id']}-latest",
            m["model_id"],
            m["name"],
            m["version"],
            now.isoformat() + "Z",
            json.dumps(m["sensitive_cols"]),
            json.dumps(metrics),
            "eeoc_default",
            m["passed"],
            m["triggered_by"],
            m["provider"],
            m["intended_purpose"],
            m["equity_score"],
            m["violations_count"],
            json.dumps(trend)
        ))

    # 2. Bias Incidents
    INCIDENTS = [
        ("INC-001", "model-loan-001", "Loan Approval", "Financial Services", "False Positive Rate", "Demographic Parity", 0.21, 0.10, "Critical", "In-Progress", "race"),
        ("INC-002", "model-resume-002", "Resume Screening", "HR Screening", "Selection Rate", "Disparate Impact", 0.61, 0.80, "High", "Open", "gender"),
        ("INC-003", "model-icu-003", "ICU Triage", "Healthcare", "Equal Opportunity", "True Positive Rate", 0.34, 0.05, "Critical", "Open", "race"),
    ]
    for inc in INCIDENTS:
        c.execute("INSERT OR REPLACE INTO bias_incidents (incident_id, model_id, model_name, model_category, detected_at, metric_name, sub_metric, current_value, threshold, severity, status, sensitive_col) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", 
                  (inc[0], inc[1], inc[2], inc[3], (now - timedelta(days=2)).isoformat() + "Z", inc[4], inc[5], inc[6], inc[7], inc[8], inc[9], inc[10]))

    # 3. Compliance Reports
    COMPLIANCE = [
        ("COMP-101", "model-loan-001", "Loan Approval", "EEOC (US)", (now - timedelta(days=5)).isoformat() + "Z", 1, "sha256-8f3a...d9e1"),
        ("COMP-102", "model-icu-003", "ICU Triage", "EU AI Act", (now - timedelta(days=12)).isoformat() + "Z", 1, "sha256-4b2e...a1f0"),
    ]
    for comp in COMPLIANCE:
        c.execute("INSERT OR REPLACE INTO compliance_reports (report_id, model_id, model_name, framework, generated_at, kms_signed, sha256_hash) VALUES (?,?,?,?,?,?,?)", comp)

    # 4. SHAP Data
    SHAP_RECORDS = [
        ("model-loan-001", "race", "White", "zip_code", 0.12, 0.31),
        ("model-loan-001", "race", "Black", "zip_code", 0.43, 0.31),
        ("model-loan-001", "race", "White", "income", 0.38, 0.04),
        ("model-loan-001", "race", "Black", "income", 0.34, 0.04),
    ]
    for s in SHAP_RECORDS:
        c.execute("INSERT OR REPLACE INTO shap_attributions VALUES (?,?,?,?,?,?,?,?)",
                  (str(uuid.uuid4()), s[0], s[1], s[2], s[3], s[4], s[5], now.isoformat() + "Z"))

    # 5. Playbooks
    STRATEGIES = [
        {"title": "Reweighting Training Data", "type": "Data Intervention", "effort": "Medium", "steps": ["Step 1", "Step 2"]},
        {"title": "Adversarial Debiasing", "type": "Model Architecture", "effort": "High", "steps": ["Step 1", "Step 2"]}
    ]
    c.execute("INSERT OR REPLACE INTO playbooks VALUES (?,?,?,?,?,?)",
              ("pb-INC-001", "INC-001", json.dumps(STRATEGIES), 0, now.isoformat() + "Z", None))

    # 6. Bias Index Scores
    for m in MODELS:
        c.execute("INSERT OR REPLACE INTO bias_index_scores VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (str(uuid.uuid4()), m["model_id"], now.isoformat() + "Z", 
                   random.uniform(60, 95), random.uniform(60, 95), random.uniform(60, 95),
                   random.uniform(60, 95), random.uniform(60, 95), random.uniform(60, 95),
                   m["equity_score"] * 100, "AMBER" if m["equity_score"] < 0.8 else "GREEN", random.uniform(70, 99)))

    conn.commit()
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed_db()
