from __future__ import annotations

from dev_shell.core.context import ShellContext
from dev_shell.core.registry import CommandRegistry


def _tail(args: list[str], context: ShellContext) -> int:
    if not args:
        print("tail failed in logs: usage: tail PATH")
        return 2
    path = context.resolve(args[0])
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-20:]
    except OSError as exc:
        print(f"tail failed in logs: {exc}")
        return 1
    for line in lines:
        print(line)
    return 0


def register(registry: CommandRegistry) -> None:
    registry.add("tail", _tail, "Show the last lines of a local file", category="Logs", usage="tail PATH")
