"""
Kumbh Operations Intelligence Layer for Sutradhar.

Provides event-specific situational intelligence correlation connecting Kumbh events,
locations, persons/entities, cases, criminal networks, vehicles, phones, accounts,
and temporal/spatial activity to the existing Sutradhar knowledge graph.

CRITICAL SAFETY PRINCIPLES:
- Kumbh Operations is an INTELLIGENCE CORRELATION layer, NOT an autonomous policing system.
- Never declare a person guilty or automatically accuse a person.
- Never generate a criminal classification solely because of Kumbh presence.
- Proximity to an incident is NOT proof of involvement (produces spatial association only).
- All generated intelligence items require human investigator review (action = "Requires investigator review").
- Respects the evidence hierarchy: STRONG > MEDIUM > WEAK.
- Purely deterministic inference using observable graph evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from pathlib import Path
import re
from typing import Any

from .models import (
    BridgeModel,
    CommunityModel,
    EdgeStrength,
    IntelligenceSignalModel,
    InvestigatorReviewObject,
    KumbhClusterModel,
    KumbhEventModel,
    MuleChainModel,
    NetworkContextModel,
    NodeType,
    RoleAssignment,
    SignalType,
)


# --------------------------------------------------------------------------- #
# Temporal & Spatial Configurations
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TemporalConfig:
    """
    Configurable temporal correlation windows for Kumbh operations.
    
    Windows:
    - immediate (default 3600s = 1 hour): Captures active incident bursts, rapid scam
      complaints, and co-incident sightings during the same ceremony or gathering.
    - short (default 21600s = 6 hours): Operational shift window (e.g. morning/evening
      bathing peak or security watch shift).
    - extended (default 86400s = 24 hours): Diurnal activity cycle capturing multi-event
      movements within the same operational day.
    """
    immediate_seconds: int = 3600
    short_seconds: int = 21600
    extended_seconds: int = 86400


@dataclass(frozen=True)
class SpatialConfig:
    """
    Configurable spatial correlation parameters.
    
    When geographic coordinates (latitude, longitude) are present in event data,
    haversine distance is calculated against max_distance_km.
    When coordinates are absent (standard Kumbh operational feed), correlation
    falls back cleanly to zone-level spatial correlation without inventing coordinates.
    """
    max_distance_km: float = 2.0
    require_coordinates: bool = False


# Known Kumbh Mela Zones (Nashik / Trimbak)
KUMBH_ZONES = (
    "Ramkund",
    "Panchavati",
    "Tapovan",
    "Trimbakeshwar",
    "Godavari Ghats",
)


def parse_iso_timestamp(ts_str: str) -> datetime:
    """Deterministically parse an ISO8601 timestamp string into a UTC datetime object."""
    clean_ts = ts_str.strip()
    if clean_ts.endswith("Z"):
        clean_ts = clean_ts[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(clean_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        # Fallback to standard base date if unparseable
        return datetime(2027, 1, 13, 0, 0, 0, tzinfo=timezone.utc)


def haversine_distance_km(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
    """Calculate the great-circle distance between two points on Earth in kilometers."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    r = 6371.0  # Earth radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def parse_kumbh_event(raw: dict[str, Any]) -> KumbhEventModel:
    """
    Convert a raw event dictionary into a validated KumbhEventModel.
    Ensures safe extraction of identifiers, timestamps, zones, and details.
    """
    evt_id = raw.get("event_id") or raw.get("id") or "KUMBH-EVT-UNKNOWN"
    evt_type = raw.get("event_type") or raw.get("type") or "INCIDENT"
    ts = raw.get("ts") or raw.get("timestamp") or "2027-01-13T06:00:00Z"
    zone = raw.get("zone") or raw.get("zone_id") or "Ramkund"
    subject_token = raw.get("subject_token")
    related_ids = list(raw.get("related_ids") or [])
    details = dict(raw.get("details") or {})
    source_agency = raw.get("source_agency") or raw.get("agency") or "KUMBH_SURVEILLANCE"
    
    # Confidence from details or default 1.0
    conf = float(details.get("confidence", raw.get("confidence", 1.0)))

    # Coordinates if present in details or top-level
    coords = None
    if "latitude" in details and "longitude" in details:
        try:
            coords = (float(details["latitude"]), float(details["longitude"]))
        except (ValueError, TypeError):
            coords = None
    elif "coordinates" in raw and isinstance(raw["coordinates"], (list, tuple)) and len(raw["coordinates"]) == 2:
        try:
            coords = (float(raw["coordinates"][0]), float(raw["coordinates"][1]))
        except (ValueError, TypeError):
            coords = None

    provenance = dict(raw.get("provenance") or {
        "source": "Kumbh Operations Feed",
        "event_id": evt_id,
        "zone": zone,
        "timestamp": ts,
    })

    return KumbhEventModel(
        event_id=evt_id,
        event_type=evt_type,
        ts=ts,
        zone=zone,
        subject_token=subject_token,
        related_ids=related_ids,
        source_agency=source_agency,
        confidence=conf,
        details=details,
        provenance=provenance,
        coordinates=coords,
    )


