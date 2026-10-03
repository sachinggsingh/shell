from __future__ import annotations

from dev_shell.commands.monitor.traces_cmd import traces_command
from dev_shell.core.context import ShellContext
from dev_shell.render.trace_tree import TraceTree


def trace_command(args: list[str], context: ShellContext) -> int:
    if len(args) < 2:
        print("trace failed in monitor: usage: monitor trace <server> <trace-id>")
        return 2
    print(f"SERVER: {args[0]}")
    print(
        "Trace querying is unavailable. Tracing, when enabled, only exports spans via OTLP."
    )
    print(TraceTree().render({"trace_id": args[1], "operation": "-", "duration": "-", "spans": []}))
    return 0
