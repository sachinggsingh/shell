from __future__ import annotations

from typing import Any

import requests

from dev_shell.core.errors import MonitoringServiceUnavailable
from dev_shell.utils.logger import get_logger

logger = get_logger("dev_shell.health")


class HealthClient:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> dict[str, Any]:
        url = f"{self.base_url}/health"
        logger.info("requesting health %s", url)
        try:
            response = requests.get(url, timeout=self.timeout)
        except requests.RequestException as exc:
            raise MonitoringServiceUnavailable(str(exc)) from exc
        if response.status_code != 200:
            raise MonitoringServiceUnavailable(
                f"GET /health returned HTTP {response.status_code}"
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise MonitoringServiceUnavailable("GET /health returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise MonitoringServiceUnavailable("GET /health returned a non-object body")
        return payload
