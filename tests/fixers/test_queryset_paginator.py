from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(2, 2))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_no_deprecated_alias():
    check_noop(
        """\
        from django.core.paginator import Paginator
        """,
    )


def test_paginator_module_imported():
    check_transformed(
        """\
        from django.core import paginator

        paginator.QuerySetPaginator
        """,
        """\
        from django.core import paginator

        paginator.Paginator
        """,
    )


def test_success():
    check_transformed(
        """\
        from django.core.paginator import QuerySetPaginator

        QuerySetPaginator(...)
        """,
        """\
        from django.core.paginator import Paginator

        Paginator(...)
        """,
    )


def test_success_other_names():
    check_transformed(
        """\
        from django.core.paginator import QuerySetPaginator, foo, bar as baz
        """,
        """\
        from django.core.paginator import Paginator, foo, bar as baz
        """,
    )


def test_success_aliased():
    check_transformed(
        """\
        from django.core.paginator import QuerySetPaginator as P
        """,
        """\
        from django.core.paginator import Paginator as P
        """,
    )
