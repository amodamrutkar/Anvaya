"""Extraction — read form_fields and narrative into Mentions.

Extraction methods:
  FORM  — structured form_fields (highest confidence)
  REGEX — regex/lexicon extraction from narrative text
  LLM   — optional LLM extraction (off by default)
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from .models import Mention, SourceRecord
from .normalise import (
    detect_script,
    expand_aliases,
    normalise_father_name,
    normalise_name,
)
from .validators import (
    ValidationStats,
    validate_account,
    validate_batch,
    validate_phone,
    validate_vehicle,
)

logger = logging.getLogger(__name__)


# ── Narrative regex cues ─────────────────────────────────────────────────────

# Cues in Marathi, Hindi, English for accused/suspect names
_NAME_CUES = re.compile(
    r"(?:आरोपी|संशयित|accused|suspect|s/o|son of|w/o|wife of|d/o|daughter of"
    r"|नावाचा|नावाची|नामक|named|namely)\s*[:—–-]?\s*"
    r"([^\n,।\.]{3,60})",
    re.IGNORECASE | re.UNICODE,
)

# Phone patterns in narrative
_PHONE_NARRATIVE = re.compile(
    r"(?:phone|mobile|mob|contact|दूरध्वनी|मोबाईल|फोन)\s*[:—–-]?\s*"
    r"\+?(?:91)?[\s-]*([6-9]\d[\s-]?\d{4}[\s-]?\d{4})",
    re.IGNORECASE,
)

# Account patterns
_ACCOUNT_NARRATIVE = re.compile(
    r"(?:account|a/c|खाते|खाता)\s*(?:no|number|क्र)?[:—–.\s]*(\d{9,18})",
    re.IGNORECASE,
)

# Vehicle patterns
_VEHICLE_NARRATIVE = re.compile(
    r"\b([A-Z]{2}[\s-]?\d{2}[\s-]?[A-Z]{1,3}[\s-]?\d{4})\b",
    re.IGNORECASE,
)


# ── Form field extraction ───────────────────────────────────────────────────


def _extract_from_form_fields(
    record: SourceRecord,
    mention_counter: list[int],
    phone_stats: ValidationStats,
    vehicle_stats: ValidationStats,
    account_stats: ValidationStats,
) -> list[Mention]:
    """Extract mentions from structured form_fields (PRD X1)."""
    mentions: list[Mention] = []
    form = record.form_fields
    if not form:
        return mentions

    # Accused persons
    accused_list = form.get("accused", [])
    if isinstance(accused_list, dict):
        accused_list = [accused_list]

    for acc in accused_list:
        if not isinstance(acc, dict):
            continue
        name_raw = acc.get("name", "")
        if not name_raw:
            continue

        mention_counter[0] += 1
        mid = f"M-{record.record_id}-{mention_counter[0]}"

        raw_phones = []
        if acc.get("phone"):
            raw_phones.append(str(acc["phone"]))
        valid_phones = validate_batch(raw_phones, validate_phone, phone_stats)

        raw_vehicles: list[str] = []
        valid_vehicles = validate_batch(raw_vehicles, validate_vehicle, vehicle_stats)

        raw_aliases = []
        alias_raw = acc.get("alias", "")
        if alias_raw:
            raw_aliases = expand_aliases(str(alias_raw))

        mentions.append(
            Mention(
                mention_id=mid,
                record_id=record.record_id,
                agency=record.agency,
                role="ACCUSED",
                name_raw=name_raw,
                name_norm=normalise_name(name_raw),
                name_script=detect_script(name_raw),
                father_name_raw=acc.get("father_name", ""),
                father_name_norm=normalise_father_name(acc.get("father_name", "")),
                age=acc.get("age"),
                address_raw=acc.get("address", ""),
                district=record.district or acc.get("district", ""),
                phones=valid_phones,
                accounts=[],
                vehicles=valid_vehicles,
                aliases=raw_aliases,
                extraction_method="FORM",
                extraction_confidence=0.99,
            )
        )

    # Complainant
    complainant = form.get("complainant")
    if isinstance(complainant, dict) and complainant.get("name"):
        mention_counter[0] += 1
        mid = f"M-{record.record_id}-{mention_counter[0]}"
        raw_phones = []
        if complainant.get("phone"):
            raw_phones.append(str(complainant["phone"]))
        valid_phones = validate_batch(raw_phones, validate_phone, phone_stats)

        mentions.append(
            Mention(
                mention_id=mid,
                record_id=record.record_id,
                agency=record.agency,
                role="COMPLAINANT",
                name_raw=complainant["name"],
                name_norm=normalise_name(complainant["name"]),
                name_script=detect_script(complainant["name"]),
                father_name_raw=complainant.get("father_name", ""),
                father_name_norm=normalise_father_name(
                    complainant.get("father_name", "")
                ),
                age=complainant.get("age"),
                address_raw=complainant.get("address", ""),
                district=record.district,
                phones=valid_phones,
                accounts=[],
                vehicles=[],
                aliases=[],
                extraction_method="FORM",
                extraction_confidence=0.99,
            )
        )

    # Record-level phones (attach to all accused in this record as extra identifiers)
    record_phones = form.get("phones", [])
    if record_phones:
        valid_record_phones = validate_batch(
            [str(p) for p in record_phones], validate_phone, phone_stats
        )
        for m in mentions:
            if m.role == "ACCUSED":
                for p in valid_record_phones:
                    if p not in m.phones:
                        m.phones.append(p)

    # Record-level vehicles
    record_vehicles = form.get("vehicles", [])
    if record_vehicles:
        valid_record_vehicles = validate_batch(
            [str(v) for v in record_vehicles], validate_vehicle, vehicle_stats
        )
        for m in mentions:
            if m.role == "ACCUSED":
                for v in valid_record_vehicles:
                    if v not in m.vehicles:
                        m.vehicles.append(v)

    # Record-level accounts
    record_accounts = form.get("accounts", [])
    if record_accounts:
        for acc_entry in record_accounts:
            if isinstance(acc_entry, dict):
                acc_no = acc_entry.get("account_no", "")
                if acc_no:
                    valid = validate_account(str(acc_no))
                    if valid:
                        for m in mentions:
                            if m.role == "ACCUSED" and valid not in m.accounts:
                                m.accounts.append(valid)
                    else:
                        account_stats.rejected += 1
                        account_stats.rejected_values.append(str(acc_no))

    return mentions


# ── Narrative regex extraction ───────────────────────────────────────────────


def _extract_from_narrative(
    record: SourceRecord,
    mention_counter: list[int],
    phone_stats: ValidationStats,
    vehicle_stats: ValidationStats,
    account_stats: ValidationStats,
) -> list[Mention]:
    """Extract mentions from narrative text using regex/lexicon (PRD X2)."""
    mentions: list[Mention] = []
    narrative = record.narrative
    if not narrative or not narrative.strip():
        return mentions

    # Extract phones
    phones_found: list[str] = []
    for m in _PHONE_NARRATIVE.finditer(narrative):
        raw = re.sub(r"[\s\-]", "", m.group(1))
        valid = validate_phone(raw)
        if valid:
            phones_found.append(valid)
            phone_stats.accepted += 1
        else:
            phone_stats.rejected += 1
            phone_stats.rejected_values.append(raw)

    # Extract accounts
    accounts_found: list[str] = []
    for m in _ACCOUNT_NARRATIVE.finditer(narrative):
        raw = m.group(1)
        valid = validate_account(raw)
        if valid:
            accounts_found.append(valid)
            account_stats.accepted += 1
        else:
            account_stats.rejected += 1
            account_stats.rejected_values.append(raw)

    # Extract vehicles
    vehicles_found: list[str] = []
    for m in _VEHICLE_NARRATIVE.finditer(narrative):
        raw = re.sub(r"[\s\-]", "", m.group(1)).upper()
        valid = validate_vehicle(raw)
        if valid:
            vehicles_found.append(valid)
            vehicle_stats.accepted += 1
        else:
            vehicle_stats.rejected += 1
            vehicle_stats.rejected_values.append(raw)

    # Narrative stop words indicating continuation of sentence rather than name
    stop_words = {
        "यांनी",
        "याने",
        "यांच्या",
        "यावर",
        "आहे",
        "होता",
        "केली",
        "मागितली",
        "केले",
        "दाखल",
        "contacted",
        "victims",
        "victim",
        "police",
        "station",
        "officer",
        "using",
        "phone",
        "account",
        "dated",
        "arrested",
        "seized",
        "reported",
        "alleged",
        "stated",
        "विरुद्ध",
    }

    # Extract names (accused/suspect cues)
    for m in _NAME_CUES.finditer(narrative):
        raw_text = m.group(1).strip()
        tokens = raw_text.split()
        clean_tokens = []
        for t in tokens:
            if t.lower().rstrip(".,;।") in stop_words:
                break
            clean_tokens.append(t)
        name_raw = " ".join(clean_tokens).strip()

        # Skip if empty, too short, or all digits
        if not name_raw or len(name_raw) < 3 or re.match(r"^\d+$", name_raw):
            continue

        mention_counter[0] += 1
        mid = f"M-{record.record_id}-{mention_counter[0]}"

        mentions.append(
            Mention(
                mention_id=mid,
                record_id=record.record_id,
                agency=record.agency,
                role="ACCUSED",
                name_raw=name_raw,
                name_norm=normalise_name(name_raw),
                name_script=detect_script(name_raw),
                father_name_raw="",
                father_name_norm="",
                age=None,
                address_raw="",
                district=record.district,
                phones=phones_found[:],
                accounts=accounts_found[:],
                vehicles=vehicles_found[:],
                aliases=[],
                extraction_method="REGEX",
                extraction_confidence=0.70,
            )
        )

    return mentions


# ── LLM extraction (optional, behind LLM_PROVIDER) ──────────────────────────


def _extract_with_llm(
    record: SourceRecord,
    mention_counter: list[int],
    cache_path: Path | None = None,
) -> list[Mention]:
    """Optional LLM extraction. Only runs if LLM_PROVIDER != 'none'.

    Cached to disk so repeated runs don't call the API.
    Never used for identity resolution — only for extraction.
    """
    provider = os.environ.get("LLM_PROVIDER", "none").lower()
    if provider == "none":
        return []

    # Check cache
    cache: dict[str, Any] = {}
    if cache_path and cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    cache[entry.get("record_id", "")] = entry

    if record.record_id in cache:
        # Return cached mentions
        cached = cache[record.record_id]
        mentions = []
        for cm in cached.get("mentions", []):
            mention_counter[0] += 1
            mid = f"M-{record.record_id}-{mention_counter[0]}"
            mentions.append(
                Mention(
                    mention_id=mid,
                    record_id=record.record_id,
                    agency=record.agency,
                    role=cm.get("role", "ACCUSED"),
                    name_raw=cm.get("name_raw", ""),
                    name_norm=normalise_name(cm.get("name_raw", "")),
                    name_script=detect_script(cm.get("name_raw", "")),
                    extraction_method="LLM",
                    extraction_confidence=0.80,
                    district=record.district,
                )
            )
        return mentions

    # Actual LLM call would go here — stubbed for now
    logger.info(
        f"LLM extraction not implemented for provider={provider}, record={record.record_id}"
    )
    return []


# ── Main extraction function ────────────────────────────────────────────────


def extract_mentions(
    records: list[SourceRecord],
    cfg: dict[str, Any],
    cache_path: Path | None = None,
) -> tuple[list[Mention], dict[str, ValidationStats]]:
    """Extract all mentions from source records.

    Returns (mentions, validation_stats).
    """
    all_mentions: list[Mention] = []
    mention_counter = [0]  # mutable counter shared across records

    phone_stats = ValidationStats()
    vehicle_stats = ValidationStats()
    account_stats = ValidationStats()

    for record in sorted(records, key=lambda r: r.record_id):
        # FORM extraction (highest priority)
        form_mentions = _extract_from_form_fields(
            record, mention_counter, phone_stats, vehicle_stats, account_stats
        )
        all_mentions.extend(form_mentions)

        # REGEX extraction from narrative
        regex_mentions = _extract_from_narrative(
            record, mention_counter, phone_stats, vehicle_stats, account_stats
        )
        # Deduplicate: skip regex mentions that closely match a form mention
        existing_norms = {m.name_norm for m in form_mentions if m.name_norm}
        for rm in regex_mentions:
            if rm.name_norm and rm.name_norm not in existing_norms:
                all_mentions.append(rm)
                existing_norms.add(rm.name_norm)

        # Optional LLM extraction
        llm_mentions = _extract_with_llm(record, mention_counter, cache_path)
        existing_norms_all = {
            m.name_norm for m in all_mentions if m.record_id == record.record_id
        }
        for lm in llm_mentions:
            if lm.name_norm and lm.name_norm not in existing_norms_all:
                all_mentions.append(lm)

    stats = {
        "phone": phone_stats,
        "vehicle": vehicle_stats,
        "account": account_stats,
    }

    logger.info(
        f"Extracted {len(all_mentions)} mentions from {len(records)} records. "
        f"Phones: {phone_stats.accepted} ok / {phone_stats.rejected} rejected. "
        f"Vehicles: {vehicle_stats.accepted} ok / {vehicle_stats.rejected} rejected. "
        f"Accounts: {account_stats.accepted} ok / {account_stats.rejected} rejected."
    )

    return all_mentions, stats


# ── Load records from disk ───────────────────────────────────────────────────


def load_records(data_dir: Path) -> list[SourceRecord]:
    """Load source records from data/<version>/<AGENCY>/records.jsonl or directly."""
    records: list[SourceRecord] = []
    data_dir = Path(data_dir)
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        return records

    candidate_files = []
    agencies = ["STATE_POLICE", "MAHA_CYBER", "CENTRAL_AGENCY"]
    for agency in agencies:
        f = data_dir / agency / "records.jsonl"
        if f.exists() and f.is_file():
            candidate_files.append(f)

    direct_file = data_dir / "records.jsonl"
    if direct_file.exists() and direct_file not in candidate_files:
        candidate_files.append(direct_file)

    if not candidate_files:
        candidate_files = list(data_dir.rglob("records.jsonl"))

    for records_file in sorted(candidate_files):
        with open(records_file, encoding="utf-8") as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    records.append(SourceRecord(**data))
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Skipping line {line_num} in {records_file}: {e}")

    logger.info(f"Loaded {len(records)} records from {data_dir}")
    return records
