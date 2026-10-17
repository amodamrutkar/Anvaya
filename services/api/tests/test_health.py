"""
tests/test_health.py
Tests for GET /health, GET /me, GET /metrics, and GET /connectors/status.
"""
import pytest


@pytest.mark.asyncio
async def test_health_ok(client):
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["simulated"] is True


@pytest.mark.asyncio
async def test_me_ok(client):
    r = await client.get("/me", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == "analyst1"
    assert body["role"] == "ANALYST"


@pytest.mark.asyncio
async def test_me_no_auth(client):
    r = await client.get("/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_unknown_user(client):
    r = await client.get("/me", headers={"X-Demo-User": "does-not-exist"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_metrics(client):
    r = await client.get("/metrics", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_connectors_status(client):
    r = await client.get("/connectors/status", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    for connector in body:
        assert connector["simulated"] is True
