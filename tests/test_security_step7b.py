"""
tests/test_security_step7b.py
Step 7B — Authentication, Authorization, Agency Isolation & Purpose-Bound Access Tests.

Covers all 17 mandatory verification scenarios:
  1. Unauthenticated request to protected endpoint -> 401
  2. Valid development authentication -> allowed
  3. Malformed/invalid token -> 401
  4. Analyst accessing permitted investigation -> allowed
  5. Analyst attempting dossier export -> 403
  6. Auditor attempting investigation mutation -> 403
  7. Approving officer performing permitted export -> allowed
  8. Same-agency access -> allowed when role permits
  9. Unauthorized cross-agency access without purpose -> 403
  10. Authorized cross-agency access with valid purpose -> allowed
  11. Cross-agency request without purpose -> 403
  12. Invalid purpose -> 403
  13. Valid purpose + authorized role + agency scope -> allowed
  14. Successful sensitive operation generates audit entry
  15. Denied sensitive operation generates auditable denial
  16. Direct API call cannot bypass frontend role restrictions
  17. Changing frontend role claim alone cannot grant backend privileges
"""

import pytest
from httpx import ASGITransport, AsyncClient

from sutradhar_api.auth import create_dev_token
from sutradhar_api.main import app
from sutradhar_api.models import AccessPurpose
from sutradhar_api.store import get_store


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture(autouse=True)
def setup_store():
    store = get_store()
    store.load()
    return store


def _get_err_code(r) -> str:
    """Helper to extract error code from detail.error or error structure."""
    data = r.json()
    if "detail" in data and isinstance(data["detail"], dict) and "error" in data["detail"]:
        return data["detail"]["error"].get("code", "")
    if "error" in data and isinstance(data["error"], dict):
        return data["error"].get("code", "")
    return ""


# ─────────────────────────────────────────────────────────────
# 1. Authentication Tests (1 - 3)
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_01_unauthenticated_request_returns_401(client):
    """Scenario 1: Protected endpoint without authentication returns 401."""
    # Test multiple protected endpoints
    r1 = await client.get("/me")
    assert r1.status_code == 401
    assert _get_err_code(r1) == "MISSING_AUTH"

    r2 = await client.get("/entities/search?q=test")
    assert r2.status_code == 401
    assert _get_err_code(r2) == "MISSING_AUTH"

    r3 = await client.get("/review-queue")
    assert r3.status_code == 401


@pytest.mark.asyncio
async def test_02_valid_development_authentication_allowed(client):
    """Scenario 2: Valid development bearer token grants access to authenticated endpoints."""
    token = create_dev_token("analyst1")
    r = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == "analyst1"
    assert data["role"] == "ANALYST"
    assert data["agency"] == "STATE_POLICE"

    # Also verify legacy header compatibility
    r_legacy = await client.get("/me", headers={"X-Demo-User": "analyst1"})
    assert r_legacy.status_code == 200
    assert r_legacy.json()["user_id"] == "analyst1"


