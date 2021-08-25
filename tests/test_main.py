import io
import sys
from unittest import mock

import pytest

from django_upgrade import __main__  # noqa: F401
from django_upgrade._main import main


def test_main_trivial():
    assert main([]) == 0


def test_main_help():
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])

    assert excinfo.value.code == 0


def test_main_syntax_error(tmp_path):
    path = tmp_path / "example.py"
    path.write_text("print 1\n")

    result = main([str(path)])

    assert result == 0


def test_main_non_utf8_bytes(tmp_path, capsys):
    path = tmp_path / "example.py"
    path.write_bytes("# -*- coding: cp1252 -*-\nx = €\n".encode("cp1252"))

    result = main([str(path)])

    assert result == 1
    out, err = capsys.readouterr()
    assert out == f"{path} is non-utf-8 (not supported)\n"
    assert err == ""


def test_main_file(tmp_path, capsys):
    path = tmp_path / "example.py"
    path.write_text("from django.core.paginator import QuerySetPaginator\n")

    result = main([str(path)])

    assert result == 1
    out, err = capsys.readouterr()
    assert err == f"Rewriting {path}\n"
    assert path.read_text() == "from django.core.paginator import Paginator\n"


def test_main_exit_zero_even_if_changed(tmp_path, capsys):
    path = tmp_path / "example.py"
    path.write_text("from django.core.paginator import QuerySetPaginator\n")

    result = main(["--exit-zero-even-if-changed", str(path)])

    assert result == 0
    out, err = capsys.readouterr()
    assert err == f"Rewriting {path}\n"
    assert path.read_text() == "from django.core.paginator import Paginator\n"


def test_main_stdin_no_changes(capsys):
    stdin = io.TextIOWrapper(io.BytesIO(b'print("hi")\n'), "UTF-8")

    with mock.patch.object(sys, "stdin", stdin):
        result = main(["-"])

    assert result == 0
    out, err = capsys.readouterr()
    assert out == 'print("hi")\n'
    assert err == ""


def test_main_stdin_with_changes(capsys):
    input_ = "from django.core.paginator import QuerySetPaginator\n"
    stdin = io.TextIOWrapper(io.BytesIO(input_.encode()), "UTF-8")

    with mock.patch.object(sys, "stdin", stdin):
        result = main(["-"])

    assert result == 1
    out, err = capsys.readouterr()
    assert out == "from django.core.paginator import Paginator\n"
    assert err == ""
