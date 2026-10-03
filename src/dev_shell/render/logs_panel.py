from __future__ import annotations

from collections import deque

from dev_shell.monitoring.models import LogEvent
from dev_shell.utils.formatters import format_timestamp


class LogsPanel:
    def __init__(self, limit: int = 20) -> None:
        self.limit = limit
        self.lines: deque[LogEvent] = deque(maxlen=limit)

    def apply(self, event: LogEvent) -> None:
        self.lines.append(event)

    def render(self) -> str:
        if not self.lines:
            return "(no log events yet)"
        rows = []
        for event in self.lines:
            rows.append(
                f"{format_timestamp(event.timestamp)} {event.level:<5} {event.service:<12} {event.message}"
            )
        return "\n".join(rows)
