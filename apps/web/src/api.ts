const API_BASE_URL = typeof import.meta.env.VITE_API_BASE_URL === 'string'
  ? import.meta.env.VITE_API_BASE_URL
  : 'http://localhost:8000';

// ─────────────────────────────────────────────────────────────
// Enums & Literals matching FastAPI models.py
// ─────────────────────────────────────────────────────────────

export type Agency = 'STATE_POLICE' | 'MAHA_CYBER' | 'CENTRAL_AGENCY';
export type Role = 'ANALYST' | 'INSPECTOR' | 'APPROVING_OFFICER' | 'LIAISON' | 'AUDITOR' | 'SYSTEM';
export type IdentifierType = 'PHONE' | 'ACCOUNT' | 'VEHICLE' | 'PERSON_NAME_FATHER';
export type QueryPurpose = 'INVESTIGATION' | 'ALERT_VERIFICATION' | 'AUDIT';
export type FederatedResult = 'MATCH' | 'NO_MATCH' | 'MAYBE';
export type FederatedReasonCode = 'OPEN_CASE_MATCH' | 'CLOSED_CASE_MATCH' | 'NO_RECORD' | 'AMBIGUOUS_IDENTITY';
export type ReviewDecision = 'CONFIRM' | 'REJECT';
export type AlertAction = 'CONFIRM' | 'DISMISS';
export type DossierExportFormat = 'JSON' | 'json' | 'PDF' | 'pdf';

// ─────────────────────────────────────────────────────────────
// User & Demo Auth Context
// ─────────────────────────────────────────────────────────────

export interface UserContext {
  userId: string;
  role: string;
  agency: string;
  displayName: string;
}

export const DEMO_USERS: UserContext[] = [
  { userId: 'analyst1', role: 'ANALYST', agency: 'STATE_POLICE', displayName: 'Analyst (State Police)' },
  { userId: 'analyst2', role: 'ANALYST', agency: 'MAHA_CYBER', displayName: 'Analyst (Maha Cyber)' },
  { userId: 'inspector1', role: 'INSPECTOR', agency: 'CENTRAL_AGENCY', displayName: 'Inspector (Central Agency)' },
  { userId: 'officer1', role: 'APPROVING_OFFICER', agency: 'STATE_POLICE', displayName: 'Approving Officer' },
  { userId: 'liaison1', role: 'LIAISON', agency: 'STATE_POLICE', displayName: 'Liaison Officer (State Police)' },
  { userId: 'auditor1', role: 'AUDITOR', agency: 'CENTRAL_AGENCY', displayName: 'Auditor (Audit Logs)' },
];

export interface UserInfo {
  user_id: string;
  role: Role | string;
  agency: Agency | string;
  display_name: string;
}

// ─────────────────────────────────────────────────────────────
// System & Metrics Models
// ─────────────────────────────────────────────────────────────

export interface HealthStatus {
  status: string;
  simulated: boolean;
  dataset_version: string;
  recompute_status: string;
  entities_loaded: number;
  links_loaded: number;
  communities_loaded: number;
  kumbh_events_loaded: number;
}

export interface MetricsReport {
  dataset_version?: string;
  message?: string;
  er?: {
    auto_precision: number;
    auto_recall: number;
    overall_recall: number;
    wrong_merge_rate: number;
    review_share: number;
    by_difficulty?: {
      easy?: { precision: number; recall: number };
      hard?: { precision: number; recall: number };
    };
  };
  network?: {
    planted: number;
    recovered: number;
    kingpin_rank?: number;
    bridges_found: number;
    bridges_planted: number;
  };
  mule?: {
    max_depth: number;
    layer1_baseline_depth?: number;
    recruiter_detected: boolean;
    deceived_precision: number;
  };
  time_saved?: {
    manual_minutes_estimate?: number;
    system_seconds?: number;
  };
}

// ─────────────────────────────────────────────────────────────
// Entity Resolution Models
// ─────────────────────────────────────────────────────────────

export interface EntityIdentifiers {
  phones?: string[];
  accounts?: string[];
  vehicles?: string[];
}

