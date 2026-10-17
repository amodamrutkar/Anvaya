"""
sutradhar_api/routers/audit.py
Audit log endpoints.
GET /audit — AUDITOR only
GET /audit/verify — all authenticated users (integrity check)
POST /audit/dev/tamper — DEMO_TAMPER=1 only (live demo use)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from sutradhar_api.auth import require_action, require_auth
from sutradhar_api.config import DEMO_TAMPER
from sutradhar_api.models import UserInfo
from sutradhar_api.store import get_store

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def get_audit_log(
    limit: int = 50,
    offset: int = 0,
    user: UserInfo = Depends(require_action("AUDIT_LOG_VIEW")),
):
    store = get_store()
    entries = store.audit_log[offset : offset + limit]
    return entries


@router.get("/verify")
def get_audit_verify(
    user: UserInfo = Depends(require_auth),
):
    store = get_store()
    result = store.verify_audit_chain()
    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="AUDIT_VERIFY",
        summary=f"Verified audit chain: valid={result['valid']}.",
        purpose="AUDIT",
    )
    return result


@router.post("/dev/tamper")
def post_audit_tamper(
    user: UserInfo = Depends(require_auth),
):
    if not DEMO_TAMPER:
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "TAMPER_DISABLED",
                    "message": "DEMO_TAMPER is not enabled. Set DEMO_TAMPER=1 in .env for live tamper demonstration.",
                }
            },
        )
    store = get_store()
    result = store.tamper_audit_for_demo()
    return result


@router.post("/dev/repair")
def post_audit_repair(
    user: UserInfo = Depends(require_auth),
):
    if not DEMO_TAMPER:
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "TAMPER_DISABLED",
                    "message": "DEMO_TAMPER is not enabled. Set DEMO_TAMPER=1 in .env for live tamper demonstration.",
                }
            },
        )
    store = get_store()
    result = store.repair_audit_for_demo()
    return result
