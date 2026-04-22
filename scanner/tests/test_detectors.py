"""
Tests for all three bias detectors with synthetic datasets where biases
are injected at known levels.
"""
import pytest
import pandas as pd
import numpy as np

from scanner.detectors.imbalance import detect_class_imbalance
from scanner.detectors.proxy_leakage import detect_proxy_leakage
from scanner.detectors.label_bias import detect_label_bias


def make_biased_dataframe(n=500, seed=42):
    """Create a synthetic DataFrame with known biases."""
    rng = np.random.RandomState(seed)
    df = pd.DataFrame({
        "feature_1": rng.randn(n),
        "feature_2": rng.randn(n),
        "gender": rng.choice(["M", "F"], n, p=[0.6, 0.4]),
        "race": rng.choice(["White", "Black", "Asian"], n, p=[0.5, 0.3, 0.2]),
    })
    # Inject label bias: M gets 70% positive, F gets 30% positive
    df["label"] = 0
    m_mask = df["gender"] == "M"
    f_mask = df["gender"] == "F"
    df.loc[m_mask, "label"] = rng.binomial(1, 0.7, m_mask.sum())
    df.loc[f_mask, "label"] = rng.binomial(1, 0.3, f_mask.sum())

    # Inject proxy: feature_3 is strongly correlated with gender
    df["proxy_feature"] = (df["gender"] == "M").astype(int) + rng.normal(0, 0.1, n)

    return df


class TestClassImbalance:
    def test_detects_imbalance(self):
        df = make_biased_dataframe()
        results = detect_class_imbalance(df, ["gender"], "label", threshold=1.5)
        assert "gender" in results
        assert results["gender"]["flagged"] == True
        assert results["gender"]["ratio"] > 1.5

    def test_no_imbalance(self):
        rng = np.random.RandomState(42)
        df = pd.DataFrame({
            "group": rng.choice(["A", "B"], 500),
            "label": rng.binomial(1, 0.5, 500),
        })
        results = detect_class_imbalance(df, ["group"], "label", threshold=1.5)
        if "group" in results:
            assert results["group"]["flagged"] == False


class TestProxyLeakage:
    def test_detects_proxy(self):
        df = make_biased_dataframe()
        results = detect_proxy_leakage(df, ["gender"], mi_threshold=0.1)
        proxy_scores = [r for r in results if r["column"] == "proxy_feature"]
        assert len(proxy_scores) > 0
        assert proxy_scores[0]["mi_score"] > 0.1
        assert proxy_scores[0]["flagged"] == True

    def test_independent_features(self):
        rng = np.random.RandomState(42)
        df = pd.DataFrame({
            "f1": rng.randn(500),
            "f2": rng.randn(500),
            "group": rng.choice(["A", "B"], 500),
        })
        results = detect_proxy_leakage(df, ["group"], mi_threshold=0.1)
        flagged = [r for r in results if r["flagged"]]
        assert len(flagged) == 0


class TestLabelBias:
    def test_detects_label_bias(self):
        df = make_biased_dataframe()
        results = detect_label_bias(df, ["gender"], "label")
        assert "gender" in results
        assert results["gender"]["max_disparity"] > 0.2
        assert results["gender"]["flagged"] == True

    def test_no_label_bias(self):
        rng = np.random.RandomState(42)
        df = pd.DataFrame({
            "group": rng.choice(["A", "B"], 500),
            "label": rng.binomial(1, 0.5, 500),
        })
        results = detect_label_bias(df, ["group"], "label")
        if "group" in results:
            assert results["group"]["max_disparity"] < 0.1
