"""
sutradhar_api/routers/review.py
Human-in-the-loop review queue and link management endpoints.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException

from sutradhar_api.auth import require_action
from sutradhar_api.models import ReviewDecisionRequest, UnlinkRequest, UserInfo
from sutradhar_api.store import get_store

router = APIRouter(tags=["review"])


@router.get("/review-queue")
def get_review_queue(
    user: UserInfo = Depends(require_action("REVIEW_QUEUE_VIEW")),
):
    store = get_store()
    queue = [lnk for lnk in store.links.values() if lnk.get("band") == "REVIEW" and lnk.get("status") == "PENDING_REVIEW"]
    return queue


@router.post("/review-queue/{link_id}/decision")
def post_review_decision(
    link_id: str,
    body: ReviewDecisionRequest,
    user: UserInfo = Depends(require_action("REVIEW_DECISION")),
):
    store = get_store()
    link = store.links.get(link_id)
    if not link:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": f"Link {link_id!r} not found."}})
    now = datetime.now(timezone.utc).isoformat()
    new_status = "ACTIVE" if body.decision.value == "CONFIRM" else "UNLINKED"
    store.update_link(link_id, status=new_status, decided_by=user.user_id, decided_at=now, reason=body.reason)
    seq = store.record_audit(
        actor=user.user_id, role=user.role.value,
        action=f"REVIEW_{body.decision.value}",
        summary=f"Link {link_id}: {body.decision.value}. Reason: {body.reason!r}",
    )
    return {"link_id": link_id, "decision": body.decision.value, "actor": user.user_id, "ts": now, "audit_seq": seq}


@router.post("/links/{link_id}/unlink")
def post_unlink(
    link_id: str,
    body: UnlinkRequest,
    user: UserInfo = Depends(require_action("UNLINK")),
):
    store = get_store()
    link = store.links.get(link_id)
    if not link:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": f"Link {link_id!r} not found."}})
    now = datetime.now(timezone.utc).isoformat()
    store.update_link(link_id, status="UNLINKED", decided_by=user.user_id, decided_at=now, reason=body.reason)
    seq = store.record_audit(
        actor=user.user_id, role=user.role.value, action="UNLINK",
        summary=f"Unlinked {link_id}. Reason: {body.reason!r}",
    )
    return {"link_id": link_id, "status": "UNLINKED", "actor": user.user_id, "ts": now, "audit_seq": seq}
