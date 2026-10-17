"""
Main generator for Sutradhar synthetic dataset.

Orchestrates entity generation, record emission, truth file creation,
and dev/holdout splitting.

CLI: python -m sutradhar_data.generate --version v0 --seed 42 --out data/
"""

import json
import os
import random
from pathlib import Path
from typing import Any

from .entities import EntityGenerator
from .kumbh import generate_kumbh_events
from .records import RecordEmitter, validate_slots


def _write_jsonl(path: Path, records: list[dict]) -> None:
    """Write records as JSONL (one JSON object per line, UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _write_json(path: Path, data: Any) -> None:
    """Write data as formatted JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_dataset(version: str = "v0", seed: int = 42,
                     out_dir: str = "data") -> dict[str, Any]:
    """
    Generate a complete synthetic dataset.

    Returns a summary dict with counts and paths.
    """
    rng = random.Random(seed)
    out = Path(out_dir)

    # --- Step 1: Generate entities ---
    entity_gen = EntityGenerator(rng, version)
    cast = entity_gen.generate_planted_cast()

    # --- Step 2: Emit records ---
    emitter = RecordEmitter(rng, version)

    # Collect all persons by network for record emission
    all_persons = entity_gen.persons

    # Bridge 1: Rakesh Pawar — appears across ALL THREE agencies
    # with at least 5 different renderings
    bridge_rakesh = cast["bridges"][0]
    bridge_nitin = cast["bridges"][1]

    # STATE_POLICE records for Network B (extortion)
    for person in cast["B"]:
        emitter.emit_state_police_fir(person, crime_type="EXTORTION")

    # Rakesh also in STATE_POLICE (extortion FIR)
    emitter.emit_state_police_fir(bridge_rakesh, crime_type="EXTORTION")

    # Additional rendering of Rakesh in STATE_POLICE (chargesheet)
    emitter.emit_state_police_fir(bridge_rakesh, crime_type="EXTORTION")

    # MAHA_CYBER records for Network A (cyber fraud)
    for person in cast["A"]:
        if person.role in ("RECRUITER", "CONTROLLER", "MEMBER"):
            emitter.emit_maha_cyber_complaint(person)

    # Rakesh also in MAHA_CYBER (fraud complaint)
    emitter.emit_maha_cyber_complaint(bridge_rakesh)

    # Additional rendering of Rakesh in MAHA_CYBER
    emitter.emit_maha_cyber_complaint(bridge_rakesh)

    # CENTRAL_AGENCY records for Network C (narcotics)
    for person in cast["C"]:
        emitter.emit_central_agency_seizure(person)

    # Rakesh also in CENTRAL_AGENCY (drug seizure) — Bridge 1
    emitter.emit_central_agency_seizure(bridge_rakesh)

    # Nitin Gaikwad also appears in CENTRAL_AGENCY (Bridge 2)
    emitter.emit_central_agency_seizure(bridge_nitin)

    # STATE_POLICE records for Network C (drug FIRs)
    for person in cast["C"]:
        if person.role == "COURIER":
            emitter.emit_state_police_fir(person, crime_type="NARCOTICS")

    # Victims / complainants as MAHA_CYBER complaints
    for person in cast["A"]:
        if person.role == "DECEIVED_HOLDER":
            emitter.emit_maha_cyber_complaint(person)

    # Collision groups — some appear in records
    for person in cast["collisions"][:20]:
        agency_choice = rng.choice(["SPO", "CYB", "CEN"])
        if agency_choice == "SPO":
            crime = rng.choice(["EXTORTION", "NARCOTICS"])
            emitter.emit_state_police_fir(person, crime_type=crime)
        elif agency_choice == "CYB":
            emitter.emit_maha_cyber_complaint(person)
        else:
            emitter.emit_central_agency_seizure(person)

    # Innocent look-alikes appear in MAHA_CYBER (some complaints about them)
    for person in cast["innocents"]:
        emitter.emit_maha_cyber_complaint(person)

    # Background noise
    for person in cast["background"]:
        agency_choice = rng.choice(["SPO", "CYB", "CEN"])
        if agency_choice == "SPO":
            emitter.emit_state_police_fir(person)
        elif agency_choice == "CYB":
            emitter.emit_maha_cyber_complaint(person)
        else:
            emitter.emit_central_agency_seizure(person)

    # Transactions (for MAHA_CYBER)
    # Build mule chain transactions: Layer 1 -> 2 -> 3 -> 4
    mule_accounts = []
    for person in cast["A"]:
        for acct in person.accounts:
            mule_accounts.append(acct)
    if len(mule_accounts) >= 2:
        num_txns = min(20, len(mule_accounts) * 2)
        emitter.emit_transactions(mule_accounts, num_txns=num_txns, base_amount=500000)

    # Ensure every account participating in transactions exists in MAHA_CYBER accounts.jsonl
    for person in cast["A"]:
        for acct in person.accounts:
            if not any(a["account_key"] == acct["account_key"] for a in emitter.all_accounts):
                emitter.all_accounts.append({
                    "account_key": acct["account_key"],
                    "bank": acct["bank"],
                    "ifsc": acct["ifsc"],
                    "holder_name_raw": person.canonical_name_rom,
                    "opened_date": "2021-01-15",
                    "complaint_count": 1,
                    "record_ids": [],
                })

    # --- Step 3: Partition records by agency ---
    spo_records = [r for r in emitter.all_records if r["agency"] == "STATE_POLICE"]
    cyb_records = [r for r in emitter.all_records if r["agency"] == "MAHA_CYBER"]
    cen_records = [r for r in emitter.all_records if r["agency"] == "CENTRAL_AGENCY"]

    version_dir = out / version
    _write_jsonl(version_dir / "STATE_POLICE" / "records.jsonl", spo_records)
    _write_jsonl(version_dir / "MAHA_CYBER" / "records.jsonl", cyb_records)
    _write_jsonl(version_dir / "MAHA_CYBER" / "accounts.jsonl", emitter.all_accounts)
    _write_jsonl(version_dir / "MAHA_CYBER" / "transactions.jsonl", emitter.all_transactions)
    _write_jsonl(version_dir / "CENTRAL_AGENCY" / "records.jsonl", cen_records)

    # --- Step 4: Generate truth files ---
    truth_dir = out / "truth" / version

    # mention_truth.jsonl
    _write_jsonl(truth_dir / "mention_truth.jsonl", emitter.all_mentions_truth)

    # person_truth.jsonl
    person_truths = [p.to_truth_dict() for p in entity_gen.persons]
    _write_jsonl(truth_dir / "person_truth.jsonl", person_truths)

    # account_truth.jsonl
    account_truths = []
    for person in entity_gen.persons:
        for acct in person.accounts:
            layer = 0
            if person.network == "A":
                if person.role == "DECEIVED_HOLDER":
                    acct_class = "DECEIVED"
                    layer = rng.randint(2, 4)
                elif person.role in ("RECRUITER", "CONTROLLER"):
                    acct_class = "ORGANISER"
                    layer = 1
                elif person.role == "MEMBER":
                    acct_class = "ORGANISER"
                    layer = rng.randint(1, 3)
                else:
                    acct_class = "NEUTRAL"
            else:
                acct_class = "NEUTRAL"
            account_truths.append({
                "account_key": acct["account_key"],
                "person_id": person.person_id,
                "layer": layer,
                "class": acct_class,
            })
    _write_jsonl(truth_dir / "account_truth.jsonl", account_truths)

    # networks_truth.json
    networks_truth = {
        "A": {
            "name": "Cyber-fraud mule ring",
            "members": [p.person_id for p in cast["A"]],
            "bridges": [bridge_nitin.person_id],
            "leader_id": None,
            "recruiter_id": cast["A"][0].person_id if cast["A"] else None,
            "controller_id": bridge_nitin.person_id,
        },
        "B": {
            "name": "Urban extortion gang",
            "members": [p.person_id for p in cast["B"]],
            "bridges": [bridge_rakesh.person_id],
            "leader_id": cast["B"][0].person_id if cast["B"] else None,
        },
        "C": {
            "name": "Interstate drug chain",
            "members": [p.person_id for p in cast["C"]],
            "bridges": [bridge_nitin.person_id],
            "leader_id": None,
            "financier_id": cast["C"][0].person_id if cast["C"] else None,
        },
        "bridge_1": {
            "person_id": bridge_rakesh.person_id,
            "name": bridge_rakesh.canonical_name_rom,
            "networks": ["B"],
            "agencies": ["STATE_POLICE", "MAHA_CYBER", "CENTRAL_AGENCY"],
        },
        "bridge_2": {
            "person_id": bridge_nitin.person_id,
            "name": bridge_nitin.canonical_name_rom,
            "networks": ["A", "C"],
            "agencies": ["MAHA_CYBER", "CENTRAL_AGENCY"],
        },
    }
    _write_json(truth_dir / "networks_truth.json", networks_truth)

    # --- Step 5: Dev split (20% stratified) ---
    dev_dir = out / "dev"
    mentions = emitter.all_mentions_truth

    # Stratify by network and difficulty
    # Group mentions by person's network
    person_network = {p.person_id: p.network for p in entity_gen.persons}

    # Simple stratified split: pick ~20% from each network group
    dev_mentions = []
    holdout_mentions = []

    # Group by network
    by_network: dict[str, list[dict]] = {}
    for m in mentions:
        net = person_network.get(m["person_id"], "NONE")
        by_network.setdefault(net, []).append(m)

    for net, group in by_network.items():
        rng.shuffle(group)
        split_idx = max(1, len(group) // 5)  # 20%
        dev_mentions.extend(group[:split_idx])
        holdout_mentions.extend(group[split_idx:])

    # Dev labels
    dev_labels = [
        {"mention_id": m["mention_id"], "person_id": m["person_id"]}
        for m in dev_mentions
    ]
    _write_jsonl(dev_dir / "dev_labels.jsonl", dev_labels)

    # Also copy the version data to dev for convenience
    _write_jsonl(dev_dir / "STATE_POLICE" / "records.jsonl", spo_records)
    _write_jsonl(dev_dir / "MAHA_CYBER" / "records.jsonl", cyb_records)
    _write_jsonl(dev_dir / "MAHA_CYBER" / "accounts.jsonl", emitter.all_accounts)
    _write_jsonl(dev_dir / "MAHA_CYBER" / "transactions.jsonl", emitter.all_transactions)
    _write_jsonl(dev_dir / "CENTRAL_AGENCY" / "records.jsonl", cen_records)

    # --- Step 6: Validate slots ---
    slot_errors = []
    for rec in emitter.all_records:
        missing = validate_slots(rec["form_fields"], rec["narrative"])
        if missing:
            slot_errors.append({
                "record_id": rec["record_id"],
                "missing_slots": missing,
            })

    # --- Step 7: Kumbh events feed ---
    kumbh_events = generate_kumbh_events(seed=seed, out_dir=str(out))

    # --- Summary ---
    summary = {
        "version": version,
        "seed": seed,
        "total_persons": len(entity_gen.persons),
        "total_records": len(emitter.all_records),
        "records_by_agency": {
            "STATE_POLICE": len(spo_records),
            "MAHA_CYBER": len(cyb_records),
            "CENTRAL_AGENCY": len(cen_records),
        },
        "total_accounts": len(emitter.all_accounts),
        "total_transactions": len(emitter.all_transactions),
        "total_mentions": len(mentions),
        "dev_mentions": len(dev_mentions),
        "holdout_mentions": len(holdout_mentions),
        "networks": {
            "A": len(cast["A"]),
            "B": len(cast["B"]),
            "C": len(cast["C"]),
        },
        "bridges": len(cast["bridges"]),
        "collision_persons": len(cast["collisions"]),
        "innocent_lookalikes": len(cast["innocents"]),
        "background": len(cast["background"]),
        "slot_validation_errors": len(slot_errors),
        "output_dir": str(out),
    }

    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Sutradhar synthetic dataset",
        prog="python -m sutradhar_data.generate",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="v0",
        choices=["v0", "v1", "v2", "v3"],
        help="Dataset version (controls noise level and scale)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="data",
        help="Output directory (default: data/)",
    )

    args = parser.parse_args()
    summary = generate_dataset(
        version=args.version,
        seed=args.seed,
        out_dir=args.out,
    )

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(
        f"\n[OK] Generated {summary['total_records']} records for "
        f"{summary['total_persons']} persons ({args.version}, seed={args.seed})"
    )


if __name__ == "__main__":
    main()
