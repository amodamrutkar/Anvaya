"""
Kumbh events generator for Sutradhar.

Generates data/kumbh/events.jsonl with:
- 3 planted events (E1, E2, E3) from PRD Section 4.3
- ~50 background events (harmless noise)

All tokens are synthetic; no real images or faces.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .lexicons import KUMBH_ZONES, KUMBH_EVENT_TYPES


def generate_kumbh_events(seed: int = 42, out_dir: str = "data") -> list[dict]:
    """Generate Kumbh Mela event feed."""
    rng = random.Random(seed)
    events: list[dict] = []
    event_counter = 0

    base_time = datetime(2027, 1, 13, 6, 0, 0)  # Kumbh start date

    def _next_event_id() -> str:
        nonlocal event_counter
        event_counter += 1
        return f"KUMBH-EVT-{event_counter:04d}"

    def _random_ts() -> str:
        offset = timedelta(
            days=rng.randint(0, 44),  # ~45 day event
            hours=rng.randint(4, 22),
            minutes=rng.randint(0, 59),
        )
        return (base_time + offset).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- Planted Event E1: Watchlist entity sighting ---
    # An associate of the extortion gang flagged in Ramkund
    events.append({
        "event_id": _next_event_id(),
        "ts": (base_time + timedelta(days=3, hours=10, minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "zone": "Ramkund",
        "event_type": "WATCHLIST_SIGHTING",
        "subject_token": "TOK-EXTORT-ASSOC-001",
        "related_ids": ["P-000001"],  # Rakesh Pawar (bridge)
        "details": {
            "description": "Synthetic sighting: subject matching watchlist entity observed near Ramkund bathing ghat. Token-based identification. No real biometric data used.",
            "confidence": 0.92,
        },
        "planted": True,
        "planted_id": "E1",
    })

    # --- Planted Event E2: Pilgrim-targeted scam pattern ---
    # Fake booking links, 14 complaints in 2 hours, matched to Network A accounts
    e2_base = base_time + timedelta(days=7, hours=14)
    events.append({
        "event_id": _next_event_id(),
        "ts": e2_base.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "zone": "Panchavati",
        "event_type": "SCAM_PATTERN",
        "subject_token": "TOK-SCAM-PATTERN-001",
        "related_ids": ["P-000002", "P-000003"],  # Sachin Kale, Nitin Gaikwad
        "details": {
            "description": "Synthetic scam alert: 14 complaints in 120 minutes about fake dharamshala booking links. Payment traced to accounts linked to Network A mule ring. All data synthetic.",
            "complaint_count": 14,
            "duration_hours": 2,
        },
        "planted": True,
        "planted_id": "E2",
    })

    # --- Planted Event E3: Missing person (control case) ---
    # No gang link; must NOT raise organized-crime alert
    events.append({
        "event_id": _next_event_id(),
        "ts": (base_time + timedelta(days=12, hours=8, minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "zone": "Trimbakeshwar",
        "event_type": "MISSING_PERSON",
        "subject_token": "TOK-MISSING-001",
        "related_ids": [],
        "details": {
            "description": "Synthetic missing person report: elderly pilgrim separated from family group near Trimbakeshwar temple. No criminal network connection. Control case for alert system.",
        },
        "planted": True,
        "planted_id": "E3",
    })

    # --- Background events (~50) ---
    bg_event_types = [
        et for et in KUMBH_EVENT_TYPES
        if et not in ("WATCHLIST_SIGHTING", "SCAM_PATTERN")
    ]

    bg_details_templates = {
        "MISSING_PERSON": [
            "Synthetic report: child separated from family at {zone}. Reunited by volunteers within {mins} minutes.",
            "Synthetic report: elderly devotee found disoriented near {zone}. Medical assistance provided.",
        ],
        "MEDICAL_EMERGENCY": [
            "Synthetic alert: heat exhaustion cases reported at {zone}. {count} persons treated at field hospital.",
            "Synthetic alert: minor stampede scare at {zone} during peak hours. No injuries. Crowd managed.",
        ],
        "CROWD_SURGE": [
            "Synthetic alert: crowd density exceeding threshold at {zone}. Additional barricades deployed.",
            "Synthetic alert: VIP movement causing crowd buildup at {zone}. Traffic diverted.",
        ],
        "LOST_AND_FOUND": [
            "Synthetic report: {count} unclaimed bags collected at {zone}. All scanned and cleared.",
            "Synthetic report: valuable item found at {zone}. Deposited at nearest police post.",
        ],
        "VIP_MOVEMENT": [
            "Synthetic alert: dignitary movement through {zone}. Route secured. Duration: {mins} minutes.",
        ],
        "TRAFFIC_DIVERSION": [
            "Synthetic alert: road closure near {zone} for ceremony. Alternate routes active.",
        ],
        "POWER_OUTAGE": [
            "Synthetic alert: temporary power disruption at {zone}. Generator backup activated.",
        ],
        "WATER_SUPPLY_ISSUE": [
            "Synthetic alert: water tanker delay at {zone}. ETA {mins} minutes.",
        ],
    }

    for _ in range(50):
        evt_type = rng.choice(bg_event_types)
        zone = rng.choice(KUMBH_ZONES)
        templates = bg_details_templates.get(evt_type, ["Synthetic event at {zone}."])
        detail = rng.choice(templates).format(
            zone=zone,
            mins=rng.randint(5, 120),
            count=rng.randint(1, 50),
        )

        events.append({
            "event_id": _next_event_id(),
            "ts": _random_ts(),
            "zone": zone,
            "event_type": evt_type,
            "subject_token": f"TOK-BG-{rng.randint(1000, 9999)}",
            "related_ids": [],
            "details": {
                "description": detail,
            },
            "planted": False,
            "planted_id": None,
        })

    # Sort by timestamp
    events.sort(key=lambda e: e["ts"])

    # Write to file
    out_path = Path(out_dir) / "kumbh" / "events.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for evt in events:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    return events
