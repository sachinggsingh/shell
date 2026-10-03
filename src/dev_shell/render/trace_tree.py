from __future__ import annotations

from typing import Any


class TraceTree:
    def render(self, trace: dict[str, Any]) -> str:
        trace_id = trace.get("trace_id", "-")
        operation = trace.get("operation", "-")
        duration = trace.get("duration", "-")
        lines = [
            f"Trace ID: {trace_id}",
            f"Root operation: {operation}",
            f"Duration: {duration}",
        ]
        spans = trace.get("spans") or []
        for span in spans:
            indent = "  " * int(span.get("depth", 0))
            lines.append(
                f"{indent}- {span.get('service', '-')}/{span.get('operation', '-')} ({span.get('duration', '-')})"
            )
        return "\n".join(lines)
