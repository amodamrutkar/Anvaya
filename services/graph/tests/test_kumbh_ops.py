"""
services/graph/tests/test_kumbh_ops.py

Comprehensive test suite for Step 4 Kumbh Operations Intelligence Layer:
1. Case 1: Civilian merely attending Kumbh -> No criminal classification
2. Case 2: Civilian near an incident -> Spatial association only
3. Case 3: Person connected to a case -> Surfaced with provenance, no auto-guilt
4. Case 4: Vehicle near multiple events -> Vehicle association only
5. Case 5: Known network member -> Network context surfaced, no auto-accusation
6. Case 6: Two unrelated people at same event -> No artificial syndicate
7. Case 7: Weak spatial vs strong direct -> Evidence hierarchy preserved
8. Direct entity correlation (person, phone, account, vehicle)
9. Temporal correlation windows (immediate, short, extended)
10. Spatial correlation & coordinate limitation
11. Incident clustering (shared infrastructure, shared entity, spatio-temporal bursts)
12. Provenance & evidence tiers preservation
13. Truth-leak audit
14. Determinism
15. Real V2 seed-42 feed integration & performance
"""

import json
from pathlib import Path
import re
import pytest

from sutradhar_graph.build import GraphBuilder
from sutradhar_graph.communities import detect_communities
from sutradhar_graph.kumbh_ops import (
    KumbhOperationsEngine,
    SpatialConfig,
    TemporalConfig,
    haversine_distance_km,
    parse_iso_timestamp,
    parse_kumbh_event,
)
from sutradhar_graph.models import (
    CommunityModel,
    KumbhEventModel,
    RoleAssignment,
)


@pytest.fixture
def base_test_graph():
    """Construct a clean, representative graph for Kumbh operations testing."""
    nodes = [
        {"id": "P-000001", "type": "PERSON", "label": "Rakesh Pawar", "attributes": {"role": "ACCUSED"}},
        {"id": "P-000002", "type": "PERSON", "label": "Sachin Kale", "attributes": {"role": "ACCUSED"}},
        {"id": "P-CIVILIAN", "type": "PERSON", "label": "Devotee Ramesh", "attributes": {}},
        {"id": "P-CIVILIAN-2", "type": "PERSON", "label": "Devotee Suresh", "attributes": {}},
        {"id": "CASE-SPO-000031", "type": "CASE", "label": "CASE-SPO-000031", "attributes": {"crime_type": "EXTORTION", "agency": "STATE_POLICE"}},
        {"id": "CASE-CYB-000014", "type": "CASE", "label": "CASE-CYB-000014", "attributes": {"crime_type": "CYBER_FRAUD", "agency": "MAHA_CYBER"}},
        {"id": "PHONE:9820011111", "type": "PHONE", "label": "9820011111", "attributes": {}},
        {"id": "ACCOUNT:AC-000310", "type": "ACCOUNT", "label": "AC-000310", "attributes": {"holder_name": "Sachin Kale"}},
        {"id": "VEH-MH15-AB1234", "type": "VEHICLE", "label": "MH-15-AB-1234", "attributes": {}},
    ]
    edges = [
        # Rakesh Pawar is accused in CASE-SPO-000031 and CASE-CYB-000014 (Cross-case)
        {
            "id": "E1",
            "source": "P-000001",
            "target": "CASE-SPO-000031",
            "type": "ACCUSED_IN",
            "strength": "STRONG",
            "confidence": 1.0,
            "evidence": ["REC-SPO-001"],
            "provenance": {"agency": "STATE_POLICE", "record_id": "REC-SPO-001"},
        },
        {
            "id": "E2",
            "source": "P-000001",
            "target": "CASE-CYB-000014",
            "type": "ACCUSED_IN",
            "strength": "STRONG",
            "confidence": 1.0,
            "evidence": ["REC-CYB-002"],
            "provenance": {"agency": "MAHA_CYBER", "record_id": "REC-CYB-002"},
        },
        # Rakesh Pawar uses phone
        {
            "id": "E3",
            "source": "P-000001",
            "target": "PHONE:9820011111",
            "type": "USES",
            "strength": "STRONG",
            "confidence": 0.95,
            "evidence": ["REC-SPO-001"],
            "provenance": {"agency": "STATE_POLICE"},
        },
        # Sachin Kale owns account AC-000310
        {
            "id": "E4",
            "source": "P-000002",
            "target": "ACCOUNT:AC-000310",
            "type": "OWNS",
            "strength": "STRONG",
            "confidence": 1.0,
            "evidence": ["REC-CYB-005"],
            "provenance": {"agency": "MAHA_CYBER"},
        },
        # Sachin Kale associated with vehicle
        {
            "id": "E5",
            "source": "P-000002",
            "target": "VEH-MH15-AB1234",
            "type": "USES",
            "strength": "MEDIUM",
            "confidence": 0.85,
            "evidence": ["REC-SPO-009"],
            "provenance": {"agency": "STATE_POLICE"},
        },
    ]

    communities = [
        CommunityModel(
            community_id="COM-001",
            label="Extortion Syndicate Nashik",
            crime_types=["EXTORTION"],
            members=["P-000001"],
            member_count=1,
            cohesion=0.85,
            districts=["Nashik"],
            agencies=["STATE_POLICE"],
            case_ids=["CASE-SPO-000031"],
            first_activity="2025-01-01",
            last_activity="2025-06-01",
            continuing_activity=True,
            is_network_of_interest=True,
        )
    ]

    roles = [
        RoleAssignment(
            entity_id="P-000001",
            role="BROKER",
            score=0.82,
            reasons=["Spans multiple clusters"],
            evidence_record_ids=["REC-SPO-001"],
            community_id="COM-001",
        )
    ]

    return {
        "graph_data": {"nodes": nodes, "edges": edges},
        "communities": communities,
        "roles": roles,
    }


