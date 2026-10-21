"""
Sutradhar Evaluation Harness.

Computes metrics from pipeline artifacts against truth files,
producing artifacts/metrics.json in the shape defined by main PRD Section 8.5.

CLI:
python -m sutradhar_eval.run \
    --data data/v1 \
    --truth data/truth/v1 \
    --artifacts artifacts \
    --out artifacts/metrics.json
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL file into a list of dicts."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _read_json(path: Path) -> Any:
    """Read a JSON file."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _compute_er_metrics(
    truth_mentions: list[dict],
    pred_entities: list[dict],
    pred_links: list[dict],
) -> dict:
    """
    Compute ER metrics: pairwise precision, recall, F1, wrong-merge rate,
    review share, split by difficulty.
    """
    # Build truth clusters: person_id -> set of mention_ids
    truth_clusters: dict[str, set] = defaultdict(set)
    mention_difficulty: dict[str, list[str]] = {}

    for mention in truth_mentions:
        truth_clusters[mention["person_id"]].add(mention["mention_id"])
        mention_difficulty[mention["mention_id"]] = mention.get("difficulty_tags", [])

    # Build predicted clusters: entity_id -> set of mention_ids
    pred_clusters: dict[str, set] = defaultdict(set)

    for entity in pred_entities:
        if entity.get("entity_type") and entity.get("entity_type") != "PERSON":
            continue
        for mention_id in entity.get("mention_ids", []):
            pred_clusters[entity["entity_id"]].add(mention_id)

    # Compute pairwise TP, FP, FN
    def _pairs(cluster: set) -> set:
        sorted_cluster = sorted(cluster)
        return {
            (sorted_cluster[i], sorted_cluster[j])
            for i in range(len(sorted_cluster))
            for j in range(i + 1, len(sorted_cluster))
        }

    truth_pairs = set()
    for cluster in truth_clusters.values():
        truth_pairs |= _pairs(cluster)

    pred_pairs = set()
    for cluster in pred_clusters.values():
        pred_pairs |= _pairs(cluster)

    tp = len(truth_pairs & pred_pairs)
    fp = len(pred_pairs - truth_pairs)
    fn = len(truth_pairs - pred_pairs)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    wrong_merge_rate = fp / (tp + fp) if (tp + fp) > 0 else 0.0

    # Review share
    review_count = sum(1 for link in pred_links if link.get("band") == "REVIEW")
    total_links = len(pred_links) if pred_links else 1
    review_share = review_count / total_links

    # Auto-band metrics
    auto_links = [link for link in pred_links if link.get("band") == "AUTO"]

    auto_pred_pairs_set = set()

    for link in auto_links:
        a = link.get("a_mention_id", "")
        b = link.get("b_mention_id", "")

        if a and b:
            pair = tuple(sorted([a, b]))
            auto_pred_pairs_set.add(pair)

    auto_tp = len(truth_pairs & auto_pred_pairs_set)
    auto_fp = len(auto_pred_pairs_set - truth_pairs)
    auto_fn = len(truth_pairs - auto_pred_pairs_set)

    auto_precision = auto_tp / (auto_tp + auto_fp) if (auto_tp + auto_fp) > 0 else 0.0
    auto_recall = auto_tp / (auto_tp + auto_fn) if (auto_tp + auto_fn) > 0 else 0.0

    # Split by difficulty
    hard_tags = {
        "translit",
        "alias",
        "initials",
        "missing_father",
        "collision",
        "old_phone",
        "script_mix",
        "word_order",
        "typo",
        "address_change",
        "age_drift",
    }

    easy_mentions = set()
    hard_mentions = set()

    for mention_id, tags in mention_difficulty.items():
        if set(tags) & hard_tags:
            hard_mentions.add(mention_id)
        else:
            easy_mentions.add(mention_id)

    # Easy/hard pairs
    def _classify_pairs(
        pairs: set,
        easy_set: set,
        hard_set: set,
    ) -> tuple:
        easy_pairs = {pair for pair in pairs if pair[0] in easy_set and pair[1] in easy_set}
        hard_pairs = pairs - easy_pairs
        return easy_pairs, hard_pairs

    easy_truth, hard_truth = _classify_pairs(
        truth_pairs,
        easy_mentions,
        hard_mentions,
    )
    easy_pred, hard_pred = _classify_pairs(
        pred_pairs,
        easy_mentions,
        hard_mentions,
    )

    easy_tp = len(easy_truth & easy_pred)
    easy_fp = len(easy_pred - easy_truth)
    easy_fn = len(easy_truth - easy_pred)

    hard_tp = len(hard_truth & hard_pred)
    hard_fp = len(hard_pred - hard_truth)
    hard_fn = len(hard_truth - hard_pred)

    easy_precision = easy_tp / (easy_tp + easy_fp) if (easy_tp + easy_fp) > 0 else 0.0
    easy_recall = easy_tp / (easy_tp + easy_fn) if (easy_tp + easy_fn) > 0 else 0.0

    hard_precision = hard_tp / (hard_tp + hard_fp) if (hard_tp + hard_fp) > 0 else 0.0
    hard_recall = hard_tp / (hard_tp + hard_fn) if (hard_tp + hard_fn) > 0 else 0.0

    return {
        "auto_precision": round(auto_precision, 4),
        "auto_recall": round(auto_recall, 4),
        "overall_precision": round(precision, 4),
        "overall_recall": round(recall, 4),
        "overall_f1": round(f1, 4),
        "by_difficulty": {
            "easy": {
                "precision": round(easy_precision, 4),
                "recall": round(easy_recall, 4),
            },
            "hard": {
                "precision": round(hard_precision, 4),
                "recall": round(hard_recall, 4),
            },
        },
        "wrong_merge_rate": round(wrong_merge_rate, 4),
        "review_share": round(review_share, 4),
    }


