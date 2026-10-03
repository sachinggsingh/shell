from __future__ import annotations

import shutil
import socket
import subprocess

from dev_shell.core.context import ShellContext
from dev_shell.core.registry import CommandRegistry


def _ping(args: list[str], context: ShellContext) -> int:
    if not args:
        print("ping failed in network: usage: ping HOST")
        return 2
    ping = shutil.which("ping")
    if ping is None:
        print("ping failed in network: ping executable is not installed")
        return 1
    completed = subprocess.run([ping, "-c", "3", args[0]], check=False)
    return int(completed.returncode)


def _dns(args: list[str], context: ShellContext) -> int:
    if not args:
        print("dns failed in network: usage: dns HOSTNAME")
        return 2
    try:
        infos = socket.getaddrinfo(args[0], None)
    except OSError as exc:
        print(f"dns failed in network: {exc}")
        return 1
    seen: set[str] = set()
    for info in infos:
        address = info[4][0]
        if address not in seen:
            seen.add(address)
            print(address)
    return 0


def register(registry: CommandRegistry) -> None:
    registry.add("ping", _ping, "Ping a host", category="Network", usage="ping HOST")
    registry.add("dns", _dns, "Resolve a hostname", category="Network", usage="dns HOSTNAME")
