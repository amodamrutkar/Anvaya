# Contracts

This directory is owned by **M4 (Backend, Security, Audit)**.

All changes to `contracts/` must be made via a pull request and announced to the full team. See [Section 4 of REPO-SETUP.md](../REPO-SETUP.md).

## Contents

| Path | Purpose |
|------|---------|
| `openapi.json` | **THE API contract.** Single source of truth for all API endpoints. |
| `schemas/` | JSON Schema (draft 2020-12) definitions for every data shape. |
| `fixtures/MANIFEST.json` | Index of all fixture files; used by `scripts/validate_fixtures.py`. |
| `fixtures/api/` | One JSON file per API endpoint — fixture response for offline development. |
| `fixtures/artifacts/` | Sample pipeline outputs (ER, graph, decisions, metrics). |
| `fixtures/data/` | Sample source records per agency partition. |
| `CHANGELOG.md` | Record of every contract change. |

## Development flow

1. Every service reads `contracts/fixtures/` instead of live upstream services (fixture mode).
2. When the real API is running, `contracts/openapi.json` is the authority for route shapes and request/response types.
3. M5 generates TypeScript types from `openapi.json` using `npx openapi-typescript`.
4. M4 updates `openapi.json` after every route change: `make openapi`.

## Contract change process

1. Open a GitHub issue using the `contract-change` template.
2. Get acknowledgement from all affected members.
3. Update `openapi.json` and/or `schemas/`.
4. Update `CHANGELOG.md`.
5. Update affected `fixtures/`.
6. Run `python scripts/validate_fixtures.py` locally.
7. PR requires M4 approval + most-affected downstream owner.
