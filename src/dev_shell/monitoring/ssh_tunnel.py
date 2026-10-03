from __future__ import annotations

import subprocess
import time
from pathlib import Path

from dev_shell.core.errors import SSHConnectionError, TunnelStartError
from dev_shell.monitoring.models import ServerConfig
from dev_shell.utils.logger import get_logger
from dev_shell.utils.ports import find_free_local_port, wait_for_port

logger = get_logger("dev_shell.ssh_tunnel")


class SSHTunnel:
    def __init__(
        self,
        host: str,
        username: str,
        remote_port: int,
        identity_file: str | None = None,
        ssh_port: int = 22,
        local_port: int | None = None,
        keepalive_interval: int = 15,
        keepalive_count: int = 3,
    ) -> None:
        self.host = host
        self.username = username
        self.remote_port = remote_port
        self.identity_file = identity_file
        self.ssh_port = ssh_port
        self._requested_local_port = local_port
        self.keepalive_interval = keepalive_interval
        self.keepalive_count = keepalive_count
        self._process: subprocess.Popen[bytes] | None = None
        self.local_port = 0

    @classmethod
    def from_server(cls, server: ServerConfig, local_port: int | None = None) -> SSHTunnel:
        return cls(
            host=server.host,
            username=server.username,
            remote_port=server.monitor_port,
            identity_file=server.identity_file,
            ssh_port=server.ssh_port,
            local_port=local_port,
        )

    def build_command(self, local_port: int | None = None) -> list[str]:
        port = local_port if local_port is not None else self.local_port or self._requested_local_port
        if not port:
            raise TunnelStartError("local port has not been allocated")
        command = [
            "ssh",
            "-N",
            "-L",
            f"{port}:127.0.0.1:{self.remote_port}",
            "-o",
            "BatchMode=yes",
            "-o",
            "ExitOnForwardFailure=yes",
            "-o",
            f"ServerAliveInterval={self.keepalive_interval}",
            "-o",
            f"ServerAliveCountMax={self.keepalive_count}",
            "-p",
            str(self.ssh_port),
        ]
        if self.identity_file:
            command.extend(["-i", str(Path(self.identity_file).expanduser())])
        command.append(f"{self.username}@{self.host}")
        return command

    def start(self) -> None:
        if self.is_running():
            return
        self.local_port = find_free_local_port(self._requested_local_port)
        command = self.build_command(self.local_port)
        logger.info("starting SSH tunnel to %s@%s local_port=%s", self.username, self.host, self.local_port)
        try:
            self._process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
            )
        except OSError as exc:
            raise TunnelStartError(f"failed to start ssh: {exc}") from exc
        if not wait_for_port("127.0.0.1", self.local_port, timeout=15.0):
            stderr = self._read_stderr()
            self.stop()
            raise TunnelStartError(
                f"SSH forwarding port {self.local_port} did not become usable. {stderr}".strip()
            )
        if self._process.poll() is not None:
            stderr = self._read_stderr()
            raise SSHConnectionError(stderr or "ssh process exited before the tunnel was ready")

    def stop(self) -> None:
        process = self._process
        self._process = None
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        logger.info("SSH tunnel stopped local_port=%s", self.local_port)

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def _read_stderr(self) -> str:
        process = self._process
        if process is None or process.stderr is None:
            return ""
        try:
            time.sleep(0.05)
            if process.poll() is None:
                return ""
            data = process.stderr.read()
            text = data.decode("utf-8", errors="replace").strip()
            return text
        except OSError:
            return ""
