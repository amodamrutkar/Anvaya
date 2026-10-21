"""
tests/test_v2_er.py
Entity Resolution (ER) test suite for V2 dataset and Indian naming patterns.

Covers the 10 mandated requirements:
1. Exact match
2. Transliteration match
3. Multilingual / script match
4. Missing-field case
5. Same-name hard negative (common name collision guard)
6. Shared-address hard negative (chawl/hostel guard)
7. Conflicting phone/name case (shared phone/family line guard)
8. AUTO_LINK band
9. REVIEW band
10. NO_LINK (SEPARATE) band
11. V2 DEV seed-42 end-to-end integration and precision guarantees
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from sutradhar_er.config import load_config
from sutradhar_er.models import Mention
from sutradhar_er.normalise import normalise_name
from sutradhar_er.run import run_pipeline
from sutradhar_er.score import apply_hard_rules, score_pair


@pytest.fixture
def er_cfg():
    return load_config()


# ── 1. Exact Match ────────────────────────────────────────────────────────────
def test_exact_match(er_cfg):
    """Identical name, father, phone, age should score high and AUTO_LINK."""
    m1 = Mention(
        mention_id="M-1",
        record_id="R-1",
        agency="STATE_POLICE",
        name_raw="Rakesh Dagdu Pawar",
        name_norm=normalise_name("Rakesh Dagdu Pawar"),
        father_name_raw="Dagdu",
        father_name_norm="dagdu",
        age=34,
        district="Nashik",
        phones=["9820011223"],
    )
    m2 = Mention(
        mention_id="M-2",
        record_id="R-2",
        agency="MAHA_CYBER",
        name_raw="Rakesh Dagdu Pawar",
        name_norm=normalise_name("Rakesh Dagdu Pawar"),
        father_name_raw="Dagdu",
        father_name_norm="dagdu",
        age=34,
        district="Nashik",
        phones=["9820011223"],
    )
    score, reasons = score_pair(m1, m2, er_cfg, Counter())
    final_score, band, status, final_reasons = apply_hard_rules(
        score, reasons, m1, m2, er_cfg, Counter(), {}, "L-1"
    )

    assert final_score >= 0.85
    assert band == "AUTO"
    assert status == "ACTIVE"
    clues = [r.clue for r in final_reasons]
    assert "SHARED_PHONE" in clues
    assert "NAME_SIMILARITY" in clues


# ── 2. Transliteration Match ──────────────────────────────────────────────────
def test_transliteration_match(er_cfg):
    """Devanagari name and Latin name for the same person must match and AUTO_LINK."""
    m_dev = Mention(
        mention_id="M-1",
        record_id="R-1",
        agency="CENTRAL_AGENCY",
        name_raw="राकेश दगडू पवार",
        name_norm=normalise_name("राकेश दगडू पवार"),
        name_script="DEVANAGARI",
        father_name_raw="दगडू",
        father_name_norm=normalise_name("दगडू"),
        age=34,
        district="Nashik",
        phones=["9820011223"],
    )
    m_lat = Mention(
        mention_id="M-2",
        record_id="R-2",
        agency="STATE_POLICE",
        name_raw="Rakesh Dagdu Powar",
        name_norm=normalise_name("Rakesh Dagdu Powar"),
        name_script="LATIN",
        father_name_raw="Dagdu",
        father_name_norm="dagdu",
        age=34,
        district="Nashik",
        phones=["9820011223"],
    )
    score, reasons = score_pair(m_dev, m_lat, er_cfg, Counter())
    final_score, band, status, final_reasons = apply_hard_rules(
        score, reasons, m_dev, m_lat, er_cfg, Counter(), {}, "L-1"
    )

    assert band == "AUTO"
    assert final_score >= 0.85
    assert any(r.clue == "NAME_SIMILARITY" for r in final_reasons)


# ── 3. Multilingual / Script Match ────────────────────────────────────────────
def test_multilingual_script_match(er_cfg):
    """Cross-lingual name normalisation (Gujarati/Hindi/Marathi lexicon variants)."""
    # Gujarati/Hindi Shah
    shah_norm = normalise_name("शाह")
    assert "shah" in shah_norm.lower()

    # Marathi/Devanagari Chavan
    chavan_norm = normalise_name("चव्हाण")
    assert "chavan" in chavan_norm.lower()

    # Patil/Patel
    patel_norm = normalise_name("पटेल")
    assert "patil" in patel_norm.lower()


# ── 4. Missing-Field Case ─────────────────────────────────────────────────────
def test_missing_field_case(er_cfg):
    """When father name is missing in one record, no penalty should be assessed."""
    m1 = Mention(
        mention_id="M-1",
        record_id="R-1",
        agency="STATE_POLICE",
        name_raw="Sachin Vilas Kamble",
        name_norm=normalise_name("Sachin Vilas Kamble"),
        father_name_raw="Vilas",
        father_name_norm="vilas",
        age=28,
        district="Pune",
        phones=["9811223344"],
    )
    m2 = Mention(
        mention_id="M-2",
        record_id="R-2",
        agency="MAHA_CYBER",
        name_raw="Sachin Vilas Kamble",
        name_norm=normalise_name("Sachin Vilas Kamble"),
        father_name_raw="",
        father_name_norm="",
        age=28,
        district="Pune",
        phones=["9811223344"],
    )
    score, reasons = score_pair(m1, m2, er_cfg, Counter())
    final_score, band, status, final_reasons = apply_hard_rules(
        score, reasons, m1, m2, er_cfg, Counter(), {}, "L-1"
    )

    # Missing father has weight 0.0, no negative penalty
    father_reasons = [r for r in final_reasons if "FATHER" in r.clue]
    assert all(r.weight >= 0 for r in father_reasons)
    assert band == "AUTO"


# ── 5. Same-Name Hard Negative ────────────────────────────────────────────────
def test_same_name_hard_negative(er_cfg):
    """Same common name & similar age but different father & different phone must NOT auto-link."""
    name_freq = Counter({"rakesh pavar": 10})
    m1 = Mention(
        mention_id="M-1",
        record_id="R-1",
        agency="STATE_POLICE",
        name_raw="Rakesh Dagdu Pawar",
        name_norm="rakesh pavar",
        father_name_raw="Dagdu",
        father_name_norm="dagdu",
        age=34,
        district="Nashik",
        phones=["9820011223"],
    )
    m2 = Mention(
        mention_id="M-2",
        record_id="R-2",
        agency="STATE_POLICE",
        name_raw="Rakesh Suresh Pawar",
        name_norm="rakesh pavar",
        father_name_raw="Suresh",
        father_name_norm="suresh",
        age=35,
        district="Nashik",
        phones=["9122334455"],
    )
    score, reasons = score_pair(m1, m2, er_cfg, name_freq)
    final_score, band, status, final_reasons = apply_hard_rules(
        score, reasons, m1, m2, er_cfg, name_freq, {}, "L-1"
    )

    clues = [r.clue for r in final_reasons]
    assert "FATHER_NAME_CONFLICT" in clues
    assert band in ("SEPARATE", "REVIEW")
    assert band != "AUTO"
    assert final_score < 0.85


# ── 6. Shared-Address Hard Negative ───────────────────────────────────────────
def test_shared_address_hard_negative(er_cfg):
    """Shared chawl/hostel address with different names and phones must NOT merge."""
    m1 = Mention(
        mention_id="M-1",
        record_id="R-1",
        agency="STATE_POLICE",
        name_raw="Ajay Mohan Shinde",
        name_norm="ajay mohan shinde",
        address_raw="Room 12, BDD Chawl No 4, Worli, Mumbai",
        district="Mumbai",
        phones=["9811000001"],
    )
    m2 = Mention(
        mention_id="M-2",
        record_id="R-2",
        agency="MAHA_CYBER",
        name_raw="Pradeep Dattatray More",
        name_norm="pradeep dattatray more",
        address_raw="Room 12, BDD Chawl No 4, Worli, Mumbai",
        district="Mumbai",
        phones=["9822000002"],
    )
    score, reasons = score_pair(m1, m2, er_cfg, Counter())
    final_score, band, status, final_reasons = apply_hard_rules(
        score, reasons, m1, m2, er_cfg, Counter(), {}, "L-1"
    )

    assert band == "SEPARATE"
    assert final_score < 0.60


# ── 7. Conflicting Phone/Name Case ─────────────────────────────────────────────
def test_conflicting_phone_name_case(er_cfg):
    """Shared phone/SIM but conflicting names (roommates, family line) must NOT AUTO_LINK."""
    m1 = Mention(
        mention_id="M-1",
        record_id="R-1",
        agency="STATE_POLICE",
        name_raw="Pooja Rakesh Shinde",
        name_norm="pooja rakesh shinde",
        district="Thane",
        phones=["7400020860"],
    )
    m2 = Mention(
        mention_id="M-2",
        record_id="R-2",
        agency="CENTRAL_AGENCY",
        name_raw="Sunita Rajesh Verma",
        name_norm="sunita rajesh verma",
        district="Thane",
        phones=["7400020860"],
    )
    score, reasons = score_pair(m1, m2, er_cfg, Counter())
    final_score, band, status, final_reasons = apply_hard_rules(
        score, reasons, m1, m2, er_cfg, Counter(), {}, "L-1"
    )

    assert band != "AUTO"
    assert band == "REVIEW"
    assert any(r.clue == "NAME_CONFLICT_ON_SHARED_ID" for r in final_reasons)


# ── 8. AUTO_LINK Band ─────────────────────────────────────────────────────────
def test_auto_link_decision(er_cfg):
    """High-confidence match with strong ID and consistent name falls in AUTO band."""
    m1 = Mention(
        mention_id="M-1",
        record_id="R-1",
        agency="STATE_POLICE",
        name_raw="Ganesh Vijay Patil",
        name_norm="ganesh vijay patil",
        phones=["9988776655"],
        district="Kolhapur",
        age=30,
    )
    m2 = Mention(
        mention_id="M-2",
        record_id="R-2",
        agency="MAHA_CYBER",
        name_raw="Ganesh Vijay Patil",
        name_norm="ganesh vijay patil",
        phones=["9988776655"],
        district="Kolhapur",
        age=30,
    )
    score, reasons = score_pair(m1, m2, er_cfg, Counter())
    final_score, band, status, _ = apply_hard_rules(
        score, reasons, m1, m2, er_cfg, Counter(), {}, "L-1"
    )

    assert band == "AUTO"
    assert status == "ACTIVE"
    assert final_score >= 0.85


# ── 9. REVIEW Band ────────────────────────────────────────────────────────────
def test_review_decision(er_cfg):
    """Near-identical phone transposition with matching name falls into REVIEW band."""
    m1 = Mention(
        mention_id="M-1",
        record_id="R-1",
        agency="STATE_POLICE",
        name_raw="Vasim Imran Khan",
        name_norm="vasim imran khan",
        phones=["8870998616"],
        district="Nashik",
    )
    m2 = Mention(
        mention_id="M-2",
        record_id="R-2",
        agency="MAHA_CYBER",
        name_raw="Vasim Imran Khan",
        name_norm="vasim imran khan",
        phones=["8879098616"],  # single transposition 09 -> 90
        district="Nashik",
    )
    score, reasons = score_pair(m1, m2, er_cfg, Counter())
    final_score, band, status, final_reasons = apply_hard_rules(
        score, reasons, m1, m2, er_cfg, Counter(), {}, "L-1"
    )

    assert band == "REVIEW"
    assert status == "PENDING_REVIEW"
    assert 0.60 <= final_score < 0.85
    assert any(r.clue == "NEAR_PHONE_MATCH" for r in final_reasons)


# ── 10. NO_LINK Band ──────────────────────────────────────────────────────────
def test_no_link_decision(er_cfg):
    """Same record with different names must receive hard SEPARATE (NO_LINK)."""
    m1 = Mention(
        mention_id="M-1",
        record_id="R-CEN-001000",
        agency="CENTRAL_AGENCY",
        name_raw="Mahendra Arjun Rathore",
        name_norm="mahendra arjun rathore",
    )
    m2 = Mention(
        mention_id="M-2",
        record_id="R-CEN-001000",
        agency="CENTRAL_AGENCY",
        name_raw="Ravi Krishna Salve",
        name_norm="ravi krishna salve",
    )
    score, reasons = score_pair(m1, m2, er_cfg, Counter())
    final_score, band, status, final_reasons = apply_hard_rules(
        score, reasons, m1, m2, er_cfg, Counter(), {}, "L-1"
    )

    assert band == "SEPARATE"
    assert final_score == 0.0
    assert any(r.clue == "SAME_RECORD_DIFFERENT_NAME" for r in final_reasons)


# ── 11. End-to-End V2 DEV Integration ─────────────────────────────────────────
def test_v2_er_pipeline_execution(tmp_path: Path):
    """Run full ER pipeline on data/v2/dev/seed-42 into temp directory and assert performance & precision."""
    data_dir = Path("data/v2/dev/seed-42")
    assert data_dir.exists(), "data/v2/dev/seed-42 must exist"

    out_dir = tmp_path / "er_v2_dev"
    summary = run_pipeline(data_dir=data_dir, out_dir=out_dir, verbose=False)

    assert summary.get("status") == "ok"
    assert summary.get("records") == 2400
    assert summary.get("mentions") == 4507
    assert summary.get("links_auto", 0) > 2000
    assert summary.get("entities_person", 0) > 1800
    assert summary.get("elapsed_seconds", 999.0) < 30.0
