from __future__ import annotations

from pathlib import Path

from dev_shell.config import load_client_config, resolve_config_path, save_client_config
from dev_shell.core.errors import ServerNotFoundError
from dev_shell.monitoring.models import ServerConfig


class ServerRegistry:
    def __init__(self, config_path: str | Path | None = None) -> None:
        self.path = resolve_config_path(str(config_path) if config_path else None)
        self._data = load_client_config(self.path)

    def servers(self) -> list[ServerConfig]:
        items = self._data.get("servers") or []
        result: list[ServerConfig] = []
        for item in items:
            if isinstance(item, dict):
                result.append(ServerConfig.from_dict(item))
        return result

    def get(self, name: str) -> ServerConfig:
        for server in self.servers():
            if server.name == name:
                return server
        raise ServerNotFoundError(name)

    def add(self, server: ServerConfig) -> None:
        servers = [item for item in self.servers() if item.name != server.name]
        servers.append(server)
        self._write(servers)

    def remove(self, name: str) -> None:
        servers = self.servers()
        if not any(item.name == name for item in servers):
            raise ServerNotFoundError(name)
        self._write([item for item in servers if item.name != name])

    def _write(self, servers: list[ServerConfig]) -> None:
        self._data["servers"] = [item.to_dict() for item in servers]
        save_client_config(self.path, self._data)