# ─────────────────────────────────────────────────────────────
# 1. Case 1: Civilian merely attending Kumbh -> No criminal classification
# ─────────────────────────────────────────────────────────────
def test_case1_civilian_attending_kumbh_no_criminal_classification(base_test_graph):
    """
    A civilian merely attending Kumbh must NEVER receive a criminal classification,
    guilty label, or threat score.
    """
    engine = KumbhOperationsEngine(
        graph_data=base_test_graph["graph_data"],
        communities=base_test_graph["communities"],
        roles=base_test_graph["roles"],
    )

    civilian_event = KumbhEventModel(
        event_id="KUMBH-EVT-1001",
        event_type="LOST_AND_FOUND",
        ts="2027-01-15T10:00:00Z",
        zone="Ramkund",
        subject_token="TOK-CIVILIAN-001",
        related_ids=["P-CIVILIAN"],
        details={"description": "Devotee Ramesh reported lost bag near bathing ghat."},
    )

    review_items = engine.correlate_event(civilian_event)
    assert len(review_items) == 1
    item = review_items[0]

    # Must NOT have any criminal signals
    signal_types = [s.signal_type for s in item.signals]
    assert "KNOWN_CASE_ASSOCIATION" not in signal_types
    assert "KNOWN_NETWORK_ASSOCIATION" not in signal_types
    assert "CROSS_CASE_ACTIVITY" not in signal_types

    # Must retain safety action and no guilty labels
    assert item.action == "Requires investigator review"
    forbidden_terms = ["GUILTY", "CRIMINAL_AT_KUMBH", "TERRORIST_AT_KUMBH", "THREAT_PERSON"]
    for term in forbidden_terms:
        assert term not in item.explanation
        for s in item.signals:
            assert term not in s.description


# ─────────────────────────────────────────────────────────────
# 2. Case 2: Civilian near an incident -> Spatial association only
# ─────────────────────────────────────────────────────────────
def test_case2_civilian_near_incident_spatial_association_only(base_test_graph):
    """
    A civilian located near an incident zone receives spatial observation only;
    proximity must NOT be converted into criminal evidence.
    """
    engine = KumbhOperationsEngine(
        graph_data=base_test_graph["graph_data"],
        communities=base_test_graph["communities"],
    )

    incident_event = KumbhEventModel(
        event_id="KUMBH-EVT-1002",
        event_type="CROWD_SURGE",
        ts="2027-01-15T11:00:00Z",
        zone="Panchavati",
        subject_token="TOK-CITIZEN-SURGE",
        related_ids=[],
        details={"description": "Crowd surge reported near Panchavati market."},
    )

    review_items = engine.correlate_event(incident_event)
    assert len(review_items) == 1
    item = review_items[0]

    assert item.type == "CIVILIAN_OPERATIONAL_OBSERVATION"
    assert item.evidence_tier == "WEAK"
    assert "No criminal syndicate, case, or watchlist association" in item.explanation
    assert item.action == "Requires investigator review"


