"""
services/graph/tests/test_step36_regression.py

Dedicated regression suite for Step 3.6 fixes:
1. Ground-truth leakage elimination (no account_category / generator labels in production)
2. Organiser false-positive flood resolution (ordinary accounts protected, coordination required)
3. Bridge candidate saturation and ranking resolution (PERSON prioritization, victim exclusion, infrastructure penalty)
4. Preservation of explainability, confidence, indicators, evidence, and safety actions
"""

import json
from pathlib import Path
import re
import pytest

from sutradhar_graph.bridges import detect_bridges
from sutradhar_graph.build import GraphBuilder
from sutradhar_graph.communities import detect_communities
from sutradhar_graph.models import CommunityModel
from sutradhar_graph.mule import trace_mule_chains
from sutradhar_graph.run import run_pipeline


def test_no_truth_leakage_in_graph_production_code():
    """Verify production graph code never imports or references truth files or generator labels."""
    prod_dir = Path("services/graph/sutradhar_graph")
    forbidden_patterns = [
        r"account_truth",
        r"person_truth",
        r"mention_truth",
        r"networks_truth",
        r"INNOCENT_FAST_PASSTHROUGH",
        r"account_category",
    ]

    for py_file in prod_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for pat in forbidden_patterns:
            matches = re.findall(pat, content)
            assert len(matches) == 0, f"Found forbidden truth reference '{pat}' in production file {py_file}"


def test_mule_logic_without_account_category():
    """Test mule classification operates purely on observable graph evidence with no generator fields."""
    mock_nodes = [
        {"id": "ACCOUNT:ACC-INTAKE", "type": "ACCOUNT", "label": "ACC-INTAKE", "attributes": {"complaint_count": 3, "holder_name": "Citizen Deceived"}},
        {"id": "ACCOUNT:ACC-LAYER2", "type": "ACCOUNT", "label": "ACC-LAYER2", "attributes": {"complaint_count": 0, "holder_name": "Master Operative"}},
        {"id": "ACCOUNT:ACC-LAYER3A", "type": "ACCOUNT", "label": "ACC-LAYER3A", "attributes": {"complaint_count": 0, "holder_name": "Cash Out 1"}},
        {"id": "ACCOUNT:ACC-LAYER3B", "type": "ACCOUNT", "label": "ACC-LAYER3B", "attributes": {"complaint_count": 0, "holder_name": "Cash Out 2"}},
        {"id": "P-OPERATIVE", "type": "PERSON", "label": "Master Operative", "attributes": {"roles": ["ACCUSED"]}},
        {"id": "P-DECEIVED", "type": "PERSON", "label": "Citizen Deceived", "attributes": {"roles": ["ACCUSED"]}},
        {"id": "CASE-1", "type": "CASE", "label": "CASE-1", "attributes": {"crime_type": "CYBER_FRAUD"}},
        {"id": "CASE-2", "type": "CASE", "label": "CASE-2", "attributes": {"crime_type": "EXTORTION"}},
    ]
    mock_edges = [
        # Transfers
        {"id": "T1", "source": "ACCOUNT:ACC-INTAKE", "target": "ACCOUNT:ACC-LAYER2", "type": "TRANSFERRED_TO", "attributes": {"amount": 50000.0, "ts": "2025-06-01T12:00:00Z"}},
        {"id": "T2", "source": "ACCOUNT:ACC-LAYER2", "target": "ACCOUNT:ACC-LAYER3A", "type": "TRANSFERRED_TO", "attributes": {"amount": 24000.0, "ts": "2025-06-01T12:15:00Z"}},
        {"id": "T3", "source": "ACCOUNT:ACC-LAYER2", "target": "ACCOUNT:ACC-LAYER3B", "type": "TRANSFERRED_TO", "attributes": {"amount": 24000.0, "ts": "2025-06-01T12:20:00Z"}},
        # Ownership
        {"id": "O1", "source": "P-DECEIVED", "target": "ACCOUNT:ACC-INTAKE", "type": "OWNS", "evidence": ["REC-1"]},
        {"id": "O2", "source": "P-OPERATIVE", "target": "ACCOUNT:ACC-LAYER2", "type": "OWNS", "evidence": ["REC-2"]},
        # Operative criminal coordination
        {"id": "C1", "source": "P-OPERATIVE", "target": "CASE-1", "type": "ACCUSED_IN", "evidence": ["REC-2"]},
        {"id": "C2", "source": "P-OPERATIVE", "target": "CASE-2", "type": "ACCUSED_IN", "evidence": ["REC-3"]},
        # Deceived only in single case
        {"id": "C3", "source": "P-DECEIVED", "target": "CASE-1", "type": "ACCUSED_IN", "evidence": ["REC-1"]},
    ]

    graph = {"nodes": mock_nodes, "edges": mock_edges}
    chains = trace_mule_chains(graph)
    assert len(chains) == 1
    accts = {a.account_key: a for a in chains[0].accounts}

    # ACC-INTAKE must be LIKELY_DECEIVED
    assert accts["ACC-INTAKE"].classification == "LIKELY_DECEIVED"
    assert accts["ACC-INTAKE"].confidence >= 0.80
    assert "Requires investigator review" in accts["ACC-INTAKE"].action
    assert len(accts["ACC-INTAKE"].indicators) > 0

    # ACC-LAYER2 has multi-case coordination + dispersion -> LIKELY_ORGANISER
    assert accts["ACC-LAYER2"].classification == "LIKELY_ORGANISER"
    assert accts["ACC-LAYER2"].confidence >= 0.80
    assert any("CROSS_CASE" in ind for ind in accts["ACC-LAYER2"].indicators)
    assert any("CROSS_CRIME" in ind for ind in accts["ACC-LAYER2"].indicators)
    assert accts["ACC-LAYER2"].action == "Requires investigator review"


