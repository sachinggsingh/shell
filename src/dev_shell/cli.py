from __future__ import annotations

from pathlib import Path

from dev_shell.commands.directory import register as register_directory
from dev_shell.commands.file import register as register_file
from dev_shell.commands.logs import register as register_logs
from dev_shell.commands.meta import register as register_meta
from dev_shell.commands.monitor import register as register_monitor
from dev_shell.commands.network import register as register_network
from dev_shell.commands.permissions import register as register_permissions
from dev_shell.commands.server import register as register_server
from dev_shell.commands.system import register as register_system
from dev_shell.core.context import ShellContext
from dev_shell.core.registry import CommandRegistry
from dev_shell.core.shell import Shell
from dev_shell.monitoring.registry import ServerRegistry


def build_registry() -> CommandRegistry:
    registry = CommandRegistry()
    register_directory(registry)
    register_file(registry)
    register_system(registry)
    register_network(registry)
    register_server(registry)
    register_logs(registry)
    register_permissions(registry)
    register_meta(registry)
    register_monitor(registry)
    return registry


def build_shell(config_path: str | None = None) -> Shell:
    path = Path(config_path).expanduser() if config_path else None
    context = ShellContext(cwd=Path.cwd(), config_path=path)
    context.registry = ServerRegistry(context.config_path)
    return Shell(build_registry(), context)


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="dev_shell", add_help=True)
    parser.add_argument("--config", help="Path to client config.json")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    shell = build_shell(args.config)
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if command:
        return shell.run_argv(command)
    return shell.repl()


if __name__ == "__main__":
    raise SystemExit(main())
