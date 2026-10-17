# Contributing to Sutradhar

> **All data is entirely synthetic.** No real person, agency or case is represented.

## Before you begin

1. Read [docs/REPO-SETUP.md](docs/REPO-SETUP.md) in full.
2. Read your personal PRD in `docs/prd/`.
3. Run `bash scripts/setup_check.sh` to verify your environment.
4. Install pre-commit hooks: `pre-commit install`.

## Branch naming

| Pattern | Purpose |
|---------|---------|
| `feat/data` | M1 — data generation and evaluation |
| `feat/nlp` | M2 — NLP and entity resolution |
| `feat/graph` | M3 — graph analytics |
| `feat/backend` | M4 — backend, security, audit |
| `feat/frontend` | M5 — frontend dashboard |
| `contract/<description>` | Contract-only changes |
| `fix/<description>` | Bug fixes |

## Commit messages

```
<area>: <what>
```

Examples: `er: add marathi surname lexicon`, `api: add audit verify endpoint`, `contracts: add dossier schema`.

## PR rules

- PRs require at least one reviewer from a different member.
- CI must pass before merge.
- Contract PRs require M4 approval regardless of author.
- No direct push to `main` or `dev`.

## Ownership

You may only edit files in your own ownership area. See [docs/REPO-SETUP.md §3](docs/REPO-SETUP.md) for the full ownership table.

## Secrets

Never commit secrets. Use `.env` (gitignored). Document variable names in `.env.example`.

## Data safety

`data/truth/` is gitignored and must **never** be committed. The pre-commit hook `check_no_truth_leak.sh` will block any commit that references it.
