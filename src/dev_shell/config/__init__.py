from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dev_shell.utils.validators import load_json

PACKAGE_CONFIG = Path(__file__).resolve().parent / "config.json"


def default_user_config_path() -> Path:
    return Path.home() / ".config" / "dev_shell" / "config.json"


def resolve_config_path(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    return default_user_config_path()


def load_client_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"servers": [], "tracing": {"enabled": False, "otlp_endpoint": "", "service_name": "dev-shell"}}
    return load_json(path)


def save_client_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
