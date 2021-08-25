from textwrap import dedent

import pytest

from django_upgrade._data import Settings
from django_upgrade._main import _fix_plugins


@pytest.mark.parametrize(
    ("s",),
    (
        pytest.param(
            dedent(
                """\
                from django.utils.encoding import something

                something("yada")
                """
            ),
            id="no deprecated aliases",
        ),
        pytest.param(
            dedent(
                """\
                from django.utils import encoding

                encoding.force_text("yada")
                """
            ),
            id="not right import format",
        ),
    ),
)
def test_fix_unittest_aliases_noop(s):
    assert _fix_plugins(s, settings=Settings(target_version=(3, 0))) == s


@pytest.mark.parametrize(
    ("s", "expected"),
    (
        (
            dedent(
                """\
                from django.utils.encoding import force_text, smart_text

                force_text("yada")
                smart_text("yada")
                """
            ),
            dedent(
                """\
                from django.utils.encoding import force_str, smart_str

                force_str("yada")
                smart_str("yada")
                """
            ),
        ),
        (
            dedent(
                """\
                from django.utils.encoding import force_text as ft

                ft("yada")
                """
            ),
            dedent(
                """\
                from django.utils.encoding import force_str as ft

                ft("yada")
                """
            ),
        ),
    ),
)
def test_fix_old_names(s, expected):
    ret = _fix_plugins(s, settings=Settings(target_version=(3, 0)))
    assert ret == expected
