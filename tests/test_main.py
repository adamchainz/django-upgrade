from __future__ import annotations

import pytest

from repo_tool.main import main


def test_no_command():
    with pytest.raises(SystemExit) as excinfo:
        main([])

    assert excinfo.value.code == 2


def test_unknown_command():
    with pytest.raises(SystemExit) as excinfo:
        main(["unknown-command"])

    assert excinfo.value.code == 2


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