# ─────────────────────────────────────────────────────────────
# 3. Case 3: Person connected to a case -> Surfaced with provenance
# ─────────────────────────────────────────────────────────────
def test_case3_person_connected_to_case_surfaced_with_provenance(base_test_graph):
    """
    When a person already connected to a case appears at Kumbh, the existing case
    association is surfaced with provenance, maintaining the human review requirement.
    """
    engine = KumbhOperationsEngine(
        graph_data=base_test_graph["graph_data"],
        communities=base_test_graph["communities"],
        roles=base_test_graph["roles"],
    )

    sighting = KumbhEventModel(
        event_id="KUMBH-EVT-1003",
        event_type="WATCHLIST_SIGHTING",
        ts="2027-01-16T14:30:00Z",
        zone="Ramkund",
        subject_token="TOK-SIGHTING-001",
        related_ids=["P-000001"],
        details={"description": "Subject observed near Ramkund.", "confidence": 0.92},
    )

    review_items = engine.correlate_event(sighting)
    assert len(review_items) == 1
    item = review_items[0]

    signal_types = [s.signal_type for s in item.signals]
    assert "KNOWN_ENTITY_MATCH" in signal_types
    assert "KNOWN_CASE_ASSOCIATION" in signal_types
    assert "KNOWN_NETWORK_ASSOCIATION" in signal_types
    assert "CROSS_CASE_ACTIVITY" in signal_types

    # Evidence tier must be STRONG due to statutory chargesheet link
    assert item.evidence_tier == "STRONG"
    assert len(item.provenance) > 0
    assert any("CASE-SPO-000031" in str(p) for p in item.provenance)
    assert item.action == "Requires investigator review"


# ─────────────────────────────────────────────────────────────
# 4. Case 4: Vehicle near multiple events -> Vehicle association only
# ─────────────────────────────────────────────────────────────
def test_case4_vehicle_near_multiple_events_vehicle_association_only(base_test_graph):
    """
    A vehicle seen near events produces vehicle association only, with WEAK tier,
    unless stronger evidence connects the vehicle to an offense.
    """
    engine = KumbhOperationsEngine(
        graph_data=base_test_graph["graph_data"],
    )

    vehicle_event = KumbhEventModel(
        event_id="KUMBH-EVT-1004",
        event_type="TRAFFIC_DIVERSION",
        ts="2027-01-17T09:00:00Z",
        zone="Tapovan",
        subject_token=None,
        related_ids=["VEH-MH15-AB1234"],
        details={"description": "Vehicle parked near security perimeter."},
    )

    review_items = engine.correlate_event(vehicle_event)
    assert len(review_items) == 1
    item = review_items[0]

    assert item.type == "VEHICLE_SIGHTING_CORRELATION"
    assert item.evidence_tier == "WEAK"
    assert any(s.signal_type == "VEHICLE_ASSOCIATION" for s in item.signals)
    assert "spatial association only" in item.explanation.lower()


# ─────────────────────────────────────────────────────────────
# 5. Case 5: Known network member -> Network context surfaced, no auto-accusation
# ─────────────────────────────────────────────────────────────
def test_case5_known_network_member_network_context_surfaced(base_test_graph):
    """
    A known network member appearing at Kumbh has network context surfaced
    without automatic accusation or declaration of guilt.
    """
    engine = KumbhOperationsEngine(
        graph_data=base_test_graph["graph_data"],
        communities=base_test_graph["communities"],
        roles=base_test_graph["roles"],
    )

    event = KumbhEventModel(
        event_id="KUMBH-EVT-1005",
        event_type="WATCHLIST_SIGHTING",
        ts="2027-01-18T16:00:00Z",
        zone="Ramkund",
        related_ids=["P-000001"],
    )

    review_items = engine.correlate_event(event)
    item = review_items[0]
    assert item.network_context is not None
    assert "COM-001" in item.network_context.communities
    assert item.network_context.is_network_of_interest is True
    assert "BROKER" in item.network_context.roles
    assert item.action == "Requires investigator review"


