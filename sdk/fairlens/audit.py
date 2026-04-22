"""
fairlens.audit() — Core entry point for ML model fairness auditing.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union
import yaml

from .metrics import ALL_METRICS
from .report import AuditReport


def audit(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    sensitive_cols: list[str],
    threshold_config: Union[str, dict, None] = None,
    triggered_by: str = "sdk",
    model_id: str = "unknown",
) -> AuditReport:
    """
    Compute fairness metrics for a model across all sensitive attribute columns.
    """
    if callable(getattr(model, "predict", None)):
        y_pred = model.predict(X_test)
    elif callable(model):
        y_pred = model(X_test)
    else:
        raise TypeError("model must expose .predict() or be callable")

    y_pred = np.asarray(y_pred)
    y_test = pd.Series(y_test).reset_index(drop=True)
    thresholds = _load_thresholds(threshold_config)
    results = {}

    for col in sensitive_cols:
        if col not in X_test.columns:
            raise ValueError(f"sensitive_col '{col}' not found in X_test columns")
        sensitive = pd.Series(X_test[col].values).reset_index(drop=True)
        col_results = {}
        for metric_name, metric_fn in ALL_METRICS.items():
            col_results[metric_name] = metric_fn(
                y_test=y_test, y_pred=y_pred, sensitive=sensitive,
            )
        results[col] = col_results

    violations = _check_thresholds(results, thresholds)

    return AuditReport(
        metrics=results, thresholds=thresholds, violations=violations,
        sensitive_cols=sensitive_cols, triggered_by=triggered_by, model_id=model_id,
    )


def _load_thresholds(config) -> dict:
    defaults = {
        "demographic_parity_difference": 0.10,
        "equalized_odds_difference": 0.10,
        "disparate_impact_ratio": 0.80,
        "calibration_error": 0.05,
        "theil_index": 0.10,
        "statistical_parity_difference": 0.10,
        "average_odds_difference": 0.10,
        "equal_opportunity_difference": 0.10,
    }
    if config is None:
        return defaults
    if isinstance(config, dict):
        merged = {**defaults}
        if "thresholds" in config:
            merged.update(config["thresholds"])
        else:
            merged.update(config)
        return merged
    if isinstance(config, (str, Path)):
        with open(config) as f:
            policy = yaml.safe_load(f)
        return {**defaults, **policy.get("thresholds", {})}
    raise TypeError(f"threshold_config must be str path, dict, or None; got {type(config)}")


def _check_thresholds(results: dict, thresholds: dict) -> list[dict]:
    violations = []
    for col, col_metrics in results.items():
        for metric, value in col_metrics.items():
            limit = thresholds.get(metric)
            if limit is None:
                continue
            if metric == "disparate_impact_ratio":
                if value < limit:
                    violations.append({"col": col, "metric": metric, "value": value,
                                       "threshold": limit, "direction": "below"})
            else:
                if abs(value) > limit:
                    violations.append({"col": col, "metric": metric, "value": value,
                                       "threshold": limit, "direction": "above"})
    return violations
