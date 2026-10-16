"""
Tests for sutradhar_eval package.

Verifies:
- Evaluation harness CLI and programmatic execution
- Metric output shape matches PRD Section 8.5
- Metric calculation with mock predictions
- Fairness calculation across roles and surnames
"""

import json
from pathlib import Path

import pytest

from sutradhar_data.generate import generate_dataset
from sutradhar_eval.run import run_evaluation


def test_eval_metric_shape(tmp_path: Path) -> None:
    """Evaluation output must match PRD Section 8.5 specification exactly."""
    data_dir = tmp_path / "data"
    truth_dir = tmp_path / "data" / "truth" / "v0"
    artifacts_dir = tmp_path / "artifacts"
    out_metrics = artifacts_dir / "metrics.json"

    # Generate synthetic v0 data + truth
    generate_dataset(version="v0", seed=42, out_dir=str(data_dir))

    # Run evaluation
    metrics = run_evaluation(
        data_dir=str(data_dir / "v0"),
        truth_dir=str(truth_dir),
        artifacts_dir=str(artifacts_dir),
        out_path=str(out_metrics),
    )

    assert out_metrics.exists()
    assert metrics["dataset_version"] == "v0"

    # Check top-level keys
    for k in ["dataset_version", "er", "network", "mule", "time_saved", "fairness"]:
        assert k in metrics, f"Missing key '{k}' in metrics"

    # Check ER metrics structure
    er = metrics["er"]
    for k in ["auto_precision", "auto_recall", "overall_precision", "overall_recall", "overall_f1", "by_difficulty", "wrong_merge_rate", "review_share"]:
        assert k in er, f"Missing ER key '{k}'"

    assert "easy" in er["by_difficulty"]
    assert "hard" in er["by_difficulty"]

    # Check network metrics structure
    net = metrics["network"]
    assert net["planted"] == 3
    assert net["bridges_planted"] == 2

    # Check mule metrics structure
    mule = metrics["mule"]
    for k in ["max_depth", "layer1_baseline_depth", "recruiter_detected", "deceived_precision"]:
        assert k in mule, f"Missing mule key '{k}'"

    # Check fairness
    assert "passed" in metrics["fairness"]
    assert metrics["fairness"]["unique_surnames"] >= 20


def test_eval_with_mock_predictions(tmp_path: Path) -> None:
    """When given perfect predictions, precision and recall should be 1.0."""
    data_dir = tmp_path / "data"
    truth_dir = tmp_path / "data" / "truth" / "v0"
    artifacts_dir = tmp_path / "artifacts"
    out_metrics = artifacts_dir / "metrics.json"

    generate_dataset(version="v0", seed=42, out_dir=str(data_dir))

    # Read ground truth mentions
    mention_truth_file = truth_dir / "mention_truth.jsonl"
    mentions = [json.loads(line) for line in mention_truth_file.read_text(encoding="utf-8").splitlines() if line]

    # Group mentions by person_id to build perfect entities
    clusters: dict[str, list[str]] = {}
    for m in mentions:
        clusters.setdefault(m["person_id"], []).append(m["mention_id"])

    entities = []
    for pid, mids in clusters.items():
        entities.append({
            "entity_id": f"ENT-{pid}",
            "mention_ids": mids,
        })

    # Write mock predictions
    er_dir = artifacts_dir / "er"
    er_dir.mkdir(parents=True, exist_ok=True)
    with open(er_dir / "entities.jsonl", "w", encoding="utf-8") as f:
        for ent in entities:
            f.write(json.dumps(ent) + "\n")

    # Run eval
    metrics = run_evaluation(
        data_dir=str(data_dir / "v0"),
        truth_dir=str(truth_dir),
        artifacts_dir=str(artifacts_dir),
        out_path=str(out_metrics),
    )

    # Perfect prediction should yield 1.0 precision and recall
    assert metrics["er"]["overall_precision"] == 1.0
    assert metrics["er"]["overall_recall"] == 1.0
    assert metrics["er"]["wrong_merge_rate"] == 0.0
