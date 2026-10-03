#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-}"
USER="${2:-}"
PORT="${3:-22}"
if [[ -z "$HOST" || -z "$USER" ]]; then
  echo "ssh-check failed in ssh: usage: ssh-check.sh <host> <user> [port]" >&2
  exit 1
fi

ssh -o BatchMode=yes -p "$PORT" "${USER}@${HOST}" true
echo "SSH connectivity to ${USER}@${HOST}:${PORT} succeeded"
