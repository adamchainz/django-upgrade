from __future__ import annotations

import io
import re
import sys
from textwrap import dedent
from unittest import mock

import pytest
from tokenize_rt import UNIMPORTANT_WS
from tokenize_rt import src_to_tokens

from django_upgrade import __main__  # noqa: F401
from django_upgrade.main import fixup_dedent_tokens
from django_upgrade.main import main
from django_upgrade.tokens import DEDENT


def test_main_no_files(capsys):
    """
    Main should fail without any files as argument
    """
    with pytest.raises(SystemExit) as excinfo:
        main([])

    assert excinfo.value.code == 2
    out, err = capsys.readouterr()
    assert "error: the following arguments are required: filenames\n" in err
    assert out == ""


def test_main_help():
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])

    assert excinfo.value.code == 0


def test_main_version(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])

    out, err = capsys.readouterr()

    assert excinfo.value.code == 0
    assert re.fullmatch(r"__main__\.py \d+\.\d+\.\d+\n", out)
    assert err == ""


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


def test_fixup_dedent_tokens():
    code = dedent(
        """\
        if True:
            if True:
                pass
            else:
                pass
        """
    )
    tokens = src_to_tokens(code)

    assert tokens[14].name == UNIMPORTANT_WS
    assert tokens[15].name == DEDENT

    fixup_dedent_tokens(tokens)

    assert tokens[14].name == DEDENT
    assert tokens[15].name == UNIMPORTANT_WS
