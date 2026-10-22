"""
Cross-Crime & Cross-Agency Bridge Detection for Sutradhar.

Identifies PERSON, PHONE, ACCOUNT, or VEHICLE nodes connecting multiple distinct
crime domains (e.g., Extortion, Cyber Fraud, Narcotics) or multiple syndicates.
Special emphasis on the Rakesh Pawar nexus linking multi-agency silos.
"""

from collections import defaultdict
from typing import Any

import networkx as nx

from .models import BridgeModel, CommunityModel


def detect_bridges(
    graph_data: dict[str, Any], communities: list[CommunityModel]
) -> list[BridgeModel]:
    """
    Detect bridges connecting >= 2 crime types or >= 2 communities.

    Returns a list of BridgeModel objects.
    """
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])

    # Person -> Community mapping
    person_to_comm: dict[str, str] = {}
    for c in communities:
        for m in c.members:
            person_to_comm[m] = c.community_id

    # Co-accused graph for network broker betweenness
    G_assoc = nx.Graph()
    person_nodes = {nid for nid, n in nodes.items() if n.get("type") == "PERSON"}
    for p in person_nodes:
        # Strictly exclude complainants/victims from criminal bridge network
        if "VICTIM" not in nodes[p].get("attributes", {}).get("roles", []):
            G_assoc.add_node(p)

    for e in edges:
        if e.get("type") == "CO_ACCUSED_WITH":
            u, v = e["source"], e["target"]
            if u in G_assoc and v in G_assoc:
                G_assoc.add_edge(u, v)

    betweenness = nx.betweenness_centrality(G_assoc) if G_assoc.number_of_nodes() > 0 else {}

    # For every node, track adjacent cases, crimes, and communities
    node_cases: dict[str, set[str]] = defaultdict(set)
    node_crimes: dict[str, set[str]] = defaultdict(set)
    node_comms: dict[str, set[str]] = defaultdict(set)
    node_evidence: dict[str, set[str]] = defaultdict(set)
    node_linked_persons: dict[str, set[str]] = defaultdict(set)

    # First pass: map PERSON connections (strictly ACCUSED_IN; VICTIM_IN excluded)
    for e in edges:
        src, tgt, etype = e["source"], e["target"], e.get("type")
        ev = e.get("evidence", [])

        if etype == "ACCUSED_IN" and src in person_nodes:
            if "VICTIM" in nodes[src].get("attributes", {}).get("roles", []):
                continue
            node_cases[src].add(tgt)
            node_evidence[src].update(ev)
            c_node = nodes.get(tgt, {})
            ctype = c_node.get("attributes", {}).get("crime_type")
            if ctype:
                node_crimes[src].add(ctype)

    # Map adjacent communities for PERSON nodes via syndicate associations
    for p in person_nodes:
        if p not in G_assoc:
            continue
        p_comms = set()
        if p in person_to_comm:
            p_comms.add(person_to_comm[p])
        for nbr in G_assoc.neighbors(p):
            if nbr in person_to_comm:
                p_comms.add(person_to_comm[nbr])
        node_comms[p] = p_comms

    # Second pass: map PHONE, ACCOUNT, VEHICLE through associated accused persons
    for e in edges:
        src, tgt, etype = e["source"], e["target"], e.get("type")
        ev = e.get("evidence", [])

        if etype in ("USES", "OWNS") and src in person_nodes:
            if "VICTIM" in nodes[src].get("attributes", {}).get("roles", []):
                continue
            item = tgt
            node_linked_persons[item].add(src)
            node_evidence[item].update(ev)
            node_cases[item].update(node_cases[src])
            node_crimes[item].update(node_crimes[src])
            node_comms[item].update(node_comms[src])

    # Check candidates for Bridge qualification (PERSON, PHONE, ACCOUNT, VEHICLE)
    bridges: list[BridgeModel] = []
    eligible_types = {"PERSON", "PHONE", "ACCOUNT", "VEHICLE"}

    for nid, node in nodes.items():
        ntype = node.get("type")
        if ntype not in eligible_types:
            continue
        # Exclude civilian complainants
        if ntype == "PERSON" and "VICTIM" in node.get("attributes", {}).get("roles", []):
            continue

        crimes = node_crimes.get(nid, set())
        comms = node_comms.get(nid, set())
        cases = node_cases.get(nid, set())
        linked_persons = node_linked_persons.get(nid, set())
        if ntype == "PERSON":
            linked_persons.add(nid)

        # Non-person infrastructure qualification: must be shared by >= 2 distinct persons OR span >= 2 crimes
        if ntype != "PERSON" and not (len(linked_persons) >= 2 or len(crimes) >= 2):
            continue

        # Qualification: touches >= 2 crime types OR touches >= 2 communities
        is_cross_crime = len(crimes) >= 2
        is_cross_comm = len(comms) >= 2

        if is_cross_crime or is_cross_comm:
            reasons = []
            if is_cross_crime:
                crimes_str = ", ".join(sorted(crimes))
                reasons.append(f"Spans {len(crimes)} distinct crime classifications: {crimes_str}")
            if is_cross_comm:
                comms_str = ", ".join(sorted(comms))
                reasons.append(
                    f"Direct operational link bridging {len(comms)} syndicates: {comms_str}"
                )

            # Collect supporting edges
            supporting = []
            for e in edges:
                if e["source"] == nid or e["target"] == nid:
                    supporting.append({
                        "source": e["source"],
                        "target": e["target"],
                        "type": e.get("type"),
                        "strength": e.get("strength", "STRONG"),
                        "evidence": e.get("evidence", []),
                    })

            # Explainable Bridge Scoring
            b_score = 0.50
            if ntype == "PERSON":
                b_score += 0.15 * min(len(crimes), 3)
                if len(comms) >= 2:
                    b_score += 0.20 * min(len(comms) - 1, 2)
                b_score += 0.05 * min(len(cases), 3)
                bw = betweenness.get(nid, 0.0)
                if bw > 0.02:
                    b_score += 0.10
                    reasons.append(
                        f"High betweenness centrality indicator ({bw:.4f}) as cross-network broker"
                    )
                b_score += 0.01 * min(len(node_evidence[nid]), 5)
                final_score = min(0.98, round(b_score, 4))
            else:
                # Technical infrastructure penalty: infrastructure is an asset, not human intelligence broker
                b_score += 0.10 * min(len(crimes), 2)
                if len(comms) >= 2:
                    b_score += 0.10
                b_score += 0.05 * min(len(linked_persons) - 1, 3)
                final_score = min(0.70, round(b_score, 4))
                reasons.append(
                    f"Shared technical infrastructure utilized by {len(linked_persons)} operatives"
                )

            bridges.append(
                BridgeModel(
                    node_id=nid,
                    node_type=ntype,
                    label=node.get("label", nid),
                    communities=sorted(comms),
                    crime_types=sorted(crimes),
                    linked_person_ids=sorted(linked_persons),
                    evidence_record_ids=sorted(node_evidence[nid]),
                    reasons=reasons,
                    score=final_score,
                    indicator="BRIDGE_CANDIDATE",
                    supporting_edges=supporting[:10],
                    action="Requires investigator review",
                )
            )

    # Deterministic Ranking: Score first, PERSON before infrastructure, then community/crime diversity
    bridges.sort(
        key=lambda b: (
            -b.score,
            0 if b.node_type == "PERSON" else 1,
            -len(b.communities),
            -len(b.crime_types),
            -len(b.evidence_record_ids),
            b.node_id,
        )
    )

    return bridges
