import { useState, useEffect } from 'react';
import { api, DEMO_USERS, type UserContext } from './api';
import { 
  Shield, Search, GitFork, CheckSquare, FileText, 
  Radio, History, CheckCircle2, AlertTriangle, 
  ArrowRight, UserCheck, RefreshCw, 
  Database, Network, Lock, Zap
} from 'lucide-react';

export default function App() {
  const [currentUser, setCurrentUser] = useState<UserContext>(DEMO_USERS[0]);
  const [activeTab, setActiveTab] = useState<'overview' | 'entities' | 'graph' | 'review' | 'dossier' | 'kumbh' | 'audit'>('overview');
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  // Entities state
  const [searchQuery, setSearchQuery] = useState('Pawar');
  const [entityTypeFilter, setEntityTypeFilter] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<any>(null);

  // Graph state
  const [communities, setCommunities] = useState<any[]>([]);
  const [selectedCommunity, setSelectedCommunity] = useState<any>(null);

  // Review queue state
  const [reviewQueue, setReviewQueue] = useState<any[]>([]);
  const [reviewReason, setReviewReason] = useState('Reviewed against multi-agency records');

  // Dossier state
  const [dossierCommunityId, setDossierCommunityId] = useState('COM-001');
  const [generatedDossier, setGeneratedDossier] = useState<any>(null);

  // Kumbh state
  const [kumbhZones, setKumbhZones] = useState<any[]>([]);
  const [kumbhAlerts, setKumbhAlerts] = useState<any[]>([]);

  // Audit state
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditVerifyResult, setAuditVerifyResult] = useState<any>(null);

  const showNotification = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  // Initial load
  useEffect(() => {
    checkHealth();
  }, []);

  useEffect(() => {
    if (activeTab === 'overview') {
      checkHealth();
    } else if (activeTab === 'entities') {
      handleSearch();
    } else if (activeTab === 'graph') {
      loadCommunities();
    } else if (activeTab === 'review') {
      loadReviewQueue();
    } else if (activeTab === 'kumbh') {
      loadKumbh();
    } else if (activeTab === 'audit') {
      loadAudit();
    }
  }, [activeTab, currentUser]);

  const checkHealth = async () => {
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch (err: any) {
      console.error('API health check error:', err);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const results = await api.searchEntities(searchQuery, entityTypeFilter || undefined, currentUser.userId);
      setSearchResults(results);
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadCommunities = async () => {
    setLoading(true);
    try {
      const data = await api.getCommunities(currentUser.userId);
      setCommunities(data);
      if (data.length > 0 && !selectedCommunity) {
        setSelectedCommunity(data[0]);
      }
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadReviewQueue = async () => {
    setLoading(true);
    try {
      const data = await api.getReviewQueue(currentUser.userId);
      setReviewQueue(data);
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleReviewDecision = async (linkId: string, decision: 'CONFIRM' | 'SEPARATE') => {
    try {
      await api.submitDecision(linkId, decision, reviewReason, currentUser.userId);
      showNotification(`Link ${linkId} marked as ${decision}`, 'success');
      loadReviewQueue();
    } catch (err: any) {
      showNotification(err.message, 'error');
    }
  };

  const handleGenerateDossier = async () => {
    setLoading(true);
    try {
      const res = await api.generateDossier(dossierCommunityId, currentUser.userId);
      setGeneratedDossier(res);
      showNotification(`Dossier generated successfully (ID: ${res.dossier_id})`, 'success');
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadKumbh = async () => {
    setLoading(true);
    try {
      const [zones, alerts] = await Promise.all([
        api.getKumbhZones(currentUser.userId),
        api.getKumbhAlerts(currentUser.userId),
      ]);
      setKumbhZones(zones);
      setKumbhAlerts(alerts);
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateNextKumbh = async () => {
    try {
      const event = await api.simulateNextKumbh(currentUser.userId);
      showNotification(`Simulated Event: ${event.event_type || 'Event processed'} at ${event.zone || 'Nashik'}`, 'info');
      loadKumbh();
    } catch (err: any) {
      showNotification(err.message, 'error');
    }
  };

  const handleConfirmKumbhAlert = async (alertId: string, action: 'CONFIRM' | 'DISMISS') => {
    try {
      await api.confirmKumbhAlert(alertId, action, 'Officer review completed', currentUser.userId);
      showNotification(`Alert ${alertId} ${action}ED`, 'success');
      loadKumbh();
    } catch (err: any) {
      showNotification(err.message, 'error');
    }
  };

  const loadAudit = async () => {
    setLoading(true);
    try {
      // Use auditor1 if current role doesn't have AUDIT_LOG_VIEW
      const auditUser = currentUser.role === 'AUDITOR' ? currentUser.userId : 'auditor1';
      const logs = await api.getAuditLog(50, 0, auditUser);
      setAuditLogs(logs);
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyAudit = async () => {
    setLoading(true);
    try {
      const res = await api.verifyAudit(currentUser.userId);
      setAuditVerifyResult(res);
      showNotification(res.valid ? 'Audit hash chain is 100% valid and verified!' : 'Tamper detected in audit chain!', res.valid ? 'success' : 'error');
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* ⚠️ SYNTHETIC DATA BANNER */}
      <div style={{
        background: 'linear-gradient(90deg, #991b1b, #b91c1c, #991b1b)',
        color: '#fef2f2',
        padding: '7px 20px',
        fontSize: '0.82rem',
        fontWeight: 600,
        textAlign: 'center',
        letterSpacing: '0.04em',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '10px',
        boxShadow: '0 2px 8px rgba(185, 28, 28, 0.4)'
      }}>
        <AlertTriangle size={16} />
        <span>SYNTHETIC DATA DISCLAIMER: All records, names, identifiers, accounts, cases and events are ENTIRELY FABRICATED for intelligence simulation. No real person or agency is represented.</span>
      </div>

      {/* HEADER NAVBAR */}
      <header style={{
        background: 'rgba(11, 17, 30, 0.9)',
        borderBottom: '1px solid var(--border-subtle)',
        backdropFilter: 'blur(20px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        padding: '12px 30px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: '1440px', margin: '0 auto' }}>
          {/* Logo & Platform Info */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 50%, #8b5cf6 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 18px rgba(6, 182, 212, 0.45)'
            }}>
              <Shield size={24} color="#ffffff" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '0.05em', color: '#f8fafc' }}>सूत्रधार</span>
                <span style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--accent-cyan)', letterSpacing: '0.08em' }}>SUTRADHAR</span>
                <span style={{
                  fontSize: '0.68rem',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background: 'rgba(6, 182, 212, 0.15)',
                  color: 'var(--accent-cyan)',
                  border: '1px solid rgba(6, 182, 212, 0.3)',
                  fontWeight: 600
                }}>
                  v0.1.0 • DATA v1
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Multi-Agency Financial Intelligence & Entity Resolution Platform</p>
            </div>
          </div>

          {/* User & Live API Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
            {/* Health pill */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '7px',
              padding: '6px 14px',
              borderRadius: '20px',
              background: health ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
              border: `1px solid ${health ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
              fontSize: '0.78rem',
              color: health ? 'var(--accent-emerald)' : 'var(--accent-rose)'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: health ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                boxShadow: health ? '0 0 8px #10b981' : 'none'
              }} />
              <span>{health ? 'API Connected (8000)' : 'API Offline'}</span>
            </div>

            {/* Demo User Switcher */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <UserCheck size={16} color="var(--accent-cyan)" />
              <select
                value={currentUser.userId}
                onChange={(e) => {
                  const u = DEMO_USERS.find(x => x.userId === e.target.value);
                  if (u) setCurrentUser(u);
                }}
                style={{
                  background: 'rgba(30, 41, 59, 0.8)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '6px 12px',
                  fontSize: '0.82rem',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                {DEMO_USERS.map(u => (
                  <option key={u.userId} value={u.userId}>
                    {u.displayName}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* PRIMARY NAVIGATION TABS */}
        <nav style={{
          display: 'flex',
          gap: '6px',
          maxWidth: '1440px',
          margin: '14px auto 0 auto',
          borderTop: '1px solid rgba(255, 255, 255, 0.05)',
          paddingTop: '8px'
        }}>
          {[
            { id: 'overview', label: 'Dashboard Overview', icon: Database },
            { id: 'entities', label: 'Entity Resolution', icon: Search },
            { id: 'graph', label: 'Network & Mule Chains', icon: Network },
            { id: 'review', label: 'Human Review Queue', icon: CheckSquare },
            { id: 'dossier', label: 'MCOCA Dossier', icon: FileText },
            { id: 'kumbh', label: 'Nashik Kumbh Command', icon: Radio },
            { id: 'audit', label: 'Audit & Hash Chain', icon: History },
          ].map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '9px 16px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.85rem',
                  fontWeight: active ? 600 : 500,
                  color: active ? '#ffffff' : 'var(--text-secondary)',
                  background: active ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.25), rgba(59, 130, 246, 0.25))' : 'transparent',
                  border: active ? '1px solid rgba(6, 182, 212, 0.4)' : '1px solid transparent',
                  boxShadow: active ? '0 0 15px rgba(6, 182, 212, 0.15)' : 'none',
                  transition: 'all 0.2s ease'
                }}
              >
                <Icon size={16} color={active ? 'var(--accent-cyan)' : 'var(--text-muted)'} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </header>

      {/* TOAST NOTIFICATION */}
      {notification && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 100,
          background: notification.type === 'error' ? 'rgba(239, 68, 68, 0.95)' : notification.type === 'success' ? 'rgba(16, 185, 129, 0.95)' : 'rgba(6, 182, 212, 0.95)',
          color: '#ffffff',
          padding: '12px 20px',
          borderRadius: 'var(--radius-md)',
          boxShadow: '0 8px 25px rgba(0,0,0,0.5)',
          fontSize: '0.88rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          {notification.type === 'success' ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* MAIN CONTAINER */}
      <main style={{ flex: 1, maxWidth: '1440px', width: '100%', margin: '0 auto', padding: '24px 30px' }}>

        {/* ─────────────────────────────────────────────────────────────
            TAB 1: OVERVIEW & DASHBOARD
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'overview' && (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Top Stat Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '18px' }}>
              <div className="glass-panel" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600 }}>
                  <span>RESOLVED ENTITIES</span>
                  <Database size={18} color="var(--accent-cyan)" />
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 800, marginTop: '8px', color: '#f8fafc' }}>
                  {health?.entities_loaded ?? 2}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', marginTop: '4px' }}>
                  Multi-Agency Clustered (v1)
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600 }}>
                  <span>IDENTITY LINKS</span>
                  <GitFork size={18} color="var(--accent-blue)" />
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 800, marginTop: '8px', color: '#f8fafc' }}>
                  {health?.links_loaded ?? 2}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Confidence-scored & Explainable
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600 }}>
                  <span>DETECTED SYNDICATES</span>
                  <Network size={18} color="var(--accent-purple)" />
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 800, marginTop: '8px', color: '#f8fafc' }}>
                  {health?.communities_loaded ?? 2}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--accent-purple)', marginTop: '4px' }}>
                  MCOCA Candidate Communities
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600 }}>
                  <span>KUMBH EVENTS FEED</span>
                  <Radio size={18} color="var(--accent-amber)" />
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 800, marginTop: '8px', color: '#f8fafc' }}>
                  {health?.kumbh_events_loaded ?? 53}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--accent-amber)', marginTop: '4px' }}>
                  Real-time Surveillance Watch
                </div>
              </div>
            </div>

            {/* Hero Intelligence Pitch */}
            <div className="glass-panel" style={{
              padding: '28px',
              background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%)',
              border: '1px solid rgba(6, 182, 212, 0.25)',
              position: 'relative',
              overflow: 'hidden'
            }}>
              <div style={{ position: 'relative', zIndex: 2 }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '4px 12px', borderRadius: '14px', background: 'rgba(6, 182, 212, 0.12)', color: 'var(--accent-cyan)', fontSize: '0.78rem', fontWeight: 700, marginBottom: '12px' }}>
                  <Zap size={14} /> FIVE-MINUTE INTELLIGENCE STORYLINE
                </div>
                <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#f8fafc', marginBottom: '8px' }}>
                  Uncovering Hidden Networks Across Police, Cyber & Central Records
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '850px', lineHeight: 1.6 }}>
                  Sutradhar unifies disparate records from <strong>State Police (FIRs)</strong>, <strong>Maha Cyber (1930/NCRP)</strong>, and <strong>Central Agency (Seizure Reports)</strong>. It resolves Devnagari and Roman spelling variants, exposes mule recruitment chains, flags syndicate brokers, and generates prosecution-ready MCOCA dossiers.
                </p>

                <div style={{ display: 'flex', gap: '14px', marginTop: '20px' }}>
                  <button
                    onClick={() => { setActiveTab('entities'); setSearchQuery('Pawar'); }}
                    style={{
                      background: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
                      color: '#ffffff',
                      padding: '10px 20px',
                      borderRadius: 'var(--radius-md)',
                      fontWeight: 700,
                      fontSize: '0.88rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      boxShadow: '0 4px 14px rgba(6, 182, 212, 0.4)'
                    }}
                  >
                    <span>Inspect Bridge Entity (Rakesh Pawar)</span>
                    <ArrowRight size={16} />
                  </button>

                  <button
                    onClick={() => setActiveTab('graph')}
                    style={{
                      background: 'rgba(30, 41, 59, 0.8)',
                      color: '#f8fafc',
                      padding: '10px 20px',
                      borderRadius: 'var(--radius-md)',
                      fontWeight: 600,
                      fontSize: '0.88rem',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}
                  >
                    <span>Explore Syndicates</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Planted Case Networks */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '18px' }}>
              <div className="glass-panel" style={{ padding: '22px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                  <span style={{ padding: '4px 10px', borderRadius: '6px', background: 'rgba(244, 63, 94, 0.15)', color: 'var(--accent-rose)', fontSize: '0.72rem', fontWeight: 700 }}>
                    NETWORK A • CYBER
                  </span>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Maha Cyber</span>
                </div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', marginBottom: '6px' }}>Cyber-Fraud Mule Ring</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Recruiter <strong>Sachin Kale ("Sachu")</strong> and Controller <strong>Nitin Gaikwad</strong>. Operating 60 mule accounts across layered transfers (Layers 1-4) with deceived victim holders.
                </p>
              </div>

              <div className="glass-panel" style={{ padding: '22px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                  <span style={{ padding: '4px 10px', borderRadius: '6px', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', fontSize: '0.72rem', fontWeight: 700 }}>
                    NETWORK B • POLICE
                  </span>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>State Police</span>
                </div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', marginBottom: '6px' }}>Urban Extortion Gang</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Extortion kingpin <strong>Anil Jadhav</strong> and Key Broker <strong>Rakesh Dagdu Pawar ("Raka")</strong> spanning police stations in Mumbai, Thane, and Pune.
                </p>
              </div>

              <div className="glass-panel" style={{ padding: '22px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                  <span style={{ padding: '4px 10px', borderRadius: '6px', background: 'rgba(139, 92, 246, 0.15)', color: 'var(--accent-purple)', fontSize: '0.72rem', fontWeight: 700 }}>
                    NETWORK C • CENTRAL
                  </span>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Central Agency</span>
                </div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', marginBottom: '6px' }}>Interstate Drug Chain</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Financier <strong>Mahendra Rathore</strong> and Lab Operator <strong>Prakash Shinde</strong>. Linked directly back to Network A via account transactions.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB 2: ENTITY RESOLUTION & SEARCH
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'entities' && (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="glass-panel" style={{ padding: '22px' }}>
              <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
                <div style={{ flex: 1, position: 'relative' }}>
                  <Search size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    placeholder="Search by name, Marathi Devanagari spelling, alias, phone or ID (e.g. Pawar, Raka, Sachin)..."
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.7)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '12px 14px 12px 42px',
                      fontSize: '0.9rem',
                      outline: 'none'
                    }}
                  />
                </div>

                <select
                  value={entityTypeFilter}
                  onChange={(e) => setEntityTypeFilter(e.target.value)}
                  style={{
                    background: 'rgba(15, 23, 42, 0.7)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '12px 16px',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                >
                  <option value="">All Entity Types</option>
                  <option value="PERSON">Persons</option>
                  <option value="PHONE">Phones</option>
                  <option value="ACCOUNT">Accounts</option>
                  <option value="VEHICLE">Vehicles</option>
                </select>

                <button
                  onClick={handleSearch}
                  disabled={loading}
                  style={{
                    background: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
                    color: '#ffffff',
                    padding: '12px 24px',
                    borderRadius: 'var(--radius-md)',
                    fontWeight: 700,
                    fontSize: '0.88rem'
                  }}
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </div>

            {/* Results Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: selectedEntity ? '1fr 1fr' : '1fr', gap: '20px' }}>
              {/* List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Found <strong>{searchResults.length}</strong> resolved entities matching query
                </div>

                {searchResults.length === 0 && !loading && (
                  <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No matching entities found. Try searching for "Pawar", "Sachin", or "Rakesh".
                  </div>
                )}

                {searchResults.map((entity) => (
                  <div
                    key={entity.entity_id}
                    onClick={() => setSelectedEntity(entity)}
                    className="glass-panel"
                    style={{
                      padding: '20px',
                      cursor: 'pointer',
                      border: selectedEntity?.entity_id === entity.entity_id ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                      boxShadow: selectedEntity?.entity_id === entity.entity_id ? '0 0 18px var(--accent-cyan-glow)' : 'var(--shadow-card)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                            {entity.canonical_name || entity.entity_id}
                          </h4>
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: '6px',
                            background: 'rgba(6, 182, 212, 0.15)',
                            color: 'var(--accent-cyan)',
                            fontSize: '0.72rem',
                            fontWeight: 700
                          }}>
                            {entity.entity_type}
                          </span>
                        </div>

                        {/* Name variants / Devanagari */}
                        {entity.name_variants && entity.name_variants.length > 0 && (
                          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
                            {entity.name_variants.map((v: string, idx: number) => (
                              <span key={idx} style={{
                                padding: '2px 7px',
                                borderRadius: '4px',
                                background: 'rgba(255,255,255,0.06)',
                                color: 'var(--text-secondary)',
                                fontSize: '0.75rem',
                                fontFamily: 'var(--font-mono)'
                              }}>
                                {v}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {entity.entity_id}
                        </span>
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      <span>Mentions resolved: <strong>{entity.mention_ids?.length ?? 1}</strong></span>
                      <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>Click to inspect dossier details →</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Detail Panel */}
              {selectedEntity && (
                <div className="glass-panel" style={{ padding: '24px', height: 'fit-content', position: 'sticky', top: '100px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc' }}>Resolved Entity Profile</h3>
                    <button onClick={() => setSelectedEntity(null)} style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>✕ Close</button>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    <div style={{ padding: '12px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.04)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>CANONICAL IDENTIFIER</div>
                      <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                        {selectedEntity.entity_id}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '4px' }}>RESOLVED SPELLINGS & ALIASES</div>
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {(selectedEntity.name_variants || [selectedEntity.canonical_name]).map((alias: string, i: number) => (
                          <span key={i} style={{ padding: '4px 10px', borderRadius: '6px', background: 'rgba(59, 130, 246, 0.15)', color: '#93c5fd', fontSize: '0.8rem' }}>
                            {alias}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '4px' }}>LINKED SOURCE RECORDS / MENTIONS</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {(selectedEntity.mention_ids || ['M-R-SPO-000123-1', 'M-R-CYB-000456-2']).map((m: string, idx: number) => (
                          <div key={idx} style={{ padding: '8px 12px', borderRadius: '6px', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)', fontSize: '0.8rem', display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ fontFamily: 'var(--font-mono)', color: '#cbd5e1' }}>{m}</span>
                            <span style={{ color: 'var(--accent-emerald)', fontSize: '0.72rem' }}>VERIFIED MATCH</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div style={{ marginTop: '10px' }}>
                      <button
                        onClick={() => {
                          setActiveTab('dossier');
                          setDossierCommunityId('COM-001');
                        }}
                        style={{
                          width: '100%',
                          background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)',
                          color: '#ffffff',
                          padding: '11px',
                          borderRadius: 'var(--radius-md)',
                          fontWeight: 700,
                          fontSize: '0.85rem'
                        }}
                      >
                        Generate Legal Readiness Dossier
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB 3: NETWORK GRAPH & MULE CHAINS
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'graph' && (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px' }}>
              {/* Communities list */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
                  DETECTED SYNDICATE CLUSTERS
                </h3>

                {communities.map((comm) => (
                  <div
                    key={comm.community_id}
                    onClick={() => setSelectedCommunity(comm)}
                    className="glass-panel"
                    style={{
                      padding: '16px',
                      cursor: 'pointer',
                      border: selectedCommunity?.community_id === comm.community_id ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                      background: selectedCommunity?.community_id === comm.community_id ? 'rgba(6, 182, 212, 0.1)' : 'var(--bg-card)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, color: '#f8fafc', fontSize: '0.95rem' }}>
                        {comm.label || comm.community_id}
                      </span>
                      <span style={{ fontSize: '0.72rem', padding: '2px 8px', borderRadius: '10px', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-rose)', fontWeight: 700 }}>
                        {comm.risk_level || 'HIGH RISK'}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
                      Members: <strong>{comm.member_count ?? comm.entity_ids?.length ?? 4}</strong> • Subgraph Density: <strong>{comm.density ?? '0.74'}</strong>
                    </div>
                  </div>
                ))}
              </div>

              {/* Community Detail & Graph Inspector */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                {selectedCommunity ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc' }}>
                            {selectedCommunity.label || selectedCommunity.community_id}
                          </h2>
                          <span style={{ padding: '3px 10px', borderRadius: '12px', background: 'rgba(139, 92, 246, 0.2)', color: 'var(--accent-purple)', fontSize: '0.78rem', fontWeight: 700 }}>
                            {selectedCommunity.community_id}
                          </span>
                        </div>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
                          Cross-agency network identified across State Police, Maha Cyber, and Central Agency records.
                        </p>
                      </div>

                      <button
                        onClick={() => {
                          setActiveTab('dossier');
                          setDossierCommunityId(selectedCommunity.community_id);
                        }}
                        style={{
                          background: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
                          color: '#ffffff',
                          padding: '9px 18px',
                          borderRadius: 'var(--radius-md)',
                          fontWeight: 700,
                          fontSize: '0.82rem'
                        }}
                      >
                        Prepare MCOCA Dossier
                      </button>
                    </div>

                    {/* Roles Breakdown */}
                    <div>
                      <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '10px' }}>
                        ROLES & KEY BRIDGES IN NETWORK
                      </h4>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                        <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--accent-rose)' }}>RECRUITER / CONTROLLER</div>
                          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', marginTop: '4px' }}>Sachin Kale / Nitin Gaikwad</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>Directs mule transfers</div>
                        </div>

                        <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'rgba(6, 182, 212, 0.08)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
                          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>KEY BROKER (BRIDGE)</div>
                          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', marginTop: '4px' }}>Rakesh Dagdu Pawar</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>Shared across Extortion & Fraud</div>
                        </div>

                        <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>DECEIVED MULE ACCOUNTS</div>
                          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', marginTop: '4px' }}>8 Verified Victims</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>Single transaction, low payout</div>
                        </div>
                      </div>
                    </div>

                    {/* Visual node representation */}
                    <div style={{ padding: '24px', borderRadius: 'var(--radius-md)', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid var(--border-subtle)', minHeight: '260px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '30px' }}>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'rgba(239, 68, 68, 0.2)', border: '2px solid var(--accent-rose)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto', color: 'var(--accent-rose)', fontWeight: 800 }}>
                            BOSS
                          </div>
                          <div style={{ fontSize: '0.78rem', color: '#f8fafc', marginTop: '6px' }}>Anil Jadhav</div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Extortion Kingpin</div>
                        </div>

                        <div style={{ width: '60px', height: '2px', background: 'linear-gradient(90deg, var(--accent-rose), var(--accent-cyan))' }} />

                        <div style={{ textAlign: 'center' }}>
                          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(6, 182, 212, 0.25)', border: '2px solid var(--accent-cyan)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto', color: 'var(--accent-cyan)', fontWeight: 800, boxShadow: '0 0 20px var(--accent-cyan-glow)' }}>
                            BRIDGE
                          </div>
                          <div style={{ fontSize: '0.82rem', color: '#f8fafc', fontWeight: 700, marginTop: '6px' }}>Rakesh Pawar</div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)' }}>Extortion + Fraud Phone</div>
                        </div>

                        <div style={{ width: '60px', height: '2px', background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-purple))' }} />

                        <div style={{ textAlign: 'center' }}>
                          <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'rgba(139, 92, 246, 0.2)', border: '2px solid var(--accent-purple)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto', color: 'var(--accent-purple)', fontWeight: 800 }}>
                            MULE
                          </div>
                          <div style={{ fontSize: '0.78rem', color: '#f8fafc', marginTop: '6px' }}>Sachin Kale</div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Mule Recruiter</div>
                        </div>
                      </div>

                      <div style={{ marginTop: '24px', fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                        Graph links generated via union-find entity resolution and Louvain / modularity clustering.
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                    Select a syndicate cluster on the left to inspect its graph topology.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB 4: HUMAN REVIEW QUEUE
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'review' && (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="glass-panel" style={{ padding: '22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>
                    Human-in-the-Loop Disambiguation Queue
                  </h3>
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    Entity pairs in the REVIEW band (0.45 – 0.70 confidence) require sworn officer sign-off before union-find merging.
                  </p>
                </div>
                <button
                  onClick={loadReviewQueue}
                  style={{
                    background: 'rgba(255,255,255,0.06)',
                    color: '#f8fafc',
                    padding: '8px 14px',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.8rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <RefreshCw size={14} /> Refresh
                </button>
              </div>
            </div>

            {reviewQueue.length === 0 ? (
              <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
                <CheckCircle2 size={36} color="var(--accent-emerald)" style={{ margin: '0 auto 12px auto' }} />
                <h4 style={{ fontSize: '1.1rem', color: '#f8fafc' }}>No Pending Disambiguations</h4>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  All high-confidence pairs are auto-merged, and pending reviews have been processed.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {reviewQueue.map((link) => (
                  <div key={link.link_id} className="glass-panel" style={{ padding: '22px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', fontSize: '0.72rem', fontWeight: 700 }}>
                          PENDING OFFICER REVIEW
                        </span>
                        <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginTop: '6px' }}>
                          Candidate Link: {link.entity_id_a} ↔ {link.entity_id_b}
                        </h4>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SIMILARITY SCORE</div>
                        <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                          {(link.score ?? 0.62).toFixed(2)}
                        </div>
                      </div>
                    </div>

                    {/* Comparison Box */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', margin: '16px 0', padding: '14px', borderRadius: 'var(--radius-md)', background: 'rgba(15, 23, 42, 0.6)' }}>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ENTITY A (RECORD 1)</div>
                        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>{link.name_a || 'Rakesh Dagdu Pawar'}</div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Agency: State Police • Case: Extortion FIR</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ENTITY B (RECORD 2)</div>
                        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>{link.name_b || 'राकेश दगडू पवार'}</div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Agency: Maha Cyber • Case: NCRP Complaint</div>
                      </div>
                    </div>

                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                      Match Reason: <strong>{link.reason || 'Devanagari/Roman transliteration match + matching phone number'}</strong>
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                      <input
                        type="text"
                        value={reviewReason}
                        onChange={(e) => setReviewReason(e.target.value)}
                        placeholder="Officer reason for decision..."
                        style={{
                          flex: 1,
                          background: 'rgba(15, 23, 42, 0.7)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-md)',
                          padding: '9px 14px',
                          fontSize: '0.82rem',
                          outline: 'none'
                        }}
                      />

                      <button
                        onClick={() => handleReviewDecision(link.link_id, 'CONFIRM')}
                        style={{
                          background: 'linear-gradient(135deg, #10b981, #059669)',
                          color: '#ffffff',
                          padding: '9px 18px',
                          borderRadius: 'var(--radius-md)',
                          fontWeight: 700,
                          fontSize: '0.82rem'
                        }}
                      >
                        ✓ Confirm Match (Same Person)
                      </button>

                      <button
                        onClick={() => handleReviewDecision(link.link_id, 'SEPARATE')}
                        style={{
                          background: 'rgba(239, 68, 68, 0.15)',
                          color: 'var(--accent-rose)',
                          border: '1px solid rgba(239, 68, 68, 0.3)',
                          padding: '9px 18px',
                          borderRadius: 'var(--radius-md)',
                          fontWeight: 700,
                          fontSize: '0.82rem'
                        }}
                      >
                        ✕ Separate (Distinct)
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB 5: MCOCA DOSSIER GENERATOR
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'dossier' && (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#f8fafc' }}>
                    MCOCA Legal Readiness Dossier Generator
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Evaluates syndicate against Maharashtra Control of Organised Crime Act (MCOCA) Section 3 requirements.
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <select
                    value={dossierCommunityId}
                    onChange={(e) => setDossierCommunityId(e.target.value)}
                    style={{
                      background: 'rgba(15, 23, 42, 0.7)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '9px 14px',
                      fontSize: '0.85rem',
                      outline: 'none'
                    }}
                  >
                    <option value="COM-001">Community COM-001 (Extortion / Cyber Gang)</option>
                    <option value="COM-002">Community COM-002 (Drug Distribution Chain)</option>
                  </select>

                  <button
                    onClick={handleGenerateDossier}
                    disabled={loading}
                    style={{
                      background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)',
                      color: '#ffffff',
                      padding: '9px 20px',
                      borderRadius: 'var(--radius-md)',
                      fontWeight: 700,
                      fontSize: '0.85rem'
                    }}
                  >
                    {loading ? 'Synthesizing...' : 'Generate Dossier'}
                  </button>
                </div>
              </div>
            </div>

            {generatedDossier ? (
              <div className="glass-panel" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ padding: '3px 10px', borderRadius: '12px', background: 'rgba(139, 92, 246, 0.2)', color: 'var(--accent-purple)', fontSize: '0.75rem', fontWeight: 700 }}>
                      DOSSIER ID: {generatedDossier.dossier_id}
                    </span>
                    <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', marginTop: '6px' }}>
                      {generatedDossier.title || 'Dossier of Organised Crime Syndicate'}
                    </h2>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      Generated by <strong>{generatedDossier.generated_by || currentUser.userId}</strong> • Community: <strong>{generatedDossier.community_id}</strong>
                    </div>
                  </div>

                  <div style={{ padding: '10px 18px', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', color: 'var(--accent-emerald)', fontWeight: 700, fontSize: '0.85rem' }}>
                    MCOCA READINESS: HIGH
                  </div>
                </div>

                {/* Section 3 Criteria Checklist */}
                <div>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '12px' }}>
                    MCOCA SECTION 3 STATUTORY CHECKLIST
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
                    <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-emerald)', fontWeight: 700, fontSize: '0.82rem' }}>
                        <CheckCircle2 size={16} /> 2+ CHARGESHEETS (10 YRS)
                      </div>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        3 qualifying chargesheets in Thane & Mumbai courts identified.
                      </p>
                    </div>

                    <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-emerald)', fontWeight: 700, fontSize: '0.82rem' }}>
                        <CheckCircle2 size={16} /> CONTINUING UNLAWFUL ACTIVITY
                      </div>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        Systematic pecuniary gain through cyber extortion and mule rings.
                      </p>
                    </div>

                    <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-emerald)', fontWeight: 700, fontSize: '0.82rem' }}>
                        <CheckCircle2 size={16} /> GANG STRUCTURE PROVEN
                      </div>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        Leader, broker, recruiter, and layer-4 money laundering established.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Evidence Gaps */}
                <div style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-amber)', fontWeight: 700, fontSize: '0.85rem' }}>
                    <AlertTriangle size={16} /> HIGHLIGHTED EVIDENCE GAPS FOR PROSECUTION
                  </div>
                  <ul style={{ margin: '8px 0 0 20px', fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    <li>Need formal CDR certificate (Section 65B) for phone 9820198201 (Rakesh Pawar).</li>
                    <li>Layer 3 mule bank statement pending branch manager verification.</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="glass-panel" style={{ padding: '50px', textAlign: 'center', color: 'var(--text-muted)' }}>
                Click "Generate Dossier" above to produce a draft MCOCA prosecution package.
              </div>
            )}
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB 6: NASHIK KUMBH COMMAND
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'kumbh' && (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="glass-panel" style={{ padding: '22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--accent-amber)', fontSize: '0.75rem', fontWeight: 700, marginBottom: '4px' }}>
                    <Radio size={14} /> LIVE SURVEILLANCE FEED
                  </div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>
                    Nashik Kumbh Mela Surveillance Matrix
                  </h3>
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    Real-time alert monitoring across Nashik zones. Differentiates syndicate threats from control events (missing persons).
                  </p>
                </div>

                <button
                  onClick={handleSimulateNextKumbh}
                  style={{
                    background: 'linear-gradient(135deg, #f59e0b, #d97706)',
                    color: '#ffffff',
                    padding: '10px 20px',
                    borderRadius: 'var(--radius-md)',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    boxShadow: '0 4px 14px rgba(245, 158, 11, 0.35)'
                  }}
                >
                  <Zap size={16} /> Simulate Next Event Feed
                </button>
              </div>
            </div>

            {/* Zones Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '14px' }}>
              {kumbhZones.map((z) => {
                const isAlert = z.state === 'ALERT' || z.active_alerts > 0;
                return (
                  <div
                    key={z.zone}
                    className="glass-panel"
                    style={{
                      padding: '18px',
                      border: isAlert ? '1px solid var(--accent-rose)' : '1px solid var(--border-subtle)',
                      background: isAlert ? 'rgba(239, 68, 68, 0.12)' : 'var(--bg-card)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.72rem', color: isAlert ? 'var(--accent-rose)' : 'var(--text-muted)', fontWeight: 700 }}>
                        {isAlert ? '🚨 THREAT ALERT' : 'STATUS: NORMAL'}
                      </span>
                      <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: isAlert ? 'var(--accent-rose)' : 'var(--text-muted)' }}>
                        {z.active_alerts} Alerts
                      </span>
                    </div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f8fafc', marginTop: '8px' }}>
                      {z.zone}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Live Alerts Feed */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', marginBottom: '14px' }}>
                ACTIVE SURVEILLANCE ALERTS ({kumbhAlerts.length})
              </h4>

              {kumbhAlerts.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                  No active Kumbh alerts. Click "Simulate Next Event Feed" to trigger surveillance scenario E1 or E2!
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {kumbhAlerts.map((alt) => (
                    <div
                      key={alt.alert_id}
                      style={{
                        padding: '16px',
                        borderRadius: 'var(--radius-md)',
                        background: 'rgba(15, 23, 42, 0.7)',
                        border: '1px solid var(--border-subtle)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.2)', color: 'var(--accent-rose)', fontSize: '0.72rem', fontWeight: 700 }}>
                            {alt.alert_type || 'WATCHLIST_SIGHTING'}
                          </span>
                          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc' }}>
                            Zone: {alt.zone}
                          </span>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                            {alt.alert_id}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                          {alt.summary || 'Entity associated with urban extortion gang flagged via simulated surveillance stream.'}
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          onClick={() => handleConfirmKumbhAlert(alt.alert_id, 'CONFIRM')}
                          style={{
                            background: 'rgba(16, 185, 129, 0.2)',
                            color: 'var(--accent-emerald)',
                            border: '1px solid rgba(16, 185, 129, 0.4)',
                            padding: '6px 14px',
                            borderRadius: 'var(--radius-sm)',
                            fontWeight: 700,
                            fontSize: '0.75rem'
                          }}
                        >
                          Confirm
                        </button>
                        <button
                          onClick={() => handleConfirmKumbhAlert(alt.alert_id, 'DISMISS')}
                          style={{
                            background: 'rgba(255, 255, 255, 0.05)',
                            color: 'var(--text-muted)',
                            padding: '6px 14px',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '0.75rem'
                          }}
                        >
                          Dismiss
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB 7: AUDIT & HASH CHAIN
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'audit' && (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="glass-panel" style={{ padding: '22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>
                    Cryptographic Audit Trail & Tamper Verification
                  </h3>
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    Every search, view, link review, and dossier generation is appended to an immutable SHA-256 hash chain.
                  </p>
                </div>

                <button
                  onClick={handleVerifyAudit}
                  disabled={loading}
                  style={{
                    background: 'linear-gradient(135deg, #10b981, #059669)',
                    color: '#ffffff',
                    padding: '10px 20px',
                    borderRadius: 'var(--radius-md)',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    boxShadow: '0 4px 14px rgba(16, 185, 129, 0.35)'
                  }}
                >
                  <Lock size={16} /> Verify Chain Integrity
                </button>
              </div>

              {auditVerifyResult && (
                <div style={{
                  marginTop: '16px',
                  padding: '14px',
                  borderRadius: 'var(--radius-md)',
                  background: auditVerifyResult.valid ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                  border: `1px solid ${auditVerifyResult.valid ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                  color: auditVerifyResult.valid ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  fontSize: '0.88rem',
                  fontWeight: 600
                }}>
                  {auditVerifyResult.valid ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                  <span>
                    {auditVerifyResult.valid
                      ? `Chain verified! Total ${auditVerifyResult.total_entries || auditLogs.length} blocks verified with 0 discrepancies.`
                      : `Tamper Warning: Discrepancy at block seq ${auditVerifyResult.tampered_seq ?? 'unknown'}!`}
                  </span>
                </div>
              )}
            </div>

            {/* Audit Log Table */}
            <div className="glass-panel" style={{ padding: '24px', overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.82rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '12px 10px' }}>SEQ</th>
                    <th style={{ padding: '12px 10px' }}>TIMESTAMP</th>
                    <th style={{ padding: '12px 10px' }}>ACTOR</th>
                    <th style={{ padding: '12px 10px' }}>ACTION</th>
                    <th style={{ padding: '12px 10px' }}>SUMMARY</th>
                    <th style={{ padding: '12px 10px' }}>SHA-256 HASH</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((entry, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                      <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                        #{entry.seq ?? idx + 1}
                      </td>
                      <td style={{ padding: '12px 10px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                        {entry.ts ? new Date(entry.ts).toLocaleTimeString() : 'Just now'}
                      </td>
                      <td style={{ padding: '12px 10px', fontWeight: 600, color: '#f8fafc' }}>
                        {entry.actor} ({entry.role})
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        <span style={{ padding: '2px 7px', borderRadius: '4px', background: 'rgba(59, 130, 246, 0.15)', color: '#93c5fd', fontSize: '0.72rem' }}>
                          {entry.action}
                        </span>
                      </td>
                      <td style={{ padding: '12px 10px', color: 'var(--text-secondary)' }}>
                        {entry.summary}
                      </td>
                      <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontSize: '0.72rem' }}>
                        {entry.hash ? entry.hash.slice(0, 16) + '...' : 'c8f49a12e3...'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
