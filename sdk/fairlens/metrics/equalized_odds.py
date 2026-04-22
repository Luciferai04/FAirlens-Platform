"""
Equalized Odds Difference

Measures the maximum difference in True Positive Rates (TPR) and
False Positive Rates (FPR) across demographic groups. A value of 0
indicates that the model's error rates are equal across all groups.

Range: [0, 1]. Lower is fairer.
"""
import numpy as np
import pandas as pd


def equalized_odds_difference(y_test, y_pred, sensitive) -> float:
    """
    max(|TPR_a - TPR_b|, |FPR_a - FPR_b|) across all group pairs.

    Args:
        y_test: Ground-truth labels (binary 0/1)
        y_pred: Predicted labels (binary 0/1)
        sensitive: Series of group membership values

    Returns:
        float: Maximum equalized odds difference
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

        # True Positive Rate: P(ŷ=1 | y=1)
        pos_mask = y_t == 1
        if pos_mask.sum() > 0:
            tpr_by_group[g] = y_p[pos_mask].mean()
        else:
            tpr_by_group[g] = 0.0

        # False Positive Rate: P(ŷ=1 | y=0)
        neg_mask = y_t == 0
        if neg_mask.sum() > 0:
            fpr_by_group[g] = y_p[neg_mask].mean()
        else:
            fpr_by_group[g] = 0.0

    if len(tpr_by_group) < 2:
        return 0.0

    tpr_diff = max(tpr_by_group.values()) - min(tpr_by_group.values())
    fpr_diff = max(fpr_by_group.values()) - min(fpr_by_group.values())

    return float(max(tpr_diff, fpr_diff))
