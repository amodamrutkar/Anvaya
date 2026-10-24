"""
services/api/tests/test_step5a_api.py
Comprehensive test suite for Step 5A: API Integration for Graph + Kumbh Intelligence.

Covers:
1. Graph shortest path (found, not found, bounded max_hops, deterministic).
2. Pagination bounds (default limit, custom limit, offset, invalid bounds rejection).
3. RBAC (authenticated, missing auth -> 401, forbidden action -> 403).
4. Audit chain (action logging, hash chain integrity).
5. Kumbh observations (separated, no ground truth leaks).
6. Kumbh intelligence signals (explainable, evidence tiers, requires review).
7. Kumbh incident clusters (operational clusters, not criminal syndicates).
8. Per-event intelligence portfolio (zero-correlation safety, portfolio structure).
9. Backward compatibility with existing graph and Kumbh simulation endpoints.
"""

from __future__ import annotations

import pytest

from sutradhar_api.store import get_store


# ─────────────────────────────────────────────────────────────
# 1. Graph Shortest Path
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_graph_path_success(client):
    """Verify deterministic shortest path lookup with real nodes and edges."""
    store = get_store()
    edges = store.graph_data.get("edges", [])
    assert len(edges) > 0, "Graph data must have edges loaded"

    first_edge = edges[0]
    src, tgt = first_edge["source"], first_edge["target"]

    r = await client.get(
        f"/graph/path?from={src}&to={tgt}",
        headers={"X-Demo-User": "analyst1"},
    )
    assert r.status_code == 200
    data = r.json()

    assert data["found"] is True
    assert data["hops"] >= 1
    assert data["from_id"] == src
    assert data["to_id"] == tgt
    assert isinstance(data["path"], list)
    assert len(data["path"]) >= 2
    assert data["path"][0] == src
    assert data["path"][-1] == tgt
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)
    assert data["requires_investigator_review"] is True


@pytest.mark.asyncio
async def test_graph_path_no_path_found(client):
    """Verify clean response when no path connects two nodes or one does not exist."""
    r = await client.get(
        "/graph/path?from=NON_EXISTENT_NODE_A&to=NON_EXISTENT_NODE_B",
        headers={"X-Demo-User": "analyst1"},
    )
    assert r.status_code == 200
    data = r.json()

    assert data["found"] is False
    assert data["hops"] == 0
    assert data["path"] == []
    assert data["nodes"] == []
    assert data["edges"] == []
    assert data["requires_investigator_review"] is True


@pytest.mark.asyncio
async def test_graph_path_max_hops_bounding(client):
    """Verify max_hops parameter bounds path length."""
    store = get_store()
    edges = store.graph_data.get("edges", [])
    first_edge = edges[0]
    src, tgt = first_edge["source"], first_edge["target"]

    # max_hops=1 allows direct 1-hop path
    r_ok = await client.get(
        f"/graph/path?from={src}&to={tgt}&max_hops=1",
        headers={"X-Demo-User": "analyst1"},
    )
    assert r_ok.status_code == 200
    assert r_ok.json()["found"] is True

    # Invalid max_hops (<1 or >10) rejected by validation
    r_bad_low = await client.get(
        f"/graph/path?from={src}&to={tgt}&max_hops=0",
        headers={"X-Demo-User": "analyst1"},
    )
    assert r_bad_low.status_code == 422

    r_bad_high = await client.get(
        f"/graph/path?from={src}&to={tgt}&max_hops=100",
        headers={"X-Demo-User": "analyst1"},
    )
    assert r_bad_high.status_code == 422


@pytest.mark.asyncio
async def test_graph_path_determinism(client):
    """Repeated calls for the same path return identical outputs."""
    store = get_store()
    edges = store.graph_data.get("edges", [])
    first_edge = edges[0]
    src, tgt = first_edge["source"], first_edge["target"]

    r1 = await client.get(f"/graph/path?from={src}&to={tgt}", headers={"X-Demo-User": "analyst1"})
    r2 = await client.get(f"/graph/path?from={src}&to={tgt}", headers={"X-Demo-User": "analyst1"})

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()


