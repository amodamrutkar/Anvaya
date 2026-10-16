"""Configuration loader — reads config.yaml and merges with env overrides."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


_DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load YAML config from *config_path* (defaults to bundled config.yaml).

    Environment variable overrides:
      LLM_PROVIDER  →  llm.provider
    """
    path = config_path or _DEFAULT_CONFIG_PATH
    with open(path, encoding="utf-8") as fh:
        cfg: dict[str, Any] = yaml.safe_load(fh)

    # env overrides
    llm_provider = os.environ.get("LLM_PROVIDER")
    if llm_provider is not None:
        cfg.setdefault("llm", {})["provider"] = llm_provider.lower()

    return cfg
