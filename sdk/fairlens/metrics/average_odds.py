"""
Average Odds Difference

The average of the differences in True Positive Rates and False Positive
Rates across demographic groups. Provides a balanced view of equalized
odds violations.

Range: [0, 1]. Lower is fairer. 0 = equal average odds.
"""
import numpy as np
import pandas as pd


def average_odds_difference(y_test, y_pred, sensitive) -> float:
    """
    0.5 * (|TPR_max - TPR_min| + |FPR_max - FPR_min|) across groups.

    Args:
        y_test: Ground-truth labels (binary 0/1)
        y_pred: Predicted labels (binary 0/1)
        sensitive: Series of group membership values

    Returns:
        float: Average of TPR and FPR differences
    """
    y_test = np.asarray(y_test)
    y_pred = np.asarray(y_pred)
    sensitive = pd.Series(sensitive).reset_index(drop=True)

    groups = sensitive.unique()
    tpr_by_group = {}
    fpr_by_group = {}

    for g in groups:
        mask = sensitive == g
        y_t = y_test[mask]
        y_p = y_pred[mask]

        # True Positive Rate
        pos_mask = y_t == 1
        tpr_by_group[g] = y_p[pos_mask].mean() if pos_mask.sum() > 0 else 0.0

        # False Positive Rate
        neg_mask = y_t == 0
        fpr_by_group[g] = y_p[neg_mask].mean() if neg_mask.sum() > 0 else 0.0

    if len(tpr_by_group) < 2:
        return 0.0

    tpr_diff = max(tpr_by_group.values()) - min(tpr_by_group.values())
    fpr_diff = max(fpr_by_group.values()) - min(fpr_by_group.values())

    return float(0.5 * (tpr_diff + fpr_diff))
