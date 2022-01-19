from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(2, 0))


def test_unmatched_import():
    check_noop(
        """\
        from functools import lru_cache
        """,
        settings,
    )


def test_unmatched_import_name():
    check_noop(
        """\
        from django.utils.functional import SimpleLazyObject
        """,
        settings,
    )


def test_unrecognized_import_format():
    check_noop(
        """\
        from django.utils import functional

        @functional.lru_cache
        def foo():
            ...
        """,
        settings,
    )


def test_fixed():
    check_transformed(
        """\
        from django.utils.functional import lru_cache

        @lru_cache
        def foo():
            ...
        """,
        """\
        from functools import lru_cache

        @lru_cache
        def foo():
            ...
        """,
        settings,
    )
