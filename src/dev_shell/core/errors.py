class DevShellError(Exception):
    """Base application error with operation, component, and reason."""

    def __init__(self, operation: str, component: str, reason: str, *args: object) -> None:
        self.operation = operation
        self.component = component
        self.reason = reason
        super().__init__(f"{operation} failed in {component}: {reason}", *args)


class ServerNotFoundError(DevShellError):
    def __init__(self, name: str) -> None:
        super().__init__("resolve_server", "server_registry", f"server {name!r} is not registered")
        self.name = name


class SSHConnectionError(DevShellError):
    def __init__(self, reason: str) -> None:
        super().__init__("ssh_connect", "ssh_tunnel", reason)


class TunnelStartError(DevShellError):
    def __init__(self, reason: str) -> None:
        super().__init__("start_tunnel", "ssh_tunnel", reason)


class MonitoringServiceUnavailable(DevShellError):
    def __init__(self, reason: str) -> None:
        super().__init__("health_check", "monitoring", reason)


class StreamProtocolError(DevShellError):
    def __init__(self, reason: str) -> None:
        super().__init__("parse_stream", "stream_client", reason)


class StreamDisconnected(DevShellError):
    def __init__(self, reason: str = "stream closed") -> None:
        super().__init__("read_stream", "stream_client", reason)


class InvalidEventError(DevShellError):
    def __init__(self, reason: str) -> None:
        super().__init__("validate_event", "stream_client", reason)


class UnsupportedProtocolVersion(DevShellError):
    def __init__(self, version: object) -> None:
        super().__init__(
            "validate_event",
            "stream_client",
            f"unsupported protocol version {version!r}",
        )
        self.version = version
