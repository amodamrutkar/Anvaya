# Contracts Changelog

All contract changes are recorded here. Breaking changes require a 24-hour notice period before merge.

Format: `## [version] — date — author — summary`

## [0.2.0] — 2026-10-24 — M4 — Step 7A Canonical Government Data Contracts & Adapter Boundary

### Added

- `schemas/ingestion_metadata.schema.json` — Shared integration & provenance metadata contract.
- `schemas/canonical_account.schema.json` — Formal bank account contract for financial analysis and mule tracking.
- `schemas/canonical_transaction.schema.json` — Formal transaction contract for fund flow analysis.
- `fixtures/canonical/` — Integration reference fixtures for canonical contracts and simulated adapter payloads:
  - `source_record.json`, `canonical_account.json`, `canonical_transaction.json`, `ingestion_metadata.json`
  - `raw_cctns_fir.json`, `raw_mahacyber_incident.json`, `raw_banking_transaction.json`, `raw_kumbh_observation.json`
- `sutradhar_api/adapters/` — Simulated normalization adapter layer (`BaseAdapter`, `CctnsFirAdapter`, `MahaCyberPortalAdapter`, `BankingFiuAdapter`, `KumbhOperationsAdapter`).

### Changed

- `schemas/source_record.schema.json` — Evolved with optional `ingestion_metadata` reference; affirmed as the single authoritative canonical SourceRecord contract.
- `schemas/kumbh_event.schema.json` — Evolved with optional `ingestion_metadata` reference.
- `fixtures/MANIFEST.json` — Linked `canonical_account.schema.json` to accounts fixtures and `canonical_transaction.schema.json` to transactions fixtures; indexed all new canonical fixtures.

### Notes

- All data remains entirely synthetic and all connectors/adapters are simulated (`simulated: true`).
- No live external network requests or production credentials exist or are claimed.
- 100% backward-compatible with frozen Step 6B datasets (V1 and V2).

---

## [0.1.0] — 2026-10-17 — M4 — Initial scaffold

### Added

- `openapi.json` v0.1 skeleton with all 28 route paths from PRD Section 9.
- `schemas/` with JSON Schema draft 2020-12 for:
  - `source_record`, `mention`, `entity`, `link`, `decision`
  - `audit_entry`, `federated_query`, `kumbh_event`, `metrics`
- `fixtures/` with one valid example file per artifact and per API endpoint.
- `fixtures/MANIFEST.json` — fixture index for `validate_fixtures.py`.
- `CHANGELOG.md` (this file).
- `README.md` — usage guide.

### Notes

- All fixture data uses the Rakesh Pawar bridge story from PRD Section 4.
- All fixture data is entirely synthetic. No real person or agency is represented.
- Legal parameters in dossier fixtures are marked `verified: false`.
