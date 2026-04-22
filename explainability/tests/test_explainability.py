"""Tests for the explainability overlay (D9)."""
from __future__ import annotations
import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


@pytest.fixture(scope="module")
def trained_model_and_data():
    """Train a simple RF model for explainability tests."""
    rng = np.random.RandomState(42)
    n = 300
    X = pd.DataFrame({
        "feature_a": rng.normal(50, 10, n),
        "feature_b": rng.normal(30, 5, n),
        "feature_c": rng.randint(0, 5, n).astype(float),
        "gender": rng.choice(["male", "female"], n),
    })
    # Make feature_a highly predictive, feature_c less so
    y = ((X["feature_a"] > 50) & (X["feature_b"] > 28)).astype(int)

    features = ["feature_a", "feature_b", "feature_c"]
    model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=4)
    model.fit(X[features], y)

    class _W:
        def __init__(self, m, cols):
            self.m = m
            self.cols = cols
        def predict(self, Xdf):
            return self.m.predict(Xdf[self.cols])
        def predict_proba(self, Xdf):
            return self.m.predict_proba(Xdf[self.cols])

    return _W(model, features), X, y


class TestGroupAttributions:
    """compute_group_attributions() returns per-group feature importance."""

    def test_returns_dict_per_group(self, trained_model_and_data):
        from explainability.shap_runner import compute_group_attributions
        model, X, y = trained_model_and_data

        result = compute_group_attributions(model, X, "gender")

        assert "male" in result
        assert "female" in result
        assert "feature_a" in result["male"]
        assert "feature_b" in result["male"]

    def test_attributions_are_non_negative(self, trained_model_and_data):
        from explainability.shap_runner import compute_group_attributions
        model, X, y = trained_model_and_data

        result = compute_group_attributions(model, X, "gender")

        for group, attrs in result.items():
            for feature, value in attrs.items():
                assert value >= 0, f"Negative attribution for {group}.{feature}: {value}"

    def test_top_feature_is_predictive(self, trained_model_and_data):
        from explainability.shap_runner import compute_group_attributions
        model, X, y = trained_model_and_data

        result = compute_group_attributions(model, X, "gender")

        # feature_a should be most important across both groups
        for group in ["male", "female"]:
            attrs = result[group]
            top_feature = max(attrs, key=attrs.get)
            assert top_feature in ["feature_a", "feature_b"], \
                f"Expected predictive feature as top, got {top_feature}"


class TestLocalAttributions:
    """compute_local_attributions() explains single instances."""

    def test_returns_per_feature_dict(self, trained_model_and_data):
        from explainability.shap_runner import compute_local_attributions
        model, X, y = trained_model_and_data

        features_only = X[["feature_a", "feature_b", "feature_c"]]
        result = compute_local_attributions(model, features_only, 0)

        assert isinstance(result, dict)
        assert "feature_a" in result
        assert "feature_b" in result
        assert "feature_c" in result


class TestDisparityDrivers:
    """compute_disparity_drivers() identifies proxy risk features."""

    def test_returns_sorted_by_disparity(self, trained_model_and_data):
        from explainability.shap_runner import compute_disparity_drivers
        model, X, y = trained_model_and_data

        result = compute_disparity_drivers(model, X, "gender")

        assert isinstance(result, dict)
        disparities = [v["disparity"] for v in result.values()]
        assert disparities == sorted(disparities, reverse=True)

    def test_driver_has_expected_keys(self, trained_model_and_data):
        from explainability.shap_runner import compute_disparity_drivers
        model, X, y = trained_model_and_data

        result = compute_disparity_drivers(model, X, "gender")
        first_feature = list(result.values())[0]

        assert "max_group" in first_feature
        assert "min_group" in first_feature
        assert "disparity" in first_feature
        assert "is_proxy_risk" in first_feature


class TestPermutationFallback:
    """_permutation_importance_fallback works without SHAP."""

    def test_fallback_shape(self, trained_model_and_data):
        from explainability.shap_runner import _permutation_importance_fallback
        model, X, y = trained_model_and_data

        features_only = X[["feature_a", "feature_b", "feature_c"]]
        result = _permutation_importance_fallback(model, features_only)

        assert result.shape == (len(features_only), 3)
