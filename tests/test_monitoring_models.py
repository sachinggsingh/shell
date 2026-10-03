from datetime import timezone

import pytest

from dev_shell.core.errors import InvalidEventError, UnsupportedProtocolVersion
from dev_shell.monitoring.models import ServerConfig, parse_event, to_metric_event


def test_server_config_validation():
    with pytest.raises(ValueError):
        ServerConfig(name="", host="h", username="u")
    with pytest.raises(ValueError):
        ServerConfig(name="n", host="h", username="u", ssh_port=0)
    cfg = ServerConfig(name="production-1", host="203.0.113.10", username="devshell")
    assert cfg.monitor_port == 9477
    assert cfg.direct is False


def test_server_config_strips_health_url():
    cfg = ServerConfig(
        name="golang",
        host="http://127.0.0.1:9477",
        username="sachin",
    )
    assert cfg.host == "127.0.0.1"
    assert cfg.monitor_port == 9477
    assert cfg.direct is True
    assert cfg.use_direct() is True


def test_host_port_without_scheme():
    cfg = ServerConfig(name="n", host="127.0.0.1:9477", username="u")
    assert cfg.host == "127.0.0.1"
    assert cfg.monitor_port == 9477
    assert cfg.direct is True
    cfg = ServerConfig(name="prod", host="203.0.113.10", username="devshell")
    assert cfg.direct is False
    assert cfg.use_direct() is False


def test_parse_metric_event():
    line = (
        '{"type":"metric","version":1,'
        '"timestamp":"2026-09-29T09:30:01Z",'
        '"server_id":"server-1","sequence":1,'
        '"data":{"name":"cpu.percent","value":20.5,"unit":"percent"}}'
    )
    event = parse_event(line)
    assert event.event_type == "metric"
    assert event.data["name"] == "cpu.percent"
    metric = to_metric_event(event)
    assert metric.value == 20.5
    assert metric.timestamp.replace(tzinfo=timezone.utc)


def test_parse_invalid_json():
    with pytest.raises(InvalidEventError):
        parse_event("{")


def test_missing_type():
    with pytest.raises(InvalidEventError):
        parse_event(
            '{"version":1,"timestamp":"2026-09-29T09:30:01Z","server_id":"s","sequence":1,"data":{}}'
        )


def test_unsupported_version():
    with pytest.raises(UnsupportedProtocolVersion):
        parse_event(
            '{"type":"metric","version":2,"timestamp":"2026-09-29T09:30:01Z","server_id":"s","sequence":1,"data":{}}'
        )


def test_unknown_type_does_not_crash():
    event = parse_event(
        '{"type":"future","version":1,"timestamp":"2026-09-29T09:30:01Z","server_id":"s","sequence":1,"data":{}}'
    )
    assert event.event_type == "future"
