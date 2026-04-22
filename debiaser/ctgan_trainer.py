"""
CTGAN-based synthetic data augmentation for underrepresented groups.
Can run as a standalone script (Vertex AI custom training job) or be
imported as a library for local use.

Usage (CLI — Vertex AI):
    python -m debiaser.ctgan_trainer \
        --input-gcs gs://bucket/data.csv \
        --output-gcs gs://bucket/augmented.csv \
        --sensitive-col gender \
        --target-group female \
        --target-count 500 \
        --epochs 300

Usage (Library):
    from debiaser.ctgan_trainer import augment_dataset
    augmented = augment_dataset(df, "gender", "female", target_count=500)
"""
from __future__ import annotations
import argparse
import json
import os
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd


def train_ctgan(
    df: pd.DataFrame,
    discrete_columns: list[str] | None = None,
    epochs: int = 300,
    batch_size: int = 500,
) -> object:
    """
    Train a CTGAN model on the provided DataFrame.

    Args:
        df: Training data
        discrete_columns: Columns to treat as categorical
        epochs: Number of training epochs
        batch_size: Training batch size

    Returns:
        Trained CTGAN model (or a SimpleSynthesizer fallback)
    """
    if discrete_columns is None:
        discrete_columns = _infer_discrete_columns(df)

    try:
        from ctgan import CTGAN
        model = CTGAN(epochs=epochs, batch_size=batch_size, verbose=True)
        model.fit(df, discrete_columns=discrete_columns)
        return model
    except ImportError:
        print("[Debiaser] ctgan not installed — using bootstrap fallback synthesizer")
        return _BootstrapSynthesizer(df)


