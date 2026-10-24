"""
sutradhar_api/store.py
In-memory data store that:
1. Loads artifacts from artifacts/ if present.
2. Falls back to contracts/fixtures/ if not.
3. Never reads ground truth answer keys.
All data is synthetic.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sutradhar_api.config import (
    CONTRACTS_FIXTURES_DIR,
    KUMBH_EVENTS_PATH,
    artifacts_path,
)

log = logging.getLogger(__name__)


def _load_json(path: Path) -> Any:
    if path.exists():
        text = path.read_text(encoding="utf-8").strip()
        if text:
            return json.loads(text)
    return None


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning("Skipping bad JSONL line in %s", path)
    return records


class DataStore:
    """Singleton in-memory store for the demo. Loaded once at startup."""

    def __init__(self) -> None:
        self._entities: dict[str, dict] = {}
        self._links: dict[str, dict] = {}
        self._graph_data: dict[str, Any] = {"nodes": [], "edges": []}
        self._communities: dict[str, dict] = {}
        self._roles: list[dict] = []
        self._bridges: list[dict] = []
        self._mule_chains: list[dict] = []
        self._audit_log: list[dict] = []
        self._decisions: dict[str, dict] = {}
        self._kumbh_events: list[dict] = []
        self._kumbh_event_cursor: int = 0
        self._kumbh_alerts: list[dict] = []
        self._kumbh_alert_counter: int = 0
        self._kumbh_observations: list[dict] = []
        self._kumbh_signals: list[dict] = []
        self._kumbh_clusters: list[dict] = []
        self._kumbh_event_intelligence: dict[str, dict] = {}
        self._federated_queries: list[dict] = []
        self._query_counter: int = 0
        self._metrics: dict = {}
        self._dossiers: dict[str, dict] = {}
        self._dossier_counter: int = 0
        # Audit chain state
        self._audit_seq: int = 0
        self._audit_prev_hash: str = "0" * 64

    # ── Loaders ──────────────────────────────────────────────

    def load(self) -> None:
        """Load all data at startup."""
        self._load_entities()
        self._load_links()
        self._load_graph_data()
        self._load_communities()
        self._load_kumbh_events()
        self._load_kumbh_intelligence()
        self._load_metrics()
        self._init_audit_chain()
        log.info(
            "DataStore loaded: %d entities, %d links, %d communities, %d kumbh events, %d observations, %d signals, %d clusters",
            len(self._entities),
            len(self._links),
            len(self._communities),
            len(self._kumbh_events),
            len(self._kumbh_observations),
            len(self._kumbh_signals),
            len(self._kumbh_clusters),
        )

    def _load_entities(self) -> None:
        fb = CONTRACTS_FIXTURES_DIR / "api" / "GET_entities_id.json"
        hero = _load_json(fb)
        if hero:
            self._entities[hero["entity_id"]] = hero

        path = artifacts_path("er/entities.jsonl")
        raw = _load_jsonl(path)
        for e in raw:
            if e["entity_id"] not in self._entities:
                self._entities[e["entity_id"]] = e

    def _load_links(self) -> None:
        path = artifacts_path("er/links.jsonl")
        raw = _load_jsonl(path)
        if not raw:
            fb = CONTRACTS_FIXTURES_DIR / "api" / "GET_entities_id_links.json"
            data = _load_json(fb) or []
            raw = data if isinstance(data, list) else [data]
        for lnk in raw:
            self._links[lnk["link_id"]] = lnk

    def _load_graph_data(self) -> None:
        path = artifacts_path("graph/graph.json")
        data = _load_json(path)
        if isinstance(data, dict) and data.get("nodes") and data.get("edges"):
            self._graph_data = data
        else:
            cid_path = CONTRACTS_FIXTURES_DIR / "api" / "GET_graph_communities_id.json"
            cid_data = _load_json(cid_path) or {}
            nodes = list(cid_data.get("nodes") or [])
            edges = list(cid_data.get("edges") or [])

            path_fixture = CONTRACTS_FIXTURES_DIR / "api" / "GET_graph_path.json"
            path_data = _load_json(path_fixture) or {}
            existing_node_ids = {n["id"] for n in nodes if isinstance(n, dict) and "id" in n}
            for nid in path_data.get("path", []):
                if nid not in existing_node_ids:
                    nodes.append(
                        {
                            "id": nid,
                            "type": "PERSON" if nid.startswith("P-") else "PHONE",
                            "label": nid,
                        }
                    )
                    existing_node_ids.add(nid)

            existing_edge_pairs = {
                (e["source"], e["target"])
                for e in edges
                if isinstance(e, dict) and "source" in e and "target" in e
            }
            for e in path_data.get("edges", []):
                src = e.get("source") or e.get("from")
                tgt = e.get("target") or e.get("to")
                if (
                    src
                    and tgt
                    and (src, tgt) not in existing_edge_pairs
                    and (tgt, src) not in existing_edge_pairs
                ):
                    edges.append(
                        {
                            "edge_id": e.get("edge_id", f"E-{src}-{tgt}"),
                            "source": src,
                            "target": tgt,
                            "type": e.get("type", "ASSOCIATED_WITH"),
                            "strength": e.get("strength", "STRONG"),
                            "evidence": list(e.get("evidence") or []),
                            "confidence": e.get("confidence", 0.90),
                        }
                    )
                    existing_edge_pairs.add((src, tgt))

            for ent in self._entities.values():
                eid = ent.get("entity_id")
                if eid and eid not in existing_node_ids:
                    nodes.append(
                        {
                            "id": eid,
                            "type": ent.get("entity_type", "PERSON"),
                            "label": ent.get("canonical_name", eid),
                            "props": ent.get("attributes", {}),
                        }
                    )
                    existing_node_ids.add(eid)

            self._graph_data = {"nodes": nodes, "edges": edges}

    def _load_communities(self) -> None:
        path = artifacts_path("graph/communities.jsonl")
        raw = _load_jsonl(path)
        if not raw:
            json_path = artifacts_path("graph/communities.json")
            c_data = _load_json(json_path)
            if isinstance(c_data, dict) and "communities" in c_data:
                raw = c_data["communities"]
            elif isinstance(c_data, list):
                raw = c_data
            else:
                fb = CONTRACTS_FIXTURES_DIR / "api" / "GET_graph_communities.json"
                data = _load_json(fb) or []
                raw = data if isinstance(data, list) else [data]
        for c in raw:
            c.setdefault("members", [])
            c.setdefault("member_count", c.get("size", len(c.get("members", []))))
            c.setdefault("continuing_activity", False)
            self._communities[c["community_id"]] = c

        # Load roles / bridges / mule chains from artifacts or fixtures
        roles_path = artifacts_path("graph/roles.json")
        r_data = _load_json(roles_path)
        if isinstance(r_data, dict) and "roles" in r_data:
            self._roles = r_data["roles"]
        elif isinstance(r_data, list):
            self._roles = r_data
        else:
            self._roles = _load_json(CONTRACTS_FIXTURES_DIR / "api" / "GET_roles.json") or []

        bridges_path = artifacts_path("graph/bridges.json")
        b_data = _load_json(bridges_path)
        if isinstance(b_data, dict) and "bridges" in b_data:
            self._bridges = b_data["bridges"]
        elif isinstance(b_data, list):
            self._bridges = b_data
        else:
            self._bridges = _load_json(CONTRACTS_FIXTURES_DIR / "api" / "GET_bridges.json") or []

        mule_path = artifacts_path("graph/mule_chains.json")
        m_data = _load_json(mule_path)
        if isinstance(m_data, dict) and "chains" in m_data:
            self._mule_chains = m_data["chains"]
        elif isinstance(m_data, dict) and "mule_chains" in m_data:
            self._mule_chains = m_data["mule_chains"]
        elif isinstance(m_data, list):
            self._mule_chains = m_data
        else:
            self._mule_chains = (
                _load_json(CONTRACTS_FIXTURES_DIR / "api" / "GET_mule_chains.json") or []
            )

        # Normalize fallback fixture records to satisfy internal analytics schemas
        for r in self._roles:
            if "reasons" in r and isinstance(r["reasons"], list):
                r["reasons"] = [
                    x.get("text", str(x)) if isinstance(x, dict) else str(x) for x in r["reasons"]
                ]
            r.setdefault("confidence", 0.85)
            r.setdefault("evidence_record_ids", [])

        for b in self._bridges:
            b.setdefault("node_id", b.get("entity_id", ""))
            b.setdefault("node_type", b.get("entity_type", "PERSON"))
            b.setdefault("label", str(b.get("node_id", "Bridge Node")))
            if "linked_person" in b and "linked_person_ids" not in b:
                b["linked_person_ids"] = [b["linked_person"]]
            b.setdefault("linked_person_ids", [])
            b.setdefault("evidence_record_ids", [])
            b.setdefault("reasons", ["Cross-community bridge detected"])
            b.setdefault("score", 0.80)

        for chain in self._mule_chains:
            chain.setdefault(
                "depth_gained",
                max(0, chain.get("max_depth", 1) - chain.get("layer1_baseline_depth", 1)),
            )
            for acc in chain.get("accounts", []):
                if "account_key" in acc and "account_id" not in acc:
                    acc["account_id"] = acc["account_key"]
                if "account_id" in acc and "account_key" not in acc:
                    acc["account_key"] = acc["account_id"]
                acc.setdefault("holder_entity_id", f"ENT-{acc.get('account_key', 'UNKNOWN')}")
                acc.setdefault("holder_name", f"Account Holder {acc.get('account_key', '')}")
                if "reasons" in acc and isinstance(acc["reasons"], list):
                    acc["reasons"] = [
                        x.get("text", str(x)) if isinstance(x, dict) else str(x)
                        for x in acc["reasons"]
                    ]
                if "median_pass_through_minutes" in acc and "median_passthrough_minutes" not in acc:
                    acc["median_passthrough_minutes"] = acc["median_pass_through_minutes"]
                acc.setdefault("median_passthrough_minutes", 0.0)
            for edge in chain.get("edges", []):
                if "from" in edge and "from_account" not in edge:
                    edge["from_account"] = edge["from"]
                if "to" in edge and "to_account" not in edge:
                    edge["to_account"] = edge["to"]

    def _load_kumbh_events(self) -> None:
        events = _load_jsonl(KUMBH_EVENTS_PATH)
        if not events:
            fb = CONTRACTS_FIXTURES_DIR / "data" / "kumbh" / "events.jsonl"
            events = _load_jsonl(fb)
        self._kumbh_events = events
        self._kumbh_event_cursor = 0

    def _load_kumbh_intelligence(self) -> None:
        """
        Step 5A: Initialize KumbhOperationsEngine using loaded graph & analytics,
        process the feed once deterministically, and cache clean, indexed results.
        Never exposes ground truth labels, planted markers, or answer keys.
        """
        from sutradhar_graph.kumbh_ops import KumbhOperationsEngine

        engine = KumbhOperationsEngine(
            graph_data=self._graph_data,
            communities=list(self._communities.values()),
            roles=self._roles,
            bridges=self._bridges,
            mule_chains=self._mule_chains,
        )
        results = engine.process_feed(self._kumbh_events)

        # 1. Clean operational observations (strictly strip planted/truth fields)
        observations: list[dict[str, Any]] = []
        for ev in self._kumbh_events:
            raw_details = dict(ev.get("details") or {})
            clean_details = {
                k: v
                for k, v in raw_details.items()
                if not k.startswith("planted")
                and not k.startswith("truth")
                and not k.startswith("oracle")
                and not k.startswith("expected")
            }
            obs = {
                "event_id": ev.get("event_id"),
                "event_type": ev.get("event_type"),
                "ts": ev.get("ts"),
                "zone": ev.get("zone"),
                "location_info": clean_details,
                "related_ids": list(ev.get("related_ids") or []),
                "source_agency": ev.get("source_agency", "KUMBH_SURVEILLANCE"),
                "status": "OBSERVED",
                "provenance": dict(
                    ev.get("provenance")
                    or {
                        "source": "Kumbh Operations Feed",
                        "event_id": ev.get("event_id"),
                        "zone": ev.get("zone"),
                    }
                ),
            }
            observations.append(obs)
        self._kumbh_observations = observations
        obs_by_id = {obs["event_id"]: obs for obs in observations}

        # 2. Intelligence signals extracted from Step 4 review items
        intel_items = results.get("intelligence_items", [])
        signals: list[dict[str, Any]] = []
        signals_by_event: dict[str, list[dict[str, Any]]] = {}
        review_by_event: dict[str, dict[str, Any]] = {}

        for item in intel_items:
            ev_id = item.get("related_event")
            review_by_event[ev_id] = item
            item_signals = item.get("signals") or []
            for idx, sig in enumerate(item_signals):
                sig_id = f"SIG-{ev_id}-{idx + 1:02d}"
                s_obj = {
                    "signal_id": sig_id,
                    "event_id": ev_id,
                    "signal_type": sig.get("signal_type"),
                    "confidence": sig.get("confidence", item.get("confidence", 0.85)),
                    "evidence_tier": item.get("evidence_tier", "MEDIUM"),
                    "description": sig.get("description", ""),
                    "reasons": [sig.get("description")] if sig.get("description") else [],
                    "evidence": list(sig.get("evidence") or item.get("evidence") or []),
                    "provenance": sig.get("provenance") or item.get("provenance") or {},
                    "network_context": item.get("network_context"),
                    "requires_investigator_review": True,
                    "action": "Requires investigator review",
                }
                signals.append(s_obj)
                signals_by_event.setdefault(ev_id, []).append(s_obj)

        self._kumbh_signals = signals

        # 3. Incident clusters (strictly operational clusters, never criminal syndicates)
        raw_clusters = results.get("clusters", [])
        clusters: list[dict[str, Any]] = []
        clusters_by_event: dict[str, list[dict[str, Any]]] = {}
        for c in raw_clusters:
            clust_obj = {
                "cluster_id": c.get("cluster_id"),
                "cluster_type": c.get("cluster_type"),
                "member_events": list(c.get("member_events") or []),
                "shared_evidence": list(c.get("shared_evidence") or []),
                "confidence": c.get("confidence", 0.80),
                "provenance": dict(c.get("provenance") or {}),
                "explanation": c.get("explanation", ""),
                "requires_investigator_review": True,
                "action": "Requires investigator review",
            }
            clusters.append(clust_obj)
            for m_id in clust_obj["member_events"]:
                clusters_by_event.setdefault(m_id, []).append(clust_obj)

        self._kumbh_clusters = clusters

        # 4. Per-event intelligence lookup table
        event_intelligence: dict[str, dict[str, Any]] = {}
        for ev in self._kumbh_events:
            ev_id = ev.get("event_id")
            obs = obs_by_id.get(ev_id, {})
            ev_signals = signals_by_event.get(ev_id, [])
            rev = review_by_event.get(ev_id)
            ev_clusters = clusters_by_event.get(ev_id, [])
            cluster_val = (
                ev_clusters[0] if len(ev_clusters) == 1 else (ev_clusters if ev_clusters else None)
            )

            event_intelligence[ev_id] = {
                "event_id": ev_id,
                "event": obs,
                "observation": obs,
                "signals": ev_signals,
                "network_context": rev.get("network_context") if (rev and ev_signals) else None,
                "cluster": cluster_val,
                "requires_investigator_review": True,
            }

        self._kumbh_event_intelligence = event_intelligence

    def _load_metrics(self) -> None:
        path = artifacts_path("metrics.json")
        if not path.exists():
            path = CONTRACTS_FIXTURES_DIR / "artifacts" / "metrics.json"
        self._metrics = _load_json(path) or {}

    def _init_audit_chain(self) -> None:
        import hashlib

        genesis = {
            "seq": 1,
            "ts": "2026-10-17T00:00:00Z",
            "actor": "SYSTEM",
            "role": "SYSTEM",
            "action": "GENESIS",
            "purpose": None,
            "case_ref": None,
            "summary": "Audit chain initialised.",
            "prev_hash": "0" * 64,
        }
        genesis_body = json.dumps({k: v for k, v in genesis.items() if k != "hash"}, sort_keys=True)
        genesis["hash"] = hashlib.sha256(genesis_body.encode()).hexdigest()
        self._audit_log = [genesis]
        self._audit_seq = 1
        self._audit_prev_hash = genesis["hash"]

    # ── Accessors ─────────────────────────────────────────────

    @property
    def entities(self) -> dict[str, dict]:
        return self._entities

    @property
    def links(self) -> dict[str, dict]:
        return self._links

    @property
    def communities(self) -> dict[str, dict]:
        return self._communities

    @property
    def roles(self) -> list[dict]:
        return self._roles

    @property
    def bridges(self) -> list[dict]:
        return self._bridges

    @property
    def mule_chains(self) -> list[dict]:
        return self._mule_chains

    @property
    def metrics(self) -> dict:
        return self._metrics

    @property
    def audit_log(self) -> list[dict]:
        return list(self._audit_log)

    @property
    def kumbh_events(self) -> list[dict]:
        return self._kumbh_events

    @property
    def kumbh_alerts(self) -> list[dict]:
        return list(self._kumbh_alerts)

    @property
    def dossiers(self) -> dict[str, dict]:
        return self._dossiers

    @property
    def federated_queries(self) -> list[dict]:
        return list(self._federated_queries)

    @property
    def graph_data(self) -> dict[str, Any]:
        return self._graph_data

    @property
    def kumbh_observations(self) -> list[dict]:
        return list(self._kumbh_observations)

    @property
    def kumbh_signals(self) -> list[dict]:
        return list(self._kumbh_signals)

    @property
    def kumbh_clusters(self) -> list[dict]:
        return list(self._kumbh_clusters)

    def get_kumbh_event_intelligence(self, event_id: str) -> dict | None:
        return self._kumbh_event_intelligence.get(event_id)

    # ── Mutation helpers ───────────────────────────────────────

    def record_audit(
        self,
        actor: str,
        role: str,
        action: str,
        summary: str,
        purpose: str | None = None,
        case_ref: str | None = None,
        agency: str | None = None,
    ) -> int:
        self._audit_seq += 1
        entry = {
            "seq": self._audit_seq,
            "ts": datetime.now(UTC).isoformat(),
            "actor": actor,
            "role": role,
            "agency": agency,
            "action": action,
            "purpose": purpose,
            "case_ref": case_ref,
            "summary": summary,
            "prev_hash": self._audit_prev_hash,
        }
        body = json.dumps({k: v for k, v in entry.items() if k != "hash"}, sort_keys=True)
        entry["hash"] = hashlib.sha256(body.encode()).hexdigest()
        self._audit_prev_hash = entry["hash"]
        self._audit_log.append(entry)
        return self._audit_seq

    def verify_audit_chain(self) -> dict:
        entries = self._audit_log
        if not entries:
            return {"valid": True, "entries": 0, "head_hash": "", "broken_at": None}
        prev_hash = "0" * 64
        for entry in entries:
            if entry["prev_hash"] != prev_hash:
                return {
                    "valid": False,
                    "entries": len(entries),
                    "head_hash": entry.get("hash", ""),
                    "broken_at": entry["seq"],
                }
            body = json.dumps({k: v for k, v in entry.items() if k != "hash"}, sort_keys=True)
            expected = hashlib.sha256(body.encode()).hexdigest()
            if entry["hash"] != expected:
                return {
                    "valid": False,
                    "entries": len(entries),
                    "head_hash": entry.get("hash", ""),
                    "broken_at": entry["seq"],
                }
            prev_hash = entry["hash"]
        return {
            "valid": True,
            "entries": len(entries),
            "head_hash": entries[-1]["hash"],
            "broken_at": None,
        }

    def tamper_audit_for_demo(self) -> dict:
        """Corrupt one entry for the demo — only used when DEMO_TAMPER=1."""
        if len(self._audit_log) >= 2:
            self._tampered_backup = dict(self._audit_log[1])
            self._audit_log[1]["summary"] = "[TAMPERED FOR DEMO]"
            self._audit_log[1]["hash"] = "deadbeef" * 8
            return {
                "tampered_seq": 2,
                "message": "Entry seq=2 corrupted. Call GET /audit/verify to detect.",
            }
        return {"tampered_seq": None, "message": "Not enough entries to tamper."}

    def repair_audit_for_demo(self) -> dict:
        """Restore tampered entry from backup — only used when DEMO_TAMPER=1."""
        if (
            hasattr(self, "_tampered_backup")
            and self._tampered_backup
            and len(self._audit_log) >= 2
        ):
            self._audit_log[1] = dict(self._tampered_backup)
            self._tampered_backup = None
            return {"repaired_seq": 2, "message": "Entry seq=2 restored from backup."}
        return {"repaired_seq": None, "message": "No tampered entry found to repair."}

    def update_link(
        self,
        link_id: str,
        status: str,
        decided_by: str | None,
        decided_at: str | None,
        reason: str | None,
    ) -> None:
        if link_id in self._links:
            self._links[link_id]["status"] = status
            self._links[link_id]["decided_by"] = decided_by
            self._links[link_id]["decided_at"] = decided_at
            self._links[link_id]["decision_reason"] = reason

    def play_next_kumbh_event(self) -> dict | None:
        if self._kumbh_event_cursor >= len(self._kumbh_events):
            return None
        event = self._kumbh_events[self._kumbh_event_cursor]
        self._kumbh_event_cursor += 1
        return event

    def add_kumbh_alert(self, event: dict, confidence: float, reason: str) -> dict:
        self._kumbh_alert_counter += 1
        alert_id = f"ALR-{self._kumbh_alert_counter:06d}"
        alert = {
            "alert_id": alert_id,
            "event_id": event.get("event_id"),
            "zone": event.get("zone"),
            "alert_type": event.get("event_type"),
            "confidence": confidence,
            "reason": reason,
            "state": "OPEN",
            "created_at": datetime.now(UTC).isoformat(),
            "confirmed_at": None,
            "dismissed_at": None,
        }
        self._kumbh_alerts.append(alert)
        return alert

    def update_kumbh_alert(self, alert_id: str, action: str) -> dict | None:
        for alert in self._kumbh_alerts:
            if alert["alert_id"] == alert_id:
                ts = datetime.now(UTC).isoformat()
                if action == "CONFIRM":
                    alert["state"] = "CONFIRMED"
                    alert["confirmed_at"] = ts
                else:
                    alert["state"] = "DISMISSED"
                    alert["dismissed_at"] = ts
                return alert
        return None

    def add_federated_query(self, query: dict) -> None:
        self._federated_queries.append(query)

    def get_next_query_id(self) -> str:
        self._query_counter += 1
        return f"Q-{self._query_counter:06d}"

    def generate_dossier(self, community_id: str, actor: str) -> dict:
        self._dossier_counter += 1
        dossier_id = f"DOS-{self._dossier_counter:03d}"
        community = self._communities.get(community_id, {})
        dos = {
            "dossier_id": dossier_id,
            "community_id": community_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "DRAFT",
            "summary": f"Community {community.get('label', community_id)}: {community.get('size', '?')} members.",
            "legal_params": {"lookback_years": 10, "min_chargesheets": 3, "verified": False},
            "sections": {
                "linked_cases": [
                    {"case_id": c, "text": "Case linked to community.", "source_record_ids": []}
                    for c in community.get("case_ids", [])
                ],
                "prior_chargesheets": [],
                "associates": [],
                "financial_links": [],
                "timeline": [],
                "evidence_gaps": [],
            },
            "disclaimer": "Draft to support officer judgement. Synthetic data. Legal parameters unverified.",
        }
        self._dossiers[dossier_id] = dos
        return dos


# Global singleton
_store: DataStore | None = None


def get_store() -> DataStore:
    global _store
    if _store is None:
        _store = DataStore()
    return _store
