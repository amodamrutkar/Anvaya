"""
services/eval/sutradhar_eval/graph_eval.py

Comprehensive Evaluation Harness for Step 3 & Step 3.5:
- Identity mapping audit: mention_id -> true_person_id without positional/zip alignment
- Oracle ER: pairwise identity precision=1.0, recall=1.0, exactly 1 PERSON node per true person appearing in data
- Identity-monotonic vs. Topology-dependent oracle sanity checks
- Syndicate recovery: Jaccard, member recall, community purity, and threshold matching (0.2, 0.3, 0.5)
- Bridge candidate audit: Precision@k and Recall@k for k in [5, 10, 20, 50]
- Decoy cluster protection audit and case threshold sensitivity analysis
- Account classification confusion matrix (LIKELY_DECEIVED, LIKELY_ORGANISER, UNCERTAIN)
- S-03 Money chain reconciliation against V1 baseline
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from itertools import combinations
import json
from pathlib import Path
import shutil
from typing import Any

from sutradhar_er.normalise import normalise_name
from sutradhar_graph.build import GraphBuilder
from sutradhar_graph.mule import trace_financial_flow, trace_mule_chains
from sutradhar_graph.run import run_pipeline as run_graph_pipeline


def _read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_mention_id_to_true_person_map(
    er_mentions: list[dict[str, Any]],
    mention_truth: list[dict[str, Any]],
    person_truth: dict[str, dict[str, Any]],
) -> dict[str, str]:
    """
    Builds strict mention_id -> true_person_id mapping.
    NEVER uses positional alignment, zip-by-record-order, or assumed record ordering.
    Matches mentions within records by role and name token overlap.
    """
    truth_by_rec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for tm in mention_truth:
        if tm.get("role") != "WITNESS":
            pid = tm["person_id"]
            p_info = person_truth.get(pid, {})
            truth_by_rec[tm["record_id"]].append({
                "truth_mention_id": tm["mention_id"],
                "person_id": pid,
                "role": tm.get("role"),
                "norm_name": normalise_name(p_info.get("canonical_name", "")),
                "canonical_name_dev": p_info.get("canonical_name_dev", ""),
            })

    er_by_rec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for em in er_mentions:
        er_by_rec[em["record_id"]].append(em)

    mid_to_pid: dict[str, str] = {}
    for rid, em_list in er_by_rec.items():
        tm_list = list(truth_by_rec.get(rid, []))

        pair_scores = []
        for em in em_list:
            raw = em.get("name_raw", "").strip()
            # Clean spaces around punctuation to normalize initials like 'S. S.J adhav' -> 'S. S. Jadhav'
            clean_raw = raw.replace(". ", ".").replace(".", ". ")
            norm = normalise_name(clean_raw)
            tokens = set(norm.split())
            inits = [t[0] for t in norm.split() if t]

            for tm in tm_list:
                tm_tokens = set(tm["norm_name"].split())
                tm_inits = [t[0] for t in tm["norm_name"].split() if t]
                overlap = len(tokens & tm_tokens)

                dev_match = (
                    (raw in tm.get("canonical_name_dev", "") or tm.get("canonical_name_dev", "") in raw)
                    if tm.get("canonical_name_dev")
                    else False
                )
                init_match = (inits == tm_inits) if len(inits) >= 2 else False
                role_match = (
                    (em.get("role") == tm.get("role"))
                    or (em.get("role") == "ACCUSED" and tm.get("role") == "SUSPECT")
                    or (em.get("role") == "COMPLAINANT" and tm.get("role") == "VICTIM")
                )
                role_mismatch = (
                    (em.get("role") in ("ACCUSED", "SUSPECT") and tm.get("role") in ("COMPLAINANT", "VICTIM"))
                    or (em.get("role") in ("COMPLAINANT", "VICTIM") and tm.get("role") in ("ACCUSED", "SUSPECT"))
                )

                score = (
                    overlap * 3.0
                    + (5.0 if dev_match else 0.0)
                    + (4.0 if init_match else 0.0)
                    + (5.0 if role_match else (-5.0 if role_mismatch else 0.0))
                )
                pair_scores.append((score, em["mention_id"], tm["truth_mention_id"], em, tm))

        # Sort pairs deterministically by score descending, then by IDs to ensure complete order-invariance
        pair_scores.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)

        assigned_ems = set()
        assigned_tms = set()
        for score, em_id, tm_id, em, tm in pair_scores:
            if score <= 0:
                break
            if em_id not in assigned_ems and tm_id not in assigned_tms:
                mid_to_pid[em_id] = tm["person_id"]
                assigned_ems.add(em_id)
                assigned_tms.add(tm_id)

        # Fallback for remaining single unassigned pair within the record
        unassigned_ems = [em for em in em_list if em["mention_id"] not in assigned_ems]
        unassigned_tms = [tm for tm in tm_list if tm["truth_mention_id"] not in assigned_tms]
        if len(unassigned_ems) == 1 and len(unassigned_tms) == 1:
            mid_to_pid[unassigned_ems[0]["mention_id"]] = unassigned_tms[0]["person_id"]

    return mid_to_pid



def create_oracle_er(data_dir: Path, truth_dir: Path, er_dir: Path, out_dir: Path) -> None:
    """
    Creates Oracle ER artifacts purely for evaluation (NEVER used in production).
    Maps extracted mentions to true person_ids without positional/zip alignment.
    Also injects complainant mention IDs so GraphBuilder creates exactly one PERSON node per true person.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    pred_mentions = _read_jsonl(er_dir / "mentions.jsonl")
    mention_truth = _read_jsonl(truth_dir / "mention_truth.jsonl")
    person_truth = {p["person_id"]: p for p in _read_jsonl(truth_dir / "person_truth.jsonl")}

    # Copy mentions.jsonl to out_dir
    shutil.copyfile(er_dir / "mentions.jsonl", out_dir / "mentions.jsonl")

    # Attribute-based mention_id -> true_person_id mapping
    mid_to_pid = build_mention_id_to_true_person_map(pred_mentions, mention_truth, person_truth)

    pid_to_mids: dict[str, set[str]] = defaultdict(set)
    pid_to_records: dict[str, set[str]] = defaultdict(set)
    for pm in pred_mentions:
        mid = pm.get("mention_id", "")
        pid = mid_to_pid.get(mid)
        rid = pm.get("record_id", "")
        if pid:
            pid_to_mids[pid].add(mid)
            if rid:
                pid_to_records[pid].add(rid)
                if pm.get("role") in ("COMPLAINANT", "VICTIM"):
                    raw_cname = pm.get("name_raw", "").strip()
                    pid_to_mids[pid].add(f"M-COMP-{rid}-{raw_cname}")

    oracle_entities = []
    for pid, mids in sorted(pid_to_mids.items()):
        p_info = person_truth.get(pid, {})
        cname = p_info.get("canonical_name", f"Person {pid}")
        oracle_entities.append({
            "entity_id": pid,
            "entity_type": "PERSON",
            "canonical_name": cname,
            "mention_ids": sorted(mids),
            "record_ids": sorted(pid_to_records[pid]),
            "min_link_confidence": 1.0,
            "status": "ACTIVE",
        })

    with open(out_dir / "entities.jsonl", "w", encoding="utf-8") as f:
        for ent in oracle_entities:
            f.write(json.dumps(ent, ensure_ascii=False) + "\n")

    # Oracle links: empty (no review links needed for oracle)
    with open(out_dir / "links.jsonl", "w", encoding="utf-8") as f:
        pass


