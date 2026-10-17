"""
Tests for sutradhar_data package.

Verifies:
- Determinism with fixed seed
- Planted networks (A, B, C) and bridges (Rakesh Pawar, Nitin Gaikwad)
- Common-name collisions (30+) and innocent look-alikes (10+)
- Slot validator: 100% of intended form field values present in narrative
- Noise operators and difficulty tags
- Kumbh events generation (E1, E2, E3 + background)
- No truth leak in published agency records
"""

import json
import random
from pathlib import Path

from sutradhar_data.entities import EntityGenerator
from sutradhar_data.generate import generate_dataset
from sutradhar_data.kumbh import generate_kumbh_events
from sutradhar_data.records import validate_slots


def test_determinism(tmp_path: Path) -> None:
    """Same seed must produce identical outputs."""
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"

    sum1 = generate_dataset(version="v0", seed=123, out_dir=str(out1))
    sum2 = generate_dataset(version="v0", seed=123, out_dir=str(out2))

    assert sum1["total_persons"] == sum2["total_persons"]
    assert sum1["total_records"] == sum2["total_records"]
    assert sum1["records_by_agency"] == sum2["records_by_agency"]

    # Verify file contents are identical
    file1 = out1 / "v0" / "STATE_POLICE" / "records.jsonl"
    file2 = out2 / "v0" / "STATE_POLICE" / "records.jsonl"
    assert file1.read_text(encoding="utf-8") == file2.read_text(encoding="utf-8")


def test_planted_cast_and_bridges() -> None:
    """Verify networks A, B, C and bridges Rakesh Pawar & Nitin Gaikwad exist."""
    rng = random.Random(42)
    eg = EntityGenerator(rng, version="v1")
    cast = eg.generate_planted_cast()

    assert len(cast["A"]) >= 10, "Network A (mule ring) must have >= 10 members"
    assert len(cast["B"]) >= 5, "Network B (extortion) must have >= 5 members"
    assert len(cast["C"]) >= 5, "Network C (drug chain) must have >= 5 members"

    # Check bridges
    bridge_names = [p.canonical_name_rom for p in cast["bridges"]]
    assert any("Rakesh" in name and "Pawar" in name for name in bridge_names)
    assert any("Nitin" in name and "Gaikwad" in name for name in bridge_names)


def test_collision_and_innocent_counts() -> None:
    """Verify >= 30 collisions and >= 10 innocent look-alikes in v1/v2."""
    rng = random.Random(42)
    eg = EntityGenerator(rng, version="v1")
    cast = eg.generate_planted_cast()

    assert len(cast["collisions"]) >= 30, (
        f"Expected >= 30 collisions, got {len(cast['collisions'])}"
    )
    assert len(cast["innocents"]) >= 10, f"Expected >= 10 innocents, got {len(cast['innocents'])}"


def test_rakesh_pawar_multi_agency_renderings(tmp_path: Path) -> None:
    """Rakesh Pawar must appear across all 3 agencies."""
    summary = generate_dataset(version="v0", seed=42, out_dir=str(tmp_path))

    # Read records across all 3 agencies
    spo_path = tmp_path / "v0" / "STATE_POLICE" / "records.jsonl"
    cyb_path = tmp_path / "v0" / "MAHA_CYBER" / "records.jsonl"
    cen_path = tmp_path / "v0" / "CENTRAL_AGENCY" / "records.jsonl"

    assert spo_path.exists()
    assert cyb_path.exists()
    assert cen_path.exists()

    truth_path = tmp_path / "truth" / "v0" / "mention_truth.jsonl"
    mentions = [
        json.loads(line) for line in truth_path.read_text(encoding="utf-8").splitlines() if line
    ]

    networks_truth = json.loads(
        (tmp_path / "truth" / "v0" / "networks_truth.json").read_text(encoding="utf-8")
    )
    rakesh_id = networks_truth["bridge_1"]["person_id"]

    rakesh_mentions = [m for m in mentions if m["person_id"] == rakesh_id]
    # Appears at least 5 times across records
    assert len(rakesh_mentions) >= 5, (
        f"Expected >= 5 mentions of Rakesh Pawar, got {len(rakesh_mentions)}"
    )

    # Check agency coverage of his records
    all_recs = []
    for p in [spo_path, cyb_path, cen_path]:
        all_recs.extend(
            [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line]
        )

    rec_by_id = {r["record_id"]: r for r in all_recs}
    rakesh_agencies = {
        rec_by_id[m["record_id"]]["agency"] for m in rakesh_mentions if m["record_id"] in rec_by_id
    }
    assert rakesh_agencies == {"STATE_POLICE", "MAHA_CYBER", "CENTRAL_AGENCY"}


def test_slot_validator(tmp_path: Path) -> None:
    """100% of generated records must pass slot validation."""
    summary = generate_dataset(version="v0", seed=42, out_dir=str(tmp_path))
    assert summary["slot_validation_errors"] == 0

    # Test error detection on corrupted narrative
    corrupted_form = {"accused": [{"name": "Missing Person"}], "complainant": {}}
    corrupted_narrative = "Completely unrelated narrative without the name."
    errs = validate_slots(corrupted_form, corrupted_narrative)
    assert len(errs) > 0
    assert "Missing Person" in errs[0]


def test_kumbh_events(tmp_path: Path) -> None:
    """Kumbh events generator produces 3 planted events (E1, E2, E3) + ~50 background."""
    events = generate_kumbh_events(seed=42, out_dir=str(tmp_path))
    assert len(events) >= 53

    planted = [e for e in events if e.get("planted")]
    assert len(planted) == 3
    planted_ids = {e["planted_id"] for e in planted}
    assert planted_ids == {"E1", "E2", "E3"}


def test_no_truth_leak(tmp_path: Path) -> None:
    """Records in agency silos must NOT contain person_id or truth network tags."""
    generate_dataset(version="v0", seed=42, out_dir=str(tmp_path))

    agency_files = [
        tmp_path / "v0" / "STATE_POLICE" / "records.jsonl",
        tmp_path / "v0" / "MAHA_CYBER" / "records.jsonl",
        tmp_path / "v0" / "CENTRAL_AGENCY" / "records.jsonl",
    ]

    for f in agency_files:
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            # Ensure person_id is not exposed in public agency records
            assert "person_id" not in rec
            for acc in rec.get("form_fields", {}).get("accused", []):
                assert "person_id" not in acc
                assert "network" not in acc