def augment_dataset(
    df: pd.DataFrame,
    sensitive_col: str,
    target_group: str,
    target_count: int,
    epochs: int = 300,
    fidelity_check: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """
    Augment a dataset by generating synthetic rows for an underrepresented group.

    Args:
        df: Original dataset
        sensitive_col: Protected attribute column name
        target_group: Value of the underrepresented group to augment
        target_count: Desired total count for the target group
        epochs: CTGAN training epochs
        fidelity_check: Whether to validate distribution fidelity

    Returns:
        (augmented_df, fidelity_report)
    """
    original_count = len(df)
    group_mask = df[sensitive_col] == target_group
    original_group_count = group_mask.sum()

    print(f"[Debiaser] Original: {original_count} rows, "
          f"{original_group_count} in target group '{target_group}'")

    n_to_generate = target_count - original_group_count
    if n_to_generate <= 0:
        print("[Debiaser] Group already meets target count. No augmentation needed.")
        return df, {"status": "no_augmentation_needed"}

    # Train on the target group subset only
    target_df = df[group_mask].reset_index(drop=True)
    model = train_ctgan(target_df, epochs=epochs)

    # Generate synthetic rows
    if hasattr(model, 'sample'):
        synthetic = model.sample(n_to_generate)
    else:
        synthetic = model.generate(n_to_generate)

    # Enforce the group label in case CTGAN drifts
    synthetic[sensitive_col] = target_group

    augmented_df = pd.concat([df, synthetic], ignore_index=True)
    print(f"[Debiaser] Generated {n_to_generate} synthetic rows.")
    print(f"[Debiaser] Augmented dataset: {len(augmented_df)} rows total.")

    fidelity_report = {}
    if fidelity_check:
        fidelity_report = check_distribution_fidelity(target_df, synthetic)
        print(f"[Debiaser] Distribution fidelity: {json.dumps(fidelity_report, indent=2)}")

    return augmented_df, fidelity_report


def check_distribution_fidelity(
    original: pd.DataFrame,
    synthetic: pd.DataFrame,
) -> dict:
    """
    Compare mean and std of numeric columns between original and synthetic.

    Returns:
        Dict mapping column -> {mean_drift_pct, std_drift_pct, ks_statistic}
    """
    from scipy import stats

    numeric_cols = original.select_dtypes("number").columns
    fidelity = {}

    for col in numeric_cols:
        if col not in synthetic.columns:
            continue
        orig_mean = original[col].mean()
        synth_mean = synthetic[col].mean()
        orig_std = original[col].std()
        synth_std = synthetic[col].std()

        mean_drift = abs(orig_mean - synth_mean) / (abs(orig_mean) + 1e-9)
        std_drift = abs(orig_std - synth_std) / (abs(orig_std) + 1e-9)

        # Kolmogorov-Smirnov test for distribution similarity
        try:
            ks_stat, ks_pval = stats.ks_2samp(
                original[col].dropna().values,
                synthetic[col].dropna().values,
            )
        except Exception:
            ks_stat, ks_pval = float("nan"), float("nan")

        fidelity[col] = {
            "mean_drift_pct": round(mean_drift * 100, 2),
            "std_drift_pct": round(std_drift * 100, 2),
            "ks_statistic": round(ks_stat, 4),
            "ks_pvalue": round(ks_pval, 4),
            "pass": bool(ks_pval > 0.05) if not np.isnan(ks_pval) else False,
        }

    return fidelity


class _BootstrapSynthesizer:
    """
    Fallback synthesizer when ctgan is not installed.
    Uses bootstrap resampling + Gaussian noise for numeric columns.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.numeric_cols = df.select_dtypes("number").columns.tolist()
        self.cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    def sample(self, n: int) -> pd.DataFrame:
        return self.generate(n)

    def generate(self, n: int) -> pd.DataFrame:
        # Bootstrap sample
        synthetic = self.df.sample(n=n, replace=True).reset_index(drop=True)

        # Add Gaussian noise to numeric columns for diversity
        for col in self.numeric_cols:
            std = self.df[col].std()
            noise = np.random.normal(0, std * 0.05, n)
            synthetic[col] = synthetic[col] + noise

        return synthetic


def _infer_discrete_columns(df: pd.DataFrame) -> list[str]:
    """Infer which columns should be treated as discrete by CTGAN."""
    return [c for c in df.columns
            if df[c].dtype == object or df[c].nunique() < 20]


# ─── CLI Entry Point (Vertex AI Custom Training Job) ─────────────────
def main():
    parser = argparse.ArgumentParser(description="FairLens CTGAN Debiaser")
    parser.add_argument("--input-gcs", required=True,
                        help="GCS path to input CSV")
    parser.add_argument("--output-gcs", required=True,
                        help="GCS path for augmented output CSV")
    parser.add_argument("--sensitive-col", required=True,
                        help="Protected attribute column name")
    parser.add_argument("--target-group", required=True,
                        help="Group value to augment (underrepresented)")
    parser.add_argument("--target-count", type=int, required=True,
                        help="Target row count for the group after augmentation")
    parser.add_argument("--epochs", type=int, default=300)
    args = parser.parse_args()

    print(f"[Debiaser] Loading dataset from {args.input_gcs}")
    df = _load_from_gcs(args.input_gcs)

    augmented_df, fidelity = augment_dataset(
        df, args.sensitive_col, args.target_group,
        args.target_count, epochs=args.epochs,
    )

    _save_to_gcs(augmented_df, args.output_gcs)

    from .provenance import write_provenance_metadata
    write_provenance_metadata(
        input_gcs=args.input_gcs,
        output_gcs=args.output_gcs,
        original_count=len(df),
        synthetic_count=args.target_count - (df[args.sensitive_col] == args.target_group).sum(),
        target_group=args.target_group,
        fidelity_report=fidelity,
    )
    print(f"[Debiaser] Done. Output written to {args.output_gcs}")


def _load_from_gcs(gcs_path: str) -> pd.DataFrame:
    import io
    from google.cloud import storage
    client = storage.Client()
    bucket_name, blob_name = gcs_path.replace("gs://", "").split("/", 1)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return pd.read_csv(io.BytesIO(blob.download_as_bytes()))


def _save_to_gcs(df: pd.DataFrame, gcs_path: str):
    import io
    from google.cloud import storage
    client = storage.Client()
    bucket_name, blob_name = gcs_path.replace("gs://", "").split("/", 1)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    blob.upload_from_string(buf.getvalue(), content_type="text/csv")


if __name__ == "__main__":
    main()
