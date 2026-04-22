"""Tests for compliance report generator."""
from __future__ import annotations
import pytest
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk"))


def _make_mock_report():
    """Create a mock AuditReport for testing."""
    import fairlens
    import numpy as np
    import pandas as pd
    from unittest.mock import MagicMock

    model = MagicMock()
    model.predict = lambda X: (X["gender"] == "male").astype(int).values
    X = pd.DataFrame({
        "feature": np.random.randn(200),
        "gender": ["male"] * 100 + ["female"] * 100,
    })
    y = pd.Series(np.random.randint(0, 2, 200))
    return fairlens.audit(model, X, y, ["gender"], model_id="test-model")


class TestComplianceGenerator:
    def test_eu_ai_act_pdf_generated(self):
        from compliance.generator import generate_from_audit
        report = _make_mock_report()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            sha = generate_from_audit(report, "eu_ai_act", path, sign=False)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 100
            assert len(sha) == 64  # SHA-256 hex digest
        finally:
            os.unlink(path)
            hash_path = path.replace(".pdf", ".sha256")
            if os.path.exists(hash_path):
                os.unlink(hash_path)

    def test_eeoc_pdf_generated(self):
        from compliance.generator import generate_from_audit
        report = _make_mock_report()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            sha = generate_from_audit(report, "eeoc", path, sign=False)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 100
        finally:
            os.unlink(path)
            hash_path = path.replace(".pdf", ".sha256")
            if os.path.exists(hash_path):
                os.unlink(hash_path)

    def test_pdf_contains_expected_text(self):
        from compliance.generator import generate_from_audit
        report = _make_mock_report()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            generate_from_audit(report, "eu_ai_act", path, sign=False)
            try:
                from pypdf import PdfReader
            except ImportError:
                from PyPDF2 import PdfReader
            reader = PdfReader(path)
            all_text = ""
            for page in reader.pages:
                all_text += page.extract_text() or ""
            assert "FairLens" in all_text
            assert "test-model" in all_text
        finally:
            os.unlink(path)
            hash_path = path.replace(".pdf", ".sha256")
            if os.path.exists(hash_path):
                os.unlink(hash_path)

    def test_invalid_framework_raises(self):
        from compliance.generator import generate_from_audit
        report = _make_mock_report()
        with pytest.raises(ValueError, match="Unknown framework"):
            generate_from_audit(report, "invalid_framework", "/tmp/test.pdf")

    def test_sha256_hash_file_created(self):
        from compliance.generator import generate_from_audit
        report = _make_mock_report()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            generate_from_audit(report, "eu_ai_act", path, sign=False)
            hash_path = path.replace(".pdf", ".sha256")
            assert os.path.exists(hash_path)
            with open(hash_path) as hf:
                stored_hash = hf.read().strip()
            assert len(stored_hash) == 64
        finally:
            os.unlink(path)
            if os.path.exists(hash_path):
                os.unlink(hash_path)


class TestComplianceSigner:
    def test_sign_without_kms_returns_unsigned(self):
        from compliance.signer import sign_pdf
        from compliance.generator import generate_from_audit
        report = _make_mock_report()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            generate_from_audit(report, "eu_ai_act", path, sign=False)
            pdf_bytes, sig_hex, sha256 = sign_pdf(path)
            assert isinstance(pdf_bytes, bytes)
            assert len(sha256) == 64
            assert sig_hex.startswith("unsigned-")
        finally:
            os.unlink(path)
            hash_path = path.replace(".pdf", ".sha256")
            if os.path.exists(hash_path):
                os.unlink(hash_path)

    def test_verify_unsigned(self):
        from compliance.signer import sign_pdf, verify
        from compliance.generator import generate_from_audit
        report = _make_mock_report()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            generate_from_audit(report, "eu_ai_act", path, sign=False)
            pdf_bytes, sig_hex, sha256 = sign_pdf(path)
            result = verify(pdf_bytes, sig_hex)
            assert result == True
        finally:
            os.unlink(path)
            hash_path = path.replace(".pdf", ".sha256")
            if os.path.exists(hash_path):
                os.unlink(hash_path)
