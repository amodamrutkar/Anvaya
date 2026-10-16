## Pull Request

### What does this PR do?

<!-- Describe the change in 2-3 sentences. -->

### Which files did you change?

<!-- List key files changed and why. -->

### Member area

- [ ] M1 — data generation / evaluation
- [ ] M2 — NLP / entity resolution
- [ ] M3 — graph analytics
- [ ] M4 — backend / security / audit / contracts
- [ ] M5 — frontend / storytelling

### Checklist

- [ ] I read `docs/REPO-SETUP.md` and worked only in my owned directories.
- [ ] I ran `bash scripts/check_no_truth_leak.sh` and it passed.
- [ ] I ran the relevant tests (`pytest services/<my-service>/tests/ -v`).
- [ ] I ran `python scripts/validate_fixtures.py` (for M4 / contract changes).
- [ ] My commit messages follow `<area>: <what>` format.
- [ ] No secrets, credentials, or real personal data were introduced.
- [ ] No files outside my ownership area were modified.

### If this is a contract change

- [ ] `contracts/CHANGELOG.md` has been updated.
- [ ] `contracts/openapi.json` has been regenerated.
- [ ] `python scripts/validate_fixtures.py` passes.
- [ ] All affected members have been notified.

### Cross-member dependencies introduced

<!-- List any new inter-member dependencies this PR introduces. -->
None.

### Open questions / blockers

<!-- Anything that requires input from another member. -->
None.
