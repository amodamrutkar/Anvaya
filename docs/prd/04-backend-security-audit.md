# PRD 4 of 5: Backend, Security and Audit (Member 4)

**Branch:** `feat/backend` | **You own:** `services/api/` (package `sutradhar_api`), `contracts/`, and the root files: `Makefile`, `docker-compose.yml`, `README.md`, `CODEOWNERS`, `.gitignore`, `scripts/`
**Read first:** `docs/prd/00-MAIN-PRD.md`, especially Sections 5 to 11 and Appendix A. If this PRD conflicts with the main PRD, the main PRD wins.

---

## 1. Your mission

Make the system **trustworthy** and hold the five parts together. You own who can ask what, what answers come back, and the permanent record of every action. In a police setting a clever tool nobody trusts is useless. Cross-agency sharing is a trust problem before it is a technology problem, so our answer lives in your part: **share answers, not data, and log everything.**

You are also the integration hub: the scaffold on Day 0, the API everyone calls, the Docker setup for the one-command offline demo, and the guardrail script that stops answer-key leakage.

## 2. User stories

- As a station inspector, I ask "does this phone appear in any open case in another agency?" and get MATCH / NO_MATCH / MAYBE with a reason, never raw records.
- As a liaison, I see queries made against my agency, with purpose and case reference.
- As an auditor, I verify that the audit log has not been altered, and I can see a tampering attempt detected.
- As an approving officer, I export a dossier only after an explicit confirmation, which is logged.
- As a teammate, I call a stable, documented API that already returns fixture data on Day 1.

## 3. Deliverables

| # | Deliverable | Milestone |
|---|---|---|
| B0 | **Scaffold** (Appendix A of the main PRD): layout, schemas, fixtures, Makefile, compose, CODEOWNERS, leak-check script | M0 |
| B1 | API serving fixtures with roles and audit chain | M1 |
| B2 | Real endpoints on `artifacts/` (search, entity, graph, roles, bridges, review queue, unlink) | M2 |
| B3 | Federated query with purpose, roles, rate limit, hashed matching, inbox | M2 to M3 |
| B4 | Audit log with verify and dev tamper demo | M3 |
| B5 | Mock connectors (`SIMULATED_*`) and `/connectors/status` | M3 |
| B6 | Dossier endpoints with export confirmation | M3 |
| B7 | Kumbh simulation, alerts and confirm | M4 |
| B8 | `make demo` offline compose, `make demo-check` smoke test, backup recording support | M4 to M5 |

## 4. Functional requirements

### 4.1 Contracts and scaffold (F-all)
- Own `contracts/schemas/*.schema.json`, `contracts/fixtures/`, `contracts/openapi.json` (regenerate on every API change).
- Fixtures cover **every artifact and every endpoint response**, using the Rakesh Pawar story. `scripts/validate_fixtures.py` validates them.
- **Fixture fallback:** if `artifacts/` is missing, the API serves from `contracts/fixtures/` (`ARTIFACTS_DIR` env var, default `artifacts/`). This lets the frontend and everyone else build before the pipeline exists.
- Announce every contract change in the team chat and keep a `contracts/CHANGELOG.md`.

### 4.2 Simulated agencies
Three agency stores built from `data/<version>/<AGENCY>/` into separate SQLite files (`STATE_POLICE`, `MAHA_CYBER`, `CENTRAL_AGENCY`), plus `app.db` for users, grants, decisions, audit and alerts. A small repository layer per agency; the API never joins across agency stores except through the federated query module.

### 4.3 Roles, purposes, grants (F10)
- Seeded demo users (one per role, plus agency) per main PRD 10.1. Auth: header `X-Demo-User` (no passwords; clearly a demo).
- Every federated query needs `purpose` (`INVESTIGATION`, `ALERT_VERIFICATION`, `AUDIT`) and a `case_ref` matching `^CASE-[A-Z]{3}-\d{6}$` or a Kumbh alert id.
- **Grants** with expiry: a table of `(user, agency, permitted purposes, expires_at)`; expired grants fail with `FORBIDDEN` and an audit entry.
- Rate limit: 20 queries per minute per user.
- Permission matrix enforced in one place (a dependency), with tests per role per endpoint.

