"""
Theil Index (Generalized Entropy Index with α=1)

An information-theoretic measure of inequality in prediction outcomes
across demographic groups. Derived from econometrics; measures how
unevenly positive predictions are distributed relative to population share.

Range: [0, ∞). Lower is fairer. 0 = perfect equality.
"""
import numpy as np
import pandas as pd


def theil_index(y_test, y_pred, sensitive) -> float:
    """
    Theil T-statistic measuring inequality in positive prediction rates.

    T = Σ_g (r_g / r̄) * ln(r_g / r̄) * (n_g / N)

    where r_g = P(ŷ=1|A=g), r̄ = overall positive rate, n_g = group count.

    Args:
        y_test: Ground-truth labels (unused, included for API consistency)
        y_pred: Predicted labels (binary 0/1)
        sensitive: Series of group membership values

    Returns:
        float: Theil index value (0 = perfect equality)
    """
    y_pred = np.asarray(y_pred, dtype=float)
    sensitive = pd.Series(sensitive).reset_index(drop=True)

    overall_rate = y_pred.mean()
    if overall_rate == 0 or overall_rate == 1:
        return 0.0  # Trivially uniform

    groups = sensitive.unique()
    N = len(y_pred)
    theil = 0.0

    for g in groups:
        mask = sensitive == g
        n_g = mask.sum()
        if n_g == 0:
            continue

        r_g = y_pred[mask].mean()
        if r_g == 0:
            continue  # 0 * ln(0) → 0 by convention

        ratio = r_g / overall_rate
        theil += (n_g / N) * ratio * np.log(ratio)

    return float(max(0.0, theil))
