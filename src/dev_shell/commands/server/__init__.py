from __future__ import annotations

import sys

from dev_shell.core.context import ShellContext
from dev_shell.core.registry import CommandRegistry
from dev_shell.monitoring.models import ServerConfig
from dev_shell.monitoring.registry import ServerRegistry


def _registry(context: ShellContext) -> ServerRegistry:
    if context.registry is None:
        context.registry = ServerRegistry(context.config_path)
    return context.registry


def _usage() -> None:
    print("add-server failed in servers: name, host, and user are required")
    print("Usage:")
    print("  add-server NAME HOST USER")
    print("  add-server name=prod host=203.0.113.10 user=devshell")
    print("  add-server name=local host=127.0.0.1 user=devshell")
    print("  add server NAME HOST USER")
    print("HOST is a hostname or IP (127.0.0.1), not a URL.")
    print("Optional: ssh_port=22 monitor_port=9477 identity_file=~/.ssh/id_ed25519 direct=true")


def _ask(label: str, default: str = "") -> str:
    if not sys.stdin.isatty():
        return default
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"{label}{suffix}: ").strip()
    except EOFError:
        return default
    return value or default


def _parse_server_args(args: list[str], context: ShellContext) -> ServerConfig | None:
    values = {item.split("=", 1)[0]: item.split("=", 1)[1] for item in args if "=" in item}
    positional = [item for item in args if "=" not in item]
    name = values.get("name") or (positional[0] if positional else "")
    host = values.get("host") or (positional[1] if len(positional) > 1 else "")
    username = (
        values.get("user")
        or values.get("username")
        or (positional[2] if len(positional) > 2 else "")
    )
    if context.interactive and sys.stdin.isatty():
        if not name:
            name = _ask("Server name")
        if not host:
            host = _ask("Host")
        if not username:
            username = _ask("SSH user")
    if not name or not host or not username:
        _usage()
        return None
    identity = values.get("identity_file") or values.get("identity")
    direct_raw = values.get("direct", "false")
    try:
        ssh_port = int(values.get("ssh_port", 22))
        monitor_port = int(values.get("monitor_port", 9477))
    except ValueError:
        print("add-server failed in servers: ssh_port and monitor_port must be integers")
        return None
    return ServerConfig(
        name=name,
        host=host,
        username=username,
        ssh_port=ssh_port,
        monitor_port=monitor_port,
        identity_file=identity,
        direct=str(direct_raw).lower() in {"1", "true", "yes"},
    )


def _add_server(args: list[str], context: ShellContext) -> int:
    server = _parse_server_args(args, context)
    if server is None:
        return 2
    registry = _registry(context)
    registry.add(server)
    mode = "direct" if server.direct else "ssh"
    print(f"registered server {server.name}")
    print(f"  {server.username}@{server.host}:{server.ssh_port}")
    print(f"  monitor_port={server.monitor_port}  mode={mode}")
    print(f"  saved to {registry.path}")
    if mode == "direct":
        print("  loopback hosts skip SSH and talk to the agent over HTTP")
    return 0


def _add(args: list[str], context: ShellContext) -> int:
    if args and args[0] in {"server", "servers"}:
        return _add_server(args[1:], context)
    print("add failed in servers: usage: add server NAME HOST USER")
    return 2


def _remove_server(args: list[str], context: ShellContext) -> int:
    if not args:
        print("remove-server failed in servers: usage: remove-server NAME")
        return 2
    _registry(context).remove(args[0])
    print(f"removed server {args[0]}")
    return 0


def _servers(args: list[str], context: ShellContext) -> int:
    servers = _registry(context).servers()
    if not servers:
        print("No servers registered. Add one with:")
        print("  add-server NAME HOST USER")
        print("  add-server name=local host=127.0.0.1 user=devshell direct=true")
        return 0
    print(f"{'NAME':<16} {'TARGET':<32} {'MONITOR':<10} {'MODE':<8} IDENTITY")
    for server in servers:
        identity = server.identity_file or "-"
        mode = "direct" if server.direct else "ssh"
        target = f"{server.username}@{server.host}:{server.ssh_port}"
        print(f"{server.name:<16} {target:<32} {server.monitor_port:<10} {mode:<8} {identity}")
    return 0


def _connect_server(args: list[str], context: ShellContext) -> int:
    if not args:
        print("connect-server failed in servers: usage: connect-server NAME")
        return 2
    from dev_shell.commands.monitor.connect_cmd import connect_server

    return connect_server(args, context)


def register(registry: CommandRegistry) -> None:
    registry.add(
        "add-server",
        _add_server,
        "Register a server for SSH/monitoring",
        category="Servers",
        usage="add-server NAME HOST USER [identity_file=PATH] [direct=true]",
        aliases=("addserver",),
    )
    registry.add(
        "add",
        _add,
        "add server NAME HOST USER",
        category="Servers",
        usage="add server NAME HOST USER",
    )
    registry.add(
        "remove-server",
        _remove_server,
        "Remove a registered server",
        category="Servers",
        usage="remove-server NAME",
    )
    registry.add(
        "servers",
        _servers,
        "List registered servers",
        category="Servers",
        usage="servers",
    )
    registry.add(
        "connect-server",
        _connect_server,
        "Open a monitoring connection to a server",
        category="Servers",
        usage="connect-server NAME",
    )