### 4.4 Federated query (F10)
`POST /federated/query` (main PRD 9). Behaviour:
1. Validate user, role, purpose, case_ref, grant, rate limit.
2. Normalise the identifier (same rules as ER).
3. **Hashed matching:** compare `HMAC-SHA256(salt, identifier)` against per-agency hashed indexes of identifiers (phones, accounts, vehicles), built at startup with a per-run salt. The asking side never sees another agency's raw values. For `PERSON_NAME_FATHER`, use the ER-normalised name+father key and allow `MAYBE` with confidence < 0.85.
4. Never match against the asking agency's own store (cross-agency only), unless `AUDIT` purpose.
5. Response: `MATCH | NO_MATCH | MAYBE`, `confidence`, `reason_code` (`OPEN_CASE_MATCH`, `CLOSED_CASE_MATCH`, `NO_RECORD`, `AMBIGUOUS_IDENTITY`), `reason_text`, `owning_agency_notified`, `audit_seq`. **No raw record content, no record ids, no names.**
6. On MATCH, create an inbox item for the owning agency (visible at `GET /agency/{agency}/inbox`); the owning liaison may later approve a follow-up disclosure (stretch; log only).
7. Every query and response goes to the audit log.
Stretch: private set intersection style matching beyond salted hashes (documented, not required).

### 4.5 Audit log (F11)
- Table `audit(seq, ts, actor, role, action, purpose, case_ref, summary, prev_hash, hash)`; append-only (no UPDATE/DELETE in code paths; DB triggers block them).
- `hash = sha256(prev_hash + canonical_json(entry without hash))`; genesis `prev_hash` = 64 zeros.
- Log: logins (demo), searches, entity views, review decisions, links/unlinks, federated queries and answers, dossier generate and export, Kumbh simulate/confirm/dismiss, auth failures.
- `GET /audit/verify` walks the chain and returns `{valid, entries, head_hash, broken_at}`.
- `POST /audit/dev/tamper` (only when `DEMO_TAMPER=1`) corrupts one entry so the UI can show detection; `POST /audit/dev/repair` restores from a backup copy.
- **Blockchain decision:** a full blockchain adds no proof beyond this hash chain for a single-operator demo. Implement the hash chain. In the pitch, describe how the head hash could be anchored with a second agency or witness to get multi-party trust. Do not build a blockchain.

### 4.6 Human-in-the-loop gates
Review decisions need `reason`; unlink needs `reason`; dossier export needs `confirm: true` and role `APPROVING_OFFICER`; Kumbh confirm/dismiss needs a click and `reason` on dismiss. All gates reject missing fields with `422` and still log the attempt.

### 4.7 Review queue and unlink (F4)
- `GET /review-queue` lists links with status `PENDING_REVIEW` from `artifacts/er/links.jsonl`, with both mentions' details for side-by-side display.
- Decisions append to `artifacts/decisions/decisions.jsonl` and apply instantly through `sutradhar_er.apply_decisions`; a background task reruns graph (`make graph` equivalent) and updates a `recompute_status` field in `/health`.

### 4.8 Read endpoints
Search (names in both scripts via ER-normalised keys), entity profile, links, community and neighborhood (via `sutradhar_graph` library functions or by reading artifacts), roles, mule chains, bridges, path, dossier generate/read/export, metrics, connectors status. Response shapes exactly as main PRD 8 and 9.

