#!/usr/bin/env python3
"""
scripts/demo_check.py
Smoke-tests the full demo path via the API.
Requires the API to be running (make api or make demo).
Usage: python scripts/demo_check.py [--base-url http://localhost:8000]
Owned by M4.
"""

import argparse
import sys
from typing import Any

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

DEMO_USER = "analyst1"
HEADERS = {"X-Demo-User": DEMO_USER}


def check(
    label: str, response: httpx.Response, expected_status: int = 200
) -> dict[str, Any] | None:
    if response.status_code == expected_status:
        print(f"  PASS [{response.status_code}] {label}")
        try:
            return response.json()
        except Exception:
            return {}
    else:
        print(f"  FAIL [{response.status_code}] {label}")
        print(f"       Response: {response.text[:200]}")
        return None


def run_checks(base_url: str) -> int:
    client = httpx.Client(base_url=base_url, headers=HEADERS, timeout=10.0)
    failures = 0

    print(f"\n=== demo_check: {base_url} ===\n")

    # 1. Health
    r = client.get("/health")
    body = check("GET /health", r)
    if body is None:
        failures += 1
    elif body.get("simulated") is not True:
        print("  WARN: /health did not return simulated: true")

    # 2. Me
    r = client.get("/me")
    if check("GET /me", r) is None:
        failures += 1

    # 3. Entity search — Rakesh Pawar demo hero
    r = client.get("/entities/search", params={"q": "Rakesh Pawar"})
    body = check("GET /entities/search?q=Rakesh Pawar", r)
    entity_id = None
    if body is None:
        failures += 1
    elif isinstance(body, list) and body:
        entity_id = body[0].get("entity_id")
    elif isinstance(body, dict) and body.get("results"):
        entity_id = body["results"][0].get("entity_id")

    # 4. Entity profile
    if entity_id:
        r = client.get(f"/entities/{entity_id}")
        if check(f"GET /entities/{entity_id}", r) is None:
            failures += 1

        r = client.get(f"/entities/{entity_id}/links")
        if check(f"GET /entities/{entity_id}/links", r) is None:
            failures += 1

    # 5. Graph communities
    r = client.get("/graph/communities")
    body = check("GET /graph/communities", r)
    community_id = None
    if body is None:
        failures += 1
    elif isinstance(body, list) and body:
        community_id = body[0].get("community_id")

    # 6. Community detail
    if community_id:
        r = client.get(f"/graph/communities/{community_id}")
        if check(f"GET /graph/communities/{community_id}", r) is None:
            failures += 1

    # 7. Roles
    r = client.get("/roles")
    if check("GET /roles", r) is None:
        failures += 1

    # 8. Bridges
    r = client.get("/bridges")
    if check("GET /bridges", r) is None:
        failures += 1

    # 9. Mule chains
    r = client.get("/mule/chains")
    if check("GET /mule/chains", r) is None:
        failures += 1

    # 10. Review queue
    r = client.get("/review-queue")
    if check("GET /review-queue", r) is None:
        failures += 1

    # 11. Federated query
    payload = {
        "querying_agency": "STATE_POLICE",
        "identifier_type": "PHONE",
        "identifier_value": "9000012345",
        "purpose": "INVESTIGATION",
        "case_ref": "CASE-SPO-000031",
    }
    r = client.post("/federated/query", json=payload)
    body = check("POST /federated/query", r)
    if body is None:
        failures += 1
    else:
        # Verify no raw data in response
        forbidden_fields = ["name", "record_id", "accused", "complainant", "narrative"]
        for field in forbidden_fields:
            if field in body:
                print(f"  FAIL: federated response contains forbidden field: {field}")
                failures += 1

    # 12. Audit verify
    r = client.get("/audit/verify")
    body = check("GET /audit/verify", r)
    if body is None:
        failures += 1
    elif body.get("valid") is not True:
        print(f"  FAIL: audit chain is not valid: {body}")
        failures += 1

    # 13. Kumbh zones
    r = client.get("/kumbh/zones")
    if check("GET /kumbh/zones", r) is None:
        failures += 1

    # 14. Kumbh alerts
    r = client.get("/kumbh/alerts")
    if check("GET /kumbh/alerts", r) is None:
        failures += 1

    # 15. Metrics
    r = client.get("/metrics")
    if check("GET /metrics", r) is None:
        failures += 1

    # 16. Connectors status
    r = client.get("/connectors/status")
    body = check("GET /connectors/status", r)
    if body is None:
        failures += 1

    print(f"\n=== Result: {16 - failures}/16 checks passed ===")
    if failures:
        print(f"FAIL: {failures} check(s) failed.")
        return 1
    print("PASS: All demo checks passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sutradhar demo smoke test")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()
    return run_checks(args.base_url)


if __name__ == "__main__":
    sys.exit(main())