@pytest.mark.asyncio
async def test_03_malformed_or_invalid_token_returns_401(client):
    """Scenario 3: Malformed, tampered, or unknown tokens are rejected with 401."""
    # Malformed token structure
    r1 = await client.get("/me", headers={"Authorization": "Bearer not-a-valid-token"})
    assert r1.status_code == 401
    assert _get_err_code(r1) == "INVALID_TOKEN"

    # Non-bearer scheme
    r2 = await client.get("/me", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert r2.status_code == 401
    assert _get_err_code(r2) == "INVALID_TOKEN"

    # Tampered signature
    r3 = await client.get("/me", headers={"Authorization": "Bearer dev-token-analyst1.tampered000000"})
    assert r3.status_code == 401
    assert _get_err_code(r3) == "INVALID_TOKEN"

    # Unknown user id
    token_ghost = create_dev_token("ghost_user_999")
    r4 = await client.get("/me", headers={"Authorization": f"Bearer {token_ghost}"})
    assert r4.status_code == 401
    assert _get_err_code(r4) == "UNKNOWN_USER"


# ─────────────────────────────────────────────────────────────
# 2. Role Authorization Tests (4 - 7)
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_04_analyst_permitted_investigation_allowed(client):
    """Scenario 4: Analyst accessing permitted investigation resources is allowed."""
    token = create_dev_token("analyst1")
    headers = {"Authorization": f"Bearer {token}"}

    # Entity search
    r = await client.get("/entities/search?q=rakesh", headers=headers)
    assert r.status_code == 200

    # Communities view
    r = await client.get("/graph/communities", headers=headers)
    assert r.status_code == 200

    # Review queue view
    r = await client.get("/review-queue", headers=headers)
    assert r.status_code == 200

    # Mule investigation view
    r = await client.get("/mule/chains", headers=headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_05_analyst_attempting_dossier_export_forbidden(client):
    """Scenario 5: Analyst attempting to export a dossier receives 403."""
    token = create_dev_token("analyst1")
    r = await client.post(
        "/dossier/DOS-001/export",
        json={"confirm": True, "export_format": "JSON"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
    assert _get_err_code(r) == "FORBIDDEN"


@pytest.mark.asyncio
async def test_06_auditor_attempting_investigation_mutation_forbidden(client):
    """Scenario 6: Auditor attempting investigation mutations receives 403."""
    token = create_dev_token("auditor1")
    headers = {"Authorization": f"Bearer {token}"}

    # Cannot generate dossier
    r1 = await client.post("/dossier/generate", json={"community_id": "COM-001"}, headers=headers)
    assert r1.status_code == 403
    assert _get_err_code(r1) == "FORBIDDEN"

    # Cannot submit human review decision
    r2 = await client.post(
        "/review-queue/LNK-001/decision",
        json={"decision": "CONFIRM", "reason": "Auditor attempting confirmation"},
        headers=headers,
    )
    assert r2.status_code == 403
    assert _get_err_code(r2) == "FORBIDDEN"

    # Cannot unlink
    r3 = await client.post(
        "/links/LNK-001/unlink",
        json={"reason": "Auditor attempting unlink"},
        headers=headers,
    )
    assert r3.status_code == 403


@pytest.mark.asyncio
async def test_07_approving_officer_performing_permitted_export_allowed(client):
    """Scenario 7: Approving officer performing export with confirm=True is allowed."""
    token = create_dev_token("officer1")
    headers = {"Authorization": f"Bearer {token}"}

    # Generate dossier for COM-001
    r_gen = await client.post("/dossier/generate", json={"community_id": "COM-001"}, headers=headers)
    assert r_gen.status_code == 200
    dos_id = r_gen.json()["dossier_id"]

    # Export dossier
    r_exp = await client.post(
        f"/dossier/{dos_id}/export",
        json={"confirm": True, "export_format": "JSON"},
        headers=headers,
    )
    assert r_exp.status_code == 200
    data = r_exp.json()
    assert data["dossier_id"] == dos_id
    assert "exported_at" in data
    assert data["actor"] == "officer1"


# ─────────────────────────────────────────────────────────────
# 3. Agency Isolation Tests (8 - 10)
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_08_same_agency_access_allowed_when_role_permits(client):
    """Scenario 8: Same-agency access is permitted without cross-agency purpose."""
    # officer1 is STATE_POLICE, generating and exporting a STATE_POLICE dossier
    token = create_dev_token("officer1")
    headers = {"Authorization": f"Bearer {token}"}

    r_gen = await client.post("/dossier/generate", json={"community_id": "COM-001"}, headers=headers)
    dos_id = r_gen.json()["dossier_id"]

    # Export without X-Access-Purpose succeeds because officer1 is in dossier agencies
    r_exp = await client.post(
        f"/dossier/{dos_id}/export",
        json={"confirm": True, "export_format": "JSON"},
        headers=headers,
    )
    assert r_exp.status_code == 200


@pytest.mark.asyncio
async def test_09_unauthorized_cross_agency_access_forbidden(client):
    """Scenario 9: Cross-agency access without valid purpose header returns 403."""
    store = get_store()

    # Create a dossier strictly owned by MAHA_CYBER
    dossier_id = "DOS-CYBER-ISOLATED"
    store.dossiers[dossier_id] = {
        "dossier_id": dossier_id,
        "community_id": "COM-CYBER",
        "agencies": ["MAHA_CYBER"],
        "status": "DRAFT",
        "summary": "Isolated Cyber Dossier",
        "sections": {},
    }

    # officer1 is STATE_POLICE; attempting export without X-Access-Purpose
    token = create_dev_token("officer1")
    r = await client.post(
        f"/dossier/{dossier_id}/export",
        json={"confirm": True, "export_format": "JSON"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
    assert _get_err_code(r) == "CROSS_AGENCY_PURPOSE_REQUIRED"


@pytest.mark.asyncio
async def test_10_authorized_cross_agency_access_with_valid_purpose_allowed(client):
    """Scenario 10: Cross-agency access with approved purpose and grant succeeds."""
    store = get_store()
    dossier_id = "DOS-CYBER-SHARED"
    store.dossiers[dossier_id] = {
        "dossier_id": dossier_id,
        "community_id": "COM-CYBER",
        "agencies": ["MAHA_CYBER"],
        "status": "DRAFT",
        "summary": "Shared Cyber Dossier",
        "sections": {},
    }

    token = create_dev_token("officer1")  # STATE_POLICE
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Access-Purpose": "COURT_DOSSIER_PREPARATION",
    }
    r = await client.post(
        f"/dossier/{dossier_id}/export",
        json={"confirm": True, "export_format": "JSON"},
        headers=headers,
    )
    assert r.status_code == 200
    assert "exported_at" in r.json()


# ─────────────────────────────────────────────────────────────
# 4. Purpose-Bound Access Tests (11 - 13)
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_11_cross_agency_request_without_purpose_forbidden(client):
    """Scenario 11: Cross-agency operation without purpose returns 403."""
    store = get_store()
    dossier_id = "DOS-CENTRAL-ONLY"
    store.dossiers[dossier_id] = {
        "dossier_id": dossier_id,
        "community_id": "COM-CEN",
        "agencies": ["CENTRAL_AGENCY"],
        "status": "DRAFT",
        "summary": "Central Agency Dossier",
        "sections": {},
    }

    # officer2 is MAHA_CYBER
    token = create_dev_token("officer2")
    r = await client.post(
        f"/dossier/{dossier_id}/export",
        json={"confirm": True, "export_format": "JSON"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
    assert _get_err_code(r) == "CROSS_AGENCY_PURPOSE_REQUIRED"


@pytest.mark.asyncio
async def test_12_invalid_purpose_forbidden(client):
    """Scenario 12: Cross-agency operation with unrecognized/unapproved purpose returns 403."""
    store = get_store()
    dossier_id = "DOS-PURPOSE-TEST"
    store.dossiers[dossier_id] = {
        "dossier_id": dossier_id,
        "community_id": "COM-TEST",
        "agencies": ["CENTRAL_AGENCY"],
        "status": "DRAFT",
        "summary": "Test Dossier",
        "sections": {},
    }

    token = create_dev_token("officer2")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Access-Purpose": "UNAUTHORIZED_CURIOSITY",
    }
    r = await client.post(
        f"/dossier/{dossier_id}/export",
        json={"confirm": True, "export_format": "JSON"},
        headers=headers,
    )
    assert r.status_code == 403
    assert _get_err_code(r) == "INVALID_PURPOSE"


@pytest.mark.asyncio
async def test_13_valid_purpose_plus_authorized_role_plus_agency_scope_allowed(client):
    """Scenario 13: Valid purpose + authorized role + mutual grant succeeds."""
    store = get_store()
    dossier_id = "DOS-VALID-ALL"
    store.dossiers[dossier_id] = {
        "dossier_id": dossier_id,
        "community_id": "COM-ALL",
        "agencies": ["MAHA_CYBER"],
        "status": "DRAFT",
        "summary": "Valid All",
        "sections": {},
    }

    # officer1 (APPROVING_OFFICER, STATE_POLICE) with valid purpose CASE_INVESTIGATION
    token = create_dev_token("officer1")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Access-Purpose": AccessPurpose.CASE_INVESTIGATION.value,
    }
    r = await client.post(
        f"/dossier/{dossier_id}/export",
        json={"confirm": True, "export_format": "JSON"},
        headers=headers,
    )
    assert r.status_code == 200
    assert "exported_at" in r.json()


# ─────────────────────────────────────────────────────────────
# 5. Audit Integration Tests (14 - 15)
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_14_successful_sensitive_operation_generates_audit_entry(client):
    """Scenario 14: Successful sensitive operation produces an auditable ledger entry with agency & purpose."""
    store = get_store()
    token = create_dev_token("officer1")
    headers = {"Authorization": f"Bearer {token}"}

    # Generate dossier
    r_gen = await client.post("/dossier/generate", json={"community_id": "COM-001"}, headers=headers)
    dos_id = r_gen.json()["dossier_id"]

    # Export dossier
    r_exp = await client.post(
        f"/dossier/{dos_id}/export",
        json={"confirm": True, "export_format": "JSON"},
        headers=headers,
    )
    assert r_exp.status_code == 200

    # Verify latest audit record
    last_audit = store.audit_log[-1]
    assert last_audit["actor"] == "officer1"
    assert last_audit["role"] == "APPROVING_OFFICER"
    assert last_audit["action"] == "DOSSIER_EXPORT"
    assert last_audit["agency"] == "STATE_POLICE"
    assert "hash" in last_audit
    assert "prev_hash" in last_audit

    # Chain remains valid
    v = store.verify_audit_chain()
    assert v["valid"] is True


@pytest.mark.asyncio
async def test_15_denied_sensitive_operation_is_audited(client):
    """Scenario 15: Denied sensitive operation produces an auditable denial entry in ledger."""
    store = get_store()
    token = create_dev_token("analyst1")

    # Analyst attempts dossier export
    r = await client.post(
        "/dossier/DOS-001/export",
        json={"confirm": True, "export_format": "JSON"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403

    # Check for denial record in audit log
    denial_entries = [
        entry
        for entry in store.audit_log
        if entry["actor"] == "analyst1" and "DENIED" in entry["action"]
    ]
    assert len(denial_entries) > 0
    latest_denial = denial_entries[-1]
    assert latest_denial["action"] == "DOSSIER_EXPORT_DENIED"
    assert latest_denial["agency"] == "STATE_POLICE"

    # Verify hash chain integrity covers denials
    v = store.verify_audit_chain()
    assert v["valid"] is True


# ─────────────────────────────────────────────────────────────
# 6. Bypass Protection Tests (16 - 17)
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_16_direct_api_call_cannot_bypass_role_restrictions(client):
    """Scenario 16: Directly calling backend API cannot bypass RBAC restrictions."""
    token = create_dev_token("analyst1")
    # Analyst tries to directly call the Approving-Officer-only export endpoint
    r = await client.post(
        "/dossier/DOS-001/export",
        json={"confirm": True, "export_format": "JSON"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
    assert _get_err_code(r) == "FORBIDDEN"


@pytest.mark.asyncio
async def test_17_changing_frontend_role_claim_cannot_grant_backend_privileges(client):
    """Scenario 17: Sending spoofed frontend role headers cannot override verified token identity."""
    token = create_dev_token("analyst1")  # Token is genuinely for ANALYST role
    spoofed_headers = {
        "Authorization": f"Bearer {token}",
        "X-User-Role": "APPROVING_OFFICER",
        "X-Role": "APPROVING_OFFICER",
        "X-Simulated-Role": "APPROVING_OFFICER",
    }
    r = await client.post(
        "/dossier/DOS-001/export",
        json={"confirm": True, "export_format": "JSON"},
        headers=spoofed_headers,
    )
    assert r.status_code == 403
    assert _get_err_code(r) == "FORBIDDEN"


# ─────────────────────────────────────────────────────────────
# 7. Step 7B Hardening: Audit RBAC Consistency and Token Expiry
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_h01_auditor_can_view_audit(client):
    """Hardening 1: Auditor role can view the audit log."""
    token = create_dev_token("auditor1")
    r = await client.get("/audit", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_h02_auditor_can_verify_audit(client):
    """Hardening 2: Auditor role can verify the audit ledger integrity."""
    token = create_dev_token("auditor1")
    r = await client.get("/audit/verify", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["valid"] is True


@pytest.mark.asyncio
async def test_h03_analyst_cannot_view_or_verify_audit(client):
    """Hardening 3: Analyst role cannot view or verify the audit ledger (403)."""
    token = create_dev_token("analyst1")
    headers = {"Authorization": f"Bearer {token}"}

    r_view = await client.get("/audit", headers=headers)
    assert r_view.status_code == 403
    assert _get_err_code(r_view) == "FORBIDDEN"

    r_verify = await client.get("/audit/verify", headers=headers)
    assert r_verify.status_code == 403
    assert _get_err_code(r_verify) == "FORBIDDEN"


@pytest.mark.asyncio
async def test_h04_inspector_cannot_verify_audit(client):
    """Hardening 4: Inspector role cannot verify the audit ledger (403)."""
    token = create_dev_token("inspector1")
    r = await client.get("/audit/verify", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert _get_err_code(r) == "FORBIDDEN"


@pytest.mark.asyncio
async def test_h05_approving_officer_cannot_verify_audit(client):
    """Hardening 5: Approving Officer role cannot verify the audit ledger (403)."""
    token = create_dev_token("officer1")
    r = await client.get("/audit/verify", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert _get_err_code(r) == "FORBIDDEN"


@pytest.mark.asyncio
async def test_h06_liaison_cannot_verify_audit(client):
    """Hardening 6: Liaison role cannot verify the audit ledger (403)."""
    token = create_dev_token("liaison1")
    r = await client.get("/audit/verify", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert _get_err_code(r) == "FORBIDDEN"


@pytest.mark.asyncio
async def test_h07_valid_unexpired_token_succeeds(client):
    """Hardening 7: Valid unexpired development token succeeds."""
    token = create_dev_token("analyst1", ttl_seconds=3600)
    r = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["user_id"] == "analyst1"


@pytest.mark.asyncio
async def test_h08_expired_token_returns_401(client):
    """Hardening 8: Expired development token returns 401 with TOKEN_EXPIRED."""
    # Create token that expired 10 seconds ago
    token = create_dev_token("analyst1", ttl_seconds=-10)
    r = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert _get_err_code(r) == "TOKEN_EXPIRED"


@pytest.mark.asyncio
async def test_h09_malformed_expiry_returns_401(client):
    """Hardening 9: Malformed non-integer timestamp claims return 401."""
    # Invalid integer for expiry
    malformed_token = "dev-token-analyst1.1729800000.not_a_valid_number.abcdef0123456789"
    r = await client.get("/me", headers={"Authorization": f"Bearer {malformed_token}"})
    assert r.status_code == 401
    assert _get_err_code(r) == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_h10_tampering_with_iat_or_exp_invalidates_signature(client):
    """Hardening 10: Modifying iat or exp timestamps invalidates cryptographic signature (401)."""
    valid_token = create_dev_token("analyst1", ttl_seconds=3600)
    parts = valid_token.removeprefix("dev-token-").split(".")
    uid, iat_val, exp_val, sig = parts[0], parts[1], parts[2], parts[3]

    # Tamper with exp: extend expiry by 100000 seconds
    tampered_exp_token = f"dev-token-{uid}.{iat_val}.{int(exp_val) + 100000}.{sig}"
    r1 = await client.get("/me", headers={"Authorization": f"Bearer {tampered_exp_token}"})
    assert r1.status_code == 401
    assert _get_err_code(r1) == "INVALID_TOKEN"

    # Tamper with iat
    tampered_iat_token = f"dev-token-{uid}.{int(iat_val) - 50000}.{exp_val}.{sig}"
    r2 = await client.get("/me", headers={"Authorization": f"Bearer {tampered_iat_token}"})
    assert r2.status_code == 401
    assert _get_err_code(r2) == "INVALID_TOKEN"

