"""Tests for the sector benchmark library (D10)."""
from __future__ import annotations
import pytest


class TestBaselines:
    """Baseline values are present and correctly structured."""

    def test_all_sectors_present(self):
        from benchmarks.baselines import SECTOR_BASELINES
        assert "financial" in SECTOR_BASELINES
        assert "healthcare" in SECTOR_BASELINES
        assert "hr" in SECTOR_BASELINES

    def test_financial_has_core_metrics(self):
        from benchmarks.baselines import SECTOR_BASELINES
        fin = SECTOR_BASELINES["financial"]
        assert "demographic_parity_difference" in fin
        assert "disparate_impact_ratio" in fin
        assert "equalized_odds_difference" in fin

    def test_each_metric_has_percentiles(self):
        from benchmarks.baselines import SECTOR_BASELINES
        for sector, metrics in SECTOR_BASELINES.items():
            for metric_name, data in metrics.items():
                assert "p75_industry" in data, f"{sector}/{metric_name} missing p75"
                assert "p90_industry" in data, f"{sector}/{metric_name} missing p90"
                assert isinstance(data["p75_industry"], (int, float))

    def test_p75_stricter_than_p90_for_lower_is_better(self):
        from benchmarks.baselines import SECTOR_BASELINES
        for sector, metrics in SECTOR_BASELINES.items():
            for name, data in metrics.items():
                if name != "disparate_impact_ratio":
                    assert data["p75_industry"] <= data["p90_industry"], \
                        f"{sector}/{name}: p75 should be ≤ p90 (lower=better)"


class TestGetBaseline:
    """get_baseline() returns correct values."""

    def test_financial_dpd(self):
        from benchmarks.baselines import get_baseline
        val = get_baseline("financial", "demographic_parity_difference")
        assert val == 0.09

    def test_hr_dir(self):
        from benchmarks.baselines import get_baseline
        val = get_baseline("hr", "disparate_impact_ratio")
        assert val == 0.85

    def test_unknown_sector_raises(self):
        from benchmarks.baselines import get_baseline
        with pytest.raises(ValueError, match="Unknown sector"):
            get_baseline("aviation", "demographic_parity_difference")

    def test_unknown_metric_raises(self):
        from benchmarks.baselines import get_baseline
        with pytest.raises(ValueError, match="No baseline"):
            get_baseline("financial", "nonexistent_metric")


class TestCompareToBenchmark:
    """compare_to_benchmark() correctly ranks model metrics."""

    def test_good_model_ranks_top_quartile(self):
        from benchmarks.baselines import compare_to_benchmark
        result = compare_to_benchmark(
            {"demographic_parity_difference": 0.05, "disparate_impact_ratio": 0.90},
            sector="financial",
        )
        assert result["demographic_parity_difference"]["ranking"] == "top_quartile"
        assert result["disparate_impact_ratio"]["ranking"] == "top_quartile"

    def test_bad_model_ranks_below_average(self):
        from benchmarks.baselines import compare_to_benchmark
        result = compare_to_benchmark(
            {"demographic_parity_difference": 0.25, "disparate_impact_ratio": 0.60},
            sector="financial",
        )
        assert result["demographic_parity_difference"]["ranking"] == "below_average"
        assert result["disparate_impact_ratio"]["ranking"] == "below_average"

    def test_comparison_has_source(self):
        from benchmarks.baselines import compare_to_benchmark
        result = compare_to_benchmark(
            {"demographic_parity_difference": 0.10}, sector="financial"
        )
        assert "source" in result["demographic_parity_difference"]
        assert len(result["demographic_parity_difference"]["source"]) > 0

    def test_unknown_metrics_ignored(self):
        from benchmarks.baselines import compare_to_benchmark
        result = compare_to_benchmark(
            {"made_up_metric": 0.5}, sector="financial"
        )
        assert "made_up_metric" not in result


class TestHMDALoader:
    """HMDA synthetic dataset loader works."""

    def test_load_sample_returns_dataframe(self):
        from benchmarks.loaders.hmda import load_hmda_sample
        df = load_hmda_sample(n_rows=100)
        assert len(df) == 100
        assert "race" in df.columns
        assert "sex" in df.columns
        assert "approved" in df.columns
        assert "loan_amount" in df.columns

    def test_sample_has_bias(self):
        from benchmarks.loaders.hmda import load_hmda_sample
        df = load_hmda_sample(n_rows=5000)
        white_rate = df[df["race"] == "White"]["approved"].mean()
        black_rate = df[df["race"] == "Black"]["approved"].mean()
        # White approval rate should be higher (bias injected)
        assert white_rate > black_rate
