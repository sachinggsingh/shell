from pathlib import Path

from dev_shell.core.context import ShellContext
from dev_shell.monitoring.models import ServerConfig
from dev_shell.monitoring.registry import ServerRegistry


def test_registry_via_commands(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text('{"servers":[]}', encoding="utf-8")
    context = ShellContext(cwd=tmp_path, config_path=path, registry=ServerRegistry(path))
    context.registry.add(ServerConfig(name="lab", host="127.0.0.1", username="devshell", direct=True))
    assert context.registry.get("lab").direct is True