def _compute_network_metrics(
    truth_networks: dict,
    pred_communities: list[dict],
    pred_roles: list[dict],
    pred_bridges: list[dict],
) -> dict:
    """Compute network recovery metrics."""
    planted = 3  # A, B, C
    recovered = 0

    # Check if predicted communities overlap with truth networks
    truth_member_sets = {}

    for network_key in ["A", "B", "C"]:
        network = truth_networks.get(network_key, {})
        truth_member_sets[network_key] = set(network.get("members", []))

    for _network_key, truth_members in truth_member_sets.items():
        if not truth_members:
            continue

        # Find best matching community
        best_overlap = 0.0

        for community in pred_communities:
            pred_members = set(community.get("member_ids", []))

            if not pred_members:
                continue

            intersection = len(truth_members & pred_members)
            union = len(truth_members | pred_members)
            overlap = intersection / union if union > 0 else 0.0
            best_overlap = max(best_overlap, overlap)

        if best_overlap >= 0.6:
            recovered += 1

    # Kingpin rank
    kingpin_rank = -1
    leader_id = truth_networks.get("B", {}).get("leader_id")

    if leader_id and pred_roles:
        kingpin_candidates = sorted(
            [role for role in pred_roles if role.get("role") == "KINGPIN_CANDIDATE"],
            key=lambda role: role.get("score", 0),
            reverse=True,
        )

        for index, role in enumerate(kingpin_candidates):
            if role.get("entity_id") == leader_id:
                kingpin_rank = index + 1
                break

    # Bridges found
    truth_bridge_ids = set()

    for bridge_key in ["bridge_1", "bridge_2"]:
        bridge = truth_networks.get(bridge_key, {})

        if bridge.get("person_id"):
            truth_bridge_ids.add(bridge["person_id"])

    pred_bridge_ids = set()

    for bridge in pred_bridges:
        linked = bridge.get("linked_person")

        if linked:
            pred_bridge_ids.add(linked)

    bridges_found = len(truth_bridge_ids & pred_bridge_ids)

    return {
        "planted": planted,
        "recovered": recovered,
        "kingpin_rank": kingpin_rank,
        "bridges_found": bridges_found,
        "bridges_planted": len(truth_bridge_ids),
    }


