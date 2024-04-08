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
from django_upgrade.data import FIXERS
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


def test_main_no_files_with_list_fixers():
    """
    Main should pass without any files as argument, if `--list-fixers` is passed in
    """
    result = main(["--list-fixers"])

    assert result == 0


def test_main_help():
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])

    assert excinfo.value.code == 0


def test_main_version(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])

    out, err = capsys.readouterr()

    assert excinfo.value.code == 0
    assert re.fullmatch(r"\d+\.\d+\.\d+\n", out)
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


def test_main_list_fixers(tmp_path, capsys):
    """
    Main with `--list-fixers` should not attempt to transform files
    """
    path = tmp_path / "example.py"
    path.write_text("from django.core.paginator import QuerySetPaginator\n")

    result = main(["--list-fixers", str(path)])

    assert result == 0
    out, err = capsys.readouterr()
    assert not err
    assert "Rewriting" not in err
    assert "Rewriting" not in out


def test_main_list_fixers_lists_fixers(tmp_path, capsys):
    """
    Main with `--list-fixers` should not attempt to transform files
    """
    result = main(["--list-fixers"])

    fixers = {fixer.name for fixer in FIXERS}

    assert result == 0
    out, err = capsys.readouterr()
    assert not err
    for fixer in fixers:
        assert fixer in out


def test_main_only_limits_fixers_invalid_fixer(tmp_path, capsys):
    """
    Main with --only invalid_fixer doesn't fix any files
    """
    path = tmp_path / "example.py"
    path.write_text("from django.core.paginator import QuerySetPaginator\n")

    result = main(["--only", "invalid_fixer", str(path)])

    assert result == 0
    out, err = capsys.readouterr()
    assert not err
    assert "Rewriting" not in err
    assert "Rewriting" not in out


def test_main_skip_excludes_fixers_invalid_fixer(tmp_path, capsys):
    """
    Main with --skip invalid_fixer fixes code as expected
    """
    path = tmp_path / "example.py"
    path.write_text("from django.core.paginator import QuerySetPaginator\n")

    result = main(["--skip", "invalid_fixer", str(path)])

    assert result == 1
    _, err = capsys.readouterr()
    assert err == f"Rewriting {path}\n"
    assert path.read_text() == "from django.core.paginator import Paginator\n"


def test_main_only_limits_fixers_valid_fixer(tmp_path, capsys):
    """
    Main with --only queryset_paginator limits fixes to that fixer
    """
    # Correctly fixes paginator code
    path = tmp_path / "example.py"
    path.write_text("from django.core.paginator import QuerySetPaginator\n")

    result = main(["--only", "queryset_paginator", str(path)])

    assert result == 1
    _, err = capsys.readouterr()
    assert err == f"Rewriting {path}\n"
    assert path.read_text() == "from django.core.paginator import Paginator\n"

    # Doesn't touch assert_form_error code
    path = tmp_path / "example2.py"
    path.write_text('self.assertFormError(response, "form", "user", "woops")\n')

    result = main(["--only", "queryset_paginator", str(path)])

    assert result == 0
    out, err = capsys.readouterr()
    assert not err
    assert "Rewriting" not in err
    assert "Rewriting" not in out


def test_main_skip_excludes_fixers_valid_fixer(tmp_path, capsys):
    """
    Main with --skip queryset_paginator ignores bad code
    """
    path = tmp_path / "example.py"
    path.write_text("from django.core.paginator import QuerySetPaginator\n")

    result = main(["--skip", "queryset_paginator", str(path)])

    assert result == 0
    out, err = capsys.readouterr()
    assert not err
    assert "Rewriting" not in err
    assert "Rewriting" not in out
