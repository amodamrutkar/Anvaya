"""
sutradhar_api/auth.py
Demo authentication and role-based access control.
No real auth: the X-Demo-User header identifies the user, looked up from a seed table.
All users and roles are synthetic.
"""

from __future__ import annotations

from fastapi import Header, HTTPException

from sutradhar_api.models import Agency, Role, UserInfo

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
        display_name="Demo Approving Officer",
    ),
    "liaison1": UserInfo(
        user_id="liaison1",
        role=Role.LIAISON,
        agency=Agency.STATE_POLICE,
        display_name="Demo Liaison Officer",
    ),
    "auditor1": UserInfo(
        user_id="auditor1",
        role=Role.AUDITOR,
        agency=Agency.CENTRAL_AGENCY,
        display_name="Demo Auditor",
    ),
    "system": UserInfo(
        user_id="system", role=Role.SYSTEM, agency=Agency.CENTRAL_AGENCY, display_name="System"
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
    "AUDIT_VERIFY",
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
    },
    Role.AUDITOR: {
        "AUDIT_LOG_VIEW",
    },
    Role.SYSTEM: set(),
}

# Agency-pair grant table: (querying_agency, target_agency) → allowed
# Symmetric grants modelled here for the demo.
_FEDERATED_GRANTS: set[tuple[str, str]] = {
    ("STATE_POLICE", "MAHA_CYBER"),
    ("STATE_POLICE", "CENTRAL_AGENCY"),
    ("MAHA_CYBER", "STATE_POLICE"),
    ("MAHA_CYBER", "CENTRAL_AGENCY"),
    ("CENTRAL_AGENCY", "STATE_POLICE"),
    ("CENTRAL_AGENCY", "MAHA_CYBER"),
}


# ─────────────────────────────────────────────────────────────
# FastAPI dependency helpers
# ─────────────────────────────────────────────────────────────


def _get_user(x_demo_user: str | None) -> UserInfo:
    if not x_demo_user:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "MISSING_AUTH",
                    "message": "X-Demo-User header is required. Use any seeded user id (e.g. analyst1).",
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


def require_auth(x_demo_user: str | None = Header(default=None)) -> UserInfo:
    """FastAPI dependency: any authenticated user."""
    return _get_user(x_demo_user)


def require_action(action: str):
    """FastAPI dependency factory: require a specific RBAC action."""

    def _dep(x_demo_user: str | None = Header(default=None)) -> UserInfo:
        user = _get_user(x_demo_user)
        allowed = _PUBLIC_ACTIONS | _ROLE_PERMISSIONS.get(user.role, set())
        if action not in allowed:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Role {user.role} cannot perform {action}.",
                    }
                },
            )
        return user

    return _dep


def check_federated_grant(querying_agency: str, target_agency: str) -> bool:
    """Return True if the querying agency has a data-sharing grant with the target."""
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
