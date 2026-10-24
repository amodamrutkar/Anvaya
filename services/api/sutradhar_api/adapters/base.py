"""
sutradhar_api/adapters/base.py
Base adapter interface and validation utilities for Sutradhar canonical contracts.

Architecture Boundary:
Raw External Payload (Simulated) -> Adapter -> Canonical Contract (JSON Schema Validated) -> Downstream Intelligence

Adapters strictly normalize data without performing entity resolution,
graph building, intelligence scoring, or making live network/API calls.
"""

from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from sutradhar_api.config import CONTRACTS_SCHEMAS_DIR

log = logging.getLogger(__name__)


class AdapterError(Exception):
    """Base exception for all adapter operations."""


class AdapterMappingError(AdapterError):
    """Raised when raw payload lacks essential fields or cannot be mapped."""


class AdapterValidationError(AdapterError):
    """Raised when canonical payload fails JSON Schema validation."""


_REGISTRY = None
_VALIDATORS: dict[str, Any] = {}


def _get_schema_validator(schema_name: str) -> Any:
    """Load and cache a Draft202012Validator with local schema referencing."""
    global _REGISTRY, _VALIDATORS

    if schema_name in _VALIDATORS:
        return _VALIDATORS[schema_name]

    import jsonschema

    schema_file = CONTRACTS_SCHEMAS_DIR / schema_name
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    schema_dict = json.loads(schema_file.read_text(encoding="utf-8"))

    if _REGISTRY is None:
        try:
            from referencing import Registry, Resource

            resources = []
            for p in CONTRACTS_SCHEMAS_DIR.glob("*.schema.json"):
                d = json.loads(p.read_text(encoding="utf-8"))
                res = Resource.from_contents(d)
                resources.append((d.get("$id", p.name), res))
                if p.name not in [d.get("$id")]:
                    resources.append((p.name, res))
            _REGISTRY = Registry().with_resources(resources)
        except Exception as e:
            log.warning("Could not build referencing Registry: %s", e)
            _REGISTRY = None

    if _REGISTRY is not None:
        validator = jsonschema.Draft202012Validator(schema_dict, registry=_REGISTRY)
    else:
        validator = jsonschema.Draft202012Validator(schema_dict)

    _VALIDATORS[schema_name] = validator
    return validator


class BaseAdapter(ABC):
    """Abstract base class for all source-specific integration adapters."""

    adapter_id: str = "BaseAdapter"
    source_system: str = "UNKNOWN_SYSTEM"
    agency: str = "STATE_POLICE"
    target_schema: str = "source_record.schema.json"

    def build_ingestion_metadata(
        self,
        source_record_id: str,
        raw_payload: dict[str, Any],
        trace_id: str | None = None,
        batch_id: str | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build standard IngestionMetadata contract for provenance tracking."""
        payload_bytes = json.dumps(raw_payload, sort_keys=True).encode("utf-8")
        payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
        now_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        meta: dict[str, Any] = {
            "schema_version": "2.0.0",
            "source_system": self.source_system,
            "source_record_id": str(source_record_id),
            "agency": self.agency,
            "adapter_id": self.adapter_id,
            "ingestion_timestamp": now_utc,
            "batch_id": batch_id,
            "trace_id": trace_id,
            "payload_sha256": payload_sha256,
            "simulated": True,
        }
        if provenance:
            meta["provenance"] = provenance
        return meta

    @abstractmethod
    def adapt(self, raw_payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Transform raw external payload into normalized canonical representation."""
        raise NotImplementedError

    def validate(
        self,
        canonical_payload: dict[str, Any],
        schema_name: str | None = None,
    ) -> None:
        """Validate canonical dictionary against target JSON schema."""
        target = schema_name or self.target_schema
        validator = _get_schema_validator(target)
        errors = list(validator.iter_errors(canonical_payload))
        if errors:
            first_err = errors[0]
            path_str = ".".join(str(p) for p in first_err.absolute_path) or "root"
            raise AdapterValidationError(
                f"Validation error in '{target}' at [{path_str}]: {first_err.message}"
            )

    def process(self, raw_payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Execute full normalization pipeline: adapt -> validate -> return canonical object."""
        canonical = self.adapt(raw_payload, **kwargs)
        self.validate(canonical)
        return canonical
