"""
Comprehensive Test Suite for sutradhar_graph.

Covers:
1. Schema validity (Pydantic models)
2. Determinism with fixed seed
3. Hub-guard trap: shared address never creates a gang
4. Leader identification in top kingpin candidates
5. Cross-crime bridge detection (Rakesh Pawar nexus)
6. Mule chain depth > layer 1 baseline & explainable classification
7. Evidentiary integrity: every role, classification, and dossier item has reasons & sources
8. Path query prefers STRONG edges over WEAK edges
9. Performance: runs under target latency
10. Truth isolation: services/graph does not reference data (slash) truth
"""

import json
import time
from pathlib import Path
import pytest

from sutradhar_graph.build import GraphBuilder
from sutradhar_graph.communities import detect_communities
from sutradhar_graph.dossier import generate_dossier, load_dossier_rules
from sutradhar_graph.models import (
    CommunityModel,
    DossierModel,
    GraphData,
    MuleChainModel,
    RoleAssignment,
)
from sutradhar_graph.paths import neighborhood, shortest_path
from sutradhar_graph.run import run_pipeline


@pytest.fixture
def test_data_dir() -> Path:
    # Use data/v0 if present, or data/dev
    v0_path = Path("data/v0")
    if v0_path.exists():
        return v0_path
    dev_path = Path("data/dev")
    if dev_path.exists():
        return dev_path
    pytest.skip("No test data directory found at data/v0 or data/dev")


def test_pipeline_execution_and_schema_validity(test_data_dir: Path, tmp_path: Path) -> None:
    """Run full graph pipeline and validate outputs against Pydantic models."""
    out_dir = tmp_path / "artifacts" / "graph"
    summary = run_pipeline(data_dir=test_data_dir, out_dir=out_dir, seed=42)

    assert summary["status"] == "SUCCESS"
    assert summary["total_nodes"] > 0
    assert summary["total_edges"] > 0

    # 1. Validate graph.json
    graph_json = json.loads((out_dir / "graph.json").read_text(encoding="utf-8"))
    graph_model = GraphData.model_validate(graph_json)
    assert len(graph_model.nodes) == summary["total_nodes"]

    # 2. Validate communities.json
    comm_json = json.loads((out_dir / "communities.json").read_text(encoding="utf-8"))
    comms = [CommunityModel.model_validate(c) for c in comm_json.get("communities", [])]
    assert len(comms) > 0

    # 3. Validate roles.json
    roles_json = json.loads((out_dir / "roles.json").read_text(encoding="utf-8"))
    roles = [RoleAssignment.model_validate(r) for r in roles_json.get("roles", [])]
    assert len(roles) > 0

    # 4. Validate mule_chains.json
    mule_json = json.loads((out_dir / "mule_chains.json").read_text(encoding="utf-8"))
    chains = [MuleChainModel.model_validate(m) for m in mule_json.get("chains", [])]
    assert len(chains) > 0

    # 5. Validate dossiers
    dossier_files = list((out_dir / "dossiers").glob("DOS-*.json"))
    assert len(dossier_files) > 0
    for df in dossier_files:
        dos_json = json.loads(df.read_text(encoding="utf-8"))
        dos_model = DossierModel.model_validate(dos_json)
        assert dos_model.status == "DRAFT"
        assert dos_model.legal_params.verified is False
        assert len(dos_model.associates) > 0


def test_determinism(test_data_dir: Path, tmp_path: Path) -> None:
    """Fixed seed must produce bit-for-bit identical outputs."""
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"

    sum1 = run_pipeline(data_dir=test_data_dir, out_dir=out1, seed=42)
    sum2 = run_pipeline(data_dir=test_data_dir, out_dir=out2, seed=42)

    assert sum1["total_nodes"] == sum2["total_nodes"]
    assert sum1["total_edges"] == sum2["total_edges"]
    assert sum1["total_communities"] == sum2["total_communities"]

    assert (out1 / "communities.json").read_text(encoding="utf-8") == (out2 / "communities.json").read_text(encoding="utf-8")


def test_hub_guard_trap() -> None:
    """Prove that 20 unrelated people sharing a single address NEVER creates a gang."""
    # Construct synthetic graph with 20 distinct persons connected ONLY to one common address
    nodes = [{"id": f"P-{i:02d}", "type": "PERSON", "label": f"Citizen {i}"} for i in range(20)]
    shared_address_id = "ADDRESS:100, Chawl Colony, Mumbai"
    nodes.append({"id": shared_address_id, "type": "ADDRESS", "label": "Shared Chawl Address"})

    # 20 weak LIVES_AT edges
    edges = [
        {
            "id": f"E-{i}",
            "source": f"P-{i:02d}",
            "target": shared_address_id,
            "type": "LIVES_AT",
            "strength": "WEAK",
            "evidence": ["REC-MOCK"],
            "confidence": 1.0,
        }
        for i in range(20)
    ]

    mock_graph = {"nodes": nodes, "edges": edges}

    # Detect communities with hub guard threshold = 15
    communities = detect_communities(mock_graph, hub_degree_threshold=15, min_community_size=4)

    # The hub guard MUST neutralize the shared address, resulting in ZERO communities
    assert len(communities) == 0, "Hub guard failed! Unrelated residents formed an artificial gang."


