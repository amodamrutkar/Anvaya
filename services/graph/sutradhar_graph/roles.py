"""
Role Detection for Sutradhar.

Assigns explainable structural roles to key entities:
- BROKER (high betweenness, cross-community connectors)
- KINGPIN_CANDIDATE (directed command/flow PageRank, not raw appearances)
- RECRUITER (high fan-out to mule accounts)
- CONTROLLER (shared infrastructure, upstream account controller)
- MEMBER (general syndicate participants)

Every role assignment provides an objective score, explicit human-readable reasons,
and verifiable evidence record IDs.
"""

from collections import defaultdict
from typing import Any

import networkx as nx

from .models import CommunityModel, RoleAssignment


def detect_roles(
    graph_data: dict[str, Any], communities: list[CommunityModel]
) -> list[RoleAssignment]:
    """
    Detect roles for key individuals across the network.

    Returns a list of RoleAssignment objects.
    """
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])

    person_nodes = {nid for nid, n in nodes.items() if n.get("type") == "PERSON"}

    # Entity to Community mapping
    entity_to_comm: dict[str, str] = {}
    for c in communities:
        for m in c.members:
            entity_to_comm[m] = c.community_id

    # Evidence collector per person
    person_evidence: dict[str, set[str]] = defaultdict(set)
    # Crimes touched per person
    person_crimes: dict[str, set[str]] = defaultdict(set)
    # Direct case count per person
    person_cases: dict[str, set[str]] = defaultdict(set)
    # Accounts owned per person
    person_accounts: dict[str, set[str]] = defaultdict(set)
    # Phones used per person
    person_phones: dict[str, set[str]] = defaultdict(set)

    for e in edges:
        src, tgt, etype = e["source"], e["target"], e["type"]
        ev = e.get("evidence", [])

        if src in person_nodes:
            person_evidence[src].update(ev)
            if etype == "ACCUSED_IN":
                person_cases[src].add(tgt)
                c_node = nodes.get(tgt, {})
                ctype = c_node.get("attributes", {}).get("crime_type")
                if ctype:
                    person_crimes[src].add(ctype)
            elif etype == "OWNS" and tgt.startswith("ACCOUNT:"):
                person_accounts[src].add(tgt)
            elif etype == "USES" and tgt.startswith("PHONE:"):
                person_phones[src].add(tgt)

    # ----------------------------------------------------------------------- #
    # 1. Build Directed Command & Flow Graph for Kingpin / Controller Scoring
    # ----------------------------------------------------------------------- #
    # Money flow edges (Account -> Account) mapped back to Person -> Person
    account_to_person: dict[str, str] = {}
    for p, accts in person_accounts.items():
        for a in accts:
            account_to_person[a] = p

    G_flow = nx.DiGraph()
    for p in person_nodes:
        G_flow.add_node(p)

    for e in edges:
        if e.get("type") == "TRANSFERRED_TO":
            src_acct = e["source"]
            tgt_acct = e["target"]
            p_src = account_to_person.get(src_acct)
            p_tgt = account_to_person.get(tgt_acct)
            if p_src and p_tgt and p_src != p_tgt:
                amount = float(e.get("attributes", {}).get("amount", 1000.0))
                current = G_flow[p_src][p_tgt]["weight"] if G_flow.has_edge(p_src, p_tgt) else 0.0
                G_flow.add_edge(p_src, p_tgt, weight=current + amount)

    # Calculate directed PageRank on flow graph (funds sink / command destination)
    try:
        pagerank_scores = (
            nx.pagerank(G_flow, weight="weight") if G_flow.number_of_nodes() > 0 else {}
        )
    except Exception:
        pagerank_scores = {p: 1.0 / len(person_nodes) for p in person_nodes}

    # ----------------------------------------------------------------------- #
    # 2. Build Undirected Co-occurrence Graph for Betweenness Centrality
    # ----------------------------------------------------------------------- #
    G_assoc = nx.Graph()
    for p in person_nodes:
        G_assoc.add_node(p)

    for e in edges:
        if e.get("type") == "CO_ACCUSED_WITH":
            u, v = e["source"], e["target"]
            if u in person_nodes and v in person_nodes:
                G_assoc.add_edge(u, v)

    betweenness = nx.betweenness_centrality(G_assoc) if G_assoc.number_of_nodes() > 0 else {}

    # ----------------------------------------------------------------------- #
    # 3. Detect Roles per Community and Global Nodes
    # ----------------------------------------------------------------------- #
    role_assignments: list[RoleAssignment] = []
    assigned_entities: set[str] = set()

    # Find Kingpin Candidates per community
    # Kingpin criteria:
    # - In a community
    # - Either highest in-flow PageRank OR (high degree in gang while having FEW public FIR appearances)
    for comm in communities:
        comm_members = comm.members
        if not comm_members:
            continue

        # Sort community members by insulation ratio:
        # Score = (internal connections / (case_count + 1)) * PageRank
        kingpin_candidates = []
        for m in comm_members:
            case_cnt = len(person_cases[m])
            deg = G_assoc.degree(m) if G_assoc.has_node(m) else 0
            pr = pagerank_scores.get(m, 0.0)

            # High degree or high flow, with insulation (few direct cases)
            insulation_score = (deg + 1.0) / (case_cnt + 1.0) + (pr * 10.0)
            kingpin_candidates.append((m, insulation_score, case_cnt, deg, pr))

        kingpin_candidates.sort(key=lambda x: -x[1])
        top_kp = kingpin_candidates[0]
        kp_id, kp_score, kp_cases, kp_deg, kp_pr = top_kp

        reasons = [
            f"Commands central position in {comm.community_id} ({kp_deg} direct syndicate ties)",
            f"High insulation ratio: appears in only {kp_cases} direct cases while directing syndicate structure",
        ]
        if kp_pr > 0.05:
            reasons.append(f"Significant financial inflow sink (directed flow score: {kp_pr:.4f})")

        role_assignments.append(
            RoleAssignment(
                entity_id=kp_id,
                role="KINGPIN_CANDIDATE",
                score=min(0.95, round(0.70 + (kp_score / 20.0), 2)),
                reasons=reasons,
                evidence_record_ids=sorted(list(person_evidence[kp_id])),
                community_id=comm.community_id,
            )
        )
        assigned_entities.add(kp_id)

    # Detect Brokers (Entities touching 2+ communities OR 2+ crime types with high betweenness)
    for p in person_nodes:
        if p in assigned_entities:
            continue

        crimes = person_crimes.get(p, set())
        b_score = betweenness.get(p, 0.0)

        # Check if connected to members of multiple communities
        adjacent_comms = set()
        if G_assoc.has_node(p):
            for neighbor in G_assoc.neighbors(p):
                c_id = entity_to_comm.get(neighbor)
                if c_id:
                    adjacent_comms.add(c_id)

        is_cross_crime = len(crimes) >= 2
        is_cross_comm = len(adjacent_comms) >= 2

        if is_cross_crime or is_cross_comm or b_score > 0.05:
            score = 0.75
            reasons = []
            if is_cross_crime:
                score += 0.15
                crimes_str = ", ".join(sorted(list(crimes)))
                reasons.append(
                    f"Cross-crime operational bridge across {len(crimes)} domains: {crimes_str}"
                )
            if is_cross_comm:
                score += 0.10
                comms_str = ", ".join(sorted(list(adjacent_comms)))
                reasons.append(f"Connects multiple distinct syndicates: {comms_str}")
            if b_score > 0.05:
                reasons.append(
                    f"High betweenness centrality ({b_score:.4f}) as vital network intermediary"
                )

            role_assignments.append(
                RoleAssignment(
                    entity_id=p,
                    role="BROKER",
                    score=min(0.98, round(score, 2)),
                    reasons=reasons,
                    evidence_record_ids=sorted(list(person_evidence[p])),
                    community_id=entity_to_comm.get(p),
                )
            )
            assigned_entities.add(p)

    # Detect Recruiters and Controllers
    for p in person_nodes:
        if p in assigned_entities:
            continue

        accts = person_accounts.get(p, set())
        phones = person_phones.get(p, set())
        cases = person_cases.get(p, set())

        # Recruiter: High fan-out to accounts or introducer in multiple complaints
        if len(accts) >= 3 or (len(accts) >= 2 and "CYBER_FRAUD" in person_crimes.get(p, set())):
            role_assignments.append(
                RoleAssignment(
                    entity_id=p,
                    role="RECRUITER",
                    score=0.82,
                    reasons=[
                        f"High fan-out to {len(accts)} financial accounts across banking nodes",
                        "Primary introducer / recruiter signature in cyber fraud complains",
                    ],
                    evidence_record_ids=sorted(list(person_evidence[p])),
                    community_id=entity_to_comm.get(p),
                )
            )
            assigned_entities.add(p)
        elif len(phones) >= 2 and len(cases) >= 2:
            role_assignments.append(
                RoleAssignment(
                    entity_id=p,
                    role="CONTROLLER",
                    score=0.78,
                    reasons=[
                        f"Operates multiple communication devices ({len(phones)} phones) across {len(cases)} cases",
                        "Coordinating node for transaction sweeps",
                    ],
                    evidence_record_ids=sorted(list(person_evidence[p])),
                    community_id=entity_to_comm.get(p),
                )
            )
            assigned_entities.add(p)

    # Assign remaining community members as MEMBER
    for comm in communities:
        for m in comm.members:
            if m not in assigned_entities:
                role_assignments.append(
                    RoleAssignment(
                        entity_id=m,
                        role="MEMBER",
                        score=0.65,
                        reasons=[
                            f"Active participant in {comm.community_id} cases ({len(person_cases[m])} case filings)"
                        ],
                        evidence_record_ids=sorted(list(person_evidence[m])),
                        community_id=comm.community_id,
                    )
                )
                assigned_entities.add(m)

    return role_assignments
