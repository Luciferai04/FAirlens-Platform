from __future__ import annotations
"""
FairLens — Enterprise AI Bias Detection SDK

Detect, monitor, and remediate bias in production ML models.

Usage:
    import fairlens

    report = fairlens.audit(model, X_test, y_test, sensitive_cols=["gender", "race"])
    
    # Remediate bias using Synthetic Data Debiaser (D8)
    X_balanced = fairlens.debias(X_train, target_col="loan_status", sensitive_cols=["race"])
"""

from .audit import audit
from .report import AuditReport
from .debias import debias

__all__ = ["audit", "AuditReport", "debias"]
__version__ = "1.0.0"
