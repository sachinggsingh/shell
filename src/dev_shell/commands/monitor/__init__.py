from __future__ import annotations

from dev_shell.commands.monitor.connect_cmd import connect_server
from dev_shell.commands.monitor.dashboard_cmd import dashboard_command
from dev_shell.commands.monitor.sources_cmd import sources_command
from dev_shell.commands.monitor.trace_cmd import trace_command
from dev_shell.commands.monitor.traces_cmd import traces_command
from dev_shell.core.context import ShellContext
from dev_shell.core.registry import CommandRegistry


def _monitor(args: list[str], context: ShellContext) -> int:
    if not args:
        print("monitor failed in monitoring: subcommand required")
        print("Usage: monitor <connect|sources|traces|trace|dashboard|watch> SERVER")
        return 2
    sub, rest = args[0], args[1:]
    if sub == "connect":
        return connect_server(rest, context)
    if sub == "sources":
        return sources_command(rest, context)
    if sub == "traces":
        return traces_command(rest, context)
    if sub == "trace":
        return trace_command(rest, context)
    if sub in {"dashboard", "watch"}:
        return dashboard_command(rest, context)
    print(f"monitor failed in monitoring: unknown subcommand {sub}")
    print("Usage: monitor <connect|sources|traces|trace|dashboard|watch> SERVER")
    return 2


def _watch_server(args: list[str], context: ShellContext) -> int:
    if not args:
        print("watch-server failed in monitoring: usage: watch-server NAME")
        return 2
    return dashboard_command(args, context)


def register(registry: CommandRegistry) -> None:
    registry.add(
        "monitor",
        _monitor,
        "Remote monitoring (connect, sources, dashboard, traces)",
        category="Monitoring",
        usage="monitor <connect|sources|dashboard|watch|traces|trace> SERVER [-i 3]",
    )
    registry.add(
        "watch-server",
        _watch_server,
        "Watch live metrics and logs for a server",
        category="Monitoring",
        usage="watch-server NAME [-i 3]",
    )
