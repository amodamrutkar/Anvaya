# Assumptions — Backend, Security and Audit (Member 4)

This document records technical and architectural assumptions made during the implementation of Member 4 (M4) deliverables for Sutradhar.

---

## 1. Authentication and Identity
- **Assumption:** In the hackathon / demo environment, full OAuth2/OIDC is replaced by a deterministic, transparent header-based mechanism: `X-Demo-User`.
- **Rationale:** Prevents login friction during live pitch while demonstrating complete RBAC enforcement across 8 distinct user roles and multiple agencies. No production secrets or passwords are required.

## 2. In-Memory DataStore with Dual Fallback
- **Assumption:** The FastAPI application uses an in-memory `DataStore` loaded at startup. It first looks for pipeline outputs in `artifacts/`. If absent or partially missing, it transparently falls back to `contracts/fixtures/`.
- **Rationale:** Ensures that frontend (M5), graph (M3), and ER (M2) can develop and demo independently without requiring an active database daemon or prior pipeline execution.

## 3. Cryptographic Audit Chain vs. Blockchain
- **Assumption:** A single-operator demonstration achieves complete audit tamper-evidence using a SHA-256 hash-chained log (`prev_hash` linking with canonical JSON serialization), rather than a full proof-of-work/stake blockchain.
- **Rationale:** Confirms with Main PRD Section 11 and PRD 4 Section 4.5. Full blockchain adds significant latency and operational overhead with zero additional proof value for an edge police deployment.

## 4. Federated Privacy & Hashed Matching
- **Assumption:** Cross-agency federated queries compute HMAC-SHA256 hashes of identifiers (phones, accounts, vehicles) with a run-time salt. The querying agency receives only `MATCH`, `NO_MATCH`, or `MAYBE` and a standardized reason code.
- **Rationale:** Satisfies law-enforcement data minimisation and inter-agency confidentiality requirements. Zero raw records, PII, or record IDs from other agencies are returned.

## 5. Kumbh Simulation Event Flow
- **Assumption:** `POST /kumbh/simulate/next` advances a sequential cursor through `contracts/fixtures/data/kumbh/events.jsonl` (or `data/kumbh/events.jsonl`).
- **Rationale:** Enables deterministic step-by-step playback during the live demo. Events E1 (`WATCHLIST_SIGHTING`) and E2 (`SCAM_PATTERN`) trigger alerts; control event E3 (`MISSING_PERSON`) does not trigger organized-crime alerts.

## 6. Zero Network Dependencies
- **Assumption:** All services, tests, and demo flows execute completely offline with `docker compose up` or local python virtual environment without internet access.
