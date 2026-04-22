"""Tests for the synthetic data debiaser (D8)."""
from __future__ import annotations
import pytest
import json
import os
import tempfile
import numpy as np
import pandas as pd


def _make_imbalanced_df(n=500):
    """Create a dataset with known gender imbalance: 80% male, 20% female."""
    rng = np.random.RandomState(42)
    n_male = int(n * 0.8)
    n_female = n - n_male
    df = pd.DataFrame({
        "years_experience": np.concatenate([
            rng.poisson(7, n_male), rng.poisson(5, n_female)
        ]),
        "education_level": np.concatenate([
            rng.choice([1, 2, 3, 4], n_male), rng.choice([1, 2, 3, 4], n_female)
        ]),
        "skill_score": np.concatenate([
            rng.normal(72, 10, n_male), rng.normal(70, 12, n_female)
        ]).round(1),
        "gender": ["male"] * n_male + ["female"] * n_female,
        "hired": np.concatenate([
            rng.binomial(1, 0.6, n_male), rng.binomial(1, 0.4, n_female)
        ]),
    })
    return df


class TestAugmentDataset:
    """augment_dataset() generates synthetic rows for underrepresented group."""

    def test_augmentation_increases_group_count(self):
        from debiaser.ctgan_trainer import augment_dataset
        df = _make_imbalanced_df(200)
        original_female = (df["gender"] == "female").sum()
        target = original_female + 50

        augmented, fidelity = augment_dataset(
            df, "gender", "female", target_count=target, epochs=1
        )

        new_female = (augmented["gender"] == "female").sum()
        assert new_female >= target, f"Expected >= {target} females, got {new_female}"
        assert len(augmented) > len(df)

    def test_no_augmentation_when_already_sufficient(self):
        from debiaser.ctgan_trainer import augment_dataset
        df = _make_imbalanced_df(200)
        original_male = (df["gender"] == "male").sum()

        augmented, fidelity = augment_dataset(
            df, "gender", "male", target_count=original_male - 10, epochs=1
        )
        assert len(augmented) == len(df)
        assert fidelity.get("status") == "no_augmentation_needed"

    def test_synthetic_rows_have_correct_group_label(self):
        from debiaser.ctgan_trainer import augment_dataset
        df = _make_imbalanced_df(200)
        original_count = len(df)

        augmented, _ = augment_dataset(
            df, "gender", "female", target_count=100, epochs=1
        )
        # All new rows should have gender == "female"
        new_rows = augmented.iloc[original_count:]
        if len(new_rows) > 0:
            assert (new_rows["gender"] == "female").all()


class TestDistributionFidelity:
    """check_distribution_fidelity() compares original vs synthetic distributions."""

    def test_fidelity_report_has_expected_keys(self):
        from debiaser.ctgan_trainer import check_distribution_fidelity
        rng = np.random.RandomState(42)
        original = pd.DataFrame({
            "age": rng.normal(35, 10, 100),
            "score": rng.normal(70, 15, 100),
        })
        synthetic = pd.DataFrame({
            "age": rng.normal(35, 10, 50),
            "score": rng.normal(70, 15, 50),
        })
        report = check_distribution_fidelity(original, synthetic)

        assert "age" in report
        assert "score" in report
        assert "mean_drift_pct" in report["age"]
        assert "ks_statistic" in report["age"]
        assert "pass" in report["age"]

    def test_identical_distributions_pass(self):
        from debiaser.ctgan_trainer import check_distribution_fidelity
        rng = np.random.RandomState(42)
        data = pd.DataFrame({"x": rng.normal(50, 10, 500)})
        report = check_distribution_fidelity(data, data)
        assert report["x"]["mean_drift_pct"] == 0.0
        assert report["x"]["pass"] == True


class TestBootstrapFallback:
    """_BootstrapSynthesizer works when ctgan is not installed."""

    def test_bootstrap_generates_correct_count(self):
        from debiaser.ctgan_trainer import _BootstrapSynthesizer
        df = pd.DataFrame({
            "a": np.random.randn(50),
            "b": np.random.choice(["x", "y"], 50),
        })
        synth = _BootstrapSynthesizer(df)
        result = synth.sample(30)
        assert len(result) == 30
        assert set(result.columns) == set(df.columns)


class TestAugmentUnderrepresented:
    """augment_underrepresented() equalizes all minority groups."""

    def test_equalize_strategy(self):
        from debiaser.augment import augment_underrepresented
        df = _make_imbalanced_df(200)
        original_counts = df["gender"].value_counts()

        augmented, report = augment_underrepresented(
            df, "gender", strategy="equalize", epochs=1
        )

        new_counts = augmented["gender"].value_counts()
        # After equalization, minority group should match majority
        assert new_counts.min() >= original_counts.max() - 5  # Allow small rounding
        assert report["majority_group"] == "male"
        assert "female" in report["augmented_groups"]


class TestProvenance:
    """write_provenance_metadata() creates valid JSON sidecar."""

    def test_provenance_local_write(self):
        from debiaser.provenance import write_provenance_metadata
        with tempfile.NamedTemporaryFile(suffix="_provenance.json", delete=False) as f:
            path = f.name
        try:
            result = write_provenance_metadata(
                input_gcs="gs://bucket/input.csv",
                output_gcs="gs://bucket/output.csv",
                original_count=1000,
                synthetic_count=200,
                target_group="female",
                fidelity_report={"age": {"mean_drift_pct": 2.5, "pass": True}},
                local_path=path,
            )
            assert os.path.exists(path)
            with open(path) as f:
                loaded = json.load(f)
            assert loaded["lineage"]["original_row_count"] == 1000
            assert loaded["lineage"]["synthetic_row_count"] == 200
            assert loaded["lineage"]["target_group"] == "female"
            assert "provenance" in loaded
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_high_ratio_warning(self):
        from debiaser.provenance import write_provenance_metadata
        result = write_provenance_metadata(
            input_gcs="gs://b/i.csv", output_gcs="gs://b/o.csv",
            original_count=100, synthetic_count=200,
            target_group="female",
            fidelity_report={},
            local_path="/dev/null",
        )
        assert any("High augmentation ratio" in w for w in result["warnings"])
