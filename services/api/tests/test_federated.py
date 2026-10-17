"""
tests/test_federated.py
Tests for cross-agency federated query, purpose & case_ref validation,
zero-data leakage guarantees, and agency inbox.
"""
import pytest


@pytest.mark.asyncio
async def test_federated_query_match_no_leak(client):
    payload = {
        "querying_agency": "STATE_POLICE",
        "purpose": "INVESTIGATION",
        "case_ref": "CASE-MUM-2026-004512",
        "identifier_type": "PHONE",
        "identifier_value": "9000012345",
    }
    r = await client.post("/federated/query", json=payload, headers={"X-Demo-User": "inspector1"})
    assert r.status_code == 200
    data = r.json()

    # Required fields
    assert "query_id" in data
    assert data["result"] in ("MATCH", "NO_MATCH", "MAYBE")
    assert "reason_code" in data
    assert "reason_text" in data
    assert "confidence" in data
    assert "owning_agency_notified" in data
    assert "audit_seq" in data

    # Zero-data leakage assertions:
    # Must NOT return raw records, entity names, suspect dossiers, or identifiers
    forbidden_keys = {"records", "raw_data", "suspect_name", "first_name", "last_name", "name", "address", "fir_id"}
    for k in forbidden_keys:
        assert k not in data, f"Leaked forbidden key '{k}' in federated response!"

    # Ensure no raw personal name appears in reason_text
    assert "Rakesh" not in data["reason_text"]
    assert "Pawar" not in data["reason_text"]


@pytest.mark.asyncio
async def test_federated_query_forbidden_for_auditor(client):
    payload = {
        "querying_agency": "STATE_POLICE",
        "purpose": "INVESTIGATION",
        "case_ref": "CASE-MUM-2026-004512",
        "identifier_type": "PHONE",
        "identifier_value": "9000012345",
    }
    r = await client.post("/federated/query", json=payload, headers={"X-Demo-User": "auditor1"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_federated_query_invalid_case_ref(client):
    payload = {
        "querying_agency": "STATE_POLICE",
        "purpose": "INVESTIGATION",
        "case_ref": "bad-ref",
        "identifier_type": "PHONE",
        "identifier_value": "9000012345",
    }
    r = await client.post("/federated/query", json=payload, headers={"X-Demo-User": "inspector1"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_agency_inbox(client):
    r = await client.get("/agency/MAHA_CYBER/inbox", headers={"X-Demo-User": "liaison1"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
