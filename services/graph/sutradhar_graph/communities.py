"""
Community detection and syndicate discovery for Sutradhar.

Constructs a weighted person-to-person projection graph with a hub guard
(preventing high-degree shared addresses or stations from creating artificial gangs),
executes deterministic Louvain community detection, and calculates cohesion,
dominant crime types, activity periods, and monthly timelines.
"""

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

import networkx as nx

from .models import CommunityModel, TimelineActivity


def detect_communities(
    graph_data: dict[str, Any],
    seed: int = 42,
    hub_degree_threshold: int = 15,
    min_community_size: int = 4,
) -> list[CommunityModel]:
    """
    Detect criminal syndicates / communities from graph.json data.

    Returns a list of CommunityModel objects.
    """
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])

    # Step 1: Build bipartite associations for Person projection
    person_nodes = {nid for nid, n in nodes.items() if n.get("type") == "PERSON"}
    case_nodes = {nid: n for nid, n in nodes.items() if n.get("type") == "CASE"}

    # Person -> Cases
    person_cases: dict[str, set[str]] = defaultdict(set)
    # Person -> Identifiers (phones, accounts, vehicles)
    person_strong_ids: dict[str, set[str]] = defaultdict(set)
    # Person -> Addresses
    person_addresses: dict[str, set[str]] = defaultdict(set)
    # Account -> Persons
    account_to_persons: dict[str, set[str]] = defaultdict(set)

    # Calculate degrees of non-person nodes for Hub Guard
    node_degrees: Counter[str] = Counter()
    for e in edges:
        node_degrees[e["source"]] += 1
        node_degrees[e["target"]] += 1

        src, tgt, etype = e["source"], e["target"], e["type"]
        if etype == "ACCUSED_IN" and src in person_nodes and tgt in case_nodes:
            person_cases[src].add(tgt)
        elif etype in ("USES", "OWNS") and src in person_nodes:
            person_strong_ids[src].add(tgt)
            if tgt.startswith("ACCOUNT:"):
                account_to_persons[tgt].add(src)
        elif etype == "LIVES_AT" and src in person_nodes:
            person_addresses[src].add(tgt)

    # Step 2: Build Weighted Person Projection Graph
    G_proj = nx.Graph()
    for p in person_nodes:
        G_proj.add_node(p)

    persons_list = sorted(list(person_nodes))

    # Weight definitions per PRD 4.2
    # Shared case: 1.0, Shared phone/account: 1.0, Transfer: 0.7, Shared address: 0.1
    for i in range(len(persons_list)):
        for j in range(i + 1, len(persons_list)):
            p1, p2 = persons_list[i], persons_list[j]
            weight = 0.0

            # 1. Shared Case (CO_ACCUSED_WITH) -> 1.0
            shared_cases = person_cases[p1] & person_cases[p2]
            if shared_cases:
                weight += 1.0 * len(shared_cases)

            # 2. Shared Strong Identifiers (Phone, Account, Vehicle) -> 1.0
            # Apply Hub Guard: ignore if node degree exceeds threshold
            shared_ids = {
                nid
                for nid in (person_strong_ids[p1] & person_strong_ids[p2])
                if node_degrees[nid] <= hub_degree_threshold
            }
            if shared_ids:
                weight += 1.0 * len(shared_ids)

            # 3. Shared Address (WEAK link) -> 0.1
            # HUB GUARD: If address has degree > hub_degree_threshold, down-weight to 0.0!
            shared_addrs = {
                aid
                for aid in (person_addresses[p1] & person_addresses[p2])
                if node_degrees[aid] <= hub_degree_threshold
            }
            if shared_addrs:
                weight += 0.1 * len(shared_addrs)

            if weight > 0:
                G_proj.add_edge(p1, p2, weight=weight)

    # 4. Account Transfer Connections (weight 0.7)
    for e in edges:
        if e.get("type") == "TRANSFERRED_TO":
            src_acct = e["source"]
            tgt_acct = e["target"]
            holders1 = account_to_persons.get(src_acct, set())
            holders2 = account_to_persons.get(tgt_acct, set())
            for h1 in holders1:
                for h2 in holders2:
                    if h1 != h2:
                        current_w = G_proj[h1][h2]["weight"] if G_proj.has_edge(h1, h2) else 0.0
                        G_proj.add_edge(h1, h2, weight=current_w + 0.7)

    # Step 3: Run Louvain Community Detection with fixed seed
    # Remove isolated nodes
    connected_persons = [p for p in G_proj.nodes() if G_proj.degree(p) > 0]
    subgraph = G_proj.subgraph(connected_persons)

    if subgraph.number_of_nodes() == 0:
        raw_communities = []
    else:
        raw_communities = nx.community.louvain_communities(subgraph, weight="weight", seed=seed)

    # Step 4: Format Communities per PRD 8.4
    communities: list[CommunityModel] = []
    comm_idx = 0

    # Sort communities by size descending, then first member ID for determinism
    sorted_raw = sorted(
        raw_communities,
        key=lambda c: (-len(c), sorted(list(c))[0] if c else ""),
    )

    for comm_set in sorted_raw:
        if len(comm_set) < min_community_size:
            continue

        comm_idx += 1
        comm_id = f"COM-{comm_idx:03d}"
        members = sorted(list(comm_set))

        # Calculate Cohesion (internal edge density)
        internal_edges = 0
        for u in members:
            for v in members:
                if u < v and G_proj.has_edge(u, v):
                    internal_edges += 1

        n_members = len(members)
        max_possible = (n_members * (n_members - 1)) / 2 if n_members > 1 else 1.0
        cohesion = round(internal_edges / max_possible, 4) if max_possible > 0 else 1.0

        # Gather Community Cases, Agencies, Districts, Dates
        comm_case_ids: set[str] = set()
        districts: set[str] = set()
        agencies: set[str] = set()
        crime_types: Counter[str] = Counter()
        dates: list[str] = []

        for p in members:
            # Person attributes
            p_node = nodes.get(p, {})
            dist = p_node.get("attributes", {}).get("district")
            if dist:
                districts.add(dist)

            for cid in person_cases.get(p, []):
                comm_case_ids.add(cid)
                c_node = case_nodes.get(cid, {})
                c_attrs = c_node.get("attributes", {})
                ctype = c_attrs.get("crime_type")
                if ctype:
                    crime_types[ctype] += 1
                c_agency = c_attrs.get("agency")
                if c_agency:
                    agencies.add(c_agency)
                c_dist = c_attrs.get("district")
                if c_dist:
                    districts.add(c_dist)
                c_date = c_attrs.get("filed_date")
                if c_date:
                    dates.append(c_date)

        sorted_cases = sorted(list(comm_case_ids))
        sorted_dates = sorted(dates) if dates else ["2025-01-01"]
        first_act = sorted_dates[0]
        last_act = sorted_dates[-1]

        # Monthly timeline aggregation
        month_counts: Counter[str] = Counter()
        for d in sorted_dates:
            try:
                month_counts[d[:7]] += 1
            except Exception:
                pass

        timeline = [
            TimelineActivity(month=m, case_count=count) for m, count in sorted(month_counts.items())
        ]

        # Continuing activity: activity within last 12 months (relative to 2026-10)
        continuing = False
        if sorted_dates:
            try:
                latest_dt = datetime.strptime(last_act, "%Y-%m-%d")
                # Active if within 12 months of 2026-10-17
                if (datetime(2026, 10, 17) - latest_dt).days <= 365:
                    continuing = True
            except Exception:
                continuing = True

        # Dominant crime type and label
        top_crimes = [c for c, _ in crime_types.most_common()] or ["ORGANIZED_CRIME"]
        primary_crime = top_crimes[0]
        dominant_dist = sorted(list(districts))[0] if districts else "Maharashtra"

        crime_labels = {
            "EXTORTION": "Extortion Syndicate",
            "CYBER_FRAUD": "Cyber-Fraud Mule Ring",
            "NARCOTICS": "Interstate Narcotics Network",
        }
        label_prefix = crime_labels.get(primary_crime, f"{primary_crime.title()} Group")
        comm_label = f"{label_prefix} ({dominant_dist})"

        communities.append(
            CommunityModel(
                community_id=comm_id,
                label=comm_label,
                crime_types=top_crimes,
                members=members,
                member_count=n_members,
                cohesion=cohesion,
                districts=sorted(list(districts)),
                agencies=sorted(list(agencies)),
                case_ids=sorted_cases,
                first_activity=first_act,
                last_activity=last_act,
                continuing_activity=continuing,
                timeline=timeline,
            )
        )

    return communities