### 4.9 Mock connectors (B5)
Package `sutradhar_api/connectors/` with `SimulatedCCTNS`, `SimulatedMahaCrimeOS`, `SimulatedMahaCyber`, `SimulatedNATGRID`. Each exposes the call a real connector would need (e.g. `fetch_fir(record_id)`, `fetch_complaint(...)`, `query_identifier(...)`), reads from the data files, and returns `simulated: true`. `/connectors/status` lists them. Document the real integration shape in `services/api/CONNECTORS.md` (what a real connector would require, without claiming access).

### 4.10 Kumbh mode (F12)
Read `data/kumbh/events.jsonl`. `POST /kumbh/simulate/next` plays the next event. Rules: a `WATCHLIST_SIGHTING` whose subject token maps to a community member raises an alert (reason, confidence, linked community); a `SCAM_PATTERN` matching accounts in a mule chain raises an alert; a `MISSING_PERSON` event with no gang link raises **no** organized-crime alert (control case). Alerts have state `OPEN | CONFIRMED | DISMISSED`; no action is taken without confirmation.

### 4.11 Privacy and legal framing
Document in `services/api/PRIVACY.md`: purpose limitation, data minimisation, security, accountability, with a note that law-enforcement exemptions exist under India's data protection law. **Confirm exact legal wording from a reliable source before the pitch**; mark it unverified until then.

### 4.12 Tooling and reliability
- `make demo` = `docker compose up` for api + web with prebuilt artifacts; no internet.
- `scripts/check_no_truth_leak.sh` as in main PRD Section 6.
- `make demo-check`: scripted calls that walk the demo path (search Rakesh Pawar → entity → community → bridge → mule chain → dossier → federated query → audit verify → Kumbh simulate) and fail on any non-2xx.
- CORS allows the web origins only.

## 5. Technical design notes

- FastAPI + pydantic v2 models generated from or validated against `contracts/schemas`. SQLite via stdlib; no external services.
- Layout: `sutradhar_api/{main,deps,auth,policy,audit,federated,stores,routes/*,connectors,kumbh,recompute}.py`.
- One policy module decides permissions; no ad hoc `if role ==` scattered in routes.
- Import ER and graph packages as libraries (`sutradhar_er`, `sutradhar_graph`); read artifacts from disk otherwise.
- Tests with pytest + httpx: permissions per role, audit chain integrity, tamper detection, federated query never leaks fields, rate limit, grant expiry.
- Latency targets: search < 500 ms, community < 1 s on v2.

## 6. Milestones

| Milestone | You deliver |
|---|---|
| M0 | B0 scaffold pushed to `main` (everyone waits on this; do it first) |
| M1 | B1: API over fixtures, auth by header, audit chain, OpenAPI, validate_fixtures |
| M2 | B2, start B3: real read endpoints, review queue, unlink, basic federated query |
| M3 | B3 complete, B4, B5, B6 |
| M4 | B7, B8, performance and security pass |
| M5 | Freeze; run `make demo-check` on a clean clone; record fallback video with M5 |

## 7. Acceptance criteria

- [ ] Fixtures validate against schemas; API responses validate against schemas.
- [ ] Each role can do only what main PRD 10.1 allows (test matrix).
- [ ] Federated responses contain **only** the specified fields (test scans responses for any name, record id, or raw identifier from another agency).
- [ ] Audit chain verifies; tamper endpoint breaks it; verify reports the broken `seq`.
- [ ] Dossier export fails without `confirm: true` or without the right role, and both attempts are logged.
- [ ] Kumbh E3 (missing person) creates no organized-crime alert; E1 and E2 do.
- [ ] `make demo` starts offline; `make demo-check` passes on a clean clone.
- [ ] `check_no_truth_leak.sh` passes.
- [ ] Everything simulated is labelled `simulated: true`.

## 8. Dependencies and handoffs

| You give | To | What |
|---|---|---|
| Stable API + fixtures + OpenAPI | Everyone, esp. M5 | `contracts/` |
| Agency partition needs | M1 | confirm the three-agency split |
| Logging hooks | M2, M3 | functions/events to call; decisions file format |
| Access and audit screens' data | M5 | endpoints above |
| Scaffold | Everyone | M0 |

