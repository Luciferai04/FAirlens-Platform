"""Tests for all API routers with mocked BigQuery responses."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
import os

os.environ["FAIRLENS_DEV_MODE"] = "true"
os.environ["GCP_PROJECT_ID"] = "test-project"

from console.backend.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "fairlens-api"


@pytest.mark.asyncio
async def test_list_models(client):
    mock_row = MagicMock()
    mock_row.__iter__ = lambda s: iter(
        [("model_id", "m1"), ("last_audited", None), ("currently_passing", True), ("total_audits", 5)]
    )
    mock_row.keys = lambda: ["model_id", "last_audited", "currently_passing", "total_audits"]
    mock_row.__getitem__ = lambda s, k: {"model_id": "m1", "last_audited": None, "currently_passing": True, "total_audits": 5}[k]

    with patch("console.backend.routers.models.bigquery") as mock_bq:
        mock_client = MagicMock()
        mock_bq.Client.return_value = mock_client
        mock_result = MagicMock()
        mock_result.result.return_value = []
        mock_client.query.return_value = mock_result

        resp = await client.get("/v1/models/")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_audit_not_found(client):
    with patch("console.backend.routers.models.bigquery") as mock_bq:
        mock_client = MagicMock()
        mock_bq.Client.return_value = mock_client
        mock_bq.QueryJobConfig = MagicMock()
        mock_bq.ScalarQueryParameter = MagicMock()
        mock_result = MagicMock()
        mock_result.result.return_value = []
        mock_client.query.return_value = mock_result

        resp = await client.get("/v1/models/nonexistent/audit")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_incidents(client):
    with patch("console.backend.routers.incidents.bigquery") as mock_bq:
        mock_client = MagicMock()
        mock_bq.Client.return_value = mock_client
        mock_bq.QueryJobConfig = MagicMock()
        mock_bq.ScalarQueryParameter = MagicMock()
        mock_result = MagicMock()
        mock_result.result.return_value = []
        mock_client.query.return_value = mock_result

        resp = await client.get("/v1/incidents/")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_compliance_report(client):
    resp = await client.get("/v1/reports/compliance?framework=eu_ai_act&model_id=test-model")
    assert resp.status_code == 200
    data = resp.json()
    assert data["framework"] == "eu_ai_act"
    assert len(data["sections"]) > 0


@pytest.mark.asyncio
async def test_compliance_invalid_framework(client):
    resp = await client.get("/v1/reports/compliance?framework=invalid&model_id=test")
    assert resp.status_code == 400
