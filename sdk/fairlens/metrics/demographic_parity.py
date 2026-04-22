"""
Demographic Parity Difference (DPD)

Measures the difference in positive prediction rates between the most and
least favored demographic groups. A value of 0 indicates perfect parity.

Range: [0, 1]. Lower is fairer.
"""
import numpy as np
import pandas as pd


def demographic_parity_difference(y_test, y_pred, sensitive) -> float:
    """
    P(ŷ=1 | A=a) max - min across all groups a.

    Args:
        y_test: Ground-truth labels (unused, included for API consistency)
        y_pred: Predicted labels (binary 0/1)
        sensitive: Series of group membership values

    Returns:
        float: Max positive rate - min positive rate across groups
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
