"""
AuditReport — structured fairness audit result container.

Provides serialization to JSON, HTML, and BigQuery, plus violation detection.
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AuditReport:
    """
    Result of a fairlens.audit() call.

    Attributes:
        metrics: {sensitive_col: {metric_name: value}} nested dict
        thresholds: {metric_name: threshold_value} dict
        violations: List of dicts describing threshold violations
        sensitive_cols: List of protected attribute column names
        triggered_by: Source tag — "sdk" | "ci_gate" | "monitor" | "manual"
        report_id: UUID4 identifier for this report
        created_at: ISO 8601 timestamp of report creation
        model_id: Optional model identifier
    """
    metrics: dict[str, dict[str, float]]
    thresholds: dict[str, float]
    violations: list[dict]
    sensitive_cols: list[str]
    triggered_by: str
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    model_id: str = field(default="unknown")
    ebi: Any = field(default=None)

    @property
    def passed(self) -> bool:
        """True if no violations were found."""
        return not self.flag_violation()

    def flag_violation(self, threshold: float = 0.1) -> bool:
        """Returns True if any metric exceeds the threshold."""
        for m in self.metrics.values():
            for val in m.values():
                if abs(val) > threshold:
                    # TRIGGER SOS SIGNAL (D12: REAL-TIME ALERTS)
                    try:
                        with open(".sos_signal", "w") as f:
                            f.write(self.model_id)
                    except:
                        pass
                    return True
        return False

    def to_dict(self) -> dict:
        """Convert report to a plain dictionary."""
        return {
            "report_id": self.report_id,
            "model_id": self.model_id,
            "created_at": self.created_at,
            "triggered_by": self.triggered_by,
            "sensitive_cols": self.sensitive_cols,
            "metrics": self.metrics,
            "thresholds": self.thresholds,
            "violations": self.violations,
            "passed": self.passed,
            "ebi": self.ebi.to_dict() if hasattr(self.ebi, 'to_dict') else self.ebi
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize report to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_html(self) -> str:
        """
        Returns a self-contained HTML fairness report with styled tables.
        No external dependencies — all CSS is inlined.
        """
        status_color = "#22c55e" if self.passed else "#ef4444"
        status_text = "✅ PASSED" if self.passed else "❌ FAILED"

        rows_html = ""
        for col, col_metrics in self.metrics.items():
            for metric_name, value in col_metrics.items():
                threshold = self.thresholds.get(metric_name, "—")
                # Check if this specific metric is violated
                is_violated = any(
                    v["col"] == col and v["metric"] == metric_name
                    for v in self.violations
                )
                badge = (
                    '<span style="color:#ef4444;font-weight:bold;">FAIL</span>'
                    if is_violated
                    else '<span style="color:#22c55e;font-weight:bold;">PASS</span>'
                )
                rows_html += f"""
                <tr>
                    <td>{col}</td>
                    <td>{metric_name}</td>
                    <td>{value:.4f}</td>
                    <td>{threshold}</td>
                    <td>{badge}</td>
                </tr>"""

        violations_html = ""
        if self.violations:
            violations_html = "<h3 style='color:#ef4444;'>Violations</h3><ul>"
            for v in self.violations:
                violations_html += (
                    f"<li><strong>{v['col']}.{v['metric']}</strong>: "
                    f"{v['value']:.4f} ({v['direction']} threshold {v['threshold']:.4f})</li>"
                )
            violations_html += "</ul>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FairLens Audit Report — {self.report_id[:8]}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 12px; padding: 2rem; margin-bottom: 1.5rem; }}
        .header h1 {{ font-size: 1.5rem; color: #f8fafc; margin-bottom: 0.5rem; }}
        .status {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 6px; font-weight: 700; font-size: 1.1rem; color: {status_color}; background: {status_color}15; border: 1px solid {status_color}40; }}
        .meta {{ color: #94a3b8; font-size: 0.85rem; margin-top: 0.75rem; }}
        table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; margin: 1rem 0; }}
        th {{ background: #334155; color: #f8fafc; text-align: left; padding: 0.75rem 1rem; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        td {{ padding: 0.65rem 1rem; border-top: 1px solid #334155; font-size: 0.9rem; }}
        tr:hover td {{ background: #334155; }}
        h3 {{ margin: 1.5rem 0 0.75rem; font-size: 1.1rem; }}
        ul {{ padding-left: 1.5rem; }}
        li {{ margin: 0.3rem 0; font-size: 0.9rem; }}
        .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #334155; color: #64748b; font-size: 0.75rem; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>FairLens Audit Report</h1>
            <div class="status">{status_text}</div>
            <div class="meta">
                Report ID: {self.report_id}<br>
                Model: {self.model_id} &nbsp;|&nbsp; Triggered by: {self.triggered_by}<br>
                Created: {self.created_at} &nbsp;|&nbsp; Protected attributes: {', '.join(self.sensitive_cols)}
            </div>
        </div>

        <h3>Metric Results</h3>
        <table>
            <thead>
                <tr><th>Attribute</th><th>Metric</th><th>Value</th><th>Threshold</th><th>Status</th></tr>
            </thead>
            <tbody>{rows_html}
            </tbody>
        </table>

        {violations_html}

        <div class="footer">
            Generated by FairLens v1.0.0 — Enterprise AI Bias Detection Platform<br>
            SDG 10: Reduced Inequalities &nbsp;|&nbsp; SDG 16: Peace, Justice & Strong Institutions
        </div>
    </div>
</body>
</html>"""

    def write_bq(
        self, project: str, dataset: str = "fairlens", table: str = "audit_reports"
    ) -> None:
        """Append audit record to BigQuery."""
        from google.cloud import bigquery

        client = bigquery.Client(project=project)
        table_ref = f"{project}.{dataset}.{table}"
        row = self.to_dict()
        # Convert metrics to JSON string for BQ JSON column
        row["metrics"] = json.dumps(row["metrics"])
        row["threshold_policy"] = json.dumps(row["thresholds"])
        row["protected_cols"] = row.pop("sensitive_cols")
        row.pop("thresholds", None)
        row.pop("violations", None)

        errors = client.insert_rows_json(table_ref, [row])
        if errors:
            raise RuntimeError(f"BigQuery insert errors: {errors}")
