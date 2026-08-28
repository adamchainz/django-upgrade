from __future__ import annotations

import subprocess
from functools import partial

run = partial(subprocess.run, check=True)


def uncommitted_changes() -> bool:
    return (
        subprocess.run(
            ["git", "diff", "--exit-code", "--no-patch"],
        ).returncode
        != 0
    )


def default_branch() -> str:
    main_exists = (
        subprocess.run(
            ["git", "rev-parse", "--quiet", "--verify", "main"],
            capture_output=True,
        ).returncode
        == 0
    )
    if main_exists:
        return "main"
    return "master"


def branch_exists(name: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--quiet", "--verify", name],
            capture_output=True,
        ).returncode
        == 0
    )
