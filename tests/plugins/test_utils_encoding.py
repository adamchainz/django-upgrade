from textwrap import dedent

import pytest

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
    ),
)
def test_fix_unittest_aliases_noop(s):
    assert _fix_plugins(s) == s


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
    ),
)
def test_fix_old_names(s, expected):
    ret = _fix_plugins(s)
    assert ret == expected
