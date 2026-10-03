from pathlib import Path

from dev_shell.cli import build_shell


def test_dns_and_pwd(tmp_path: Path):
    shell = build_shell()
    shell.context.cwd = tmp_path
    assert shell.run_argv(["pwd"]) == 0
    assert shell.run_argv(["help"]) == 0
    assert shell.run_argv(["version"]) == 0
