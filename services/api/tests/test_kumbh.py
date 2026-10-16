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

    # Helper function to play until a specific event_type is encountered
    async def play_until(target_type: str):
        while True:
            r = await client.post("/kumbh/simulate/next", headers={"X-Demo-User": "inspector1"})
            assert r.status_code == 200
            data = r.json()
            if not data.get("event_played"):
                pytest.fail(f"Reached end of events without finding event_type={target_type}")
            if data["event_played"]["event_type"] == target_type:
                return data

    # Play Event 1: E1 WATCHLIST_SIGHTING -> must raise alert
    d1 = await play_until("WATCHLIST_SIGHTING")
    assert d1["alert_raised"] is True
    assert d1["alert_id"] is not None

    # Play Event 2: E2 SCAM_PATTERN -> must raise alert
    d2 = await play_until("SCAM_PATTERN")
    assert d2["alert_raised"] is True
    assert d2["alert_id"] is not None

    # Play Event 3: E3 MISSING_PERSON -> control case, must NOT raise alert!
    d3 = await play_until("MISSING_PERSON")
    assert d3["alert_raised"] is False
    assert d3["alert_id"] is None


@pytest.mark.asyncio
async def test_kumbh_alert_confirm_and_dismiss(client):
    store = get_store()
    # Ensure there is an alert
    if not store.kumbh_alerts:
        store._kumbh_event_cursor = 0
        while not store.kumbh_alerts and store._kumbh_event_cursor < len(store.kumbh_events):
            await client.post("/kumbh/simulate/next", headers={"X-Demo-User": "inspector1"})

    assert store.kumbh_alerts, "Expected at least one alert to be generated"
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
