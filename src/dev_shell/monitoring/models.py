from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from dev_shell.core.errors import InvalidEventError, UnsupportedProtocolVersion
from dev_shell.utils.validators import is_loopback_host, parse_monitor_endpoint, require_non_empty, require_port

SUPPORTED_PROTOCOL_VERSION = 1
KNOWN_EVENT_TYPES = frozenset({"ready", "heartbeat", "metric", "log", "error"})


@dataclass(slots=True)
class ServerConfig:
    name: str
    host: str
    username: str
    ssh_port: int = 22
    monitor_port: int = 9477
    identity_file: str | None = None
    direct: bool = False

    def __post_init__(self) -> None:
        self.name = require_non_empty(self.name, "name")
        self.username = require_non_empty(self.username, "username")
        self.ssh_port = require_port(self.ssh_port, "ssh_port")
        self.monitor_port = require_port(self.monitor_port, "monitor_port")
        self.host, parsed_port = parse_monitor_endpoint(self.host, self.monitor_port)
        self.monitor_port = parsed_port
        if self.identity_file == "":
            self.identity_file = None
        if not self.direct and is_loopback_host(self.host):
            self.direct = True

    def use_direct(self) -> bool:
        return bool(self.direct) or is_loopback_host(self.host)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServerConfig:
        return cls(
            name=str(data.get("name", "")),
            host=str(data.get("host", "")),
            username=str(data.get("username", "")),
            ssh_port=int(data.get("ssh_port", 22)),
            monitor_port=int(data.get("monitor_port", 9477)),
            identity_file=data.get("identity_file"),
            direct=bool(data.get("direct", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "host": self.host,
            "username": self.username,
            "ssh_port": self.ssh_port,
            "monitor_port": self.monitor_port,
        }
        if self.identity_file:
            payload["identity_file"] = self.identity_file
        if self.direct:
            payload["direct"] = True
        return payload


@dataclass(slots=True)
class MetricEvent:
    timestamp: datetime
    server_id: str
    sequence: int
    name: str
    value: float
    unit: str
    labels: dict[str, str]


@dataclass(slots=True)
class LogEvent:
    timestamp: datetime
    server_id: str
    sequence: int
    level: str
    service: str
    message: str
    source: str


@dataclass(slots=True)
class StreamEvent:
    event_type: str
    version: int
    timestamp: datetime
    server_id: str
    sequence: int
    data: dict[str, object]


def parse_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value:
        raise InvalidEventError("timestamp must be an ISO-8601 string")
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise InvalidEventError(f"invalid timestamp {value!r}") from exc


def validate_envelope(raw: dict[str, Any]) -> None:
    for field_name in ("type", "version", "timestamp", "server_id", "sequence", "data"):
        if field_name not in raw:
            raise InvalidEventError(f"missing required field {field_name}")
    version = raw["version"]
    if not isinstance(version, int):
        raise UnsupportedProtocolVersion(version)
    if version != SUPPORTED_PROTOCOL_VERSION:
        raise UnsupportedProtocolVersion(version)
    if not isinstance(raw["type"], str) or not raw["type"]:
        raise InvalidEventError("type must be a non-empty string")
    if not isinstance(raw["server_id"], str) or not raw["server_id"]:
        raise InvalidEventError("server_id must be a non-empty string")
    if not isinstance(raw["sequence"], int) or raw["sequence"] < 0:
        raise InvalidEventError("sequence must be a non-negative integer")
    if not isinstance(raw["data"], dict):
        raise InvalidEventError("data must be an object")


def parse_event(line: str) -> StreamEvent:
    import json

    try:
        raw = json.loads(line)
    except json.JSONDecodeError as exc:
        raise InvalidEventError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(raw, dict):
        raise InvalidEventError("event must be a JSON object")
    validate_envelope(raw)
    return StreamEvent(
        event_type=str(raw["type"]),
        version=int(raw["version"]),
        timestamp=parse_timestamp(raw["timestamp"]),
        server_id=str(raw["server_id"]),
        sequence=int(raw["sequence"]),
        data=dict(raw["data"]),
    )


def to_metric_event(event: StreamEvent) -> MetricEvent:
    data = event.data
    name = data.get("name")
    value = data.get("value")
    if not isinstance(name, str) or not name:
        raise InvalidEventError("metric name must be a non-empty string")
    if not isinstance(value, (int, float)):
        raise InvalidEventError("metric value must be a number")
    labels_raw = data.get("labels") or {}
    if not isinstance(labels_raw, dict):
        raise InvalidEventError("metric labels must be an object")
    labels = {str(k): str(v) for k, v in labels_raw.items()}
    unit = data.get("unit", "")
    return MetricEvent(
        timestamp=event.timestamp,
        server_id=event.server_id,
        sequence=event.sequence,
        name=name,
        value=float(value),
        unit=str(unit),
        labels=labels,
    )


def to_log_event(event: StreamEvent) -> LogEvent:
    data = event.data
    return LogEvent(
        timestamp=event.timestamp,
        server_id=event.server_id,
        sequence=event.sequence,
        level=str(data.get("level", "")),
        service=str(data.get("service", "")),
        message=str(data.get("message", "")),
        source=str(data.get("source", "")),
    )
