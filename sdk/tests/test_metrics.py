"""
Unit tests for all 8 FairLens fairness metrics.
Each test uses a known-outcome dataset where the expected metric value
is exactly computable by hand.
"""
import pytest
import numpy as np
import pandas as pd

from fairlens.metrics.demographic_parity import demographic_parity_difference
from fairlens.metrics.equalized_odds import equalized_odds_difference
from fairlens.metrics.disparate_impact import disparate_impact_ratio
from fairlens.metrics.calibration import calibration_error_per_group
from fairlens.metrics.theil import theil_index
from fairlens.metrics.statistical_parity import statistical_parity_difference
from fairlens.metrics.average_odds import average_odds_difference
from fairlens.metrics.equal_opportunity import equal_opportunity_difference


class TestDemographicParityDifference:
    def test_known_outcome(self):
        # Group A: 3/5 positive = 0.6, Group B: 2/5 positive = 0.4 → DPD = 0.2
        y_pred = np.array([1, 1, 1, 0, 0, 1, 1, 0, 0, 0])
        sensitive = pd.Series(["A", "A", "A", "A", "A", "B", "B", "B", "B", "B"])
        y_test = np.zeros(10)  # unused
        result = demographic_parity_difference(y_test, y_pred, sensitive)
        assert abs(result - 0.2) < 1e-6

    def test_perfect_parity(self):
        y_pred = np.array([1, 0, 1, 0])
        sensitive = pd.Series(["A", "A", "B", "B"])
        result = demographic_parity_difference(np.zeros(4), y_pred, sensitive)
        assert abs(result) < 1e-6

    def test_single_group(self):
        y_pred = np.array([1, 0, 1])
        sensitive = pd.Series(["A", "A", "A"])
        result = demographic_parity_difference(np.zeros(3), y_pred, sensitive)
        assert result == 0.0

    def test_maximum_disparity(self):
        # A: all positive, B: all negative → DPD = 1.0
        y_pred = np.array([1, 1, 0, 0])
        sensitive = pd.Series(["A", "A", "B", "B"])
        result = demographic_parity_difference(np.zeros(4), y_pred, sensitive)
        assert abs(result - 1.0) < 1e-6


class TestEqualizedOddsDifference:
    def test_known_outcome(self):
        # Group A: TPR=1.0 (1/1), FPR=0.5 (1/2)
        # Group B: TPR=0.0 (0/1), FPR=0.0 (0/2)
        # TPR diff = 1.0, FPR diff = 0.5 → EOD = max(1.0, 0.5) = 1.0
        y_test = np.array([1, 0, 0, 1, 0, 0])
        y_pred = np.array([1, 1, 0, 0, 0, 0])
        sensitive = pd.Series(["A", "A", "A", "B", "B", "B"])
        result = equalized_odds_difference(y_test, y_pred, sensitive)
        assert abs(result - 1.0) < 1e-6

    def test_equal_odds(self):
        y_test = np.array([1, 0, 1, 0])
        y_pred = np.array([1, 0, 1, 0])
        sensitive = pd.Series(["A", "A", "B", "B"])
        result = equalized_odds_difference(y_test, y_pred, sensitive)
        assert abs(result) < 1e-6


class TestDisparateImpactRatio:
    def test_known_outcome(self):
        # A: 2/4 = 0.5, B: 1/4 = 0.25 → DIR = 0.25/0.5 = 0.5
        y_pred = np.array([1, 1, 0, 0, 1, 0, 0, 0])
        sensitive = pd.Series(["A", "A", "A", "A", "B", "B", "B", "B"])
        result = disparate_impact_ratio(np.zeros(8), y_pred, sensitive)
        assert abs(result - 0.5) < 1e-6

    def test_perfect_parity(self):
        y_pred = np.array([1, 0, 1, 0])
        sensitive = pd.Series(["A", "A", "B", "B"])
        result = disparate_impact_ratio(np.zeros(4), y_pred, sensitive)
        assert abs(result - 1.0) < 1e-6

    def test_eeoc_threshold(self):
        # A: 4/5 = 0.8, B: 3/5 = 0.6 → DIR = 0.6/0.8 = 0.75 < 0.80
        y_pred = np.array([1, 1, 1, 1, 0, 1, 1, 1, 0, 0])
        sensitive = pd.Series(["A"] * 5 + ["B"] * 5)
        result = disparate_impact_ratio(np.zeros(10), y_pred, sensitive)
        assert abs(result - 0.75) < 1e-6
        assert result < 0.80  # Would violate EEOC 4/5ths rule


