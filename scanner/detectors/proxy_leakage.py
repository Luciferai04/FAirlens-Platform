"""
Proxy Leakage Detector — identifies features that are proxies for
protected attributes using mutual information.

Flags columns where MI > 0.1 with any protected attribute.
"""
import pandas as pd
import numpy as np
from sklearn.feature_selection import mutual_info_classif
from sklearn.preprocessing import LabelEncoder


def detect_proxy_leakage(
    df: pd.DataFrame,
    sensitive_cols: list[str],
    mi_threshold: float = 0.1,
) -> list[dict]:
    """
    Compute mutual information between each non-protected feature and
    each protected column.

    Returns:
        List of {column, protected_col, mi_score, flagged} dicts
    """
    results = []
    feature_cols = [c for c in df.columns if c not in sensitive_cols]
    le = LabelEncoder()

    for protected_col in sensitive_cols:
        # Encode protected attribute as integer target
        try:
            y_encoded = le.fit_transform(df[protected_col].astype(str))
        except Exception:
            continue

        # Prepare feature matrix (encode categoricals)
        X_encoded = pd.DataFrame()
        for fc in feature_cols:
            if df[fc].dtype == object or df[fc].dtype.name == "category":
                try:
                    X_encoded[fc] = le.fit_transform(df[fc].astype(str))
                except Exception:
                    X_encoded[fc] = 0
            else:
                X_encoded[fc] = df[fc].fillna(0)

        if X_encoded.empty:
            continue

        # Compute mutual information
        mi_scores = mutual_info_classif(
            X_encoded, y_encoded, discrete_features="auto", random_state=42
        )

        for fc, mi_score in zip(feature_cols, mi_scores):
            results.append({
                "column": fc,
                "protected_col": protected_col,
                "mi_score": round(float(mi_score), 4),
                "flagged": float(mi_score) > mi_threshold,
            })

    return results
