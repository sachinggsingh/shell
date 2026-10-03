from __future__ import annotations

from pathlib import Path

from dev_shell.core.context import ShellContext
from dev_shell.core.registry import CommandRegistry


def _pwd(args: list[str], context: ShellContext) -> int:
    print(context.cwd)
    return 0


def _cd(args: list[str], context: ShellContext) -> int:
    target = args[0] if args else str(Path.home())
    path = context.resolve(target)
    if not path.exists() or not path.is_dir():
        print(f"cd failed in directory: {path} is not a directory")
        return 1
    context.cwd = path
    return 0


def _ls(args: list[str], context: ShellContext) -> int:
    path = context.resolve(args[0]) if args else context.cwd
    if not path.exists():
        print(f"ls failed in directory: {path} does not exist")
        return 1
    if path.is_file():
        print(path.name)
        return 0
    try:
        entries = sorted(path.iterdir(), key=lambda item: item.name.lower())
    except OSError as exc:
        print(f"ls failed in directory: {exc}")
        return 1
    for entry in entries:
        suffix = "/" if entry.is_dir() else ""
        print(f"{entry.name}{suffix}")
    return 0


def _mkdir(args: list[str], context: ShellContext) -> int:
    parents = "-p" in args or "--parents" in args
    targets = [item for item in args if not item.startswith("-")]
    if not targets:
        print("mkdir failed in directory: usage: mkdir [-p] PATH")
        return 2
    path = context.resolve(targets[0])
    try:
        path.mkdir(parents=parents, exist_ok=parents)
    except FileExistsError:
        print(f"mkdir failed in directory: {path} already exists")
        return 1
    except OSError as exc:
        print(f"mkdir failed in directory: {exc}")
        return 1
    return 0


def _rmdir(args: list[str], context: ShellContext) -> int:
    if not args:
        print("rmdir failed in directory: usage: rmdir PATH")
        return 2
    path = context.resolve(args[0])
    try:
        path.rmdir()
    except OSError as exc:
        print(f"rmdir failed in directory: {exc}")
        return 1
    return 0


def register(registry: CommandRegistry) -> None:
    registry.add("pwd", _pwd, "Print working directory", category="Directory", usage="pwd")
    registry.add("cd", _cd, "Change directory", category="Directory", usage="cd [PATH]")
    registry.add("ls", _ls, "List directory contents", category="Directory", usage="ls [PATH]")
    registry.add("mkdir", _mkdir, "Create a directory", category="Directory", usage="mkdir [-p] PATH")
    registry.add("rmdir", _rmdir, "Remove an empty directory", category="Directory", usage="rmdir PATH")