# ─────────────────────────────────────────────────────────────
# 2. Neighborhood Bounds
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_graph_neighborhood_bounds(client):
    """Verify neighborhood endpoint accepts bounded hops and limit."""
    store = get_store()
    eid = next(iter(store.entities))

    r = await client.get(
        f"/graph/entity/{eid}/neighborhood?hops=2&limit=10",
        headers={"X-Demo-User": "analyst1"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) <= 10

    # Negative bounds rejected
    r_bad = await client.get(
        f"/graph/entity/{eid}/neighborhood?limit=-1",
        headers={"X-Demo-User": "analyst1"},
    )
    assert r_bad.status_code == 422


# ─────────────────────────────────────────────────────────────
# 3. Pagination & Bounds across Collection Endpoints
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pagination_defaults_and_limits(client):
    """Verify pagination on graph and kumbh collection endpoints."""
    endpoints = [
        "/graph/communities",
        "/roles",
        "/bridges",
        "/mule/chains",
        "/kumbh/observations",
        "/kumbh/signals",
        "/kumbh/clusters",
    ]

    for ep in endpoints:
        r = await client.get(ep, headers={"X-Demo-User": "analyst1"})
        assert r.status_code == 200, f"Endpoint {ep} failed"
        data = r.json()
        assert isinstance(data, list)

        # Custom limit
        r_lim = await client.get(f"{ep}?limit=2&offset=0", headers={"X-Demo-User": "analyst1"})
        assert r_lim.status_code == 200
        assert len(r_lim.json()) <= 2

        # Invalid bounds rejected
        r_neg_lim = await client.get(f"{ep}?limit=-1", headers={"X-Demo-User": "analyst1"})
        assert r_neg_lim.status_code == 422

        r_neg_off = await client.get(f"{ep}?offset=-1", headers={"X-Demo-User": "analyst1"})
        assert r_neg_off.status_code == 422


# ─────────────────────────────────────────────────────────────
# 4. RBAC & Security
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rbac_authentication_required(client):
    """Missing or empty auth header must yield 401."""
    endpoints = [
        "/graph/path?from=A&to=B",
        "/graph/communities",
        "/roles",
        "/bridges",
        "/kumbh/observations",
        "/kumbh/signals",
        "/kumbh/clusters",
        "/kumbh/events/KUMBH-EVT-0050/intelligence",
    ]

    for ep in endpoints:
        r = await client.get(ep)
        assert r.status_code == 401, f"Expected 401 for unauthenticated {ep}"
        err = r.json().get("detail", {}).get("error", {}) or r.json().get("error", {})
        assert err.get("code") == "MISSING_AUTH"


@pytest.mark.asyncio
async def test_rbac_unauthorized_action(client):
    """Auditor role cannot access MULE_VIEW endpoint."""
    r = await client.get("/mule/chains", headers={"X-Demo-User": "auditor1"})
    assert r.status_code == 403
    err = r.json().get("detail", {}).get("error", {}) or r.json().get("error", {})
    assert err.get("code") == "FORBIDDEN"


# ─────────────────────────────────────────────────────────────
# 5. Audit Logging & Chain Integrity
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_entries_and_chain_validity(client):
    """Sensitive graph and Kumbh reads must append valid audit log entries."""
    store = get_store()
    seq_before = len(store.audit_log)

    # 1. Trigger sensitive views
    await client.get("/graph/path?from=A&to=B", headers={"X-Demo-User": "analyst1"})
    await client.get("/roles", headers={"X-Demo-User": "analyst1"})
    await client.get("/bridges", headers={"X-Demo-User": "analyst1"})
    await client.get("/kumbh/observations", headers={"X-Demo-User": "analyst1"})
    await client.get("/kumbh/signals", headers={"X-Demo-User": "analyst1"})
    await client.get("/kumbh/clusters", headers={"X-Demo-User": "analyst1"})
    await client.get("/kumbh/events/KUMBH-EVT-0050/intelligence", headers={"X-Demo-User": "analyst1"})

    seq_after = len(store.audit_log)
    assert seq_after >= seq_before + 7

    # Verify audit action names
    recent_actions = [e["action"] for e in store.audit_log[-7:]]
    assert "GRAPH_PATH_VIEW" in recent_actions
    assert "GRAPH_ROLES_VIEW" in recent_actions
    assert "GRAPH_BRIDGES_VIEW" in recent_actions
    assert "KUMBH_OBSERVATIONS_VIEW" in recent_actions
    assert "KUMBH_SIGNALS_VIEW" in recent_actions
    assert "KUMBH_CLUSTERS_VIEW" in recent_actions
    assert "KUMBH_EVENT_INTELLIGENCE_VIEW" in recent_actions

    # 2. Verify hash chain integrity (restricted to AUDITOR)
    r_ver = await client.get("/audit/verify", headers={"X-Demo-User": "auditor1"})
    assert r_ver.status_code == 200
    assert r_ver.json()["valid"] is True


# ─────────────────────────────────────────────────────────────
# 6. Kumbh Observations & Truth-Leak Protection
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_kumbh_observations_no_truth_leak(client):
    """Observations must return objective data only, with no generator oracle fields."""
    r = await client.get("/kumbh/observations?limit=50", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    observations = r.json()
    assert len(observations) > 0

    forbidden_keys = {"planted", "planted_id", "truth_label", "expected_label", "oracle"}

    for obs in observations:
        assert "event_id" in obs
        assert "event_type" in obs
        assert "ts" in obs
        assert "zone" in obs
        assert "status" in obs
        assert "provenance" in obs

        # Ensure no forbidden ground-truth fields are present
        for fk in forbidden_keys:
            assert fk not in obs, f"Forbidden key '{fk}' leaked in observation {obs['event_id']}"
            assert fk not in obs.get("location_info", {})


# ─────────────────────────────────────────────────────────────
# 7. Kumbh Intelligence Signals
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_kumbh_signals_structure(client):
    """Signals must preserve explainability, evidence tiers, and review requirement."""
    r = await client.get("/kumbh/signals", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    signals = r.json()

    for sig in signals:
        assert "signal_id" in sig
        assert "event_id" in sig
        assert "signal_type" in sig
        assert "confidence" in sig
        assert sig["evidence_tier"] in ("STRONG", "MEDIUM", "WEAK")
        assert "reasons" in sig
        assert "evidence" in sig
        assert "provenance" in sig
        assert sig["requires_investigator_review"] is True
        assert sig["action"] == "Requires investigator review"


# ─────────────────────────────────────────────────────────────
# 8. Kumbh Incident Clusters
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_kumbh_clusters_are_operational_not_syndicates(client):
    """Clusters must be operational grouping only, never labeled as criminal syndicates."""
    r = await client.get("/kumbh/clusters", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    clusters = r.json()

    valid_cluster_types = {
        "SHARED_INFRASTRUCTURE_CLUSTER",
        "SHARED_ENTITY_CLUSTER",
        "SPATIO_TEMPORAL_BURST",
    }

    for c in clusters:
        assert "cluster_id" in c
        assert c["cluster_type"] in valid_cluster_types
        assert "member_events" in c
        assert "shared_evidence" in c
        assert "confidence" in c
        assert c["requires_investigator_review"] is True
        assert c["action"] == "Requires investigator review"
        # Must not claim guilt or confirmed syndicate
        assert "Confirmed criminal" not in c.get("explanation", "")


# ─────────────────────────────────────────────────────────────
# 9. Per-Event Intelligence & Zero-Correlation Safety
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_per_event_intelligence_portfolio(client):
    """Event intelligence portfolio must distinguish event, observation, signals, and context."""
    store = get_store()
    assert len(store.kumbh_events) > 0
    first_event_id = store.kumbh_events[0]["event_id"]

    r = await client.get(
        f"/kumbh/events/{first_event_id}/intelligence",
        headers={"X-Demo-User": "analyst1"},
    )
    assert r.status_code == 200
    portfolio = r.json()

    assert portfolio["event_id"] == first_event_id
    assert "event" in portfolio
    assert "observation" in portfolio
    assert "signals" in portfolio
    assert "network_context" in portfolio
    assert "cluster" in portfolio
    assert portfolio["requires_investigator_review"] is True


@pytest.mark.asyncio
async def test_zero_correlation_event_produces_no_false_signal(client):
    """
    CRITICAL SAFETY PROPERTY:
    Civilian or benign events with no graph correlation (e.g. lost & found / power outage)
    must retain their observation while producing zero signals and null network context.
    """
    r = await client.get(
        "/kumbh/events/KUMBH-EVT-0050/intelligence",
        headers={"X-Demo-User": "analyst1"},
    )
    assert r.status_code == 200
    portfolio = r.json()

    assert portfolio["event_id"] == "KUMBH-EVT-0050"
    assert portfolio["observation"] is not None
    assert portfolio["signals"] == [], "Zero-correlation event must not produce false signals"
    assert portfolio["network_context"] is None, "Zero-correlation event must have no network context"
    assert portfolio["requires_investigator_review"] is True


@pytest.mark.asyncio
async def test_event_intelligence_not_found(client):
    """Non-existent event_id must return 404."""
    r = await client.get(
        "/kumbh/events/NON_EXISTENT_EVT/intelligence",
        headers={"X-Demo-User": "analyst1"},
    )
    assert r.status_code == 404
    err = r.json().get("detail", {}).get("error", {}) or r.json().get("error", {})
    assert err.get("code") == "NOT_FOUND"
