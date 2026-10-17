"""
Pydantic data models for Sutradhar Graph and Network Analytics.

Mirrors main PRD Section 8.4 specifications for graph artifacts:
- graph.json (nodes & edges)
- communities.json (syndicate detection)
- roles.json (kingpin, broker, recruiter, controller)
- bridges.json (cross-crime, cross-agency hubs)
- mule_chains.json (layered account money routing)
- dossiers/DOS-*.json (MCOCA-readiness dossiers)
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# 1. Graph Model (graph.json)
# --------------------------------------------------------------------------- #
NodeType = Literal["PERSON", "PHONE", "ACCOUNT", "VEHICLE", "ADDRESS", "CASE", "PLACE"]
EdgeType = Literal[
    "USES",
    "OWNS",
    "ACCUSED_IN",
    "VICTIM_IN",
    "TRANSFERRED_TO",
    "RECRUITED",
    "CO_ACCUSED_WITH",
    "SEEN_AT",
    "LIVES_AT",
]
EdgeStrength = Literal["STRONG", "WEAK"]


class NodeModel(BaseModel):
    id: str
    type: NodeType
    label: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class EdgeModel(BaseModel):
    id: str
    source: str
    target: str
    type: EdgeType
    strength: EdgeStrength = "STRONG"
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    attributes: dict[str, Any] = Field(default_factory=dict)


class GraphData(BaseModel):
    nodes: list[NodeModel]
    edges: list[EdgeModel]


# --------------------------------------------------------------------------- #
# 2. Community Model (communities.json)
# --------------------------------------------------------------------------- #
class TimelineActivity(BaseModel):
    month: str
    case_count: int


class CommunityModel(BaseModel):
    community_id: str
    label: str
    crime_types: list[str]
    members: list[str]
    member_count: int
    cohesion: float
    districts: list[str]
    agencies: list[str]
    case_ids: list[str]
    first_activity: str
    last_activity: str
    continuing_activity: bool
    timeline: list[TimelineActivity] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# 3. Roles Model (roles.json)
# --------------------------------------------------------------------------- #
RoleName = Literal[
    "BROKER",
    "KINGPIN_CANDIDATE",
    "RECRUITER",
    "CONTROLLER",
    "LIKELY_ORGANISER",
    "LIKELY_DECEIVED_HOLDER",
    "MEMBER",
]


class RoleAssignment(BaseModel):
    entity_id: str
    role: RoleName
    score: float
    reasons: list[str]
    evidence_record_ids: list[str]
    community_id: str | None = None


# --------------------------------------------------------------------------- #
# 4. Bridges Model (bridges.json)
# --------------------------------------------------------------------------- #
class BridgeModel(BaseModel):
    node_id: str
    node_type: NodeType
    label: str
    communities: list[str]
    crime_types: list[str]
    linked_person_ids: list[str]
    evidence_record_ids: list[str]
    reasons: list[str]


# --------------------------------------------------------------------------- #
# 5. Mule Chains Model (mule_chains.json)
# --------------------------------------------------------------------------- #
AccountClass = Literal["LIKELY_ORGANISER", "LIKELY_DECEIVED", "UNCERTAIN"]


class MuleAccountModel(BaseModel):
    account_key: str
    holder_entity_id: str
    holder_name: str
    layer: int
    classification: AccountClass
    score: float
    reasons: list[str]
    inflow: float = 0.0
    outflow: float = 0.0
    fan_in: int = 0
    fan_out: int = 0
    median_passthrough_minutes: float = 0.0
    complaint_count: int = 0


class MuleTransferEdge(BaseModel):
    from_account: str
    to_account: str
    amount: float
    ts: str
    channel: str = "UPI"


class MuleChainModel(BaseModel):
    chain_id: str
    total_amount: float
    victims_count: int
    max_depth: int
    layer1_baseline_depth: int = 1
    depth_gained: int
    accounts: list[MuleAccountModel]
    edges: list[MuleTransferEdge]
    recruiter_candidates: list[str] = Field(default_factory=list)
    controller_candidates: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# 6. Dossier Model (dossiers/DOS-*.json)
# --------------------------------------------------------------------------- #
class LegalParamsModel(BaseModel):
    act_name: str
    section: str
    lookback_years: int
    min_chargesheets_required: int
    min_gang_members_required: int
    verified: bool = False
    disclaimer: str


class LinkedCaseItem(BaseModel):
    case_ref: str
    crime_type: str
    agency: str
    filed_date: str
    station: str
    source_record_ids: list[str]


class PriorChargesheetItem(BaseModel):
    case_ref: str
    sections: list[str]
    filed_date: str
    source_record_ids: list[str]


class AssociateItem(BaseModel):
    entity_id: str
    name: str
    role: str
    role_score: float
    role_reasons: list[str]
    source_record_ids: list[str]


class FinancialLinkItem(BaseModel):
    from_account: str
    to_account: str
    amount: float
    source_record_ids: list[str]


class TimelineItem(BaseModel):
    date: str
    event_type: str
    description: str
    source_record_ids: list[str]


class EvidenceGapItem(BaseModel):
    gap_type: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    description: str


class DossierModel(BaseModel):
    dossier_id: str
    community_id: str
    community_label: str
    status: Literal["DRAFT", "APPROVED"] = "DRAFT"
    generated_at: str
    disclaimer: str
    legal_params: LegalParamsModel
    summary: str
    linked_cases: list[LinkedCaseItem]
    prior_chargesheets: list[PriorChargesheetItem]
    associates: list[AssociateItem]
    financial_links: list[FinancialLinkItem]
    timeline: list[TimelineItem]
    evidence_gaps: list[EvidenceGapItem]
