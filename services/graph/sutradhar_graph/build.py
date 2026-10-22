"""
Graph Builder for Sutradhar.

Ingests agency records, accounts, transactions, and ER clusters to construct
a multi-modal heterogeneous intelligence graph with STRONG/MEDIUM/WEAK evidence tiers,
provenance trails, and confidence values per edge.
"""

import json
from pathlib import Path
from typing import Any

import networkx as nx

from .models import EdgeModel, EdgeStrength, EdgeType, GraphData, NodeModel, NodeType


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class GraphBuilder:
    """Builds the heterogeneous Sutradhar intelligence graph."""

    def __init__(self, data_dir: str | Path, er_dir: str | Path | None = None):
        self.data_dir = Path(data_dir)
        self.er_dir = Path(er_dir) if er_dir else None

        self.nodes: dict[str, NodeModel] = {}
        self.edges: dict[str, EdgeModel] = {}
        self._edge_index: dict[tuple[str, str, EdgeType], EdgeModel] = {}
        self._edge_counter = 0

        # Raw records & data
        self.records: list[dict[str, Any]] = []
        self.accounts: list[dict[str, Any]] = []
        self.transactions: list[dict[str, Any]] = []
        self.kumbh_events: list[dict[str, Any]] = []

        # Entity resolution mapping: mention_id -> entity_id
        self.mention_to_entity: dict[Any, str] = {}
        self.entity_to_name: dict[str, str] = {}
        self.entity_to_mentions: dict[str, list[str]] = {}

        # NetworkX representations
        self.nx_graph = nx.MultiDiGraph()

    def _next_edge_id(self) -> str:
        self._edge_counter += 1
        return f"EDGE-{self._edge_counter:06d}"

    def _add_node(
        self,
        node_id: str,
        node_type: NodeType,
        label: str,
        attributes: dict[str, Any] | None = None,
    ) -> NodeModel:
        if node_id in self.nodes:
            if attributes:
                self.nodes[node_id].attributes.update(attributes)
            return self.nodes[node_id]

        node = NodeModel(
            id=node_id,
            type=node_type,
            label=label,
            attributes=attributes or {},
        )
        self.nodes[node_id] = node
        self.nx_graph.add_node(node_id, type=node_type, label=label, **(attributes or {}))
        return node

    def _add_edge(
        self,
        source: str,
        target: str,
        edge_type: EdgeType,
        strength: EdgeStrength = "STRONG",
        evidence: list[str] | None = None,
        confidence: float = 1.0,
        provenance: dict[str, Any] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> EdgeModel:
        ev_list = sorted(set(evidence or []))
        key = (source, target, edge_type)

        if key in self._edge_index:
            existing = self._edge_index[key]
            combined_ev = sorted(set(existing.evidence + ev_list))
            existing.evidence = combined_ev
            if strength == "STRONG" or existing.strength == "STRONG":
                existing.strength = "STRONG"
            elif strength == "MEDIUM" or existing.strength == "MEDIUM":
                existing.strength = "MEDIUM"
            if provenance and not existing.provenance:
                existing.provenance = provenance
            return existing

        edge_id = self._next_edge_id()
        edge = EdgeModel(
            id=edge_id,
            source=source,
            target=target,
            type=edge_type,
            strength=strength,
            evidence=ev_list,
            confidence=confidence,
            provenance=provenance or {},
            attributes=attributes or {},
        )
        self.edges[edge_id] = edge
        self._edge_index[key] = edge
        self.nx_graph.add_edge(
            source,
            target,
            key=edge_id,
            id=edge_id,
            type=edge_type,
            strength=strength,
            evidence=ev_list,
            confidence=confidence,
            provenance=provenance or {},
            **(attributes or {}),
        )
        return edge

    def load_data(self) -> None:
        """Load records, accounts, transactions, and ER clusters."""
        # 1. Load Agency Records
        agency_dirs = ["STATE_POLICE", "MAHA_CYBER", "CENTRAL_AGENCY"]
        for agency in agency_dirs:
            rec_file = self.data_dir / agency / "records.jsonl"
            self.records.extend(_read_jsonl(rec_file))

        # 2. Load Cyber accounts and transactions
        acct_file = self.data_dir / "MAHA_CYBER" / "accounts.jsonl"
        self.accounts = _read_jsonl(acct_file)

        txn_file = self.data_dir / "MAHA_CYBER" / "transactions.jsonl"
        self.transactions = _read_jsonl(txn_file)

        # 3. Load Kumbh events if present
        kumbh_file = self.data_dir / "kumbh" / "events.jsonl"
        self.kumbh_events = _read_jsonl(kumbh_file)

        # 4. Load ER clusters if available
        is_v2 = "v2" in str(self.data_dir).lower()
        er_entities_file = self.er_dir / "entities.jsonl" if self.er_dir else None

        if er_entities_file and er_entities_file.exists():
            entities = _read_jsonl(er_entities_file)
            for ent in entities:
                # Strictly filter for PERSON entities to avoid overwriting person mention lookups
                if ent.get("entity_type") and ent.get("entity_type") != "PERSON":
                    continue
                ent_id = ent.get("entity_id") or f"ENT-{len(self.entity_to_name) + 1:04d}"
                cname = ent.get("canonical_name", "Unknown")
                mids = ent.get("mention_ids", [])
                self.entity_to_name[ent_id] = cname
                self.entity_to_mentions[ent_id] = mids
                for mid in mids:
                    self.mention_to_entity[mid] = ent_id

            if is_v2:
                # Map mentions by (record_id, name) for V2 records
                mentions_file = self.er_dir / "mentions.jsonl" if self.er_dir else None
                if mentions_file and mentions_file.exists():
                    mentions = _read_jsonl(mentions_file)
                    for m in mentions:
                        mid = m.get("mention_id")
                        rid = m.get("record_id")
                        nraw = m.get("name_raw")
                        nnorm = m.get("name_norm")
                        ent_id = self.mention_to_entity.get(mid)
                        if ent_id:
                            if rid and nraw:
                                self.mention_to_entity[(rid, nraw.strip())] = ent_id
                            if rid and nnorm:
                                self.mention_to_entity[(rid, nnorm.strip())] = ent_id
        else:
            # Fallback ER: group mentions by exact phone or normalized name
            self._provisional_entity_resolution()

    def _provisional_entity_resolution(self) -> None:
        """Provisional resolution when artifacts/er is not provided."""
        phone_to_ent: dict[str, str] = {}
        name_to_ent: dict[str, str] = {}
        ent_counter = 0

        for rec in self.records:
            rid = rec.get("record_id", "")
            ff = rec.get("form_fields", {})

            for acc in ff.get("accused", []):
                name = acc.get("name", "").strip()
                phone = acc.get("phone", "").strip()
                mid = f"M-{rid}-{name}"

                ent_id = None
                if phone and phone in phone_to_ent:
                    ent_id = phone_to_ent[phone]
                elif name and name in name_to_ent:
                    ent_id = name_to_ent[name]

                if not ent_id:
                    ent_counter += 1
                    ent_id = f"ENT-{ent_counter:04d}"
                    if name:
                        name_to_ent[name] = ent_id
                        self.entity_to_name[ent_id] = name
                    else:
                        self.entity_to_name[ent_id] = f"Person {ent_counter}"

                if phone:
                    phone_to_ent[phone] = ent_id

                self.mention_to_entity[mid] = ent_id
                self.entity_to_mentions.setdefault(ent_id, []).append(mid)

    def build_graph(self) -> GraphData:
        """Construct graph nodes and edges from loaded dataset."""
        self.load_data()
        is_v2 = "v2" in str(self.data_dir).lower()

        # Step A: Register Cases and Persons from Records
        for rec in self.records:
            rid = rec["record_id"]
            case_ref = rec.get("case_ref") or f"CASE-{rid}"
            crime_type = rec.get("crime_type", "GENERAL")
            agency = rec.get("agency", "UNKNOWN")
            district = rec.get("district", "Unknown")
            filed_date = rec.get("filed_date", "2025-01-01")

            # CASE Node
            self._add_node(
                node_id=case_ref,
                node_type="CASE",
                label=case_ref,
                attributes={
                    "crime_type": crime_type,
                    "agency": agency,
                    "district": district,
                    "filed_date": filed_date,
                    "record_ids": [rid],
                },
            )

            ff = rec.get("form_fields", {})
            accused_entities: list[str] = []

            # Accused Persons
            for acc in ff.get("accused", []):
                name = acc.get("name", "Unknown Accused").strip()
                mid = f"M-{rid}-{name}"

                person_id = None
                if is_v2:
                    person_id = (
                        self.mention_to_entity.get((rid, name))
                        or self.mention_to_entity.get((rid, name.lower()))
                        or self.mention_to_entity.get(mid)
                    )
                else:
                    person_id = self.mention_to_entity.get(mid)

                if not person_id:
                    person_id = f"ENT-{len(self.nodes) + 1:04d}"

                canonical_name = self.entity_to_name.get(person_id, name)

                # PERSON Node
                self._add_node(
                    node_id=person_id,
                    node_type="PERSON",
                    label=canonical_name,
                    attributes={"district": district, "roles": ["ACCUSED"]},
                )
                accused_entities.append(person_id)

                # Person -> ACCUSED_IN -> Case (STRONG)
                self._add_edge(
                    source=person_id,
                    target=case_ref,
                    edge_type="ACCUSED_IN",
                    strength="STRONG",
                    evidence=[rid],
                    confidence=1.0,
                    provenance={
                        "source_agency": agency,
                        "source_record_id": rid,
                        "evidence_field": "form_fields.accused",
                        "relationship_type": "ACCUSED_IN",
                        "evidence_tier": "STRONG",
                        "timestamp": filed_date,
                    },
                )

                # Phone (STRONG)
                phone = acc.get("phone")
                if phone:
                    phone_node_id = f"PHONE:{phone}"
                    self._add_node(phone_node_id, "PHONE", phone)
                    self._add_edge(
                        source=person_id,
                        target=phone_node_id,
                        edge_type="USES",
                        strength="STRONG",
                        evidence=[rid],
                        confidence=1.0,
                        provenance={
                            "source_agency": agency,
                            "source_record_id": rid,
                            "evidence_field": "form_fields.accused.phone",
                            "relationship_type": "USES",
                            "evidence_tier": "STRONG",
                            "timestamp": filed_date,
                        },
                    )

                # Address (WEAK edge per Phase 3)
                address = acc.get("address")
                if address and len(address.strip()) > 3:
                    addr_node_id = f"ADDRESS:{address.strip()}"
                    self._add_node(
                        addr_node_id,
                        "ADDRESS",
                        address.strip(),
                        attributes={"district": district},
                    )
                    self._add_edge(
                        source=person_id,
                        target=addr_node_id,
                        edge_type="LIVES_AT",
                        strength="WEAK",
                        evidence=[rid],
                        confidence=0.5,
                        provenance={
                            "source_agency": agency,
                            "source_record_id": rid,
                            "evidence_field": "form_fields.accused.address",
                            "relationship_type": "LIVES_AT",
                            "evidence_tier": "WEAK",
                            "timestamp": filed_date,
                        },
                    )

            # Co-accused edges (STRONG)
            for i in range(len(accused_entities)):
                for j in range(i + 1, len(accused_entities)):
                    p1, p2 = accused_entities[i], accused_entities[j]
                    self._add_edge(
                        source=p1,
                        target=p2,
                        edge_type="CO_ACCUSED_WITH",
                        strength="STRONG",
                        evidence=[rid],
                        confidence=1.0,
                        provenance={
                            "source_agency": agency,
                            "source_record_id": rid,
                            "evidence_field": "form_fields.accused",
                            "relationship_type": "CO_ACCUSED_WITH",
                            "evidence_tier": "STRONG",
                            "timestamp": filed_date,
                        },
                    )
                    self._add_edge(
                        source=p2,
                        target=p1,
                        edge_type="CO_ACCUSED_WITH",
                        strength="STRONG",
                        evidence=[rid],
                        confidence=1.0,
                        provenance={
                            "source_agency": agency,
                            "source_record_id": rid,
                            "evidence_field": "form_fields.accused",
                            "relationship_type": "CO_ACCUSED_WITH",
                            "evidence_tier": "STRONG",
                            "timestamp": filed_date,
                        },
                    )

            # Complainant / Victims
            comp = ff.get("complainant", {})
            if isinstance(comp, dict) and comp.get("name"):
                comp_name = comp["name"].strip()
                comp_mid = f"M-COMP-{rid}-{comp_name}"
                comp_id = (
                    self.mention_to_entity.get(comp_mid)
                    or f"ENT-COMP-{comp_name.replace(' ', '_')}"
                )
                self._add_node(
                    comp_id,
                    "PERSON",
                    comp_name,
                    attributes={"roles": ["VICTIM"]},
                )
                self._add_edge(
                    source=comp_id,
                    target=case_ref,
                    edge_type="VICTIM_IN",
                    strength="STRONG",
                    evidence=[rid],
                    confidence=1.0,
                    provenance={
                        "source_agency": agency,
                        "source_record_id": rid,
                        "evidence_field": "form_fields.complainant",
                        "relationship_type": "VICTIM_IN",
                        "evidence_tier": "STRONG",
                        "timestamp": filed_date,
                    },
                )

            # Accounts attached to record (STRONG)
            for acct in ff.get("accounts", []):
                bank = acct.get("bank", "BANK")
                acct_no = acct.get("account_no", "")
                if acct_no:
                    acct_key = f"{bank}:{acct_no}"
                    acct_node_id = f"ACCOUNT:{acct_key}"
                    self._add_node(
                        acct_node_id,
                        "ACCOUNT",
                        acct_key,
                        attributes={"bank": bank},
                    )
                    for p in accused_entities:
                        self._add_edge(
                            source=p,
                            target=acct_node_id,
                            edge_type="OWNS",
                            strength="STRONG",
                            evidence=[rid],
                            confidence=1.0,
                            provenance={
                                "source_agency": agency,
                                "source_record_id": rid,
                                "evidence_field": "form_fields.accounts",
                                "relationship_type": "OWNS",
                                "evidence_tier": "STRONG",
                                "timestamp": filed_date,
                            },
                        )

            # Vehicles attached to record (MEDIUM per Phase 3)
            for veh in ff.get("vehicles", []):
                if veh and veh != "N/A":
                    veh_node_id = f"VEHICLE:{veh}"
                    self._add_node(veh_node_id, "VEHICLE", veh)
                    for p in accused_entities:
                        self._add_edge(
                            source=p,
                            target=veh_node_id,
                            edge_type="OWNS",
                            strength="MEDIUM",
                            evidence=[rid],
                            confidence=0.85,
                            provenance={
                                "source_agency": agency,
                                "source_record_id": rid,
                                "evidence_field": "form_fields.vehicles",
                                "relationship_type": "OWNS",
                                "evidence_tier": "MEDIUM",
                                "timestamp": filed_date,
                            },
                        )

        # Step B: Accounts & Transactions (from MAHA_CYBER)
        import re

        name_to_person = {}
        for nid, n in self.nodes.items():
            if n.type == "PERSON":
                norm_lbl = re.sub(r"\s+", " ", n.label.lower().strip())
                name_to_person[norm_lbl] = nid

        for acct in self.accounts:
            ak = acct.get("account_key")
            if not ak:
                continue
            acct_node_id = f"ACCOUNT:{ak}"
            holder_raw = acct.get("holder_name_raw", "")
            self._add_node(
                acct_node_id,
                "ACCOUNT",
                ak,
                attributes={
                    "bank": acct.get("bank"),
                    "ifsc": acct.get("ifsc"),
                    "holder_name": holder_raw,
                    "complaint_count": acct.get("complaint_count", 0),
                    "account_category": acct.get("account_category", "ORDINARY"),
                },
            )

            # Link account to person if holder matches
            if holder_raw:
                clean_holder = re.sub(r"\(.*?\)", "", holder_raw).strip().lower()
                clean_holder = re.sub(r"\s+", " ", clean_holder)
                p_match = name_to_person.get(clean_holder)
                if p_match:
                    self._add_edge(
                        source=p_match,
                        target=acct_node_id,
                        edge_type="OWNS",
                        strength="STRONG",
                        evidence=[ak],
                        confidence=0.95,
                        provenance={
                            "source_agency": "MAHA_CYBER",
                            "source_record_id": ak,
                            "evidence_field": "accounts.holder_name_raw",
                            "relationship_type": "OWNS",
                            "evidence_tier": "STRONG",
                        },
                    )

        for txn in self.transactions:
            src_ak = txn.get("from_account")
            dst_ak = txn.get("to_account")
            if src_ak and dst_ak:
                src_node = f"ACCOUNT:{src_ak}"
                dst_node = f"ACCOUNT:{dst_ak}"
                self._add_node(src_node, "ACCOUNT", src_ak)
                self._add_node(dst_node, "ACCOUNT", dst_ak)
                ts_val = txn.get("ts") or txn.get("timestamp") or "2025-06-01T12:00:00Z"
                amt_val = float(txn.get("amount", 0.0))
                txn_id = txn.get("txn_id", "")
                self._add_edge(
                    source=src_node,
                    target=dst_node,
                    edge_type="TRANSFERRED_TO",
                    strength="STRONG",
                    confidence=1.0,
                    provenance={
                        "source_agency": "MAHA_CYBER",
                        "source_record_id": txn_id,
                        "evidence_field": "transactions",
                        "relationship_type": "TRANSFERRED_TO",
                        "evidence_tier": "STRONG",
                        "timestamp": ts_val,
                    },
                    attributes={
                        "amount": amt_val,
                        "ts": ts_val,
                        "channel": txn.get("channel", "UPI"),
                        "txn_id": txn_id,
                    },
                )

        # Step C: ER REVIEW links (Phase 3 & Phase 15: ER REVIEW does NOT merge entities)
        er_links_file = self.er_dir / "links.jsonl" if self.er_dir else None
        if er_links_file and er_links_file.exists():
            links = _read_jsonl(er_links_file)
            for link in links:
                if link.get("band") == "REVIEW":
                    a_mid = link.get("a_mention_id")
                    b_mid = link.get("b_mention_id")
                    ent_a = self.mention_to_entity.get(a_mid)
                    ent_b = self.mention_to_entity.get(b_mid)
                    if ent_a and ent_b and ent_a != ent_b:
                        self._add_node(ent_a, "PERSON", self.entity_to_name.get(ent_a, ent_a))
                        self._add_node(ent_b, "PERSON", self.entity_to_name.get(ent_b, ent_b))
                        link_id = link.get("link_id", "ER_REVIEW")
                        conf = float(link.get("score", 0.75))
                        self._add_edge(
                            source=ent_a,
                            target=ent_b,
                            edge_type="POSSIBLE_DUPLICATE_ENTITY",
                            strength="MEDIUM",
                            evidence=[link_id],
                            confidence=conf,
                            provenance={
                                "source_agency": "ENTITY_RESOLUTION",
                                "source_record_id": link_id,
                                "evidence_field": "ER_REVIEW_BAND",
                                "relationship_type": "POSSIBLE_DUPLICATE_ENTITY",
                                "confidence": conf,
                                "evidence_tier": "MEDIUM",
                                "explanation": link.get("explanation_text", ""),
                            },
                        )

        # Step D: Register Kumbh Events if present
        for evt in self.kumbh_events:
            evt_id = evt.get("event_id")
            if not evt_id:
                continue
            self._add_node(
                node_id=evt_id,
                node_type="EVENT",
                label=evt.get("title") or evt_id,
                attributes={
                    "event_type": evt.get("event_type"),
                    "zone_id": evt.get("zone_id"),
                    "timestamp": evt.get("timestamp"),
                    "severity": evt.get("severity"),
                },
            )

        return GraphData(
            nodes=list(self.nodes.values()),
            edges=list(self.edges.values()),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.model_dump() for n in self.nodes.values()],
            "edges": [e.model_dump() for e in self.edges.values()],
        }
