#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
go build -o dist/dev-shell-monitor ./cmd/dev-shell-monitor
echo "built $ROOT/dist/dev-shell-monitor"