def _compute_mule_metrics(
    truth_accounts: list[dict],
    pred_chains: list[dict],
) -> dict:
    """Compute mule chain tracing metrics."""
    max_depth = 0
    recruiter_detected = False
    deceived_tp = 0
    deceived_fp = 0

    truth_acct_class = {}

    for account in truth_accounts:
        truth_acct_class[account["account_key"]] = account.get(
            "class",
            "NEUTRAL",
        )

    for chain in pred_chains:
        depth = chain.get("max_depth", 0)
        max_depth = max(max_depth, depth)

        if chain.get("recruiter_candidates"):
            recruiter_detected = True

        for account in chain.get("accounts", []):
            account_key = account.get("account_id", "")
            pred_class = account.get("classification", "")
            truth_class = truth_acct_class.get(
                account_key,
                "NEUTRAL",
            )

            if pred_class == "LIKELY_DECEIVED":
                if truth_class == "DECEIVED":
                    deceived_tp += 1
                else:
                    deceived_fp += 1

    deceived_precision = (
        deceived_tp / (deceived_tp + deceived_fp) if (deceived_tp + deceived_fp) > 0 else 0.0
    )

    return {
        "max_depth": max_depth,
        "layer1_baseline_depth": 1,
        "recruiter_detected": recruiter_detected,
        "deceived_precision": round(deceived_precision, 4),
    }


def _compute_fairness(truth_persons: list[dict]) -> dict:
    """
    Check that role is not correlated with surname community.
    Simple chi-squared-like independence check.
    """
    # Group by surname (last word of canonical_name) and role
    surname_role: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for person in truth_persons:
        name = person.get("canonical_name", "")
        parts = name.split()
        surname = parts[-1] if parts else "Unknown"
        role = person.get("role", "NEUTRAL")
        surname_role[surname][role] += 1

    # Check if any surname is disproportionately assigned criminal roles
    criminal_roles = {
        "RECRUITER",
        "CONTROLLER",
        "LEADER",
        "BROKER",
        "MEMBER",
        "COURIER",
        "FINANCIER",
    }

    concerns = []

    for surname, roles in surname_role.items():
        total = sum(roles.values())
        criminal_count = sum(roles.get(role, 0) for role in criminal_roles)

        if total >= 3 and criminal_count / total > 0.8:
            concerns.append(
                {
                    "surname": surname,
                    "total": total,
                    "criminal_count": criminal_count,
                    "ratio": round(criminal_count / total, 2),
                }
            )

    return {
        "passed": len(concerns) == 0,
        "concerns": concerns,
        "unique_surnames": len(surname_role),
    }


