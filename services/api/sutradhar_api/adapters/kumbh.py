"""
sutradhar_api/adapters/kumbh.py
Simulated Kumbh Mela Operations & Sensor Feed Adapter.

Normalizes smart-city sensor packets, crowd monitors, and CCTV sighting alerts
into the canonical KumbhEvent contract (kumbh_event.schema.json).
All feeds are simulated; no live camera feeds or external IoT network calls exist.
"""

from __future__ import annotations

import re
from typing import Any

from sutradhar_api.adapters.base import (
    AdapterMappingError,
    BaseAdapter,
)

_VALID_ZONES = {"Ramkund", "Panchavati", "Tapovan", "Trimbakeshwar", "Godavari Ghats"}
_VALID_EVENT_TYPES = {
    "WATCHLIST_SIGHTING",
    "SCAM_PATTERN",
    "MISSING_PERSON",
    "LOST_AND_FOUND",
    "MEDICAL_EMERGENCY",
    "TRAFFIC_DIVERSION",
    "CROWD_SURGE",
    "POWER_OUTAGE",
    "WATER_SUPPLY_ISSUE",
    "VIP_MOVEMENT",
}


class KumbhOperationsAdapter(BaseAdapter):
    """Adapter for simulated Kumbh Mela tactical operations feeds."""

    adapter_id = "KumbhOperationsAdapter"
    source_system = "KUMBH_SURVEILLANCE"
    agency = "STATE_POLICE"
    target_schema = "kumbh_event.schema.json"

    def adapt(self, raw_payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Transform raw sensor/edge alert payload into canonical KumbhEvent."""
        raw_id = raw_payload.get("sensor_event_id") or raw_payload.get("event_id")
        if not raw_id:
            raise AdapterMappingError("Missing required field: 'sensor_event_id' or 'event_id'")

        zone = raw_payload.get("operational_sector") or raw_payload.get("zone")
        if not zone or zone not in _VALID_ZONES:
            raise AdapterMappingError(f"Invalid or missing Kumbh zone '{zone}'. Must be one of {_VALID_ZONES}")

        ev_type = raw_payload.get("category") or raw_payload.get("event_type")
        if not ev_type or ev_type not in _VALID_EVENT_TYPES:
            raise AdapterMappingError(f"Invalid or missing Kumbh event_type '{ev_type}'. Must be one of {_VALID_EVENT_TYPES}")

        subject = raw_payload.get("detected_token") or raw_payload.get("subject_token")
        if not subject:
            raise AdapterMappingError("Missing required field: 'detected_token' or 'subject_token'")

        ts = raw_payload.get("timestamp_local") or raw_payload.get("ts")
        if not ts:
            raise AdapterMappingError("Missing required timestamp: 'timestamp_local' or 'ts'")

        override_eid = kwargs.get("event_id") or raw_payload.get("canonical_event_id")
        if override_eid:
            canonical_eid = override_eid
        else:
            num_match = re.search(r"\d+", str(raw_id))
            num_val = int(num_match.group(0)) if num_match else 1
            canonical_eid = f"EVT-KMB-{num_val:06d}"

        ingestion_metadata = self.build_ingestion_metadata(
            source_record_id=str(raw_id),
            raw_payload=raw_payload,
            trace_id=kwargs.get("trace_id"),
            batch_id=kwargs.get("batch_id"),
            provenance={
                "feed_source": raw_payload.get("feed_source", "CAMERA_EDGE"),
                "sector": zone,
            },
        )

        details = dict(raw_payload.get("sensor_telemetry", raw_payload.get("details", {})))
        if "feed_source" in raw_payload:
            details["feed_source"] = raw_payload["feed_source"]
        details["sensor_event_id"] = str(raw_id)

        return {
            "event_id": canonical_eid,
            "ts": str(ts),
            "zone": zone,
            "event_type": ev_type,
            "subject_token": str(subject),
            "related_ids": raw_payload.get("associated_tokens", raw_payload.get("related_ids", [])),
            "details": details,
            "ingestion_metadata": ingestion_metadata,
        }