# --------------------------------------------------------------------------- #
# Kumbh Operations Intelligence Engine
# --------------------------------------------------------------------------- #
class KumbhOperationsEngine:
    """
    Event-specific situational intelligence engine for Kumbh operations.
    Correlates Kumbh events with the validated Sutradhar Knowledge Graph and Network Analytics.
    """

    def __init__(
        self,
        graph_data: dict[str, Any],
        communities: list[CommunityModel | dict[str, Any]] | None = None,
        roles: list[RoleAssignment | dict[str, Any]] | None = None,
        bridges: list[BridgeModel | dict[str, Any]] | None = None,
        mule_chains: list[MuleChainModel | dict[str, Any]] | None = None,
        temporal_config: TemporalConfig | None = None,
        spatial_config: SpatialConfig | None = None,
    ):
        self.graph_data = graph_data
        self.temporal_config = temporal_config or TemporalConfig()
        self.spatial_config = spatial_config or SpatialConfig()

        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []
        self._communities: list[CommunityModel] = []
        self._roles: list[RoleAssignment] = []
        self._bridges: list[BridgeModel] = []
        self._mule_chains: list[MuleChainModel] = []

        # Fast lookup indexes
        self._entity_to_cases: dict[str, list[dict[str, Any]]] = {}
        self._entity_to_phones: dict[str, list[str]] = {}
        self._phone_to_entities: dict[str, list[str]] = {}
        self._entity_to_accounts: dict[str, list[str]] = {}
        self._account_to_entities: dict[str, list[str]] = {}
        self._entity_to_vehicles: dict[str, list[str]] = {}
        self._vehicle_to_entities: dict[str, list[str]] = {}

        self._entity_to_communities: dict[str, list[CommunityModel]] = {}
        self._entity_to_roles: dict[str, list[RoleAssignment]] = {}
        self._entity_to_bridges: dict[str, BridgeModel] = {}
        self._account_to_chains: dict[str, list[dict[str, Any]]] = {}

        self._ingest_analytics(communities, roles, bridges, mule_chains)
        self._build_graph_indexes()

    def _ingest_analytics(
        self,
        communities: list[CommunityModel | dict[str, Any]] | None,
        roles: list[RoleAssignment | dict[str, Any]] | None,
        bridges: list[BridgeModel | dict[str, Any]] | None,
        mule_chains: list[MuleChainModel | dict[str, Any]] | None,
    ) -> None:
        if communities:
            for c in communities:
                model = c if isinstance(c, CommunityModel) else CommunityModel(**c)
                self._communities.append(model)
                for member_id in model.members:
                    self._entity_to_communities.setdefault(member_id, []).append(model)

        if roles:
            for r in roles:
                model = r if isinstance(r, RoleAssignment) else RoleAssignment(**r)
                self._roles.append(model)
                self._entity_to_roles.setdefault(model.entity_id, []).append(model)

        if bridges:
            for b in bridges:
                model = b if isinstance(b, BridgeModel) else BridgeModel(**b)
                self._bridges.append(model)
                self._entity_to_bridges[model.node_id] = model

        if mule_chains:
            for ch in mule_chains:
                model = ch if isinstance(ch, MuleChainModel) else MuleChainModel(**ch)
                self._mule_chains.append(model)
                for acct in model.accounts:
                    self._account_to_chains.setdefault(acct.account_key, []).append({
                        "chain_id": model.chain_id,
                        "layer": acct.layer,
                        "classification": acct.classification,
                        "score": acct.score,
                    })

    def _build_graph_indexes(self) -> None:
        """Index nodes and edges for O(1) intelligence retrieval."""
        for n in self.graph_data.get("nodes", []):
            nid = n.get("id")
            if nid:
                self._nodes[nid] = n

        for e in self.graph_data.get("edges", []):
            self._edges.append(e)
            src = e.get("source", "")
            tgt = e.get("target", "")
            etype = e.get("type", "")

            # Person <-> Case
            if etype in ("ACCUSED_IN", "VICTIM_IN"):
                self._entity_to_cases.setdefault(src, []).append({
                    "case_ref": tgt,
                    "relationship": etype,
                    "evidence": e.get("evidence", []),
                    "provenance": e.get("provenance", {}),
                    "confidence": e.get("confidence", 1.0),
                    "strength": e.get("strength", "STRONG"),
                })

            # Person <-> Phone
            elif etype == "USES":
                target_node = self._nodes.get(tgt, {})
                target_type = target_node.get("type", "")
                source_node = self._nodes.get(src, {})
                source_type = source_node.get("type", "")

                if target_type == "PHONE" or tgt.startswith("PHONE:") or tgt.startswith("PH-"):
                    self._entity_to_phones.setdefault(src, []).append(tgt)
                    self._phone_to_entities.setdefault(tgt, []).append(src)
                elif target_type == "VEHICLE" or tgt.startswith("VEH-"):
                    self._entity_to_vehicles.setdefault(src, []).append(tgt)
                    self._vehicle_to_entities.setdefault(tgt, []).append(src)
                elif source_type == "PHONE" or src.startswith("PHONE:") or src.startswith("PH-"):
                    self._entity_to_phones.setdefault(tgt, []).append(src)
                    self._phone_to_entities.setdefault(src, []).append(tgt)
                elif source_type == "VEHICLE" or src.startswith("VEH-"):
                    self._entity_to_vehicles.setdefault(tgt, []).append(src)
                    self._vehicle_to_entities.setdefault(src, []).append(tgt)

            # Person <-> Account
            elif etype == "OWNS":
                self._entity_to_accounts.setdefault(src, []).append(tgt)
                self._account_to_entities.setdefault(tgt, []).append(src)

            # Person <-> Vehicle / Seen with Vehicle
            elif etype in ("SEEN_AT", "ASSOCIATED_WITH"):
                target_node = self._nodes.get(tgt, {})
                if target_node.get("type") == "VEHICLE" or tgt.startswith("VEH-"):
                    self._entity_to_vehicles.setdefault(src, []).append(tgt)
                    self._vehicle_to_entities.setdefault(tgt, []).append(src)

    # ----------------------------------------------------------------------- #
    # Network Context Retrieval (Step 4G)
    # ----------------------------------------------------------------------- #
    def get_network_context(self, entity_id: str) -> NetworkContextModel | None:
        """
        Surface relevant existing intelligence from the validated graph for an entity.
        Respects evidence hierarchy: STRONG statutory evidence > MEDIUM ER links > WEAK proximity.
        """
        node = self._nodes.get(entity_id)
        canonical_name = node.get("label") if node else None

        # Cases
        cases_info = self._entity_to_cases.get(entity_id, [])
        case_refs = [c["case_ref"] for c in cases_info]
        crime_types = sorted(set(
            self._nodes.get(c["case_ref"], {}).get("attributes", {}).get("crime_type", "GENERAL")
            for c in cases_info
        ))

        # Communities
        comms = self._entity_to_communities.get(entity_id, [])
        comm_ids = [c.community_id for c in comms]
        is_noi = any(c.is_network_of_interest for c in comms)

        # Roles
        roles_assigned = self._entity_to_roles.get(entity_id, [])
        role_names = [r.role for r in roles_assigned]

        # Bridges
        bridge = self._entity_to_bridges.get(entity_id)
        is_bridge = bridge is not None
        bridge_score = bridge.score if bridge else None

        # Associated Infrastructure
        phones = sorted(set(self._entity_to_phones.get(entity_id, [])))
        accounts = sorted(set(self._entity_to_accounts.get(entity_id, [])))
        vehicles = sorted(set(self._entity_to_vehicles.get(entity_id, [])))

        # Financial Chains
        chains_found: list[str] = []
        for acct in accounts:
            chains_for_acct = self._account_to_chains.get(acct, [])
            for ch in chains_for_acct:
                chains_found.append(f"{ch['chain_id']}:{ch['classification']}")

        # Determine Evidence Tier
        # Statutory case charges = STRONG
        # Verified phone/account ownership = STRONG or MEDIUM
        # Indirect or unverified = WEAK
        if any(c["relationship"] == "ACCUSED_IN" and c["strength"] == "STRONG" for c in cases_info):
            tier: EdgeStrength = "STRONG"
        elif cases_info or comms or accounts or phones:
            tier = "MEDIUM"
        else:
            tier = "WEAK"

        provenance_entries: list[dict[str, Any]] = []
        for c in cases_info:
            provenance_entries.append({
                "source": "CASE_RECORD",
                "case_ref": c["case_ref"],
                "relationship": c["relationship"],
                "provenance": c["provenance"],
            })

        return NetworkContextModel(
            entity_id=entity_id,
            entity_type=node.get("type", "PERSON") if node else "PERSON",
            canonical_name=canonical_name,
            cases=case_refs,
            crime_types=crime_types,
            communities=comm_ids,
            is_network_of_interest=is_noi,
            roles=role_names,
            is_bridge_candidate=is_bridge,
            bridge_score=bridge_score,
            financial_chains=sorted(set(chains_found)),
            associated_phones=phones,
            associated_accounts=accounts,
            associated_vehicles=vehicles,
            evidence_tier=tier,
            provenance=provenance_entries,
            action="Requires investigator review",
        )

    # ----------------------------------------------------------------------- #
    # Event Correlation (Step 4B & 4C)
    # ----------------------------------------------------------------------- #
    def correlate_event(
        self,
        event: KumbhEventModel,
        all_events: list[KumbhEventModel] | None = None,
    ) -> list[InvestigatorReviewObject]:
        """
        Deterministically correlate a single Kumbh event against existing graph entities.
        Generates explainable review objects with signals, evidence, provenance, and tiers.
        """
        review_objects: list[InvestigatorReviewObject] = []
        event_dt = parse_iso_timestamp(event.ts)

        # 1. Direct Identity Matching (related_ids, subject_token, details)
        candidate_entity_ids: set[str] = set()

        for rid in event.related_ids:
            if rid in self._nodes:
                node = self._nodes[rid]
                if node.get("type") == "PERSON":
                    candidate_entity_ids.add(rid)
            # Check phone to entity
            if rid in self._phone_to_entities:
                candidate_entity_ids.update(self._phone_to_entities[rid])
            # Check account to entity
            if rid in self._account_to_entities:
                candidate_entity_ids.update(self._account_to_entities[rid])
            # Vehicle sightings produce vehicle association only (Case 4), not person presence

        # If subject token directly matches an entity or is formatted as entity
        if event.subject_token and event.subject_token in self._nodes:
            node = self._nodes[event.subject_token]
            if node.get("type") == "PERSON":
                candidate_entity_ids.add(event.subject_token)

        # Check description/details for phone or account tokens
        desc = str(event.details.get("description", ""))
        for acct_key in self._account_to_entities:
            # Extract plain key if prefixed
            plain_acct = acct_key.replace("ACCOUNT:", "")
            if plain_acct and plain_acct in desc:
                candidate_entity_ids.update(self._account_to_entities[acct_key])

        # If entities matched, generate rich contextual intelligence
        for ent_id in sorted(candidate_entity_ids):
            signals: list[IntelligenceSignalModel] = []
            evidence_lines: list[str] = []
            provenance_list: list[dict[str, Any]] = []

            node = self._nodes.get(ent_id, {})
            node_label = node.get("label", ent_id)
            context = self.get_network_context(ent_id)

            # Signal 1: KNOWN_ENTITY_MATCH
            signals.append(
                IntelligenceSignalModel(
                    signal_type="KNOWN_ENTITY_MATCH",
                    description=f"Entity {ent_id} ({node_label}) matches identifier in Kumbh event {event.event_id}.",
                    evidence=[f"Event {event.event_id} references {ent_id}"],
                    provenance=event.provenance,
                    confidence=event.confidence,
                    action="Requires investigator review",
                )
            )
            evidence_lines.append(f"Direct identifier match: {ent_id} observed at {event.zone}.")

            # Signal 2: KNOWN_CASE_ASSOCIATION
            if context and context.cases:
                signals.append(
                    IntelligenceSignalModel(
                        signal_type="KNOWN_CASE_ASSOCIATION",
                        description=f"Entity {ent_id} is already linked to statutory case(s): {', '.join(context.cases)}.",
                        evidence=[f"Case filing(s): {', '.join(context.cases)}"],
                        provenance={"cases": context.cases, "crime_types": context.crime_types},
                        confidence=0.90,
                        action="Requires investigator review",
                    )
                )
                evidence_lines.append(f"Statutory case link: {ent_id} associated with {', '.join(context.cases)}.")
                provenance_list.extend(context.provenance)

            # Signal 3: KNOWN_NETWORK_ASSOCIATION
            if context and context.communities:
                signals.append(
                    IntelligenceSignalModel(
                        signal_type="KNOWN_NETWORK_ASSOCIATION",
                        description=f"Entity {ent_id} is associated with community network(s): {', '.join(context.communities)}.",
                        evidence=[f"Community membership: {', '.join(context.communities)}"],
                        provenance={"communities": context.communities, "is_network_of_interest": context.is_network_of_interest},
                        confidence=0.85,
                        action="Requires investigator review",
                    )
                )
                evidence_lines.append(f"Network intelligence: Community {', '.join(context.communities)} membership.")

            # Signal 4: CROSS_CASE_ACTIVITY
            if context and len(context.cases) >= 2:
                signals.append(
                    IntelligenceSignalModel(
                        signal_type="CROSS_CASE_ACTIVITY",
                        description=f"Entity {ent_id} spans {len(context.cases)} separate cases across law enforcement jurisdictions.",
                        evidence=[f"Cross-case activity across: {', '.join(context.cases)}"],
                        provenance={"case_count": len(context.cases)},
                        confidence=0.92,
                        action="Requires investigator review",
                    )
                )
                evidence_lines.append(f"Multi-case footprint: Spans {len(context.cases)} cases.")

            # Signal 5: ACCOUNT_ASSOCIATION
            if context and context.financial_chains:
                signals.append(
                    IntelligenceSignalModel(
                        signal_type="ACCOUNT_ASSOCIATION",
                        description=f"Entity {ent_id} has financial infrastructure linked to money routing chain(s): {', '.join(context.financial_chains)}.",
                        evidence=[f"Mule chain match: {', '.join(context.financial_chains)}"],
                        provenance={"financial_chains": context.financial_chains},
                        confidence=0.88,
                        action="Requires investigator review",
                    )
                )
                evidence_lines.append(f"Financial flow linkage: {', '.join(context.financial_chains)}.")

            # Signal 6: PHONE_ASSOCIATION
            if context and context.associated_phones:
                signals.append(
                    IntelligenceSignalModel(
                        signal_type="PHONE_ASSOCIATION",
                        description=f"Entity {ent_id} uses phone identifier(s): {', '.join(context.associated_phones)}.",
                        evidence=[f"Registered phone(s): {', '.join(context.associated_phones)}"],
                        provenance={"phones": context.associated_phones},
                        confidence=0.90,
                        action="Requires investigator review",
                    )
                )

            # Signal 7: VEHICLE_ASSOCIATION
            if context and context.associated_vehicles:
                signals.append(
                    IntelligenceSignalModel(
                        signal_type="VEHICLE_ASSOCIATION",
                        description=f"Entity {ent_id} is associated with vehicle(s): {', '.join(context.associated_vehicles)}.",
                        evidence=[f"Associated vehicle(s): {', '.join(context.associated_vehicles)}"],
                        provenance={"vehicles": context.associated_vehicles},
                        confidence=0.85,
                        action="Requires investigator review",
                    )
                )

            # Signal 8: REPEATED_EVENT_ASSOCIATION (across event feed)
            if all_events:
                same_entity_events = [
                    ev for ev in all_events
                    if ev.event_id != event.event_id and ent_id in ev.related_ids
                ]
                if same_entity_events:
                    other_ev_ids = [ev.event_id for ev in same_entity_events]
                    signals.append(
                        IntelligenceSignalModel(
                            signal_type="REPEATED_EVENT_ASSOCIATION",
                            description=f"Entity {ent_id} appears in {len(same_entity_events) + 1} distinct Kumbh events: {', '.join(other_ev_ids)}.",
                            evidence=[f"Repeated sightings across events: {', '.join(other_ev_ids)}"],
                            provenance={"other_events": other_ev_ids},
                            confidence=0.89,
                            action="Requires investigator review",
                        )
                    )
                    evidence_lines.append(f"Repeated Kumbh presence: {len(same_entity_events) + 1} events.")

            # Determine Tier: STRONG if statutory case linkage exists, else MEDIUM
            evidence_tier: EdgeStrength = context.evidence_tier if context else "MEDIUM"

            explanation = (
                f"Sutradhar intelligence correlation for Kumbh event {event.event_id} at zone {event.zone}: "
                f"Subject {ent_id} ({node_label}) was surfaced based on deterministic graph matching. "
                f"Existing intelligence reflects {len(context.cases if context else [])} statutory cases, "
                f"{len(context.communities if context else [])} community networks, and "
                f"{len(context.financial_chains if context else [])} financial flow linkages. "
                f"Presence at Kumbh is not criminal evidence by itself. Action requires investigator review."
            )

            review_objects.append(
                InvestigatorReviewObject(
                    intelligence_id=f"INTEL-{event.event_id}-{ent_id}",
                    type="EVENT_ENTITY_CORRELATION",
                    subject=ent_id,
                    related_event=event.event_id,
                    confidence=event.confidence,
                    signals=signals,
                    evidence=evidence_lines,
                    provenance=provenance_list or [event.provenance],
                    evidence_tier=evidence_tier,
                    network_context=context,
                    explanation=explanation,
                    action="Requires investigator review",
                )
            )

        # 2. Control Case / Civilian Attendance Protection (Step 4I Case 1 & Case 2)
        # If no known entity or case matched, and this is a general/benign event (e.g. missing person, lost & found),
        # create an informational record without any criminal classification.
        if not candidate_entity_ids:
            # Check if this is an infrastructure sighting (e.g. vehicle seen near event)
            vehicle_matches = [rid for rid in event.related_ids if rid.startswith("VEH-") or (rid in self._nodes and self._nodes[rid].get("type") == "VEHICLE")]
            if vehicle_matches:
                for v_id in vehicle_matches:
                    v_signals = [
                        IntelligenceSignalModel(
                            signal_type="VEHICLE_ASSOCIATION",
                            description=f"Vehicle {v_id} observed near Kumbh event {event.event_id} ({event.zone}). Proximity is not proof of wrongdoing.",
                            evidence=[f"Vehicle {v_id} recorded at zone {event.zone}"],
                            provenance=event.provenance,
                            confidence=0.75,
                            action="Requires investigator review",
                        )
                    ]
                    if all_events:
                        same_v_events = [
                            ev for ev in all_events
                            if ev.event_id != event.event_id and v_id in ev.related_ids
                        ]
                        if same_v_events:
                            other_v_ids = [ev.event_id for ev in same_v_events]
                            v_signals.append(
                                IntelligenceSignalModel(
                                    signal_type="REPEATED_EVENT_ASSOCIATION",
                                    description=f"Vehicle {v_id} observed near {len(same_v_events) + 1} distinct events: {', '.join(other_v_ids)}.",
                                    evidence=[f"Repeated vehicle presence across: {', '.join(other_v_ids)}"],
                                    provenance={"other_events": other_v_ids},
                                    confidence=0.80,
                                    action="Requires investigator review",
                                )
                            )
                    review_objects.append(
                        InvestigatorReviewObject(
                            intelligence_id=f"INTEL-{event.event_id}-{v_id}",
                            type="VEHICLE_SIGHTING_CORRELATION",
                            subject=v_id,
                            related_event=event.event_id,
                            confidence=0.75,
                            signals=v_signals,
                            evidence=[f"Vehicle {v_id} observed at {event.zone}."],
                            provenance=[event.provenance],
                            evidence_tier="WEAK",
                            network_context=None,
                            explanation=(
                                f"Vehicle {v_id} was observed near event {event.event_id}. "
                                "Vehicle presence near an event represents spatial association only. "
                                "Requires investigator review."
                            ),
                            action="Requires investigator review",
                        )
                    )
            else:
                # Pure civilian / benign observation
                review_objects.append(
                    InvestigatorReviewObject(
                        intelligence_id=f"INTEL-{event.event_id}-OBSERVATION",
                        type="CIVILIAN_OPERATIONAL_OBSERVATION",
                        subject=event.subject_token or event.event_id,
                        related_event=event.event_id,
                        confidence=event.confidence,
                        signals=[],
                        evidence=[f"Event {event.event_id} ({event.event_type}) recorded in zone {event.zone}."],
                        provenance=[event.provenance],
                        evidence_tier="WEAK",
                        network_context=None,
                        explanation=(
                            f"Standard operational observation for event {event.event_id} ({event.event_type}) at {event.zone}. "
                            "No criminal syndicate, case, or watchlist association exists in the Sutradhar knowledge graph. "
                            "Event attendance or proximity to Kumbh is not criminal evidence."
                        ),
                        action="Requires investigator review",
                    )
                )

        return review_objects

    # ----------------------------------------------------------------------- #
    # Event Clustering (Step 4F)
    # ----------------------------------------------------------------------- #
    def cluster_events(
        self,
        events: list[KumbhEventModel],
    ) -> list[KumbhClusterModel]:
        """
        Deterministically cluster Kumbh events by:
        1. Shared Infrastructure (accounts, phones, vehicles)
        2. Shared Entities (persons observed across events)
        3. Spatio-Temporal Proximity (same zone/proximity within immediate or short window)

        Each cluster exposes clear shared evidence, confidence, provenance, and explanation.
        NEVER labels a cluster as an autonomous criminal syndicate.
        """
        clusters: list[KumbhClusterModel] = []
        cluster_counter = 0

        # Index events by time and zone
        events_by_id = {e.event_id: e for e in events}

        # ------------------------------------------------------------------- #
        # Cluster Type 1: Shared Infrastructure (Account / Phone / Vehicle)
        # ------------------------------------------------------------------- #
        infra_to_events: dict[str, list[str]] = {}
        for ev in events:
            # Check related_ids for accounts, phones, vehicles
            for rid in ev.related_ids:
                if rid.startswith("AC-") or rid.startswith("PH-") or rid.startswith("VEH-"):
                    infra_to_events.setdefault(rid, []).append(ev.event_id)
            # Check description for account tokens
            desc = str(ev.details.get("description", ""))
            for acct_match in re.findall(r"AC-\d{6}", desc):
                infra_to_events.setdefault(acct_match, []).append(ev.event_id)

        for infra_id, ev_ids in sorted(infra_to_events.items()):
            unique_ev_ids = sorted(set(ev_ids))
            if len(unique_ev_ids) >= 2:
                cluster_counter += 1
                clusters.append(
                    KumbhClusterModel(
                        cluster_id=f"KUMBH-CLUST-{cluster_counter:04d}",
                        cluster_type="SHARED_INFRASTRUCTURE_CLUSTER",
                        member_events=unique_ev_ids,
                        shared_evidence=[f"Shared infrastructure token: {infra_id}"],
                        confidence=0.88,
                        provenance={
                            "infrastructure_id": infra_id,
                            "event_count": len(unique_ev_ids),
                        },
                        explanation=(
                            f"Multiple Kumbh events ({', '.join(unique_ev_ids)}) reference shared infrastructure {infra_id}. "
                            "This represents an operational correlation across event reports. "
                            "Requires investigator review."
                        ),
                        action="Requires investigator review",
                    )
                )

        # ------------------------------------------------------------------- #
        # Cluster Type 2: Shared Entity (Same person across multiple events)
        # ------------------------------------------------------------------- #
        entity_to_events: dict[str, list[str]] = {}
        for ev in events:
            for rid in ev.related_ids:
                if rid.startswith("P-") or rid.startswith("ENT-"):
                    entity_to_events.setdefault(rid, []).append(ev.event_id)

        for ent_id, ev_ids in sorted(entity_to_events.items()):
            unique_ev_ids = sorted(set(ev_ids))
            if len(unique_ev_ids) >= 2:
                cluster_counter += 1
                clusters.append(
                    KumbhClusterModel(
                        cluster_id=f"KUMBH-CLUST-{cluster_counter:04d}",
                        cluster_type="SHARED_ENTITY_CLUSTER",
                        member_events=unique_ev_ids,
                        shared_evidence=[f"Shared entity identifier: {ent_id}"],
                        confidence=0.91,
                        provenance={
                            "entity_id": ent_id,
                            "event_count": len(unique_ev_ids),
                        },
                        explanation=(
                            f"Entity {ent_id} is referenced in {len(unique_ev_ids)} separate Kumbh events ({', '.join(unique_ev_ids)}). "
                            "Correlated as a repeated association. Requires investigator review."
                        ),
                        action="Requires investigator review",
                    )
                )

        # ------------------------------------------------------------------- #
        # Cluster Type 3: Spatio-Temporal Bursts (Same zone within temporal window)
        # ------------------------------------------------------------------- #
        # Group events by zone
        events_by_zone: dict[str, list[KumbhEventModel]] = {}
        for ev in events:
            events_by_zone.setdefault(ev.zone, []).append(ev)

        # For each zone, sort chronologically and find clusters within immediate window
        window_seconds = self.temporal_config.immediate_seconds
        for zone, z_events in sorted(events_by_zone.items()):
            z_events.sort(key=lambda e: parse_iso_timestamp(e.ts))
            n = len(z_events)
            i = 0
            while i < n:
                burst = [z_events[i]]
                t_i = parse_iso_timestamp(z_events[i].ts)
                j = i + 1
                while j < n:
                    t_j = parse_iso_timestamp(z_events[j].ts)
                    diff = (t_j - t_i).total_seconds()
                    if diff <= window_seconds:
                        burst.append(z_events[j])
                        j += 1
                    else:
                        break
                # Only form cluster if there are >= 3 events in burst (e.g. fraud wave or incident surge)
                if len(burst) >= 3:
                    cluster_counter += 1
                    b_ids = [e.event_id for e in burst]
                    clusters.append(
                        KumbhClusterModel(
                            cluster_id=f"KUMBH-CLUST-{cluster_counter:04d}",
                            cluster_type="SPATIO_TEMPORAL_BURST",
                            member_events=b_ids,
                            shared_evidence=[
                                f"Zone: {zone}",
                                f"Temporal window: {window_seconds}s (immediate window)",
                                f"Event count: {len(b_ids)}",
                            ],
                            confidence=0.82,
                            provenance={
                                "zone": zone,
                                "start_time": burst[0].ts,
                                "end_time": burst[-1].ts,
                            },
                            explanation=(
                                f"Spatio-temporal burst detected in zone {zone}: {len(b_ids)} events occurred within "
                                f"{window_seconds // 3600} hour(s). Proximity alone does not indicate criminal activity. "
                                "Requires investigator review."
                            ),
                            action="Requires investigator review",
                        )
                    )
                    i = j  # advance past this cluster to avoid duplicates
                else:
                    i += 1

        return clusters

    # ----------------------------------------------------------------------- #
    # Full Execution Pipeline (Step 4M)
    # ----------------------------------------------------------------------- #
    def process_feed(
        self,
        raw_events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Process the complete Kumbh event feed:
        1. Ingest & validate events
        2. Correlate against graph entities
        3. Cluster events
        4. Assemble explainable investigator review portfolio
        """
        import time
        t0 = time.time()

        parsed_events = [parse_kumbh_event(e) for e in raw_events]
        t_ingest = time.time()

        # Correlate all events
        all_review_items: list[InvestigatorReviewObject] = []
        for ev in parsed_events:
            items = self.correlate_event(ev, parsed_events)
            all_review_items.extend(items)
        t_correlate = time.time()

        # Cluster events
        clusters = self.cluster_events(parsed_events)
        t_cluster = time.time()

        total_runtime = round(t_cluster - t0, 4)

        return {
            "total_events": len(parsed_events),
            "total_intelligence_items": len(all_review_items),
            "total_clusters": len(clusters),
            "intelligence_items": [item.model_dump() for item in all_review_items],
            "clusters": [c.model_dump() for c in clusters],
            "metrics": {
                "ingestion_runtime_seconds": round(t_ingest - t0, 4),
                "correlation_runtime_seconds": round(t_correlate - t_ingest, 4),
                "clustering_runtime_seconds": round(t_cluster - t_correlate, 4),
                "total_runtime_seconds": total_runtime,
            },
        }
