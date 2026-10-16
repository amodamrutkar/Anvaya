"""
sutradhar_api/models.py
Pydantic request/response models for all API endpoints.
All models are entirely synthetic — no real person or case is represented.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────


class Agency(StrEnum):
    STATE_POLICE = "STATE_POLICE"
    MAHA_CYBER = "MAHA_CYBER"
    CENTRAL_AGENCY = "CENTRAL_AGENCY"


class Role(StrEnum):
    ANALYST = "ANALYST"
    INSPECTOR = "INSPECTOR"
    APPROVING_OFFICER = "APPROVING_OFFICER"
    LIAISON = "LIAISON"
    AUDITOR = "AUDITOR"
    SYSTEM = "SYSTEM"


class IdentifierType(StrEnum):
    PHONE = "PHONE"
    ACCOUNT = "ACCOUNT"
    VEHICLE = "VEHICLE"
    PERSON_NAME_FATHER = "PERSON_NAME_FATHER"


class QueryPurpose(StrEnum):
    INVESTIGATION = "INVESTIGATION"
    ALERT_VERIFICATION = "ALERT_VERIFICATION"
    AUDIT = "AUDIT"


class FederatedResult(StrEnum):
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    MAYBE = "MAYBE"


class FederatedReasonCode(StrEnum):
    OPEN_CASE_MATCH = "OPEN_CASE_MATCH"
    CLOSED_CASE_MATCH = "CLOSED_CASE_MATCH"
    NO_RECORD = "NO_RECORD"
    AMBIGUOUS_IDENTITY = "AMBIGUOUS_IDENTITY"


class ReviewDecision(StrEnum):
    CONFIRM = "CONFIRM"
    REJECT = "REJECT"


class AlertAction(StrEnum):
    CONFIRM = "CONFIRM"
    DISMISS = "DISMISS"


class DossierExportFormat(StrEnum):
    JSON = "JSON"
    json = "json"
    PDF = "PDF"
    pdf = "pdf"


# ─────────────────────────────────────────────────────────────
# Generic
# ─────────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ─────────────────────────────────────────────────────────────
# Auth / User
# ─────────────────────────────────────────────────────────────


class UserInfo(BaseModel):
    user_id: str
    role: Role
    agency: Agency
    display_name: str


# ─────────────────────────────────────────────────────────────
# Federated query
# ─────────────────────────────────────────────────────────────


class FederatedQueryRequest(BaseModel):
    querying_agency: Agency
    identifier_type: IdentifierType
    identifier_value: str = Field(min_length=1)
    purpose: QueryPurpose
    case_ref: str = Field(pattern=r"^(CASE-[A-Z]{3}(-\d{4})?-\d{6}|ALR-\d{6})$")


class FederatedQueryResponse(BaseModel):
    query_id: str
    result: FederatedResult
    confidence: float = Field(ge=0.0, le=1.0)
    reason_code: FederatedReasonCode
    reason_text: str
    owning_agency_notified: bool
    audit_seq: int


# ─────────────────────────────────────────────────────────────
# Review queue
# ─────────────────────────────────────────────────────────────


class ReviewDecisionRequest(BaseModel):
    decision: ReviewDecision
    reason: str = Field(min_length=3)


class UnlinkRequest(BaseModel):
    reason: str = Field(min_length=3)


# ─────────────────────────────────────────────────────────────
# Dossier
# ─────────────────────────────────────────────────────────────


class DossierGenerateRequest(BaseModel):
    community_id: str


class DossierExportRequest(BaseModel):
    confirm: bool
    export_format: DossierExportFormat = DossierExportFormat.json


# ─────────────────────────────────────────────────────────────
# Kumbh
# ─────────────────────────────────────────────────────────────


class KumbhAlertActionRequest(BaseModel):
    action: AlertAction
    reason: str | None = None


# ─────────────────────────────────────────────────────────────
# Generic passthrough (for fixture-mode responses)
# ─────────────────────────────────────────────────────────────


class AnyDict(BaseModel):
    model_config = {"extra": "allow"}

    def model_post_init(self, __context: Any) -> None:
        pass
