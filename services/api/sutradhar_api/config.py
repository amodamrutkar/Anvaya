"""
sutradhar_api/config.py
Runtime configuration loaded from environment variables.
No secrets are hard-coded. All values come from .env / environment.
"""

import os
from pathlib import Path

# Environment and Root of the repository / container
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

_env_root = os.getenv("APP_ROOT") or os.getenv("REPO_ROOT")
if _env_root:
    _REPO_ROOT = Path(_env_root)
elif (
    Path("/app/contracts").exists()
    and not (Path(__file__).parent.parent.parent.parent / "contracts").exists()
):
    _REPO_ROOT = Path("/app")
else:
    _REPO_ROOT = Path(__file__).parent.parent.parent.parent

# Where pipeline artifacts live. Falls back to contracts/fixtures/ if absent.
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", str(_REPO_ROOT / "artifacts")))
CONTRACTS_FIXTURES_DIR = _REPO_ROOT / "contracts" / "fixtures"
CONTRACTS_SCHEMAS_DIR = _REPO_ROOT / "contracts" / "schemas"
DATA_DIR = _REPO_ROOT / "data"
KUMBH_EVENTS_PATH = DATA_DIR / "kumbh" / "events.jsonl"

# Demo tamper mode — defaults to 0 for production; enable explicitly (DEMO_TAMPER=1) only for live tamper demo
DEMO_TAMPER = os.getenv("DEMO_TAMPER", "0") == "1"

# Development / controlled deployment authentication and token verification
DEV_AUTH_ENABLED = os.getenv("DEV_AUTH_ENABLED", "1") == "1"
DEV_AUTH_SECRET = os.getenv("DEV_AUTH_SECRET", "sutradhar-dev-secret-change-in-prod")
DEV_AUTH_TOKEN_TTL_SECONDS = int(os.getenv("DEV_AUTH_TOKEN_TTL_SECONDS", "3600"))

_INSECURE_DEFAULT_SECRET = "sutradhar-dev-secret-change-in-prod"
if ENVIRONMENT == "production" and DEV_AUTH_ENABLED and DEV_AUTH_SECRET == _INSECURE_DEFAULT_SECRET:
    raise RuntimeError(
        "Production deployment cannot use the default DEV_AUTH_SECRET. "
        "Set a strong DEV_AUTH_SECRET in your environment or .env file."
    )

# CORS
CORS_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080",
    ).split(",")
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
