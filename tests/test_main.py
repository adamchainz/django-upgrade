from __future__ import annotations

import subprocess
import sys

import pytest

from repo_tool import __main__  # noqa: F401
from repo_tool.main import main


def test_no_command():
    with pytest.raises(SystemExit) as excinfo:
        main([])

    assert excinfo.value.code == 2


def test_unknown_command():
    with pytest.raises(SystemExit) as excinfo:
        main(["unknown-command"])

    assert excinfo.value.code == 2


def test_main_module_subprocess():
    proc = subprocess.run(
        [sys.executable, "-m", "repo_tool", "--help"],
        check=True,
        capture_output=True,
    )

    assert proc.stdout.startswith(b"usage: repo-tool ")


def test_version(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])

    assert excinfo.value.code == 0
    out, err = capsys.readouterr()
    assert out.count(".") >= 2


def test_help(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])

    assert excinfo.value.code == 0
    out, err = capsys.readouterr()
    assert "changelog" in out
    assert "release" in out
    assert "upgrade-dependencies" in out
