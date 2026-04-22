"""
Statistical Parity Difference

Equivalent to Demographic Parity Difference — measures the difference in
positive prediction rates between the most and least favored groups.
Included as a separate metric name for regulatory compatibility (some
frameworks reference SPD explicitly).

Range: [0, 1]. Lower is fairer. 0 = perfect statistical parity.
"""
import numpy as np
import pandas as pd


def statistical_parity_difference(y_test, y_pred, sensitive) -> float:
    """
    max(P(ŷ=1|A=a)) - min(P(ŷ=1|A=a)) across all groups a.

    Functionally identical to demographic_parity_difference.
    Both are provided because different regulatory frameworks
    reference them by different names.

    Args:
        y_test: Ground-truth labels (unused, included for API consistency)
        y_pred: Predicted labels (binary 0/1)
        sensitive: Series of group membership values

    Returns:
        float: Statistical parity difference
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
        return 0.0

    return float(max(rates.values()) - min(rates.values()))
