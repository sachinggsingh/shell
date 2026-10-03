from __future__ import annotations

from typing import Any


class TracesTable:
    def render(self, traces: list[dict[str, Any]]) -> str:
        if not traces:
            return "No traces available. Tracing export may be configured without a query backend."
        lines = ["TRACE ID             ROOT OPERATION              DURATION"]
        for item in traces:
            lines.append(
                f"{item.get('trace_id', '-'):<20} {item.get('operation', '-'):<26} {item.get('duration', '-')}"
            )
        return "\n".join(lines)