def test_ordinary_accounts_not_flagged_as_organisers():
    """Prove high-degree ordinary civilian, merchant, and salary accounts are not flagged as organisers."""
    mock_nodes = [
        {"id": "ACCOUNT:ACC-HIGH-DEG", "type": "ACCOUNT", "label": "ACC-HIGH-DEG", "attributes": {"complaint_count": 0, "holder_name": "Ramesh Citizen"}},
        {"id": "ACCOUNT:ACC-MERCHANT", "type": "ACCOUNT", "label": "ACC-MERCHANT", "attributes": {"complaint_count": 0, "holder_name": "Deepak Traders (Kirana Store)"}},
        {"id": "ACCOUNT:ACC-SALARY", "type": "ACCOUNT", "label": "ACC-SALARY", "attributes": {"complaint_count": 0, "holder_name": "Sunita Corporate Employee"}},
        {"id": "P-RAMESH", "type": "PERSON", "label": "Ramesh Citizen", "attributes": {"roles": []}},
        {"id": "P-DEEPAK", "type": "PERSON", "label": "Deepak Traders", "attributes": {"roles": []}},
        {"id": "P-SUNITA", "type": "PERSON", "label": "Sunita Corporate Employee", "attributes": {"roles": []}},
    ]
    # Add 10 downstream civilian accounts
    for i in range(10):
        mock_nodes.append({"id": f"ACCOUNT:DOWN-{i}", "type": "ACCOUNT", "label": f"DOWN-{i}", "attributes": {"complaint_count": 0, "holder_name": f"Citizen {i}"}})

    mock_edges = [
        {"id": "O1", "source": "P-RAMESH", "target": "ACCOUNT:ACC-HIGH-DEG", "type": "OWNS"},
        {"id": "O2", "source": "P-DEEPAK", "target": "ACCOUNT:ACC-MERCHANT", "type": "OWNS"},
        {"id": "O3", "source": "P-SUNITA", "target": "ACCOUNT:ACC-SALARY", "type": "OWNS"},
    ]
    # Inflow into high degree
    mock_edges.append({"id": "TI-1", "source": "ACCOUNT:DOWN-0", "target": "ACCOUNT:ACC-HIGH-DEG", "type": "TRANSFERRED_TO", "attributes": {"amount": 50000.0, "ts": "2025-06-01T10:00:00Z"}})
    mock_edges.append({"id": "TI-2", "source": "ACCOUNT:DOWN-0", "target": "ACCOUNT:ACC-MERCHANT", "type": "TRANSFERRED_TO", "attributes": {"amount": 5000.0, "ts": "2025-06-01T10:00:00Z"}})
    mock_edges.append({"id": "TI-3", "source": "ACCOUNT:DOWN-0", "target": "ACCOUNT:ACC-SALARY", "type": "TRANSFERRED_TO", "attributes": {"amount": 90000.0, "ts": "2025-06-01T10:00:00Z"}})

    # High-degree dispersal to 8 accounts
    for i in range(1, 9):
        mock_edges.append({"id": f"TH-{i}", "source": "ACCOUNT:ACC-HIGH-DEG", "target": f"ACCOUNT:DOWN-{i}", "type": "TRANSFERRED_TO", "attributes": {"amount": 1000.0, "ts": "2025-06-01T11:00:00Z"}})
    # Merchant sweep
    mock_edges.append({"id": "TM-1", "source": "ACCOUNT:ACC-MERCHANT", "target": "ACCOUNT:DOWN-9", "type": "TRANSFERRED_TO", "attributes": {"amount": 4800.0, "ts": "2025-06-01T10:20:00Z"}})

    graph = {"nodes": mock_nodes, "edges": mock_edges}
    chains = trace_mule_chains(graph)
    assert len(chains) > 0
    accts = {a.account_key: a for a in chains[0].accounts}

    # None of these accounts must EVER be LIKELY_ORGANISER
    assert accts["ACC-HIGH-DEG"].classification != "LIKELY_ORGANISER"
    assert accts["ACC-MERCHANT"].classification != "LIKELY_ORGANISER"
    assert accts["ACC-SALARY"].classification != "LIKELY_ORGANISER"

    assert accts["ACC-HIGH-DEG"].classification == "UNCERTAIN"
    assert accts["ACC-MERCHANT"].classification == "UNCERTAIN"
    assert accts["ACC-SALARY"].classification == "UNCERTAIN"

    # Verify observable indicators and investigator review action
    for key in ["ACC-HIGH-DEG", "ACC-MERCHANT", "ACC-SALARY"]:
        assert len(accts[key].indicators) > 0
        assert accts[key].action == "Requires investigator review"
        assert accts[key].confidence > 0.0


