"""
Class Imbalance Detector — detects disproportionate class distribution
across protected attribute groups.

Flags if imbalance ratio > 1.5 for any protected attribute.
"""
import pandas as pd
import numpy as np


def detect_class_imbalance(
    df: pd.DataFrame,
    sensitive_cols: list[str],
    label_col: str = "label",
    threshold: float = 1.5,
) -> dict:
    """
    Compute class imbalance ratio per protected attribute.

    Returns:
        {col: {ratio: float, majority_group: str, minority_group: str, flagged: bool}}
    """
    results = {}
    for col in sensitive_cols:
        groups = df[col].unique()
        rates = {}
        for g in groups:
            group_df = df[df[col] == g]
            if len(group_df) == 0:
                continue
            rates[g] = group_df[label_col].mean()

        if len(rates) < 2:
            continue

        max_group = max(rates, key=rates.get)
        min_group = min(rates, key=rates.get)
        min_rate = rates[min_group]
        max_rate = rates[max_group]

        ratio = max_rate / (min_rate + 1e-9)
        results[col] = {
            "ratio": round(ratio, 4),
            "majority_group": str(max_group),
            "minority_group": str(min_group),
            "majority_rate": round(max_rate, 4),
            "minority_rate": round(min_rate, 4),
            "flagged": ratio > threshold,
        }

    return results
