"""
Disparate Impact Ratio

Ratio of the lowest group's positive prediction rate to the highest group's
positive prediction rate. Based on the EEOC 4/5ths (80%) rule: a ratio below
0.80 indicates potential adverse impact.

Range: [0, 1]. Higher is fairer. 1.0 = perfect parity.
"""
import numpy as np
import pandas as pd


def disparate_impact_ratio(y_test, y_pred, sensitive) -> float:
    """
    min(P(ŷ=1|A=a)) / max(P(ŷ=1|A=a)) across all groups a.

    Args:
        y_test: Ground-truth labels (unused, included for API consistency)
        y_pred: Predicted labels (binary 0/1)
        sensitive: Series of group membership values

    Returns:
        float: Ratio of min to max positive prediction rate (0 to 1)
    """
    y_pred = np.asarray(y_pred)
    sensitive = pd.Series(sensitive).reset_index(drop=True)

    groups = sensitive.unique()
    rates = {}
    for g in groups:
        mask = sensitive == g
        if mask.sum() == 0:
            continue
        rates[g] = y_pred[mask].mean()

    if len(rates) < 2:
        return 1.0

    max_rate = max(rates.values())
    min_rate = min(rates.values())

    if max_rate == 0:
        return 1.0  # No positive predictions — trivially equal

    return float(min_rate / max_rate)
