#!/usr/bin/env bash
# scripts/check_no_truth_leak.sh
# CI gate: blocks any commit that references data/truth/ in non-M1 service code.
# Run automatically by pre-commit and CI (make test includes this).
# Owned by M4.

set -euo pipefail

FORBIDDEN_DIRS=(
  "services/nlp"
  "services/graph"
  "services/api"
  "apps/web"
  "contracts"
  "scripts"
  "docs"
)

SEARCH_PATTERN="data/truth"
FOUND=0

echo "=== check_no_truth_leak: scanning for data/truth references ==="

for dir in "${FORBIDDEN_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    # grep returns exit code 0 if found, 1 if not found
    matches=$(grep -rl "$SEARCH_PATTERN" "$dir" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.sh" --exclude="check_no_truth_leak.sh" 2>/dev/null || true)
    if [ -n "$matches" ]; then
      echo "ERROR: data/truth reference found in forbidden area:"
      echo "$matches"
      FOUND=1
    fi
  fi
done

if [ "$FOUND" -eq 1 ]; then
  echo ""
  echo "FAIL: data/truth references detected in non-M1 code paths."
  echo "The answer key must NEVER be accessible to NLP, graph, API, or frontend services."
  echo "Only services/eval/ and services/data_gen/ may read data/truth/."
  exit 1
fi

echo "PASS: No data/truth references found in forbidden paths."
exit 0
