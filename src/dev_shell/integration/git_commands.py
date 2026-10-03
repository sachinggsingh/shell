from __future__ import annotations

import subprocess
from pathlib import Path

from dev_shell.core.context import ShellContext


def run_git(args: list[str], context: ShellContext) -> int:
    cwd: Path = context.cwd
    completed = subprocess.run(["git", *args], cwd=cwd, check=False)
    return int(completed.returncode)
