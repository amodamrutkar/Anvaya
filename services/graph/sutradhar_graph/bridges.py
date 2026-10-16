"""
Cross-Crime & Cross-Agency Bridge Detection for Sutradhar.

Identifies PERSON, PHONE, ACCOUNT, or VEHICLE nodes connecting multiple distinct
crime domains (e.g., Extortion, Cyber Fraud, Narcotics) or multiple syndicates.
Special emphasis on the Rakesh Pawar nexus linking multi-agency silos.
"""

from collections import defaultdict
from typing import Any

from .models import BridgeModel, CommunityModel


def detect_bridges(graph_data: dict[str, Any],
                   communities: list[CommunityModel]) -> list[BridgeModel]:
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

    # For every node, track adjacent cases, crimes, and communities
    node_cases: dict[str, set[str]] = defaultdict(set)
    node_crimes: dict[str, set[str]] = defaultdict(set)
    node_comms: dict[str, set[str]] = defaultdict(set)
    node_evidence: dict[str, set[str]] = defaultdict(set)
    node_linked_persons: dict[str, set[str]] = defaultdict(set)

    # First pass: map PERSON connections to cases and communities
    for e in edges:
        src, tgt, etype = e["source"], e["target"], e["type"]
        ev = e.get("evidence", [])

        if etype in ("ACCUSED_IN", "VICTIM_IN"):
            # Person -> Case
            node_cases[src].add(tgt)
            node_evidence[src].update(ev)
            c_node = nodes.get(tgt, {})
            ctype = c_node.get("attributes", {}).get("crime_type")
            if ctype:
                node_crimes[src].add(ctype)
            cid = person_to_comm.get(src)
            if cid:
                node_comms[src].add(cid)

    # Second pass: map PHONE, ACCOUNT, VEHICLE through their associated persons
    for e in edges:
        src, tgt, etype = e["source"], e["target"], e["type"]
        ev = e.get("evidence", [])

        if etype in ("USES", "OWNS", "LIVES_AT"):
            person = src
            item = tgt
            node_linked_persons[item].add(person)
            node_evidence[item].update(ev)
            node_cases[item].update(node_cases[person])
            node_crimes[item].update(node_crimes[person])
            node_comms[item].update(node_comms[person])

    # Check candidates for Bridge qualification (PERSON, PHONE, ACCOUNT, VEHICLE)
    bridges: list[BridgeModel] = []
    eligible_types = {"PERSON", "PHONE", "ACCOUNT", "VEHICLE"}

    for nid, node in nodes.items():
        ntype = node.get("type")
        if ntype not in eligible_types:
            continue

        crimes = node_crimes.get(nid, set())
        comms = node_comms.get(nid, set())
        linked_persons = node_linked_persons.get(nid, set())
        if ntype == "PERSON":
            linked_persons.add(nid)

        # Qualification: touches >= 2 crime types OR touches >= 2 communities
        is_cross_crime = len(crimes) >= 2
        is_cross_comm = len(comms) >= 2

        if is_cross_crime or is_cross_comm:
            reasons = []
            if is_cross_crime:
                crimes_str = ", ".join(sorted(list(crimes)))
                reasons.append(f"Spans {len(crimes)} distinct crime classifications: {crimes_str}")
            if is_cross_comm:
                comms_str = ", ".join(sorted(list(comms)))
                reasons.append(f"Direct operational link bridging {len(comms)} syndicates: {comms_str}")
            if ntype != "PERSON":
                reasons.append(f"Shared technical infrastructure utilized by {len(linked_persons)} persons")

            bridges.append(
                BridgeModel(
                    node_id=nid,
                    node_type=ntype,
                    label=node.get("label", nid),
                    communities=sorted(list(comms)),
                    crime_types=sorted(list(crimes)),
                    linked_person_ids=sorted(list(linked_persons)),
                    evidence_record_ids=sorted(list(node_evidence[nid])),
                    reasons=reasons,
                )
            )

    # Sort bridges deterministically: cross-crime first, then by number of evidence records
    bridges.sort(
        key=lambda b: (-len(b.crime_types), -len(b.communities), -len(b.evidence_record_ids), b.node_id)
    )

    return bridges
