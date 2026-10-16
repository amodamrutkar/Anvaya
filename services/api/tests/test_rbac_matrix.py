"""
tests/test_rbac_matrix.py
Comprehensive RBAC permission matrix tests verifying that each role
can access only permitted endpoints and is strictly forbidden from unauthorized ones.
"""
import pytest
from sutradhar_api.store import get_store


@pytest.mark.asyncio
async def test_rbac_matrix(client):
    store = get_store()
    comm_id = next(iter(store.communities))
    eid = next(iter(store.entities))

    # AUDITOR permissions
    # Permitted: /audit, /audit/verify
    r = await client.get("/audit", headers={"X-Demo-User": "auditor1"})
    assert r.status_code == 200
    r = await client.get("/audit/verify", headers={"X-Demo-User": "auditor1"})
    assert r.status_code == 200

    # Forbidden for AUDITOR: /entities/search, /dossier/generate, /federated/query
    r = await client.get("/entities/search?q=test", headers={"X-Demo-User": "auditor1"})
    assert r.status_code == 403
    r = await client.post("/dossier/generate", json={"community_id": comm_id}, headers={"X-Demo-User": "auditor1"})
    assert r.status_code == 403

    # ANALYST permissions
    # Permitted: /entities/search, /graph/communities, /review-queue, /dossier/generate
    r = await client.get("/entities/search?q=rakesh", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    r = await client.get("/graph/communities", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    r = await client.get("/review-queue", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200

    # Forbidden for ANALYST: /audit (audit log view), /dossier/{id}/export
    r = await client.get("/audit", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 403
    r = await client.post("/dossier/DOS-001/export", json={"confirm": True, "export_format": "JSON"}, headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 403

    # APPROVING_OFFICER permissions
    # Permitted: /dossier/generate, /dossier/{id}/export (with confirm)
    r = await client.post("/dossier/generate", json={"community_id": comm_id}, headers={"X-Demo-User": "officer1"})
    assert r.status_code == 200
    dos_id = r.json()["dossier_id"]
    r = await client.post(f"/dossier/{dos_id}/export", json={"confirm": True, "export_format": "JSON"}, headers={"X-Demo-User": "officer1"})
    assert r.status_code == 200

    # Forbidden for APPROVING_OFFICER: /audit
    r = await client.get("/audit", headers={"X-Demo-User": "officer1"})
    assert r.status_code == 403