export interface Entity {
  entity_id: string;
  entity_type: 'PERSON' | 'PHONE' | 'ACCOUNT' | 'VEHICLE' | 'ADDRESS' | string;
  canonical_name: string;
  name_variants?: string[];
  identifiers?: EntityIdentifiers;
  mention_ids?: string[];
  record_ids?: string[];
  agencies?: string[];
  districts?: string[];
  min_link_confidence?: number | null;
  status?: 'ACTIVE' | 'MERGED' | 'UNLINKED' | string;
}

export interface EntityLinkClue {
  clue: string;
  direction: 'FOR' | 'AGAINST';
  weight: number;
  detail?: string;
}

export interface EntityLink {
  link_id: string;
  a_mention_id: string;
  b_mention_id: string;
  score: number;
  band: 'AUTO' | 'REVIEW' | 'SEPARATE' | string;
  reasons: EntityLinkClue[];
  explanation_text: string;
  explanation_source?: 'TEMPLATE' | 'LLM' | string;
  status: 'ACTIVE' | 'PENDING_REVIEW' | 'UNLINKED' | string;
  decided_by?: string | null;
  decided_at?: string | null;
  decision_reason?: string | null;
  // Fallback compatibility properties that current UI code references
  entity_id_a?: string;
  entity_id_b?: string;
  name_a?: string;
  name_b?: string;
  reason?: string;
}

// ─────────────────────────────────────────────────────────────
// Graph & Community Models
// ─────────────────────────────────────────────────────────────

export interface Community {
  community_id: string;
  label?: string;
  size?: number;
  crime_types?: string[];
  districts?: string[];
  agencies?: string[];
  cohesion?: number;
  first_activity?: string;
  last_activity?: string;
  case_ids?: string[];
  density?: string | number;
  member_count?: number;
  members?: string[];
  entity_ids?: string[];
  risk_level?: string;
}

export interface GraphNode {
  id: string;
  type?: string;
  label?: string;
  props?: Record<string, any>;
  agencies?: string[];
  crime_types?: string[];
}

export interface GraphEdge {
  edge_id?: string;
  source: string;
  target: string;
  type?: string;
  strength?: 'STRONG' | 'WEAK' | string;
  evidence?: string[];
  confidence?: number;
  weight?: number | null;
}

export interface RoleReason {
  signal: string;
  value?: number;
  text: string;
}

export interface RoleAssignment {
  entity_id: string;
  community_id: string;
  role: 'BROKER' | 'KINGPIN_CANDIDATE' | 'RECRUITER' | 'CONTROLLER' | 'LIKELY_ORGANISER' | 'LIKELY_DECEIVED_HOLDER' | string;
  score: number;
  reasons: RoleReason[];
  evidence_record_ids: string[];
}

export interface CommunityDetail extends Community {
  nodes?: GraphNode[];
  edges?: GraphEdge[];
  roles?: RoleAssignment[];
}

export interface NeighborhoodGraph {
  nodes: (Entity | GraphNode)[];
  edges: (EntityLink | GraphEdge)[];
}

export interface GraphPathEdge {
  from: string;
  to: string;
  type?: string;
  evidence?: string[];
}

export interface GraphPathResponse {
  from_id?: string | null;
  to_id?: string | null;
  found: boolean;
  hops: number;
  path: (string | null)[];
  nodes?: (GraphNode | Entity | Record<string, any>)[];
  edges: GraphPathEdge[];
  evidence?: string[];
  requires_investigator_review?: boolean;
}

export interface BridgeEntity {
  entity_id: string;
  entity_type: string;
  communities: string[];
  crime_types: string[];
  linked_person?: string;
  evidence_record_ids: string[];
}

// ─────────────────────────────────────────────────────────────
// Mule Chain Models
// ─────────────────────────────────────────────────────────────

export interface MuleAccountReason {
  signal: string;
  text: string;
}

export interface MuleAccount {
  account_id: string;
  layer: number;
  inflow: number;
  outflow: number;
  median_pass_through_minutes: number;
  complaint_count: number;
  classification: 'LIKELY_DECEIVED' | 'LIKELY_ORGANISER' | 'UNCERTAIN' | string;
  score: number;
  reasons: MuleAccountReason[];
}

