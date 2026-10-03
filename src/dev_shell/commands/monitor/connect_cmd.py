from __future__ import annotations

import time

from dev_shell.core.context import ShellContext
from dev_shell.core.errors import DevShellError, StreamDisconnected
from dev_shell.monitoring.connect import MonitoringConnection
from dev_shell.monitoring.jaeger_client import JaegerClient
from dev_shell.monitoring.models import ServerConfig
from dev_shell.monitoring.reconnect import ReconnectPolicy
from dev_shell.monitoring.registry import ServerRegistry
from dev_shell.utils.logger import get_logger

logger = get_logger("dev_shell.monitor.connect")


def resolve_server(args: list[str], context: ShellContext) -> ServerConfig:
    if not args:
        raise DevShellError("resolve_server", "servers", "server name is required")
    registry = context.registry or ServerRegistry(context.config_path)
    context.registry = registry
    return registry.get(args[0])


def connect_server(args: list[str], context: ShellContext) -> int:
    server = resolve_server(args, context)
    tracer = JaegerClient()
    print(f"Connecting to {server.name}...")
    with tracer.span("monitor.connect", server=server.name):
        with tracer.span("monitor.ssh_tunnel", host=server.host):
            connection = MonitoringConnection(server)
            health = connection.connect()
    print("SSH tunnel established." if not server.use_direct() else "Direct local connection established.")
    print(f"Monitoring service: {health.get('status', 'unknown')}.")
    print(f"Protocol: v{health.get('version', '0.1.0')}.")
    print("Stream: ready.")
    return 0


def watch_events(connection: MonitoringConnection, on_event, reconnect: bool = True) -> None:
    policy = ReconnectPolicy()
    while True:
        try:
            if connection.server.use_direct():
                if connection.client is None:
                    connection.connect()
            elif connection.tunnel is None or not connection.tunnel.is_running():
                connection.connect()
            connection.health()
            policy.reset()
            for event in connection.stream():
                on_event(event)
        except (StreamDisconnected, OSError) as exc:
            logger.warning("stream failure: %s", exc)
            if not reconnect:
                raise
            delay = policy.next_delay()
            print(f"stream disconnected; reconnecting in {delay}s...")
            time.sleep(delay)
            try:
                connection.close()
            except Exception:
                pass
            continue
