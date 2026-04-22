"""
Equal Opportunity Difference

Measures the difference in True Positive Rates (recall) across demographic
groups. Focuses specifically on whether qualified individuals from all groups
have equal chances of receiving a positive prediction.

Range: [0, 1]. Lower is fairer. 0 = equal opportunity.
"""
import numpy as np
import pandas as pd


def equal_opportunity_difference(y_test, y_pred, sensitive) -> float:
    """
    max(TPR_a) - min(TPR_a) across all groups a.

    TPR = P(ŷ=1 | y=1, A=a) — the true positive rate per group.

    Args:
        y_test: Ground-truth labels (binary 0/1)
        y_pred: Predicted labels (binary 0/1)
        sensitive: Series of group membership values

    Returns:
        float: Max TPR difference across groups
    """
    y_test = np.asarray(y_test)
    y_pred = np.asarray(y_pred)
    sensitive = pd.Series(sensitive).reset_index(drop=True)

    groups = sensitive.unique()
    tpr_by_group = {}

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

    if len(tpr_by_group) < 2:
        return 0.0

    return float(max(tpr_by_group.values()) - min(tpr_by_group.values()))
