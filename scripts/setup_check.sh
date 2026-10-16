#!/usr/bin/env bash
# scripts/setup_check.sh
# Verifies that the developer's environment meets minimum requirements.
# Run on first day: bash scripts/setup_check.sh
# Owned by M4.

set -euo pipefail

PASS=0
FAIL=0

check() {
  local name="$1"
  local cmd="$2"
  local min_version="$3"
  if command -v "$cmd" &>/dev/null; then
    local version
    version=$($cmd --version 2>&1 | head -n1)
    echo "  OK  $name: $version"
    PASS=$((PASS + 1))
  else
    echo "  FAIL $name: not found (requires $min_version or later)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Sutradhar Environment Check ==="
echo ""
echo "--- Runtime ---"
check "Python 3.11+" "python3" "3.11"
check "pip" "pip3" "23"
check "Node.js 18+" "node" "18"
check "npm" "npm" "9"
check "Docker" "docker" "24"

echo ""
echo "--- Dev tools ---"
check "ruff" "ruff" "0.3"
check "pre-commit" "pre-commit" "3.6"

echo ""
echo "--- Git ---"
check "git" "git" "2.40"

echo ""
if [ "$FAIL" -gt 0 ]; then
  echo "RESULT: $PASS passed, $FAIL FAILED."
  echo "Install missing tools before proceeding."
  exit 1
else
  echo "RESULT: All $PASS checks passed."
  echo ""
  echo "Next steps:"
  echo "  cp .env.example .env         # fill in your local values"
  echo "  pip install -r requirements-dev.txt"
  echo "  pre-commit install"
  echo "  cd services/<your-service> && pip install -e '.[dev]'"
  exit 0
fi
