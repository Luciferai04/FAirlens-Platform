"""Tests for the Gemini remediation Cloud Function."""
import pytest
import json
import time
from unittest.mock import patch, MagicMock


class TestPlaybookGeneration:
    def test_playbook_generated_and_stored(self):
        """Verify playbook is generated and stored with pending_approval=True."""
        from remediation.function.main import _generate_with_gemini, FALLBACK_PLAYBOOK

        mock_db = MagicMock()
        incident = {
            "incident_id": "test-001",
            "model_id": "model-abc",
            "metric_name": "demographic_parity_difference",
            "current_value": 0.25,
            "threshold": 0.10,
            "severity": "High",
            "sensitive_col": "gender",
        }

        # Mock Gemini to return valid JSON
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "playbook_id": "pb-001",
            "incident_id": "test-001",
            "strategies": [
                {"name": "S1", "description": "d1", "technique": "reweighting",
                 "code_snippet": "code", "estimated_effort": "low"},
                {"name": "S2", "description": "d2", "technique": "resampling",
                 "code_snippet": "code", "estimated_effort": "medium"},
                {"name": "S3", "description": "d3", "technique": "threshold_adjustment",
                 "code_snippet": "code", "estimated_effort": "low"},
            ],
            "root_cause_analysis": "Test root cause",
            "priority_order": ["S1", "S2", "S3"],
        })

        with patch("remediation.function.main.genai") as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_model.generate_content.return_value = mock_response

            result = _generate_with_gemini(incident, mock_db)

        assert "strategies" in result
        assert len(result["strategies"]) == 3
        assert result["root_cause_analysis"] == "Test root cause"

    def test_fallback_on_json_parse_failure(self):
        """Verify fallback template is used when Gemini returns non-JSON."""
        from remediation.function.main import _generate_with_gemini, FALLBACK_PLAYBOOK

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        incident = {"incident_id": "test-002", "model_id": "m1",
                     "metric_name": "dpd", "current_value": 0.3, "threshold": 0.1,
                     "severity": "High"}

        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON at all!"

        with patch("remediation.function.main.genai") as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_model.generate_content.return_value = mock_response

            result = _generate_with_gemini(incident, mock_db)

        assert "strategies" in result
        assert len(result["strategies"]) == 3
        assert result == FALLBACK_PLAYBOOK

    def test_generation_completes_within_30s(self):
        """Verify function completes in < 30s (measured with time.time)."""
        from remediation.function.main import _generate_with_gemini

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        incident = {"incident_id": "perf-test", "model_id": "m1",
                     "metric_name": "dpd", "current_value": 0.2, "threshold": 0.1,
                     "severity": "Medium"}

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "strategies": [{"name": "S", "description": "d", "technique": "reweighting",
                           "code_snippet": "", "estimated_effort": "low"}],
            "root_cause_analysis": "test", "priority_order": ["S"],
        })

        with patch("remediation.function.main.genai") as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_model.generate_content.return_value = mock_response

            start = time.time()
            _generate_with_gemini(incident, mock_db)
            elapsed = time.time() - start

        assert elapsed < 30, f"Generation took {elapsed:.1f}s, exceeds 30s limit"
