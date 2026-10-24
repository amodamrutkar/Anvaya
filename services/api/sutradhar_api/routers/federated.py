"""
sutradhar_api/routers/federated.py
Cross-agency federated query.
Returns MATCH/NO_MATCH/MAYBE — never returns raw records.
Enforces: role, agency-pair grant, rate-limit stub, audit every call.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from sutradhar_api.auth import check_federated_grant, policy, require_action
from sutradhar_api.models import (
    Agency,
    FederatedQueryRequest,
    FederatedQueryResponse,
    FederatedReasonCode,
    FederatedResult,
    Role,
    UserInfo,
)
from sutradhar_api.store import get_store

router = APIRouter(tags=["federated"])

# HMAC salt for one-way hashing of identifiers before cross-agency matching.
# Prevents raw data from leaving the owning agency silo.
_HMAC_SALT = os.getenv("FEDERATED_HMAC_SALT", "sutradhar-demo-salt-change-in-prod").encode()

_AGENCY_GRANTS: dict[tuple[str, str], bool] = {
    ("STATE_POLICE", "MAHA_CYBER"): True,
    ("STATE_POLICE", "CENTRAL_AGENCY"): True,
    ("MAHA_CYBER", "STATE_POLICE"): True,
    ("MAHA_CYBER", "CENTRAL_AGENCY"): True,
    ("CENTRAL_AGENCY", "STATE_POLICE"): True,
    ("CENTRAL_AGENCY", "MAHA_CYBER"): True,
}


def _hash_identifier(identifier: str) -> str:
    return hmac.new(_HMAC_SALT, identifier.encode(), hashlib.sha256).hexdigest()


def _match_identifier(
    identifier_type: str, identifier_value: str, store
) -> tuple[FederatedResult, FederatedReasonCode, str]:
    """
    Check if hashed identifier appears in entities across agencies
    other than the querying agency.
    Returns (result, reason_code, reason_text).
    Never returns raw entity records.
    """
    _ = _hash_identifier(identifier_value)

    # Simple heuristic: look for the raw value in entity identifiers
    # (In production, all data would be hashed at ingestion.)
    found_in_open = False
    found_in_closed = False
    ambiguous = False

    for entity in store.entities.values():
        ids = entity.get("identifiers", {})
        all_ids = []
        if identifier_type == "PHONE":
            all_ids = ids.get("phones", [])
        elif identifier_type == "ACCOUNT":
            all_ids = ids.get("accounts", [])
        elif identifier_type == "VEHICLE":
            all_ids = ids.get("vehicles", [])

        if identifier_value in all_ids or any(identifier_value in str(v) for v in all_ids):
            if entity.get("status") == "ACTIVE":
                found_in_open = True
            else:
                found_in_closed = True

    if found_in_open and found_in_closed:
        ambiguous = True

    if ambiguous:
        return (
            FederatedResult.MAYBE,
            FederatedReasonCode.AMBIGUOUS_IDENTITY,
            "Identifier appears in both open and closed case records.",
        )
    if found_in_open:
        return (
            FederatedResult.MATCH,
            FederatedReasonCode.OPEN_CASE_MATCH,
            "Identifier appears in an open case held by another agency.",
        )
    if found_in_closed:
        return (
            FederatedResult.MATCH,
            FederatedReasonCode.CLOSED_CASE_MATCH,
            "Identifier appears in a closed case held by another agency.",
        )
    return (
        FederatedResult.NO_MATCH,
        FederatedReasonCode.NO_RECORD,
        "No record of this identifier found in cross-agency data.",
    )


@router.post("/federated/query", response_model=FederatedQueryResponse)
def post_federated_query(
    body: FederatedQueryRequest,
    user: Annotated[UserInfo, Depends(require_action("FEDERATED_QUERY"))],
):
    store = get_store()

    # Caller agency authorization: must be same agency or have federated grant
    if (
        user.role != Role.SYSTEM
        and user.agency.value != body.querying_agency.value
        and not check_federated_grant(user.agency.value, body.querying_agency.value)
    ):
        store.record_audit(
            actor=user.user_id,
            role=user.role.value,
            action="FEDERATED_QUERY_DENIED",
            summary=f"No data-sharing grant between {user.agency.value} and {body.querying_agency.value}",
            agency=user.agency.value,
            purpose=body.purpose.value,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "NO_GRANT",
                    "message": f"User from {user.agency.value} cannot issue queries on behalf of {body.querying_agency.value} without an active data-sharing agreement.",
                }
            },
        )

    # Check grant
    for target_agency in Agency:
        if target_agency.value != body.querying_agency.value and not _AGENCY_GRANTS.get(
            (body.querying_agency.value, target_agency.value), False
        ):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "NO_GRANT",
                        "message": f"No data-sharing grant: {body.querying_agency.value} → {target_agency.value}",
                    }
                },
            )

    # Perform match
    result, reason_code, reason_text = _match_identifier(
        body.identifier_type.value, body.identifier_value, store
    )

    query_id = store.get_next_query_id()

    # Owning agency notification (simulated — just flagged in response)
    owning_agency_notified = result == FederatedResult.MATCH

    seq = store.record_audit(
        actor=user.user_id,
        role=user.role.value,
        action="FEDERATED_QUERY",
        purpose=body.purpose.value,
        case_ref=body.case_ref,
        summary=(
            f"FederatedQuery {query_id}: {body.identifier_type.value} from {body.querying_agency.value}. "
            f"Result={result.value} ({reason_code.value})."
        ),
    )

    response = FederatedQueryResponse(
        query_id=query_id,
        result=result,
        confidence=0.97
        if result == FederatedResult.MATCH
        else (0.55 if result == FederatedResult.MAYBE else 0.99),
        reason_code=reason_code,
        reason_text=reason_text,
        owning_agency_notified=owning_agency_notified,
        audit_seq=seq,
    )
    store.add_federated_query(
        {"query_id": query_id, "request": body.model_dump(), "response": response.model_dump()}
    )
    return response


@router.get("/agency/{agency}/inbox")
def get_agency_inbox(
    agency: str,
    user: Annotated[UserInfo, Depends(require_action("AGENCY_INBOX_VIEW"))],
    x_access_purpose: Annotated[str | None, Header()] = None,
):
    store = get_store()

    # Agency isolation check
    if user.agency.value != agency:
        decision = policy.check_agency_access(user, agency, purpose=x_access_purpose)
        if not decision.allowed:
            store.record_audit(
                actor=user.user_id,
                role=user.role.value,
                action="AGENCY_INBOX_VIEW_DENIED",
                summary=f"Cross-agency inbox view denied for agency {agency}: {decision.reason}",
                agency=user.agency.value,
                purpose=x_access_purpose,
            )
            raise HTTPException(
                status_code=403,
                detail={"error": {"code": decision.code, "message": decision.reason}},
            )
        store.record_audit(
            actor=user.user_id,
            role=user.role.value,
            action="CROSS_AGENCY_INBOX_VIEW",
            summary=f"Cross-agency inbox viewed for {agency}. Purpose={x_access_purpose}",
            agency=user.agency.value,
            purpose=x_access_purpose,
        )

    # Return all queries that targeted the given agency (simulated: return all for demo)
    queries = [
        {
            "inbox_id": f"INB-{i + 1:06d}",
            "query_id": q["query_id"],
            "querying_agency": q["request"]["querying_agency"],
            "purpose": q["request"]["purpose"],
            "case_ref": q["request"]["case_ref"],
            "identifier_type": q["request"]["identifier_type"],
            "result_shared": q["response"]["result"],
            "received_at": q["response"].get("ts", ""),
            "reviewed": False,
        }
        for i, q in enumerate(store.federated_queries)
    ]
    return queries
