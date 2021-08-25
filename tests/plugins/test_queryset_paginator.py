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
                from django.core.paginator import Paginator
                """
            ),
            id="no deprecated alias",
        ),
        pytest.param(
            dedent(
                """\
                from django.core import paginator

                paginator.QuerySetPaginator
                """
            ),
            id="not right import format",
        ),
    ),
)
def test_fix_queryset_paginator_noop(s):
    assert _fix_plugins(s, settings=Settings(target_version=(3, 0))) == s


@pytest.mark.parametrize(
    ("s", "expected"),
    (
        (
            dedent(
                """\
                from django.core.paginator import QuerySetPaginator

                QuerySetPaginator(...)
                """
            ),
            dedent(
                """\
                from django.core.paginator import Paginator

                Paginator(...)
                """
            ),
        ),
    ),
)
def test_fix_queryset_paginator(s, expected):
    ret = _fix_plugins(s, settings=Settings(target_version=(3, 0)))
    assert ret == expected
