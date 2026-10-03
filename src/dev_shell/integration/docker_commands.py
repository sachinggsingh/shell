from __future__ import annotations

import subprocess

from dev_shell.core.context import ShellContext


def run_docker(args: list[str], context: ShellContext) -> int:
    completed = subprocess.run(["docker", *args], cwd=context.cwd, check=False)
    return int(completed.returncode)