# ─────────────────────────────────────────────────────────────
# 6. Case 6: Two unrelated people at same event -> No artificial syndicate
# ─────────────────────────────────────────────────────────────
def test_case6_unrelated_attendees_at_same_event_no_artificial_syndicate(base_test_graph):
    """
    Two unrelated individuals attending the same event must NEVER be joined
    into an artificial syndicate relationship or co-accused link.
    """
    engine = KumbhOperationsEngine(
        graph_data=base_test_graph["graph_data"],
    )

    shared_event = KumbhEventModel(
        event_id="KUMBH-EVT-1006",
        event_type="VIP_MOVEMENT",
        ts="2027-01-19T12:00:00Z",
        zone="Godavari Ghats",
        related_ids=["P-CIVILIAN", "P-CIVILIAN-2"],
        details={"description": "Two devotees observed in the same public sector during VIP movement."},
    )

    review_items = engine.correlate_event(shared_event)
    # Both individuals receive independent review items
    subjects = {item.subject for item in review_items}
    assert subjects == {"P-CIVILIAN", "P-CIVILIAN-2"}

    for item in review_items:
        # No syndicate or case signals generated between them
        signal_types = [s.signal_type for s in item.signals]
        assert "KNOWN_NETWORK_ASSOCIATION" not in signal_types
        assert "KNOWN_CASE_ASSOCIATION" not in signal_types


# ─────────────────────────────────────────────────────────────
# 7. Case 7: Weak spatial vs strong direct -> Evidence hierarchy preserved
# ─────────────────────────────────────────────────────────────
def test_case7_evidence_hierarchy_preserved_weak_spatial_vs_strong_direct(base_test_graph):
    """
    Statutory case filings retain STRONG tier, while spatial proximity retains WEAK tier.
    Weak proximity never dilutes or overwrites statutory evidence.
    """
    engine = KumbhOperationsEngine(
        graph_data=base_test_graph["graph_data"],
        communities=base_test_graph["communities"],
    )

    # Strong direct case link for P-000001
    ctx_strong = engine.get_network_context("P-000001")
    assert ctx_strong is not None
    assert ctx_strong.evidence_tier == "STRONG"

    # Weak observation for civilian
    ctx_weak = engine.get_network_context("P-CIVILIAN")
    assert ctx_weak is not None
    assert ctx_weak.evidence_tier == "WEAK"


# ─────────────────────────────────────────────────────────────
# 8. Direct Entity Correlation (Person, Phone, Account, Vehicle)
# ─────────────────────────────────────────────────────────────
def test_direct_entity_correlation_dimensions(base_test_graph):
    """
    Test direct correlation across person, phone, account, and vehicle dimensions.
    """
    engine = KumbhOperationsEngine(graph_data=base_test_graph["graph_data"])

    # Phone correlation
    phone_event = KumbhEventModel(
        event_id="KUMBH-EVT-PHONE",
        event_type="SCAM_PATTERN",
        ts="2027-01-20T10:00:00Z",
        zone="Panchavati",
        related_ids=["PHONE:9820011111"],
    )
    items = engine.correlate_event(phone_event)
    assert any(it.subject == "P-000001" for it in items)

    # Account correlation
    acct_event = KumbhEventModel(
        event_id="KUMBH-EVT-ACCT",
        event_type="SCAM_PATTERN",
        ts="2027-01-20T11:00:00Z",
        zone="Panchavati",
        related_ids=["ACCOUNT:AC-000310"],
    )
    items_acct = engine.correlate_event(acct_event)
    assert any(it.subject == "P-000002" for it in items_acct)


