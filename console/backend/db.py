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
            rows = self.conn.execute("""
                SELECT ar.*, bis.enterprise_bias_index as ebi_score, bis.risk_tier
                FROM audit_reports ar
                LEFT JOIN (
                    SELECT model_id, enterprise_bias_index, risk_tier,
                           ROW_NUMBER() OVER (PARTITION BY model_id ORDER BY computed_at DESC) as rn
                    FROM bias_index_scores
                ) bis ON ar.model_id = bis.model_id AND bis.rn = 1
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

    def get_benchmarks(self) -> Dict:
        # Static sector baselines as requested
        return {
            "financial": {
                "demographic_parity_difference": {"p75": 0.09, "p90": 0.14},
                "disparate_impact_ratio": {"p75": 0.83, "p90": 0.76},
                "equalized_odds_difference": {"p75": 0.08, "p90": 0.13},
            },
            "healthcare": {
                "demographic_parity_difference": {"p75": 0.11, "p90": 0.17},
                "equalized_odds_difference": {"p75": 0.10, "p90": 0.15},
                "calibration_error": {"p75": 0.06, "p90": 0.09},
            },
            "hr": {
                "demographic_parity_difference": {"p75": 0.07, "p90": 0.12},
                "disparate_impact_ratio": {"p75": 0.85, "p90": 0.78},
                "equalized_odds_difference": {"p75": 0.06, "p90": 0.11},
            }
        }
    
    def _parse_model_row(self, row) -> Dict:
        r = dict(row)
        r['protected_cols'] = json.loads(r.get('protected_cols') or '[]')
        r['metrics'] = json.loads(r.get('metrics') or '{}')
        r['trend'] = json.loads(r.get('trend') or '[]')
        # Map DB 'passed' integer to boolean for frontend
        r['passed'] = bool(r['passed'])
        return r
    
    def _generate_mock_playbook(self, incident_id: str) -> Dict:
        return {
            "playbook_id": f"pb-{incident_id[:8]}",
            "incident_id": incident_id,
            "human_approved": False,
            "strategies": [
                {
                    "title": "Reweighting Training Data",
                    "type": "Data Intervention",
                    "effort": "Medium",
                    "steps": [
                        "Compute sample weights inversely proportional to group frequency",
                        "Apply sklearn.utils.class_weight.compute_sample_weight",
                        "Retrain model with sample_weight parameter",
                        "Re-run fairlens.audit() and verify DPD drops below 0.10"
                    ]
                }
            ],
            "created_at": datetime.utcnow().isoformat()
        }

# Singleton instance
db = FairLensDB()
