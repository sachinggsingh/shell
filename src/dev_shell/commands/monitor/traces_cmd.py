from __future__ import annotations

from dev_shell.commands.monitor.connect_cmd import resolve_server
from dev_shell.core.context import ShellContext
from dev_shell.render.traces_table import TracesTable


def traces_command(args: list[str], context: ShellContext) -> int:
    server = resolve_server(args, context)
    print(f"SERVER: {server.name}")
    print(
        "Tracing is optional and export-only in this build. "
        "Trace querying is unavailable because no Jaeger query backend is configured."
    )
    print(TracesTable().render([]))
    return 0
