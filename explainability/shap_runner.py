"""
Computes per-group SHAP attributions and writes to BigQuery.
Bridges SHAP library with Vertex Explainable AI.

Usage (Library):
    from explainability import compute_group_attributions
    attributions = compute_group_attributions(model, X, "gender", "model-v1")

Usage (with BQ):
    attributions = compute_group_attributions(
        model, X, "gender", "model-v1", project="my-project"
    )
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd


def compute_group_attributions(
    model,
    X: pd.DataFrame,
    sensitive_col: str,
    model_id: str = "unknown",
    project: str | None = None,
    background_sample_size: int = 100,
    write_to_bq: bool = False,
) -> dict:
    """
    Compute SHAP values per demographic group.

    Args:
        model: sklearn estimator with .predict() or .predict_proba()
        X: Feature DataFrame (must include sensitive_col)
        sensitive_col: Column name for demographic grouping
        model_id: Model identifier for attribution record
        project: GCP project ID (required if write_to_bq=True)
        background_sample_size: Background dataset size for KernelExplainer
        write_to_bq: Whether to write results to BigQuery

    Returns:
        dict of {group: {feature: mean_abs_shap}}
    """
    features = [c for c in X.columns if c != sensitive_col]
    X_features = X[features]

    shap_values = _compute_shap_values(model, X_features, background_sample_size)
    shap_df = pd.DataFrame(shap_values, columns=features, index=X.index)

    # Compute per-group mean |SHAP|
    groups = X[sensitive_col].unique()
    group_attributions = {}
    bq_rows = []

    for group in groups:
        mask = X[sensitive_col] == group
        group_shap = shap_df[mask].abs().mean()
        group_attributions[str(group)] = group_shap.to_dict()

        for feature, importance in group_shap.items():
            bq_rows.append({
                "attribution_id": str(uuid.uuid4()),
                "model_id": model_id,
                "sensitive_col": sensitive_col,
                "group_value": str(group),
                "feature_name": feature,
                "mean_abs_shap": float(importance),
                "computed_at": datetime.now(timezone.utc).isoformat(),
            })

    if write_to_bq and project:
        _write_to_bq(bq_rows, project)

    return group_attributions


def compute_local_attributions(
    model,
    X: pd.DataFrame,
    instance_idx: int,
    background_sample_size: int = 100,
) -> dict:
    """
    Compute SHAP attribution for a single instance.

    Args:
        model: sklearn estimator
        X: Feature DataFrame
        instance_idx: Row index to explain
        background_sample_size: Background size for explainer

    Returns:
        dict of {feature: shap_value}
    """
    shap_values = _compute_shap_values(model, X, background_sample_size)
    return dict(zip(X.columns, shap_values[instance_idx]))


def compute_disparity_drivers(
    model,
    X: pd.DataFrame,
    sensitive_col: str,
    background_sample_size: int = 100,
) -> dict:
    """
    Identify which features drive the largest attribution disparity between groups.

    Returns:
        dict of {feature: {max_group, min_group, disparity, is_proxy_risk}}
    """
    attributions = compute_group_attributions(
        model, X, sensitive_col, background_sample_size=background_sample_size
    )

    features = list(next(iter(attributions.values())).keys())
    drivers = {}

    for feature in features:
        group_vals = {g: attrs[feature] for g, attrs in attributions.items()}
        max_group = max(group_vals, key=group_vals.get)
        min_group = min(group_vals, key=group_vals.get)
        disparity = group_vals[max_group] - group_vals[min_group]

        drivers[feature] = {
            "max_group": max_group,
            "max_importance": round(group_vals[max_group], 6),
            "min_group": min_group,
            "min_importance": round(group_vals[min_group], 6),
            "disparity": round(disparity, 6),
            "is_proxy_risk": disparity > 0.05,  # Flag features with >5% disparity
        }

    # Sort by disparity descending
    drivers = dict(sorted(drivers.items(), key=lambda x: x[1]["disparity"], reverse=True))
    return drivers


def _compute_shap_values(
    model,
    X: pd.DataFrame,
    background_sample_size: int = 100,
) -> np.ndarray:
    """Compute SHAP values using best available explainer."""
    try:
        import shap
    except ImportError:
        print("[Explainability] shap not installed — using permutation importance fallback")
        return _permutation_importance_fallback(model, X)

    # Try TreeExplainer first (fastest for tree-based models)
    if hasattr(model, "predict_proba"):
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Positive class
            return shap_values
        except Exception:
            pass

        # Fallback to KernelExplainer
        try:
            bg_size = min(background_sample_size, len(X))
            background = shap.sample(X, bg_size)
            explainer = shap.KernelExplainer(
                lambda x: model.predict_proba(x)[:, 1], background
            )
            return explainer.shap_values(X, nsamples=min(200, len(X)))
        except Exception:
            pass

    # Final fallback: permutation importance
    return _permutation_importance_fallback(model, X)


def _permutation_importance_fallback(model, X: pd.DataFrame) -> np.ndarray:
    """
    Fallback when SHAP is unavailable — uses prediction difference as proxy.
    Not true SHAP values but gives directional feature importance per row.
    """
    baseline = model.predict(X).mean()
    n_rows, n_features = X.shape
    importances = np.zeros((n_rows, n_features))

    for j in range(n_features):
        X_permuted = X.copy()
        X_permuted.iloc[:, j] = np.random.permutation(X_permuted.iloc[:, j].values)
        preds_permuted = model.predict(X_permuted)
        preds_original = model.predict(X)
        importances[:, j] = np.abs(preds_original - preds_permuted)

    return importances


def _write_to_bq(rows: list, project: str):
    """Write attribution rows to BigQuery."""
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=project)
        table = f"{project}.fairlens.shap_attributions"
        errors = client.insert_rows_json(table, rows)
        if errors:
            print(f"[Explainability] BigQuery write errors: {errors}")
        else:
            print(f"[Explainability] Wrote {len(rows)} attribution records to {table}")
    except ImportError:
        print("[Explainability] google-cloud-bigquery not available. Skipping BQ write.")
    except Exception as e:
        print(f"[Explainability] BQ write failed: {e}")
