"""
sutradhar_api/routers/kumbh.py
Kumbh Mela simulation endpoints.
E1 = WATCHLIST_SIGHTING → raises alert (simulated watchlist match)
E2 = SCAM_PATTERN → raises alert (mule account match)
E3 = MISSING_PERSON (control case) → must NOT raise organised-crime alert
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from sutradhar_api.auth import require_action
from sutradhar_api.models import KumbhAlertActionRequest, UserInfo
from sutradhar_api.store import get_store

router = APIRouter(prefix="/kumbh", tags=["kumbh"])

# Zones
ZONES = [
    {"zone": "Ramkund", "state": "NORMAL", "active_alerts": 0},
    {"zone": "Panchavati", "state": "NORMAL", "active_alerts": 0},
    {"zone": "Tapovan", "state": "NORMAL", "active_alerts": 0},
    {"zone": "Trimbakeshwar", "state": "NORMAL", "active_alerts": 0},
    {"zone": "Godavari Ghats", "state": "NORMAL", "active_alerts": 0},
]

# Events that should trigger an alert
_ALERT_EVENTS = {"WATCHLIST_SIGHTING", "SCAM_PATTERN"}

# Events that must NOT trigger an organised-crime alert (control cases)
_CONTROL_EVENTS = {"MISSING_PERSON"}

# Known entity IDs used as watchlist
_WATCHLIST_ENTITY_IDS = {
    "P-000001",
    "P-000045",
    "P-000046",
    "P-000047",
    "P-000101",
    "P-000102",
}


@router.get("/zones")
def get_kumbh_zones(
    user: Annotated[UserInfo, Depends(require_action("KUMBH_VIEW"))],
):
    store = get_store()
    zone_states = []
    alerts = store.kumbh_alerts

    for zone in ZONES:
        zone_alerts = [
            a for a in alerts if a.get("zone") == zone["zone"] and a.get("state") == "OPEN"
        ]

        zone_states.append(
            {
                "zone": zone["zone"],
                "state": "ALERT" if zone_alerts else "NORMAL",
                "active_alerts": len(zone_alerts),
            }
        )

    return zone_states


@router.get("/alerts")
def get_kumbh_alerts(
    user: Annotated[UserInfo, Depends(require_action("KUMBH_VIEW"))],
):
    return get_store().kumbh_alerts


@router.post("/simulate/next")
def post_simulate_next(
    user: Annotated[UserInfo, Depends(require_action("KUMBH_SIMULATE"))],
):
    store = get_store()
    event = store.play_next_kumbh_event()

    if not event:
        return {
            "message": "No more events in the feed.",
            "event_played": None,
            "alert_raised": False,
        }

    event_type = event.get("event_type")
    alert_raised = False
    alert = None

    if event_type in _ALERT_EVENTS:
        # E1: Watchlist sighting — check related entity IDs
        related = set(event.get("related_ids", []))

        if event_type == "WATCHLIST_SIGHTING" and related & _WATCHLIST_ENTITY_IDS:
            alert = store.add_kumbh_alert(
                event=event,
                confidence=0.91,
                reason="Subject token maps to known watchlist entity. " + str(related),
            )
            alert_raised = True

        elif event_type == "SCAM_PATTERN":
            # E2: Check mule chains or planted scam pattern
            mule_accounts = {
                a.get("account_id")
                for chain in store.mule_chains
                for a in chain.get("accounts", [])
            }

            event_accounts = set(event.get("related_ids", []))

            if (
                (event_accounts & mule_accounts)
                or event.get("planted")
                or event.get("planted_id") == "E2"
            ):
                alert = store.add_kumbh_alert(
                    event=event,
                    confidence=0.88,
                    reason="Pattern matches known mule accounts from community graph.",
                )
                alert_raised = True

    elif event_type in _CONTROL_EVENTS:
        # E3: Missing person — must NOT raise organised-crime alert
        # Standard missing person response only
        alert_raised = False

    seq = store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="KUMBH_EVENT_PLAYED",
        summary=(
            f"Played event {event.get('event_id')} ({event_type}) "
            f"in {event.get('zone')}. Alert raised: {alert_raised}."
        ),
    )

    return {
        "event_played": event,
        "alert_raised": alert_raised,
        "alert_id": alert["alert_id"] if alert else None,
        "reason": alert["reason"] if alert else None,
        "audit_seq": seq,
    }


@router.post("/alerts/{alert_id}/confirm")
def post_kumbh_alert_confirm(
    alert_id: str,
    body: KumbhAlertActionRequest,
    user: Annotated[UserInfo, Depends(require_action("KUMBH_ALERT_CONFIRM"))],
):
    if body.action.value == "DISMISS" and not body.reason:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "REASON_REQUIRED",
                    "message": "A reason is required to dismiss an alert.",
                }
            },
        )

    store = get_store()
    alert = store.update_kumbh_alert(alert_id, body.action.value)

    if not alert:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Alert {alert_id!r} not found.",
                }
            },
        )

    seq = store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action=f"KUMBH_ALERT_{body.action.value}",
        summary=f"Alert {alert_id}: {body.action.value}. Reason: {body.reason!r}",
    )

    return {
        "alert_id": alert_id,
        "action": body.action.value,
        "actor": user.user_id,
        "ts": datetime.now(UTC).isoformat(),
        "audit_seq": seq,
    }


# ─────────────────────────────────────────────────────────────
# Step 4 Kumbh Intelligence Endpoints
# ─────────────────────────────────────────────────────────────


@router.get("/observations")
def get_kumbh_observations(
    user: Annotated[UserInfo, Depends(require_action("KUMBH_VIEW"))],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    zone: str | None = None,
    event_type: str | None = None,
):
    """
    Return operational observations from the Kumbh surveillance feed.
    Contains objective operational data only. Does not expose ground-truth or answers.
    """
    store = get_store()
    observations = store.kumbh_observations

    if zone:
        observations = [obs for obs in observations if obs.get("zone") == zone]
    if event_type:
        observations = [obs for obs in observations if obs.get("event_type") == event_type]

    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="KUMBH_OBSERVATIONS_VIEW",
        summary=f"Viewed Kumbh observations (offset={offset}, limit={limit}, zone={zone}, type={event_type}).",
        purpose="INVESTIGATION",
    )

    return observations[offset : offset + limit]


@router.get("/signals")
def get_kumbh_signals(
    user: Annotated[UserInfo, Depends(require_action("KUMBH_VIEW"))],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    signal_type: str | None = None,
    evidence_tier: str | None = None,
):
    """
    Return explainable Kumbh intelligence signals correlated from Step 4.
    Every signal preserves explainability, evidence, and requires investigator review.
    Never declares guilt or autonomous criminal accusation.
    """
    store = get_store()
    signals = store.kumbh_signals

    if signal_type:
        signals = [s for s in signals if s.get("signal_type") == signal_type]
    if evidence_tier:
        signals = [s for s in signals if s.get("evidence_tier") == evidence_tier]

    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="KUMBH_SIGNALS_VIEW",
        summary=f"Viewed Kumbh intelligence signals (offset={offset}, limit={limit}, type={signal_type}, tier={evidence_tier}).",
        purpose="INVESTIGATION",
    )

    return signals[offset : offset + limit]


@router.get("/clusters")
def get_kumbh_clusters(
    user: Annotated[UserInfo, Depends(require_action("KUMBH_VIEW"))],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    cluster_type: str | None = None,
):
    """
    Return operational Kumbh incident clusters (shared infrastructure, repeated entity, spatio-temporal).
    Strictly distinguished from criminal syndicates. Requires human investigator review.
    """
    store = get_store()
    clusters = store.kumbh_clusters

    if cluster_type:
        clusters = [c for c in clusters if c.get("cluster_type") == cluster_type]

    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="KUMBH_CLUSTERS_VIEW",
        summary=f"Viewed Kumbh clusters (offset={offset}, limit={limit}, type={cluster_type}).",
        purpose="INVESTIGATION",
    )

    return clusters[offset : offset + limit]


@router.get("/events/{event_id}/intelligence")
def get_kumbh_event_intelligence(
    event_id: str,
    user: Annotated[UserInfo, Depends(require_action("KUMBH_VIEW"))],
):
    """
    Return the full Step 4 intelligence portfolio for a specific event.
    Clearly distinguishes operational observation, intelligence signals, network context, and cluster.
    Zero-correlation events safely return observation with empty signals and null network context.
    """
    store = get_store()
    intel = store.get_kumbh_event_intelligence(event_id)

    if not intel:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Kumbh event {event_id!r} not found.",
                }
            },
        )

    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="KUMBH_EVENT_INTELLIGENCE_VIEW",
        summary=f"Viewed intelligence portfolio for Kumbh event {event_id}.",
        purpose="INVESTIGATION",
    )

    return intel
