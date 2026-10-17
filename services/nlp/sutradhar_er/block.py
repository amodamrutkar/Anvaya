"""Blocking — generate candidate pairs without all-vs-all comparison.

Four strategies (PRD 4.3):
  1. Exact normalised phone / account / vehicle (strong keys)
  2. Phonetic surname code + first-name initial
  3. Phonetic surname + father's name phonetic
  4. District + phonetic surname + age band (±3 years)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from .models import Mention

logger = logging.getLogger(__name__)

# ── Phonetic helpers ─────────────────────────────────────────────────────────

try:
    import jellyfish

    def _metaphone(s: str) -> str:
        """Get metaphone code for a string."""
        if not s:
            return ""
        return jellyfish.metaphone(s)

    def _soundex(s: str) -> str:
        if not s:
            return ""
        return jellyfish.soundex(s)
except ImportError:
    # Fallback: just use the first 4 chars
    def _metaphone(s: str) -> str:
        return s[:4].upper() if s else ""

    def _soundex(s: str) -> str:
        return s[:4].upper() if s else ""


def _surname_token(name_norm: str) -> str:
    """Extract the last token of a normalised name as the surname."""
    tokens = name_norm.strip().split()
    return tokens[-1] if tokens else ""


def _first_initial(name_norm: str) -> str:
    """Extract first character of the first token."""
    tokens = name_norm.strip().split()
    return tokens[0][0] if tokens and tokens[0] else ""


def _age_band(age: int | None, tolerance: int = 3) -> str:
    """Map age to a band string for blocking."""
    if age is None:
        return "UNK"
    band_start = (age // tolerance) * tolerance
    return f"{band_start}-{band_start + tolerance}"


# ── Blocking strategies ─────────────────────────────────────────────────────


def generate_candidate_pairs(
    mentions: list[Mention],
    cfg: dict[str, Any],
) -> list[tuple[str, str]]:
    """Generate candidate mention-id pairs using four blocking strategies.

    Returns a deduplicated list of (mention_id_a, mention_id_b) tuples,
    always with a < b lexicographically for determinism.
    """
    max_block_size = cfg.get("blocking", {}).get("max_block_size", 200)
    age_tolerance = cfg.get("blocking", {}).get("age_band_tolerance", 3)

    # Index mentions by id
    {m.mention_id: m for m in mentions}

    # We only block PERSON-like mentions (accused, suspect, etc.)
    person_roles = {"ACCUSED", "SUSPECT", "VICTIM", "WITNESS", "COMPLAINANT", "ACCOUNT_HOLDER"}

    # Collect blocks by key
    blocks: dict[str, set[str]] = defaultdict(set)

    for m in mentions:
        if m.role not in person_roles:
            continue

        surname = _surname_token(m.name_norm)
        surname_ph = _metaphone(surname)
        first_init = _first_initial(m.name_norm)
        father_ph = _metaphone(m.father_name_norm.split()[-1]) if m.father_name_norm else ""

        # Strategy 1: Exact identifier keys
        for phone in m.phones:
            blocks[f"PH:{phone}"].add(m.mention_id)
        for account in m.accounts:
            blocks[f"AC:{account}"].add(m.mention_id)
        for vehicle in m.vehicles:
            blocks[f"VH:{vehicle}"].add(m.mention_id)

        # Strategy 2: Phonetic surname + first initial
        if surname_ph and first_init:
            blocks[f"SN-FI:{surname_ph}:{first_init}"].add(m.mention_id)

        # Strategy 3: Phonetic surname + father's name phonetic
        if surname_ph and father_ph:
            blocks[f"SN-FN:{surname_ph}:{father_ph}"].add(m.mention_id)

        # Strategy 4: District + phonetic surname + age band
        if m.district and surname_ph:
            ab = _age_band(m.age, age_tolerance)
            blocks[f"DSA:{m.district}:{surname_ph}:{ab}"].add(m.mention_id)

    # Generate pairs from blocks
    pairs: set[tuple[str, str]] = set()
    skipped_blocks = 0

    for block_key, member_ids in sorted(blocks.items()):
        if len(member_ids) > max_block_size:
            logger.warning(
                f"Skipping block '{block_key}' with {len(member_ids)} members "
                f"(exceeds max_block_size={max_block_size})"
            )
            skipped_blocks += 1
            continue

        members = sorted(member_ids)
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                # Ensure same-record pairs from different persons are included
                # (they'll be handled by the scorer's same-record rule)
                pair = (a, b) if a < b else (b, a)
                pairs.add(pair)

    logger.info(
        f"Blocking: {len(blocks)} blocks, {len(pairs)} candidate pairs, "
        f"{skipped_blocks} blocks skipped (size cap)"
    )

    return sorted(pairs)