export interface MuleEdge {
  from: string;
  to: string;
  amount: number;
  ts: string;
}

export interface MuleChain {
  chain_id: string;
  community_id: string;
  total_amount: number;
  victims_count: number;
  max_depth: number;
  layer1_only_accounts: number;
  accounts: MuleAccount[];
  recruiter_candidates: string[];
  controller_candidates: string[];
  edges: MuleEdge[];
}

// ─────────────────────────────────────────────────────────────
// Dossier Models
// ─────────────────────────────────────────────────────────────

export interface DossierSectionItem {
  case_id?: string;
  text?: string;
  source_record_ids?: string[];
  entity_id?: string;
  role?: string;
  date?: string;
  event?: string;
  severity?: 'LOW' | 'MEDIUM' | 'HIGH' | string;
}

export interface DossierSections {
  linked_cases?: DossierSectionItem[];
  prior_chargesheets?: DossierSectionItem[];
  associates?: DossierSectionItem[];
  financial_links?: DossierSectionItem[];
  timeline?: DossierSectionItem[];
  evidence_gaps?: DossierSectionItem[];
}

export interface Dossier {
  dossier_id: string;
  community_id: string;
  generated_at?: string;
  status?: string;
  summary?: string;
  legal_params?: {
    lookback_years?: number;
    min_chargesheets?: number;
    verified?: boolean;
  };
  sections?: DossierSections;
  disclaimer?: string;
  audit_seq?: number;
}

export interface DossierExportRequest {
  confirm: boolean;
  export_format?: DossierExportFormat;
}

export interface DossierExportResponse {
  dossier_id: string;
  export_format: string;
  exported_at: string;
  actor: string;
  audit_seq: number;
  content: Dossier;
}

// ─────────────────────────────────────────────────────────────
// Cross-Agency Federated Query Models
// ─────────────────────────────────────────────────────────────

export interface FederatedQueryRequest {
  querying_agency: Agency;
  identifier_type: IdentifierType;
  identifier_value: string;
  purpose: QueryPurpose;
  case_ref: string;
}

export interface FederatedQueryResponse {
  query_id: string;
  result: FederatedResult;
  confidence: number;
  reason_code: FederatedReasonCode;
  reason_text: string;
  owning_agency_notified: boolean;
  audit_seq: number;
}

export interface AgencyInboxItem {
  inbox_id: string;
  query_id: string;
  querying_agency: Agency | string;
  purpose: QueryPurpose | string;
  case_ref: string;
  identifier_type: IdentifierType | string;
  result_shared: FederatedResult | string;
  received_at: string;
  reviewed: boolean;
}

// ─────────────────────────────────────────────────────────────
// Audit & Tamper Models
// ─────────────────────────────────────────────────────────────

export interface AuditEntry {
  seq: number;
  ts: string;
  actor: string;
  role: string;
  action: string;
  purpose?: string | null;
  case_ref?: string | null;
  summary: string;
  prev_hash: string;
  hash: string;
}

export interface AuditVerifyResult {
  valid: boolean;
  entries: number;
  head_hash: string;
  broken_at: number | null;
  // Compatibility properties referenced in current UI
  total_entries?: number;
  tampered_seq?: number | null;
}

export interface AuditTamperResponse {
  tampered_seq: number | null;
  message: string;
}

export interface AuditRepairResponse {
  repaired_seq: number | null;
  message: string;
}

// ─────────────────────────────────────────────────────────────
// Connectors Status Model
// ─────────────────────────────────────────────────────────────

export interface ConnectorStatus {
  connector_id: string;
  agency: string;
  description: string;
  simulated: boolean;
  status: 'ONLINE' | 'OFFLINE' | string;
}

// ─────────────────────────────────────────────────────────────
// Kumbh Mela Models
// ─────────────────────────────────────────────────────────────

export interface KumbhZone {
  zone: string;
  state: 'NORMAL' | 'ALERT' | string;
  active_alerts: number;
}

export interface KumbhAlert {
  alert_id: string;
  event_id?: string;
  zone: string;
  alert_type: string;
  confidence: number;
  reason: string;
  summary?: string;
  state: 'OPEN' | 'CONFIRMED' | 'DISMISS' | 'DISMISSED' | string;
  created_at: string;
  confirmed_at?: string | null;
  dismissed_at?: string | null;
}

