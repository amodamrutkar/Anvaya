"""
Path Query and Graph Neighborhood Library Functions for Sutradhar.

Used by Backend and UI:
- neighborhood(graph, entity_id, hops): extracts k-hop ego subgraph.
- shortest_path(graph, a, b): weighted shortest path preferring STRONG edges
  and returning evidence trails per traversed edge.
"""

from typing import Any

import networkx as nx


def neighborhood(graph_data: dict[str, Any], entity_id: str, hops: int = 1) -> dict[str, Any]:
    """
    Extract the k-hop neighborhood ego network around entity_id.

    Returns a graph dictionary with 'nodes' and 'edges'.
    """
    nodes_map = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])

    if entity_id not in nodes_map:
        return {"nodes": [], "edges": []}

    # Build undirected representation for neighborhood exploration
    G = nx.Graph()
    for nid in nodes_map:
        G.add_node(nid)

    for e in edges:
        G.add_edge(e["source"], e["target"], **e)

    # Calculate k-hop nodes using ego_graph or single_source_shortest_path_length
    sub_node_ids = set(nx.single_source_shortest_path_length(G, entity_id, cutoff=hops).keys())

    sub_nodes = [nodes_map[nid] for nid in sorted(sub_node_ids) if nid in nodes_map]

    # Collect edges where both endpoints are in sub_nodes
    sub_edges = [e for e in edges if e["source"] in sub_node_ids and e["target"] in sub_node_ids]

    return {
        "nodes": sub_nodes,
        "edges": sub_edges,
    }


def shortest_path(graph_data: dict[str, Any], a: str, b: str) -> dict[str, Any]:
    """
    Compute shortest path from node a to node b, heavily preferring STRONG edges.

    Weight model:
    - STRONG edge: weight 1.0
    - WEAK edge: weight 10.0 (high cost so weak links are avoided unless no alternative exists)

    Returns path node IDs, traversed edges with type, strength, and evidence.
    """
    nodes_map = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])

    if a not in nodes_map or b not in nodes_map:
        return {
            "found": False,
            "path": [],
            "edges": [],
            "message": f"One or both endpoints ('{a}', '{b}') do not exist in graph",
        }

    if a == b:
        return {
            "found": True,
            "path": [a],
            "edges": [],
            "total_weight": 0.0,
        }

    # Build MultiGraph with edge costs
    G = nx.Graph()
    for nid in nodes_map:
        G.add_node(nid)

    # Group edges by (u, v) and select lowest cost
    pair_best_edge: dict[tuple[str, str], tuple[float, dict]] = {}

    for e in edges:
        u, v = e["source"], e["target"]
        strength = e.get("strength", "STRONG")
        cost = 1.0 if strength == "STRONG" else 10.0

        # Disallow or penalize lower confidence
        conf = e.get("confidence", 1.0)
        cost = cost / max(0.1, conf)

        pair = (min(u, v), max(u, v))
        if pair not in pair_best_edge or cost < pair_best_edge[pair][0]:
            pair_best_edge[pair] = (cost, e)

    for (u, v), (cost, e_data) in pair_best_edge.items():
        G.add_edge(u, v, weight=cost, edge_info=e_data)

    try:
        path_nodes = nx.shortest_path(G, source=a, target=b, weight="weight")
        total_weight = nx.shortest_path_length(G, source=a, target=b, weight="weight")

        traversed_edges = []
        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i + 1]
            e_info = G[u][v]["edge_info"]
            traversed_edges.append(
                {
                    "id": e_info.get("id"),
                    "source": e_info.get("source"),
                    "target": e_info.get("target"),
                    "type": e_info.get("type"),
                    "strength": e_info.get("strength"),
                    "evidence": e_info.get("evidence", []),
                    "confidence": e_info.get("confidence", 1.0),
                }
            )

        return {
            "found": True,
            "path": path_nodes,
            "edges": traversed_edges,
            "total_weight": round(total_weight, 2),
        }
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return {
            "found": False,
            "path": [],
            "edges": [],
            "message": f"No connecting path found between '{a}' and '{b}'",
        }
