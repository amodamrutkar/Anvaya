"""
scripts/v2_report.py
Validation and state report script for Sutradhar dataset v2.

Reads generated dataset from data/v2/<tier>/seed-<seed>/ and ground truth from
data/truth/v2/<tier>/seed-<seed>/, computing:
1. Counts (persons, records per agency, mentions, accounts, transactions, Kumbh events)
2. Achieved difficulty mix (EASY, MEDIUM, HARD)
3. Fairness / Demographic distribution (pool proportions across civilian vs criminal roles)
4. Surname frequency distribution (Zipfian check)
5. Syndicate & Bridge operative topologies
6. Safety validations (pseudo-Aadhaar Verhoeff failure, denylist check)

Usage:
    python scripts/v2_report.py --tier dev --seed 42
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

# Add services/data_gen to sys.path
services_dir = Path(__file__).resolve().parent.parent / "services" / "data_gen"
if str(services_dir) not in sys.path:
    sys.path.insert(0, str(services_dir))

from sutradhar_data.safety import (
    validate_pseudo_aadhaar_fails_verhoeff,
    check_name_denylist,
)


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_v2_report(
    tier: str = "dev",
    seed: int = 42,
    base_dir: str = "data",
) -> dict:
    base = Path(base_dir)
    tier_dir = base / "v2" / tier / f"seed-{seed}"
    truth_dir = base / "truth" / "v2" / tier / f"seed-{seed}"

    if not tier_dir.exists():
        print(f"Error: {tier_dir} does not exist. Run data generator first.")
        sys.exit(1)

    # 1. Load data
    spo_records = _read_jsonl(tier_dir / "STATE_POLICE" / "records.jsonl")
    cyb_records = _read_jsonl(tier_dir / "MAHA_CYBER" / "records.jsonl")
    cen_records = _read_jsonl(tier_dir / "CENTRAL_AGENCY" / "records.jsonl")
    accounts = _read_jsonl(tier_dir / "MAHA_CYBER" / "accounts.jsonl")
    transactions = _read_jsonl(tier_dir / "MAHA_CYBER" / "transactions.jsonl")
    kumbh_events = _read_jsonl(tier_dir / "kumbh" / "events.jsonl")

    # Load truth
    mention_truth = _read_jsonl(truth_dir / "mention_truth.jsonl")
    person_truth = _read_jsonl(truth_dir / "person_truth.jsonl")
    account_truth = _read_jsonl(truth_dir / "account_truth.jsonl")
    networks_truth = _read_json(truth_dir / "networks_truth.json")
    mcoca_truth = _read_json(truth_dir / "mcoca_truth.json")

    # 2. Counts Summary
    counts = {
        "persons": len(person_truth),
        "records": {
            "STATE_POLICE": len(spo_records),
            "MAHA_CYBER": len(cyb_records),
            "CENTRAL_AGENCY": len(cen_records),
            "total": len(spo_records) + len(cyb_records) + len(cen_records),
        },
        "mentions": len(mention_truth),
        "accounts": len(accounts),
        "transactions": len(transactions),
        "kumbh_events": len(kumbh_events),
    }

    # 3. Difficulty Mix
    diff_counts = Counter(m.get("difficulty", "UNKNOWN") for m in mention_truth)
    total_m = len(mention_truth) or 1
    difficulty_mix = {
        k: f"{v} ({v / total_m * 100:.1f}%)" for k, v in diff_counts.items()
    }

    # 4. Demographic Fairness Check
    # Verify pool representation in civilian roles vs syndicate membership
    pool_counts = Counter(p.get("pool", "unknown") for p in person_truth)
    total_p = len(person_truth) or 1
    pool_proportions = {
        k: f"{v} ({v / total_p * 100:.1f}%)" for k, v in pool_counts.items()
    }

    # Check syndicate vs civilian roles per pool
    pool_criminality: dict[str, dict[str, int]] = defaultdict(lambda: {"syndicate": 0, "civilian": 0})
    for p in person_truth:
        pool = p.get("pool", "unknown")
        if p.get("network") not in (None, "NONE"):
            pool_criminality[pool]["syndicate"] += 1
        else:
            pool_criminality[pool]["civilian"] += 1

    fairness_check = {}
    for pool, stat in pool_criminality.items():
        tot = stat["syndicate"] + stat["civilian"]
        rate = (stat["syndicate"] / tot * 100) if tot > 0 else 0
        fairness_check[pool] = {
            "total": tot,
            "syndicate_members": stat["syndicate"],
            "civilian": stat["civilian"],
            "syndicate_rate": f"{rate:.1f}%",
        }

    # 5. Surname Histogram (Top 15)
    surnames = Counter()
    for p in person_truth:
        name_parts = p.get("canonical_name", "").split()
        if name_parts:
            surnames[name_parts[-1]] += 1
    top_surnames = surnames.most_common(15)

    # 6. Syndicate & Bridge Operatives Topology
    syndicates_info = {}
    for cid, sdata in networks_truth.get("syndicates", {}).items():
        syndicates_info[cid] = {
            "member_count": sdata.get("count", len(sdata.get("members", []))),
            "sample_members": sdata.get("members", [])[:4],
        }

    bridges_info = [
        {
            "person_id": b.get("person_id"),
            "name": b.get("canonical_name"),
            "network": b.get("network"),
            "secondary_network": b.get("secondary_network"),
        }
        for b in networks_truth.get("bridges", [])
    ]

    # 7. Safety Audits
    # A. Pseudo-Aadhaar Verhoeff audit
    aadhaars_tested = 0
    aadhaars_failed_verhoeff = 0
    for p in person_truth:
        for a in p.get("pseudo_aadhaar", []):
            aadhaars_tested += 1
            if validate_pseudo_aadhaar_fails_verhoeff(a):
                aadhaars_failed_verhoeff += 1

    # B. Denylist figure audit
    names_tested = 0
    denylist_hits = 0
    for p in person_truth:
        names_tested += 1
        if not check_name_denylist(p.get("canonical_name", "")):
            denylist_hits += 1

    safety_report = {
        "pseudo_aadhaars_evaluated": aadhaars_tested,
        "pseudo_aadhaars_guaranteed_invalid": aadhaars_failed_verhoeff,
        "names_evaluated": names_tested,
        "denylist_prominent_figure_hits": denylist_hits,
        "safety_audit_passed": (aadhaars_tested == aadhaars_failed_verhoeff) and (denylist_hits == 0),
    }

    # Format full report
    report = {
        "dataset_tier": tier,
        "seed": seed,
        "counts": counts,
        "difficulty_mix": difficulty_mix,
        "pool_proportions": pool_proportions,
        "demographic_fairness": fairness_check,
        "top_surnames": top_surnames,
        "syndicates_count": len(syndicates_info),
        "syndicates": syndicates_info,
        "bridges_count": len(bridges_info),
        "bridges": bridges_info,
        "mcoca_test_cases": len(mcoca_truth.get("syndicates", {})),
        "safety_audit": safety_report,
    }

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Sutradhar dataset v2 state and validation report")
    parser.add_argument("--tier", default="dev", choices=["dev", "full", "stress"], help="Dataset tier")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--out", default="data", help="Data base directory")
    args = parser.parse_args()

    report = generate_v2_report(tier=args.tier, seed=args.seed, base_dir=args.out)
    print("=" * 70)
    print(f"SUTRADHAR DATASET V2 REPORT ({args.tier.upper()} TIER, SEED {args.seed})")
    print("=" * 70)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("=" * 70)
    print("[OK] Report generation and safety checks complete.")


if __name__ == "__main__":
    main()
