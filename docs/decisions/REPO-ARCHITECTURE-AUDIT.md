# Repository Architecture Audit

**Audit Date:** 2026-10-17
**Auditor:** Antigravity (pre-implementation, read-only inspection)
**Repository Root:** `sutradhar/`
**Scope:** Structural audit only. No code was written, moved, or modified.

---

## 1. Current Repository Tree

The following is the complete tree as observed by directory inspection. All files marked `[EMPTY]` were confirmed to be 0-byte stub files (single blank line, no content).

```
sutradhar/
├── .editorconfig                        [EMPTY]
├── .env.example                         [EMPTY]
├── .gitattributes                       [EMPTY]
├── .gitignore                           [EMPTY]
├── .pre-commit-config.yaml              [EMPTY]
├── CONTRIBUTING.md                      [EMPTY]
├── Makefile                             [EMPTY]
├── NOTICE-SYNTHETIC-DATA.md             [EMPTY]
├── README.md                            [EMPTY]
├── docker-compose.yml                   [EMPTY]
├── pyproject.toml                       [EMPTY]
├── requirements-dev.txt                 [EMPTY]
│
├── .github/
│   ├── CODEOWNERS                       [EMPTY]
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── ISSUE_TEMPLATE/
│   │   └── contract-change.md
│   └── workflows/
│       └── ci.yml                       [EMPTY]
│
├── apps/
│   └── web/
│       └── Dockerfile                   [EMPTY]
│           (no package.json, no src/, no public/, no framework files)
│
├── artifacts/                           [EMPTY DIRECTORY]
│
├── contracts/
│   ├── CHANGELOG.md                     [EMPTY]
│   ├── README.md                        [EMPTY]
│   ├── openapi.json                     [EMPTY]
│   ├── fixtures/
│   │   ├── MANIFEST.json                [EMPTY]
│   │   ├── api/
│   │   │   ├── GET_agency_inbox.json
│   │   │   ├── GET_audit.json
│   │   │   ├── GET_audit_verify.json
│   │   │   ├── GET_bridges.json
│   │   │   ├── GET_connectors_status.json
│   │   │   ├── GET_dossier_id.json
│   │   │   ├── GET_entities_id.json
│   │   │   ├── GET_entities_id_links.json
│   │   │   ├── GET_entities_search.json
│   │   │   ├── GET_graph_communities.json
│   │   │   ├── GET_graph_communities_id.json
│   │   │   ├── GET_graph_entity_neighborhood.json
│   │   │   ├── GET_graph_path.json
│   │   │   ├── GET_health.json
│   │   │   ├── GET_kumbh_alerts.json
│   │   │   ├── GET_kumbh_zones.json
│   │   │   ├── GET_me.json
│   │   │   ├── GET_metrics.json
│   │   │   ├── GET_mule_chains.json
│   │   │   ├── GET_review-queue.json
│   │   │   ├── GET_roles.json
│   │   │   ├── POST_audit_dev_tamper.json
│   │   │   ├── POST_dossier_export.json
│   │   │   ├── POST_dossier_generate.json
│   │   │   ├── POST_federated_query.json
│   │   │   ├── POST_kumbh_alerts_confirm.json
│   │   │   ├── POST_kumbh_simulate_next.json
│   │   │   ├── POST_links_unlink.json
│   │   │   └── POST_review-queue_decision.json
│   │   ├── artifacts/
│   │   │   ├── decisions/
│   │   │   │   └── decisions.jsonl
│   │   │   ├── er/
│   │   │   │   ├── entities.jsonl
│   │   │   │   ├── links.jsonl
│   │   │   │   └── mentions.jsonl
│   │   │   └── graph/
│   │   │       ├── bridges.json
│   │   │       ├── communities.json
│   │   │       ├── graph.json
│   │   │       ├── mule_chains.json
│   │   │       ├── roles.json
│   │   │       └── dossiers/
│   │   │           └── DOS-001.json
│   │   └── data/
│   │       ├── CENTRAL_AGENCY/
│   │       │   └── records.jsonl
│   │       ├── MAHA_CYBER/
│   │       │   ├── accounts.jsonl
│   │       │   ├── records.jsonl
│   │       │   └── transactions.jsonl
│   │       ├── STATE_POLICE/
│   │       │   └── records.jsonl
│   │       └── kumbh/
│   │           └── events.jsonl
│   └── schemas/                         [EMPTY DIRECTORY]
│
├── data/
│   ├── DATASET_CARD.md                  [EMPTY]
│   ├── dev/                             [EMPTY DIRECTORY]
│   ├── kumbh/
│   │   └── events.jsonl
│   ├── v0/
│   │   ├── CENTRAL_AGENCY/              [EMPTY]
│   │   ├── MAHA_CYBER/                  [EMPTY]
│   │   └── STATE_POLICE/               [EMPTY]
│   └── v1/
│       ├── CENTRAL_AGENCY/              [EMPTY]
│       ├── MAHA_CYBER/                  [EMPTY]
│       └── STATE_POLICE/               [EMPTY]
│
├── docs/
│   ├── REPO-SETUP.md                    [EMPTY]
│   ├── decisions/
│   │   └── ADR-template.md              [EMPTY]
│   ├── pitch/
│   │   ├── backup-plan.md
│   │   ├── cast.md
│   │   ├── deck-outline.md              [EMPTY]
│   │   ├── demo-script.md
│   │   ├── numbers.md
│   │   └── qa.md
│   └── prd/
│       ├── 00-MAIN-PRD.md               [EMPTY]
│       ├── 01-data-synthetic.md         [EMPTY]
│       ├── 02-nlp-entity-resolution.md  [EMPTY]
│       ├── 03-graph-analytics.md        [EMPTY]
│       ├── 04-backend-security-audit.md [EMPTY]
│       └── 05-frontend-storytelling.md  [EMPTY]
│
├── scripts/
│   ├── check_no_truth_leak.sh
│   ├── check_scope.sh
│   ├── demo_check.py
│   ├── setup_check.sh
│   └── validate_fixtures.py
│
└── services/
    ├── api/
    │   ├── Dockerfile                   [EMPTY]
    │   ├── pyproject.toml               [EMPTY]
    │   ├── sutradhar_api/
    │   │   ├── __init__.py              [EMPTY]
    │   │   ├── __main__.py              [EMPTY]
    │   │   ├── connectors/
    │   │   │   └── __init__.py
    │   │   └── routes/
    │   │       └── __init__.py
    │   └── tests/
    │       └── test_api_smoke.py
    ├── data_gen/
    │   ├── pyproject.toml               [EMPTY]
    │   ├── sutradhar_data/
    │   │   ├── __init__.py              [EMPTY]
    │   │   ├── __main__.py              [EMPTY]
    │   │   └── lexicons/                [EMPTY DIRECTORY]
    │   └── tests/
    │       └── test_data_gen_smoke.py
    ├── eval/
    │   ├── pyproject.toml               [EMPTY]
    │   ├── sutradhar_eval/
    │   │   ├── __init__.py              [EMPTY]
    │   │   └── __main__.py              [EMPTY]
    │   └── tests/
    │       └── test_eval_smoke.py
    ├── graph/
    │   ├── pyproject.toml               [EMPTY]
    │   ├── sutradhar_graph/
    │   │   ├── __init__.py              [EMPTY]
    │   │   ├── __main__.py              [EMPTY]
    │   │   └── dossier_rules.yaml       [EMPTY]
    │   └── tests/
    │       └── test_graph_smoke.py
    └── nlp/
        ├── pyproject.toml               [EMPTY]
        ├── sutradhar_er/
        │   ├── __init__.py              [EMPTY]
        │   └── __main__.py              [EMPTY]
        └── tests/
            └── test_er_smoke.py
```