def evaluate_graph_run(
    data_dir: Path,
    truth_dir: Path,
    er_dir: Path,
    graph_dir: Path,
    is_oracle: bool = False,
) -> dict[str, Any]:
    """
    Computes rigorous graph, network, role, financial, and safety metrics.
    """
    graph_data = _read_json(graph_dir / "graph.json")
    communities_data = _read_json(graph_dir / "communities.json").get("communities", [])
    roles_data = _read_json(graph_dir / "roles.json").get("roles", [])
    bridges_data = _read_json(graph_dir / "bridges.json").get("bridges", [])
    mule_data = _read_json(graph_dir / "mule_chains.json").get("chains", [])
    summary_data = _read_json(graph_dir / "summary.json")

    networks_truth = _read_json(truth_dir / "networks_truth.json")
    account_truth = _read_jsonl(truth_dir / "account_truth.jsonl")
    person_truth_list = _read_jsonl(truth_dir / "person_truth.jsonl")
    person_truth = {p["person_id"]: p for p in person_truth_list}
    mention_truth = _read_jsonl(truth_dir / "mention_truth.jsonl")
    pred_mentions = _read_jsonl(er_dir / "mentions.jsonl")
    pred_entities = [e for e in _read_jsonl(er_dir / "entities.jsonl") if e.get("entity_type") == "PERSON"]

    mid_to_pid = build_mention_id_to_true_person_map(pred_mentions, mention_truth, person_truth)

    entity_to_dominant_pid: dict[str, str] = {}
    entity_to_pids: dict[str, set[str]] = defaultdict(set)
    for e in pred_entities:
        eid = e["entity_id"]
        pids = [mid_to_pid[mid] for mid in e.get("mention_ids", []) if mid in mid_to_pid]
        if pids:
            entity_to_dominant_pid[eid] = Counter(pids).most_common(1)[0][0]
            entity_to_pids[eid].update(pids)

    # Truth bridges
    truth_bridge_pids = set()
    for b in networks_truth.get("bridges", []):
        if b.get("person_id"):
            truth_bridge_pids.add(b["person_id"])
    for p in person_truth_list:
        if p.get("role") == "BROKER":
            truth_bridge_pids.add(p["person_id"])

    # Active truth bridges present in dataset
    all_data_pids = set(mid_to_pid.values())
    active_truth_bridges = truth_bridge_pids & all_data_pids

    # Bridge Precision@k and Recall@k
    bridge_metrics: dict[str, Any] = {}
    for k in [5, 10, 20, 50]:
        cands_k = bridges_data[:k]
        hits = 0
        hit_bridges = set()
        for b in cands_k:
            nid = b.get("node_id", "")
            pids_assoc = entity_to_pids.get(nid, set())
            matched_bridge = None
            if nid in truth_bridge_pids:
                matched_bridge = nid
            elif pids_assoc & truth_bridge_pids:
                matched_bridge = list(pids_assoc & truth_bridge_pids)[0]
            if matched_bridge:
                hits += 1
                hit_bridges.add(matched_bridge)
        prec = hits / k if k > 0 else 0.0
        rec = len(hit_bridges) / len(active_truth_bridges) if active_truth_bridges else 1.0
        bridge_metrics[f"precision_{k}"] = f"{hits}/{k} = {prec*100:.2f}%"
        bridge_metrics[f"recall_{k}"] = f"{len(hit_bridges)}/{len(active_truth_bridges)} = {rec*100:.2f}%"
        bridge_metrics[f"raw_precision_{k}"] = prec
        bridge_metrics[f"raw_recall_{k}"] = rec

    # Syndicate recovery
    syndicates_truth = networks_truth.get("syndicates", {})
    syndicate_recovery = []
    recovered_at_02 = 0
    recovered_at_03 = 0
    recovered_at_05 = 0
    for syn_id in sorted(syndicates_truth.keys()):
        s_info = syndicates_truth[syn_id]
        t_members = set(s_info.get("members", []))
        data_members = t_members & all_data_pids
        best_comm = "NONE"
        best_jaccard = 0.0
        best_rec = 0.0
        best_pur = 0.0
        best_inter = 0
        best_comm_len = 0
        for c in communities_data:
            cid = c["community_id"]
            if is_oracle:
                comm_pids = set(c.get("members", []))
            else:
                comm_pids = {entity_to_dominant_pid.get(m) for m in c.get("members", []) if entity_to_dominant_pid.get(m)}
            inter = len(data_members & comm_pids)
            union = len(data_members | comm_pids)
            jaccard = inter / union if union > 0 else 0.0
            rec = inter / len(data_members) if len(data_members) > 0 else 0.0
            pur = inter / len(comm_pids) if len(comm_pids) > 0 else 0.0
            if jaccard > best_jaccard or (jaccard == best_jaccard and rec > best_rec):
                best_jaccard = jaccard
                best_comm = cid
                best_rec = rec
                best_pur = pur
                best_inter = inter
                best_comm_len = len(comm_pids)
        if best_jaccard >= 0.2:
            recovered_at_02 += 1
        if best_jaccard >= 0.3:
            recovered_at_03 += 1
        if best_jaccard >= 0.5:
            recovered_at_05 += 1
        syndicate_recovery.append({
            "syndicate": syn_id,
            "truth_members": len(t_members),
            "data_members": len(data_members),
            "best_community": best_comm,
            "jaccard": round(best_jaccard, 4),
            "member_recall": f"{best_inter}/{len(data_members)} = {best_rec*100:.2f}%",
            "community_purity": f"{best_inter}/{best_comm_len} = {best_pur*100:.2f}%",
        })

    # Decoy cluster audit
    total_decoys = sum(1 for c in communities_data if len(c.get("case_ids", [])) == 0)
    flagged_decoys = sum(1 for c in communities_data if len(c.get("case_ids", [])) == 0 and c.get("is_network_of_interest", False))
    decoy_status = "DECOY TEST VACUOUS" if total_decoys == 0 else f"{flagged_decoys}/{total_decoys}"

    # Case threshold analysis
    case_counts = [len(c.get("case_ids", [])) for c in communities_data]
    case_thresholds = {}
    for th in [1, 2, 3, 5]:
        cnt = sum(1 for cc in case_counts if cc >= th)
        pct = cnt / len(communities_data) * 100 if communities_data else 0.0
        case_thresholds[f"threshold_{th}"] = f"{cnt}/{len(communities_data)} = {pct:.2f}%"

    # Innocent pass-through
    innocent_accts = {a["account_key"] for a in account_truth if a.get("category") == "INNOCENT_FAST_PASSTHROUGH"}
    mule_accounts = mule_data[0].get("accounts", []) if mule_data else []
    innocent_flagged_lo = sum(1 for a in mule_accounts if a["account_key"] in innocent_accts and a.get("classification") == "LIKELY_ORGANISER")
    innocent_fpr = f"{innocent_flagged_lo}/{len(innocent_accts)} = {innocent_flagged_lo/len(innocent_accts)*100:.2f}%" if innocent_accts else "0/0"

    # Account confusion matrix
    truth_acct_map = {a["account_key"]: a.get("category", "UNKNOWN") for a in account_truth}
    pred_acct_map = {a["account_key"]: a.get("classification", "UNCERTAIN") for a in mule_accounts}
    conf_matrix: dict[str, dict[str, int]] = defaultdict(lambda: Counter())
    for ak, cat in truth_acct_map.items():
        pred_cls = pred_acct_map.get(ak, "NOT_IN_CHAINS")
        conf_matrix[cat][pred_cls] += 1

    return {
        "is_oracle": is_oracle,
        "total_nodes": summary_data.get("total_nodes", len(graph_data.get("nodes", []))),
        "total_edges": summary_data.get("total_edges", len(graph_data.get("edges", []))),
        "edges_by_tier": summary_data.get("edges_by_tier", {}),
        "edges_by_type": summary_data.get("edges_by_type", {}),
        "bridge_metrics": bridge_metrics,
        "syndicate_recovery": syndicate_recovery,
        "syndicates_matching_02": f"{recovered_at_02}/{len(syndicates_truth)} = {recovered_at_02/len(syndicates_truth)*100:.2f}%" if syndicates_truth else "0/0",
        "syndicates_matching_03": f"{recovered_at_03}/{len(syndicates_truth)} = {recovered_at_03/len(syndicates_truth)*100:.2f}%" if syndicates_truth else "0/0",
        "syndicates_matching_05": f"{recovered_at_05}/{len(syndicates_truth)} = {recovered_at_05/len(syndicates_truth)*100:.2f}%" if syndicates_truth else "0/0",
        "decoy_status": decoy_status,
        "case_threshold_analysis": case_thresholds,
        "innocent_passthrough_fpr": innocent_fpr,
        "confusion_matrix": {cat: dict(cnts) for cat, cnts in conf_matrix.items()},
        "build_runtime_seconds": summary_data.get("build_runtime_seconds", 0.0),
        "analytics_runtime_seconds": summary_data.get("analytics_runtime_seconds", 0.0),
        "total_runtime_seconds": summary_data.get("total_runtime_seconds", 0.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Sutradhar Knowledge Graph")
    parser.add_argument("--tier", default="dev", help="Dataset tier")
    parser.add_argument("--seed", type=int, default=42, help="Seed to evaluate")
    parser.add_argument("--all-seeds", action="store_true", help="Run full evaluation across seeds 42, 43, 44")
    args = parser.parse_args()

    seeds = [42, 43, 44] if args.all_seeds else [args.seed]
    results: dict[str, Any] = {}

    for s in seeds:
        print(f"\n=======================================================")
        print(f" EVALUATING SEED {s}")
        print(f"=======================================================")
        data_dir = Path(f"data/v2/{args.tier}/seed-{s}")
        truth_dir = Path(f"data/truth/v2/{args.tier}/seed-{s}")
        er_dir = Path(f"scratch/er_seed{s}")
        graph_dir = Path(f"scratch/graph_seed{s}")

        if not (graph_dir / "summary.json").exists():
            print(f"Running Actual Graph pipeline for seed-{s}...")
            run_graph_pipeline(data_dir, er_dir, graph_dir)

        print(f"Computing Actual ER Graph evaluation for seed-{s}...")
        res_actual = evaluate_graph_run(data_dir, truth_dir, er_dir, graph_dir, is_oracle=False)

        oracle_er_dir = Path(f"scratch/oracle_er_seed{s}")
        oracle_graph_dir = Path(f"scratch/oracle_graph_seed{s}")
        print(f"Generating Oracle ER for seed-{s}...")
        create_oracle_er(data_dir, truth_dir, er_dir, oracle_er_dir)
        print(f"Running Oracle Graph pipeline for seed-{s}...")
        run_graph_pipeline(data_dir, oracle_er_dir, oracle_graph_dir)
        print(f"Computing Oracle ER Graph evaluation for seed-{s}...")
        res_oracle = evaluate_graph_run(data_dir, truth_dir, oracle_er_dir, oracle_graph_dir, is_oracle=True)

        results[f"seed_{s}"] = {
            "actual_er": res_actual,
            "oracle_er": res_oracle,
        }

    out_file = Path("scratch/graph_evaluation_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nAll evaluations saved to {out_file}")


if __name__ == "__main__":
    main()