export interface KumbhSimulationResponse {
  message?: string;
  event_played: any | null;
  alert_raised: boolean;
  alert_id?: string | null;
  reason?: string | null;
  audit_seq?: number;
  // Compatibility properties referenced in current UI
  event_type?: string;
  zone?: string;
}

export interface KumbhObservation {
  event_id: string;
  event_type: string;
  ts: string;
  zone: string;
  location_info?: Record<string, any>;
  related_ids?: string[];
  source_agency?: string;
  status?: string;
  provenance?: Record<string, any>;
}

export interface KumbhSignal {
  signal_id: string;
  event_id: string;
  signal_type: string;
  confidence: number;
  evidence_tier: 'STRONG' | 'MEDIUM' | 'WEAK' | string;
  description: string;
  reasons: string[];
  evidence: string[];
  provenance?: Record<string, any> | Record<string, any>[];
  network_context?: Record<string, any> | null;
  requires_investigator_review: boolean;
  action: string;
}

export interface KumbhCluster {
  cluster_id: string;
  cluster_type: 'SHARED_INFRASTRUCTURE_CLUSTER' | 'SHARED_ENTITY_CLUSTER' | 'SPATIO_TEMPORAL_BURST' | string;
  member_events: string[];
  shared_evidence: string[];
  confidence: number;
  provenance?: Record<string, any>;
  explanation: string;
  requires_investigator_review: boolean;
  action: string;
}

export interface KumbhEventIntelligence {
  event_id: string;
  event: Record<string, any>;
  observation: Record<string, any>;
  signals: KumbhSignal[] | Record<string, any>[];
  network_context: Record<string, any> | null;
  cluster: KumbhCluster | Record<string, any> | Record<string, any>[] | null;
  requires_investigator_review: boolean;
}

// ─────────────────────────────────────────────────────────────
// Generic Fetch Helper
// ─────────────────────────────────────────────────────────────

