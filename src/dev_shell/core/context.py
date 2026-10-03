from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from dev_shell.monitoring.registry import ServerRegistry


@dataclass
class ShellContext:
    cwd: Path = field(default_factory=Path.cwd)
    config_path: Path | None = None
    registry: ServerRegistry | None = None
    interactive: bool = True
    history: list[str] = field(default_factory=list)
    last_command: str | None = None
    command_registry: object | None = None

    def resolve(self, path: str) -> Path:
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = (self.cwd / candidate).resolve()
        else:
            candidate = candidate.resolve()
        return candidate

    def record_command(self, line: str) -> None:
        text = line.strip()
        if not text:
            return
        self.last_command = text
        if self.history and self.history[-1] == text:
            return
        self.history.append(text)
        if len(self.history) > 100:
            del self.history[:-100]
