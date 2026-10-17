"""Main entry point — CLI for the entity resolution pipeline.

Usage:
    python -m sutradhar_er.run --data <dir> --out <dir> [--decisions <file>]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

from .block import generate_candidate_pairs
from .cluster import cluster_mentions
from .config import load_config
from .decisions import apply_decisions, load_decisions
from .explain import generate_all_explanations
from .extract import extract_mentions, load_records

logger = logging.getLogger("sutradhar_er")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def write_jsonl(items: list, path: Path) -> None:
    """Write a list of Pydantic models to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for item in items:
            if hasattr(item, "model_dump"):
                fh.write(json.dumps(item.model_dump(), ensure_ascii=False) + "\n")
            else:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")


def run_pipeline(
    data_dir: Path,
    out_dir: Path,
    decisions_path: Path | None = None,
    config_path: Path | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Run the full entity resolution pipeline.

    Returns a summary dict with stats.
    """
    setup_logging(verbose)
    t0 = time.time()

    # Load config
    cfg = load_config(config_path)
    logger.info(f"Config loaded. LLM provider: {cfg.get('llm', {}).get('provider', 'none')}")

    # Stage 1: Load records
    records = load_records(data_dir)
    if not records:
        logger.warning(f"No records found in {data_dir}")
        return {"status": "empty", "records": 0}

    # Stage 2: Extract mentions
    cache_path = out_dir / cfg.get("llm", {}).get("cache_path", "llm_cache.jsonl")
    mentions, validation_stats = extract_mentions(records, cfg, cache_path)
    if not mentions:
        logger.warning("No mentions extracted")
        return {"status": "no_mentions", "records": len(records)}

    # Stage 3: Blocking
    candidate_pairs = generate_candidate_pairs(mentions, cfg)

    # Stage 4: Scoring
    mention_map = {m.mention_id: m for m in mentions}
    decisions = load_decisions(decisions_path)

    from .score import score_all_pairs

    links = score_all_pairs(candidate_pairs, mention_map, cfg, decisions)

    # Stage 5: Clustering
    entities, links = cluster_mentions(mentions, links, cfg)

    # Stage 6: Apply decisions (if any)
    if decisions:
        entities, links = apply_decisions(entities, links, decisions)

    # Stage 7: Explanations
    # Detect hero mentions (Rakesh Pawar variants for Marathi translation)
    hero_mention_ids: set[str] = set()
    for m in mentions:
        if "rakesh" in m.name_norm.lower() and "pavar" in m.name_norm.lower():
            hero_mention_ids.add(m.mention_id)
    links = generate_all_explanations(links, mention_map, hero_mention_ids)

    # Stage 8: Write output
    out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(mentions, out_dir / "mentions.jsonl")
    write_jsonl(entities, out_dir / "entities.jsonl")
    write_jsonl(links, out_dir / "links.jsonl")

    elapsed = time.time() - t0

    # Summary
    person_entities = [e for e in entities if e.entity_type == "PERSON"]
    auto_links = [l for l in links if l.band == "AUTO"]
    review_links = [l for l in links if l.band == "REVIEW"]

    summary = {
        "status": "ok",
        "elapsed_seconds": round(elapsed, 2),
        "records": len(records),
        "mentions": len(mentions),
        "candidate_pairs": len(candidate_pairs),
        "links_total": len(links),
        "links_auto": len(auto_links),
        "links_review": len(review_links),
        "entities_person": len(person_entities),
        "entities_phone": sum(1 for e in entities if e.entity_type == "PHONE"),
        "entities_account": sum(1 for e in entities if e.entity_type == "ACCOUNT"),
        "entities_vehicle": sum(1 for e in entities if e.entity_type == "VEHICLE"),
        "validation_stats": {
            k: {"accepted": v.accepted, "rejected": v.rejected} for k, v in validation_stats.items()
        },
    }

    logger.info(f"Pipeline complete in {elapsed:.2f}s")
    logger.info(json.dumps(summary, indent=2))

    # Write summary
    with open(out_dir / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    return summary


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sutradhar_er",
        description="Sutradhar Entity Resolution — cross-agency identity resolution",
    )
    parser.add_argument(
        "--data",
        required=True,
        type=Path,
        help="Path to data directory (e.g. data/v1 or contracts/fixtures/data)",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Output directory for mentions.jsonl, entities.jsonl, links.jsonl",
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=None,
        help="Path to decisions.jsonl (reviewer must-link/cannot-link)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config.yaml (defaults to bundled config)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    summary = run_pipeline(
        data_dir=args.data,
        out_dir=args.out,
        decisions_path=args.decisions,
        config_path=args.config,
        verbose=args.verbose,
    )

    if summary.get("status") != "ok":
        sys.exit(1)


if __name__ == "__main__":
    main()