def test_bridge_person_prioritization_and_victim_exclusion():
    """Prove PERSON nodes outrank infrastructure and civilian victims are excluded from bridges."""
    mock_nodes = [
        {"id": "P-BROKER", "type": "PERSON", "label": "Arjun Syndicate Bridge", "attributes": {"roles": ["ACCUSED"]}},
        {"id": "P-VICTIM", "type": "PERSON", "label": "Complainant Citizen", "attributes": {"roles": ["VICTIM"]}},
        {"id": "PHONE:9999999999", "type": "PHONE", "label": "9999999999"},
        {"id": "VEHICLE:MH01AA1111", "type": "VEHICLE", "label": "MH01AA1111"},
        {"id": "CASE-C1", "type": "CASE", "label": "CASE-C1", "attributes": {"crime_type": "CYBER_FRAUD"}},
        {"id": "CASE-C2", "type": "CASE", "label": "CASE-C2", "attributes": {"crime_type": "EXTORTION"}},
        {"id": "P-ASSOC1", "type": "PERSON", "label": "Associate Gang 1", "attributes": {"roles": ["ACCUSED"]}},
        {"id": "P-ASSOC2", "type": "PERSON", "label": "Associate Gang 2", "attributes": {"roles": ["ACCUSED"]}},
    ]
    mock_edges = [
        # Broker connects 2 distinct crime cases
        {"id": "E1", "source": "P-BROKER", "target": "CASE-C1", "type": "ACCUSED_IN", "evidence": ["R1", "R2"]},
        {"id": "E2", "source": "P-BROKER", "target": "CASE-C2", "type": "ACCUSED_IN", "evidence": ["R3", "R4"]},
        # Co-accused ties bridging two communities
        {"id": "E3", "source": "P-BROKER", "target": "P-ASSOC1", "type": "CO_ACCUSED_WITH", "evidence": ["R1"]},
        {"id": "E4", "source": "P-BROKER", "target": "P-ASSOC2", "type": "CO_ACCUSED_WITH", "evidence": ["R3"]},
        # Infrastructure uses
        {"id": "E5", "source": "P-BROKER", "target": "PHONE:9999999999", "type": "USES", "evidence": ["R1"]},
        {"id": "E6", "source": "P-ASSOC1", "target": "PHONE:9999999999", "type": "USES", "evidence": ["R2"]},
        {"id": "E7", "source": "P-BROKER", "target": "VEHICLE:MH01AA1111", "type": "OWNS", "evidence": ["R3"]},
        # Complainant reports both cases as a VICTIM
        {"id": "EV1", "source": "P-VICTIM", "target": "CASE-C1", "type": "VICTIM_IN", "evidence": ["R1"]},
        {"id": "EV2", "source": "P-VICTIM", "target": "CASE-C2", "type": "VICTIM_IN", "evidence": ["R3"]},
    ]

    mock_comms = [
        CommunityModel(
            community_id="COMM-1",
            label="COMM-1",
            crime_types=["CYBER_FRAUD"],
            members=["P-ASSOC1", "P-BROKER"],
            member_count=2,
            cohesion=0.8,
            districts=["Mumbai"],
            agencies=["MAHA_CYBER"],
            case_ids=["CASE-C1"],
            first_activity="2025-01-01",
            last_activity="2025-06-01",
            continuing_activity=False,
            timeline=[],
        ),
        CommunityModel(
            community_id="COMM-2",
            label="COMM-2",
            crime_types=["EXTORTION"],
            members=["P-ASSOC2"],
            member_count=1,
            cohesion=0.8,
            districts=["Thane"],
            agencies=["STATE_POLICE"],
            case_ids=["CASE-C2"],
            first_activity="2025-01-01",
            last_activity="2025-06-01",
            continuing_activity=False,
            timeline=[],
        ),
    ]

    graph = {"nodes": mock_nodes, "edges": mock_edges}
    bridges = detect_bridges(graph, mock_comms)

    assert len(bridges) > 0
    # Rank 1 MUST be the PERSON broker
    top_bridge = bridges[0]
    assert top_bridge.node_id == "P-BROKER"
    assert top_bridge.node_type == "PERSON"
    assert top_bridge.score >= 0.90

    # Complainant victim MUST be excluded completely
    victim_bridges = [b for b in bridges if b.node_id == "P-VICTIM"]
    assert len(victim_bridges) == 0, "Victim complainant was wrongly qualified as a criminal bridge"

    # Infrastructure score must be capped below human operative
    infra_bridges = [b for b in bridges if b.node_type in ("PHONE", "VEHICLE", "ACCOUNT")]
    for ib in infra_bridges:
        assert ib.score <= 0.70, f"Infrastructure {ib.node_id} exceeded score cap: {ib.score}"
        assert ib.score < top_bridge.score
