# Agency Connectors Integration Specification

> **NOTICE:** All connectors currently implemented in Sutradhar are **simulated mock connectors** (`simulated: true`). No live connections to real government databases, police intranets, or production network feeds exist or are claimed.

## 1. Overview

Sutradhar operates on a federated and decoupled data-sharing principle:
- **Share answers, not data.**
- Agencies maintain custodian control over their internal databases (FIRs, complaints, CDRs, transaction logs).
- Sutradhar queries agency connectors via cryptographically salted, one-way hashed identifiers (HMAC-SHA256).

## 2. Simulated Connectors

| Connector ID | Target Agency / System | Capabilities | Demo Implementation |
|---|---|---|---|
| `SimulatedCCTNS` | Central Agency / CCTNS | Case & FIR cross-referencing | In-memory mock + local JSON fixtures |
| `SimulatedMahaCrimeOS` | State Police (Maharashtra) | State case records, FIR profiles | In-memory mock + local JSON fixtures |
| `SimulatedMahaCyber` | Maharashtra Cyber Police | Mule account tracking, cyber fraud incidents | In-memory mock + local JSON fixtures |
| `SimulatedNATGRID` | Central Federated Gateway | Multi-agency identifier matching | In-memory mock + salted hash index |

## 3. Real-World Production Architecture (Speculative)

In a live law-enforcement deployment, real connectors would require:

### 3.1 Network & Infrastructure Requirements
- **Dedicated MPLS / VPN Tunnel:** Air-gapped or encrypted IPsec site-to-site VPN to state police intranet and central agency gateways.
- **Mutual TLS (mTLS):** Client certificate authentication with hardware security modules (HSM) on both ends.
- **Zero Raw Data Ingestion:** Real connectors would run edge agents in each agency's security zone. Only salted HMAC hash digests and Boolean match assertions (`MATCH` / `NO_MATCH`) cross the boundary.

### 3.2 Protocol & Schema Standards
- **REST/JSON with OAS 3.1** or gRPC over TLS.
- Request payload:
  ```json
  {
    "query_id": "UUIDv4",
    "purpose": "INVESTIGATION",
    "case_reference": "CASE-MUM-2026-004512",
    "hashed_identifier": "HMAC-SHA256(agency_salt, identifier)",
    "timestamp": "ISO-8601"
  }
  ```
- Response payload (Zero PII):
  ```json
  {
    "query_id": "UUIDv4",
    "result": "MATCH | NO_MATCH | MAYBE",
    "reason_code": "OPEN_CASE_MATCH",
    "notified_agency_liaison": true
  }
  ```

### 3.3 Authorization & Governance
- Token-based API access tied to officer service ID and e-Pramaan / National Government SSO.
- Every external query cryptographically logged in an append-only audit trail before dispatch and upon response receipt.
