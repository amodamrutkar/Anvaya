# Contracts Changelog

All contract changes are recorded here. Breaking changes require a 24-hour notice period before merge.

Format: `## [version] — date — author — summary`

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
