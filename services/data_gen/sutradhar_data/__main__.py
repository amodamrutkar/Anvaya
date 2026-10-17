"""
CLI entry point for Sutradhar data generation.

Usage: python -m sutradhar_data.generate --version v0|v1|v2|v3 --seed N --out data/
"""

import argparse
import json
import sys

from .generate import generate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Sutradhar synthetic dataset",
        prog="python -m sutradhar_data.generate",
    )
    parser.add_argument(
        "--version", type=str, default="v0",
        choices=["v0", "v1", "v2", "v3"],
        help="Dataset version (controls noise level and scale)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for deterministic generation",
    )
    parser.add_argument(
        "--out", type=str, default="data",
        help="Output directory (default: data/)",
    )

    args = parser.parse_args()
    summary = generate_dataset(
        version=args.version,
        seed=args.seed,
        out_dir=args.out,
    )

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\n[OK] Generated {summary['total_records']} records for "
          f"{summary['total_persons']} persons ({args.version}, seed={args.seed})")


if __name__ == "__main__":
    main()
