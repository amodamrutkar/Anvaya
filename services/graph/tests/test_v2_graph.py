"""
services/graph/tests/test_v2_graph.py

Comprehensive test suite for Step 3 Knowledge Graph + Network Intelligence:
1. Person → Phone
2. Person → Account
3. Person → Case
4. Multi-hop path
5. Bridge detection
6. Centrality
7. Community detection
8. Financial chain
9. Evidence/provenance
10. Evidence tier behavior
11. ER REVIEW does not merge entities
12. Possible duplicate entity hint
13. Role inference
14. LIKELY_DECEIVED
15. LIKELY_ORGANISER
16. Innocent pass-through hard negative
17. Decoy cluster protection
18. No truth dependency
19. V1 regression
"""

import json
from pathlib import Path
import pytest

from sutradhar_graph.bridges import detect_bridges
from sutradhar_graph.build import GraphBuilder
from sutradhar_graph.communities import detect_communities
from sutradhar_graph.mule import trace_financial_flow, trace_mule_chains
from sutradhar_graph.paths import (
    compute_centrality_metrics,
    find_connected_network,
    neighborhood,
    shortest_path,
)
from sutradhar_graph.roles import detect_roles
from sutradhar_graph.run import run_pipeline


@pytest.fixture(scope="module")
def v2_seed42_graph() -> dict:
    """Build graph from V2 dev seed-42 and ER scratch artifacts."""
    data_dir = Path("data/v2/dev/seed-42")
    er_dir = Path("scratch/er_seed42")
    assert data_dir.exists(), "data/v2/dev/seed-42 must exist"
    assert er_dir.exists(), "scratch/er_seed42 must exist"

    builder = GraphBuilder(data_dir=data_dir, er_dir=er_dir)
    builder.build_graph()
    return builder.to_dict()


# 1. Person → Phone
def test_v2_person_to_phone(v2_seed42_graph: dict):
    edges = [e for e in v2_seed42_graph["edges"] if e["type"] == "USES"]
    assert len(edges) > 100, "Must have USES edges connecting Person -> Phone"
    sample = edges[0]
    assert sample["strength"] == "STRONG"
    assert sample["target"].startswith("PHONE:")
    assert "source_agency" in sample.get("provenance", {})
    assert sample["provenance"]["relationship_type"] == "USES"


# 2. Person → Account
def test_v2_person_to_account(v2_seed42_graph: dict):
    edges = [e for e in v2_seed42_graph["edges"] if e["type"] == "OWNS" and e["target"].startswith("ACCOUNT:")]
    assert len(edges) > 0, "Must have OWNS edges connecting Person -> Account"
    sample = edges[0]
    assert sample["strength"] == "STRONG"
    assert sample["provenance"]["evidence_tier"] == "STRONG"


# 3. Person → Case
def test_v2_person_to_case(v2_seed42_graph: dict):
    edges = [e for e in v2_seed42_graph["edges"] if e["type"] == "ACCUSED_IN"]
    assert len(edges) > 1000, "Must have ACCUSED_IN edges connecting Person -> Case"
    sample = edges[0]
    assert sample["strength"] == "STRONG"
    assert sample["target"].startswith("CASE-")
    assert sample["provenance"]["source_record_id"] != ""


# 4. Multi-hop path
def test_v2_multi_hop_path(v2_seed42_graph: dict):
    person_nodes = [n["id"] for n in v2_seed42_graph["nodes"] if n["type"] == "PERSON"]
    assert len(person_nodes) > 10
    start_person = person_nodes[0]

    net = find_connected_network(v2_seed42_graph, start_person, max_depth=3)
    assert net["entity"] == start_person
    assert net["total_connected"] > 0
    assert len(net["paths"]) > 0
    # Verify each path has proper depth and edge structures
    for p in net["paths"][:5]:
        assert p["depth"] <= 3
        assert len(p["edges"]) == p["depth"]
        assert all("strength" in ed for ed in p["edges"])


# 5. Bridge detection
def test_v2_bridge_detection(v2_seed42_graph: dict):
    communities = detect_communities(v2_seed42_graph, seed=42)
    bridges = detect_bridges(v2_seed42_graph, communities)
    assert len(bridges) > 0, "Must identify bridge candidates"

    for b in bridges[:5]:
        assert b.indicator == "BRIDGE_CANDIDATE"
        assert b.action == "Requires investigator review"
        assert b.score >= 0.50
        assert len(b.reasons) > 0
        assert len(b.evidence_record_ids) > 0


# 6. Centrality
def test_v2_centrality_metrics(v2_seed42_graph: dict):
    metrics = compute_centrality_metrics(v2_seed42_graph)
    assert metrics["total_nodes"] == len(v2_seed42_graph["nodes"])
    assert metrics["total_edges"] == len(v2_seed42_graph["edges"])
    assert metrics["largest_component_size"] > 100
    assert len(metrics["top_degree"]) == 10
    assert len(metrics["top_betweenness"]) == 10


