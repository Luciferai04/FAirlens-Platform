"""
Gate tests — verify biased model triggers exit 1, fair model triggers exit 0.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
import sys
import os

# Add SDK to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk"))
import fairlens


def make_biased_model():
    """Model that always predicts 1 for group A, 0 for group B — maximum bias."""
    model = MagicMock()
    def predict(X):
        return (X["sensitive"] == "A").astype(int).values
    model.predict = predict
    return model


def make_fair_model():
    """Model that predicts identically for all groups — no bias."""
    model = MagicMock()
    def predict(X):
        return np.array([1, 0] * (len(X) // 2))
    model.predict = predict
    return model


class TestGateBiasedModel:
    def test_gate_fails_on_biased_model(self):
        X = pd.DataFrame({
            "feature": np.random.randn(200),
            "sensitive": ["A"] * 100 + ["B"] * 100,
        })
        y = pd.Series(np.random.randint(0, 2, 200))
        report = fairlens.audit(make_biased_model(), X, y, ["sensitive"])
        assert report.flag_violation() is True
        assert len(report.violations) >= 1
        # Verify DPD is exactly 1.0 (all A=1, all B=0)
        dpd = report.metrics["sensitive"]["demographic_parity_difference"]
        assert dpd == 1.0

    def test_disparate_impact_violated(self):
        X = pd.DataFrame({
            "feature": np.random.randn(200),
            "sensitive": ["A"] * 100 + ["B"] * 100,
        })
        y = pd.Series(np.random.randint(0, 2, 200))
        report = fairlens.audit(make_biased_model(), X, y, ["sensitive"])
        dir_val = report.metrics["sensitive"]["disparate_impact_ratio"]
        assert dir_val == 0.0  # B has 0% positive rate
        violations = [v for v in report.violations if v["metric"] == "disparate_impact_ratio"]
        assert len(violations) == 1


class TestGateFairModel:
    def test_gate_passes_on_fair_model(self):
        X = pd.DataFrame({
            "feature": np.random.randn(200),
            "sensitive": ["A"] * 100 + ["B"] * 100,
        })
        y = pd.Series([1, 0] * 100)
        report = fairlens.audit(make_fair_model(), X, y, ["sensitive"])
        dpd = report.metrics["sensitive"]["demographic_parity_difference"]
        assert dpd < 0.01
        # With default thresholds, fair model should pass
        assert report.flag_violation() is False

    def test_report_json_structure(self):
        X = pd.DataFrame({
            "feature": np.random.randn(100),
            "sensitive": ["A"] * 50 + ["B"] * 50,
        })
        y = pd.Series([1, 0] * 50)
        report = fairlens.audit(make_fair_model(), X, y, ["sensitive"])
        import json
        parsed = json.loads(report.to_json())
        assert "passed" in parsed
        assert parsed["passed"] is True
        assert "metrics" in parsed
        assert "sensitive" in parsed["metrics"]
