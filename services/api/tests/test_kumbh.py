"""
tests/test_kumbh.py
Tests for Kumbh simulation mode, alert generation (E1, E2),
control case (E3 missing person raises no alert), and alert confirm/dismiss.
"""
import pytest

from sutradhar_api.store import get_store


@pytest.mark.asyncio
async def test_kumbh_zones(client):
    r = await client.get("/kumbh/zones", headers={"X-Demo-User": "inspector1"})
    assert r.status_code == 200
    zones = r.json()
    assert len(zones) >= 5
    assert all("zone" in z and "state" in z for z in zones)


@pytest.mark.asyncio
async def test_kumbh_simulation_and_control_case(client):
    store = get_store()
    # Reset cursor
    store._kumbh_event_cursor = 0
    store._kumbh_alerts.clear()

    # Play Event 1: E1 WATCHLIST_SIGHTING -> must raise alert
    r1 = await client.post("/kumbh/simulate/next", headers={"X-Demo-User": "inspector1"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["event_played"]["event_id"] == "EVT-001"
    assert d1["alert_raised"] is True
    assert d1["alert_id"] is not None

    # Play Event 2: E2 SCAM_PATTERN -> must raise alert
    r2 = await client.post("/kumbh/simulate/next", headers={"X-Demo-User": "inspector1"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["event_played"]["event_id"] == "EVT-002"
    assert d2["alert_raised"] is True
    assert d2["alert_id"] is not None

    # Play Event 3: E3 MISSING_PERSON -> control case, must NOT raise alert!
    r3 = await client.post("/kumbh/simulate/next", headers={"X-Demo-User": "inspector1"})
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["event_played"]["event_id"] == "EVT-003"
    assert d3["alert_raised"] is False
    assert d3["alert_id"] is None


@pytest.mark.asyncio
async def test_kumbh_alert_confirm_and_dismiss(client):
    store = get_store()
    # Ensure there is an alert
    if not store.kumbh_alerts:
        store._kumbh_event_cursor = 0
        await client.post("/kumbh/simulate/next", headers={"X-Demo-User": "inspector1"})

    alert_id = store.kumbh_alerts[0]["alert_id"]

    # Confirm alert
    r_conf = await client.post(
        f"/kumbh/alerts/{alert_id}/confirm",
        json={"action": "CONFIRM", "reason": "Officer visual confirmation at ghat."},
        headers={"X-Demo-User": "inspector1"},
    )
    assert r_conf.status_code == 200
    assert r_conf.json()["action"] == "CONFIRM"

    # Dismiss requires reason (missing reason should return 422)
    r_dismiss_noreason = await client.post(
        f"/kumbh/alerts/{alert_id}/confirm",
        json={"action": "DISMISS", "reason": None},
        headers={"X-Demo-User": "inspector1"},
    )
    assert r_dismiss_noreason.status_code == 422

    # Dismiss with reason succeeds
    r_dismiss = await client.post(
        f"/kumbh/alerts/{alert_id}/confirm",
        json={"action": "DISMISS", "reason": "False positive: verified pilgrim identity."},
        headers={"X-Demo-User": "inspector1"},
    )
    assert r_dismiss.status_code == 200
    assert r_dismiss.json()["action"] == "DISMISS"
