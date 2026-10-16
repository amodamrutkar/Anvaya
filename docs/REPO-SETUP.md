# Sutradhar — Repository Setup and Architecture Reference

> **This document is the single source of truth for repository structure, ownership rules, workflow conventions, and Antigravity agent instructions.**
> Every member must read this in full before writing a single line of code.
> Every Antigravity prompt must be consistent with the rules in this file.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Final Repository Tree](#2-final-repository-tree)
3. [Ownership Rules](#3-ownership-rules)
4. [Contract Rules](#4-contract-rules)
5. [Data and Truth Protection](#5-data-and-truth-protection)
6. [Branch Rules](#6-branch-rules)
7. [First-Day Workflow](#7-first-day-workflow)
8. [Integration Workflow](#8-integration-workflow)
9. [Antigravity Rules](#9-antigravity-rules)
10. [Contracts-Generation Workflow](#10-contracts-generation-workflow)
11. [PRD Synchronization Rules](#11-prd-synchronization-rules)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. System Overview

**Sutradhar** (Hindi: सूत्रधार, "narrator" / "thread-holder") is a multi-agency financial intelligence and entity-resolution platform built as a hackathon demonstration system.

The system ingests records from three synthetic law-enforcement agency siloes, resolves entities across them, builds a relationship graph, and surfaces actionable intelligence through a secure API consumed by a web dashboard.

### Pipeline (Canonical Data Flow)

```
[Synthetic Data]  ──M1──►  [NLP / Entity Resolution]  ──M2──►  [Graph / Analytics]
                                                                        │
                                                                        ▼ M3
                                                               [Backend API / Security]  ──M4──►  [Frontend / Dashboard]
                                                                                                          M5
```

The architecture is **NOT** simply "frontend + backend". It is a five-stage pipeline:

| Stage | Service | Owner | Description |
|-------|---------|-------|-------------|
| 1 | `services/data_gen/` + `services/eval/` | M1 | Synthetic data generation and quality evaluation |
| 2 | `services/nlp/` | M2 | NLP entity extraction and cross-agency entity resolution |
| 3 | `services/graph/` | M3 | Graph construction, community detection, dossier generation |
| 4 | `services/api/` | M4 | Authenticated REST API, audit trail, security layer |
| 5 | `apps/web/` | M5 | Interactive dashboard, storytelling, visualisation |

### Data Sources (Synthetic)

| Source | Type | Location |
|--------|------|----------|
| CENTRAL_AGENCY | Criminal records | `data/v1/CENTRAL_AGENCY/` |
| MAHA_CYBER | Cyber crime + financial accounts | `data/v1/MAHA_CYBER/` |
| STATE_POLICE | FIR and incident records | `data/v1/STATE_POLICE/` |
| kumbh | Live event stream (Kumbh Mela scenario) | `data/kumbh/` |

All data is **entirely synthetic**. No real person, organisation, or case is represented.

---

## 2. Final Repository Tree

This is the canonical, enforced structure. Do not create directories outside this tree without a team ADR recorded in `docs/decisions/`.

```
sutradhar/
├── .editorconfig
├── .env.example                          ← env var documentation (no real secrets)
├── .gitattributes
├── .gitignore
├── .pre-commit-config.yaml
├── CONTRIBUTING.md
├── Makefile                              ← M4 owns; all common dev targets here
├── NOTICE-SYNTHETIC-DATA.md             ← M1 owns; data disclaimer
├── README.md                            ← project landing page
├── docker-compose.yml                   ← M4 owns; orchestrates all services
├── pyproject.toml                       ← root workspace config (ruff, mypy, pytest)
├── requirements-dev.txt
│
├── .github/                             ── M4 owns ──────────────────────────────
│   ├── CODEOWNERS
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── ISSUE_TEMPLATE/
│   │   └── contract-change.md
│   └── workflows/
│       └── ci.yml
│
├── apps/                                ── M5 owns ──────────────────────────────
│   └── web/                             ← THE frontend. No other frontend exists.
│       ├── Dockerfile
│       ├── package.json
│       ├── src/
│       └── public/
│
├── artifacts/                           ── Generated output (gitignored) ─────────
│   └── (pipeline output; never committed)
│
├── contracts/                           ── M4 owns ──────────────────────────────
│   ├── CHANGELOG.md
│   ├── README.md
│   ├── openapi.json                     ← THE API contract. Single source of truth.
│   ├── fixtures/
│   │   ├── MANIFEST.json
│   │   ├── api/                         ← per-endpoint JSON fixture responses
│   │   ├── artifacts/                   ← fixture pipeline outputs (er/, graph/, decisions/)
│   │   └── data/                        ← fixture agency source records
│   └── schemas/                         ← JSON Schema + Pydantic model exports
│
├── data/                                ── M1 owns ──────────────────────────────
│   ├── DATASET_CARD.md
│   ├── dev/                             ← scratch data for development
│   ├── kumbh/
│   │   └── events.jsonl
│   ├── v0/                              ← initial synthetic dataset version
│   │   ├── CENTRAL_AGENCY/
│   │   ├── MAHA_CYBER/
│   │   └── STATE_POLICE/
│   └── v1/                              ← current canonical synthetic dataset version
│       ├── CENTRAL_AGENCY/
│       ├── MAHA_CYBER/
│       └── STATE_POLICE/
│
│   NOTE: data/truth/ MUST NOT be committed. See Section 5.
│
├── docs/
│   ├── REPO-SETUP.md                    ← THIS FILE
│   ├── decisions/                       ← Architecture Decision Records (ADRs)
│   │   └── ADR-template.md
│   ├── pitch/                           ── M5 owns ───────────────────────────
│   │   ├── backup-plan.md
│   │   ├── cast.md
│   │   ├── deck-outline.md
│   │   ├── demo-script.md
│   │   ├── numbers.md
│   │   └── qa.md
│   └── prd/                             ← All PRDs live here
│       ├── 00-MAIN-PRD.md               ← M4 authors; defines system scope
│       ├── 01-data-synthetic.md         ← M1 authors
│       ├── 02-nlp-entity-resolution.md  ← M2 authors
│       ├── 03-graph-analytics.md        ← M3 authors
│       ├── 04-backend-security-audit.md ← M4 authors
│       └── 05-frontend-storytelling.md  ← M5 authors
│
├── scripts/                             ── Shared tooling ────────────────────────
│   ├── check_no_truth_leak.sh           ← CI gate: blocks commits to data/truth/
│   ├── check_scope.sh                   ← CI gate: blocks out-of-boundary edits
│   ├── demo_check.py                    ← pre-demo validation
│   ├── setup_check.sh                   ← environment validation
│   └── validate_fixtures.py             ← validates contracts/fixtures/ completeness
│
└── services/                            ── Per-member service directories ────────
    ├── api/                             ── M4 owns ───────────────────────────
    │   ├── Dockerfile
    │   ├── pyproject.toml
    │   ├── sutradhar_api/               ← Python package: THE backend
    │   │   ├── __init__.py
    │   │   ├── __main__.py
    │   │   ├── connectors/
    │   │   └── routes/
    │   └── tests/
    │       └── test_api_smoke.py
    │
    ├── data_gen/                        ── M1 owns ───────────────────────────
    │   ├── pyproject.toml
    │   ├── sutradhar_data/
    │   │   ├── __init__.py
    │   │   ├── __main__.py
    │   │   └── lexicons/
    │   └── tests/
    │       └── test_data_gen_smoke.py
    │
    ├── eval/                            ── M1 owns ───────────────────────────
    │   ├── pyproject.toml
    │   ├── sutradhar_eval/
    │   │   ├── __init__.py
    │   │   └── __main__.py
    │   └── tests/
    │       └── test_eval_smoke.py
    │
    ├── graph/                           ── M3 owns ───────────────────────────
    │   ├── pyproject.toml
    │   ├── sutradhar_graph/
    │   │   ├── __init__.py
    │   │   ├── __main__.py
    │   │   └── dossier_rules.yaml
    │   └── tests/
    │       └── test_graph_smoke.py
    │
    └── nlp/                             ── M2 owns ───────────────────────────
        ├── pyproject.toml
        ├── sutradhar_er/                ← IMPORTANT: package is named sutradhar_er
        │   ├── __init__.py              ←            NOT sutradhar_nlp
        │   └── __main__.py
        └── tests/
            └── test_er_smoke.py
```

### Hard Prohibitions on Directory Names

The following directories **must never be created** anywhere in this repository:

| Forbidden Path | Correct Alternative |
|----------------|---------------------|
| `frontend/` | `apps/web/` |
| `backend/` | `services/api/` |
| `api/` at root | `services/api/` |
| `web/` at root | `apps/web/` |
| `apps/frontend/` | `apps/web/` |
| `services/backend/` | `services/api/` |
| `services/er/` | `services/nlp/` |
| `services/analytics/` | `services/graph/` |
| `services/data/` | `services/data_gen/` |
| `services/evaluation/` | `services/eval/` |
| `services/nlp/sutradhar_nlp/` | `services/nlp/sutradhar_er/` |
| `services/api/contracts/` | `contracts/` at root |
| `services/api/schemas/` | `contracts/schemas/` at root |
| `src/` at root | per-service package directories |
| `tests/` at root | per-service `tests/` subdirectories |

---

## 3. Ownership Rules

### Summary Table

| Path | Owner | Notes |
|------|-------|-------|
| `data/` | **M1** | All versions; all agency partitions |
| `services/data_gen/` | **M1** | Package: `sutradhar_data` |
| `services/eval/` | **M1** | Package: `sutradhar_eval` |
| `NOTICE-SYNTHETIC-DATA.md` | **M1** | |
| `data/DATASET_CARD.md` | **M1** | |
| `docs/prd/01-data-synthetic.md` | **M1** | |
| `services/nlp/` | **M2** | Package: `sutradhar_er` |
| `docs/prd/02-nlp-entity-resolution.md` | **M2** | |
| `services/graph/` | **M3** | Package: `sutradhar_graph` |
| `docs/prd/03-graph-analytics.md` | **M3** | |
| `services/api/` | **M4** | Package: `sutradhar_api` |
| `contracts/` | **M4** | Entire directory |
| `.github/` | **M4** | All workflows and templates |
| `Makefile` | **M4** | |
| `docker-compose.yml` | **M4** | |
| `pyproject.toml` (root) | **M4** | |
| `requirements-dev.txt` | **M4** | |
| `.env.example` | **M4** | |
| `.gitignore` | **M4** | |
| `.editorconfig` | **M4** | |
| `.gitattributes` | **M4** | |
| `.pre-commit-config.yaml` | **M4** | |
| `README.md` | **M4** | |
| `CONTRIBUTING.md` | **M4** | |
| `docs/REPO-SETUP.md` | **M4** | THIS FILE |
| `docs/prd/00-MAIN-PRD.md` | **M4** | |
| `docs/prd/04-backend-security-audit.md` | **M4** | |
| `docs/decisions/` | **M4** | ADR management |
| `scripts/` | **M4** (lead) | All members may read; M4 maintains |
| `apps/web/` | **M5** | Entire web application |
| `docs/pitch/` | **M5** | Deck, script, Q&A |
| `docs/prd/05-frontend-storytelling.md` | **M5** | |
| `artifacts/` | **Generated** | No member owns this; it is pipeline output |

### Cross-Member Editing Rules

1. **Never edit another member's service directory** without their explicit agreement and a joint PR.
2. **`contracts/` is edited exclusively by M4**, but all members must review and approve PRs that change `contracts/openapi.json`.
3. **`contracts/fixtures/` may be updated by the member who owns that fixture layer** (M1 for `data/`, M2 for `artifacts/er/`, M3 for `artifacts/graph/`, M4 for `api/`), but all updates must go through PR.
4. **`scripts/` changes require M4 approval** since scripts gate CI for all members.
5. Members may read any file in the repository. Restrictions apply only to commits.

### Package Name Cross-Reference

| Service Directory | Python Package | Entry Point |
|-------------------|---------------|-------------|
| `services/data_gen/` | `sutradhar_data` | `python -m sutradhar_data` |
| `services/eval/` | `sutradhar_eval` | `python -m sutradhar_eval` |
| `services/nlp/` | `sutradhar_er` | `python -m sutradhar_er` |
| `services/graph/` | `sutradhar_graph` | `python -m sutradhar_graph` |
| `services/api/` | `sutradhar_api` | `python -m sutradhar_api` |

> **Note on `sutradhar_er`:** The NLP service directory is `services/nlp/` because the domain is natural language processing. The Python package is named `sutradhar_er` because the primary function is Entity Resolution. These names are intentionally different. Do **not** create `sutradhar_nlp/`. Do **not** rename `sutradhar_er/` to `sutradhar_nlp/`.

---

## 4. Contract Rules

### What is a contract?

A contract is any interface definition that one member depends on from another member's work. All contracts live in `contracts/`.

### The Three Contract Layers

```
contracts/
├── openapi.json          ← HTTP API surface (M4 → all consumers)
├── schemas/              ← Data shape definitions (all services publish here)
├── fixtures/
│   ├── api/              ← Expected API response bodies (M4 maintains)
│   ├── data/             ← Fixture source records (M1 maintains)
│   └── artifacts/
│       ├── er/           ← Fixture ER outputs (M2 maintains)
│       ├── graph/        ← Fixture graph outputs (M3 maintains)
│       └── decisions/    ← Fixture review decisions (M4 maintains)
```

### Contract Rules

**Rule C-1: openapi.json is the single API source of truth.**
- No member may hard-code API paths, request shapes, or response shapes that contradict `contracts/openapi.json`.
- M5 generates TypeScript types from `openapi.json`. M4 generates server stubs from `openapi.json`.
- If you need to add or change an endpoint, file a `contract-change` GitHub issue first.

**Rule C-2: Schema changes require a PR with all dependent members as reviewers.**
- Any change to `contracts/schemas/` must include a migration note in `contracts/CHANGELOG.md`.
- Breaking changes (field removal, type change, rename) require a version bump and at least 24 hours for all members to migrate.

**Rule C-3: Fixtures must match the contract.**
- Fixture files in `contracts/fixtures/api/` must be valid responses as defined by `contracts/openapi.json`.
- `scripts/validate_fixtures.py` enforces this. It is run in CI.
- Members may not skip fixture validation to unblock themselves.

**Rule C-4: No direct service-to-service imports.**
- Services communicate via the HTTP API defined in `contracts/openapi.json` at runtime.
- Services must not `import` from another service's Python package.
- For development and testing, services consume `contracts/fixtures/` instead of live upstream services.

**Rule C-5: Contracts directory is never duplicated.**
- `contracts/` exists at repository root. It must not be recreated inside any service, app, or other subdirectory.

### Contract Change Workflow

1. Open a GitHub issue using the `contract-change` template.
2. Describe the change, motivation, and affected members.
3. Get acknowledgement from all affected members in the issue thread.
4. Update `contracts/openapi.json` in a dedicated branch: `contract/describe-change`.
5. Update `contracts/CHANGELOG.md` with the change and date.
6. Update affected `contracts/fixtures/`.
7. Run `python scripts/validate_fixtures.py` locally before pushing.
8. PR requires approval from M4 + the owner of the most-affected downstream service.

---

## 5. Data and Truth Protection

### All Data Is Synthetic

Every record, name, identifier, account number, and event in this repository is **entirely fabricated**. No real person, real agency, real organisation, or real criminal case is represented. The NOTICE-SYNTHETIC-DATA.md file at repository root contains the formal disclaimer.

### The data/truth/ Rule

`data/truth/` is a local-only directory used during ground-truth evaluation. It **must never be committed**.

- `.gitignore` must contain `data/truth/` and `data/*/truth/`.
- `scripts/check_no_truth_leak.sh` is a pre-commit hook that blocks any commit containing files from `data/truth/`.
- CI runs this check as a gate. A failing check blocks merge.
- If you believe you need to commit truth data, you are wrong. Use `contracts/fixtures/` for fixture data.

### Data Versioning

| Directory | Purpose |
|-----------|---------|
| `data/v0/` | Initial dataset. Used for smoke tests. Do not modify once tagged. |
| `data/v1/` | Current canonical dataset. M1 may update during development. |
| `data/dev/` | Scratch space for M1. Not used by other services. Not validated. |
| `data/kumbh/` | Kumbh Mela live-event simulation data. Updated by M1. |

### Secrets Rule

- Secrets (API keys, tokens, passwords, database credentials) live **only** in `.env` (your local copy, gitignored).
- `.env.example` documents the names of required variables with placeholder values.
- **No secret must ever appear in:**
  - A PRD document
  - A prompt sent to Antigravity
  - A commit
  - A fixture file
  - A script
  - A Docker Compose file (use `${ENV_VAR}` references instead)
- If you accidentally commit a secret, rotate it immediately and rewrite history.

---

## 6. Branch Rules

### Branch Naming

| Pattern | Used For | Example |
|---------|---------|---------|
| `main` | Stable, demo-ready code | — |
| `dev` | Integration branch. All members merge here first. | — |
| `m1/description` | M1 feature work | `m1/data-gen-v1` |
| `m2/description` | M2 feature work | `m2/er-blocking` |
| `m3/description` | M3 feature work | `m3/community-detection` |
| `m4/description` | M4 feature work | `m4/jwt-auth` |
| `m5/description` | M5 feature work | `m5/graph-visualisation` |
| `contract/description` | Contract changes | `contract/add-dossier-export` |
| `fix/description` | Bug fixes | `fix/er-duplicate-entities` |

### Merge Rules

1. **No direct push to `main`.** All merges to `main` must go through a PR.
2. **No direct push to `dev`.** Feature branches merge to `dev` first.
3. **All PRs require at least one reviewer.** The reviewer must be from a different member than the author.
4. **CODEOWNERS enforces automatic reviewer assignment.** Do not bypass it.
5. **CI must pass before merge.** A failing CI gate blocks merge; it cannot be overridden.
6. **Contract PRs require M4 approval** regardless of who files the PR.

### Merge Order for Integration

When integrating a demo build:
1. Merge `m1/*` to `dev` first (data must exist before pipeline runs).
2. Merge `m2/*` to `dev` (NLP consumes data).
3. Merge `m3/*` to `dev` (graph consumes ER output).
4. Merge `m4/*` to `dev` (API serves graph output).
5. Merge `m5/*` to `dev` (frontend consumes API).
6. Run full integration smoke test on `dev`.
7. PR `dev` → `main` with all five members as reviewers.

---

## 7. First-Day Workflow

Follow these steps on your first day working in this repository.

### Step 1 — Clone and environment check

```bash
git clone <repo-url>
cd sutradhar
bash scripts/setup_check.sh      # checks Python, Node, Docker versions
cp .env.example .env             # create your local env file; fill in real values
```

### Step 2 — Install development dependencies

```bash
# Python (all services share dev tooling at root)
pip install -e ".[dev]"          # installs ruff, mypy, pytest, pre-commit

# Install pre-commit hooks (runs check_no_truth_leak.sh before every commit)
pre-commit install

# Install your service's dependencies
cd services/<your-service>/
pip install -e ".[dev]"
cd ../..
```

### Step 3 — Install frontend dependencies (M5 only)

```bash
cd apps/web/
npm install
npm run dev                      # verify the dev server starts
cd ../..
```

### Step 4 — Verify contracts are present

```bash
python scripts/validate_fixtures.py
```

This will fail if `contracts/fixtures/MANIFEST.json` is not populated. Contact M4.

### Step 5 — Run your service's smoke test

```bash
cd services/<your-service>/
pytest tests/ -v
cd ../..
```

### Step 6 — Read your PRD

Open `docs/prd/0X-your-prd.md`. If it is empty, write it before implementing.

### Step 7 — Create your working branch

```bash
git checkout dev
git pull origin dev
git checkout -b mX/your-feature-name
```

---

## 8. Integration Workflow

### Local Integration (Docker Compose)

```bash
# Start all services
docker compose up --build

# Services and their default ports
# services/api       → http://localhost:8000
# apps/web           → http://localhost:3000
# (data_gen, eval, nlp, graph are batch/offline services; no persistent port)

# Verify API is healthy
curl http://localhost:8000/health

# Verify frontend reaches API
open http://localhost:3000
```

### Pipeline Execution Order (manual / CI)

```bash
# Stage 1: Generate data
python -m sutradhar_data --version v1 --out data/v1/

# Stage 2: Run entity resolution
python -m sutradhar_er --in data/v1/ --out artifacts/er/

# Stage 3: Build graph
python -m sutradhar_graph --in artifacts/er/ --out artifacts/graph/

# Stage 4: Load into API (API reads from artifacts/)
python -m sutradhar_api

# Stage 5: Open frontend
# npm run dev (in apps/web/)
```

### Fixture-Based Development (offline, no pipeline required)

All services can run against `contracts/fixtures/` instead of live pipeline output. This is the default mode for development and CI.

```bash
# API running against fixtures
SUTRADHAR_MODE=fixture python -m sutradhar_api

# Frontend against fixture API
VITE_API_MODE=fixture npm run dev   # (in apps/web/)
```

### Integration Smoke Test

```bash
# Run all smoke tests across all services
pytest services/api/tests/ services/nlp/tests/ services/graph/tests/ \
       services/data_gen/tests/ services/eval/tests/ -v

# Run fixture validation
python scripts/validate_fixtures.py

# Run demo check
python scripts/demo_check.py
```

---

## 9. Antigravity Rules

These rules govern how Antigravity AI agent prompts must be written for this repository. Violation of these rules will cause the agent to create structurally incorrect files.

### Rule A-1: Always specify the exact target path.

> Bad:  "Create a FastAPI app."
> Good: "Create a FastAPI app in `services/api/sutradhar_api/`."

> Bad:  "Add a React component."
> Good: "Add a React component at `apps/web/src/components/EntityCard.tsx`."

### Rule A-2: Never ask the agent to create top-level directories not in the canonical tree.

The following instructions are **permanently forbidden**:

- "Create a `frontend/` directory" → Use `apps/web/`
- "Create a `backend/` directory" → Use `services/api/`
- "Create an `api/` directory at root" → Use `services/api/`
- "Scaffold the API project" without specifying `services/api/` as the target
- "Create a `src/` directory" → each service has its own package directory

### Rule A-3: Never ask the agent to edit another member's files.

Each prompt must target only the files owned by the member issuing the prompt. If cross-member edits are needed, file a PR and coordinate manually.

### Rule A-4: The NLP package is sutradhar_er.

Any Antigravity prompt for M2 must reference:
- Directory: `services/nlp/`
- Package: `sutradhar_er`

Never ask the agent to create `sutradhar_nlp/` or rename `sutradhar_er/`.

### Rule A-5: Never ask the agent to put secrets in code or documents.

If a prompt requires credentials (database URL, API key, etc.), use environment variable references:

> Bad:  "Set the database URL to postgres://admin:password@localhost/sutradhar"
> Good: "Read the database URL from the `DATABASE_URL` environment variable."

### Rule A-6: Never ask the agent to commit to artifacts/.

`artifacts/` is gitignored pipeline output. Do not ask the agent to write source-controlled files there.

### Rule A-7: Use fixture mode for development prompts.

When asking the agent to build frontend features or API consumers, always specify fixture mode first:

> "Implement the entity search page in `apps/web/src/pages/Search.tsx`. Consume `GET /entities/search` as defined in `contracts/openapi.json`. Use the fixture at `contracts/fixtures/api/GET_entities_search.json` for local development."

### Rule A-8: Antigravity must not be used to modify contracts unilaterally.

Contract changes follow the workflow in Section 4. Antigravity may help draft a contract change, but the draft must be reviewed by M4 and all affected members before being committed.

### Rule A-9: PRDs must not contain real data or secrets.

When asking Antigravity to help write a PRD, use placeholder names, generic scenarios, and no real credentials. The agent must not be given real personal data.

### Rule A-10: Specify the Python package when asking for service work.

Always include the package name so the agent targets the correct directory:

> "In the `sutradhar_er` package at `services/nlp/sutradhar_er/`, implement a blocking function..."

---

## 10. Contracts-Generation Workflow

This section describes how each member generates and publishes their half of the shared contract.

### M4 → All: Generating API Types from openapi.json

M4 maintains `contracts/openapi.json`. When it changes:

1. **Notify all members** by updating `contracts/CHANGELOG.md` and pushing to `contract/*` branch.
2. **M5 regenerates TypeScript types:**
   ```bash
   # in apps/web/
   npx openapi-typescript ../../contracts/openapi.json --output src/types/api.d.ts
   ```
3. **M2, M3 update integration tests** if endpoint shapes changed.
4. **M4 updates fixture files** in `contracts/fixtures/api/` to match new shapes.

### M1 → All: Publishing New Fixture Data

When M1 updates `data/v1/`:

1. Run data generation: `python -m sutradhar_data --version v1`
2. Copy representative samples to `contracts/fixtures/data/`.
3. Update `contracts/fixtures/MANIFEST.json`.
4. Run `python scripts/validate_fixtures.py`.
5. PR to `dev` with M4 as reviewer (M4 validates fixture schema compliance).

### M2 → M3: Publishing ER Output Contract

When M2 changes the entity resolution output schema:

1. Update `contracts/fixtures/artifacts/er/entities.jsonl`, `links.jsonl`, `mentions.jsonl` with representative samples.
2. Update `contracts/schemas/er_output.json` with the new JSON Schema.
3. Notify M3 that the graph input contract has changed.
4. PR with M3 as required reviewer.

### M3 → M4: Publishing Graph Output Contract

When M3 changes the graph output schema:

1. Update `contracts/fixtures/artifacts/graph/` with representative samples.
2. Update `contracts/schemas/graph_output.json` with the new JSON Schema.
3. Notify M4 that the API data source contract has changed.
4. PR with M4 as required reviewer.

### M4 → M5: API Contract Updates

When M4 changes `contracts/openapi.json`:

1. Bump the version field in the OpenAPI document.
2. Update `contracts/CHANGELOG.md`.
3. Post in team channel with diff summary.
4. M5 has 24 hours to raise blockers before the contract PR is merged.

---

## 11. PRD Synchronization Rules

Each member's PRD lives in `docs/prd/`. PRDs define the functional scope for a single pipeline stage. These rules prevent scope creep across member boundaries.

### PRD Hierarchy

```
00-MAIN-PRD.md         ← Parent PRD. Defines the whole system. Written by M4.
├── 01-data-synthetic  ← Child PRD for M1. Inherits data definitions from 00.
├── 02-nlp-er          ← Child PRD for M2. Inherits entity schema from 00.
├── 03-graph           ← Child PRD for M3. Inherits graph schema from 00.
├── 04-backend         ← Child PRD for M4. Inherits API surface from 00.
└── 05-frontend        ← Child PRD for M5. Inherits UI/UX scope from 00.
```

### PRD Synchronization Rules

**Rule P-1: 00-MAIN-PRD.md is the authority.**
If a child PRD contradicts 00-MAIN-PRD.md, the child PRD is wrong. File an issue and resolve with M4.

**Rule P-2: Each PRD defines only its own stage.**
M2's PRD defines entity resolution. It must not define data generation (M1) or graph structure (M3). If M2 needs to reference M1's output, cite the fixture file path, not a re-specification of M1's schema.

**Rule P-3: PRDs reference contracts, not implementation details.**
A PRD may say: "The entity output schema is defined in `contracts/schemas/er_output.json`."
A PRD must not re-copy the JSON schema inline.

**Rule P-4: PRDs must not contain secrets.**
No API keys, passwords, database URLs, or real personal data in any PRD.

**Rule P-5: PRD changes that affect a downstream member require their sign-off.**
If M2 changes the ER output definition in their PRD, M3 must approve (since M3 consumes it).
If M3 changes the graph output definition, M4 must approve.
If M4 changes the API surface in their PRD, M5 must approve.

**Rule P-6: Antigravity prompts for implementation must cite the PRD.**
When issuing an implementation prompt, include: "Implement as specified in `docs/prd/0X-your-prd.md`, Section Y."
This prevents the agent from inventing interfaces not defined in the PRD.

**Rule P-7: PRDs are written before implementation begins.**
No member may ask Antigravity to implement a feature whose PRD section is still empty.

---

## 12. Troubleshooting

### "The CI fixture validation is failing"

```bash
python scripts/validate_fixtures.py
# Read the output. It will name the missing or mismatched fixture file.
# Ensure contracts/fixtures/MANIFEST.json lists all expected files.
# Ensure all fixture files are non-empty valid JSON / JSONL.
```

### "I cannot import from another service"

This is by design. Services must not cross-import. If you need data from another service:
1. In development: consume `contracts/fixtures/artifacts/` directly.
2. In production: call the REST API at `services/api/`.
3. If you need a new API endpoint to expose that data, file a `contract-change` issue.

### "The agent created a frontend/ directory"

1. Do **not** commit this.
2. Delete `frontend/` entirely.
3. Re-issue the prompt with the explicit target path: `apps/web/`.
4. See Rule A-1 and Rule A-2 in Section 9.

### "The agent created a backend/ or api/ directory at root"

1. Do **not** commit this.
2. Delete it.
3. Re-issue the prompt targeting `services/api/sutradhar_api/`.
4. See Rule A-2 in Section 9.

### "The agent renamed sutradhar_er/ to sutradhar_nlp/"

1. Do **not** commit this.
2. Revert: `git checkout -- services/nlp/`
3. Re-issue the prompt explicitly referencing the `sutradhar_er` package.
4. See Rule A-4 in Section 9 and the package name table in Section 3.

### "A secret was accidentally committed"

1. **Rotate the secret immediately.** The old value is now compromised.
2. Rewrite history: `git rebase -i` or `git filter-repo` to remove the commit.
3. Force-push (requires M4 to temporarily lift branch protection).
4. Notify all members to re-pull.
5. Add the secret's variable name to `.env.example` with a placeholder value and a comment.

### "data/truth/ files appeared in git status"

1. Do **not** stage or commit them.
2. Check that `.gitignore` contains `data/truth/` and `data/*/truth/`.
3. Run: `git rm --cached data/truth/ -r` if they were accidentally staged.
4. Verify `pre-commit` is installed: `pre-commit install`.

### "I don't know which fixture to use for my test"

Consult `contracts/fixtures/MANIFEST.json`. It maps every expected fixture file to its purpose, owner, and schema reference.

### "The API and frontend are on different machines and cannot connect"

In `.env`, set:
```
SUTRADHAR_API_URL=http://<api-host>:8000
```
In `apps/web/.env.local`, set:
```
VITE_API_BASE_URL=http://<api-host>:8000
```
The Docker Compose network handles this automatically when using `docker compose up`.

### "I need to add a new top-level directory"

You need a team vote and an ADR. Steps:
1. Describe the need in a GitHub issue.
2. All five members must approve.
3. M4 writes an ADR in `docs/decisions/` using `ADR-template.md`.
4. ADR is merged before the directory is created.

---

*End of REPO-SETUP.md*

*Last updated: 2026-10-17*
*Maintained by: M4 (repository owner / integrator)*
*Questions: open a GitHub issue with label `repo-setup`*
