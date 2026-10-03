#!/usr/bin/env bash
set -euo pipefail

BINARY_SRC="${1:-}"
if [[ -z "$BINARY_SRC" || ! -x "$BINARY_SRC" ]]; then
  echo "update-server failed in updater: usage: update-server.sh /path/to/dev-shell-monitor" >&2
  exit 1
fi
if [[ "$(id -u)" -ne 0 ]]; then
  echo "update-server failed in updater: root privileges are required" >&2
  exit 1
fi

systemctl stop dev-shell-monitor.service
install -o devshell -g devshell -m 0755 "$BINARY_SRC" /opt/dev-shell-monitor/dev-shell-monitor
systemctl start dev-shell-monitor.service

for _ in $(seq 1 20); do
  if curl --fail --silent http://127.0.0.1:9477/health >/dev/null; then
    echo "dev-shell-monitor updated and healthy"
    exit 0
  fi
  sleep 0.5
done

echo "update-server failed in health: service did not become healthy" >&2
systemctl status dev-shell-monitor.service --no-pager >&2 || true
exit 1