class TestCalibrationError:
    def test_known_outcome(self):
        # A: PPV = P(y=1|ŷ=1) = 1/2 = 0.5
        # B: PPV = P(y=1|ŷ=1) = 2/2 = 1.0
        # Error = 1.0 - 0.5 = 0.5
        y_test = np.array([1, 0, 0, 1, 1, 0])
        y_pred = np.array([1, 1, 0, 1, 1, 0])
        sensitive = pd.Series(["A", "A", "A", "B", "B", "B"])
        result = calibration_error_per_group(y_test, y_pred, sensitive)
        assert abs(result - 0.5) < 1e-6

    def test_perfect_calibration(self):
        y_test = np.array([1, 0, 1, 0])
        y_pred = np.array([1, 0, 1, 0])
        sensitive = pd.Series(["A", "A", "B", "B"])
        result = calibration_error_per_group(y_test, y_pred, sensitive)
        assert abs(result) < 1e-6


class TestTheilIndex:
    def test_perfect_equality(self):
        # Both groups have same positive rate → Theil = 0
        y_pred = np.array([1, 0, 1, 0])
        sensitive = pd.Series(["A", "A", "B", "B"])
        result = theil_index(np.zeros(4), y_pred, sensitive)
        assert abs(result) < 1e-6

    def test_inequality(self):
        # A: all positive (1.0), B: all negative (0.0) → high Theil
        y_pred = np.array([1, 1, 0, 0])
        sensitive = pd.Series(["A", "A", "B", "B"])
        result = theil_index(np.zeros(4), y_pred, sensitive)
        assert result > 0


class TestStatisticalParityDifference:
    def test_matches_dpd(self):
        y_pred = np.array([1, 1, 1, 0, 0, 1, 1, 0, 0, 0])
        sensitive = pd.Series(["A"] * 5 + ["B"] * 5)
        y_test = np.zeros(10)
        dpd = demographic_parity_difference(y_test, y_pred, sensitive)
        spd = statistical_parity_difference(y_test, y_pred, sensitive)
        assert abs(dpd - spd) < 1e-6


class TestAverageOddsDifference:
    def test_known_outcome(self):
        # A: TPR=1.0, FPR=0.5; B: TPR=0.0, FPR=0.0
        # AOD = 0.5 * (|1.0-0.0| + |0.5-0.0|) = 0.5 * 1.5 = 0.75
        y_test = np.array([1, 0, 0, 1, 0, 0])
        y_pred = np.array([1, 1, 0, 0, 0, 0])
        sensitive = pd.Series(["A", "A", "A", "B", "B", "B"])
        result = average_odds_difference(y_test, y_pred, sensitive)
        assert abs(result - 0.75) < 1e-6


class TestEqualOpportunityDifference:
    def test_known_outcome(self):
        # A: TPR = 1/1 = 1.0, B: TPR = 0/1 = 0.0 → EOppD = 1.0
        y_test = np.array([1, 0, 0, 1, 0, 0])
        y_pred = np.array([1, 1, 0, 0, 0, 0])
        sensitive = pd.Series(["A", "A", "A", "B", "B", "B"])
        result = equal_opportunity_difference(y_test, y_pred, sensitive)
        assert abs(result - 1.0) < 1e-6

    def test_equal_opportunity(self):
        y_test = np.array([1, 0, 1, 0])
        y_pred = np.array([1, 0, 1, 0])
        sensitive = pd.Series(["A", "A", "B", "B"])
        result = equal_opportunity_difference(y_test, y_pred, sensitive)
        assert abs(result) < 1e-6


class TestAuditIntegration:
    """Integration test for the full audit() pipeline."""

    def test_biased_model_flagged(self):
        import fairlens
        from unittest.mock import MagicMock

        model = MagicMock()
        model.predict = lambda X: (X["sensitive"] == "A").astype(int).values
        X = pd.DataFrame({
            "feature": np.random.randn(200),
            "sensitive": ["A"] * 100 + ["B"] * 100,
        })
        y = pd.Series(np.random.randint(0, 2, 200))
        report = fairlens.audit(model, X, y, ["sensitive"])
        assert report.flag_violation() is True
        assert len(report.violations) >= 1

    def test_fair_model_passes(self):
        import fairlens
        from unittest.mock import MagicMock

        model = MagicMock()
        model.predict = lambda X_: np.array([1, 0] * (len(X_) // 2))
        X = pd.DataFrame({
            "feature": np.random.randn(200),
            "sensitive": ["A"] * 100 + ["B"] * 100,
        })
        y = pd.Series([1, 0] * 100)
        report = fairlens.audit(model, X, y, ["sensitive"])
        assert report.metrics["sensitive"]["demographic_parity_difference"] < 0.01

    def test_report_serialization(self):
        import fairlens
        from unittest.mock import MagicMock
        import json

        model = MagicMock()
        model.predict = lambda X_: np.array([1, 0] * (len(X_) // 2))
        X = pd.DataFrame({"f": np.random.randn(100), "s": ["A"] * 50 + ["B"] * 50})
        y = pd.Series([1, 0] * 50)
        report = fairlens.audit(model, X, y, ["s"])

        # JSON roundtrip
        j = report.to_json()
        parsed = json.loads(j)
        assert "report_id" in parsed
        assert "metrics" in parsed
        assert "passed" in parsed

        # HTML generation
        html = report.to_html()
        assert "FairLens Audit Report" in html
        assert report.report_id[:8] in html
