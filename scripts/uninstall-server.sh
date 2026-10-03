#!/usr/bin/env bash
set -euo pipefail

REMOVE_CONFIG=0
if [[ "${1:-}" == "--remove-config" ]]; then
  REMOVE_CONFIG=1
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "uninstall-server failed in uninstaller: root privileges are required" >&2
  exit 1
fi

systemctl stop dev-shell-monitor.service >/dev/null 2>&1 || true
systemctl disable dev-shell-monitor.service >/dev/null 2>&1 || true
rm -f /etc/systemd/system/dev-shell-monitor.service
systemctl daemon-reload
rm -f /opt/dev-shell-monitor/dev-shell-monitor
if [[ "$REMOVE_CONFIG" -eq 1 ]]; then
  rm -rf /etc/dev-shell-monitor
fi
echo "dev-shell-monitor uninstalled"
