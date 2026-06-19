"""API authentication regression tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


def make_client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


@pytest.mark.asyncio
async def test_root_endpoint_remains_public(monkeypatch):
    monkeypatch.setattr(settings, "RAILMIND_API_KEY", "")

    async with make_client() as client:
        response = await client.get("/")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_routes_fail_closed_when_auth_is_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "RAILMIND_API_KEY", "")

    async with make_client() as client:
        response = await client.get("/api/health")

    assert response.status_code == 503


@pytest.mark.asyncio
async def test_api_routes_reject_missing_or_invalid_api_key(monkeypatch):
    monkeypatch.setattr(settings, "RAILMIND_API_KEY", "test-secret")

    async with make_client() as client:
        missing = await client.get("/api/health")
        invalid = await client.get("/api/health", headers={"X-API-Key": "wrong"})

    assert missing.status_code == 401
    assert invalid.status_code == 401


@pytest.mark.asyncio
async def test_api_routes_accept_configured_api_key(monkeypatch):
    monkeypatch.setattr(settings, "RAILMIND_API_KEY", "test-secret")

    async with make_client() as client:
        response = await client.get("/api/health", headers={"X-API-Key": "test-secret"})

    assert response.status_code == 200
    assert response.json()["status"] == "online"
