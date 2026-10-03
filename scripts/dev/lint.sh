#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck "$ROOT"/scripts/*.sh "$ROOT"/scripts/dev/*.sh "$ROOT"/remote/dev-shell-monitor/scripts/*.sh
else
  echo "shellcheck not installed; skipped"
fi
