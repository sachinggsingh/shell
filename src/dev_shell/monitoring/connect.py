from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from dev_shell.core.errors import StreamDisconnected
from dev_shell.monitoring.health import HealthClient
from dev_shell.monitoring.models import ServerConfig, StreamEvent
from dev_shell.monitoring.ssh_tunnel import SSHTunnel
from dev_shell.monitoring.stream_client import MonitoringStreamClient
from dev_shell.utils.logger import get_logger

logger = get_logger("dev_shell.monitoring.connect")

_ACTIVE: dict[str, "MonitoringConnection"] = {}


class MonitoringConnection:
    def __init__(self, server: ServerConfig) -> None:
        self.server = server
        self.tunnel: SSHTunnel | None = None
        self.client: MonitoringStreamClient | None = None
        self._connected = False

    def _http_host(self) -> str:
        host = self.server.host
        if ":" in host and not host.startswith("["):
            return f"[{host}]"
        return host

    @property
    def base_url(self) -> str:
        if self.server.use_direct():
            return f"http://{self._http_host()}:{self.server.monitor_port}"
        if self.tunnel is None:
            raise RuntimeError("tunnel has not been started")
        return f"http://127.0.0.1:{self.tunnel.local_port}"

    def connect(self) -> dict[str, Any]:
        logger.info("connecting to %s", self.server.name)
        if not self.server.use_direct():
            self.tunnel = SSHTunnel.from_server(self.server)
            self.tunnel.start()
        self.client = MonitoringStreamClient(self.base_url)
        payload = self.health()
        self._connected = True
        _ACTIVE[self.server.name] = self
        return payload

    def health(self) -> dict[str, Any]:
        if self.client is None:
            return HealthClient(self.base_url).health()
        return self.client.health()

    def stream(self) -> Iterator[StreamEvent]:
        if self.client is None:
            raise StreamDisconnected("not connected")
        yield from self.client.stream()

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
        if self.tunnel is not None:
            self.tunnel.stop()
        self._connected = False
        _ACTIVE.pop(self.server.name, None)


def get_active(name: str) -> MonitoringConnection | None:
    return _ACTIVE.get(name)


def close_all() -> None:
    for connection in list(_ACTIVE.values()):
        connection.close()
