"""
Sutradhar Graph and Network Analytics Package.
"""

from .bridges import detect_bridges
from .build import GraphBuilder
from .communities import detect_communities
from .dossier import generate_dossier, load_dossier_rules
from .mule import trace_mule_chains
from .paths import neighborhood, shortest_path
from .roles import detect_roles


def run_pipeline(*args, **kwargs):
    from .run import run_pipeline as _rp

    return _rp(*args, **kwargs)


__version__ = "0.1.0"

__all__ = [
    "GraphBuilder",
    "detect_communities",
    "detect_roles",
    "detect_bridges",
    "trace_mule_chains",
    "generate_dossier",
    "load_dossier_rules",
    "neighborhood",
    "shortest_path",
    "run_pipeline",
]
