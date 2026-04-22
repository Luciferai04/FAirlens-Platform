"""
Provenance metadata tracking for synthetic data augmentation.
Writes a JSON sidecar file alongside the augmented dataset documenting
the transformation lineage, fidelity metrics, and generation parameters.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone


def write_provenance_metadata(
    input_gcs: str,
    output_gcs: str,
    original_count: int,
    synthetic_count: int,
    target_group: str,
    fidelity_report: dict,
    method: str = "CTGAN",
    local_path: str | None = None,
) -> dict:
    """
    Write provenance metadata as a JSON sidecar.

    Args:
        input_gcs: Source dataset path
        output_gcs: Augmented dataset path
        original_count: Row count before augmentation
        synthetic_count: Number of synthetic rows generated
        target_group: The underrepresented group that was augmented
        fidelity_report: Distribution fidelity check results
        method: Synthesis method used
        local_path: Optional local path to write the sidecar

    Returns:
        The provenance metadata dict
    """
    metadata = {
        "provenance": {
            "tool": "FairLens Debiaser",
            "version": "1.0.0",
            "method": method,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "lineage": {
            "input_dataset": input_gcs,
            "output_dataset": output_gcs,
            "original_row_count": original_count,
            "synthetic_row_count": synthetic_count,
            "augmented_row_count": original_count + synthetic_count,
            "target_group": target_group,
            "augmentation_ratio": round(
                synthetic_count / max(original_count, 1), 4
            ),
        },
        "fidelity": fidelity_report,
        "warnings": _generate_warnings(fidelity_report, synthetic_count, original_count),
    }

    # Write locally
    if local_path:
        sidecar_path = local_path
    else:
        sidecar_path = output_gcs.replace(".csv", "_provenance.json") if output_gcs else None

    if sidecar_path and not sidecar_path.startswith("gs://"):
        os.makedirs(os.path.dirname(sidecar_path) or ".", exist_ok=True)
        with open(sidecar_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"[Provenance] Metadata written to {sidecar_path}")
    elif sidecar_path and sidecar_path.startswith("gs://"):
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket_name, blob_name = sidecar_path.replace("gs://", "").split("/", 1)
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(
                json.dumps(metadata, indent=2),
                content_type="application/json",
            )
            print(f"[Provenance] Metadata written to {sidecar_path}")
        except ImportError:
            print("[Provenance] google-cloud-storage not available. Metadata not uploaded.")

    return metadata


def _generate_warnings(fidelity: dict, synthetic_count: int, original_count: int) -> list[str]:
    """Generate warnings based on fidelity and augmentation ratio."""
    warnings = []

    ratio = synthetic_count / max(original_count, 1)
    if ratio > 0.5:
        warnings.append(
            f"High augmentation ratio ({ratio:.1%}). "
            "Synthetic data exceeds 50% of original — model may overfit to generated patterns."
        )

    for col, metrics in fidelity.items():
        if isinstance(metrics, dict):
            drift = metrics.get("mean_drift_pct", 0)
            if drift > 10:
                warnings.append(
                    f"Column '{col}' shows {drift:.1f}% mean drift between "
                    "original and synthetic distributions."
                )
            ks_pass = metrics.get("pass", True)
            if not ks_pass:
                warnings.append(
                    f"Column '{col}' fails KS test (p < 0.05) — "
                    "synthetic distribution significantly differs from original."
                )

    return warnings
