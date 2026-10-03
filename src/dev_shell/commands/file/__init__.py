from __future__ import annotations

import shutil

from dev_shell.core.context import ShellContext
from dev_shell.core.registry import CommandRegistry


def _fail(operation: str, exc: OSError) -> int:
    print(f"{operation} failed in file: {exc}")
    return 1


def _cat(args: list[str], context: ShellContext) -> int:
    if not args:
        print("cat failed in file: usage: cat PATH")
        return 2
    path = context.resolve(args[0])
    try:
        print(path.read_text(encoding="utf-8"), end="")
    except OSError as exc:
        return _fail("cat", exc)
    return 0


def _touch(args: list[str], context: ShellContext) -> int:
    if not args:
        print("touch failed in file: usage: touch PATH")
        return 2
    path = context.resolve(args[0])
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    except OSError as exc:
        return _fail("touch", exc)
    return 0


def _cp(args: list[str], context: ShellContext) -> int:
    if len(args) < 2:
        print("cp failed in file: usage: cp SOURCE DEST")
        return 2
    try:
        shutil.copy2(context.resolve(args[0]), context.resolve(args[1]))
    except OSError as exc:
        return _fail("cp", exc)
    return 0


def _mv(args: list[str], context: ShellContext) -> int:
    if len(args) < 2:
        print("mv failed in file: usage: mv SOURCE DEST")
        return 2
    try:
        shutil.move(str(context.resolve(args[0])), str(context.resolve(args[1])))
    except OSError as exc:
        return _fail("mv", exc)
    return 0


def _rm(args: list[str], context: ShellContext) -> int:
    if not args:
        print("rm failed in file: usage: rm [-r] PATH")
        return 2
    recursive = "-r" in args or "-rf" in args or "--recursive" in args
    targets = [item for item in args if not item.startswith("-")]
    if not targets:
        print("rm failed in file: usage: rm [-r] PATH")
        return 2
    for target in targets:
        path = context.resolve(target)
        try:
            if path.is_dir() and recursive:
                shutil.rmtree(path)
            elif path.is_dir():
                print(f"rm failed in file: {path} is a directory (use rm -r)")
                return 1
            else:
                path.unlink()
        except OSError as exc:
            return _fail("rm", exc)
    return 0


def register(registry: CommandRegistry) -> None:
    registry.add("cat", _cat, "Print file contents", category="File", usage="cat PATH")
    registry.add("touch", _touch, "Create an empty file", category="File", usage="touch PATH")
    registry.add("cp", _cp, "Copy a file", category="File", usage="cp SOURCE DEST")
    registry.add("mv", _mv, "Move a file", category="File", usage="mv SOURCE DEST")
    registry.add("rm", _rm, "Remove a file or directory", category="File", usage="rm [-r] PATH")
