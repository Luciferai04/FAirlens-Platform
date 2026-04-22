"""
Calibration Error Per Group

Measures the maximum difference in calibration (|P(y=1|ŷ=1) - P(y=1|ŷ=1)|)
across demographic groups. A well-calibrated model has equal positive
predictive value across all groups.

Range: [0, 1]. Lower is fairer. 0 = perfectly calibrated across groups.
"""
import numpy as np
import pandas as pd


def calibration_error_per_group(y_test, y_pred, sensitive) -> float:
    """
    max|PPV_a - PPV_b| where PPV = P(y=1 | ŷ=1) across all group pairs.

    For groups with no positive predictions, PPV is treated as 0.

    Args:
        y_test: Ground-truth labels (binary 0/1)
        y_pred: Predicted labels (binary 0/1)
        sensitive: Series of group membership values

    Returns:
        float: Maximum calibration error across groups
    """
    y_test = np.asarray(y_test)
    y_pred = np.asarray(y_pred)
    sensitive = pd.Series(sensitive).reset_index(drop=True)

    groups = sensitive.unique()
    ppv_by_group = {}

    for g in groups:
        mask = sensitive == g
        y_t = y_test[mask]
        y_p = y_pred[mask]

        # Positive Predictive Value: P(y=1 | ŷ=1)
        pred_pos = y_p == 1
        if pred_pos.sum() > 0:
            ppv_by_group[g] = y_t[pred_pos].mean()
        else:
            ppv_by_group[g] = 0.0

    if len(ppv_by_group) < 2:
        return 0.0

    return float(max(ppv_by_group.values()) - min(ppv_by_group.values()))
