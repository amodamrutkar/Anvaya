"""
scripts/evaluate_seeds.py
Step 6B Comprehensive Evaluation Runner across seeds 42, 43, 44:
- Runs ER pipeline (sutradhar_er)
- Runs Graph intelligence pipeline (sutradhar_graph)
- Runs Evaluation harness (sutradhar_eval)
- Measures decoy false-merge rates, bridge discovery & ranks, mule classification, and timings.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time

# Ensure services are on sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "services" / "data_gen"))
sys.path.insert(0, str(root_dir / "services" / "nlp"))
sys.path.insert(0, str(root_dir / "services" / "graph"))
sys.path.insert(0, str(root_dir / "services" / "eval"))

from sutradhar_data.generate import generate_dataset
from sutradhar_er.run import run_pipeline as run_er
from sutradhar_graph.run import run_pipeline as run_graph
from sutradhar_eval.run import run_evaluation


def evaluate_seed(seed: int, base_dir: Path) -> dict:
    data_dir = base_dir / "data" / "v2" / "dev" / f"seed-{seed}"
    truth_dir = base_dir / "data" / "truth" / "v2" / "dev" / f"seed-{seed}"
    artifacts_dir = base_dir / "artifacts" / f"seed-{seed}"
    er_out = artifacts_dir / "er"
    graph_out = artifacts_dir / "graph"
    metrics_out = artifacts_dir / "metrics.json"

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    er_out.mkdir(parents=True, exist_ok=True)
    graph_out.mkdir(parents=True, exist_ok=True)

    # 1. Generation Timing (from a fresh run to measure time)
    t0 = time.perf_counter()
    gen_summary = generate_dataset(version="v2", tier="dev", seed=seed, out_dir=str(base_dir / "data"))
    t_gen = round(time.perf_counter() - t0, 3)

    # 2. ER Pipeline Timing & Execution
    t0 = time.perf_counter()
    er_summary = run_er(data_dir=data_dir, out_dir=er_out, verbose=False)
    t_er = round(time.perf_counter() - t0, 3)

    # 3. Graph Pipeline Timing & Execution
    t0 = time.perf_counter()
    graph_summary = run_graph(data_dir=data_dir, er_dir=er_out, out_dir=graph_out)
    t_graph = round(time.perf_counter() - t0, 3)

    # 4. Eval Harness Timing & Execution
    t0 = time.perf_counter()
    eval_metrics = run_evaluation(
        data_dir=str(data_dir),
        truth_dir=str(truth_dir),
        artifacts_dir=str(artifacts_dir),
        out_path=str(metrics_out),
        version="v2",
    )
    t_eval = round(time.perf_counter() - t0, 3)

    # 5. Extract Detailed Observable Graph Insights
    # Read bridges prediction
    bridges_path = graph_out / "bridges.json"
    pred_bridges = []
    if bridges_path.exists():
        with open(bridges_path, encoding="utf-8") as f:
            b_data = json.load(f)
            pred_bridges = b_data.get("bridges", []) if isinstance(b_data, dict) else b_data

    # Read communities prediction
    comm_path = graph_out / "communities.json"
    pred_comms = []
    if comm_path.exists():
        with open(comm_path, encoding="utf-8") as f:
            c_data = json.load(f)
            pred_comms = c_data.get("communities", []) if isinstance(c_data, dict) else c_data

    # Read mule chains prediction
    mule_path = graph_out / "mule_chains.json"
    pred_mules = []
    if mule_path.exists():
        with open(mule_path, encoding="utf-8") as f:
            m_data = json.load(f)
            pred_mules = m_data.get("chains", []) if isinstance(m_data, dict) else m_data

    # Read roles prediction
    roles_path = graph_out / "roles.json"
    pred_roles = []
    if roles_path.exists():
        with open(roles_path, encoding="utf-8") as f:
            r_data = json.load(f)
            pred_roles = r_data.get("roles", []) if isinstance(r_data, dict) else r_data

    # Read truth networks
    networks_truth = {}
    with open(truth_dir / "networks_truth.json", encoding="utf-8") as f:
        networks_truth = json.load(f)

    # Planted bridge discovery & ranking details
    planted_bridges = networks_truth.get("bridges", [])
    bridge_eval_details = []
    for pb in planted_bridges:
        pid = pb["person_id"]
        pname = pb["canonical_name"]
        # Look for this person in pred_bridges
        matched_rank = None
        matched_score = None
        evidence_found = []
        for idx, pb_pred in enumerate(pred_bridges):
            if pb_pred.get("linked_person") == pid or pb_pred.get("node_id") == f"PERSON:{pid}" or pname.lower() in pb_pred.get("label", "").lower():
                matched_rank = idx + 1
                matched_score = pb_pred.get("score")
                evidence_found = pb_pred.get("reasons", [])
                break

        bridge_eval_details.append({
            "person_id": pid,
            "name": pname,
            "network": pb.get("network"),
            "secondary_network": pb.get("secondary_network"),
            "discovered": matched_rank is not None,
            "rank": matched_rank,
            "score": matched_score,
            "evidence": evidence_found,
        })

    # Decoy False Positives in ER:
    # Check if any different people with same name (COLLISION_A vs COLLISION_B) were auto-linked
    person_truth = []
    with open(truth_dir / "person_truth.jsonl", encoding="utf-8") as f:
        person_truth = [json.loads(line) for line in f if line.strip()]
    pt_map = {p["person_id"]: p for p in person_truth}

    mention_truth = []
    with open(truth_dir / "mention_truth.jsonl", encoding="utf-8") as f:
        mention_truth = [json.loads(line) for line in f if line.strip()]
    mt_map = {m["mention_id"]: m for m in mention_truth}

    pred_links = []
    with open(er_out / "links.jsonl", encoding="utf-8") as f:
        pred_links = [json.loads(line) for line in f if line.strip()]

    name_collision_wrong_merges = 0
    chawl_wrong_merges = 0
    family_phone_wrong_merges = 0

    for link in pred_links:
        if link.get("band") == "AUTO":
            ma = mt_map.get(link.get("a_mention_id"))
            mb = mt_map.get(link.get("b_mention_id"))
            if ma and mb and ma["person_id"] != mb["person_id"]:
                pa = pt_map.get(ma["person_id"], {})
                pb = pt_map.get(mb["person_id"], {})
                if pa.get("decoy_type") == "NAME_COLLISION" or pb.get("decoy_type") == "NAME_COLLISION":
                    name_collision_wrong_merges += 1
                if pa.get("decoy_type") == "CIVILIAN_CHAWL" or pb.get("decoy_type") == "CIVILIAN_CHAWL":
                    chawl_wrong_merges += 1
                if pa.get("decoy_type") == "FAMILY_SHARED_PHONE" or pb.get("decoy_type") == "FAMILY_SHARED_PHONE":
                    family_phone_wrong_merges += 1

    # Legitimate pass-through false positive organiser classifications in mule intelligence
    legit_pt_as_organiser = 0
    deceived_correct = 0
    deceived_total = 0
    for chain in pred_mules:
        for acct in chain.get("accounts", []):
            ak = acct.get("account_id") or acct.get("account_key")
            cls = acct.get("classification")
            raw_holder = acct.get("holder_name", "")
            if any(k in raw_holder.lower() for k in ["kirana", "store", "stall", "partner", "delivery"]):
                if cls == "LIKELY_ORGANISER":
                    legit_pt_as_organiser += 1
            if cls == "LIKELY_DECEIVED":
                deceived_correct += 1

    # Kumbh control case verification
    kumbh_control_alarms = 0
    kumbh_path = base_dir / "data" / "v2" / "dev" / f"seed-{seed}" / "kumbh" / "events.jsonl"
    with open(kumbh_path, encoding="utf-8") as f:
        for line in f:
            evt = json.loads(line)
            if evt.get("event_id") == "KUMBH-EVT-0003":
                # Control event: verify it is NOT a watchlist or scam alert
                if evt.get("event_type") in ("WATCHLIST_SIGHTING", "SCAM_PATTERN"):
                    kumbh_control_alarms += 1

    return {
        "seed": seed,
        "timings": {
            "generation_seconds": t_gen,
            "er_seconds": t_er,
            "graph_seconds": t_graph,
            "eval_seconds": t_eval,
            "total_pipeline_seconds": round(t_er + t_graph + t_eval, 3),
        },
        "counts": {
            "persons": gen_summary["total_persons"],
            "records": gen_summary["total_records"],
            "mentions": len(mention_truth),
            "accounts": gen_summary["total_accounts"],
            "transactions": gen_summary["total_transactions"],
            "kumbh_events": gen_summary["total_kumbh_events"],
            "syndicates": gen_summary["total_syndicates"],
            "bridges": gen_summary["total_bridges"],
        },
        "er_metrics": eval_metrics.get("er", eval_metrics.get("entity_resolution", {})),
        "network_metrics": eval_metrics.get("network", eval_metrics.get("network_recovery", {})),
        "mule_metrics": eval_metrics.get("mule", eval_metrics.get("mule_investigation", {})),
        "fairness": eval_metrics.get("fairness", eval_metrics.get("fairness_audit", {})),
        "bridge_details": bridge_eval_details,
        "decoy_false_positives": {
            "name_collision_wrong_merges": name_collision_wrong_merges,
            "chawl_shared_address_wrong_merges": chawl_wrong_merges,
            "family_shared_phone_wrong_merges": family_phone_wrong_merges,
            "legitimate_passthrough_organiser_false_positives": legit_pt_as_organiser,
        },
        "kumbh_control_alarms": kumbh_control_alarms,
    }


def main():
    base_dir = Path(".").resolve()
    results = {}
    for s in [42, 43, 44]:
        print(f"\n==========================================")
        print(f"RUNNING STEP 6B EVALUATION FOR SEED {s}")
        print(f"==========================================")
        res = evaluate_seed(s, base_dir)
        results[s] = res
        print(f"Seed {s} Results:")
        print(f"  ER Auto Precision: {res['er_metrics'].get('auto_precision')}")
        print(f"  ER Auto Recall: {res['er_metrics'].get('auto_recall')}")
        print(f"  ER Wrong Merge Rate: {res['er_metrics'].get('wrong_merge_rate')}")
        print(f"  ER Review Share: {res['er_metrics'].get('review_share')}")
        print(f"  Network Communities: {res['network_metrics'].get('recovered')}/{res['network_metrics'].get('planted')}")
        print(f"  Kingpin Rank: {res['network_metrics'].get('kingpin_rank')}")
        print(f"  Bridges Discovered: {res['network_metrics'].get('bridges_found')}/{res['network_metrics'].get('bridges_planted')}")
        print(f"  Mule Max Depth: {res['mule_metrics'].get('max_depth')}")
        print(f"  Deceived Precision: {res['mule_metrics'].get('deceived_precision')}")
        print(f"  Decoy Name Collision Wrong Merges: {res['decoy_false_positives']['name_collision_wrong_merges']}")
        print(f"  Decoy Chawl Address Wrong Merges: {res['decoy_false_positives']['chawl_shared_address_wrong_merges']}")
        print(f"  Kumbh Control Alarms: {res['kumbh_control_alarms']}")
        print(f"  Total Pipeline Time: {res['timings']['total_pipeline_seconds']}s")

    out_file = base_dir / "artifacts" / "evaluation_report_step6b.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Full Step 6B evaluation written to {out_file}")


if __name__ == "__main__":
    main()
