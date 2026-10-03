from pathlib import Path

from dev_shell.cli import build_shell
from dev_shell.commands.monitor.dashboard_cmd import parse_watch_args


def test_help_is_grouped_by_category(capsys):
    shell = build_shell()
    assert shell.run_argv(["help"]) == 0
    out = capsys.readouterr().out
    for heading in ("Directory", "File", "System", "Network", "Servers", "Monitoring"):
        assert heading in out
    assert "add-server" in out
    assert "watch-server" in out


def test_help_command_and_category(capsys):
    shell = build_shell()
    assert shell.run_argv(["help", "add-server"]) == 0
    out = capsys.readouterr().out
    assert "Usage:" in out
    assert shell.run_argv(["help", "network"]) == 0
    out = capsys.readouterr().out
    assert "ping" in out
    assert "dns" in out


def test_file_and_directory_commands(tmp_path: Path, capsys):
    shell = build_shell()
    shell.context.cwd = tmp_path
    assert shell.run_argv(["mkdir", "-p", "a/b"]) == 0
    assert shell.run_argv(["touch", "a/b/note.txt"]) == 0
    assert shell.run_argv(["ls", "a/b"]) == 0
    assert "note.txt" in capsys.readouterr().out
    assert shell.run_argv(["cat", "a/b/note.txt"]) == 0
    assert shell.run_argv(["rm", "a/b/note.txt"]) == 0
    assert not (tmp_path / "a/b/note.txt").exists()


def test_add_server_and_history(tmp_path: Path, capsys):
    config = tmp_path / "config.json"
    config.write_text('{"servers":[]}', encoding="utf-8")
    shell = build_shell(str(config))
    shell.context.interactive = False
    assert shell.run_argv(["add-server", "lab", "10.0.0.5", "devshell"]) == 0
    assert shell.run_argv(["add", "server", "name=local", "host=127.0.0.1", "user=devshell", "direct=true"]) == 0
    assert shell.run_argv(["servers"]) == 0
    listed = capsys.readouterr().out
    assert "lab" in listed
    assert "local" in listed
    assert shell.run_argv(["last"]) == 0
    assert "servers" in capsys.readouterr().out.strip()
    assert shell.run_argv(["pwd"]) == 0
    capsys.readouterr()
    assert shell.run_argv(["last"]) == 0
    assert capsys.readouterr().out.strip() == "pwd"
    assert shell.run_argv(["history"]) == 0
    history = capsys.readouterr().out
    assert "add-server lab 10.0.0.5 devshell" in history
    assert "pwd" in history


def test_parse_watch_args_default_interval():
    names, interval = parse_watch_args(["golang"])
    assert names == ["golang"]
    assert interval == 5.0
    names, interval = parse_watch_args(["golang", "-i", "3"])
    assert names == ["golang"]
    assert interval == 3.0


def test_watch_server_rejects_bad_interval(capsys):
    shell = build_shell()
    assert shell.run_argv(["watch-server", "x", "-i", "0"]) == 2
    assert "greater than 0" in capsys.readouterr().out
