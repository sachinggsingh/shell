from __future__ import annotations

import time

from dev_shell.commands.monitor.connect_cmd import resolve_server, watch_events
from dev_shell.core.context import ShellContext
from dev_shell.monitoring.connect import MonitoringConnection
from dev_shell.monitoring.models import KNOWN_EVENT_TYPES, to_log_event, to_metric_event
from dev_shell.render.logs_panel import LogsPanel
from dev_shell.render.metrics_panel import MetricsPanel
from dev_shell.utils.logger import get_logger

DEFAULT_REFRESH_SECONDS = 5.0
logger = get_logger("dev_shell.monitor.dashboard")


def parse_watch_args(args: list[str]) -> tuple[list[str], float]:
    interval = DEFAULT_REFRESH_SECONDS
    name_parts: list[str] = []
    pending: str | None = None
    for item in args:
        if pending == "interval":
            interval = float(item)
            pending = None
            continue
        if item in {"-i", "--interval"}:
            pending = "interval"
            continue
        if item.startswith("--interval="):
            interval = float(item.split("=", 1)[1])
            continue
        name_parts.append(item)
    if pending == "interval":
        raise ValueError("usage: watch-server NAME [-i 3]")
    if interval <= 0:
        raise ValueError("refresh interval must be greater than 0")
    return name_parts, interval


def _draw(metrics: MetricsPanel, logs: LogsPanel, interval: float) -> None:
    print("\033[2J\033[H", end="")
    print(metrics.render())
    print()
    print("LOGS")
    print(logs.render())
    print()
    print(f"(metrics and logs refresh every {interval:g}s — Ctrl+C to stop)")


def dashboard_command(args: list[str], context: ShellContext) -> int:
    try:
        name_args, interval = parse_watch_args(args)
    except ValueError as exc:
        print(f"watch-server failed in monitoring: {exc}")
        return 2
    server = resolve_server(name_args, context)
    connection = MonitoringConnection(server)
    metrics = MetricsPanel()
    logs = LogsPanel()
    metrics.update_status(server.name, "CONNECTING")
    connection.connect()
    metrics.update_status(server.name, "CONNECTED")
    _draw(metrics, logs, interval)
    last_draw = 0.0

    def on_event(event) -> None:
        nonlocal last_draw
        if event.event_type not in KNOWN_EVENT_TYPES:
            return
        if event.event_type == "metric":
            try:
                metrics.apply(to_metric_event(event))
            except Exception:
                return
        elif event.event_type == "log":
            try:
                logs.apply(to_log_event(event))
            except Exception:
                return
        elif event.event_type == "error":
            logger.error("remote error: %s", event.data)
            metrics.update_status(server.name, "DEGRADED")
        now = time.monotonic()
        if now - last_draw < interval:
            return
        last_draw = now
        metrics.update_status(server.name, "CONNECTED")
        _draw(metrics, logs, interval)

    try:
        watch_events(connection, on_event)
    except KeyboardInterrupt:
        print()
    finally:
        connection.close()
    return 0
