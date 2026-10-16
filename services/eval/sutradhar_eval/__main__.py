"""
CLI entry point for Sutradhar evaluation harness.

Usage: python -m sutradhar_eval.run --data data/v1 --truth data/truth/v1 --artifacts artifacts --out artifacts/metrics.json
"""

import argparse
import json
import sys

from .run import run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Sutradhar evaluation harness",
        prog="python -m sutradhar_eval.run",
    )
    parser.add_argument(
        "--data", type=str, required=True,
        help="Path to data version directory (e.g., data/v1)",
    )
    parser.add_argument(
        "--truth", type=str, required=True,
        help="Path to truth directory (e.g., data/truth/v1)",
    )
    parser.add_argument(
        "--artifacts", type=str, default="artifacts",
        help="Path to pipeline artifacts directory",
    )
    parser.add_argument(
        "--out", type=str, default="artifacts/metrics.json",
        help="Output path for metrics JSON",
    )

    args = parser.parse_args()
    metrics = run_evaluation(
        data_dir=args.data,
        truth_dir=args.truth,
        artifacts_dir=args.artifacts,
        out_path=args.out,
    )

    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"\n[OK] Evaluation complete. Metrics written to {args.out}")


if __name__ == "__main__":
    main()
