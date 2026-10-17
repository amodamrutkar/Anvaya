"""Clustering — union-find over AUTO/confirmed links, with cannot-link constraints.

Creates PERSON entities from clusters and deterministic PHONE/ACCOUNT/VEHICLE/ADDRESS entities.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Any

from .models import Entity, EntityIdentifiers, Link, Mention

logger = logging.getLogger(__name__)


# ── Union-Find ───────────────────────────────────────────────────────────────


class UnionFind:
    """Weighted union-find with path compression."""

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def find(self, x: str) -> str:
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True

    def components(self) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = defaultdict(list)
        for x in self.parent:
            groups[self.find(x)].append(x)
        return dict(groups)


# ── Clustering ───────────────────────────────────────────────────────────────


def cluster_mentions(
    mentions: list[Mention],
    links: list[Link],
    cfg: dict[str, Any],
) -> tuple[list[Entity], list[Link]]:
    """Cluster mentions into entities using union-find.

    Returns (entities, updated_links).
    Updated links may have some demoted from AUTO to REVIEW if cannot-link violated.
    """
    mention_map = {m.mention_id: m for m in mentions}

    # Build cannot-link set from:
    #  1. Same-record different-name pairs
    #  2. UNLINKED/SEPARATE status links
    cannot_link: set[tuple[str, str]] = set()
    for link in links:
        if link.status == "UNLINKED" or link.band == "SEPARATE":
            pair = tuple(sorted([link.a_mention_id, link.b_mention_id]))
            cannot_link.add(pair)

    # Also: same-record different-name
    records_mentions: dict[str, list[Mention]] = defaultdict(list)
    for m in mentions:
        records_mentions[m.record_id].append(m)
    for rec_mentions in records_mentions.values():
        for i in range(len(rec_mentions)):
            for j in range(i + 1, len(rec_mentions)):
                a, b = rec_mentions[i], rec_mentions[j]
                if a.name_norm != b.name_norm:
                    pair = tuple(sorted([a.mention_id, b.mention_id]))
                    cannot_link.add(pair)

    # Sort links by score descending for greedy merge
    mergeable_links = [lnk for lnk in links if lnk.band == "AUTO" and lnk.status == "ACTIVE"]
    mergeable_links.sort(key=lambda lnk: (-lnk.score, lnk.link_id))

    uf = UnionFind()
    # Initialize all mentions
    for m in mentions:
        uf.find(m.mention_id)

    # Merge AUTO links, checking cannot-link constraints
    demoted_links: set[str] = set()
    for link in mergeable_links:
        a_root = uf.find(link.a_mention_id)
        b_root = uf.find(link.b_mention_id)

        if a_root == b_root:
            continue  # already merged

        # Check: would this merge violate a cannot-link?
        # Get all members of both components
        a_comp = {x for x in uf.parent if uf.find(x) == a_root}
        b_comp = {x for x in uf.parent if uf.find(x) == b_root}

        violated = False
        for am in a_comp:
            for bm in b_comp:
                pair = tuple(sorted([am, bm]))
                if pair in cannot_link:
                    violated = True
                    break
            if violated:
                break

        if violated:
            # Demote to REVIEW
            link.band = "REVIEW"
            link.status = "PENDING_REVIEW"
            demoted_links.add(link.link_id)
            logger.info(f"Demoted {link.link_id} to REVIEW (cannot-link constraint)")
        else:
            uf.union(link.a_mention_id, link.b_mention_id)

    if demoted_links:
        logger.info(f"Demoted {len(demoted_links)} links from AUTO to REVIEW")

    # Build clusters
    clusters = uf.components()

    # ── Create PERSON entities ───────────────────────────────────────────
    entities: list[Entity] = []
    person_counter = 0

    # Deterministic ordering: sort cluster roots
    for root in sorted(clusters.keys()):
        member_ids = sorted(clusters[root])
        members = [mention_map[mid] for mid in member_ids if mid in mention_map]
        if not members:
            continue

        person_counter += 1
        entity_id = f"P-{person_counter:06d}"

        # Canonical name: most frequent Roman form
        name_counter: Counter = Counter()
        all_variants: set[str] = set()
        all_phones: set[str] = set()
        all_accounts: set[str] = set()
        all_vehicles: set[str] = set()
        all_record_ids: set[str] = set()
        all_agencies: set[str] = set()
        all_districts: set[str] = set()

        for m in members:
            if m.name_raw:
                all_variants.add(m.name_raw)
                # Prefer Latin names for canonical
                if m.name_script == "LATIN" and m.name_raw.strip():
                    name_counter[m.name_raw.strip()] += 1
                elif m.name_norm:
                    name_counter[m.name_norm.strip()] += 1
            for alias in m.aliases:
                if alias:
                    all_variants.add(alias)
            all_phones.update(m.phones)
            all_accounts.update(m.accounts)
            all_vehicles.update(m.vehicles)
            all_record_ids.add(m.record_id)
            all_agencies.add(m.agency)
            if m.district:
                all_districts.add(m.district)

        # If no Latin name found, use normalised form title-cased
        canonical = ""
        if name_counter:
            canonical = name_counter.most_common(1)[0][0]
        elif members[0].name_norm:
            canonical = members[0].name_norm.title()

        # Min link confidence for this cluster
        cluster_links = [
            lnk
            for lnk in links
            if lnk.band == "AUTO"
            and lnk.status == "ACTIVE"
            and (lnk.a_mention_id in member_ids or lnk.b_mention_id in member_ids)
        ]
        min_conf = min((lnk.score for lnk in cluster_links), default=None)

        entities.append(
            Entity(
                entity_id=entity_id,
                entity_type="PERSON",
                canonical_name=canonical,
                name_variants=sorted(all_variants),
                identifiers=EntityIdentifiers(
                    phones=[],  # will be linked via phone entities
                    accounts=[],
                    vehicles=[],
                ),
                mention_ids=member_ids,
                record_ids=sorted(all_record_ids),
                agencies=sorted(all_agencies),
                districts=sorted(all_districts),
                min_link_confidence=round(min_conf, 4) if min_conf is not None else None,
                status="ACTIVE",
            )
        )

    # ── Create deterministic PHONE entities ──────────────────────────────
    phone_entities: dict[str, Entity] = {}
    phone_counter = 0
    for m in sorted(mentions, key=lambda x: x.mention_id):
        for phone in sorted(m.phones):
            if phone not in phone_entities:
                phone_counter += 1
                phone_entities[phone] = Entity(
                    entity_id=f"PH-{phone_counter:06d}",
                    entity_type="PHONE",
                    canonical_name=phone,
                    name_variants=[phone],
                    identifiers=EntityIdentifiers(),
                    mention_ids=[],
                    record_ids=[],
                    agencies=[],
                    districts=[],
                    status="ACTIVE",
                )
            pe = phone_entities[phone]
            if m.mention_id not in pe.mention_ids:
                pe.mention_ids.append(m.mention_id)
            if m.record_id not in pe.record_ids:
                pe.record_ids.append(m.record_id)
            if m.agency not in pe.agencies:
                pe.agencies.append(m.agency)

    entities.extend(sorted(phone_entities.values(), key=lambda e: e.entity_id))

    # Link PERSON entities to PHONE entity IDs
    phone_id_map = {pe.canonical_name: pe.entity_id for pe in phone_entities.values()}
    for entity in entities:
        if entity.entity_type == "PERSON":
            person_phones = set()
            for mid in entity.mention_ids:
                m = mention_map.get(mid)
                if m:
                    person_phones.update(m.phones)
            entity.identifiers.phones = sorted(
                phone_id_map[p] for p in person_phones if p in phone_id_map
            )

    # ── Create deterministic ACCOUNT entities ────────────────────────────
    account_entities: dict[str, Entity] = {}
    account_counter = 0
    for m in sorted(mentions, key=lambda x: x.mention_id):
        for acc in sorted(m.accounts):
            if acc not in account_entities:
                account_counter += 1
                account_entities[acc] = Entity(
                    entity_id=f"AC-{account_counter:06d}",
                    entity_type="ACCOUNT",
                    canonical_name=acc,
                    name_variants=[acc],
                    identifiers=EntityIdentifiers(),
                    mention_ids=[],
                    record_ids=[],
                    agencies=[],
                    districts=[],
                    status="ACTIVE",
                )
            ae = account_entities[acc]
            if m.mention_id not in ae.mention_ids:
                ae.mention_ids.append(m.mention_id)
            if m.record_id not in ae.record_ids:
                ae.record_ids.append(m.record_id)
            if m.agency not in ae.agencies:
                ae.agencies.append(m.agency)

    entities.extend(sorted(account_entities.values(), key=lambda e: e.entity_id))

    # Link PERSON entities to ACCOUNT entity IDs
    account_id_map = {ae.canonical_name: ae.entity_id for ae in account_entities.values()}
    for entity in entities:
        if entity.entity_type == "PERSON":
            person_accounts = set()
            for mid in entity.mention_ids:
                m = mention_map.get(mid)
                if m:
                    person_accounts.update(m.accounts)
            entity.identifiers.accounts = sorted(
                account_id_map[a] for a in person_accounts if a in account_id_map
            )

    # ── Create deterministic VEHICLE entities ────────────────────────────
    vehicle_entities: dict[str, Entity] = {}
    vehicle_counter = 0
    for m in sorted(mentions, key=lambda x: x.mention_id):
        for veh in sorted(m.vehicles):
            if veh not in vehicle_entities:
                vehicle_counter += 1
                vehicle_entities[veh] = Entity(
                    entity_id=f"VH-{vehicle_counter:06d}",
                    entity_type="VEHICLE",
                    canonical_name=veh,
                    name_variants=[veh],
                    identifiers=EntityIdentifiers(),
                    mention_ids=[],
                    record_ids=[],
                    agencies=[],
                    districts=[],
                    status="ACTIVE",
                )
            ve = vehicle_entities[veh]
            if m.mention_id not in ve.mention_ids:
                ve.mention_ids.append(m.mention_id)
            if m.record_id not in ve.record_ids:
                ve.record_ids.append(m.record_id)
            if m.agency not in ve.agencies:
                ve.agencies.append(m.agency)

    entities.extend(sorted(vehicle_entities.values(), key=lambda e: e.entity_id))

    # Link PERSON entities to VEHICLE entity IDs
    vehicle_id_map = {ve.canonical_name: ve.entity_id for ve in vehicle_entities.values()}
    for entity in entities:
        if entity.entity_type == "PERSON":
            person_vehicles = set()
            for mid in entity.mention_ids:
                m = mention_map.get(mid)
                if m:
                    person_vehicles.update(m.vehicles)
            entity.identifiers.vehicles = sorted(
                vehicle_id_map[v] for v in person_vehicles if v in vehicle_id_map
            )

    logger.info(
        f"Clustered {len(mentions)} mentions → "
        f"{sum(1 for e in entities if e.entity_type == 'PERSON')} persons, "
        f"{len(phone_entities)} phones, {len(account_entities)} accounts, "
        f"{len(vehicle_entities)} vehicles"
    )

    return entities, links
