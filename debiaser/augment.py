"""
High-level augmentation API for bias mitigation.
Provides a simple one-call interface to equalize group representation.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from .ctgan_trainer import augment_dataset


def augment_underrepresented(
    df: pd.DataFrame,
    sensitive_col: str,
    strategy: str = "equalize",
    target_ratio: float = 1.0,
    epochs: int = 300,
) -> tuple[pd.DataFrame, dict]:
    """
    Automatically augment underrepresented groups in a dataset.

    Args:
        df: Input DataFrame
        sensitive_col: Protected attribute column
        strategy: "equalize" (match majority) | "boost" (use target_ratio)
        target_ratio: For "boost" strategy — ratio relative to majority group
        epochs: CTGAN training epochs

    Returns:
        (augmented_df, augmentation_report)
    """
    group_counts = df[sensitive_col].value_counts()
    majority_count = group_counts.max()
    majority_group = group_counts.idxmax()

    report = {
        "original_distribution": group_counts.to_dict(),
        "majority_group": majority_group,
        "majority_count": int(majority_count),
        "augmented_groups": {},
    }

    augmented_df = df.copy()

    for group_value, count in group_counts.items():
        if group_value == majority_group:
            continue

        if strategy == "equalize":
            target = int(majority_count)
        elif strategy == "boost":
            target = int(majority_count * target_ratio)
        else:
            raise ValueError(f"Unknown strategy '{strategy}'. Choose 'equalize' or 'boost'.")

        if count >= target:
            report["augmented_groups"][str(group_value)] = {
                "status": "already_sufficient",
                "original": int(count),
                "target": target,
            }
            continue

        augmented_df, fidelity = augment_dataset(
            augmented_df, sensitive_col, str(group_value),
            target_count=target, epochs=epochs,
        )

        report["augmented_groups"][str(group_value)] = {
            "status": "augmented",
            "original": int(count),
            "target": target,
            "synthetic_added": target - int(count),
            "fidelity": fidelity,
        }

    report["final_distribution"] = augmented_df[sensitive_col].value_counts().to_dict()
    report["final_row_count"] = len(augmented_df)

    return augmented_df, report