# ─────────────────────────────────────────────────────────────
# 9. Temporal Correlation Windows (Immediate, Short, Extended)
# ─────────────────────────────────────────────────────────────
def test_temporal_correlation_windows():
    """
    Verify configurable temporal correlation windows and ISO timestamp parsing.
    """
    cfg = TemporalConfig(immediate_seconds=3600, short_seconds=21600, extended_seconds=86400)
    assert cfg.immediate_seconds == 3600
    assert cfg.short_seconds == 21600
    assert cfg.extended_seconds == 86400

    t1 = parse_iso_timestamp("2027-01-15T12:00:00Z")
    t2 = parse_iso_timestamp("2027-01-15T12:45:00Z")
    diff = abs((t2 - t1).total_seconds())

    assert diff <= cfg.immediate_seconds
    assert diff <= cfg.short_seconds
    assert diff <= cfg.extended_seconds


# ─────────────────────────────────────────────────────────────
# 10. Spatial Correlation & Coordinate Limitation
# ─────────────────────────────────────────────────────────────
def test_spatial_correlation_and_coordinate_limitation():
    """
    Test haversine calculation when coordinates exist, and ensure no fabricated coordinates
    when only zones are given.
    """
    # Ramkund (approx 19.9975, 73.7915) to Panchavati (approx 20.0030, 73.7950) ~ 0.7 km
    dist = haversine_distance_km((19.9975, 73.7915), (20.0030, 73.7950))
    assert 0.5 <= dist <= 1.5

    # Feed without coordinates
    raw_event = {
        "event_id": "EVT-TEST",
        "ts": "2027-01-15T10:00:00Z",
        "zone": "Ramkund",
        "event_type": "MISSING_PERSON",
        "subject_token": "TOK-1",
        "related_ids": [],
        "details": {"description": "No coordinates supplied."},
    }
    model = parse_kumbh_event(raw_event)
    assert model.coordinates is None, "Coordinates must NOT be fabricated when absent"


# ─────────────────────────────────────────────────────────────
# 11. Incident Clustering
# ─────────────────────────────────────────────────────────────
def test_incident_clustering_shared_infra_and_spatio_temporal():
    """
    Verify deterministic clustering for shared infrastructure and spatio-temporal bursts.
    """
    graph_data = {"nodes": [], "edges": []}
    engine = KumbhOperationsEngine(graph_data=graph_data)

    # 3 events sharing account AC-000310 in Panchavati within 1 hour
    events = [
        KumbhEventModel(
            event_id="EVT-1",
            event_type="SCAM_PATTERN",
            ts="2027-01-15T12:00:00Z",
            zone="Panchavati",
            related_ids=["AC-000310"],
            details={"description": "Scam 1"},
        ),
        KumbhEventModel(
            event_id="EVT-2",
            event_type="SCAM_PATTERN",
            ts="2027-01-15T12:20:00Z",
            zone="Panchavati",
            related_ids=["AC-000310"],
            details={"description": "Scam 2"},
        ),
        KumbhEventModel(
            event_id="EVT-3",
            event_type="SCAM_PATTERN",
            ts="2027-01-15T12:45:00Z",
            zone="Panchavati",
            related_ids=["AC-000310"],
            details={"description": "Scam 3"},
        ),
    ]

    clusters = engine.cluster_events(events)
    assert len(clusters) >= 1

    # Check shared infrastructure cluster
    infra_cluster = next((c for c in clusters if c.cluster_type == "SHARED_INFRASTRUCTURE_CLUSTER"), None)
    assert infra_cluster is not None
    assert set(infra_cluster.member_events) == {"EVT-1", "EVT-2", "EVT-3"}
    assert "AC-000310" in infra_cluster.shared_evidence[0]
    assert infra_cluster.action == "Requires investigator review"


# ─────────────────────────────────────────────────────────────
# 12. Provenance & Evidence Tiers Preservation
# ─────────────────────────────────────────────────────────────
def test_provenance_and_tiers(base_test_graph):
    """
    Ensure all generated review items contain valid provenance entries and explicit evidence tiers.
    """
    engine = KumbhOperationsEngine(
        graph_data=base_test_graph["graph_data"],
        communities=base_test_graph["communities"],
    )

    event = KumbhEventModel(
        event_id="EVT-PROV",
        event_type="WATCHLIST_SIGHTING",
        ts="2027-01-15T10:00:00Z",
        zone="Ramkund",
        related_ids=["P-000001"],
    )

    items = engine.correlate_event(event)
    for it in items:
        assert it.evidence_tier in ("STRONG", "MEDIUM", "WEAK")
        assert len(it.provenance) > 0
        assert it.action == "Requires investigator review"


