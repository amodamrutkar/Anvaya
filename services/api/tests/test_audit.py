"""
tests/test_audit.py
Tests for append-only audit log, hash chain verification, tamper detection, and repair.
"""

import pytest

from sutradhar_api.store import get_store


@pytest.mark.asyncio
async def test_audit_log_access_auditor(client):
    r = await client.get("/audit", headers={"X-Demo-User": "auditor1"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_audit_log_forbidden_for_analyst(client):
    r = await client.get("/audit", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_audit_chain_valid_initially(client):
    r = await client.get("/audit/verify", headers={"X-Demo-User": "auditor1"})
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["broken_at"] is None


@pytest.mark.asyncio
async def test_audit_tamper_and_repair(client, monkeypatch):
    import sutradhar_api.routers.audit as audit_router

    monkeypatch.setattr(audit_router, "DEMO_TAMPER", True)

    store = get_store()
    # Ensure there are at least two entries
    store.record_audit("test_user", "ANALYST", "TEST_ACTION_1", "Test summary 1")
    store.record_audit("test_user", "ANALYST", "TEST_ACTION_2", "Test summary 2")

    # Tamper
    r_tamper = await client.post("/audit/dev/tamper", headers={"X-Demo-User": "auditor1"})
    assert r_tamper.status_code == 200
    assert r_tamper.json()["tampered_seq"] == 2

    # Verify should now fail and detect broken_at == 2
    r_verify = await client.get("/audit/verify", headers={"X-Demo-User": "auditor1"})
    assert r_verify.status_code == 200
    body_verify = r_verify.json()
    assert body_verify["valid"] is False
    assert body_verify["broken_at"] == 2

    # Repair
    r_repair = await client.post("/audit/dev/repair", headers={"X-Demo-User": "auditor1"})
    assert r_repair.status_code == 200
    assert r_repair.json()["repaired_seq"] == 2

    # Verify should now be valid again
    r_verify_repaired = await client.get("/audit/verify", headers={"X-Demo-User": "auditor1"})
    assert r_verify_repaired.status_code == 200
    assert r_verify_repaired.json()["valid"] is True
