"""
sutradhar_api/routers/dossier.py
Draft dossier generation and export.
APPROVING_OFFICER must explicitly set confirm=true to export.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from sutradhar_api.auth import policy, require_action
from sutradhar_api.models import DossierExportRequest, DossierGenerateRequest, UserInfo
from sutradhar_api.store import get_store

router = APIRouter(prefix="/dossier", tags=["dossier"])


@router.post("/generate")
def post_dossier_generate(
    body: DossierGenerateRequest,
    user: Annotated[UserInfo, Depends(require_action("DOSSIER_GENERATE"))],
):
    store = get_store()
    if body.community_id not in store.communities:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Community {body.community_id!r} not found.",
                }
            },
        )
    dossier = store.generate_dossier(community_id=body.community_id, actor=user.user_id)
    # Associate community agencies and generating agency with dossier
    comm = store.communities.get(body.community_id, {})
    agencies = set(comm.get("agencies", []))
    agencies.add(user.agency.value)
    dossier["agencies"] = sorted(agencies)
    seq = store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="DOSSIER_GENERATE",
        summary=f"Generated dossier {dossier['dossier_id']} for community {body.community_id}.",
        agency=user.agency.value,
    )
    result = dict(dossier)
    result["audit_seq"] = seq
    return result


@router.get("/{dossier_id}")
def get_dossier(
    dossier_id: str,
    user: Annotated[UserInfo, Depends(require_action("DOSSIER_VIEW"))],
):
    store = get_store()
    dossier = store.dossiers.get(dossier_id)
    if not dossier:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"code": "NOT_FOUND", "message": f"Dossier {dossier_id!r} not found."}
            },
        )
    store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="DOSSIER_VIEW",
        summary=f"Viewed dossier {dossier_id}.",
        agency=user.agency.value,
    )
    return dossier


@router.post("/{dossier_id}/export")
def post_dossier_export(
    dossier_id: str,
    body: DossierExportRequest,
    user: Annotated[UserInfo, Depends(require_action("DOSSIER_EXPORT"))],
    x_access_purpose: Annotated[str | None, Header()] = None,
):
    if not body.confirm:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "CONFIRM_REQUIRED",
                    "message": "confirm must be true to export a dossier.",
                }
            },
        )
    store = get_store()
    dossier = store.dossiers.get(dossier_id)
    if not dossier:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"code": "NOT_FOUND", "message": f"Dossier {dossier_id!r} not found."}
            },
        )

    # Agency isolation check
    dossier_agencies = dossier.get("agencies", [])
    if dossier_agencies and user.agency.value not in dossier_agencies:
        decision = policy.check_agency_access(user, dossier_agencies, purpose=x_access_purpose)
        if not decision.allowed:
            store.record_audit(
                actor=user.user_id,
                role=user.role.value,
                action="DOSSIER_EXPORT_DENIED",
                summary=f"Cross-agency export denied for dossier {dossier_id}: {decision.reason}",
                agency=user.agency.value,
                purpose=x_access_purpose,
            )
            raise HTTPException(
                status_code=403,
                detail={"error": {"code": decision.code, "message": decision.reason}},
            )

    exported_at = datetime.now(UTC).isoformat()
    seq = store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="DOSSIER_EXPORT",
        summary=f"Exported dossier {dossier_id} in format {body.export_format.value}.",
        agency=user.agency.value,
        purpose=x_access_purpose,
    )
    return {
        "dossier_id": dossier_id,
        "export_format": body.export_format.value,
        "exported_at": exported_at,
        "actor": user.user_id,
        "audit_seq": seq,
        "content": {**dossier, "disclaimer": dossier.get("disclaimer", "")},
    }
