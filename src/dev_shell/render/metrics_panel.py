from __future__ import annotations

from datetime import datetime

from dev_shell.monitoring.models import MetricEvent
from dev_shell.utils.formatters import format_bytes, format_percent, format_uptime


class MetricsPanel:
    def __init__(self) -> None:
        self.values: dict[str, MetricEvent] = {}
        self.status = "DISCONNECTED"
        self.server = ""
        self.updated_at: datetime | None = None

    def update_status(self, server: str, status: str) -> None:
        self.server = server
        self.status = status

    def apply(self, event: MetricEvent) -> None:
        key = event.name
        if event.labels.get("interface"):
            key = f"{event.name}:{event.labels['interface']}"
        elif event.labels.get("path"):
            key = f"{event.name}:{event.labels['path']}"
        self.values[key] = event
        self.updated_at = event.timestamp

    def _latest(self, name: str, default: float = 0.0) -> float:
        event = self.values.get(name)
        if event is not None:
            return event.value
        for item in self.values.values():
            if item.name == name:
                return item.value
        return default

    def render(self) -> str:
        rx = 0.0
        tx = 0.0
        for key, event in self.values.items():
            if event.name == "network.rx_bytes":
                rx += event.value
            elif event.name == "network.tx_bytes":
                tx += event.value
        lines = [
            f"SERVER: {self.server or '-'}",
            f"STATUS: {self.status}",
            "",
            f"CPU       {format_percent(self._latest('cpu.percent'))}",
            f"MEMORY    {format_percent(self._latest('memory.percent'))}",
            f"DISK      {format_percent(self._latest('disk.percent'))}",
            f"NETWORK   RX {format_bytes(rx)}",
            f"          TX {format_bytes(tx)}",
            f"UPTIME    {format_uptime(self._latest('uptime.seconds'))}",
        ]
        return "\n".join(lines)
