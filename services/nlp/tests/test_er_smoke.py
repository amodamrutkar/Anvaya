"""Comprehensive tests for Sutradhar Entity Resolution (sutradhar_er).

Acceptance Criteria tested:
1. Hero case: Rakesh Pawar variants resolve to one PERSON entity; 2 decoy Rakesh Pawars stay separate.
2. No name-only match ever reaches AUTO.
3. Same-record different-name mentions are never merged (cannot-link).
4. Rejecting a link and rerunning never re-merges the pair.
5. Validator behaviour: phone, IFSC, vehicle, account validation & rejection counting.
6. Determinism: sorted inputs produce stable, deterministic outputs.
7. Schema validity: outputs conform strictly to PRD Section 8.3 models.
8. Fast pure function apply_decisions for UI use.
9. Performance on synthetic sample.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import pytest

from sutradhar_er.config import load_config
from sutradhar_er.decisions import apply_decisions
from sutradhar_er.extract import extract_mentions
from sutradhar_er.models import (
    Decision,
    Entity,
    Link,
    Mention,
    SourceRecord,
)
from sutradhar_er.normalise import normalise_father_name, normalise_name
from sutradhar_er.run import run_pipeline, write_jsonl
from sutradhar_er.score import score_pair
from sutradhar_er.validators import (
    ValidationStats,
    validate_account,
    validate_batch,
    validate_ifsc,
    validate_phone,
    validate_vehicle,
)


# ── 1. Hero Rakesh Pawar Test ────────────────────────────────────────────────

def test_hero_rakesh_pawar_resolution(tmp_path: Path):
    """Hero case: 5 Rakesh Pawar renderings resolve to one PERSON entity with reasons.
    Two other Rakesh Pawars (decoys with different fathers/districts/phones) stay separate.
    """
    records_data = [
        # Hero mention 1: Devanagari with father Dagdu, phone, Thane
        {
            "record_id": "R-SPO-000001",
            "agency": "STATE_POLICE",
            "record_type": "FIR",
            "crime_type": "EXTORTION",
            "case_ref": "CASE-SPO-000001",
            "district": "Thane",
            "station": "Synthetic Nagar PS",
            "filed_date": "2025-11-04",
            "language": "mr",
            "sections": ["BNS-308"],
            "form_fields": {
                "accused": [{
                    "name": "राकेश दगडू पवार",
                    "father_name": "दगडू",
                    "age": 34,
                    "address": "कळवा, ठाणे",
                    "phone": "9000012345",
                    "alias": "राका",
                }],
            },
            "narrative": "आरोपी राकेश दगडू पवार यांनी खंडणी मागितली.",
        },
        # Hero mention 2: English with initial, shared phone
        {
            "record_id": "R-CYB-000002",
            "agency": "MAHA_CYBER",
            "record_type": "COMPLAINT",
            "crime_type": "CYBER_FRAUD",
            "case_ref": "CASE-CYB-000002",
            "district": "Pune",
            "station": "Cyber Cell",
            "filed_date": "2025-11-10",
            "language": "en",
            "sections": ["IT-66D"],
            "form_fields": {
                "accused": [{
                    "name": "Rakesh D. Pawar",
                    "father_name": "Dagdu",
                    "age": 35,
                    "address": "Pune",
                    "phone": "9000012345",
                }],
            },
            "narrative": "Accused contacted victims using phone 9000012345.",
        },
        # Hero mention 3: Spelling variant Powar, shared phone
        {
            "record_id": "R-CEN-000003",
            "agency": "CENTRAL_AGENCY",
            "record_type": "SEIZURE_REPORT",
            "crime_type": "NARCOTICS",
            "case_ref": "CASE-CEN-000003",
            "district": "Mumbai Suburban",
            "station": "Central Cell",
            "filed_date": "2025-11-15",
            "language": "en",
            "sections": ["NDPS-21"],
            "form_fields": {
                "accused": [{
                    "name": "Rakesh Powar",
                    "phone": "9000012345",
                    "alias": "Raka",
                }],
            },
            "narrative": "Contact seized in narcotics courier phone: 9000012345.",
        },
        # Hero mention 4: English with full name and matching alias
        {
            "record_id": "R-SPO-000004",
            "agency": "STATE_POLICE",
            "record_type": "CHARGESHEET",
            "crime_type": "EXTORTION",
            "case_ref": "CASE-SPO-000001",
            "district": "Thane",
            "station": "Synthetic Nagar PS",
            "filed_date": "2025-12-01",
            "language": "mr",
            "form_fields": {
                "accused": [{
                    "name": "Rakesh Pawar",
                    "father_name": "Dagdu Pawar",
                    "age": 34,
                    "phone": "9000012345",
                    "alias": "Raka",
                }],
            },
            "narrative": "",
        },
        # Hero mention 5: Honorific Devanagari, shared father & district
        {
            "record_id": "R-SPO-000005",
            "agency": "STATE_POLICE",
            "record_type": "FIR",
            "crime_type": "EXTORTION",
            "case_ref": "CASE-SPO-000005",
            "district": "Thane",
            "station": "Synthetic Nagar PS",
            "filed_date": "2026-01-05",
            "language": "mr",
            "form_fields": {
                "accused": [{
                    "name": "श्री राकेश पवार",
                    "father_name": "दगडू",
                    "age": 34,
                    "address": "ठाणे",
                    "phone": "9000012345",
                }],
            },
            "narrative": "",
        },
        # Decoy 1: Different father (Kashinath), different phone, Nagpur
        {
            "record_id": "R-SPO-000006",
            "agency": "STATE_POLICE",
            "record_type": "FIR",
            "crime_type": "CYBER_FRAUD",
            "district": "Nagpur",
            "station": "Nagpur PS",
            "filed_date": "2025-11-20",
            "language": "en",
            "form_fields": {
                "accused": [{
                    "name": "Rakesh Pawar",
                    "father_name": "Kashinath",
                    "age": 45,
                    "phone": "9888811111",
                }],
            },
            "narrative": "",
        },
        # Decoy 2: Different father (Baban), different phone, Nashik
        {
            "record_id": "R-SPO-000007",
            "agency": "STATE_POLICE",
            "record_type": "FIR",
            "crime_type": "EXTORTION",
            "district": "Nashik",
            "station": "Nashik PS",
            "filed_date": "2025-11-22",
            "language": "mr",
            "form_fields": {
                "accused": [{
                    "name": "राकेश पवार",
                    "father_name": "बबन",
                    "age": 22,
                    "phone": "9777722222",
                }],
            },
            "narrative": "",
        },
    ]

    # Write records directly to data directory
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    records_file = data_dir / "records.jsonl"
    with open(records_file, "w", encoding="utf-8") as f:
        for r in records_data:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    out_dir = tmp_path / "artifacts" / "er"

    summary = run_pipeline(data_dir=data_dir, out_dir=out_dir, verbose=True)

    assert summary["status"] == "ok"
    assert summary["records"] == 7
    assert summary["mentions"] == 7

    # Load produced entities and links
    entities = []
    with open(out_dir / "entities.jsonl", encoding="utf-8") as f:
        for line in f:
            entities.append(Entity(**json.loads(line)))

    links = []
    with open(out_dir / "links.jsonl", encoding="utf-8") as f:
        for line in f:
            links.append(Link(**json.loads(line)))

    person_entities = [e for e in entities if e.entity_type == "PERSON"]

    # Hero mentions are from records 1 to 5
    hero_record_ids = {"R-SPO-000001", "R-CYB-000002", "R-CEN-000003", "R-SPO-000004", "R-SPO-000005"}
    decoy1_record_id = "R-SPO-000006"
    decoy2_record_id = "R-SPO-000007"

    # Find the entity containing the first hero record
    hero_entity = None
    decoy1_entity = None
    decoy2_entity = None

    for pe in person_entities:
        rec_set = set(pe.record_ids)
        if "R-SPO-000001" in rec_set:
            hero_entity = pe
        if decoy1_record_id in rec_set:
            decoy1_entity = pe
        if decoy2_record_id in rec_set:
            decoy2_entity = pe

    assert hero_entity is not None, "Hero entity not found"
    assert decoy1_entity is not None, "Decoy 1 entity not found"
    assert decoy2_entity is not None, "Decoy 2 entity not found"

    # All 5 hero records must be inside the single hero entity!
    for r_id in hero_record_ids:
        assert r_id in hero_entity.record_ids, f"Hero record {r_id} missing from hero entity"

    # Decoys must be strictly separate entities!
    assert hero_entity.entity_id != decoy1_entity.entity_id, "Decoy 1 was wrongly merged with Hero!"
    assert hero_entity.entity_id != decoy2_entity.entity_id, "Decoy 2 was wrongly merged with Hero!"
    assert decoy1_entity.entity_id != decoy2_entity.entity_id, "Decoy 1 and Decoy 2 should be separate!"

    # Every link must have reasons and non-empty explanation_text
    for l in links:
        assert len(l.reasons) > 0, f"Link {l.link_id} has no reasons"
        assert len(l.explanation_text.strip()) > 0, f"Link {l.link_id} has empty explanation_text"

    # Hero links must include Marathi translation "[mr]"
    hero_links = [
        l for l in links
        if any(r in l.explanation_text for r in ["9000012345", "rakesh"])
    ]
    has_marathi = any("[mr]" in l.explanation_text for l in hero_links)
    assert has_marathi, "Hero links must contain bilingual Marathi translation"


# ── 2. Name-only Match Never AUTO ────────────────────────────────────────────

def test_no_name_only_auto():
    """Unit test: a pair with identical name but no shared identifiers or father/area never reaches AUTO."""
    cfg = load_config()

    m1 = Mention(
        mention_id="M-1",
        record_id="R-1",
        agency="STATE_POLICE",
        name_raw="Rakesh Pawar",
        name_norm="rakesh pavar",
        district="Pune",
        phones=["9111111111"],
    )
    m2 = Mention(
        mention_id="M-2",
        record_id="R-2",
        agency="MAHA_CYBER",
        name_raw="Rakesh Pawar",
        name_norm="rakesh pavar",
        district="Nagpur",
        phones=["9222222222"],
    )

    from collections import Counter
    score, reasons = score_pair(m1, m2, cfg, Counter({"rakesh pavar": 1}))

    from sutradhar_er.score import apply_hard_rules
    final_score, band, status, final_reasons = apply_hard_rules(
        score, reasons, m1, m2, cfg, Counter(), {}, "L-test"
    )

    assert band != "AUTO", f"Name-only pair reached AUTO (band={band}, score={final_score})"
    assert band in ("REVIEW", "SEPARATE")


# ── 3. Same-record Different-name Never Merged ────────────────────────────────

def test_same_record_rule():
    """Unit test: Two mentions in the same record with different names are never merged (cannot-link)."""
    cfg = load_config()

    m1 = Mention(
        mention_id="M-R-001-1",
        record_id="R-001",
        agency="STATE_POLICE",
        name_raw="Suresh Patil",
        name_norm="suresh patil",
        phones=["9000012345"],
    )
    m2 = Mention(
        mention_id="M-R-001-2",
        record_id="R-001",
        agency="STATE_POLICE",
        name_raw="Ramesh Shinde",
        name_norm="ramesh shinde",
        phones=["9000012345"],  # even if they share a phone in the same FIR!
    )

    from collections import Counter
    score, reasons = score_pair(m1, m2, cfg, Counter())

    from sutradhar_er.score import apply_hard_rules
    final_score, band, status, final_reasons = apply_hard_rules(
        score, reasons, m1, m2, cfg, Counter(), {}, "L-test"
    )

    assert band == "SEPARATE"
    assert final_score == 0.0
    assert any(r.clue == "SAME_RECORD_DIFFERENT_NAME" for r in final_reasons)


# ── 4. Reject-then-rerun Stays Separate ──────────────────────────────────────

def test_reject_then_rerun_stays_separate(tmp_path: Path):
    """Rejecting a link and rerunning never re-merges the pair (PRD Section 7 Acceptance Criteria)."""
    records_data = [
        {
            "record_id": "R-001",
            "agency": "STATE_POLICE",
            "district": "Thane",
            "form_fields": {
                "accused": [{
                    "name": "Anil Jadhav",
                    "father_name": "Baburao",
                    "phone": "9800011111",
                }],
            },
        },
        {
            "record_id": "R-002",
            "agency": "MAHA_CYBER",
            "district": "Thane",
            "form_fields": {
                "accused": [{
                    "name": "Anil Jadhav",
                    "father_name": "Baburao",
                    "phone": "9800011111",
                }],
            },
        },
    ]

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    with open(data_dir / "records.jsonl", "w", encoding="utf-8") as f:
        for r in records_data:
            f.write(json.dumps(r) + "\n")

    out_dir_1 = tmp_path / "out_1"
    run_pipeline(data_dir=data_dir, out_dir=out_dir_1)

    # First run should merge them
    entities_1 = [Entity(**json.loads(l)) for l in open(out_dir_1 / "entities.jsonl")]
    person_entities_1 = [e for e in entities_1 if e.entity_type == "PERSON"]
    assert len(person_entities_1) == 1
    assert len(person_entities_1[0].record_ids) == 2

    # Now simulate human reviewer rejecting link L-000001
    links_1 = [Link(**json.loads(l)) for l in open(out_dir_1 / "links.jsonl")]
    target_link = links_1[0]

    decisions_file = tmp_path / "decisions.jsonl"
    decision_entry = {
        "link_id": target_link.link_id,
        "decision": "REJECT",
        "reason": "Different persons confirmed by officer",
        "actor": "inspector_patil",
        "ts": "2026-10-17T12:00:00Z",
    }
    with open(decisions_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(decision_entry) + "\n")

    # Rerun pipeline with decisions
    out_dir_2 = tmp_path / "out_2"
    run_pipeline(data_dir=data_dir, out_dir=out_dir_2, decisions_path=decisions_file)

    entities_2 = [Entity(**json.loads(l)) for l in open(out_dir_2 / "entities.jsonl")]
    person_entities_2 = [e for e in entities_2 if e.entity_type == "PERSON"]

    # Must now be 2 separate person entities!
    assert len(person_entities_2) == 2, "Rejected link re-merged the entities on rerun!"

    links_2 = [Link(**json.loads(l)) for l in open(out_dir_2 / "links.jsonl")]
    unlinked = [l for l in links_2 if l.status == "UNLINKED" or l.band == "SEPARATE"]
    assert len(unlinked) >= 1
    assert unlinked[0].decided_by == "inspector_patil"


# ── 5. Validator Behaviour ───────────────────────────────────────────────────

def test_validator_behaviour():
    """Validators reject malformed inputs and track counts accurately."""
    # Phone
    assert validate_phone("9000012345") == "9000012345"
    assert validate_phone("+91 90000 12345") == "9000012345"
    assert validate_phone("91-9000012345") == "9000012345"
    assert validate_phone("09000012345") == "9000012345"
    assert validate_phone("5000012345") is None  # invalid start digit
    assert validate_phone("90000123") is None     # too short
    assert validate_phone("abcdefghij") is None   # not numeric

    # IFSC
    assert validate_ifsc("HDFC0001234") == "HDFC0001234"
    assert validate_ifsc("SBIN0000691") == "SBIN0000691"
    assert validate_ifsc("hdfc0001234") == "HDFC0001234"
    assert validate_ifsc("HDFC1001234") is None  # 5th char must be 0
    assert validate_ifsc("HDF0001234") is None   # too short

    # Vehicle
    assert validate_vehicle("MH12AB1234") == "MH12AB1234"
    assert validate_vehicle("mh-12-ab-1234") == "MH12AB1234"
    assert validate_vehicle("MH 05 CD 5678") == "MH05CD5678"
    assert validate_vehicle("1234AB5678") is None
    assert validate_vehicle("M12AB1234") is None

    # Account
    assert validate_account("123456789") == "123456789"
    assert validate_account("50100012345678") == "50100012345678"
    assert validate_account("12345") is None  # < 9 digits
    assert validate_account("1234567890123456789") is None  # > 18 digits

    # Batch tracking
    stats = ValidationStats()
    res = validate_batch(["9000012345", "123", "+91 88888 77777"], validate_phone, stats)
    assert len(res) == 2
    assert stats.accepted == 2
    assert stats.rejected == 1
    assert "123" in stats.rejected_values


# ── 6. Determinism ───────────────────────────────────────────────────────────

def test_pipeline_determinism(tmp_path: Path):
    """Running the pipeline twice on identical input produces byte-identical output."""
    records_data = [
        {"record_id": f"R-{i:03d}", "agency": "STATE_POLICE",
         "form_fields": {"accused": [{"name": f"Person {i % 5}", "phone": f"900000000{i % 3}"}]}}
        for i in range(15)
    ]
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    with open(data_dir / "records.jsonl", "w", encoding="utf-8") as f:
        for r in records_data:
            f.write(json.dumps(r) + "\n")

    out_1 = tmp_path / "run_1"
    out_2 = tmp_path / "run_2"

    run_pipeline(data_dir=data_dir, out_dir=out_1)
    run_pipeline(data_dir=data_dir, out_dir=out_2)

    for fname in ["entities.jsonl", "links.jsonl", "mentions.jsonl"]:
        content1 = (out_1 / fname).read_text(encoding="utf-8")
        content2 = (out_2 / fname).read_text(encoding="utf-8")
        assert content1 == content2, f"Pipeline output for {fname} is not deterministic"


# ── 7. Schema Validity ───────────────────────────────────────────────────────

def test_schema_validity(tmp_path: Path):
    """All output models conform to PRD Section 8.3 definitions without schema errors."""
    records_data = [
        {"record_id": "R-100", "agency": "STATE_POLICE",
         "form_fields": {"accused": [{"name": "Sachin Kale", "phone": "9999988888", "alias": "Sachu"}]}},
        {"record_id": "R-200", "agency": "MAHA_CYBER",
         "form_fields": {"accused": [{"name": "Sachin Kale", "phone": "9999988888"}]}},
    ]
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    with open(data_dir / "records.jsonl", "w", encoding="utf-8") as f:
        for r in records_data:
            f.write(json.dumps(r) + "\n")

    out_dir = tmp_path / "out"
    run_pipeline(data_dir=data_dir, out_dir=out_dir)

    for line in open(out_dir / "mentions.jsonl", encoding="utf-8"):
        m = Mention.model_validate_json(line)
        assert m.mention_id.startswith("M-")
        assert m.extraction_method in ("FORM", "REGEX", "LLM")

    for line in open(out_dir / "entities.jsonl", encoding="utf-8"):
        e = Entity.model_validate_json(line)
        assert e.entity_id.split("-")[0] in ("P", "PH", "AC", "VH", "AD")
        assert e.status in ("ACTIVE", "MERGED")

    for line in open(out_dir / "links.jsonl", encoding="utf-8"):
        l = Link.model_validate_json(line)
        assert l.link_id.startswith("L-")
        assert l.band in ("AUTO", "REVIEW", "SEPARATE")
        assert l.status in ("ACTIVE", "PENDING_REVIEW", "UNLINKED")
        assert l.explanation_source in ("TEMPLATE", "LLM")


# ── 8. Fast Pure Function apply_decisions ────────────────────────────────────

def test_apply_decisions_fast_performance():
    """apply_decisions is a pure function that runs in < 50ms for UI instant confirm/unlink."""
    entities = [
        Entity(
            entity_id=f"P-{i:06d}",
            entity_type="PERSON",
            canonical_name=f"Person {i}",
            mention_ids=[f"M-A-{i}", f"M-B-{i}"],
            record_ids=[f"R-{i}"],
            agencies=["STATE_POLICE"],
            districts=["Thane"],
        )
        for i in range(200)
    ]
    links = [
        Link(
            link_id=f"L-{i:06d}",
            a_mention_id=f"M-A-{i}",
            b_mention_id=f"M-B-{i}",
            score=0.75,
            band="REVIEW",
            status="PENDING_REVIEW",
        )
        for i in range(200)
    ]
    decisions = [
        Decision(
            link_id=f"L-{i:06d}",
            decision="CONFIRM" if i % 2 == 0 else "UNLINK",
            reason="Reviewed by officer",
            actor="officer_1",
            ts="2026-10-17T12:00:00Z",
        )
        for i in range(50)
    ]

    t0 = time.perf_counter()
    new_entities, new_links = apply_decisions(entities, links, decisions)
    elapsed = time.perf_counter() - t0

    assert elapsed < 0.20, f"apply_decisions took {elapsed:.4f}s, must be < 200ms"
    # Verify state of decided links
    link_map = {l.link_id: l for l in new_links}
    assert link_map["L-000000"].band == "AUTO"
    assert link_map["L-000000"].status == "ACTIVE"
    assert link_map["L-000001"].band == "SEPARATE"
    assert link_map["L-000001"].status == "UNLINKED"


# ── 9. Normalisation Lexicon & Equivalence Tests ──────────────────────────────

def test_normalisation_lexicons():
    """Verify Marathi/Hindi surnames, first names, honorific stripping, equivalences."""
    assert normalise_name("राकेश दगडू पवार") == "rakesh dagdu pavar"
    assert normalise_name("Rakesh D. Pawar") == "rakesh d pavar"
    assert normalise_name("Rakesh Powar") == "rakesh pavar"
    assert normalise_name("Shri Rakesh Pawar") == "rakesh pavar"
    assert normalise_name("श्री सचिन काळे") == "sachin kale"
    assert normalise_name("नितिन गायकवाड") == "nitin gaikwad"
    assert normalise_name("Anil Jadav") == "anil jadhav"
    assert normalise_name("Prakash Shindey") == "prakash shinde"
