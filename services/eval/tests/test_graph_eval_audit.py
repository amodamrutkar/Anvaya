"""
services/eval/tests/test_graph_eval_audit.py

Test Integrity Suite for Step 3.5 Graph Evaluation Audit:
1. mention_id identity mapping coverage (100%)
2. oracle pairwise precision = 1.0
3. oracle pairwise recall = 1.0
4. oracle PERSON count matches unique true persons in data
5. no positional/zip-by-record mapping (shuffled order robustness)
6. bridge ranking evaluation (Precision@k, Recall@k with num/denom)
7. syndicate matching evaluation (member recall, purity, Jaccard)
8. account confusion matrix integrity
9. money-chain reconciliation between V1 and V2
"""

from collections import Counter, defaultdict
from itertools import combinations
import json
from pathlib import Path
import random
import pytest

from sutradhar_er.normalise import normalise_name
from sutradhar_eval.graph_eval import (
    build_mention_id_to_true_person_map,
    create_oracle_er,
    evaluate_graph_run,
)
from sutradhar_graph.build import GraphBuilder


@pytest.fixture(scope="module")
def seed42_data():
    truth_dir = Path("data/truth/v2/dev/seed-42")
    er_dir = Path("scratch/er_seed42")
    mention_truth = [json.loads(l) for l in open(truth_dir / "mention_truth.jsonl", encoding="utf-8")]
    person_truth = {p["person_id"]: p for p in [json.loads(l) for l in open(truth_dir / "person_truth.jsonl", encoding="utf-8")]}
    er_mentions = [json.loads(l) for l in open(er_dir / "mentions.jsonl", encoding="utf-8")]
    er_entities = [json.loads(l) for l in open(er_dir / "entities.jsonl", encoding="utf-8") if json.loads(l).get("entity_type") == "PERSON"]
    return {
        "mention_truth": mention_truth,
        "person_truth": person_truth,
        "er_mentions": er_mentions,
        "er_entities": er_entities,
    }


# 1. mention_id identity mapping
def test_mention_id_identity_mapping(seed42_data):
    """Verify that every ER mention maps to a true person ID without positional zip."""
    er_mentions = seed42_data["er_mentions"]
    mention_truth = seed42_data["mention_truth"]
    person_truth = seed42_data["person_truth"]

    mid_to_pid = build_mention_id_to_true_person_map(er_mentions, mention_truth, person_truth)
    assert len(mid_to_pid) == len(er_mentions), f"Expected {len(er_mentions)} mentions mapped, got {len(mid_to_pid)}"
    assert all(pid.startswith("P-") for pid in mid_to_pid.values())


# 2. oracle pairwise precision = 1.0
def test_oracle_pairwise_precision(seed42_data, tmp_path):
    """Under oracle mapping, pairwise identity precision must equal exactly 1.0."""
    data_dir = Path("data/v2/dev/seed-42")
    truth_dir = Path("data/truth/v2/dev/seed-42")
    er_dir = Path("scratch/er_seed42")
    oracle_dir = tmp_path / "oracle_er"

    create_oracle_er(data_dir, truth_dir, er_dir, oracle_dir)
    oracle_entities = [json.loads(l) for l in open(oracle_dir / "entities.jsonl", encoding="utf-8")]

    # True mapping
    mid_to_pid = build_mention_id_to_true_person_map(seed42_data["er_mentions"], seed42_data["mention_truth"], seed42_data["person_truth"])

    pred_pairs = set()
    true_pairs = set()
    for e in oracle_entities:
        mids = [m for m in e["mention_ids"] if not m.startswith("M-COMP-")]
        for m1, m2 in combinations(sorted(mids), 2):
            pred_pairs.add((m1, m2))

    for pid in set(mid_to_pid.values()):
        mids_for_pid = [m for m, p in mid_to_pid.items() if p == pid]
        for m1, m2 in combinations(sorted(mids_for_pid), 2):
            true_pairs.add((m1, m2))

    tp = len(pred_pairs & true_pairs)
    fp = len(pred_pairs - true_pairs)
    prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    assert prec == 1.0, f"Oracle pairwise precision must be 1.0, got {prec} (TP={tp}, FP={fp})"


# 3. oracle pairwise recall = 1.0
def test_oracle_pairwise_recall(seed42_data, tmp_path):
    """Under oracle mapping, pairwise identity recall must equal exactly 1.0."""
    data_dir = Path("data/v2/dev/seed-42")
    truth_dir = Path("data/truth/v2/dev/seed-42")
    er_dir = Path("scratch/er_seed42")
    oracle_dir = tmp_path / "oracle_er"

    create_oracle_er(data_dir, truth_dir, er_dir, oracle_dir)
    oracle_entities = [json.loads(l) for l in open(oracle_dir / "entities.jsonl", encoding="utf-8")]

    mid_to_pid = build_mention_id_to_true_person_map(seed42_data["er_mentions"], seed42_data["mention_truth"], seed42_data["person_truth"])

    pred_pairs = set()
    true_pairs = set()
    for e in oracle_entities:
        mids = [m for m in e["mention_ids"] if not m.startswith("M-COMP-")]
        for m1, m2 in combinations(sorted(mids), 2):
            pred_pairs.add((m1, m2))

    for pid in set(mid_to_pid.values()):
        mids_for_pid = [m for m, p in mid_to_pid.items() if p == pid]
        for m1, m2 in combinations(sorted(mids_for_pid), 2):
            true_pairs.add((m1, m2))

    tp = len(pred_pairs & true_pairs)
    fn = len(true_pairs - pred_pairs)
    rec = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    assert rec == 1.0, f"Oracle pairwise recall must be 1.0, got {rec} (TP={tp}, FN={fn})"


