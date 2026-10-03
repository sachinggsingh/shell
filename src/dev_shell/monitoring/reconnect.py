from __future__ import annotations

from collections.abc import Iterator

BACKOFF_SECONDS = (1, 2, 4, 8, 16, 30)


class ReconnectPolicy:
    def __init__(self, delays: tuple[int, ...] = BACKOFF_SECONDS) -> None:
        self.delays = delays
        self.attempt = 0

    def reset(self) -> None:
        self.attempt = 0

    def next_delay(self) -> int:
        index = min(self.attempt, len(self.delays) - 1)
        delay = self.delays[index]
        self.attempt += 1
        return delay

    def delays_iter(self) -> Iterator[int]:
        while True:
            yield self.next_delay()