You need: ER/graph function signatures from M2/M3; screen needs from M5; Kumbh events from M1.

## 9. Risks

- Over-engineering security instead of one clear flow: build the single federated-query-plus-audit flow first.
- A blockchain with no added proof: do not build one (see 4.5).
- Claiming real integration: everything labelled simulated.
- A fragile setup on demo day: offline compose, smoke test, backup video.
- Becoming the bottleneck: ship fixtures-first so the others are never blocked.

## 10. Git rules

Work on `feat/backend`. You may edit `services/api/`, `contracts/`, root files, `scripts/`. Commit format `api: ...`, `contracts: ...`. Contract changes go to `main` by small PR and are announced. Rebase on `main` daily.

---

## 11. Antigravity prompt (copy and paste)

```
You are Member 4 (Backend, Security and Audit) on the Sutradhar project. Branch: feat/backend (the scaffold in step 0 goes to main first).

FIRST read, fully: docs/prd/00-MAIN-PRD.md (especially Sections 5 to 11 and Appendix A) and docs/prd/04-backend-security-audit.md. They are the source of truth. If something is unclear, make the smallest reasonable assumption, record it in docs/prd/ASSUMPTIONS-backend.md, and continue.

SCOPE: You may create or edit ONLY services/api/, contracts/, scripts/, Makefile, docker-compose.yml, README.md, CODEOWNERS, .gitignore, and docs/prd/ASSUMPTIONS-backend.md. Do not implement NLP, graph, data generation or UI logic; call those parts as libraries or read their artifacts. Never use real data. No runtime network calls.

STEP 0 (do this first, then stop and tell me the git commands to push main and create branches): execute the scaffold prompt in Appendix A of docs/prd/00-MAIN-PRD.md.

THEN BUILD on feat/backend, in order, committing after each step:
1. FastAPI app sutradhar_api with X-Demo-User auth, seeded demo users per role and agency, one central policy module, pydantic models validated against contracts/schemas, CORS for web origins, ARTIFACTS_DIR with fallback to contracts/fixtures/.
2. Hash-chained audit log (append-only with DB triggers), audit verify, dev tamper and repair endpoints enabled only with DEMO_TAMPER=1, tests for integrity and tamper detection.
3. Read endpoints per main PRD Section 9: search (both scripts), entity, links, communities, neighborhood, path, roles, mule chains, bridges, metrics, health (dataset_version, simulated true, recompute_status).
4. Review queue, decisions (written to artifacts/decisions/decisions.jsonl), unlink, instant apply via sutradhar_er.apply_decisions, background recompute.
5. Three SQLite agency stores plus app.db; federated query with purpose and case_ref validation, grants with expiry, rate limit, per-run salted HMAC hashed matching, reason codes, inbox for owning agency; responses must never contain names, record ids or raw identifiers from another agency.
6. Dossier generate/read/export with confirm and role gating; every gate logs attempts.
7. Mock connectors SimulatedCCTNS, SimulatedMahaCrimeOS, SimulatedMahaCyber, SimulatedNATGRID, /connectors/status, services/api/CONNECTORS.md and PRIVACY.md (mark legal wording unverified).
8. Kumbh simulation from data/kumbh/events.jsonl with alert rules (watchlist, scam pattern; missing-person control case raises no alert), confirm/dismiss endpoints.
9. Makefile targets from main PRD Section 11, docker compose for offline demo, scripts/check_no_truth_leak.sh, make demo-check smoke test, regenerate contracts/openapi.json and contracts/CHANGELOG.md.
10. Tests with pytest and httpx: permission matrix per role, federated no-leak test, rate limit, grant expiry, gate logging, Kumbh control case.

QUALITY BAR: one clear trust flow, everything auditable and labelled simulated, fixtures-first so teammates are never blocked. Run tests after each step and fix failures. At the end print a summary: endpoints, how to run, test results, assumptions, open questions.
```
