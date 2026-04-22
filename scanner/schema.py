"""
BiasProfile — structured result of a dataset bias scan.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid
import json


@dataclass
class BiasProfile:
    """Bias profile produced by the scanner pipeline."""
    dataset_id: str
    scan_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    n_rows: int = 0
    n_cols: int = 0
    protected_cols: list[str] = field(default_factory=list)
    imbalance_results: dict = field(default_factory=dict)
    proxy_leakage_results: list = field(default_factory=list)
    label_bias_results: dict = field(default_factory=dict)
    severity_scores: dict = field(default_factory=dict)
    overall_health_score: float = 1.0
    profile_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def compute_severity(self):
        """Compute severity scores (Critical/High/Medium/Low) per finding."""
        for col, result in self.imbalance_results.items():
            ratio = result.get("ratio", 1.0)
            if ratio > 3.0:
                self.severity_scores[f"imbalance_{col}"] = "Critical"
            elif ratio > 2.0:
                self.severity_scores[f"imbalance_{col}"] = "High"
            elif ratio > 1.5:
                self.severity_scores[f"imbalance_{col}"] = "Medium"
            else:
                self.severity_scores[f"imbalance_{col}"] = "Low"

        for item in self.proxy_leakage_results:
            if item.get("flagged"):
                mi = item["mi_score"]
                key = f"proxy_{item['column']}_{item['protected_col']}"
                if mi > 0.5:
                    self.severity_scores[key] = "Critical"
                elif mi > 0.3:
                    self.severity_scores[key] = "High"
                else:
                    self.severity_scores[key] = "Medium"

        for col, result in self.label_bias_results.items():
            disp = result.get("max_disparity", 0)
            if disp > 0.3:
                self.severity_scores[f"label_bias_{col}"] = "Critical"
            elif disp > 0.2:
                self.severity_scores[f"label_bias_{col}"] = "High"
            elif disp > 0.1:
                self.severity_scores[f"label_bias_{col}"] = "Medium"
            else:
                self.severity_scores[f"label_bias_{col}"] = "Low"

    def compute_health_score(self):
        """Compute overall dataset health score [0, 1]. Higher = healthier."""
        if not self.severity_scores:
            self.overall_health_score = 1.0
            return

        weights = {"Critical": 0.0, "High": 0.3, "Medium": 0.6, "Low": 0.9}
        scores = [weights.get(s, 0.5) for s in self.severity_scores.values()]
        self.overall_health_score = round(sum(scores) / len(scores), 2)

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "dataset_gcs_path": self.dataset_id,
            "scanned_at": self.scan_timestamp,
            "sensitive_cols": self.protected_cols,
            "class_imbalance": json.dumps(self.imbalance_results),
            "proxy_leakage": json.dumps(self.proxy_leakage_results),
            "label_bias": json.dumps(self.label_bias_results),
            "representation_gap": json.dumps({}),
            "overall_risk_score": self.overall_health_score,
        }

    BQ_SCHEMA = "profile_id:STRING,dataset_gcs_path:STRING,scanned_at:TIMESTAMP,sensitive_cols:STRING,class_imbalance:STRING,proxy_leakage:STRING,label_bias:STRING,representation_gap:STRING,overall_risk_score:FLOAT"
