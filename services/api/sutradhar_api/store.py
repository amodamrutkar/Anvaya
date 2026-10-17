"""
sutradhar_api/store.py
In-memory data store that:
1. Loads artifacts from artifacts/ if present.
2. Falls back to contracts/fixtures/ if not.
3. Never reads ground truth answer keys.
All data is synthetic.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC
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
        self._load_communities()
        self._load_kumbh_events()
        self._load_metrics()
        self._init_audit_chain()
        log.info(
            "DataStore loaded: %d entities, %d links, %d communities, %d kumbh events",
            len(self._entities),
            len(self._links),
            len(self._communities),
            len(self._kumbh_events),
        )

    def _load_entities(self) -> None:
        path = artifacts_path("er/entities.jsonl")
        raw = _load_jsonl(path)
        if not raw:
            # Fallback to api fixture
            fb = CONTRACTS_FIXTURES_DIR / "api" / "GET_entities_id.json"
            item = _load_json(fb)
            if item:
                raw = [item]
        for e in raw:
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

    def _load_communities(self) -> None:
        path = artifacts_path("graph/communities.jsonl")
        raw = _load_jsonl(path)
        if not raw:
            fb = CONTRACTS_FIXTURES_DIR / "api" / "GET_graph_communities.json"
            data = _load_json(fb) or []
            raw = data if isinstance(data, list) else [data]
        for c in raw:
            self._communities[c["community_id"]] = c
        # Load roles / bridges / mule chains from fixtures
        roles_path = CONTRACTS_FIXTURES_DIR / "api" / "GET_roles.json"
        self._roles = _load_json(roles_path) or []
        bridges_path = CONTRACTS_FIXTURES_DIR / "api" / "GET_bridges.json"
        self._bridges = _load_json(bridges_path) or []
        mule_path = CONTRACTS_FIXTURES_DIR / "api" / "GET_mule_chains.json"
        self._mule_chains = _load_json(mule_path) or []

    def _load_kumbh_events(self) -> None:
        events = _load_jsonl(KUMBH_EVENTS_PATH)
        if not events:
            fb = CONTRACTS_FIXTURES_DIR / "data" / "kumbh" / "events.jsonl"
            events = _load_jsonl(fb)
        self._kumbh_events = events
        self._kumbh_event_cursor = 0

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

    # ── Mutation helpers ───────────────────────────────────────

    def record_audit(
        self,
        actor: str,
        role: str,
        action: str,
        summary: str,
        purpose: str | None = None,
        case_ref: str | None = None,
    ) -> int:
        import hashlib
        from datetime import datetime

        self._audit_seq += 1
        entry = {
            "seq": self._audit_seq,
            "ts": datetime.now(UTC).isoformat(),
            "actor": actor,
            "role": role,
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
        import hashlib

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
        from datetime import datetime

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
        from datetime import datetime

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
        from datetime import datetime

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
