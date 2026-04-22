from __future__ import annotations
"""
FairLens — Enterprise AI Bias Detection SDK

Detect, monitor, and remediate bias in production ML models.

Usage:
    import fairlens

    report = fairlens.audit(model, X_test, y_test, sensitive_cols=["gender", "race"])
    print(report.to_json())
    print(f"Passed: {not report.flag_violation()}")
"""

from .audit import audit
from .report import AuditReport

__all__ = ["audit", "AuditReport"]
__version__ = "1.0.0"
