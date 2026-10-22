"""
Path Query, Graph Neighborhood, and Network Centrality Library Functions for Sutradhar.

Used by Backend and UI:
- neighborhood(graph, entity_id, hops): extracts k-hop ego subgraph.
- shortest_path(graph, a, b): weighted shortest path preferring STRONG edges over MEDIUM and WEAK.
- find_connected_network(graph, entity_id, max_depth): multi-hop traversal with path and evidence provenance.
- compute_centrality_metrics(graph): degree, betweenness, component analysis.
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

    G = nx.Graph()
    for nid in nodes_map:
        G.add_node(nid)

    for e in edges:
        G.add_edge(e["source"], e["target"], **e)

    sub_node_ids = set(nx.single_source_shortest_path_length(G, entity_id, cutoff=hops).keys())
    sub_nodes = [nodes_map[nid] for nid in sorted(sub_node_ids) if nid in nodes_map]
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
    - MEDIUM edge: weight 3.0
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

    G = nx.Graph()
    for nid in nodes_map:
        G.add_node(nid)

    pair_best_edge: dict[tuple[str, str], tuple[float, dict]] = {}

    for e in edges:
        u, v = e["source"], e["target"]
        strength = e.get("strength", "STRONG")
        if strength == "STRONG":
            cost = 1.0
        elif strength == "MEDIUM":
            cost = 3.0
        else:
            cost = 10.0

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
                    "provenance": e_info.get("provenance", {}),
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


def find_connected_network(
    graph_data: dict[str, Any],
    entity_id: str,
    max_depth: int = 3,
) -> dict[str, Any]:
    """
    Given a person/entity, return connected entities within configurable depth,
    including the actual paths, edge types, tiers, and supporting evidence.
    """
    nodes_map = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])

    if entity_id not in nodes_map:
        return {"entity": entity_id, "connections": [], "paths": [], "nodes": [], "edges": []}

    adj: dict[str, list[dict[str, Any]]] = {}
    for e in edges:
        adj.setdefault(e["source"], []).append(e)
        adj.setdefault(e["target"], []).append(e)

    # BFS tracking paths
    visited: set[str] = {entity_id}
    queue: list[tuple[str, list[str], list[dict[str, Any]]]] = [(entity_id, [entity_id], [])]
    discovered_paths: list[dict[str, Any]] = []
    included_edges: list[dict[str, Any]] = []

    while queue:
        curr, path_nodes, path_edges = queue.pop(0)
        depth = len(path_nodes) - 1

        if depth >= max_depth:
            continue

        for e in adj.get(curr, []):
            nbr = e["target"] if e["source"] == curr else e["source"]
            if nbr not in path_nodes:
                new_path_nodes = path_nodes + [nbr]
                new_path_edges = path_edges + [e]
                included_edges.append(e)

                discovered_paths.append({
                    "target_entity": nbr,
                    "target_type": nodes_map.get(nbr, {}).get("type", "UNKNOWN"),
                    "depth": depth + 1,
                    "path": new_path_nodes,
                    "edges": [
                        {
                            "source": ed["source"],
                            "target": ed["target"],
                            "type": ed["type"],
                            "strength": ed.get("strength", "STRONG"),
                            "evidence": ed.get("evidence", []),
                            "provenance": ed.get("provenance", {}),
                        }
                        for ed in new_path_edges
                    ],
                })

                if nbr not in visited:
                    visited.add(nbr)
                    queue.append((nbr, new_path_nodes, new_path_edges))

    unique_nodes = [nodes_map[nid] for nid in sorted(visited) if nid in nodes_map]
    return {
        "entity": entity_id,
        "entity_type": nodes_map[entity_id].get("type"),
        "total_connected": len(visited) - 1,
        "nodes": unique_nodes,
        "paths": discovered_paths,
    }


def compute_centrality_metrics(graph_data: dict[str, Any]) -> dict[str, Any]:
    """
    Computes degree, weighted degree, betweenness centrality, and component metrics.
    Centrality alone does not make a person a person-of-interest.
    """
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])

    G = nx.Graph()
    for nid in nodes:
        G.add_node(nid)

    for e in edges:
        weight = 1.0 if e.get("strength") == "STRONG" else (0.5 if e.get("strength") == "MEDIUM" else 0.1)
        G.add_edge(e["source"], e["target"], weight=weight)

    degree_dict = dict(G.degree())
    weighted_degree = {n: round(sum(d.get("weight", 1.0) for _, _, d in G.edges(n, data=True)), 2) for n in G.nodes()}

    # Compute betweenness (sampled/approximate if large for fast turnaround)
    k_sample = min(100, len(nodes)) if len(nodes) > 100 else None
    betweenness = nx.betweenness_centrality(G, k=k_sample, weight="weight")

    # Connected components
    components = list(nx.connected_components(G))
    comp_sizes = [len(c) for c in components]
    largest_component = max(comp_sizes) if comp_sizes else 0

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "total_components": len(components),
        "largest_component_size": largest_component,
        "top_degree": sorted(degree_dict.items(), key=lambda x: -x[1])[:10],
        "top_betweenness": sorted(
            [{"node": k, "score": round(v, 4)} for k, v in betweenness.items()],
            key=lambda x: -x["score"]
        )[:10],
        "node_centralities": {
            nid: {
                "degree": degree_dict.get(nid, 0),
                "weighted_degree": weighted_degree.get(nid, 0.0),
                "betweenness": round(betweenness.get(nid, 0.0), 4),
            }
            for nid in nodes
        },
    }
