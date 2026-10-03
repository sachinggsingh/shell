from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def require_non_empty(value: str, field: str) -> str:
    if not value or not str(value).strip():
        raise ValueError(f"{field} must not be empty")
    return str(value).strip()


def require_port(value: int, field: str) -> int:
    port = int(value)
    if not 1 <= port <= 65535:
        raise ValueError(f"{field} must be between 1 and 65535")
    return port


def is_loopback_host(host: str) -> bool:
    name = host.strip().lower().rstrip(".")
    if name.startswith("[") and name.endswith("]"):
        name = name[1:-1]
    return name in {"127.0.0.1", "localhost", "::1", "0:0:0:0:0:0:0:1"}


def parse_monitor_endpoint(value: str, default_port: int) -> tuple[str, int]:
    """Turn a URL or host:port into (hostname, monitor_port)."""
    text = require_non_empty(value, "host")
    if "://" in text:
        from urllib.parse import urlparse

        parsed = urlparse(text)
        host = parsed.hostname or ""
        if not host:
            raise ValueError("host must be a hostname, IP, or URL like http://127.0.0.1:9477")
        port = parsed.port if parsed.port is not None else default_port
        return host, require_port(port, "monitor_port")
    if text.count(":") == 1 and not text.startswith("["):
        host, _, port_text = text.partition(":")
        if host and port_text.isdigit():
            return require_non_empty(host, "host"), require_port(int(port_text), "monitor_port")
    return text, default_port


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data
