"""
tests/test_v2_data_gen.py
Regression and contract tests for Sutradhar Dataset v2 (Dev tier):
1. Test v1 immutability (v1 files must remain strictly byte-identical to pinned checksums)
2. Test schema compliance of v2 dev records, accounts, transactions, and Kumbh events against contracts/schemas/
3. Test determinism: same seed run twice produces byte-identical checksums
4. Test seed sensitivity: seed 42 vs seed 99 produces distinct outputs
5. Test safety guarantees: 100% of pseudo-Aadhaar numbers fail Verhoeff algorithm
6. Test safety guarantees: zero denylist prominent figures in generated population
7. Test target difficulty mix: ~50% Easy / ~30% Medium / ~20% Hard
8. Test hero scenario preservation: canonical IDs P-000045, PH-000007, AC-000310, KUMBH-EVT-0001..0003 present
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import jsonschema
import pytest

from sutradhar_data.generate import generate_dataset
from sutradhar_data.safety import (
    validate_pseudo_aadhaar_fails_verhoeff,
    check_name_denylist,
)


V1_PINNED_CHECKSUMS = {
    "data/v1/CENTRAL_AGENCY/records.jsonl": "1e56f38d39911ca39fe2920d809c057aea8e6391dcff95deb44e11ce9624c402",
    "data/v1/MAHA_CYBER/records.jsonl": "1cd70f054a379d30abbb613b97c22689e60ad55da2367531ece23a9f4c396de7",
    "data/v1/MAHA_CYBER/accounts.jsonl": "ae03afdef8f2447c1c14ee427b77eca313b6904afc516493179da94ac39ed513",
    "data/v1/MAHA_CYBER/transactions.jsonl": "13423b61fca81a17b380b1812c00acf5ba424d587a7a77cb76ccfc2788db66d4",
    "data/v1/STATE_POLICE/records.jsonl": "0e1a5924b7ee838b6e526e035a07599b6a4dd58bb3c3ed78a4f8e41598e45159",
    "data/kumbh/events.jsonl": "c502d61c6852df4de8d54f4a3436b59c0b869101d737a9dc0150d6b19e1ed047",
}


def _sha256(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ─────────────────────────────────────────────────────────────
# 1. v1 Immutability Test
# ─────────────────────────────────────────────────────────────
def test_v1_files_remain_byte_identical():
    """Verify that all committed v1 dataset files match their exact SHA-256 baseline checksums."""
    for filepath, expected_hash in V1_PINNED_CHECKSUMS.items():
        p = Path(filepath)
        assert p.exists(), f"v1 file missing: {filepath}"
        actual_hash = _sha256(p)
        assert actual_hash == expected_hash, f"v1 file mutated: {filepath}"


# ─────────────────────────────────────────────────────────────
# 2. Schema Validation Tests
# ─────────────────────────────────────────────────────────────
def test_v2_records_conform_to_schema():
    """Validate all generated records against contracts/schemas/source_record.schema.json."""
    schema_path = Path("contracts/schemas/source_record.schema.json")
    assert schema_path.exists()
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    for agency in ["STATE_POLICE", "MAHA_CYBER", "CENTRAL_AGENCY"]:
        records_file = Path("data/v2/dev/seed-42") / agency / "records.jsonl"
        assert records_file.exists(), f"Missing records for {agency}"

        count = 0
        with open(records_file, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                jsonschema.validate(rec, schema)
                count += 1
        assert count > 0, f"No records in {agency}"


def test_v2_kumbh_events_conform_to_schema():
    """Validate all generated Kumbh events against contracts/schemas/kumbh_event.schema.json."""
    schema_path = Path("contracts/schemas/kumbh_event.schema.json")
    assert schema_path.exists()
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    events_file = Path("data/v2/dev/seed-42/kumbh/events.jsonl")
    assert events_file.exists()

    count = 0
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            evt = json.loads(line)
            jsonschema.validate(evt, schema)
            count += 1
    assert count == 300, f"Expected 300 Kumbh events, found {count}"


# ─────────────────────────────────────────────────────────────
# 3. Determinism and Seeding Tests
# ─────────────────────────────────────────────────────────────
def test_v2_generation_determinism(tmp_path: Path):
    """Verify that running generation with the same seed in two temp dirs produces identical files."""
    run1 = tmp_path / "run1"
    run2 = tmp_path / "run2"

    generate_dataset(version="v2", tier="dev", seed=42, out_dir=str(run1))
    generate_dataset(version="v2", tier="dev", seed=42, out_dir=str(run2))

    check_files = [
        "v2/dev/seed-42/STATE_POLICE/records.jsonl",
        "v2/dev/seed-42/MAHA_CYBER/records.jsonl",
        "v2/dev/seed-42/CENTRAL_AGENCY/records.jsonl",
        "v2/dev/seed-42/MAHA_CYBER/accounts.jsonl",
        "v2/dev/seed-42/MAHA_CYBER/transactions.jsonl",
        "v2/dev/seed-42/kumbh/events.jsonl",
        "truth/v2/dev/seed-42/mention_truth.jsonl",
        "truth/v2/dev/seed-42/person_truth.jsonl",
    ]

    for rel_path in check_files:
        f1 = run1 / rel_path
        f2 = run2 / rel_path
        assert f1.exists() and f2.exists(), f"File {rel_path} missing in output"
        assert _sha256(f1) == _sha256(f2), f"Non-deterministic generation for {rel_path}"


def test_v2_seed_variance(tmp_path: Path):
    """Verify that seed 42 and seed 99 produce distinct datasets."""
    run_a = tmp_path / "seed42"
    run_b = tmp_path / "seed99"

    generate_dataset(version="v2", tier="dev", seed=42, out_dir=str(run_a))
    generate_dataset(version="v2", tier="dev", seed=99, out_dir=str(run_b))

    fa = run_a / "v2/dev/seed-42/STATE_POLICE/records.jsonl"
    fb = run_b / "v2/dev/seed-99/STATE_POLICE/records.jsonl"
    assert fa.exists() and fb.exists()
    assert _sha256(fa) != _sha256(fb), "Different seeds must produce different records"


# ─────────────────────────────────────────────────────────────
# 4. Safety Guarantees Tests
# ─────────────────────────────────────────────────────────────
def test_pseudo_aadhaar_strictly_fails_verhoeff():
    """Verify that 100% of generated pseudo-Aadhaar numbers fail the Verhoeff checksum algorithm."""
    person_truth_file = Path("data/truth/v2/dev/seed-42/person_truth.jsonl")
    assert person_truth_file.exists()

    count = 0
    with open(person_truth_file, "r", encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            for aadhaar in p.get("pseudo_aadhaar", []):
                count += 1
                assert validate_pseudo_aadhaar_fails_verhoeff(aadhaar), (
                    f"Aadhaar {aadhaar} passed Verhoeff algorithm unexpectedly!"
                )
    assert count > 1000, f"Expected >1000 pseudo-Aadhaars, tested {count}"


def test_zero_prominent_figure_denylist_collisions():
    """Verify that no prominent political or criminal figures appear in the generated population."""
    person_truth_file = Path("data/truth/v2/dev/seed-42/person_truth.jsonl")
    assert person_truth_file.exists()

    with open(person_truth_file, "r", encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            name = p.get("canonical_name", "")
            assert check_name_denylist(name), f"Denylisted figure collision found: {name}"


# ─────────────────────────────────────────────────────────────
# 5. Hero Scenario & Syndicate Topology Tests
# ─────────────────────────────────────────────────────────────
def test_hero_scenarios_preserved_in_v2():
    """Verify that canonical hero IDs and properties are preserved in v2 dev."""
    # Check Rakesh Dagdu Pawar
    person_truth_file = Path("data/truth/v2/dev/seed-42/person_truth.jsonl")
    persons = {}
    with open(person_truth_file, "r", encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            persons[p["person_id"]] = p

    assert "P-000045" in persons
    rakesh = persons["P-000045"]
    assert rakesh["canonical_name"] == "Rakesh Dagdu Pawar"
    assert "PH-000007" in rakesh["phones"]

    # Check Nitin Gaikwad
    assert "P-000046" in persons
    nitin = persons["P-000046"]
    assert nitin["canonical_name"] == "Nitin Shankar Gaikwad"
    assert "PH-000008" in nitin["phones"]

    # Check Deceived account AC-000310 in accounts.jsonl
    accounts_file = Path("data/v2/dev/seed-42/MAHA_CYBER/accounts.jsonl")
    accounts = {}
    with open(accounts_file, "r", encoding="utf-8") as f:
        for line in f:
            a = json.loads(line)
            accounts[a["account_key"]] = a

    assert "BARB:54004320985996" in accounts

    # Check Kumbh events
    events_file = Path("data/v2/dev/seed-42/kumbh/events.jsonl")
    events = {}
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            events[e["event_id"]] = e

    assert "KUMBATHON" not in str(events)
    assert "KUMBH-EVT-0001" in events
    assert "KUMBH-EVT-0002" in events
    assert "KUMBH-EVT-0003" in events
    # Control event zone is Trimbakeshwar
    assert events["KUMBH-EVT-0003"]["zone"] == "Trimbakeshwar"


def test_v2_difficulty_mix_calibration():
    """Verify that achieved difficulty mix is calibrated to ~50% Easy / ~30% Medium / ~20% Hard."""
    mention_truth_file = Path("data/truth/v2/dev/seed-42/mention_truth.jsonl")
    assert mention_truth_file.exists()

    diff_counts = {"EASY": 0, "MEDIUM": 0, "HARD": 0}
    total = 0
    with open(mention_truth_file, "r", encoding="utf-8") as f:
        for line in f:
            m = json.loads(line)
            d = m.get("difficulty")
            if d in diff_counts:
                diff_counts[d] += 1
                total += 1

    easy_pct = diff_counts["EASY"] / total
    med_pct = diff_counts["MEDIUM"] / total
    hard_pct = diff_counts["HARD"] / total

    assert 0.40 <= easy_pct <= 0.55, f"Easy percentage out of expected range: {easy_pct:.3f}"
    assert 0.25 <= med_pct <= 0.38, f"Medium percentage out of expected range: {med_pct:.3f}"
    assert 0.17 <= hard_pct <= 0.28, f"Hard percentage out of expected range: {hard_pct:.3f}"
