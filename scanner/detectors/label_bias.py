"""
Label Bias Detector — computes P(y=1 | group) for each group value
and returns the max disparity across groups.
"""
import pandas as pd
import numpy as np


def detect_label_bias(
    df: pd.DataFrame,
    sensitive_cols: list[str],
    label_col: str = "label",
) -> dict:
    """
    Compute P(y=1 | group) disparity per protected attribute.

    Returns:
        {col: {max_disparity: float, group_rates: {group: rate}, flagged: bool}}
    """
    results = {}
    for col in sensitive_cols:
        groups = df[col].unique()
        rates = {}
        for g in groups:
            group_df = df[df[col] == g]
            if len(group_df) == 0:
                continue
            rates[str(g)] = round(group_df[label_col].mean(), 4)

        if len(rates) < 2:
            continue

        max_disparity = max(rates.values()) - min(rates.values())
        results[col] = {
            "max_disparity": round(max_disparity, 4),
            "group_rates": rates,
            "flagged": max_disparity > 0.10,
        }

    return results
