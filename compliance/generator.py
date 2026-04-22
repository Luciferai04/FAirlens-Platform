"""
Compliance Report Generator — produces professional PDF reports from FairLens
audit data for regulatory frameworks (EU AI Act, EEOC, RBI/SEBI).

Can operate in two modes:
  1. Live mode: fetches audit data from BigQuery (requires GCP)
  2. Local mode: accepts an AuditReport object directly (no GCP needed)
"""
from __future__ import annotations
import yaml
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)

TEMPLATES_DIR = Path(__file__).parent / "templates"
FRAMEWORKS = ["eu_ai_act", "eeoc", "rbi_sebi"]


def generate_from_audit(
    audit_report,
    framework: str,
    output_path: str,
    sign: bool = False,
    project: str = None,
) -> str:
    """
    Generate a compliance PDF from an AuditReport object (no GCP needed).

    Args:
        audit_report: fairlens.AuditReport instance
        framework: "eu_ai_act" | "eeoc"
        output_path: Local path for output PDF
        sign: Whether to sign with Cloud KMS (requires GCP)
        project: GCP project ID (only needed if sign=True)

    Returns:
        SHA-256 hex digest of the generated PDF
    """
    if framework not in FRAMEWORKS:
        raise ValueError(f"Unknown framework '{framework}'. Choose from: {FRAMEWORKS}")

    template_path = TEMPLATES_DIR / f"{framework}.yaml"
    with open(template_path) as f:
        template = yaml.safe_load(f)

    # Convert AuditReport to the data dict the renderer expects
    report_dict = audit_report.to_dict() if hasattr(audit_report, "to_dict") else audit_report
    data = _audit_report_to_data(report_dict)

    _render_pdf(data, template, output_path, framework)

    if sign and project:
        from .signer import sign_pdf
        _, _, sha = sign_pdf(output_path, project=project)
        return sha
    else:
        with open(output_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()


def generate(
    model_id: str,
    framework: str,
    project: str,
    output_path: str,
    sign: bool = True,
) -> str:
    """
    Generate a signed compliance PDF by fetching audit data from BigQuery.
    Requires GCP credentials.
    """
    if framework not in FRAMEWORKS:
        raise ValueError(f"Unknown framework '{framework}'. Choose from: {FRAMEWORKS}")

    template_path = TEMPLATES_DIR / f"{framework}.yaml"
    with open(template_path) as f:
        template = yaml.safe_load(f)

    audit_data = _fetch_audit_data(model_id, project)
    _render_pdf(audit_data, template, output_path, framework)

    if sign:
        from .signer import sign_pdf
        _, _, sha = sign_pdf(output_path, project=project)
        return sha
    else:
        with open(output_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()


def _audit_report_to_data(report: dict) -> dict:
    """Convert a flat AuditReport dict to the nested structure templates expect."""
    # Flatten metrics from {col: {metric: val}} to {metric: val} for first col
    flat_metrics = {}
    metrics = report.get("metrics", {})
    if isinstance(metrics, dict):
        for col_metrics in metrics.values():
            if isinstance(col_metrics, dict):
                flat_metrics.update(col_metrics)
                break
    elif isinstance(metrics, str):
        try:
            parsed = json.loads(metrics)
            for col_metrics in parsed.values():
                if isinstance(col_metrics, dict):
                    flat_metrics.update(col_metrics)
                    break
        except (json.JSONDecodeError, AttributeError):
            pass

    return {
        "model_id": report.get("model_id", "unknown"),
        "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "latest_audit": {
            "model_id": report.get("model_id", "unknown"),
            "created_at": report.get("created_at", ""),
            "protected_cols": report.get("sensitive_cols", report.get("protected_cols", [])),
            "metrics": flat_metrics,
            "passed": report.get("passed", False),
            "intended_purpose": report.get("intended_purpose", "See model registry"),
            "provider": report.get("provider", "Organisation"),
        },
        "incident_history": [],
    }


def _fetch_audit_data(model_id: str, project: str) -> dict:
    """Pull latest audit report + incident history from BigQuery."""
    from google.cloud import bigquery
    client = bigquery.Client(project=project)

    audit_query = f"""
        SELECT * FROM `{project}.fairlens.audit_reports`
        WHERE model_id = @model_id
        ORDER BY created_at DESC LIMIT 1
    """
    incident_query = f"""
        SELECT * FROM `{project}.fairlens.bias_incidents`
        WHERE model_id = @model_id
        ORDER BY detected_at DESC LIMIT 10
    """
    params = [bigquery.ScalarQueryParameter("model_id", "STRING", model_id)]
    cfg = bigquery.QueryJobConfig(query_parameters=params)

    audit_rows = list(client.query(audit_query, job_config=cfg).result())
    incident_rows = list(client.query(incident_query, job_config=cfg).result())

    return {
        "model_id": model_id,
        "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "latest_audit": dict(audit_rows[0]) if audit_rows else {},
        "incident_history": [dict(r) for r in incident_rows],
    }


def _render_pdf(data: dict, template: dict, output_path: str, framework: str):
    """Render a professional compliance PDF with cover page, metrics table, and signature block."""
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=25 * mm, rightMargin=25 * mm,
        topMargin=20 * mm, bottomMargin=25 * mm,
    )
    story = []
    styles = getSampleStyleSheet()

    # --- Cover Page ---
    story.append(Spacer(1, 30 * mm))

    title_style = ParagraphStyle(
        "cover_title", fontName="Helvetica-Bold", fontSize=24,
        spaceAfter=8, textColor=colors.HexColor("#1a3a5c"),
    )
    story.append(Paragraph("FairLens", title_style))

    subtitle_style = ParagraphStyle(
        "cover_subtitle", fontName="Helvetica", fontSize=11,
        spaceAfter=4, textColor=colors.HexColor("#64748b"),
    )
    story.append(Paragraph("Enterprise AI Bias Detection Platform", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#06b6d4"), spaceAfter=12))

    report_title_style = ParagraphStyle(
        "report_title", fontName="Helvetica-Bold", fontSize=16,
        spaceAfter=12, textColor=colors.HexColor("#0f172a"),
    )
    story.append(Paragraph(template["report_title"], report_title_style))

    meta_style = ParagraphStyle(
        "meta", fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#64748b"), spaceAfter=4,
    )
    story.append(Paragraph(f"Model: {data['model_id']}", meta_style))
    story.append(Paragraph(f"Generated: {data['report_date']}", meta_style))
    story.append(Paragraph(f"Framework: {template.get('regulation', framework)}", meta_style))

    # --- Executive Summary ---
    story.append(Spacer(1, 15 * mm))
    passed = data.get("latest_audit", {}).get("passed", False)
    status_text = "PASSED — All fairness thresholds met" if passed else "FAILED — Fairness threshold violations detected"
    status_color = colors.HexColor("#16a34a") if passed else colors.HexColor("#dc2626")

    exec_style = ParagraphStyle(
        "exec", fontName="Helvetica-Bold", fontSize=14,
        spaceAfter=8, textColor=status_color,
    )
    story.append(Paragraph(f"Executive Summary: {status_text}", exec_style))

    # --- Metric Table ---
    metrics = data.get("latest_audit", {}).get("metrics", {})
    if metrics and isinstance(metrics, dict):
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph("Fairness Metric Results", ParagraphStyle(
            "h2", fontName="Helvetica-Bold", fontSize=13, spaceAfter=6,
            textColor=colors.HexColor("#1a3a5c"),
        )))

        # Default thresholds for color coding
        thresholds = {
            "demographic_parity_difference": 0.10,
            "equalized_odds_difference": 0.10,
            "disparate_impact_ratio": 0.80,
            "calibration_error": 0.05,
            "theil_index": 0.10,
            "statistical_parity_difference": 0.10,
            "average_odds_difference": 0.10,
            "equal_opportunity_difference": 0.10,
        }

        table_data = [["Metric", "Value", "Threshold", "Status"]]
        row_colors = []
        for metric_name, value in metrics.items():
            if not isinstance(value, (int, float)):
                continue
            threshold = thresholds.get(metric_name, "—")
            if metric_name == "disparate_impact_ratio":
                is_pass = value >= threshold if isinstance(threshold, (int, float)) else True
            else:
                is_pass = abs(value) <= threshold if isinstance(threshold, (int, float)) else True

            status = "PASS" if is_pass else "FAIL"
            row_colors.append(colors.HexColor("#dcfce7") if is_pass else colors.HexColor("#fee2e2"))
            table_data.append([
                metric_name.replace("_", " ").title(),
                f"{value:.4f}",
                f"{threshold}" if isinstance(threshold, (int, float)) else "—",
                status,
            ])

        if len(table_data) > 1:
            t = Table(table_data, colWidths=[55 * mm, 25 * mm, 25 * mm, 20 * mm])
            style_cmds = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
            for i, bg_color in enumerate(row_colors):
                style_cmds.append(("BACKGROUND", (0, i + 1), (-1, i + 1), bg_color))
            t.setStyle(TableStyle(style_cmds))
            story.append(t)

    story.append(PageBreak())

    # --- Template Sections ---
    for section in template.get("sections", []):
        story.append(Paragraph(section["heading"], ParagraphStyle(
            "h2", fontName="Helvetica-Bold", fontSize=13, spaceBefore=12,
            spaceAfter=6, textColor=colors.HexColor("#1a3a5c"),
        )))
        for field in section.get("fields", []):
            value = _resolve_field(field, data)
            req_marker = " *" if field.get("required") else ""
            story.append(Paragraph(
                f"<b>{field['label']}{req_marker}:</b>  {value}",
                ParagraphStyle("body", fontName="Helvetica", fontSize=9,
                               spaceAfter=5, leading=14),
            ))
        story.append(Spacer(1, 4 * mm))

    # --- Signature Block ---
    story.append(Spacer(1, 15 * mm))
    story.append(HRFlowable(width="100%", thickness=1, spaceAfter=8))
    sig_style = ParagraphStyle("sig", fontName="Helvetica", fontSize=8,
                                textColor=colors.HexColor("#94a3b8"), spaceAfter=4)
    story.append(Paragraph("DOCUMENT INTEGRITY", ParagraphStyle(
        "sig_head", fontName="Helvetica-Bold", fontSize=9,
        textColor=colors.HexColor("#64748b"), spaceAfter=4,
    )))
    story.append(Paragraph(
        "This document was generated by FairLens v1.0.0 — Enterprise AI Bias Detection Platform.",
        sig_style))
    story.append(Paragraph(
        f"Generated: {datetime.now(timezone.utc).isoformat()}", sig_style))

    doc.build(story)

    # Append SHA-256 hash as footer by re-reading and re-rendering
    with open(output_path, "rb") as f:
        content_hash = hashlib.sha256(f.read()).hexdigest()

    # Write hash to a sidecar file
    hash_path = output_path.replace(".pdf", ".sha256")
    with open(hash_path, "w") as f:
        f.write(content_hash)


def _resolve_field(field: dict, data: dict) -> str:
    """Map template field data_path to audit data value."""
    path = field.get("data_path", "")
    if not path:
        return field.get("default", "N/A")

    parts = path.split(".")
    val = data
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part, None)
        else:
            val = None
            break

    if val is None:
        return field.get("default", "N/A")
    if isinstance(val, (list, dict)):
        return str(val)
    if isinstance(val, float):
        return f"{val:.4f}"
    return str(val)
