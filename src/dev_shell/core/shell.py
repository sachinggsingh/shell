from __future__ import annotations

import shlex
from collections.abc import Iterable

from dev_shell.core.context import ShellContext
from dev_shell.core.errors import DevShellError
from dev_shell.core.registry import CommandRegistry
from dev_shell.utils.logger import get_logger

logger = get_logger("dev_shell.shell")


def _enable_readline(registry: CommandRegistry) -> None:
    try:
        import readline
    except ImportError:
        return

    names = registry.names()

    def complete(text: str, state: int) -> str | None:
        options = [name for name in names if name.startswith(text)]
        if state < len(options):
            return options[state]
        return None

    readline.set_completer(complete)
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" \t\n")


class Shell:
    def __init__(self, registry: CommandRegistry, context: ShellContext) -> None:
        self.registry = registry
        self.context = context
        self.context.command_registry = registry

    def run_line(self, line: str) -> int:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return 0
        if stripped in {"!!", "rerun"}:
            if not self.context.last_command:
                print("last failed in shell: no previous command")
                return 1
            print(f"+ {self.context.last_command}")
            return self.run_line(self.context.last_command)
        try:
            parts = shlex.split(stripped)
        except ValueError as exc:
            print(f"parse failed in cli: {exc}")
            return 2
        return self.run_argv(parts)

    def run_argv(self, argv: Iterable[str]) -> int:
        parts = list(argv)
        if not parts:
            return 0
        if parts[0] in {"!!", "rerun"}:
            if not self.context.last_command:
                print("last failed in shell: no previous command")
                return 1
            print(f"+ {self.context.last_command}")
            return self.run_argv(shlex.split(self.context.last_command))
        if parts[0] not in {"last", "history"}:
            self.context.record_command(shlex.join(parts))
        name = parts[0]
        args = parts[1:]
        spec = self.registry.get(name)
        if spec is None:
            print(f"unknown command: {name}. Type 'help' for commands by category.")
            return 127
        try:
            return int(spec.handler(args, self.context))
        except DevShellError as exc:
            logger.error("%s", exc)
            print(str(exc))
            return 1
        except KeyboardInterrupt:
            print()
            return 130
        except Exception as exc:  # noqa: BLE001 — keep REPL alive
            logger.exception("command %s crashed", name)
            print(f"{name} failed in {spec.category.lower()}: {exc}")
            return 1

    def repl(self) -> int:
        _enable_readline(self.registry)
        print("dev_shell 0.1.0 — type 'help' for commands by category, 'last' for the previous command, 'exit' to quit")
        while True:
            try:
                line = input("dev_shell> ")
            except EOFError:
                print()
                return 0
            except KeyboardInterrupt:
                print()
                continue
            if line.strip() in {"exit", "quit"}:
                self.context.record_command(line.strip())
                return 0
            code = self.run_line(line)
            if code == 130:
                continue
