"""Pydantic v2 models mirroring Main PRD Section 8.3 — Mentions, Entities, Links, Decisions."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ── Enums ────────────────────────────────────────────────────────────────────


class Agency(StrEnum):
    STATE_POLICE = "STATE_POLICE"
    MAHA_CYBER = "MAHA_CYBER"
    CENTRAL_AGENCY = "CENTRAL_AGENCY"


AGENCY_CODE = {
    Agency.STATE_POLICE: "SPO",
    Agency.MAHA_CYBER: "CYB",
    Agency.CENTRAL_AGENCY: "CEN",
}


class RecordType(StrEnum):
    FIR = "FIR"
    CHARGESHEET = "CHARGESHEET"
    COMPLAINT = "COMPLAINT"
    SEIZURE_REPORT = "SEIZURE_REPORT"


class CrimeType(StrEnum):
    CYBER_FRAUD = "CYBER_FRAUD"
    EXTORTION = "EXTORTION"
    NARCOTICS = "NARCOTICS"
    MISSING_PERSON = "MISSING_PERSON"


class MentionRole(StrEnum):
    ACCUSED = "ACCUSED"
    SUSPECT = "SUSPECT"
    VICTIM = "VICTIM"
    COMPLAINANT = "COMPLAINANT"
    WITNESS = "WITNESS"
    ACCOUNT_HOLDER = "ACCOUNT_HOLDER"


class ExtractionMethod(StrEnum):
    FORM = "FORM"
    REGEX = "REGEX"
    LLM = "LLM"


class NameScript(StrEnum):
    DEVANAGARI = "DEVANAGARI"
    LATIN = "LATIN"
    MIXED = "MIXED"


class EntityType(StrEnum):
    PERSON = "PERSON"
    PHONE = "PHONE"
    ACCOUNT = "ACCOUNT"
    VEHICLE = "VEHICLE"
    ADDRESS = "ADDRESS"


class Band(StrEnum):
    AUTO = "AUTO"
    REVIEW = "REVIEW"
    SEPARATE = "SEPARATE"


class LinkStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PENDING_REVIEW = "PENDING_REVIEW"
    UNLINKED = "UNLINKED"


class EntityStatus(StrEnum):
    ACTIVE = "ACTIVE"
    MERGED = "MERGED"


class ClueDirection(StrEnum):
    FOR = "FOR"
    AGAINST = "AGAINST"


class ExplanationSource(StrEnum):
    TEMPLATE = "TEMPLATE"
    LLM = "LLM"


class DecisionType(StrEnum):
    CONFIRM = "CONFIRM"
    REJECT = "REJECT"
    UNLINK = "UNLINK"


# ── Source record (what M1 writes, M2 reads) ────────────────────────────────


class AccusedField(BaseModel):
    """A single accused entry in form_fields."""

    name: str = ""
    father_name: str = ""
    age: int | None = None
    address: str = ""
    phone: str = ""
    alias: str = ""


class FormFields(BaseModel):
    accused: list[AccusedField] = Field(default_factory=list)
    complainant: dict[str, Any] | None = None
    victims: list[dict[str, Any]] = Field(default_factory=list)
    accounts: list[dict[str, Any]] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    vehicles: list[str] = Field(default_factory=list)


class SourceRecord(BaseModel):
    """A single agency source record (PRD 8.2)."""

    record_id: str
    agency: str
    record_type: str = ""
    crime_type: str = ""
    case_ref: str = ""
    district: str = ""
    station: str = ""
    filed_date: str = ""
    language: str = "en"
    sections: list[str] = Field(default_factory=list)
    form_fields: dict[str, Any] | None = None
    narrative: str = ""


# ── ER output: Mention ──────────────────────────────────────────────────────


class Mention(BaseModel):
    """A single mention extracted from a source record (PRD 8.3)."""

    mention_id: str
    record_id: str
    agency: str
    role: str = ""
    name_raw: str = ""
    name_norm: str = ""
    name_script: str = "LATIN"
    father_name_raw: str = ""
    father_name_norm: str = ""
    age: int | None = None
    address_raw: str = ""
    district: str = ""
    phones: list[str] = Field(default_factory=list)
    accounts: list[str] = Field(default_factory=list)
    vehicles: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    extraction_method: str = "FORM"
    extraction_confidence: float = 0.99


# ── ER output: Reason / Link ────────────────────────────────────────────────


class Reason(BaseModel):
    """A single explainable reason for/against a link."""

    clue: str
    direction: str  # FOR or AGAINST
    weight: float
    detail: str = ""


class Link(BaseModel):
    """A pairwise link between two person mentions (PRD 8.3)."""

    link_id: str
    a_mention_id: str
    b_mention_id: str
    score: float
    band: str  # AUTO, REVIEW, SEPARATE
    reasons: list[Reason] = Field(default_factory=list)
    explanation_text: str = ""
    explanation_source: str = "TEMPLATE"
    status: str = "ACTIVE"
    decided_by: str | None = None
    decided_at: str | None = None
    decision_reason: str | None = None


# ── ER output: Entity identifiers ───────────────────────────────────────────


class EntityIdentifiers(BaseModel):
    phones: list[str] = Field(default_factory=list)
    accounts: list[str] = Field(default_factory=list)
    vehicles: list[str] = Field(default_factory=list)


class Entity(BaseModel):
    """A resolved entity (PRD 8.3)."""

    entity_id: str
    entity_type: str  # PERSON, PHONE, ACCOUNT, VEHICLE, ADDRESS
    canonical_name: str = ""
    name_variants: list[str] = Field(default_factory=list)
    identifiers: EntityIdentifiers = Field(default_factory=EntityIdentifiers)
    mention_ids: list[str] = Field(default_factory=list)
    record_ids: list[str] = Field(default_factory=list)
    agencies: list[str] = Field(default_factory=list)
    districts: list[str] = Field(default_factory=list)
    min_link_confidence: float | None = None
    status: str = "ACTIVE"


# ── Decisions (written by backend, read by M2) ──────────────────────────────


class Decision(BaseModel):
    """A reviewer decision on a link (PRD 8.3)."""

    link_id: str
    decision: str  # CONFIRM, REJECT, UNLINK
    reason: str = ""
    actor: str = ""
    ts: str = ""


# ── Dev labels (data/dev/dev_labels.jsonl) ──────────────────────────────────


class DevLabel(BaseModel):
    """Ground-truth label for tuning on data/dev."""

    mention_id: str
    person_id: str
