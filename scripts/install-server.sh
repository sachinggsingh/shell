#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BINARY_SRC="${BINARY_SRC:-}"
CONFIG_SRC="${CONFIG_SRC:-$ROOT/remote/dev-shell-monitor/configs/dev-shell-monitor.example.yaml}"
UNIT_SRC="${UNIT_SRC:-$ROOT/deploy/systemd/dev-shell-monitor.service}"
INSTALL_DIR="${INSTALL_DIR:-/opt/dev-shell-monitor}"
CONFIG_DIR="${CONFIG_DIR:-/etc/dev-shell-monitor}"
SERVICE_USER="${SERVICE_USER:-devshell}"
SERVICE_GROUP="${SERVICE_GROUP:-devshell}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:9477/health}"

if [[ ! -x "${BINARY_SRC}" ]]; then
  echo "install-server failed in installer: BINARY_SRC must point to a built dev-shell-monitor binary" >&2
  exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "install-server failed in installer: systemd/systemctl is required" >&2
  exit 1
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "install-server failed in installer: root privileges are required" >&2
  exit 1
fi

if ! getent group "$SERVICE_GROUP" >/dev/null; then
  groupadd --system "$SERVICE_GROUP"
fi
if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --gid "$SERVICE_GROUP" --home-dir "$INSTALL_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
fi

install -d -o "$SERVICE_USER" -g "$SERVICE_GROUP" -m 0755 "$INSTALL_DIR"
install -d -o root -g "$SERVICE_GROUP" -m 0755 "$CONFIG_DIR"
install -o "$SERVICE_USER" -g "$SERVICE_GROUP" -m 0755 "$BINARY_SRC" "$INSTALL_DIR/dev-shell-monitor"

if [[ ! -f "$CONFIG_DIR/config.yaml" ]]; then
  install -o root -g "$SERVICE_GROUP" -m 0640 "$CONFIG_SRC" "$CONFIG_DIR/config.yaml"
fi

install -o root -g root -m 0644 "$UNIT_SRC" /etc/systemd/system/dev-shell-monitor.service
systemctl daemon-reload
systemctl enable dev-shell-monitor.service
systemctl restart dev-shell-monitor.service
systemctl is-active --quiet dev-shell-monitor.service

for _ in $(seq 1 20); do
  if curl --fail --silent "$HEALTH_URL" >/dev/null; then
    echo "dev-shell-monitor installed and healthy"
    exit 0
  fi
  sleep 0.5
done

echo "install-server failed in health: $HEALTH_URL did not succeed after service start" >&2
systemctl status dev-shell-monitor.service --no-pager >&2 || true
exit 1
