"""
sutradhar_api/routers/graph.py
Community, neighborhood, path, role, bridge, and mule chain endpoints.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from sutradhar_api.auth import require_action
from sutradhar_api.models import UserInfo
from sutradhar_api.store import get_store
from sutradhar_graph.paths import shortest_path

router = APIRouter(tags=["graph"])


# ─────────────────────────────────────────────────────────────
# Communities
# ─────────────────────────────────────────────────────────────


@router.get("/graph/communities")
def get_communities(
    user: Annotated[UserInfo, Depends(require_action("GRAPH_VIEW"))],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    store = get_store()
    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="COMMUNITIES_VIEW",
        summary=f"Listed communities (offset={offset}, limit={limit}).",
    )
    all_communities = list(store.communities.values())
    return all_communities[offset : offset + limit]


@router.get("/graph/communities/{community_id}")
def get_community(
    community_id: str,
    user: Annotated[UserInfo, Depends(require_action("GRAPH_VIEW"))],
):
    store = get_store()
    community = store.communities.get(community_id)
    if not community:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"code": "NOT_FOUND", "message": f"Community {community_id!r} not found."}
            },
        )
    # Enrich with roles for this community
    community_roles = [r for r in store.roles if r.get("community_id") == community_id]
    result = dict(community)
    result["roles"] = community_roles
    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="COMMUNITY_VIEW",
        summary=f"Viewed community {community_id}.",
    )
    return result


# ─────────────────────────────────────────────────────────────
# Subgraph / path
# ─────────────────────────────────────────────────────────────


@router.get("/graph/entity/{entity_id}/neighborhood")
def get_neighborhood(
    entity_id: str,
    user: Annotated[UserInfo, Depends(require_action("GRAPH_VIEW"))],
    hops: int = Query(2, ge=1, le=5),
    limit: int = Query(50, ge=1, le=200),
):
    store = get_store()
    entity = store.entities.get(entity_id)
    if not entity:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Entity {entity_id!r} not found."}},
        )
    # Return entity nodes + links connected to this entity's mentions
    mention_ids = set(entity.get("mention_ids", []))
    related_links = [
        lnk
        for lnk in store.links.values()
        if lnk.get("a_mention_id") in mention_ids or lnk.get("b_mention_id") in mention_ids
    ]
    # Collect connected entity IDs
    connected_eids = {entity_id}
    for e in store.entities.values():
        for mid in e.get("mention_ids", []):
            for lnk in related_links:
                if mid in (lnk.get("a_mention_id"), lnk.get("b_mention_id")):
                    connected_eids.add(e["entity_id"])
    nodes = [store.entities[eid] for eid in connected_eids if eid in store.entities]
    bounded_nodes = nodes[:limit]
    bounded_edges = related_links[:limit]

    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="NEIGHBORHOOD_VIEW",
        summary=f"Viewed neighborhood for {entity_id} (hops={hops}): {len(bounded_nodes)} nodes, {len(bounded_edges)} links.",
    )
    return {"nodes": bounded_nodes, "edges": bounded_edges}


@router.get("/graph/path")
def get_graph_path(
    user: Annotated[UserInfo, Depends(require_action("GRAPH_VIEW"))],
    from_id: str = Query(..., alias="from"),
    to_id: str = Query(..., alias="to"),
    max_hops: int = Query(5, ge=1, le=10),
):
    store = get_store()
    path_result = shortest_path(store.graph_data, from_id, to_id)
    found = path_result.get("found", False)
    path_nodes = path_result.get("path", [])
    traversed_edges = path_result.get("edges", [])

    hops = max(0, len(path_nodes) - 1) if path_nodes else 0
    if found and hops > max_hops:
        found = False
        path_nodes = []
        traversed_edges = []
        hops = 0

    nodes_map = {n["id"]: n for n in store.graph_data.get("nodes", [])}
    nodes = [nodes_map[nid] for nid in path_nodes if nid in nodes_map]

    evidence: list[str] = []
    for e in traversed_edges:
        for ev_item in e.get("evidence", []):
            if ev_item not in evidence:
                evidence.append(ev_item)

    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="GRAPH_PATH_VIEW",
        summary=f"Queried path between {from_id} and {to_id}: found={found}, hops={hops}",
        purpose="INVESTIGATION",
    )

    return {
        "from_id": from_id,
        "to_id": to_id,
        "found": found,
        "hops": hops,
        "path": path_nodes,
        "nodes": nodes,
        "edges": traversed_edges,
        "evidence": evidence,
        "requires_investigator_review": True,
    }


# ─────────────────────────────────────────────────────────────
# Roles, bridges, mules
# ─────────────────────────────────────────────────────────────


@router.get("/roles")
def get_roles(
    user: Annotated[UserInfo, Depends(require_action("GRAPH_VIEW"))],
    community_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    store = get_store()
    roles = store.roles
    if community_id:
        roles = [r for r in roles if r.get("community_id") == community_id]
    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="GRAPH_ROLES_VIEW",
        summary=f"Viewed graph roles (offset={offset}, limit={limit}).",
        purpose="INVESTIGATION",
    )
    return roles[offset : offset + limit]


@router.get("/bridges")
def get_bridges(
    user: Annotated[UserInfo, Depends(require_action("GRAPH_VIEW"))],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    store = get_store()
    bridges = store.bridges
    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="GRAPH_BRIDGES_VIEW",
        summary=f"Viewed graph bridges (offset={offset}, limit={limit}).",
        purpose="INVESTIGATION",
    )
    return bridges[offset : offset + limit]


@router.get("/mule/chains")
def get_mule_chains(
    user: Annotated[UserInfo, Depends(require_action("MULE_VIEW"))],
    community_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    store = get_store()
    chains = store.mule_chains
    if community_id:
        chains = [c for c in chains if c.get("community_id") == community_id]
    return chains[offset : offset + limit]
