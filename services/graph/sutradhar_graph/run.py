"""
Main Pipeline Runner for Sutradhar Graph and Network Analytics.

CLI: python -m sutradhar_graph.run --data data/v1 --er artifacts/er --out artifacts/graph

Generates artifacts/graph:
- graph.json
- communities.json
- roles.json
- bridges.json
- mule_chains.json
- dossiers/DOS-*.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .build import GraphBuilder
from .communities import detect_communities
from .roles import detect_roles
from .bridges import detect_bridges
from .mule import trace_mule_chains
from .dossier import generate_dossier, load_dossier_rules


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_pipeline(data_dir: str | Path,
                 er_dir: str | Path | None = None,
                 out_dir: str | Path = "artifacts/graph",
                 seed: int = 42) -> dict[str, Any]:
    """
    Execute full graph construction, community detection, role assignment,
    mule tracing, bridge detection, and dossier generation.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Build Graph
    builder = GraphBuilder(data_dir=data_dir, er_dir=er_dir)
    graph_data_model = builder.build_graph()
    graph_dict = builder.to_dict()

    _write_json(out_path / "graph.json", graph_dict)

    # 2. Detect Communities
    communities_models = detect_communities(graph_dict, seed=seed)
    communities_list = [c.model_dump() for c in communities_models]
    _write_json(out_path / "communities.json", {"communities": communities_list})

    # 3. Detect Roles
    roles_models = detect_roles(graph_dict, communities_models)
    roles_list = [r.model_dump() for r in roles_models]
    _write_json(out_path / "roles.json", {"roles": roles_list})

    # 4. Detect Bridges
    bridges_models = detect_bridges(graph_dict, communities_models)
    bridges_list = [b.model_dump() for b in bridges_models]
    _write_json(out_path / "bridges.json", {"bridges": bridges_list})

    # 5. Trace Mule Chains
    mule_chains_models = trace_mule_chains(graph_dict, data_dir=data_dir)
    mule_chains_list = [m.model_dump() for m in mule_chains_models]
    _write_json(out_path / "mule_chains.json", {"chains": mule_chains_list})

    # 6. Generate Dossiers
    dossiers_dir = out_path / "dossiers"
    dossiers_dir.mkdir(parents=True, exist_ok=True)
    dossiers_generated = []
    rules = load_dossier_rules()

    for comm in communities_models:
        dos = generate_dossier(
            community_id=comm.community_id,
            graph_data=graph_dict,
            communities=communities_models,
            roles=roles_models,
            records=builder.records,
            rules=rules,
        )
        dos_dict = dos.model_dump()
        _write_json(dossiers_dir / f"{dos.dossier_id}.json", dos_dict)
        dossiers_generated.append(dos.dossier_id)

    summary = {
        "status": "SUCCESS",
        "data_dir": str(data_dir),
        "er_dir": str(er_dir) if er_dir else None,
        "out_dir": str(out_dir),
        "total_nodes": len(graph_dict["nodes"]),
        "total_edges": len(graph_dict["edges"]),
        "total_communities": len(communities_list),
        "total_roles": len(roles_list),
        "total_bridges": len(bridges_list),
        "total_mule_chains": len(mule_chains_list),
        "dossiers": dossiers_generated,
    }

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Sutradhar Graph and Network Analytics Pipeline",
        prog="python -m sutradhar_graph.run",
    )
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to data directory (e.g. data/v1 or data/dev)",
    )
    parser.add_argument(
        "--er",
        type=str,
        default=None,
        help="Optional path to ER artifacts (e.g. artifacts/er)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="artifacts/graph",
        help="Output directory (default: artifacts/graph)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic Louvain clustering",
    )

    args = parser.parse_args()
    summary = run_pipeline(
        data_dir=args.data,
        er_dir=args.er,
        out_dir=args.out,
        seed=args.seed,
    )

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(
        f"\n[OK] Graph pipeline complete. Generated {summary['total_nodes']} nodes, "
        f"{summary['total_edges']} edges, {summary['total_communities']} communities, "
        f"{len(summary['dossiers'])} dossiers -> {args.out}"
    )


if __name__ == "__main__":
    main()
