"""
tests/test_dossier.py
Tests for draft dossier generation, viewing, and confirm-gated export.
"""
import pytest
from sutradhar_api.store import get_store


@pytest.mark.asyncio
async def test_dossier_lifecycle(client):
    store = get_store()
    comm_id = next(iter(store.communities))

    # 1. Generate dossier as analyst
    r_gen = await client.post(
        "/dossier/generate",
        json={"community_id": comm_id},
        headers={"X-Demo-User": "analyst1"},
    )
    assert r_gen.status_code == 200
    dos_data = r_gen.json()
    dossier_id = dos_data["dossier_id"]
    assert "audit_seq" in dos_data
    assert "sections" in dos_data

    # 2. View dossier
    r_view = await client.get(f"/dossier/{dossier_id}", headers={"X-Demo-User": "officer1"})
    assert r_view.status_code == 200
    assert r_view.json()["dossier_id"] == dossier_id

    # 3. Export without confirm fails with 422
    r_unconf = await client.post(
        f"/dossier/{dossier_id}/export",
        json={"confirm": False, "export_format": "JSON"},
        headers={"X-Demo-User": "officer1"},
    )
    assert r_unconf.status_code == 422

    # 4. Export by analyst (not APPROVING_OFFICER) fails with 403
    r_analyst = await client.post(
        f"/dossier/{dossier_id}/export",
        json={"confirm": True, "export_format": "JSON"},
        headers={"X-Demo-User": "analyst1"},
    )
    assert r_analyst.status_code == 403

    # 5. Export by APPROVING_OFFICER with confirm=True succeeds
    r_export = await client.post(
        f"/dossier/{dossier_id}/export",
        json={"confirm": True, "export_format": "JSON"},
        headers={"X-Demo-User": "officer1"},
    )
    assert r_export.status_code == 200
    exp_data = r_export.json()
    assert exp_data["dossier_id"] == dossier_id
    assert "audit_seq" in exp_data
