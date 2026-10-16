"""
tests/test_api_smoke.py
End-to-end demo walk smoke tests covering all core user journeys.
"""
import pytest
from sutradhar_api.store import get_store


@pytest.mark.asyncio
async def test_full_demo_walk(client):
    # 1. System health and info
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["simulated"] is True

    r = await client.get("/me", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    assert r.json()["user_id"] == "analyst1"

    r = await client.get("/metrics", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200

    r = await client.get("/connectors/status", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    assert len(r.json()) >= 4

    # 2. Search & Entity view
    r = await client.get("/entities/search?q=rakesh", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    results = r.json()
    assert len(results) > 0
    eid = results[0]["entity_id"]

    r = await client.get(f"/entities/{eid}", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200

    r = await client.get(f"/entities/{eid}/links", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200

    # 3. Graph analytics
    r = await client.get("/graph/communities", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    comms = r.json()
    assert len(comms) > 0
    cid = comms[0]["community_id"]

    r = await client.get(f"/graph/communities/{cid}", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200

    r = await client.get(f"/graph/entity/{eid}/neighborhood", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200

    r = await client.get("/roles", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200

    r = await client.get("/bridges", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200

    r = await client.get("/mule/chains", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200

    # 4. Review Queue
    r = await client.get("/review-queue", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200

    # 5. Dossier lifecycle
    r = await client.post("/dossier/generate", json={"community_id": cid}, headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    dos_id = r.json()["dossier_id"]

    r = await client.get(f"/dossier/{dos_id}", headers={"X-Demo-User": "officer1"})
    assert r.status_code == 200

    r = await client.post(f"/dossier/{dos_id}/export", json={"confirm": True, "export_format": "JSON"}, headers={"X-Demo-User": "officer1"})
    assert r.status_code == 200

    # 6. Federated query
    r = await client.post(
        "/federated/query",
        json={
            "querying_agency": "STATE_POLICE",
            "purpose": "INVESTIGATION",
            "case_ref": "CASE-MUM-2026-004512",
            "identifier_type": "PHONE",
            "identifier_value": "9000012345",
        },
        headers={"X-Demo-User": "inspector1"},
    )
    assert r.status_code == 200
    assert r.json()["result"] in ("MATCH", "NO_MATCH", "MAYBE")

    # 7. Audit verification
    r = await client.get("/audit/verify", headers={"X-Demo-User": "auditor1"})
    assert r.status_code == 200
    assert r.json()["valid"] is True

    # 8. Kumbh simulation
    r = await client.get("/kumbh/zones", headers={"X-Demo-User": "inspector1"})
    assert r.status_code == 200

    r = await client.post("/kumbh/simulate/next", headers={"X-Demo-User": "inspector1"})
    assert r.status_code == 200
