from __future__ import annotations

from collections.abc import Iterator

import requests

from dev_shell.core.errors import (
    InvalidEventError,
    MonitoringServiceUnavailable,
    StreamDisconnected,
    StreamProtocolError,
    UnsupportedProtocolVersion,
)
from dev_shell.monitoring.health import HealthClient
from dev_shell.monitoring.models import StreamEvent, parse_event
from dev_shell.utils.logger import get_logger

logger = get_logger("dev_shell.stream_client")


class MonitoringStreamClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._health = HealthClient(self.base_url, timeout=timeout)
        self._response: requests.Response | None = None
        self.last_sequence: int | None = None
        self.sequence_gaps: list[int] = []

    def health(self) -> dict:
        return self._health.health()

    def close(self) -> None:
        response = self._response
        self._response = None
        if response is not None:
            response.close()

    def stream(self) -> Iterator[StreamEvent]:
        url = f"{self.base_url}/stream"
        logger.info("opening stream %s", url)
        try:
            response = requests.get(
                url,
                stream=True,
                timeout=(self.timeout, None),
                headers={"Accept": "application/x-ndjson"},
            )
        except requests.RequestException as exc:
            raise MonitoringServiceUnavailable(str(exc)) from exc
        if response.status_code != 200:
            response.close()
            raise MonitoringServiceUnavailable(
                f"GET /stream returned HTTP {response.status_code}"
            )
        self._response = response
        try:
            for raw_line in response.iter_lines(decode_unicode=True):
                if raw_line is None:
                    continue
                line = raw_line.strip() if isinstance(raw_line, str) else raw_line.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    event = parse_event(line)
                except UnsupportedProtocolVersion:
                    raise
                except InvalidEventError as exc:
                    logger.error("skipping invalid event: %s", exc)
                    continue
                except StreamProtocolError as exc:
                    logger.error("protocol error: %s", exc)
                    continue
                self._track_sequence(event)
                yield event
        except requests.RequestException as exc:
            raise StreamDisconnected(str(exc)) from exc
        finally:
            self.close()
        raise StreamDisconnected("stream ended")

    def _track_sequence(self, event: StreamEvent) -> None:
        if self.last_sequence is not None and event.sequence > self.last_sequence + 1:
            missing = list(range(self.last_sequence + 1, event.sequence))
            self.sequence_gaps.extend(missing)
            logger.warning(
                "sequence gap on %s: expected %s, got %s",
                event.server_id,
                self.last_sequence + 1,
                event.sequence,
            )
        self.last_sequence = event.sequence
