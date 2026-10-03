#!/usr/bin/env bash
set -euo pipefail

if command -v systemctl >/dev/null 2>&1; then
  if ! systemctl is-active --quiet dev-shell-monitor.service; then
    echo "health-check failed in systemd: service is not active" >&2
    exit 1
  fi
fi

curl --fail --silent http://127.0.0.1:9477/health
echo
