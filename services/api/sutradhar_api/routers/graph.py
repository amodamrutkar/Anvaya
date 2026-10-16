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

router = APIRouter(tags=["graph"])


# ─────────────────────────────────────────────────────────────
# Communities
# ─────────────────────────────────────────────────────────────

@router.get("/graph/communities")
def get_communities(
    user: Annotated[UserInfo, Depends(require_action("GRAPH_VIEW"))],
):
    store = get_store()
    store.record_audit(actor=user.user_id, role=user.role.value, action="COMMUNITIES_VIEW", summary="Listed all communities.")
    return list(store.communities.values())


@router.get("/graph/communities/{community_id}")
def get_community(
    community_id: str,
    user: Annotated[UserInfo, Depends(require_action("GRAPH_VIEW"))],
):
    store = get_store()
    community = store.communities.get(community_id)
    if not community:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": f"Community {community_id!r} not found."}})
    # Enrich with roles for this community
    community_roles = [r for r in store.roles if r.get("community_id") == community_id]
    result = dict(community)
    result["roles"] = community_roles
    store.record_audit(
        actor=user.user_id, role=user.role.value, action="COMMUNITY_VIEW",
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
    hops: int = 2,
):
    store = get_store()
    entity = store.entities.get(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": f"Entity {entity_id!r} not found."}})
    # Simplified: return all entity nodes + links connected to this entity's mentions
    mention_ids = set(entity.get("mention_ids", []))
    related_links = [
        lnk for lnk in store.links.values()
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
    store.record_audit(
        actor=user.user_id, role=user.role.value, action="NEIGHBORHOOD_VIEW",
        summary=f"Viewed neighborhood for {entity_id}: {len(nodes)} nodes, {len(related_links)} links.",
    )
    return {"nodes": nodes, "edges": related_links}


@router.get("/graph/path")
def get_graph_path(
    user: Annotated[UserInfo, Depends(require_action("GRAPH_VIEW"))],
    from_id: str | None = Query(None, alias="from"),
    to_id: str | None = Query(None, alias="to"),
):
    return {"path": [from_id, to_id], "edges": [], "hops": 1}


# ─────────────────────────────────────────────────────────────
# Roles, bridges, mules
# ─────────────────────────────────────────────────────────────

@router.get("/roles")
def get_roles(
    user: Annotated[UserInfo, Depends(require_action("GRAPH_VIEW"))],
    community_id: str | None = None,
):
    store = get_store()
    roles = store.roles
    if community_id:
        roles = [r for r in roles if r.get("community_id") == community_id]
    return roles


@router.get("/bridges")
def get_bridges(
    user: Annotated[UserInfo, Depends(require_action("GRAPH_VIEW"))],
):
    return get_store().bridges


@router.get("/mule/chains")
def get_mule_chains(
    user: Annotated[UserInfo, Depends(require_action("MULE_VIEW"))],
    community_id: str | None = None,
):
    store = get_store()
    chains = store.mule_chains
    if community_id:
        chains = [c for c in chains if c.get("community_id") == community_id]
    return chains
