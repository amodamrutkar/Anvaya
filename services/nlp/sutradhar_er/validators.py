"""Validators for phone, IFSC, vehicle, and account numbers.

Invalid values are dropped and counted — never silently accepted (PRD X4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Compiled regexes (default patterns from config.yaml / PRD)
_PHONE_RE = re.compile(r"^[6-9]\d{9}$")
_IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
_VEHICLE_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z]{1,3}\d{4}$")


@dataclass
class ValidationStats:
    """Counts of accepted vs rejected values per field type."""

    accepted: int = 0
    rejected: int = 0
    rejected_values: list[str] = field(default_factory=list)


def validate_phone(raw: str) -> str | None:
    """Return cleaned 10-digit phone or None."""
    cleaned = re.sub(r"[\s\-\+\(\)]", "", raw)
    # strip leading +91 or 0
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]
    if _PHONE_RE.match(cleaned):
        return cleaned
    return None


def validate_ifsc(raw: str) -> str | None:
    """Return valid IFSC or None."""
    cleaned = raw.strip().upper()
    if _IFSC_RE.match(cleaned):
        return cleaned
    return None


def validate_vehicle(raw: str) -> str | None:
    """Return normalised vehicle number or None."""
    cleaned = re.sub(r"[\s\-]", "", raw).upper()
    if _VEHICLE_RE.match(cleaned):
        return cleaned
    return None


def validate_account(raw: str) -> str | None:
    """Return account number if 9–18 digits, else None."""
    cleaned = re.sub(r"[\s\-]", "", raw)
    if cleaned.isdigit() and 9 <= len(cleaned) <= 18:
        return cleaned
    return None


def validate_batch(
    values: list[str],
    validator_fn,
    stats: ValidationStats | None = None,
) -> list[str]:
    """Run *validator_fn* on each value. Return accepted list, update *stats*."""
    if stats is None:
        stats = ValidationStats()
    accepted: list[str] = []
    for v in values:
        result = validator_fn(v)
        if result is not None:
            accepted.append(result)
            stats.accepted += 1
        else:
            stats.rejected += 1
            stats.rejected_values.append(v)
    return accepted