async function apiRequest<T>(endpoint: string, options: RequestInit = {}, userId = 'analyst1'): Promise<T> {
  const baseUrl = API_BASE_URL.replace(/\/+$/, '');
  const cleanEndpoint = endpoint.replace(/^\/+/, '');
  const url = baseUrl ? `${baseUrl}/${cleanEndpoint}` : `/${cleanEndpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    'X-Demo-User': userId,
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const message = errorData?.detail?.error?.message || errorData?.detail || `HTTP ${res.status}: ${res.statusText}`;
      throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
    }
    return (await res.json()) as T;
  } catch (err: unknown) {
    if (err instanceof Error) {
      throw err;
    }
    throw new Error(String(err));
  }
}

// ─────────────────────────────────────────────────────────────
// Sutradhar API Wrapper Client
// ─────────────────────────────────────────────────────────────

export const api = {
  // System Health, Info & Connectors
  getHealth: () => apiRequest<HealthStatus>('/health', { method: 'GET' }),
  getMe: (userId = 'analyst1') => apiRequest<UserInfo>('/me', { method: 'GET' }, userId),
  getMetrics: (userId = 'analyst1') =>
    apiRequest<MetricsReport>('/metrics', { method: 'GET' }, userId),
  getConnectorsStatus: (userId = 'analyst1') =>
    apiRequest<ConnectorStatus[]>('/connectors/status', { method: 'GET' }, userId),

  // Entities
  searchEntities: (q: string, type?: string, userId = 'analyst1') => {
    const params = new URLSearchParams({ q });
    if (type) params.set('type', type);
    return apiRequest<Entity[]>(`/entities/search?${params.toString()}`, { method: 'GET' }, userId);
  },
  getEntity: (id: string, userId = 'analyst1') =>
    apiRequest<Entity>(`/entities/${encodeURIComponent(id)}`, { method: 'GET' }, userId),
  getEntityLinks: (id: string, userId = 'analyst1') =>
    apiRequest<EntityLink[]>(`/entities/${encodeURIComponent(id)}/links`, { method: 'GET' }, userId),

  // Graph Analytics, Topology, Roles, Bridges & Mule Chains
  getCommunities: (userId = 'analyst1') =>
    apiRequest<Community[]>('/graph/communities', { method: 'GET' }, userId),
  getCommunity: (id: string, userId = 'analyst1') =>
    apiRequest<CommunityDetail>(`/graph/communities/${encodeURIComponent(id)}`, { method: 'GET' }, userId),
  getNeighborhood: (entityId: string, hops = 2, userId = 'analyst1') =>
    apiRequest<NeighborhoodGraph>(`/graph/entity/${encodeURIComponent(entityId)}/neighborhood?hops=${hops}`, { method: 'GET' }, userId),
  getGraphPath: (
    fromId: string,
    toId: string,
    maxHopsOrUserId?: number | string,
    maybeUserId?: string
  ) => {
    let maxHops = 5;
    let userId = 'analyst1';
    if (typeof maxHopsOrUserId === 'number') {
      maxHops = maxHopsOrUserId;
      if (maybeUserId) userId = maybeUserId;
    } else if (typeof maxHopsOrUserId === 'string') {
      userId = maxHopsOrUserId;
    }
    return apiRequest<GraphPathResponse>(
      `/graph/path?from=${encodeURIComponent(fromId)}&to=${encodeURIComponent(toId)}&max_hops=${maxHops}`,
      { method: 'GET' },
      userId
    );
  },
  getRoles: (communityId?: string, userId = 'analyst1') => {
    const params = communityId ? `?community_id=${encodeURIComponent(communityId)}` : '';
    return apiRequest<RoleAssignment[]>(`/roles${params}`, { method: 'GET' }, userId);
  },
  getBridges: (userId = 'analyst1') =>
    apiRequest<BridgeEntity[]>('/bridges', { method: 'GET' }, userId),
  getMuleChains: (communityId?: string, userId = 'analyst1') => {
    const params = communityId ? `?community_id=${encodeURIComponent(communityId)}` : '';
    return apiRequest<MuleChain[]>(`/mule/chains${params}`, { method: 'GET' }, userId);
  },

  // Review Queue & Link Disambiguation
  getReviewQueue: (userId = 'analyst1') =>
    apiRequest<EntityLink[]>('/review-queue', { method: 'GET' }, userId),
  submitDecision: (linkId: string, decision: 'CONFIRM' | 'SEPARATE' | 'REJECT', reason: string, userId = 'analyst1') =>
    apiRequest<{ link_id: string; decision: string; actor: string; ts: string; audit_seq: number }>(
      `/review-queue/${encodeURIComponent(linkId)}/decision`,
      {
        method: 'POST',
        body: JSON.stringify({ decision, reason }),
      },
      userId
    ),
  unlink: (linkId: string, reason: string, userId = 'analyst1') =>
    apiRequest<{ link_id: string; status: string; actor: string; ts: string; audit_seq: number }>(
      `/links/${encodeURIComponent(linkId)}/unlink`,
      {
        method: 'POST',
        body: JSON.stringify({ reason }),
      },
      userId
    ),

  // Dossier Lifecycle & Export
  generateDossier: (communityId: string, userId = 'analyst1') =>
    apiRequest<Dossier>(
      '/dossier/generate',
      {
        method: 'POST',
        body: JSON.stringify({ community_id: communityId, purpose: 'INVESTIGATION' }),
      },
      userId
    ),
  getDossier: (dossierId: string, userId = 'analyst1') =>
    apiRequest<Dossier>(`/dossier/${encodeURIComponent(dossierId)}`, { method: 'GET' }, userId),
  exportDossier: (
    dossierId: string,
    request: DossierExportRequest = { confirm: true, export_format: 'json' },
    userId = 'officer1'
  ) =>
    apiRequest<DossierExportResponse>(
      `/dossier/${encodeURIComponent(dossierId)}/export`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      },
      userId
    ),

  // Cross-Agency Federated Query & Liaison Inbox
  queryFederated: (request: FederatedQueryRequest, userId = 'inspector1') =>
    apiRequest<FederatedQueryResponse>(
      '/federated/query',
      {
        method: 'POST',
        body: JSON.stringify(request),
      },
      userId
    ),
  getAgencyInbox: (agency: string, userId = 'liaison1') =>
    apiRequest<AgencyInboxItem[]>(`/agency/${encodeURIComponent(agency)}/inbox`, { method: 'GET' }, userId),

  // Nashik Kumbh Mela Surveillance Matrix & Operations Intelligence
  getKumbhZones: (userId = 'analyst1') =>
    apiRequest<KumbhZone[]>('/kumbh/zones', { method: 'GET' }, userId),
  getKumbhAlerts: (userId = 'analyst1') =>
    apiRequest<KumbhAlert[]>('/kumbh/alerts', { method: 'GET' }, userId),
  simulateNextKumbh: (userId = 'analyst1') =>
    apiRequest<KumbhSimulationResponse>('/kumbh/simulate/next', { method: 'POST' }, userId),
  confirmKumbhAlert: (alertId: string, action: 'CONFIRM' | 'DISMISS', notes?: string, userId = 'analyst1') =>
    apiRequest<{ alert_id: string; action: string; actor: string; ts: string; audit_seq: number }>(
      `/kumbh/alerts/${encodeURIComponent(alertId)}/confirm`,
      {
        method: 'POST',
        body: JSON.stringify({ action, reason: notes }),
      },
      userId
    ),
  getKumbhObservations: (
    params?: { limit?: number; offset?: number; zone?: string; event_type?: string },
    userId = 'analyst1'
  ) => {
    const q = new URLSearchParams();
    if (params?.limit !== undefined) q.set('limit', String(params.limit));
    if (params?.offset !== undefined) q.set('offset', String(params.offset));
    if (params?.zone) q.set('zone', params.zone);
    if (params?.event_type) q.set('event_type', params.event_type);
    const qs = q.toString() ? `?${q.toString()}` : '';
    return apiRequest<KumbhObservation[]>(`/kumbh/observations${qs}`, { method: 'GET' }, userId);
  },
  getKumbhSignals: (
    params?: { limit?: number; offset?: number; signal_type?: string; evidence_tier?: string },
    userId = 'analyst1'
  ) => {
    const q = new URLSearchParams();
    if (params?.limit !== undefined) q.set('limit', String(params.limit));
    if (params?.offset !== undefined) q.set('offset', String(params.offset));
    if (params?.signal_type) q.set('signal_type', params.signal_type);
    if (params?.evidence_tier) q.set('evidence_tier', params.evidence_tier);
    const qs = q.toString() ? `?${q.toString()}` : '';
    return apiRequest<KumbhSignal[]>(`/kumbh/signals${qs}`, { method: 'GET' }, userId);
  },
  getKumbhClusters: (
    params?: { limit?: number; offset?: number; cluster_type?: string },
    userId = 'analyst1'
  ) => {
    const q = new URLSearchParams();
    if (params?.limit !== undefined) q.set('limit', String(params.limit));
    if (params?.offset !== undefined) q.set('offset', String(params.offset));
    if (params?.cluster_type) q.set('cluster_type', params.cluster_type);
    const qs = q.toString() ? `?${q.toString()}` : '';
    return apiRequest<KumbhCluster[]>(`/kumbh/clusters${qs}`, { method: 'GET' }, userId);
  },
  getKumbhEventIntelligence: (eventId: string, userId = 'analyst1') =>
    apiRequest<KumbhEventIntelligence>(`/kumbh/events/${encodeURIComponent(eventId)}/intelligence`, { method: 'GET' }, userId),

  // Audit Ledger & Integrity Verification
  getAuditLog: (limit = 50, offset = 0, userId = 'auditor1') =>
    apiRequest<AuditEntry[]>(`/audit?limit=${limit}&offset=${offset}`, { method: 'GET' }, userId),
  verifyAudit: (userId = 'analyst1') =>
    apiRequest<AuditVerifyResult>('/audit/verify', { method: 'GET' }, userId),
  tamperAudit: (userId = 'analyst1') =>
    apiRequest<AuditTamperResponse>('/audit/dev/tamper', { method: 'POST' }, userId),
  repairAudit: (userId = 'analyst1') =>
    apiRequest<AuditRepairResponse>('/audit/dev/repair', { method: 'POST' }, userId),
};
