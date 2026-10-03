from __future__ import annotations

from dev_shell import __version__
from dev_shell.core.context import ShellContext
from dev_shell.core.registry import CommandRegistry
from dev_shell.integration.docker_commands import run_docker
from dev_shell.integration.git_commands import run_git


def _help(args: list[str], context: ShellContext) -> int:
    registry = context.command_registry
    if registry is None:
        from dev_shell.cli import build_registry

        registry = build_registry()
    topic = args[0] if args else None
    print(registry.help_text(topic))
    return 0


def _version(args: list[str], context: ShellContext) -> int:
    print(__version__)
    return 0


def _clear(args: list[str], context: ShellContext) -> int:
    print("\033[2J\033[H", end="")
    return 0


def _history(args: list[str], context: ShellContext) -> int:
    if not context.history:
        print("No commands in history yet.")
        return 0
    start = max(len(context.history) - 20, 0)
    for index, command in enumerate(context.history[start:], start=start + 1):
        print(f"{index:>4}  {command}")
    return 0


def _last(args: list[str], context: ShellContext) -> int:
    if not context.last_command:
        print("No previous command.")
        return 0
    print(context.last_command)
    return 0


def _git(args: list[str], context: ShellContext) -> int:
    return run_git(args, context)


def _docker(args: list[str], context: ShellContext) -> int:
    return run_docker(args, context)


def register(registry: CommandRegistry) -> None:
    registry.add(
        "help",
        _help,
        "Show commands by category, or help for one command",
        category="Shell",
        usage="help [command|category]",
    )
    registry.add(
        "version",
        _version,
        "Show dev_shell version",
        category="Shell",
        usage="version",
    )
    registry.add(
        "clear",
        _clear,
        "Clear the terminal",
        category="Shell",
        usage="clear",
    )
    registry.add(
        "history",
        _history,
        "Show recent commands",
        category="Shell",
        usage="history",
    )
    registry.add(
        "last",
        _last,
        "Show the last command",
        category="Shell",
        usage="last   (rerun with !!)",
    )
    registry.add(
        "git",
        _git,
        "Run git in the current directory",
        category="Integration",
        usage="git STATUS_ARGS...",
    )
    registry.add(
        "docker",
        _docker,
        "Run docker in the current directory",
        category="Integration",
        usage="docker ARGS...",
    )
