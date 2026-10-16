"""
sutradhar_api/config.py
Runtime configuration loaded from environment variables.
No secrets are hard-coded. All values come from .env / environment.
"""
import os
from pathlib import Path

# Root of the repository (two levels up from services/api/sutradhar_api/)
_REPO_ROOT = Path(__file__).parent.parent.parent.parent

# Where pipeline artifacts live. Falls back to contracts/fixtures/ if absent.
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", str(_REPO_ROOT / "artifacts")))
CONTRACTS_FIXTURES_DIR = _REPO_ROOT / "contracts" / "fixtures"
DATA_DIR = _REPO_ROOT / "data"
KUMBH_EVENTS_PATH = DATA_DIR / "kumbh" / "events.jsonl"

# Demo tamper mode — only for live demo tamper-detection demonstration
DEMO_TAMPER = os.getenv("DEMO_TAMPER", "0") == "1"

# CORS
CORS_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",")
    if o.strip()
]

# Dataset version
DATASET_VERSION = os.getenv("DATASET_VERSION", "v1")

# LLM provider (none = offline)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none")

# Rate limiting
RATE_LIMIT_QUERIES_PER_MINUTE = int(os.getenv("RATE_LIMIT_QPM", "20"))


def artifacts_path(relative: str) -> Path:
    """
    Resolve a path inside artifacts/, falling back to contracts/fixtures/artifacts/
    or contracts/fixtures/ if the artifacts directory doesn't exist or the file is absent.
    """
    primary = ARTIFACTS_DIR / relative
    if primary.exists():
        return primary
    fallback_art = CONTRACTS_FIXTURES_DIR / "artifacts" / relative
    if fallback_art.exists():
        return fallback_art
    return CONTRACTS_FIXTURES_DIR / relative