# 7. Community detection
def test_v2_community_detection(v2_seed42_graph: dict):
    communities = detect_communities(v2_seed42_graph, seed=42)
    assert len(communities) >= 5, "Expected at least 5 syndicates / communities"
    for comm in communities:
        assert comm.community_id.startswith("COM-")
        assert comm.member_count >= 4
        assert comm.cohesion > 0.0


# 8. Financial chain
def test_v2_financial_chain(v2_seed42_graph: dict):
    # Find an account with outbound transfers
    transfer_edges = [e for e in v2_seed42_graph["edges"] if e["type"] == "TRANSFERRED_TO"]
    assert len(transfer_edges) > 100
    source_acct = transfer_edges[0]["source"]

    flow = trace_financial_flow(v2_seed42_graph, source_acct, max_hops=3)
    assert flow.target == source_acct
    assert len(flow.connected_accounts) > 0
    assert flow.total_volume >= 0.0
    assert flow.layers_detected >= 1


# 9. Evidence / Provenance
def test_v2_evidence_provenance(v2_seed42_graph: dict):
    for edge in v2_seed42_graph["edges"][:500]:
        prov = edge.get("provenance", {})
        assert "source_agency" in prov or "reason" in prov, f"Missing provenance in edge: {edge}"
        assert edge.get("strength") in ("STRONG", "MEDIUM", "WEAK")
        assert edge.get("confidence", 0.0) > 0.0


# 10. Evidence tier behavior
def test_v2_evidence_tier_behavior():
    # Verify shortest path strictly prefers STRONG over MEDIUM and WEAK
    mock_nodes = [
        {"id": "P1", "type": "PERSON", "label": "P1"},
        {"id": "P2", "type": "PERSON", "label": "P2"},
        {"id": "P3", "type": "PERSON", "label": "P3"},
    ]
    # Strong 2-hop vs Weak 1-hop
    mock_edges = [
        {"id": "E1", "source": "P1", "target": "P2", "type": "CO_ACCUSED_WITH", "strength": "STRONG", "confidence": 1.0},
        {"id": "E2", "source": "P2", "target": "P3", "type": "CO_ACCUSED_WITH", "strength": "STRONG", "confidence": 1.0},
        {"id": "E3", "source": "P1", "target": "P3", "type": "LIVES_AT", "strength": "WEAK", "confidence": 0.5},
    ]
    graph = {"nodes": mock_nodes, "edges": mock_edges}
    res = shortest_path(graph, "P1", "P3")
    assert res["found"] is True
    # Should choose STRONG path P1 -> P2 -> P3 (cost 1 + 1 = 2) over WEAK shortcut (cost 20)
    assert res["path"] == ["P1", "P2", "P3"]


# 11. ER REVIEW does NOT merge entities
def test_v2_er_review_does_not_merge(v2_seed42_graph: dict):
    dup_edges = [e for e in v2_seed42_graph["edges"] if e["type"] == "POSSIBLE_DUPLICATE_ENTITY"]
    assert len(dup_edges) > 0, "ER REVIEW pairs must be exposed as POSSIBLE_DUPLICATE_ENTITY edges"
    # Verify that source and target remain two separate nodes in graph
    nodes_map = {n["id"]: n for n in v2_seed42_graph["nodes"]}
    for e in dup_edges[:20]:
        src, tgt = e["source"], e["target"]
        assert src != tgt, "Duplicate entity link cannot self-loop"
        assert src in nodes_map, f"Entity {src} missing from nodes"
        assert tgt in nodes_map, f"Entity {tgt} missing from nodes"


# 12. Possible duplicate entity hint
def test_v2_possible_duplicate_entity_hint(v2_seed42_graph: dict):
    dup_edges = [e for e in v2_seed42_graph["edges"] if e["type"] == "POSSIBLE_DUPLICATE_ENTITY"]
    sample = dup_edges[0]
    assert sample["strength"] == "MEDIUM"
    assert sample["provenance"]["relationship_type"] == "POSSIBLE_DUPLICATE_ENTITY"
    assert sample["provenance"]["evidence_tier"] == "MEDIUM"


# 13. Role inference
def test_v2_role_inference(v2_seed42_graph: dict):
    communities = detect_communities(v2_seed42_graph, seed=42)
    roles = detect_roles(v2_seed42_graph, communities)
    assert len(roles) > 0

    role_types = {r.role for r in roles}
    assert "KINGPIN_CANDIDATE" in role_types
    assert "BROKER" in role_types or "CROSS_CRIME_BROKER" in role_types
    assert "RECRUITER" in role_types or "CONTROLLER" in role_types

    for r in roles:
        assert r.action == "Requires investigator review"
        # Never output words of conviction
        text = " ".join(r.reasons).lower()
        assert "convicted" not in text and "guilty" not in text and "criminal" not in text


