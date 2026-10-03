from __future__ import annotations

import os
import stat

from dev_shell.core.context import ShellContext
from dev_shell.core.registry import CommandRegistry


def _chmod(args: list[str], context: ShellContext) -> int:
    if len(args) < 2:
        print("chmod failed in permissions: usage: chmod MODE PATH")
        return 2
    path = context.resolve(args[1])
    try:
        os.chmod(path, int(args[0], 8))
    except ValueError:
        print("chmod failed in permissions: MODE must be octal, for example 644")
        return 2
    except OSError as exc:
        print(f"chmod failed in permissions: {exc}")
        return 1
    return 0


def _stat(args: list[str], context: ShellContext) -> int:
    if not args:
        print("stat failed in permissions: usage: stat PATH")
        return 2
    path = context.resolve(args[0])
    try:
        info = path.stat()
    except OSError as exc:
        print(f"stat failed in permissions: {exc}")
        return 1
    print(f"path  {path}")
    print(f"mode  {stat.filemode(info.st_mode)}")
    print(f"size  {info.st_size}")
    return 0


def register(registry: CommandRegistry) -> None:
    registry.add("chmod", _chmod, "Change file permissions", category="Permissions", usage="chmod MODE PATH")
    registry.add("stat", _stat, "Show file metadata", category="Permissions", usage="stat PATH")
