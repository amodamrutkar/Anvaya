// API Client for Sutradhar Backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
  { userId: 'auditor1', role: 'AUDITOR', agency: 'CENTRAL_AGENCY', displayName: 'Auditor (Audit Logs)' },
];

async function apiRequest<T>(endpoint: string, options: RequestInit = {}, userId = 'analyst1'): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
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

export const api = {
  getHealth: () => apiRequest<any>('/health', { method: 'GET' }),
  getMe: (userId: string) => apiRequest<any>('/me', { method: 'GET' }, userId),

  // Entities
  searchEntities: (q: string, type?: string, userId = 'analyst1') => {
    const params = new URLSearchParams({ q });
    if (type) params.set('type', type);
    return apiRequest<any[]>(`/entities/search?${params.toString()}`, { method: 'GET' }, userId);
  },
  getEntity: (id: string, userId = 'analyst1') =>
    apiRequest<any>(`/entities/${encodeURIComponent(id)}`, { method: 'GET' }, userId),
  getEntityLinks: (id: string, userId = 'analyst1') =>
    apiRequest<any[]>(`/entities/${encodeURIComponent(id)}/links`, { method: 'GET' }, userId),

  // Graph
  getCommunities: (userId = 'analyst1') =>
    apiRequest<any[]>('/graph/communities', { method: 'GET' }, userId),
  getCommunity: (id: string, userId = 'analyst1') =>
    apiRequest<any>(`/graph/communities/${encodeURIComponent(id)}`, { method: 'GET' }, userId),
  getNeighborhood: (entityId: string, hops = 2, userId = 'analyst1') =>
    apiRequest<any>(`/graph/entity/${encodeURIComponent(entityId)}/neighborhood?hops=${hops}`, { method: 'GET' }, userId),

  // Review Queue
  getReviewQueue: (userId = 'analyst1') =>
    apiRequest<any[]>('/review-queue', { method: 'GET' }, userId),
  submitDecision: (linkId: string, decision: 'CONFIRM' | 'SEPARATE', reason: string, userId = 'analyst1') =>
    apiRequest<any>(
      `/review-queue/${encodeURIComponent(linkId)}/decision`,
      {
        method: 'POST',
        body: JSON.stringify({ decision, reason }),
      },
      userId
    ),

  // Dossier
  generateDossier: (communityId: string, userId = 'analyst1') =>
    apiRequest<any>(
      '/dossier/generate',
      {
        method: 'POST',
        body: JSON.stringify({ community_id: communityId, purpose: 'INVESTIGATION' }),
      },
      userId
    ),
  getDossier: (dossierId: string, userId = 'analyst1') =>
    apiRequest<any>(`/dossier/${encodeURIComponent(dossierId)}`, { method: 'GET' }, userId),

  // Kumbh
  getKumbhZones: (userId = 'analyst1') =>
    apiRequest<any[]>('/kumbh/zones', { method: 'GET' }, userId),
  getKumbhAlerts: (userId = 'analyst1') =>
    apiRequest<any[]>('/kumbh/alerts', { method: 'GET' }, userId),
  simulateNextKumbh: (userId = 'analyst1') =>
    apiRequest<any>('/kumbh/simulate/next', { method: 'POST' }, userId),
  confirmKumbhAlert: (alertId: string, action: 'CONFIRM' | 'DISMISS', notes?: string, userId = 'analyst1') =>
    apiRequest<any>(
      `/kumbh/alerts/${encodeURIComponent(alertId)}/confirm`,
      {
        method: 'POST',
        body: JSON.stringify({ action, notes }),
      },
      userId
    ),

  // Audit
  getAuditLog: (limit = 50, offset = 0, userId = 'auditor1') =>
    apiRequest<any[]>(`/audit?limit=${limit}&offset=${offset}`, { method: 'GET' }, userId),
  verifyAudit: (userId = 'analyst1') =>
    apiRequest<any>('/audit/verify', { method: 'GET' }, userId),
};
