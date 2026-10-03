from __future__ import annotations

import os
import platform
import socket

from dev_shell.core.context import ShellContext
from dev_shell.core.registry import CommandRegistry


def _sysinfo(args: list[str], context: ShellContext) -> int:
    print(f"hostname   {socket.gethostname()}")
    print(f"system     {platform.system()} {platform.release()}")
    print(f"machine    {platform.machine()}")
    print(f"python     {platform.python_version()}")
    print(f"cwd        {context.cwd}")
    return 0


def _whoami(args: list[str], context: ShellContext) -> int:
    print(os.environ.get("USER") or os.environ.get("USERNAME") or "unknown")
    return 0


def _env(args: list[str], context: ShellContext) -> int:
    if args:
        print(os.environ.get(args[0], ""))
        return 0
    for key in sorted(os.environ):
        print(f"{key}={os.environ[key]}")
    return 0


def register(registry: CommandRegistry) -> None:
    registry.add("sysinfo", _sysinfo, "Show local system information", category="System", usage="sysinfo")
    registry.add("whoami", _whoami, "Show the current user", category="System", usage="whoami")
    registry.add("env", _env, "Show environment variables", category="System", usage="env [NAME]")
