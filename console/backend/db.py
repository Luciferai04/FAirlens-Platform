import os
import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

LOCAL_MODE = os.getenv("LOCAL_MODE", "true").lower() == "true"
# Try relative to this file (Docker/Standalone) or root (Repo)
DB_PATH = Path(__file__).parent / "local_data" / "fairlens.db"
if not DB_PATH.exists():
    DB_PATH = Path(__file__).parent.parent.parent / "local_data" / "fairlens.db"

class FairLensDB:
    """
    Unified data access layer.
    LOCAL_MODE=true → SQLite
    LOCAL_MODE=false → BigQuery (production)
    """
    
    def __init__(self):
        self.local = LOCAL_MODE
        if self.local:
            # Ensure path exists for local development
            DB_PATH.parent.mkdir(exist_ok=True, parents=True)
            self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        else:
            try:
                from google.cloud import bigquery
                self.bq = bigquery.Client()
            except ImportError:
                print("Warning: google-cloud-bigquery not installed. Falling back to local mode.")
                self.local = True
                self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
                self.conn.row_factory = sqlite3.Row
    
    def get_models(self) -> List[Dict]:
        if self.local:
            # Local SQLite: Get latest audit for each model, joined with latest EBI score
            rows = self.conn.execute("""
                SELECT 
                    ar.*, 
                    bis.enterprise_bias_index as ebi_score, 
                    bis.risk_tier,
                    bis.percentile_rank
                FROM audit_reports ar
                LEFT JOIN bias_index_scores bis ON ar.model_id = bis.model_id
                WHERE ar.report_id IN (
                    SELECT MAX(report_id) FROM audit_reports GROUP BY model_id
                )
                AND (bis.computed_at IS NULL OR bis.computed_at = (
                    SELECT MAX(computed_at) FROM bias_index_scores WHERE model_id = ar.model_id
                ))
                ORDER BY ar.equity_score ASC
            """).fetchall()
            return [self._parse_model_row(r) for r in rows]
        else:
            # Standard production BQ query (actual implementation would match your BQ schema)
            query = "SELECT * FROM `fairlens.audit_reports` ORDER BY equity_score ASC"
            rows = self.bq.query(query).result()
            return [dict(r) for r in rows]
    
    def get_model_audit(self, model_id: str) -> Optional[Dict]:
        if self.local:
            row = self.conn.execute(
                "SELECT * FROM audit_reports WHERE model_id=?", (model_id,)
            ).fetchone()
            if not row: return None
            return self._parse_model_row(row)
        else:
            # BigQuery implementation...
            return None
    
    def get_incidents(self, status=None, severity=None) -> List[Dict]:
        if self.local:
            query = "SELECT * FROM bias_incidents WHERE 1=1"
            params = []
            if status and status != 'All':
                query += " AND status=?"
                params.append(status)
            if severity and severity != 'All':
                query += " AND severity=?"
                params.append(severity)
            rows = self.conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        return []
    
    def get_compliance_reports(self) -> List[Dict]:
        if self.local:
            return [dict(r) for r in 
                self.conn.execute("SELECT * FROM compliance_reports").fetchall()]
        return []
    
    def get_playbook(self, incident_id: str) -> Optional[Dict]:
        if self.local:
            row = self.conn.execute(
                "SELECT * FROM playbooks WHERE incident_id=?", (incident_id,)
            ).fetchone()
            if row:
                result = dict(row)
                result['strategies'] = json.loads(result['strategies'] or '[]')
                return result
            # Generate mock playbook if none exists
            return self._generate_mock_playbook(incident_id)
        return None
    
    def get_bias_index(self, model_id: str) -> Optional[Dict]:
        if self.local:
            row = self.conn.execute(
                "SELECT * FROM bias_index_scores WHERE model_id=? ORDER BY computed_at DESC LIMIT 1",
                (model_id,)
            ).fetchone()
            if not row: return None
            result = dict(row)
            # Add dimensions nesting to match EBIResult shape
            result['dimensions'] = {
                "metric_coverage": result.pop('metric_coverage_score'),
                "severity_weighted": result.pop('severity_weighted_score'),
                "temporal_stability": result.pop('temporal_stability_score'),
                "intersectional": result.pop('intersectional_score'),
                "remediation_velocity": result.pop('remediation_velocity_score'),
                "regulatory_alignment": result.pop('regulatory_alignment_score'),
            }
            # Add mock explainability if missing
            result['biggest_risk_factor'] = "Metric threshold violations"
            result['improvement_priority'] = ["Metric Coverage", "Severity Impact"]
            return result
        return None
    
    def update_incident_status(self, incident_id: str, status: str):
        if self.local:
            self.conn.execute(
                "UPDATE bias_incidents SET status=? WHERE incident_id=?",
                (status, incident_id)
            )
            self.conn.commit()
            return True
        return False
    
    def approve_playbook(self, playbook_id: str):
        if self.local:
            exec_at = datetime.utcnow().isoformat()
            self.conn.execute(
                "UPDATE playbooks SET human_approved=1, executed_at=? WHERE playbook_id=?",
                (exec_at, playbook_id)
            )
            self.conn.commit()
            return True
        return False

    def get_benchmarks(self) -> List[Dict]:
        # Industry baselines as expected by the frontend array map
        return [
            {
                "sector": "Financial Services (BFSI)",
                "count": 1240,
                "avg_ebi": 68.4,
                "target_ebi": "85+",
            },
            {
                "sector": "Healthcare & Life Sciences",
                "count": 840,
                "avg_ebi": 62.1,
                "target_ebi": "80+",
            },
            {
                "sector": "Technology & HR",
                "count": 2100,
                "avg_ebi": 71.8,
                "target_ebi": "90+",
            }
        ]
    
    def _parse_model_row(self, row) -> Dict:
        r = dict(row)
        r['protected_cols'] = json.loads(r.get('protected_cols') or '[]')
        metrics = json.loads(r.get('metrics') or '{}')
        r['metrics'] = metrics
        r['trend'] = json.loads(r.get('trend') or '[]')
        r['ebi_score'] = r.get('ebi_score') or 0
        r['passed'] = bool(r['passed'])
        
        # Derive specific violations for the UI
        violations = []
        thresholds = {
            "demographic_parity_difference": 0.1,
            "equalized_odds_difference": 0.1,
            "disparate_impact_ratio": 0.8,
            "statistical_parity_difference": 0.1
        }
        
        for metric, groups in metrics.items():
            threshold = thresholds.get(metric, 0.1)
            for group, val in groups.items():
                is_ratio = "ratio" in metric
                failed = val < threshold if is_ratio else val > threshold
                if failed:
                    violations.append({
                        "col": "multiple", # Simplification for local mode
                        "metric": metric,
                        "value": val,
                        "threshold": threshold
                    })
        r['violations'] = violations
        return r
    
    def _generate_mock_playbook(self, incident_id: str) -> Dict:
        # Specialized analysis for the Maria demo case (INC-001)
        if incident_id == "INC-001":
            root_cause = (
                "The model exhibits a critical disparity (0.21 DPD) in loan approval rates. "
                "The primary driver is 'Feature Proxying': the feature 'zip_code' has a 0.84 correlation "
                "with the protected attribute 'race', causing the model to unintentionally learn "
                "historical redlining patterns."
            )
        else:
            root_cause = "The model exhibits a critical disparity across protected demographic attributes."

        return {
            "playbook_id": f"pb-{incident_id[:8]}",
            "incident_id": incident_id,
            "human_approved": False,
            "root_cause_analysis": root_cause,
            "status": "Generated",
            "strategies": [
                {
                    "title": "Reweighting Training Data",
                    "type": "Data Intervention",
                    "effort": "Medium",
                    "steps": [
                        "Compute group-wise selection rates across sensitive attributes.",
                        "Apply inverse frequency weighting to the training objective.",
                        "Re-train using 'sample_weight' parameter in sklearn/XGBoost.",
                        "Verify that DPD drops below 0.10 while maintaining >95% of original AUC."
                    ]
                },
                {
                    "title": "Adversarial Debiasing",
                    "type": "Model Architecture",
                    "effort": "High",
                    "steps": [
                        "Initialize a GAN-based debiaser (fairlens.debias).",
                        "Train an adversary network to predict race from the model's latent embeddings.",
                        "Apply gradient reversal to minimize the adversary's performance.",
                        "Ensure the model is unable to reconstruct protected attributes."
                    ]
                },
                {
                    "title": "Post-Hoc Threshold Optimization",
                    "type": "Post-Processing",
                    "effort": "Low",
                    "steps": [
                        "Calculate equalized odds thresholds for each demographic group.",
                        "Adjust decision boundaries to ensure equal TPR across groups.",
                        "Note: This may impact overall accuracy (Pareto-Frontier trade-off)."
                    ]
                }
            ],
            "created_at": datetime.utcnow().isoformat()
        }

# Singleton instance
db = FairLensDB()
