from __future__ import annotations

from dev_shell.commands.monitor.connect_cmd import resolve_server
from dev_shell.core.context import ShellContext


def sources_command(args: list[str], context: ShellContext) -> int:
    server = resolve_server(args, context)
    print(f"SERVER: {server.name}")
    print()
    print("Metrics")
    print("  cpu")
    print("  memory")
    print("  disk")
    print("  network")
    print("  system")
    print()
    print("Logs")
    print("  (configured on the remote agent; journal and explicit files only)")
    return 0
