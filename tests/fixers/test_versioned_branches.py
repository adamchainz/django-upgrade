from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(4, 0))


def test_future_version_gte():
    check_noop(
        """\
        import django

        if django.VERSION >= (4, 1):
            foo()
        """,
        settings,
    )


def test_elif():
    check_noop(
        """\
        import django

        if something:
            pass
        elif django.VERSION >= (4, 0):
            foo()
        """,
        settings,
    )


def test_current_version_gte():
    check_transformed(
        """\
        import django

        if django.VERSION >= (4, 0):
            foo()
        """,
        """\
        import django

        foo()
        """,
        settings,
    )


def test_current_version_gte_in_function():
    check_transformed(
        """\
        import django

        def foo():
            if django.VERSION >= (4, 0):
                bar()
        """,
        """\
        import django

        def foo():
            bar()
        """,
        settings,
    )


def test_current_version_gte_in_if():
    check_transformed(
        """\
        import django

        if something:
            if django.VERSION >= (4, 0):
                bar()
        """,
        """\
        import django

        if something:
            bar()
        """,
        settings,
    )


def test_current_version_gte_with_else():
    check_transformed(
        """\
        import django

        if django.VERSION >= (4, 0):
            foo()
        else:
            bar()
        """,
        """\
        import django

        foo()
        """,
        settings,
    )


def test_current_version_gt():
    check_transformed(
        """\
        import django

        if django.VERSION > (3, 2):
            foo()
        """,
        """\
        import django

        foo()
        """,
        settings,
    )
