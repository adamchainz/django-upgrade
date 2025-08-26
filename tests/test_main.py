from __future__ import annotations

import io
import re
import subprocess
import sys
from textwrap import dedent
from unittest import mock

import pytest
from tokenize_rt import UNIMPORTANT_WS, src_to_tokens

from django_upgrade import __main__  # noqa: F401
from django_upgrade.main import fixup_dedent_tokens, get_target_version, main
from django_upgrade.tokens import DEDENT
from tests.compat import chdir


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


def test_main_help_subprocess():
    proc = subprocess.run(
        [sys.executable, "-m", "django_upgrade", "--help"],
        check=True,
        capture_output=True,
    )

    assert proc.stdout.startswith(b"usage: django-upgrade ")


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
    assert out == ""
    assert err == f"{path} is non-utf-8 (not supported)\n"


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

    assert result == 0
    out, err = capsys.readouterr()
    assert out == "from django.core.paginator import Paginator\n"
    assert err == ""


@pytest.mark.parametrize(
    "string,expected",
    [
        ("1.7", (1, 7)),
        ("2.2", (2, 2)),
        ("3.2", (3, 2)),
        ("5.2", (5, 2)),
    ],
)
def test_get_target_version_explicit(capsys, string, expected):
    assert get_target_version(string) == expected
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""


def test_get_target_version_auto_no_pyproject_toml(tmp_path, capsys):
    with chdir(tmp_path):
        assert get_target_version("auto") == (2, 2)

    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""


@pytest.mark.skipif(sys.version_info < (3, 11), reason="Python 3.11+")
@pytest.mark.parametrize(
    "deps_line,expected",
    [
        ("django>=3.2", (3, 2)),
        ("DJANGO>=3.2", (3, 2)),
        ("Django==4.0", (4, 0)),
        ("django~=4.1.3", (4, 1)),
        ("django>=3.2,<4.0", (3, 2)),
        ("django >= 2.2, <= 3.1", (2, 2)),
        ("django[argon2] >= 5.2", (5, 2)),
        ("django[argon2] >= 5.2, <6", (5, 2)),
    ],
)
def test_get_target_version_auto_matched(tmp_path, capsys, deps_line, expected):
    pyproject_content = f"""[project]
dependencies = [
    "{deps_line}",
]
"""
    (tmp_path / "pyproject.toml").write_text(pyproject_content)

    with chdir(tmp_path):
        assert get_target_version("auto") == expected

    out, err = capsys.readouterr()
    assert out == ""
    assert (
        err
        == f"Detected Django version from pyproject.toml: {expected[0]}.{expected[1]}\n"
    )


@pytest.mark.skipif(sys.version_info < (3, 11), reason="Python 3.11+")
@pytest.mark.parametrize(
    "deps_line",
    [
        "django-upgrade>=1.0.0",
        "Django>=5.2 ; sys_platform == 'linux'",
        "Django>=5.2, <6.0, !=5.2.1",
        "Django>=0.0",
        "DJANGO[argon2]>=0.0",
    ],
)
def test_get_target_version_auto_unmatched(tmp_path, capsys, deps_line):
    pyproject_content = f"""[project]
dependencies = [
    "{deps_line}",
]
"""
    (tmp_path / "pyproject.toml").write_text(pyproject_content)

    with chdir(tmp_path):
        assert get_target_version("auto") == (2, 2)

    out, err = capsys.readouterr()
    assert out == ""
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


def test_main_only(tmp_path, capsys):
    """
    Main with --only runs that fixer only.
    """
    path = tmp_path / "example.py"
    path.write_text(
        # For queryset_paginator, will change
        "from django.core.paginator import QuerySetPaginator\n"
        # For request_headers, will not change
        "request.META['HTTP_ACCEPT_ENCODING']\n"
    )

    result = main(["--only", "queryset_paginator", str(path)])

    assert result == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err == f"Rewriting {path}\n"
    assert path.read_text() == (
        "from django.core.paginator import Paginator\n"
        "request.META['HTTP_ACCEPT_ENCODING']\n"
    )


def test_main_only_multiple(tmp_path, capsys):
    """
    Main with multiple --only options selects multiple fixers.
    """
    path = tmp_path / "example.py"
    path.write_text(
        # For queryset_paginator, will change
        "from django.core.paginator import QuerySetPaginator\n"
        # For request_headers, will change
        "request.META['HTTP_ACCEPT_ENCODING']\n"
        # For timezone_fixedoffset, will not change
        "from django.utils.timezone import FixedOffset\n"
        'FixedOffset(120, "Super time")\n'
    )

    result = main(
        ["--only", "queryset_paginator", "--only", "request_headers", str(path)]
    )

    assert result == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err == f"Rewriting {path}\n"
    assert path.read_text() == (
        "from django.core.paginator import Paginator\n"
        "request.headers['accept-encoding']\n"
        "from django.utils.timezone import FixedOffset\n"
        'FixedOffset(120, "Super time")\n'
    )


def test_main_only_nonexistent_fixer(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--only", "nonexistent", "example.py"])

    assert excinfo.value.code == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert "error: argument --only: Unknown fixer: 'nonexistent'\n" in err


def test_main_skip(tmp_path, capsys):
    """
    Main with --skip does not run that fixer.
    """
    path = tmp_path / "example.py"
    source = "from django.core.paginator import QuerySetPaginator\n"
    path.write_text(source)

    result = main(["--skip", "queryset_paginator", str(path)])

    assert result == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    assert path.read_text() == source


def test_main_skip_multiple(tmp_path, capsys):
    """
    Main with multiple --skip options does not run those fixers.
    """
    path = tmp_path / "example.py"
    path.write_text(
        # For queryset_paginator, will not change
        "from django.core.paginator import QuerySetPaginator\n"
        # For request_headers, will not change
        "request.META['HTTP_ACCEPT_ENCODING']\n"
        # For timezone_fixedoffset, will change
        "from django.utils.timezone import FixedOffset\n"
        'FixedOffset(120, "Super time")\n'
    )

    result = main(
        ["--skip", "queryset_paginator", "--skip", "request_headers", str(path)]
    )

    assert result == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err == f"Rewriting {path}\n"
    assert path.read_text() == (
        "from django.core.paginator import QuerySetPaginator\n"
        "request.META['HTTP_ACCEPT_ENCODING']\n"
        "from datetime import timedelta, timezone\n"
        'timezone(timedelta(minutes=120), "Super time")\n'
    )


def test_main_skip_nonexistent_fixer(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--skip", "nonexistent", "example.py"])

    assert excinfo.value.code == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert "error: argument --skip: Unknown fixer: 'nonexistent'\n" in err


def test_main_list_fixers(tmp_path, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--list-fixers"])

    assert excinfo.value.code == 0
    out, err = capsys.readouterr()
    assert out.startswith("admin_allow_tags\n")
    assert err == ""


def test_main_list_fixers_filename(tmp_path, capsys):
    """
    Main with --list-fixers does not change files.
    """
    path = tmp_path / "example.py"
    source = "from django.core.paginator import QuerySetPaginator\n"
    path.write_text(source)

    with pytest.raises(SystemExit) as excinfo:
        main(["--list-fixers", str(path)])

    assert excinfo.value.code == 0
    # No change
    assert path.read_text() == source
