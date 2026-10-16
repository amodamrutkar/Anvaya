"""Rule-based scorer — deterministic, explainable scoring of mention pairs.

Produces a list of Reasons (clue, direction, weight, detail) and a total score.
Implements all hard rules from PRD 4.4.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from .models import Decision, Link, Mention, Reason

logger = logging.getLogger(__name__)

# ── String similarity ────────────────────────────────────────────────────────

try:
    from rapidfuzz.distance import JaroWinkler

    def jaro_winkler_sim(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        if a == b:
            return 1.0
        sim = JaroWinkler.similarity(a, b)
        # Indian naming pattern: first and last name match, middle name omitted or initial
        a_tokens = a.strip().split()
        b_tokens = b.strip().split()
        if len(a_tokens) >= 2 and len(b_tokens) >= 2:
            if a_tokens[0] == b_tokens[0] and a_tokens[-1] == b_tokens[-1]:
                sim = max(sim, 0.94)
            elif (a_tokens[0][0] == b_tokens[0][0]) and a_tokens[-1] == b_tokens[-1]:
                sim = max(sim, 0.92)
        return sim
except ImportError:
    # Simple fallback
    def jaro_winkler_sim(a: str, b: str) -> float:
        if a == b:
            return 1.0
        if not a or not b:
            return 0.0
        a_tokens = a.strip().split()
        b_tokens = b.strip().split()
        if (
            len(a_tokens) >= 2
            and len(b_tokens) >= 2
            and a_tokens[0] == b_tokens[0]
            and a_tokens[-1] == b_tokens[-1]
        ):
            return 0.94
        return 0.5


# ── Score one pair ───────────────────────────────────────────────────────────


def score_pair(
    a: Mention,
    b: Mention,
    cfg: dict[str, Any],
    name_freq: Counter,
) -> tuple[float, list[Reason]]:
    """Score a candidate pair (a, b).

    Returns (total_score, reasons_list).
    """
    weights = cfg.get("weights", {})
    name_cfg = cfg.get("name_similarity", {})
    jw_threshold = name_cfg.get("jaro_winkler_threshold", 0.92)

    reasons: list[Reason] = []
    has_strong_id = False

    # ── Shared phone ─────────────────────────────────────────────────────
    shared_phones = set(a.phones) & set(b.phones)
    if shared_phones:
        w = weights.get("shared_phone", 0.55)
        reasons.append(
            Reason(
                clue="SHARED_PHONE",
                direction="FOR",
                weight=w,
                detail=f"both list {', '.join(sorted(shared_phones))}",
            )
        )
        has_strong_id = True

    # ── Shared account ───────────────────────────────────────────────────
    shared_accounts = set(a.accounts) & set(b.accounts)
    if shared_accounts:
        w = weights.get("shared_account", 0.60)
        reasons.append(
            Reason(
                clue="SHARED_ACCOUNT",
                direction="FOR",
                weight=w,
                detail=f"both list {', '.join(sorted(shared_accounts))}",
            )
        )
        has_strong_id = True

    # ── Shared vehicle ───────────────────────────────────────────────────
    shared_vehicles = set(a.vehicles) & set(b.vehicles)
    if shared_vehicles:
        w = weights.get("shared_vehicle", 0.50)
        reasons.append(
            Reason(
                clue="SHARED_VEHICLE",
                direction="FOR",
                weight=w,
                detail=f"both list {', '.join(sorted(shared_vehicles))}",
            )
        )
        has_strong_id = True

    # ── Name similarity ──────────────────────────────────────────────────
    name_sim = 0.0
    if a.name_norm and b.name_norm:
        name_sim = jaro_winkler_sim(a.name_norm, b.name_norm)
        if name_sim >= jw_threshold:
            base_w = weights.get("name_similarity", 0.25)
            # Scale weight by how far above threshold
            scaled = base_w * (
                (name_sim - jw_threshold) / (1.0 - jw_threshold + 0.001) * 0.5 + 0.5
            )
            reasons.append(
                Reason(
                    clue="NAME_SIMILARITY",
                    direction="FOR",
                    weight=round(scaled, 4),
                    detail=f"{a.name_norm} vs {b.name_norm}: {name_sim:.3f}",
                )
            )

    # ── Strong ID + Name corroboration bonus (PRD 8.3) ───────────────────
    if has_strong_id and any(r.clue == "NAME_SIMILARITY" for r in reasons):
        w = weights.get("strong_id_corroboration", 0.11)
        reasons.append(
            Reason(
                clue="STRONG_ID_CORROBORATION",
                direction="FOR",
                weight=w,
                detail="strong identifier verified by near-identical name",
            )
        )

    # ── Alias match ──────────────────────────────────────────────────────
    a_all_names = {a.name_norm} | set(a.aliases)
    b_all_names = {b.name_norm} | set(b.aliases)
    alias_overlap = (a_all_names & b_all_names) - {""}
    if alias_overlap:
        w = weights.get("alias_match", 0.15)
        reasons.append(
            Reason(
                clue="ALIAS_MATCH",
                direction="FOR",
                weight=w,
                detail=f"alias overlap: {', '.join(sorted(alias_overlap))}",
            )
        )

    # ── Father's name ────────────────────────────────────────────────────
    if a.father_name_norm and b.father_name_norm:
        father_sim = jaro_winkler_sim(a.father_name_norm, b.father_name_norm)
        if father_sim >= 0.85:
            w = weights.get("father_name_match", 0.25)
            reasons.append(
                Reason(
                    clue="FATHER_NAME_MATCH",
                    direction="FOR",
                    weight=w,
                    detail=f"{a.father_name_norm} vs {b.father_name_norm}: {father_sim:.3f}",
                )
            )
        elif father_sim < 0.60:
            w = weights.get("father_name_conflict", -0.30)
            reasons.append(
                Reason(
                    clue="FATHER_NAME_CONFLICT",
                    direction="AGAINST",
                    weight=w,
                    detail=f"{a.father_name_norm} vs {b.father_name_norm}: {father_sim:.3f}",
                )
            )
    elif (a.father_name_norm and not b.father_name_norm) or (
        not a.father_name_norm and b.father_name_norm
    ):
        # One missing: no penalty, note it
        reasons.append(
            Reason(
                clue="FATHER_NAME_MISMATCH",
                direction="AGAINST",
                weight=0.0,
                detail="father's name missing in one record",
            )
        )

    # ── Age ──────────────────────────────────────────────────────────────
    if a.age is not None and b.age is not None:
        age_diff = abs(a.age - b.age)
        if age_diff <= 2:
            w = weights.get("age_within_2", 0.05)
            reasons.append(
                Reason(
                    clue="AGE_MATCH",
                    direction="FOR",
                    weight=w,
                    detail=f"age {a.age} vs {b.age} (diff={age_diff})",
                )
            )
        elif age_diff > 5:
            w = weights.get("age_differ_5", -0.20)
            reasons.append(
                Reason(
                    clue="AGE_CONFLICT",
                    direction="AGAINST",
                    weight=w,
                    detail=f"age {a.age} vs {b.age} (diff={age_diff})",
                )
            )

    # ── Same district ────────────────────────────────────────────────────
    if a.district and b.district and a.district.lower() == b.district.lower():
        w = weights.get("same_district", 0.05)
        reasons.append(
            Reason(
                clue="SAME_DISTRICT",
                direction="FOR",
                weight=w,
                detail=f"both in {a.district}",
            )
        )

    # ── Name-only penalty ────────────────────────────────────────────────
    # Different phone AND different district AND name-only match
    if not has_strong_id:
        different_phone = not shared_phones and (a.phones or b.phones)
        different_district = (
            a.district and b.district and a.district.lower() != b.district.lower()
        )
        name_only = any(r.clue == "NAME_SIMILARITY" for r in reasons)
        if name_only and (different_phone or different_district):
            w = weights.get("name_only_penalty", -0.15)
            reasons.append(
                Reason(
                    clue="NAME_ONLY_PENALTY",
                    direction="AGAINST",
                    weight=w,
                    detail="name match only with different phone/district",
                )
            )

    # ── Total score ──────────────────────────────────────────────────────
    total = sum(r.weight for r in reasons)
    total = max(0.0, min(1.0, total))  # clamp to [0, 1]

    return total, reasons


# ── Apply hard rules and decisions ──────────────────────────────────────────


def apply_hard_rules(
    score: float,
    reasons: list[Reason],
    a: Mention,
    b: Mention,
    cfg: dict[str, Any],
    name_freq: Counter,
    decisions_map: dict[str, Decision],
    link_key: str,
) -> tuple[float, str, str, list[Reason]]:
    """Apply hard rules on top of the raw score.

    Returns (final_score, band, status, reasons).
    """
    bands_cfg = cfg.get("bands", {})
    auto_threshold = bands_cfg.get("auto_threshold", 0.85)
    review_threshold = bands_cfg.get("review_threshold", 0.60)
    common_name_threshold = cfg.get("name_similarity", {}).get(
        "common_name_threshold", 5
    )

    has_strong_id = any(
        r.clue in ("SHARED_PHONE", "SHARED_ACCOUNT", "SHARED_VEHICLE")
        and r.direction == "FOR"
        for r in reasons
    )
    has_name_match = any(
        r.clue in ("NAME_SIMILARITY", "ALIAS_MATCH") and r.direction == "FOR"
        for r in reasons
    )
    has_father_match = any(
        r.clue == "FATHER_NAME_MATCH" and r.direction == "FOR" for r in reasons
    )
    same_district = any(
        r.clue == "SAME_DISTRICT" and r.direction == "FOR" for r in reasons
    )

    # Common name check
    is_common = False
    for name in (a.name_norm, b.name_norm):
        if name and name_freq.get(name, 0) > common_name_threshold:
            is_common = True

    # ── Hard rule: same record, different name → never merge ─────────────
    if a.record_id == b.record_id and a.name_norm != b.name_norm:
        return (
            0.0,
            "SEPARATE",
            "ACTIVE",
            reasons
            + [
                Reason(
                    clue="SAME_RECORD_DIFFERENT_NAME",
                    direction="AGAINST",
                    weight=-1.0,
                    detail=f"same record {a.record_id}, different names",
                )
            ],
        )

    # ── Hard rule: name-only never AUTO ──────────────────────────────────
    # AUTO requires at least one strong identifier, or name + father + same area
    if score >= auto_threshold and not has_strong_id:
        can_auto = has_name_match and has_father_match and same_district
        if not can_auto:
            # Demote to REVIEW
            score = min(score, auto_threshold - 0.01)

    # ── Hard rule: common name guard ─────────────────────────────────────
    if is_common and not has_strong_id:
        score = min(score, auto_threshold - 0.01)
        reasons = reasons + [
            Reason(
                clue="COMMON_NAME_GUARD",
                direction="AGAINST",
                weight=0.0,
                detail="common name, requires strong identifier for AUTO",
            )
        ]

    # ── Decisions: must-link / cannot-link ───────────────────────────────
    decision = decisions_map.get(link_key)
    if decision:
        if decision.decision in ("REJECT", "UNLINK"):
            return (
                0.0,
                "SEPARATE",
                "UNLINKED",
                reasons
                + [
                    Reason(
                        clue="DECISION_CANNOT_LINK",
                        direction="AGAINST",
                        weight=-1.0,
                        detail=f"rejected/unlinked by {decision.actor}: {decision.reason}",
                    )
                ],
            )
        elif decision.decision == "CONFIRM":
            return (
                max(score, auto_threshold),
                "AUTO",
                "ACTIVE",
                reasons
                + [
                    Reason(
                        clue="DECISION_MUST_LINK",
                        direction="FOR",
                        weight=0.0,
                        detail=f"confirmed by {decision.actor}: {decision.reason}",
                    )
                ],
            )

    # ── Determine band ───────────────────────────────────────────────────
    if score >= auto_threshold:
        band = "AUTO"
        status = "ACTIVE"
    elif score >= review_threshold:
        band = "REVIEW"
        status = "PENDING_REVIEW"
    else:
        band = "SEPARATE"
        status = "ACTIVE"

    return score, band, status, reasons


# ── Score all candidate pairs ────────────────────────────────────────────────


def score_all_pairs(
    candidate_pairs: list[tuple[str, str]],
    mention_map: dict[str, Mention],
    cfg: dict[str, Any],
    decisions: list[Decision] | None = None,
) -> list[Link]:
    """Score all candidate pairs, apply hard rules, return Links.

    Only keeps AUTO and REVIEW links (plus any SEPARATE with decisions).
    """
    # Build name frequency counter
    name_freq: Counter = Counter()
    for m in mention_map.values():
        if m.name_norm:
            name_freq[m.name_norm] += 1

    # Build decisions map (keyed by sorted mention pair)
    decisions_map: dict[str, Decision] = {}
    if decisions:
        for d in decisions:
            # Decisions reference link_ids; we need to map them to mention pairs
            # For now, we key by link_id (will be set during scoring)
            decisions_map[d.link_id] = d

    # Also build a reverse map from mention pairs to decisions
    # (decisions will be matched by link_id after first run)
    pair_decisions: dict[str, Decision] = {}
    if decisions:
        for d in decisions:
            pair_decisions[d.link_id] = d

    links: list[Link] = []
    link_counter = 0

    for a_id, b_id in candidate_pairs:
        a = mention_map.get(a_id)
        b = mention_map.get(b_id)
        if not a or not b:
            continue

        raw_score, reasons = score_pair(a, b, cfg, name_freq)

        link_counter += 1
        link_id = f"L-{link_counter:06d}"

        # Check if there's a decision for this pair
        pair_key = f"{a_id}|{b_id}"
        reverse_key = f"{b_id}|{a_id}"
        decision_for_pair = None
        for d in decisions or []:
            # Match decisions against the mention pair
            if hasattr(d, "_pair_key") and d._pair_key in (pair_key, reverse_key):
                decision_for_pair = d
                break

        if decision_for_pair:
            decisions_map[link_id] = decision_for_pair

        final_score, band, status, final_reasons = apply_hard_rules(
            raw_score,
            reasons,
            a,
            b,
            cfg,
            name_freq,
            decisions_map,
            link_id,
        )

        # Only keep AUTO and REVIEW links (and SEPARATE with decisions)
        keep_separate = cfg.get("output", {}).get("keep_separate_links", False)
        if band == "SEPARATE" and not keep_separate and status != "UNLINKED":
            continue

        links.append(
            Link(
                link_id=link_id,
                a_mention_id=a_id,
                b_mention_id=b_id,
                score=round(final_score, 4),
                band=band,
                reasons=final_reasons,
                explanation_text="",  # filled by explain module
                explanation_source="TEMPLATE",
                status=status,
            )
        )

    logger.info(
        f"Scored {len(candidate_pairs)} pairs → "
        f"{sum(1 for lnk in links if lnk.band == 'AUTO')} AUTO, "
        f"{sum(1 for lnk in links if lnk.band == 'REVIEW')} REVIEW, "
        f"{sum(1 for lnk in links if lnk.band == 'SEPARATE')} SEPARATE"
    )

    return links
