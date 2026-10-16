# Sutradhar

> **Multi-agency financial intelligence and entity-resolution platform.**
> All data is entirely synthetic. No real person, agency or case is represented.

See **[docs/REPO-SETUP.md](docs/REPO-SETUP.md)** for the full architecture, ownership rules, workflow conventions, and Antigravity agent instructions.

---

## Quick Start

```bash
# 1 — Clone and check environment
git clone <repo-url>
cd sutradhar
bash scripts/setup_check.sh

# 2 — Copy env template
cp .env.example .env          # fill in real values as needed

# 3 — Install Python dev dependencies (at root)
pip install -e ".[dev]"
pre-commit install

# 4 — Install your service dependencies
cd services/<your-service>/
pip install -e ".[dev]"
cd ../..

# 5 — Run your service smoke test
pytest services/<your-service>/tests/ -v

# 6 — Run the full offline demo
make demo

# 7 — Run the demo smoke-test
make demo-check
```

## Pipeline

```
data/  ──M1──►  services/nlp  ──M2──►  services/graph  ──M3──►  artifacts/
                                                                      │
                                                                      ▼ M4
                                                             services/api  ──M4──►  apps/web  (M5)
```

## Feature Branches

| Branch | Owner | Area |
|--------|-------|------|
| `feat/data` | M1 | Data generation + evaluation |
| `feat/nlp` | M2 | NLP + entity resolution |
| `feat/graph` | M3 | Graph analytics |
| `feat/backend` | M4 | Backend API + security + audit |
| `feat/frontend` | M5 | Frontend dashboard |

All feature branches merge to `dev` first. Only `dev` merges to `main` via PR.

## Synthetic Data Disclaimer

All records, names, identifiers, accounts and events in this repository are **entirely fabricated**.
See [NOTICE-SYNTHETIC-DATA.md](NOTICE-SYNTHETIC-DATA.md).