---

## 2. Expected Repository Tree

The following is the canonical tree as specified in the task brief (sourced from the stated REPO-SETUP.md intent, which is currently an empty file — see Section 5 for this conflict):

```
sutradhar/
├── apps/
│   └── web/                    # Member 5 – Frontend
├── services/
│   ├── data_gen/               # Member 1 – Data generation
│   ├── eval/                   # Member 1 – Evaluation
│   ├── nlp/                    # Member 2 – NLP / Entity Resolution
│   ├── graph/                  # Member 3 – Graph / Analytics
│   └── api/                    # Member 4 – Backend / API
├── contracts/                  # Member 4 – Shared contracts
├── data/                       # Member 1
├── artifacts/                  # Generated output
├── docs/
├── scripts/
├── .github/
├── Makefile
├── docker-compose.yml
├── pyproject.toml
├── requirements-dev.txt
├── .env.example
└── README.md
```

---

## 3. Current vs Expected

Legend: PRESENT=exists with content | EMPTY=exists but 0 bytes | MISSING=does not exist | CONFLICT=structural issue

| Path | Expected Owner | Current State | Action Required |
|------|----------------|---------------|-----------------|
| apps/web/ | Member 5 | EMPTY — only an empty Dockerfile stub. No JS framework, no package.json, no src/. | Member 5 must populate. No structural action needed. |
| services/api/ | Member 4 | EMPTY — package scaffold present (sutradhar_api/, routes/, connectors/), all files empty. | Member 4 must populate. |
| services/nlp/ | Member 2 | EMPTY — sutradhar_er/ package scaffold (note: package is named sutradhar_er not sutradhar_nlp). All files empty. | Member 2 must populate. Package name divergence noted in Section 5. |
| services/graph/ | Member 3 | EMPTY — sutradhar_graph/ package scaffold. dossier_rules.yaml stub present but empty. | Member 3 must populate. |
| services/data_gen/ | Member 1 | EMPTY — sutradhar_data/ package scaffold, lexicons/ dir empty. All files empty. | Member 1 must populate. |
| services/eval/ | Member 1 | EMPTY — sutradhar_eval/ package scaffold. All files empty. | Member 1 must populate. |
| contracts/ | Member 4 | EMPTY — openapi.json, README.md, CHANGELOG.md all empty. Fixture JSON files present. schemas/ is empty. | Member 4 must populate stubs. Fixture files in correct location. |
| contracts/schemas/ | Member 4 | MISSING — empty directory, no schema files present. | Member 4 must add schema files. |
| data/ | Member 1 | PARTIAL — kumbh/events.jsonl present. v0/ and v1/ agency subdirs exist but are empty. dev/ is empty. | Member 1 must populate. |
| artifacts/ | Shared generated output | EMPTY DIRECTORY | Correct. Should remain empty until pipeline runs. |
| docs/REPO-SETUP.md | Member 4 / shared | CONFLICT: EMPTY — primary architecture reference has no content. | CRITICAL: Must be authored before implementation. |
| docs/prd/00-MAIN-PRD.md | Member 4 / shared | CONFLICT: EMPTY — main PRD has no content. | CRITICAL: Must be authored before implementation. |
| docs/prd/01-data-synthetic.md | Member 1 | CONFLICT: EMPTY | Member 1 must author before implementing. |
| docs/prd/02-nlp-entity-resolution.md | Member 2 | CONFLICT: EMPTY | Member 2 must author before implementing. |
| docs/prd/03-graph-analytics.md | Member 3 | CONFLICT: EMPTY | Member 3 must author before implementing. |
| docs/prd/04-backend-security-audit.md | Member 4 | CONFLICT: EMPTY | Member 4 must author before implementing. |
| docs/prd/05-frontend-storytelling.md | Member 5 | CONFLICT: EMPTY | Member 5 must author before implementing. |
| README.md | Member 4 / shared | CONFLICT: EMPTY | Must be authored. |
| Makefile | Member 4 | CONFLICT: EMPTY — no build targets. | Member 4 must populate. |
| docker-compose.yml | Member 4 | CONFLICT: EMPTY — no services defined. | Member 4 must populate. |
| pyproject.toml (root) | Member 4 | CONFLICT: EMPTY — no workspace/tool config. | Member 4 must populate. |
| requirements-dev.txt | Member 4 | CONFLICT: EMPTY | Member 4 must populate. |
| .env.example | Member 4 | CONFLICT: EMPTY | Member 4 must populate. |
| .github/CODEOWNERS | Member 4 | CONFLICT: EMPTY — ownership enforcement non-functional. | Member 4 must populate. |
| .github/workflows/ci.yml | Member 4 | CONFLICT: EMPTY | Member 4 must populate. |
| .gitignore | Member 4 | CONFLICT: EMPTY | Member 4 must populate. |
| .pre-commit-config.yaml | Member 4 | CONFLICT: EMPTY | Member 4 must populate. |
| contracts/openapi.json | Member 4 | CONFLICT: EMPTY — API contract not yet authored. | Member 4 must populate. |
| services/*/pyproject.toml | Per-service owner | CONFLICT: All EMPTY — no package metadata, deps, or entry points. | Each member must populate their service's pyproject.toml. |
| services/api/Dockerfile | Member 4 | CONFLICT: EMPTY | Member 4 must populate. |
| apps/web/Dockerfile | Member 5 | CONFLICT: EMPTY | Member 5 must populate. |
| scripts/ | Member 4 / shared | PRESENT — 5 non-empty scripts. | No action required. |
| contracts/fixtures/api/ | Member 4 | PRESENT — 29 fixture JSON files present. | Verify content completeness during development. |
| contracts/fixtures/data/ | Member 1 | PRESENT — agency-partitioned JSONL files present. | Verify content completeness during development. |
| contracts/fixtures/artifacts/ | Member 1/2/3 | PRESENT — ER, graph, decisions artifacts present as fixtures. | Verify content completeness during development. |

---

## 4. Ownership Boundaries

### Member 1 — Data and Evaluation

**Owns:**
- data/ — all subdirectories (v0/, v1/, dev/, kumbh/)
- services/data_gen/ — data generation service (sutradhar_data package)
- services/eval/ — evaluation service (sutradhar_eval package)
- NOTICE-SYNTHETIC-DATA.md
- data/DATASET_CARD.md
- docs/prd/01-data-synthetic.md

**Does NOT own:**
- contracts/ (even though contracts/fixtures/data/ mirrors their data — fixture authorship is a Member 4 coordination concern)
- services/api/, services/nlp/, services/graph/, apps/web/

---

### Member 2 — NLP / Entity Resolution

**Owns:**
- services/nlp/ — NLP service (Python package is named sutradhar_er, not sutradhar_nlp)
- docs/prd/02-nlp-entity-resolution.md

**Does NOT own:**
- contracts/fixtures/artifacts/er/ — shared fixtures; format governed by Member 4 contracts

---

### Member 3 — Graph / Analytics

**Owns:**
- services/graph/ — graph service (sutradhar_graph package)
- services/graph/sutradhar_graph/dossier_rules.yaml
- docs/prd/03-graph-analytics.md

**Does NOT own:**
- contracts/fixtures/artifacts/graph/ — shared fixtures; format governed by Member 4 contracts

---

### Member 4 — Backend API / Security / Audit / Root Tooling

**Owns:**
- services/api/ — backend API service (sutradhar_api package)
- contracts/ — entire directory including openapi.json, schemas/, fixtures/, CHANGELOG.md, README.md
- .github/ — CODEOWNERS, workflows, issue templates
- Makefile
- docker-compose.yml
- pyproject.toml (root)
- requirements-dev.txt
- .env.example
- .gitignore
- .gitattributes
- .editorconfig
- .pre-commit-config.yaml
- CONTRIBUTING.md
- README.md
- docs/REPO-SETUP.md
- docs/prd/00-MAIN-PRD.md
- docs/prd/04-backend-security-audit.md
- docs/decisions/ (ADR management)

**Does NOT own:**
- apps/web/, services/nlp/, services/graph/, services/data_gen/, services/eval/, data/

---

### Member 5 — Frontend / Storytelling

**Owns:**
- apps/web/ — entire web application
- docs/prd/05-frontend-storytelling.md

**Does NOT own:**
- Anything outside apps/web/

---

## 5. PRD/Repository Conflicts

| ID | Conflict Description | Severity |
|----|---------------------|----------|
| C-01 | docs/REPO-SETUP.md is EMPTY. It is the canonical architecture reference yet contains no content. Implementations cannot correctly reference it. | Critical |
| C-02 | docs/prd/00-MAIN-PRD.md is EMPTY. Every member's work depends on the main PRD defining scope, personas, and system context. | Critical |
| C-03 | All six PRD files (00 through 05) are empty. No member has a written specification to implement against. | Critical |
| C-04 | contracts/openapi.json is EMPTY. The frontend (apps/web/) and every service integration depends on this contract. | Critical |
| C-05 | contracts/schemas/ is an EMPTY directory. No JSON schemas, Pydantic model exports, or TypeScript type exports exist. | Critical |
| C-06 | services/nlp/ Python package is named sutradhar_er (entity resolution), not sutradhar_nlp. The directory name is nlp/ but the package name is er. This must be documented explicitly to prevent contributors from creating a parallel sutradhar_nlp/ package. | Moderate |
| C-07 | contracts/fixtures/MANIFEST.json is EMPTY. Scripts like scripts/validate_fixtures.py likely depend on this manifest to enumerate expected fixture paths. | Moderate |
| C-08 | All pyproject.toml files (root + all 5 services) are EMPTY. No package names, versions, dependencies, or entry points are declared. CI and local installs will fail. | Critical |
| C-09 | Makefile is EMPTY. No build, lint, test, or run targets exist. | Critical |
| C-10 | docker-compose.yml is EMPTY. The multi-service architecture cannot be orchestrated locally. | Moderate |
| C-11 | .gitignore is EMPTY. Python artifacts (__pycache__, .venv, *.egg-info), Node artifacts (node_modules, .next), and pipeline artifacts will be committed unless fixed. | Moderate |
| C-12 | .github/CODEOWNERS is EMPTY. GitHub PR review enforcement is non-functional. Cross-member edits will not trigger required reviews. | Moderate |
| C-13 | apps/web/ contains only an empty Dockerfile — no framework scaffold, no package.json, no src/. Member 5 has no starting point. | Moderate |
| C-14 | data/v0/ and data/v1/ agency subdirectories (CENTRAL_AGENCY/, MAHA_CYBER/, STATE_POLICE/) are all EMPTY. Canonical versioned data store is unpopulated. | Moderate |
| C-15 | services/data_gen/sutradhar_data/lexicons/ is EMPTY. Data generation relies on lexicons but none exist yet. | Low — expected to be populated by Member 1 |
| C-16 | data/dev/ is an EMPTY directory. Its purpose is undefined (REPO-SETUP.md is empty, so no reference available). | Low |
| C-17 | services/graph/sutradhar_graph/dossier_rules.yaml is EMPTY. The graph dossier generation logic has no rules to operate on. | Low — expected to be populated by Member 3 |

---

## 6. Antigravity Prompt Risks

The following patterns in implementation prompts could cause structural violations:

| ID | Risk Description | Example Trigger | Correct Location |
|----|----------------|-----------------|-----------------|
| R-01 | Creating a frontend/ directory at repository root | "Create a React frontend" without specifying path | Must be apps/web/ |
| R-02 | Creating a backend/ directory at repository root | "Create a FastAPI backend" without specifying path | Must be services/api/ |
| R-03 | Creating an api/ directory at repository root | "Scaffold the API" without specifying path | Must be services/api/ |
| R-04 | Creating a web/ directory at repository root | "Build the web app" without specifying path | Must be apps/web/ |
| R-05 | Creating duplicate contracts/ inside a service directory (e.g., services/api/contracts/) | "Add the API contracts here" | Must remain at root contracts/ |
| R-06 | Moving or duplicating openapi.json into services/api/ | Auto-generating OpenAPI from FastAPI into the wrong location | Source of truth is contracts/openapi.json |
| R-07 | Creating services/nlp/sutradhar_nlp/ as a new package directory | "Initialize the NLP package" | Package is already sutradhar_er/. Do not create sutradhar_nlp/. |
| R-08 | Creating data/ inside any service directory (e.g., services/data_gen/data/) | "Store generated data here" | All data lives at root data/ |
| R-09 | Creating a schemas/ directory outside contracts/schemas/ | "Add Pydantic model exports" to services/api/schemas/ | Must be contracts/schemas/ |
| R-10 | Populating artifacts/ with source-controlled files | "Save pipeline results here and commit" | artifacts/ is for generated output and should be gitignored |
| R-11 | Creating a separate tests/ directory at repository root | "Add integration tests" | Tests belong in each service's own tests/ subdirectory |
| R-12 | Installing a JS framework scaffold that creates root-level config files (package.json, vite.config.ts, etc.) at repository root | Running `npx create-vite` without targeting ./apps/web | Framework init must target apps/web/ |
| R-13 | Editing files owned by another member without an explicit cross-member instruction | "Update the API contract to match my frontend needs" — Member 5 directly editing contracts/openapi.json | Cross-member changes require PR and CODEOWNERS review |
| R-14 | Creating a src/ directory at repository root | Generic Python project scaffold | Python source lives in per-service package dirs (e.g., services/api/sutradhar_api/) |
| R-15 | Treating contracts/fixtures/ as the canonical data store instead of data/ | "The fixture data is the real data" | data/ is canonical; contracts/fixtures/ is the contract test harness |

---

## 7. Required Changes

The following changes are actually necessary before implementation can begin safely. These are documentation and stub-population tasks, not architectural restructuring.

> NOTE: None of these changes involve creating new directories or moving files. All required paths already exist as empty stubs.

| ID | Change | Owner | Priority |
|----|--------|-------|----------|
| RC-01 | Author docs/REPO-SETUP.md with canonical architecture, conventions, service boundaries, and contribution rules | Member 4 | Blocking |
| RC-02 | Author docs/prd/00-MAIN-PRD.md with system overview, personas, scope, and pipeline definition | Member 4 | Blocking |
| RC-03 | Author docs/prd/01-data-synthetic.md | Member 1 | Blocking for Member 1 |
| RC-04 | Author docs/prd/02-nlp-entity-resolution.md | Member 2 | Blocking for Member 2 |
| RC-05 | Author docs/prd/03-graph-analytics.md | Member 3 | Blocking for Member 3 |
| RC-06 | Author docs/prd/04-backend-security-audit.md | Member 4 | Blocking for Member 4 |
| RC-07 | Author docs/prd/05-frontend-storytelling.md | Member 5 | Blocking for Member 5 |
| RC-08 | Populate contracts/openapi.json with at minimum a v0.1 OpenAPI 3.x skeleton | Member 4 | Blocking for Members 2, 3, 5 |
| RC-09 | Populate each service's pyproject.toml with correct package name, version, and dependencies | Per-member | Blocking — CI/install will fail |
| RC-10 | Populate root pyproject.toml with workspace/tool config (ruff, mypy, pytest, etc.) | Member 4 | Blocking |
| RC-11 | Populate requirements-dev.txt | Member 4 | High |
| RC-12 | Populate .gitignore | Member 4 | High |
| RC-13 | Populate Makefile with at minimum lint, test, run-api, run-web targets | Member 4 | High |
| RC-14 | Populate docker-compose.yml with service definitions | Member 4 | High |
| RC-15 | Populate .env.example with required env vars | Member 4 | High |
| RC-16 | Populate .github/CODEOWNERS with ownership rules | Member 4 | High |
| RC-17 | Populate .github/workflows/ci.yml | Member 4 | High |
| RC-18 | Populate contracts/fixtures/MANIFEST.json so validation scripts work | Member 4 | High |
| RC-19 | Document services/nlp/ package name divergence (sutradhar_er vs sutradhar_nlp) in docs/REPO-SETUP.md | Member 4 | Medium |
| RC-20 | Initialize apps/web/ with framework scaffold (package.json, src/, etc.) | Member 5 | Medium |
| RC-21 | Add at least one JSON Schema or Pydantic model export to contracts/schemas/ | Member 4 | Medium |
| RC-22 | Author README.md at repository root | Member 4 | Medium |
| RC-23 | Author CONTRIBUTING.md | Member 4 | Medium |
| RC-24 | Author NOTICE-SYNTHETIC-DATA.md | Member 1 | Medium |
| RC-25 | Populate data/DATASET_CARD.md | Member 1 | Low |
| RC-26 | Define purpose of data/dev/ or remove the placeholder | Member 1 | Low |

---

## 8. No-Change Areas

The following parts of the repository are correctly structured and must not be reorganized, renamed, or relocated:

| Path | Reason |
|------|--------|
| apps/web/ | Correct location for Member 5's frontend. Do not create frontend/, web/, or apps/frontend/. |
| services/api/ | Correct location for Member 4's backend. Do not create backend/, api/ at root, or services/backend/. |
| services/nlp/ | Correct directory name. Do not rename to services/er/. |
| services/nlp/sutradhar_er/ | Correct Python package name. Do not add a parallel sutradhar_nlp/. |
| services/graph/ | Correct location. Do not create services/analytics/. |
| services/data_gen/ | Correct location. Do not create services/data/. |
| services/eval/ | Correct location. Do not create services/evaluation/. |
| contracts/ | Correct root-level location. Do not duplicate inside any service. |
| contracts/fixtures/api/ | 29 fixture JSON files are in place and correctly structured. Do not reorganize. |
| contracts/fixtures/data/ | Agency-partitioned JSONL fixture files are in place. Do not reorganize. |
| contracts/fixtures/artifacts/ | ER, graph, and decisions fixtures are in place. Do not reorganize. |
| data/kumbh/events.jsonl | Only populated data file at root data/. Do not move. |
| scripts/ | All 5 scripts are present and correctly placed at root. Do not move into a service. |
| docs/ | Directory structure (prd/, decisions/, pitch/) is correct. |
| .github/ISSUE_TEMPLATE/contract-change.md | Correctly placed. |
| services/*/tests/ | Smoke test files are correctly placed per-service. Do not consolidate into a root tests/. |
| services/graph/sutradhar_graph/dossier_rules.yaml | Correct location (even if empty). Do not move to contracts/. |
| artifacts/ | Correct location for generated output. Must remain empty until pipeline runs. Do not commit generated files here. |

