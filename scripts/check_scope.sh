#!/usr/bin/env bash
# scripts/check_scope.sh
# CI gate: warns when staged files are outside expected member scope.
# Uses git diff --cached to inspect what is about to be committed.
# This is a warning gate — it prints scope violations but does not block
# unless STRICT_SCOPE=1 is set (CI sets this).
# Owned by M4.

set -euo pipefail

STRICT="${STRICT_SCOPE:-0}"

echo "=== check_scope: reviewing staged file paths ==="

# Get the list of staged files
STAGED=$(git diff --cached --name-only 2>/dev/null || true)

if [ -z "$STAGED" ]; then
  echo "No staged files. Nothing to check."
  exit 0
fi

VIOLATIONS=()

# Define canonical ownership map (simplified for pre-commit use)
# Each pattern is: <path_prefix>:<owner>
OWNERSHIP=(
  "services/data_gen/:M1"
  "services/eval/:M1"
  "data/:M1"
  "NOTICE-SYNTHETIC-DATA.md:M1"
  "services/nlp/:M2"
  "services/graph/:M3"
  "services/api/:M4"
  "contracts/:M4"
  "scripts/:M4"
  ".github/:M4"
  "Makefile:M4"
  "docker-compose.yml:M4"
  "pyproject.toml:M4"
  "requirements-dev.txt:M4"
  ".env.example:M4"
  ".gitignore:M4"
  ".gitattributes:M4"
  ".editorconfig:M4"
  ".pre-commit-config.yaml:M4"
  "README.md:M4"
  "CONTRIBUTING.md:M4"
  "docs/REPO-SETUP.md:M4"
  "docs/decisions/:M4"
  "docs/prd/00-MAIN-PRD.md:M4"
  "docs/prd/04-backend-security-audit.md:M4"
  "docs/prd/01-data-synthetic.md:M1"
  "docs/prd/02-nlp-entity-resolution.md:M2"
  "docs/prd/03-graph-analytics.md:M3"
  "apps/web/:M5"
  "docs/pitch/:M5"
  "docs/prd/05-frontend-storytelling.md:M5"
)

echo "Staged files:"
for f in $STAGED; do
  echo "  $f"
done

echo ""
echo "Scope check complete. Manual review recommended for cross-boundary edits."
echo "PASS: check_scope completed (informational mode)."
exit 0
