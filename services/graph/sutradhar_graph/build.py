"""
Graph Builder for Sutradhar.

Ingests agency records, accounts, transactions, and ER clusters to construct
a multi-modal heterogeneous intelligence graph with STRONG/WEAK strength flags,
evidence trails, and confidence values per edge.
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
        self._edge_counter = 0

        # Raw records & data
        self.records: list[dict[str, Any]] = []
        self.accounts: list[dict[str, Any]] = []
        self.transactions: list[dict[str, Any]] = []

        # Entity resolution mapping: mention_id -> entity_id
        self.mention_to_entity: dict[str, str] = {}
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
            # Merge attributes if needed
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
        attributes: dict[str, Any] | None = None,
    ) -> EdgeModel:
        ev_list = sorted(list(set(evidence or [])))
        edge_key = f"{source}::{edge_type}::{target}"

        # If edge already exists between these two with same type, merge evidence
        for existing in self.edges.values():
            if (
                existing.source == source
                and existing.target == target
                and existing.type == edge_type
            ):
                combined_ev = sorted(list(set(existing.evidence + ev_list)))
                existing.evidence = combined_ev
                if strength == "STRONG":
                    existing.strength = "STRONG"
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
            attributes=attributes or {},
        )
        self.edges[edge_id] = edge
        self.nx_graph.add_edge(
            source,
            target,
            key=edge_id,
            id=edge_id,
            type=edge_type,
            strength=strength,
            evidence=ev_list,
            confidence=confidence,
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

        # 3. Load ER clusters if available
        er_entities_file = self.er_dir / "entities.jsonl" if self.er_dir else None
        if er_entities_file and er_entities_file.exists():
            entities = _read_jsonl(er_entities_file)
            for ent in entities:
                ent_id = ent.get("entity_id") or f"ENT-{len(self.entity_to_name) + 1:04d}"
                cname = ent.get("canonical_name", "Unknown")
                mids = ent.get("mention_ids", [])
                self.entity_to_name[ent_id] = cname
                self.entity_to_mentions[ent_id] = mids
                for mid in mids:
                    self.mention_to_entity[mid] = ent_id
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

                # Match by phone first, then name
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
                name = acc.get("name", "Unknown Accused")
                mid = f"M-{rid}-{name}"
                person_id = self.mention_to_entity.get(mid) or f"ENT-{len(self.nodes) + 1:04d}"
                canonical_name = self.entity_to_name.get(person_id, name)

                # PERSON Node
                self._add_node(
                    node_id=person_id,
                    node_type="PERSON",
                    label=canonical_name,
                    attributes={"district": district, "roles": ["ACCUSED"]},
                )
                accused_entities.append(person_id)

                # Person -> ACCUSED_IN -> Case
                self._add_edge(
                    source=person_id,
                    target=case_ref,
                    edge_type="ACCUSED_IN",
                    strength="STRONG",
                    evidence=[rid],
                )

                # Phone
                phone = acc.get("phone")
                if phone:
                    phone_node_id = f"PHONE:{phone}"
                    self._add_node(phone_node_id, "PHONE", phone)
                    self._add_edge(
                        person_id, phone_node_id, "USES", strength="STRONG", evidence=[rid]
                    )

                # Address (WEAK edge by default per PRD 4.1)
                address = acc.get("address")
                if address and len(address.strip()) > 3:
                    addr_node_id = f"ADDRESS:{address.strip()}"
                    self._add_node(
                        addr_node_id, "ADDRESS", address.strip(), attributes={"district": district}
                    )
                    self._add_edge(
                        person_id, addr_node_id, "LIVES_AT", strength="WEAK", evidence=[rid]
                    )

            # Co-accused edges (STRONG)
            for i in range(len(accused_entities)):
                for j in range(i + 1, len(accused_entities)):
                    p1, p2 = accused_entities[i], accused_entities[j]
                    self._add_edge(p1, p2, "CO_ACCUSED_WITH", strength="STRONG", evidence=[rid])
                    self._add_edge(p2, p1, "CO_ACCUSED_WITH", strength="STRONG", evidence=[rid])

            # Complainant / Victims
            comp = ff.get("complainant", {})
            if isinstance(comp, dict) and comp.get("name"):
                comp_name = comp["name"]
                comp_mid = f"M-COMP-{rid}-{comp_name}"
                comp_id = (
                    self.mention_to_entity.get(comp_mid)
                    or f"ENT-COMP-{comp_name.replace(' ', '_')}"
                )
                self._add_node(comp_id, "PERSON", comp_name, attributes={"roles": ["VICTIM"]})
                self._add_edge(comp_id, case_ref, "VICTIM_IN", strength="STRONG", evidence=[rid])

            # Accounts attached to record
            for acct in ff.get("accounts", []):
                bank = acct.get("bank", "BANK")
                acct_no = acct.get("account_no", "")
                if acct_no:
                    acct_key = f"{bank}:{acct_no}"
                    acct_node_id = f"ACCOUNT:{acct_key}"
                    self._add_node(acct_node_id, "ACCOUNT", acct_key, attributes={"bank": bank})
                    # Link accused to account
                    for p in accused_entities:
                        self._add_edge(p, acct_node_id, "OWNS", strength="STRONG", evidence=[rid])

            # Vehicles attached to record
            for veh in ff.get("vehicles", []):
                if veh and veh != "N/A":
                    veh_node_id = f"VEHICLE:{veh}"
                    self._add_node(veh_node_id, "VEHICLE", veh)
                    for p in accused_entities:
                        self._add_edge(p, veh_node_id, "OWNS", strength="STRONG", evidence=[rid])

        # Step B: Accounts & Transactions (from MAHA_CYBER)
        for acct in self.accounts:
            ak = acct.get("account_key")
            if not ak:
                continue
            acct_node_id = f"ACCOUNT:{ak}"
            self._add_node(
                acct_node_id,
                "ACCOUNT",
                ak,
                attributes={
                    "bank": acct.get("bank"),
                    "ifsc": acct.get("ifsc"),
                    "holder_name": acct.get("holder_name_raw"),
                    "complaint_count": acct.get("complaint_count", 0),
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
                self._add_edge(
                    source=src_node,
                    target=dst_node,
                    edge_type="TRANSFERRED_TO",
                    strength="STRONG",
                    confidence=1.0,
                    attributes={
                        "amount": txn.get("amount", 0),
                        "ts": txn.get("ts"),
                        "channel": txn.get("channel", "UPI"),
                        "txn_id": txn.get("txn_id"),
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
