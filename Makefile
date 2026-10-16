# Sutradhar — Root Makefile
# Owned by M4. All common dev targets live here.
# Usage: make <target>

.DEFAULT_GOAL := help
VERSION ?= v1
SEED    ?= 42
API_URL ?= http://localhost:8000

# ─────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────
.PHONY: help
help:
	@echo ""
	@echo "Sutradhar Makefile"
	@echo "─────────────────────────────────────────"
	@echo "  make data VERSION=v1 SEED=42  Generate synthetic dataset"
	@echo "  make er                        Run entity resolution"
	@echo "  make graph                     Run graph analytics"
	@echo "  make eval                      Run evaluation against truth"
	@echo "  make pipeline                  data → er → graph → eval"
	@echo "  make api                       Start API dev server"
	@echo "  make web                       Start frontend dev server"
	@echo "  make test                      Run all tests + gates"
	@echo "  make lint                      Run ruff linter"
	@echo "  make format                    Run ruff formatter"
	@echo "  make demo                      docker compose up (offline demo)"
	@echo "  make demo-check                Smoke test the full demo path"
	@echo "  make fixtures                  Validate contracts/fixtures/"
	@echo "  make setup-check               Verify dev environment"
	@echo ""

# ─────────────────────────────────────────────────────────────
# Data generation (M1 — calls sutradhar_data)
# ─────────────────────────────────────────────────────────────
.PHONY: data
data:
	python -m sutradhar_data.generate --version $(VERSION) --seed $(SEED) --out data/

# ─────────────────────────────────────────────────────────────
# Entity resolution (M2 — calls sutradhar_er)
# ─────────────────────────────────────────────────────────────
.PHONY: er
er:
	python -m sutradhar_er.run --data data/$(VERSION) --out artifacts/er

# ─────────────────────────────────────────────────────────────
# Graph analytics (M3 — calls sutradhar_graph)
# ─────────────────────────────────────────────────────────────
.PHONY: graph
graph:
	python -m sutradhar_graph.run --data data/$(VERSION) --er artifacts/er --out artifacts/graph

# ─────────────────────────────────────────────────────────────
# Evaluation (M1 — calls sutradhar_eval, reads data/truth/)
# ─────────────────────────────────────────────────────────────
.PHONY: eval
eval:
	python -m sutradhar_eval.run \
		--data data/$(VERSION) \
		--truth data/truth/$(VERSION) \
		--artifacts artifacts \
		--out artifacts/metrics.json

# ─────────────────────────────────────────────────────────────
# Full pipeline
# ─────────────────────────────────────────────────────────────
.PHONY: pipeline
pipeline: data er graph eval

# ─────────────────────────────────────────────────────────────
# API dev server (M4)
# ─────────────────────────────────────────────────────────────
.PHONY: api
api:
	cd services/api && uvicorn sutradhar_api.main:app --reload --host 0.0.0.0 --port 8000

# ─────────────────────────────────────────────────────────────
# Frontend dev server (M5)
# ─────────────────────────────────────────────────────────────
.PHONY: web
web:
	cd apps/web && npm run dev

# ─────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────
.PHONY: test
test: test-truth-leak test-fixtures test-api-unit

.PHONY: test-truth-leak
test-truth-leak:
	@echo "--- truth-leak gate ---"
	bash scripts/check_no_truth_leak.sh

.PHONY: test-fixtures
test-fixtures:
	@echo "--- fixture validation ---"
	python scripts/validate_fixtures.py

.PHONY: test-api-unit
test-api-unit:
	@echo "--- API unit tests ---"
	cd services/api && pytest tests/ -v --tb=short

.PHONY: test-all
test-all:
	pytest services/api/tests/ \
	       services/nlp/tests/ \
	       services/graph/tests/ \
	       services/data_gen/tests/ \
	       services/eval/tests/ \
	       -v --tb=short

# ─────────────────────────────────────────────────────────────
# Linting / formatting
# ─────────────────────────────────────────────────────────────
.PHONY: lint
lint:
	ruff check services/ scripts/

.PHONY: format
format:
	ruff format services/ scripts/

# ─────────────────────────────────────────────────────────────
# Offline demo (docker compose)
# ─────────────────────────────────────────────────────────────
.PHONY: demo
demo:
	docker compose up --build

.PHONY: demo-check
demo-check:
	python scripts/demo_check.py --base-url $(API_URL)

# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────
.PHONY: fixtures
fixtures:
	python scripts/validate_fixtures.py

# ─────────────────────────────────────────────────────────────
# Environment setup
# ─────────────────────────────────────────────────────────────
.PHONY: setup-check
setup-check:
	bash scripts/setup_check.sh

.PHONY: install-dev
install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

# ─────────────────────────────────────────────────────────────
# OpenAPI regeneration (M4 calls after route changes)
# ─────────────────────────────────────────────────────────────
.PHONY: openapi
openapi:
	cd services/api && python -c "from sutradhar_api.main import app; import json; from fastapi.openapi.utils import get_openapi; spec = get_openapi(title=app.title, version=app.version, routes=app.routes); print(json.dumps(spec, indent=2))" > ../../contracts/openapi.json
	@echo "contracts/openapi.json updated."