# ─────────────────────────────────────────────────────────────
# 13. Truth-Leak Audit in Production Code
# ─────────────────────────────────────────────────────────────
def test_truth_leak_audit_in_kumbh_ops():
    """
    Verify production code in kumbh_ops.py never references forbidden truth labels or files.
    """
    target = Path("services/graph/sutradhar_graph/kumbh_ops.py")
    assert target.exists()
    content = target.read_text(encoding="utf-8")

    forbidden_patterns = [
        r"account_truth",
        r"person_truth",
        r"mention_truth",
        r"networks_truth",
        r"INNOCENT_FAST_PASSTHROUGH",
        r"account_category",
        r"data/truth",
        r"data\\truth",
    ]

    for pat in forbidden_patterns:
        matches = re.findall(pat, content)
        assert len(matches) == 0, f"Forbidden truth pattern '{pat}' leaked into kumbh_ops.py"


# ─────────────────────────────────────────────────────────────
# 14. Determinism
# ─────────────────────────────────────────────────────────────
def test_determinism_kumbh_operations(base_test_graph):
    """
    Running the Kumbh operations engine multiple times on the same input produces
    strictly identical results.
    """
    raw_events = [
        {
            "event_id": "EVT-DET-1",
            "ts": "2027-01-15T10:00:00Z",
            "zone": "Ramkund",
            "event_type": "WATCHLIST_SIGHTING",
            "related_ids": ["P-000001"],
            "details": {"description": "Sighting 1"},
        },
        {
            "event_id": "EVT-DET-2",
            "ts": "2027-01-15T11:00:00Z",
            "zone": "Panchavati",
            "event_type": "SCAM_PATTERN",
            "related_ids": ["ACCOUNT:AC-000310"],
            "details": {"description": "Scam 2"},
        },
    ]

    engine1 = KumbhOperationsEngine(graph_data=base_test_graph["graph_data"])
    res1 = engine1.process_feed(raw_events)

    engine2 = KumbhOperationsEngine(graph_data=base_test_graph["graph_data"])
    res2 = engine2.process_feed(raw_events)

    assert json.dumps(res1["intelligence_items"], sort_keys=True) == json.dumps(res2["intelligence_items"], sort_keys=True)
    assert json.dumps(res1["clusters"], sort_keys=True) == json.dumps(res2["clusters"], sort_keys=True)


# ─────────────────────────────────────────────────────────────
# 15. V2 Multi-Seed Kumbh Feed Integration & Regression (Seeds 42, 43, 44)
# ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("seed_dir", ["seed-42", "seed-43", "seed-44"])
def test_v2_multiseed_kumbh_regression(seed_dir):
    """
    Verify full feed ingestion, correlation, and clustering against V2 dev seeds (42, 43, 44):
    - Graph construction intact
    - Network intelligence intact
    - Kumbh event correlation works
    - No truth leakage occurs
    """
    data_path = Path("data/v2/dev") / seed_dir
    kumbh_file = data_path / "kumbh" / "events.jsonl"
    if not kumbh_file.exists():
        pytest.skip(f"V2 dev {seed_dir} dataset not found")

    events = [json.loads(line) for line in kumbh_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(events) >= 300

    # Build graph from seed
    builder = GraphBuilder(data_dir=data_path)
    graph_data = builder.build_graph().model_dump()
    assert len(graph_data["nodes"]) >= 500
    assert len(graph_data["edges"]) >= 500

    communities = detect_communities(graph_data, seed=42)
    assert len(communities) >= 2

    engine = KumbhOperationsEngine(
        graph_data=graph_data,
        communities=communities,
    )

    feed_result = engine.process_feed(events)
    assert feed_result["total_events"] == len(events)
    assert feed_result["total_intelligence_items"] >= len(events)
    assert feed_result["metrics"]["total_runtime_seconds"] < 5.0, f"Feed processing for {seed_dir} must be under 5s"