---

## 9. Final Architecture Decision

### Verdict: The existing repository structure is CORRECT and must be retained as-is.

No structural changes (directory creation, renaming, or file moves) are required.

**The repository skeleton is sound.** All top-level directories match the canonical architecture:
- apps/web/ — PRESENT
- services/{api,nlp,graph,data_gen,eval}/ — PRESENT
- contracts/ — PRESENT
- data/ — PRESENT
- artifacts/ — PRESENT
- docs/, scripts/, .github/ — PRESENT

**The sole problem is content, not structure.** The vast majority of files are 0-byte stubs. The repository was scaffolded correctly but not yet authored. Every member must populate their owned files before implementation begins.

### Minimum Viable Pre-Implementation Checklist

Before any member begins writing application code, the following must exist with actual content:

1. docs/REPO-SETUP.md — architecture conventions (Member 4)
2. docs/prd/00-MAIN-PRD.md — system scope (Member 4)
3. Each member's PRD (01 through 05)
4. contracts/openapi.json — at minimum a v0.1 skeleton with all route paths defined
5. All pyproject.toml files — package names and dependencies
6. Root pyproject.toml — workspace configuration
7. .gitignore — to prevent accidental commits of build artifacts

### Architectural Rules to Enforce Going Forward

1. No new top-level directories without a team decision recorded in docs/decisions/.
2. No parallel package directories inside existing services.
3. All cross-service data contracts go through contracts/ — not through direct service-to-service imports.
4. artifacts/ is gitignored output — never commit generated files there.
5. Member boundary enforcement is the responsibility of .github/CODEOWNERS once populated.

---

*Audit complete. No files were modified. No code was written. No dependencies were installed.*