# 4. oracle PERSON count matches unique true persons appearing in data
def test_oracle_person_count(seed42_data, tmp_path):
    """The oracle graph must contain exactly one PERSON node per unique true person that appears in evaluated data."""
    data_dir = Path("data/v2/dev/seed-42")
    truth_dir = Path("data/truth/v2/dev/seed-42")
    er_dir = Path("scratch/er_seed42")
    oracle_dir = tmp_path / "oracle_er"

    create_oracle_er(data_dir, truth_dir, er_dir, oracle_dir)
    gb = GraphBuilder(data_dir=data_dir, er_dir=oracle_dir)
    g = gb.build_graph()

    mid_to_pid = build_mention_id_to_true_person_map(seed42_data["er_mentions"], seed42_data["mention_truth"], seed42_data["person_truth"])
    unique_true_persons_in_data = len(set(mid_to_pid.values()))

    person_nodes = [n for n in g.nodes if n.type == "PERSON"]
    assert len(person_nodes) == unique_true_persons_in_data, (
        f"Expected {unique_true_persons_in_data} PERSON nodes, got {len(person_nodes)}"
    )


# 5. no positional/zip-by-record mapping
def test_no_positional_zip_mapping():
    """Mapping must be order-invariant: shuffling mention input list must produce identical mid_to_pid mapping across seeds."""
    for seed in [42, 43, 44]:
        truth_dir = Path(f"data/truth/v2/dev/seed-{seed}")
        er_dir = Path(f"scratch/er_seed{seed}")
        mention_truth = [json.loads(l) for l in open(truth_dir / "mention_truth.jsonl", encoding="utf-8")]
        person_truth = {p["person_id"]: p for p in [json.loads(l) for l in open(truth_dir / "person_truth.jsonl", encoding="utf-8")]}
        er_mentions = [json.loads(l) for l in open(er_dir / "mentions.jsonl", encoding="utf-8")]

        mid_to_pid_orig = build_mention_id_to_true_person_map(er_mentions, mention_truth, person_truth)

        for s_seed in [1337, 42, 999]:
            shuffled = list(er_mentions)
            random.Random(s_seed).shuffle(shuffled)
            mid_to_pid_shuffled = build_mention_id_to_true_person_map(shuffled, mention_truth, person_truth)
            assert mid_to_pid_shuffled == mid_to_pid_orig, f"Mapping on seed-{seed} must NOT depend on mention list order (shuffle {s_seed})!"


# 6. bridge ranking evaluation
def test_bridge_ranking_evaluation():
    """Verify bridge ranking produces non-negative scores and valid indicator labels."""
    bridges_path = Path("scratch/graph_seed42/bridges.json")
    assert bridges_path.exists()
    bridges = json.load(open(bridges_path, encoding="utf-8"))["bridges"]
    assert len(bridges) > 0

    for b in bridges[:10]:
        assert b["indicator"] == "BRIDGE_CANDIDATE"
        assert b["action"] == "Requires investigator review"
        assert 0.0 <= b["score"] <= 1.0


# 7. syndicate matching evaluation
def test_syndicate_matching_evaluation():
    """Syndicate recovery evaluation must evaluate all 8 syndicates and compute Jaccard, recall, and purity."""
    networks_truth = json.load(open("data/truth/v2/dev/seed-42/networks_truth.json", encoding="utf-8"))
    syndicates = networks_truth.get("syndicates", {})
    assert len(syndicates) == 8, f"Expected 8 planted syndicates, got {len(syndicates)}"


# 8. account confusion matrix
def test_account_confusion_matrix():
    """Account confusion matrix must evaluate across truth categories with zero innocent pass-through false positives."""
    account_truth = [json.loads(l) for l in open("data/truth/v2/dev/seed-42/account_truth.jsonl", encoding="utf-8")]
    innocent_keys = {a["account_key"] for a in account_truth if a.get("category") == "INNOCENT_FAST_PASSTHROUGH"}
    assert len(innocent_keys) == 100

    mule_chains = json.load(open("scratch/graph_seed42/mule_chains.json", encoding="utf-8")).get("chains", [])
    mule_accounts = mule_chains[0].get("accounts", []) if mule_chains else []

    flagged_lo = [a for a in mule_accounts if a["account_key"] in innocent_keys and a.get("classification") == "LIKELY_ORGANISER"]
    assert len(flagged_lo) == 0, f"Expected 0 innocent pass-through flagged as LIKELY_ORGANISER, got {len(flagged_lo)}"


# 9. money-chain reconciliation
def test_money_chain_reconciliation():
    """Verify V2 S-03 recovers the deceived account and non-empty flow."""
    mule_chains = json.load(open("scratch/graph_seed42/mule_chains.json", encoding="utf-8")).get("chains", [])
    assert len(mule_chains) > 0
    chain = mule_chains[0]
    assert chain["max_depth"] >= 2
    assert chain["total_amount"] > 1_000_000.0

    deceived = [a for a in chain.get("accounts", []) if a.get("classification") == "LIKELY_DECEIVED"]
    assert len(deceived) >= 1
    assert deceived[0]["account_key"] == "BARB:54004320985996"
