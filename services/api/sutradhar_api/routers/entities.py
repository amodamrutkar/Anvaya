"""
sutradhar_api/routers/entities.py
Entity search, profile, and link endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from sutradhar_api.auth import require_action
from sutradhar_api.models import UserInfo
from sutradhar_api.store import get_store

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/search")
def search_entities(
    q: str,
    type: str | None = None,
    user: UserInfo = Depends(require_action("ENTITY_SEARCH")),
):
    store = get_store()
    q_lower = q.lower()
    results = []
    for entity in store.entities.values():
        # Filter by type
        if type and entity.get("entity_type") != type:
            continue
        # Simple match on canonical_name, name_variants, or entity_id
        haystack = " ".join(
            [
                entity.get("canonical_name", ""),
                entity.get("entity_id", ""),
                " ".join(entity.get("name_variants", [])),
            ]
        ).lower()
        if q_lower in haystack:
            results.append(entity)
    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="ENTITY_SEARCH",
        summary=f"Searched entities: q={q!r}, hits={len(results)}",
        purpose="INVESTIGATION",
    )
    return results


@router.get("/{entity_id}")
def get_entity(
    entity_id: str,
    user: UserInfo = Depends(require_action("ENTITY_VIEW")),
):
    store = get_store()
    entity = store.entities.get(entity_id)
    if not entity:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Entity {entity_id!r} not found."}},
        )
    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="ENTITY_VIEW",
        summary=f"Viewed entity {entity_id}.",
        purpose="INVESTIGATION",
    )
    return entity


@router.get("/{entity_id}/links")
def get_entity_links(
    entity_id: str,
    user: UserInfo = Depends(require_action("ENTITY_VIEW")),
):
    store = get_store()
    entity = store.entities.get(entity_id)
    if not entity:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Entity {entity_id!r} not found."}},
        )
    mention_ids = set(entity.get("mention_ids", []))
    links = [
        lnk
        for lnk in store.links.values()
        if lnk.get("a_mention_id") in mention_ids or lnk.get("b_mention_id") in mention_ids
    ]
    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="ENTITY_LINKS_VIEW",
        summary=f"Viewed links for entity {entity_id}: {len(links)} found.",
    )
    return links
