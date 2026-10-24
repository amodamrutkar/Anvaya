"""
sutradhar_api/auth.py
Authentication, Role-Based Access Control (RBAC), Agency Isolation,
and Purpose-Bound Access Control for Sutradhar.

ALL DATA IS SYNTHETIC. ALL AUTHENTICATION IS SIMULATED / DEVELOPMENT-ONLY.
No real government credentials, IdP integrations, or secrets are used or claimed.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from dataclasses import dataclass

from fastapi import Header, HTTPException

from sutradhar_api.config import (
    DEV_AUTH_ENABLED,
    DEV_AUTH_SECRET,
    DEV_AUTH_TOKEN_TTL_SECONDS,
)
from sutradhar_api.models import AccessPurpose, Agency, Role, UserInfo
from sutradhar_api.store import get_store

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Seeded demo users
# ─────────────────────────────────────────────────────────────
_DEMO_USERS: dict[str, UserInfo] = {
    "analyst1": UserInfo(
        user_id="analyst1",
        role=Role.ANALYST,
        agency=Agency.STATE_POLICE,
        display_name="Demo Analyst (STATE_POLICE)",
    ),
    "analyst2": UserInfo(
        user_id="analyst2",
        role=Role.ANALYST,
        agency=Agency.MAHA_CYBER,
        display_name="Demo Analyst (MAHA_CYBER)",
    ),
    "inspector1": UserInfo(
        user_id="inspector1",
        role=Role.INSPECTOR,
        agency=Agency.CENTRAL_AGENCY,
        display_name="Demo Inspector (CENTRAL_AGENCY)",
    ),
    "officer1": UserInfo(
        user_id="officer1",
        role=Role.APPROVING_OFFICER,
        agency=Agency.STATE_POLICE,
        display_name="Demo Approving Officer (STATE_POLICE)",
    ),
    "officer2": UserInfo(
        user_id="officer2",
        role=Role.APPROVING_OFFICER,
        agency=Agency.MAHA_CYBER,
        display_name="Demo Approving Officer (MAHA_CYBER)",
    ),
    "liaison1": UserInfo(
        user_id="liaison1",
        role=Role.LIAISON,
        agency=Agency.STATE_POLICE,
        display_name="Demo Liaison Officer (STATE_POLICE)",
    ),
    "liaison2": UserInfo(
        user_id="liaison2",
        role=Role.LIAISON,
        agency=Agency.MAHA_CYBER,
        display_name="Demo Liaison Officer (MAHA_CYBER)",
    ),
    "auditor1": UserInfo(
        user_id="auditor1",
        role=Role.AUDITOR,
        agency=Agency.CENTRAL_AGENCY,
        display_name="Demo Auditor (CENTRAL_AGENCY)",
    ),
    "system": UserInfo(
        user_id="system",
        role=Role.SYSTEM,
        agency=Agency.CENTRAL_AGENCY,
        display_name="System",
    ),
}

# ─────────────────────────────────────────────────────────────
# RBAC permission table
# ─────────────────────────────────────────────────────────────

# Actions that every authenticated user can do
_PUBLIC_ACTIONS = {
    "HEALTH",
    "ENTITY_VIEW",
    "GRAPH_VIEW",
    "METRICS_VIEW",
    "KUMBH_VIEW",
    "CONNECTORS_STATUS",
}

# Role → additional allowed actions
_ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ANALYST: {
        "ENTITY_SEARCH",
        "LINK_REVIEW",
        "MULE_VIEW",
        "DOSSIER_VIEW",
        "DOSSIER_GENERATE",
        "REVIEW_QUEUE_VIEW",
        "REVIEW_DECISION",
        "UNLINK",
        "FEDERATED_QUERY",
        "KUMBH_SIMULATE",
        "KUMBH_ALERT_CONFIRM",
    },
    Role.INSPECTOR: {
        "ENTITY_SEARCH",
        "LINK_REVIEW",
        "MULE_VIEW",
        "DOSSIER_VIEW",
        "DOSSIER_GENERATE",
        "REVIEW_QUEUE_VIEW",
        "REVIEW_DECISION",
        "UNLINK",
        "FEDERATED_QUERY",
        "KUMBH_SIMULATE",
        "KUMBH_ALERT_CONFIRM",
    },
    Role.APPROVING_OFFICER: {
        "ENTITY_SEARCH",
        "DOSSIER_VIEW",
        "DOSSIER_GENERATE",
        "DOSSIER_EXPORT",
        "REVIEW_QUEUE_VIEW",
        "KUMBH_ALERT_CONFIRM",
    },
    Role.LIAISON: {
        "ENTITY_SEARCH",
        "FEDERATED_QUERY",
        "AGENCY_INBOX_VIEW",
        "CROSS_AGENCY_QUERY",
    },
    Role.AUDITOR: {
        "AUDIT_LOG_VIEW",
        "AUDIT_VERIFY",
    },
    Role.SYSTEM: set(),
}

# Agency-pair grant table: (querying_agency, target_agency) → allowed
_FEDERATED_GRANTS: set[tuple[str, str]] = {
    ("STATE_POLICE", "MAHA_CYBER"),
    ("STATE_POLICE", "CENTRAL_AGENCY"),
    ("MAHA_CYBER", "STATE_POLICE"),
    ("MAHA_CYBER", "CENTRAL_AGENCY"),
    ("CENTRAL_AGENCY", "STATE_POLICE"),
    ("CENTRAL_AGENCY", "MAHA_CYBER"),
}

# ─────────────────────────────────────────────────────────────
# Token Generation and Parsing
# ─────────────────────────────────────────────────────────────


def create_dev_token(user_id: str, ttl_seconds: int | None = None) -> str:
    """Create a signed development token with iat and exp timestamp claims."""
    ttl = ttl_seconds if ttl_seconds is not None else DEV_AUTH_TOKEN_TTL_SECONDS
    iat = int(time.time())
    exp = iat + ttl
    payload = f"{user_id}.{iat}.{exp}"
    sig = hmac.new(
        DEV_AUTH_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()[:16]
    return f"dev-token-{user_id}.{iat}.{exp}.{sig}"


def _parse_token(token: str) -> UserInfo:
    """Parse and validate a development bearer token with expiry verification."""
    if not DEV_AUTH_ENABLED:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "DEV_AUTH_DISABLED",
                    "message": "Development authentication is disabled.",
                }
            },
        )

    clean_token = token.strip()
    candidate_uid = None
    iat_str = None
    exp_str = None
    sig = None

    if clean_token.startswith("dev-token-"):
        parts = clean_token.removeprefix("dev-token-").split(".")
        if len(parts) != 4:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Malformed token structure. Expected 'dev-token-<user_id>.<iat>.<exp>.<sig>'.",
                    }
                },
            )
        candidate_uid, iat_str, exp_str, sig = parts[0], parts[1], parts[2], parts[3]
    elif clean_token.startswith("sutradhar_dev."):
        parts = clean_token.split(".")
        if len(parts) != 5:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Malformed token structure. Expected 'sutradhar_dev.<user_id>.<iat>.<exp>.<sig>'.",
                    }
                },
            )
        candidate_uid, iat_str, exp_str, sig = parts[1], parts[2], parts[3], parts[4]
    else:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Malformed authentication token format. Use 'dev-token-<user_id>.<iat>.<exp>.<sig>'.",
                }
            },
        )

    # Validate integer timestamp claims
    try:
        iat = int(iat_str)
        exp = int(exp_str)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Malformed token timestamp claims. iat and exp must be valid integer timestamps.",
                }
            },
        )

    # Verify signature covers user_id, iat, and exp
    payload = f"{candidate_uid}.{iat}.{exp}"
    expected_sig = hmac.new(
        DEV_AUTH_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()[:16]
    if not hmac.compare_digest(sig, expected_sig):
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Development token signature mismatch.",
                }
            },
        )

    # Check token expiry
    now = int(time.time())
    if now > exp:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": f"Development token has expired (exp={exp}, now={now}).",
                }
            },
        )

    user = _DEMO_USERS.get(candidate_uid)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "UNKNOWN_USER",
                    "message": f"Token references unknown user: {candidate_uid!r}",
                }
            },
        )
    return user


def _get_user(
    authorization: str | None = None,
    x_demo_user: str | None = None,
) -> UserInfo:
    """Authenticate incoming principal via Bearer token or legacy X-Demo-User."""
    if authorization:
        auth_str = authorization.strip()
        if auth_str.lower().startswith("bearer "):
            token = auth_str[7:].strip()
            return _parse_token(token)
        elif auth_str.startswith("dev-token-") or auth_str.startswith("sutradhar_dev."):
            return _parse_token(auth_str)
        else:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Authorization header must use Bearer scheme (e.g. 'Bearer dev-token-analyst1').",
                    }
                },
            )

    if x_demo_user:
        if not DEV_AUTH_ENABLED:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "DEV_AUTH_DISABLED",
                        "message": "X-Demo-User header disabled in production.",
                    }
                },
            )
        user = _DEMO_USERS.get(x_demo_user.strip())
        if not user:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "UNKNOWN_USER",
                        "message": f"Unknown demo user: {x_demo_user!r}. Valid users: {list(_DEMO_USERS)}",
                    }
                },
            )
        return user

    raise HTTPException(
        status_code=401,
        detail={
            "error": {
                "code": "MISSING_AUTH",
                "message": "Authentication required. Provide 'Authorization: Bearer <token>' or 'X-Demo-User: <user_id>'.",
            }
        },
    )


# ─────────────────────────────────────────────────────────────
# Central Security Policy Model
# ─────────────────────────────────────────────────────────────


@dataclass
class AuthorizationDecision:
    """Result of an authorization evaluation."""

    allowed: bool
    code: str = "ALLOWED"
    reason: str = "Authorized"
    is_cross_agency: bool = False
    target_agency: str | None = None
    purpose: str | None = None


class SecurityPolicy:
    """Central policy engine for role permissions, agency isolation, and purpose binding."""

    @staticmethod
    def check_action(user: UserInfo, action: str) -> AuthorizationDecision:
        allowed_actions = _PUBLIC_ACTIONS | _ROLE_PERMISSIONS.get(user.role, set())
        if action not in allowed_actions:
            return AuthorizationDecision(
                allowed=False,
                code="FORBIDDEN",
                reason=f"Role {user.role} cannot perform {action}.",
            )
        return AuthorizationDecision(allowed=True)

    @staticmethod
    def check_agency_access(
        user: UserInfo,
        resource_agencies: list[str] | set[str] | str,
        purpose: str | None = None,
        case_ref: str | None = None,
    ) -> AuthorizationDecision:
        if isinstance(resource_agencies, str):
            agencies = {resource_agencies}
        else:
            agencies = set(resource_agencies)

        # Same-agency access: user's agency is among the resource custodians
        if not agencies or user.agency.value in agencies:
            return AuthorizationDecision(allowed=True, is_cross_agency=False)

        # Verify cross-agency sharing grants
        for target in agencies:
            if not check_federated_grant(user.agency.value, target):
                return AuthorizationDecision(
                    allowed=False,
                    code="NO_GRANT",
                    reason=f"No data-sharing grant between {user.agency.value} and {target}.",
                    is_cross_agency=True,
                    target_agency=target,
                )

        # Liaison officers have cross-agency coordination authority
        if user.role == Role.LIAISON:
            if purpose:
                valid_purposes = {p.value for p in AccessPurpose}
                if purpose not in valid_purposes:
                    return AuthorizationDecision(
                        allowed=False,
                        code="INVALID_PURPOSE",
                        reason=f"Purpose '{purpose}' is not valid. Valid purposes: {sorted(valid_purposes)}",
                        is_cross_agency=True,
                    )
            return AuthorizationDecision(
                allowed=True,
                is_cross_agency=True,
                target_agency=list(agencies)[0],
                purpose=purpose or "CROSS_AGENCY_COORDINATION",
            )

        # Cross-agency access evaluation for other roles
        target_str = ", ".join(sorted(agencies))
        if not purpose:
            return AuthorizationDecision(
                allowed=False,
                code="CROSS_AGENCY_PURPOSE_REQUIRED",
                reason=f"Cross-agency access to {target_str} requires an authorized purpose.",
                is_cross_agency=True,
                target_agency=list(agencies)[0],
            )

        # Validate purpose
        valid_purposes = {p.value for p in AccessPurpose}
        if purpose not in valid_purposes:
            return AuthorizationDecision(
                allowed=False,
                code="INVALID_PURPOSE",
                reason=f"Purpose '{purpose}' is not valid. Valid purposes: {sorted(valid_purposes)}",
                is_cross_agency=True,
            )

        # Auditor role restriction
        if user.role == Role.AUDITOR and purpose != AccessPurpose.AUDIT.value:
            return AuthorizationDecision(
                allowed=False,
                code="FORBIDDEN",
                reason="Auditors are restricted to compliance and audit verification operations.",
                is_cross_agency=True,
            )

        return AuthorizationDecision(
            allowed=True,
            is_cross_agency=True,
            target_agency=list(agencies)[0],
            purpose=purpose,
        )



policy = SecurityPolicy()


# ─────────────────────────────────────────────────────────────
# FastAPI Dependencies
# ─────────────────────────────────────────────────────────────


def require_auth(
    authorization: str | None = Header(default=None),
    x_demo_user: str | None = Header(default=None),
) -> UserInfo:
    """FastAPI dependency: require an authenticated principal."""
    return _get_user(authorization, x_demo_user)


def require_action(action: str):
    """FastAPI dependency factory: require a specific RBAC action."""

    def _dep(
        authorization: str | None = Header(default=None),
        x_demo_user: str | None = Header(default=None),
    ) -> UserInfo:
        user = _get_user(authorization, x_demo_user)
        decision = policy.check_action(user, action)
        if not decision.allowed:
            # Audit denied attempt
            try:
                store = get_store()
                store.record_audit(
                    actor=user.user_id,
                    role=user.role.value,
                    action=f"{action}_DENIED",
                    summary=f"Access denied: {decision.reason}",
                    agency=user.agency.value,
                )
            except Exception as e:
                log.warning("Could not record denial audit: %s", e)

            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": decision.code,
                        "message": decision.reason,
                    }
                },
            )
        return user

    return _dep


def check_federated_grant(querying_agency: str, target_agency: str) -> bool:
    """Return True if querying agency has a data-sharing grant with target."""
    return (querying_agency, target_agency) in _FEDERATED_GRANTS


def require_federated_grant(querying_agency: str, target_agency: str) -> None:
    """Raise HTTPException 403 if no cross-agency grant exists."""
    if not check_federated_grant(querying_agency, target_agency):
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "NO_GRANT",
                    "message": f"No data-sharing grant: {querying_agency} → {target_agency}",
                }
            },
        )