def run_evaluation(
    data_dir: str,
    truth_dir: str,
    artifacts_dir: str,
    out_path: str,
    version: str | None = None,
) -> dict:
    """
    Run the full evaluation harness.

    Args:
        data_dir: Path to data version (e.g., data/v1)
        truth_dir: Path to truth (e.g., data/truth/v1)
        artifacts_dir: Path to pipeline artifacts
        out_path: Where to write metrics.json
    """
    data = Path(data_dir)
    truth = Path(truth_dir)
    arts = Path(artifacts_dir)
    out = Path(out_path)

    # Read truth
    mention_truth = _read_jsonl(truth / "mention_truth.jsonl")
    person_truth = _read_jsonl(truth / "person_truth.jsonl")
    account_truth = _read_jsonl(truth / "account_truth.jsonl")
    networks_truth = _read_json(truth / "networks_truth.json")

    # Read predictions (may not exist yet)
    er_dir = arts / "er" if (arts / "er" / "entities.jsonl").exists() else arts
    pred_entities = _read_jsonl(er_dir / "entities.jsonl")
    pred_links = _read_jsonl(er_dir / "links.jsonl")
    pred_mentions = _read_jsonl(er_dir / "mentions.jsonl")

    pred_communities = _read_json(arts / "graph" / "communities.json")
    if isinstance(pred_communities, dict):
        pred_communities = pred_communities.get("communities", [])

    pred_roles = _read_json(arts / "graph" / "roles.json")
    if isinstance(pred_roles, dict):
        pred_roles = pred_roles.get("roles", [])

    pred_bridges = _read_json(arts / "graph" / "bridges.json")
    if isinstance(pred_bridges, dict):
        pred_bridges = pred_bridges.get("bridges", [])

    pred_chains = _read_json(arts / "graph" / "mule_chains.json")
    if isinstance(pred_chains, dict):
        pred_chains = pred_chains.get("chains", [])

    # Detect dataset version from path or explicit parameter
    if version:
        detected_version = version
    else:
        m = re.search(r"(v\d+)", str(data))
        detected_version = m.group(1) if m else (data.name if data.name.startswith("v") else "v0")

    # Align extracted mention IDs with truth mentions if pipeline IDs use local counter
    pred_mids = {mid for e in pred_entities for mid in e.get("mention_ids", [])}
    truth_mids = {m.get("mention_id") for m in mention_truth}
    if pred_mids and truth_mids and not (pred_mids & truth_mids) and pred_mentions:
        pred_by_rec = defaultdict(list)
        for pm in pred_mentions:
            pred_by_rec[pm.get("record_id")].append(pm)
        truth_by_rec = defaultdict(list)
        for tm in mention_truth:
            if tm.get("role") != "WITNESS":
                truth_by_rec[tm.get("record_id")].append(tm)
        mid_map = {}
        for rid, m_list in pred_by_rec.items():
            t_list = truth_by_rec.get(rid, [])
            for pm, tm in zip(m_list, t_list):
                mid_map[pm.get("mention_id")] = tm.get("mention_id")

        mapped_entities = []
        for e in pred_entities:
            mapped_mids = [mid_map[mid] for mid in e.get("mention_ids", []) if mid in mid_map]
            mapped_entities.append({**e, "mention_ids": mapped_mids})
        pred_entities = mapped_entities

        mapped_links = []
        for lnk in pred_links:
            a_mid = mid_map.get(lnk.get("a_mention_id"), lnk.get("a_mention_id"))
            b_mid = mid_map.get(lnk.get("b_mention_id"), lnk.get("b_mention_id"))
            mapped_links.append({**lnk, "a_mention_id": a_mid, "b_mention_id": b_mid})
        pred_links = mapped_links

    # Compute metrics
    er_metrics = _compute_er_metrics(
        mention_truth,
        pred_entities,
        pred_links,
    )

    network_metrics = _compute_network_metrics(
        networks_truth,
        pred_communities,
        pred_roles,
        pred_bridges,
    )

    mule_metrics = _compute_mule_metrics(
        account_truth,
        pred_chains,
    )

    fairness = _compute_fairness(person_truth)

    metrics = {
        "dataset_version": detected_version,
        "er": er_metrics,
        "network": network_metrics,
        "mule": mule_metrics,
        "time_saved": {
            "manual_minutes_estimate": 240,
            "system_seconds": 0,
        },
        "fairness": fairness,
    }

    # Write output
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            metrics,
            f,
            ensure_ascii=False,
            indent=2,
        )

    return metrics


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Sutradhar evaluation harness",
        prog="python -m sutradhar_eval.run",
    )

    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to data version directory (e.g., data/v1)",
    )

    parser.add_argument(
        "--truth",
        type=str,
        required=True,
        help="Path to truth directory (e.g., data/truth/v1)",
    )

    parser.add_argument(
        "--artifacts",
        type=str,
        default="artifacts",
        help="Path to pipeline artifacts directory",
    )

    parser.add_argument(
        "--out",
        type=str,
        default="artifacts/metrics.json",
        help="Output path for metrics JSON",
    )

    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Explicit dataset version (e.g. v1, v2). Overrides path inference.",
    )

    args = parser.parse_args()

    metrics = run_evaluation(
        data_dir=args.data,
        truth_dir=args.truth,
        artifacts_dir=args.artifacts,
        out_path=args.out,
        version=args.version,
    )

    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"\n[OK] Evaluation complete. Metrics written to {args.out}")


if __name__ == "__main__":
    main()
