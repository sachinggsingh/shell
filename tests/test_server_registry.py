from pathlib import Path

from dev_shell.monitoring.models import ServerConfig
from dev_shell.monitoring.registry import ServerRegistry


def test_server_registry_roundtrip(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text('{"servers":[]}', encoding="utf-8")
    registry = ServerRegistry(path)
    registry.add(ServerConfig(name="s1", host="10.0.0.1", username="devshell", identity_file="~/.ssh/id_ed25519"))
    loaded = ServerRegistry(path).get("s1")
    assert loaded.host == "10.0.0.1"
    assert loaded.identity_file == "~/.ssh/id_ed25519"
    registry.remove("s1")
    assert ServerRegistry(path).servers() == []