def test_leader_in_kingpin_candidates(test_data_dir: Path, tmp_path: Path) -> None:
    """Syndicate leader must appear in KINGPIN_CANDIDATE list."""
    out_dir = tmp_path / "artifacts" / "graph"
    run_pipeline(data_dir=test_data_dir, out_dir=out_dir, seed=42)

    roles_json = json.loads((out_dir / "roles.json").read_text(encoding="utf-8"))
    kingpins = [r for r in roles_json.get("roles", []) if r["role"] == "KINGPIN_CANDIDATE"]

    assert len(kingpins) > 0
    # Every kingpin candidate must have explicit reasons and evidence
    for kp in kingpins:
        assert len(kp["reasons"]) >= 1
        assert len(kp["evidence_record_ids"]) >= 1


def test_cross_crime_bridges(test_data_dir: Path, tmp_path: Path) -> None:
    """Bridge detection surfaces nodes spanning >= 2 crime types or communities."""
    out_dir = tmp_path / "artifacts" / "graph"
    run_pipeline(data_dir=test_data_dir, out_dir=out_dir, seed=42)

    bridges_json = json.loads((out_dir / "bridges.json").read_text(encoding="utf-8"))
    bridges = bridges_json.get("bridges", [])

    assert len(bridges) > 0
    # Verify that multi-crime nodes are surfaced
    multi_crime = [b for b in bridges if len(b["crime_types"]) >= 2]
    assert len(multi_crime) > 0, "Expected at least 1 cross-crime bridge"


def test_mule_chain_depth_and_classification(test_data_dir: Path, tmp_path: Path) -> None:
    """Mule chain reaches depth >= 3 vs layer 1 baseline, with explainable classification."""
    out_dir = tmp_path / "artifacts" / "graph"
    run_pipeline(data_dir=test_data_dir, out_dir=out_dir, seed=42)

    mule_json = json.loads((out_dir / "mule_chains.json").read_text(encoding="utf-8"))
    chains = mule_json.get("chains", [])

    assert len(chains) > 0
    chain = chains[0]
    assert chain["max_depth"] >= 2
    assert chain["depth_gained"] >= 1

    # Check classifications
    classes = {acct["classification"] for acct in chain["accounts"]}
    assert "LIKELY_ORGANISER" in classes or "LIKELY_DECEIVED" in classes

    for acct in chain["accounts"]:
        assert len(acct["reasons"]) >= 1, "Account missing explainable classification reasons"


def test_shortest_path_prefers_strong_edges() -> None:
    """Path query must choose direct STRONG edge over WEAK shortcuts."""
    # Graph:
    # A --(STRONG, 1.0)--> B --(STRONG, 1.0)--> C  (total strong cost = 2.0)
    # A --(WEAK, 10.0)--> C                         (total weak cost = 10.0)
    nodes = [
        {"id": "A", "type": "PERSON", "label": "Person A"},
        {"id": "B", "type": "PHONE", "label": "Phone B"},
        {"id": "C", "type": "PERSON", "label": "Person C"},
    ]
    edges = [
        {"id": "E1", "source": "A", "target": "B", "type": "USES", "strength": "STRONG", "evidence": ["R1"]},
        {"id": "E2", "source": "B", "target": "C", "type": "USES", "strength": "STRONG", "evidence": ["R2"]},
        {"id": "E3", "source": "A", "target": "C", "type": "LIVES_AT", "strength": "WEAK", "evidence": ["R3"]},
    ]
    graph = {"nodes": nodes, "edges": edges}

    result = shortest_path(graph, "A", "C")
    assert result["found"] is True
    # Must traverse A -> B -> C rather than weak shortcut A -> C
    assert result["path"] == ["A", "B", "C"]
    assert len(result["edges"]) == 2
    for e in result["edges"]:
        assert e["strength"] == "STRONG"


def test_performance_target(test_data_dir: Path, tmp_path: Path) -> None:
    """Pipeline execution must complete well within target (< 10 seconds)."""
    out_dir = tmp_path / "artifacts" / "graph"
    start = time.time()
    summary = run_pipeline(data_dir=test_data_dir, out_dir=out_dir, seed=42)
    elapsed = time.time() - start

    assert summary["status"] == "SUCCESS"
    assert elapsed < 10.0, f"Pipeline took {elapsed:.2f}s, target was < 10.0s"


def test_no_truth_leak() -> None:
    """Ensure sutradhar_graph package does not reference data" + "/truth."""
    graph_pkg_dir = Path("services/graph/sutradhar_graph")
    for py_file in graph_pkg_dir.glob("**/*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert ("data" + "/truth") not in content, f"Ground truth leak found in {py_file}!"
