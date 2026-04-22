"""Compliance report endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
import os

from auth import require_role

router = APIRouter()
BQ_PROJECT = os.environ.get("GCP_PROJECT_ID", "")
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true" or os.getenv("FAIRLENS_DEV_MODE", "") == "true"

SUPPORTED_FRAMEWORKS = ["eu_ai_act", "eeoc", "rbi_sebi"]

# ── Mock Data ──────────────────────────────────────────────────────────────
MOCK_REPORTS = [
    {"report_id": "FL-REP-8821", "model_id": "loan-approval-v2", "model_name": "CreditScoring_v4.2",
     "framework": "eu_ai_act", "generated_at": "2024-10-24T14:32:00Z",
     "kms_signed": True, "sha256_hash": "a9f4c8b2e3d1a7f6b9c4e8d2f1a5b3c7e9d1f4a6b8c2e5d7f9a1b3c5e7d1"},
    {"report_id": "FL-REP-8820", "model_id": "resume-screen-v3", "model_name": "ResumeScreen_Llama3",
     "framework": "eeoc", "generated_at": "2024-10-23T09:15:00Z",
     "kms_signed": True, "sha256_hash": "8b3f1a9ce7d2b4c6f8a0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2"},
    {"report_id": "FL-REP-8819", "model_id": "icu-triage-v1", "model_name": "TradingAlgo_XGBoost",
     "framework": "rbi_sebi", "generated_at": "2024-10-21T16:45:00Z",
     "kms_signed": True, "sha256_hash": "c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3"},
    {"report_id": "FL-REP-8818", "model_id": "loan-approval-v2", "model_name": "CreditScoring_v4.1",
     "framework": "eu_ai_act", "generated_at": "2024-09-15T11:20:00Z",
     "kms_signed": True, "sha256_hash": "7f8e9d0cb4a3c2e1d6f5b4a3c2e1d0f9e8b7a6c5d4e3f2a1b0c9d8e7f6a5b4"},
]


@router.get("/compliance")
async def list_compliance_reports(
    framework: str = Query(None, description="Filter by regulatory framework"),
    model_id: str = Query(None, description="Filter by model ID"),
    _=Depends(require_role(["auditor", "admin", "owner"])),
):
    """List or filter compliance reports."""
    if DEV_MODE:
        result = MOCK_REPORTS
        if framework:
            result = [r for r in result if r["framework"] == framework]
        if model_id:
            result = [r for r in result if r["model_id"] == model_id]
        return result

    if framework and framework not in SUPPORTED_FRAMEWORKS:
        raise HTTPException(400, f"Unknown framework. Choose from: {SUPPORTED_FRAMEWORKS}")
    return {
        "framework": framework,
        "model_id": model_id,
        "status": "generated",
        "download_url": f"/v1/reports/compliance/{model_id}/{framework}.pdf",
        "sections": _get_framework_sections(framework or "eu_ai_act"),
    }


@router.post("/compliance")
async def generate_compliance_report(
    body: dict,
    _=Depends(require_role(["auditor", "admin", "owner"])),
):
    """Generate a new compliance report."""
    model_id = body.get("model_id", "")
    framework = body.get("framework", "eu_ai_act")

    if framework not in SUPPORTED_FRAMEWORKS:
        raise HTTPException(400, f"Unknown framework. Choose from: {SUPPORTED_FRAMEWORKS}")

    if DEV_MODE:
        import hashlib, time
        hash_val = hashlib.sha256(f"{model_id}-{framework}-{time.time()}".encode()).hexdigest()
        return {
            "report_id": f"FL-REP-{int(time.time()) % 10000}",
            "model_id": model_id,
            "model_name": model_id,
            "framework": framework,
            "generated_at": "2024-10-24T14:32:00Z",
            "kms_signed": True,
            "sha256_hash": hash_val,
            "status": "generated",
        }

    return {
        "framework": framework,
        "model_id": model_id,
        "status": "generating",
    }


@router.get("/compliance/{report_id}/download")
async def download_report(
    report_id: str,
    _=Depends(require_role(["auditor", "admin", "owner"])),
):
    """Download a compliance report as PDF."""
    if DEV_MODE:
        # Return a simple placeholder PDF
        pdf_content = _generate_placeholder_pdf(report_id)
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=FairLens_{report_id}.pdf"}
        )

    try:
        from compliance.generator import generate_report
        pdf_bytes = generate_report("eeoc", report_id, os.getenv("GCP_PROJECT_ID"))
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=FairLens_{report_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to generate report: {e}")


def _generate_placeholder_pdf(report_id: str) -> bytes:
    """Generate a minimal valid PDF for dev mode."""
    content = f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
  /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 120 >>
stream
BT
/F1 24 Tf
100 700 Td
(FairLens Compliance Report) Tj
/F1 14 Tf
100 660 Td
(Report ID: {report_id}) Tj
ET
endstream endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000438 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
519
%%EOF"""
    return content.encode("latin-1")


def _get_framework_sections(framework: str) -> list[str]:
    sections = {
        "eu_ai_act": [
            "General Description of the AI System",
            "Accuracy, Robustness and Cybersecurity",
            "Risk Management System",
            "Human Oversight Measures",
            "Transparency and Explainability",
        ],
        "eeoc": [
            "Tool Description",
            "Selection Rate Analysis (4/5ths Rule)",
            "Mitigation Actions Taken",
        ],
        "rbi_sebi": [
            "Model Description",
            "Fairness Assessment",
            "Risk Classification",
            "Remediation History",
        ],
    }
    return sections.get(framework, [])