# 14. LIKELY_DECEIVED
def test_v2_likely_deceived_classification(v2_seed42_graph: dict):
    chains = trace_mule_chains(v2_seed42_graph)
    assert len(chains) > 0
    accounts = chains[0].accounts
    deceived = [a for a in accounts if a.classification == "LIKELY_DECEIVED"]
    assert len(deceived) > 0
    for a in deceived:
        assert a.layer <= 2
        assert len(a.reasons) > 0


# 15. LIKELY_ORGANISER
def test_v2_likely_organiser_classification(v2_seed42_graph: dict):
    chains = trace_mule_chains(v2_seed42_graph)
    assert len(chains) > 0
    accounts = chains[0].accounts
    organisers = [a for a in accounts if a.classification == "LIKELY_ORGANISER"]
    assert len(organisers) > 0
    for a in organisers:
        assert a.layer >= 2 or a.fan_out >= 2
        assert any("organiser" in r.lower() for r in a.reasons)


# 16. Innocent pass-through hard negative
def test_v2_innocent_passthrough_guard(v2_seed42_graph: dict):
    # Find accounts categorized as INNOCENT_FAST_PASSTHROUGH in node attributes
    nodes_map = {n["id"]: n for n in v2_seed42_graph["nodes"]}
    innocent_nodes = {
        nid for nid, n in nodes_map.items()
        if n.get("attributes", {}).get("account_category") == "INNOCENT_FAST_PASSTHROUGH"
    }

    chains = trace_mule_chains(v2_seed42_graph)
    assert len(chains) > 0
    accounts = chains[0].accounts

    # Check how many innocent nodes received LIKELY_ORGANISER
    wrongly_flagged = [
        a for a in accounts
        if f"ACCOUNT:{a.account_key}" in innocent_nodes and a.classification == "LIKELY_ORGANISER"
    ]
    assert len(wrongly_flagged) == 0, f"Found {len(wrongly_flagged)} innocent accounts wrongly marked LIKELY_ORGANISER"


# 17. Decoy cluster protection
def test_v2_decoy_cluster_protection():
    # 5 residents sharing a chawl address with 0 case linkages
    mock_nodes = [
        {"id": f"P{i}", "type": "PERSON", "label": f"Resident {i}"} for i in range(5)
    ]
    mock_nodes.append({"id": "ADDR:Worli_Chawl", "type": "ADDRESS", "label": "Worli Chawl"})
    mock_edges = [
        {"id": f"E{i}", "source": f"P{i}", "target": "ADDR:Worli_Chawl", "type": "LIVES_AT", "strength": "WEAK", "confidence": 0.5, "evidence": ["REC-1"]}
        for i in range(5)
    ]
    # Also add weak shared phone
    mock_nodes.append({"id": "PHONE:9999999999", "type": "PHONE", "label": "9999999999"})
    for i in range(5):
        mock_edges.append({"id": f"EP{i}", "source": f"P{i}", "target": "PHONE:9999999999", "type": "USES", "strength": "STRONG", "confidence": 1.0, "evidence": ["REC-1"]})

    graph = {"nodes": mock_nodes, "edges": mock_edges}
    comms = detect_communities(graph, hub_degree_threshold=20, min_community_size=4)
    assert len(comms) > 0, "Decoy cluster was formed"
    for comm in comms:
        assert len(comm.case_ids) == 0
        assert comm.is_network_of_interest is False, f"Decoy community {comm.community_id} wrongly flagged as network of interest"


# 18. No truth dependency in production code
def test_v2_no_truth_dependency():
    import re
    prod_files = [
        Path("services/graph/sutradhar_graph/build.py"),
        Path("services/graph/sutradhar_graph/bridges.py"),
        Path("services/graph/sutradhar_graph/communities.py"),
        Path("services/graph/sutradhar_graph/roles.py"),
        Path("services/graph/sutradhar_graph/mule.py"),
        Path("services/graph/sutradhar_graph/paths.py"),
        Path("services/graph/sutradhar_graph/run.py"),
    ]
    for p in prod_files:
        content = p.read_text(encoding="utf-8")
        assert "data/truth" not in content and "data\\truth" not in content, f"Truth data leak in {p}"


# 19. V1 Regression
def test_v2_v1_regression(tmp_path: Path):
    from sutradhar_er.run import run_pipeline as run_er_pipeline
    data_dir = Path("data/v1")
    er_out = tmp_path / "v1_er"
    graph_out = tmp_path / "v1_graph"
    run_er_pipeline(data_dir=data_dir, out_dir=er_out, verbose=False)
    summary = run_pipeline(data_dir=data_dir, er_dir=er_out, out_dir=graph_out)
    assert summary["status"] == "SUCCESS"
    assert summary["total_nodes"] > 500
    assert summary["total_edges"] >= 400
    assert summary["total_communities"] >= 2
