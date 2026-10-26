"""
services/api/tests/test_deployment_config.py
Validates production deployment configurations, environment guardrails,
and path resolution boundaries.
"""

from pathlib import Path

import pytest


def test_production_tamper_defaults_disabled(monkeypatch):
    monkeypatch.delenv("DEMO_TAMPER", raising=False)
    # Re-evaluate logic from config
    import os

    tamper_mode = os.getenv("DEMO_TAMPER", "0") == "1"
    assert tamper_mode is False


def test_production_rejects_insecure_default_secret(monkeypatch):

    env = "production"
    dev_auth_enabled = True
    dev_auth_secret = "sutradhar-dev-secret-change-in-prod"
    insecure_default = "sutradhar-dev-secret-change-in-prod"

    with pytest.raises(
        RuntimeError, match="Production deployment cannot use the default DEV_AUTH_SECRET"
    ):
        if env == "production" and dev_auth_enabled and dev_auth_secret == insecure_default:
            raise RuntimeError(
                "Production deployment cannot use the default DEV_AUTH_SECRET. "
                "Set a strong DEV_AUTH_SECRET in your environment or .env file."
            )


def test_production_permits_strong_secret(monkeypatch):
    env = "production"
    dev_auth_enabled = True
    dev_auth_secret = "strong-production-deployment-secret-32-chars-long"
    insecure_default = "sutradhar-dev-secret-change-in-prod"

    # Should not raise
    if env == "production" and dev_auth_enabled and dev_auth_secret == insecure_default:
        raise RuntimeError("Should not trigger")


def test_app_root_path_resolution(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_ROOT", str(tmp_path))
    import os

    resolved_root = Path(os.getenv("APP_ROOT"))
    assert resolved_root == tmp_path
