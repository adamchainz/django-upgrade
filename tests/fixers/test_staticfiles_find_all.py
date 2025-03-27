from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(5, 2))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_no_import():
    check_noop(
        """\
        find("example.css", all=True)
        """,
    )


def test_wrong_import():
    check_noop(
        """\
        from django.contrib import find

        find("example.css", all=True)
        """,
    )


def test_no_all_kwarg():
    check_noop(
        """\
        from django.contrib.staticfiles import find

        find("example.css")
        """,
    )


def test_find_all_present():
    check_noop(
        """\
        from django.contrib.staticfiles import find

        find("example.css", all=True, find_all=True)
        """,
    )


def test_success():
    check_transformed(
        """\
        from django.contrib.staticfiles import find

        find("example.css", all=True)
        """,
        """\
        from django.contrib.staticfiles import find

        find("example.css", find_all=True)
        """,
    )


def test_success_other_args():
    check_transformed(
        """\
        from django.contrib.staticfiles import find

        find(
            "example.css",
            path="static",
            all=True,
        )
        """,
        """\
        from django.contrib.staticfiles import find

        find(
            "example.css",
            path="static",
            find_all=True,
        )
        """,
    )


def test_finders_import_no_transform():
    check_noop(
        """\
        import django.contrib.staticfiles.finders as finders

        finders.find("example.css", all=True)
        """,
    )


def test_finders_attr_success():
    check_transformed(
        """\
        from django.contrib.staticfiles import finders

        finders.find("example.css", all=True)
        """,
        """\
        from django.contrib.staticfiles import finders

        finders.find("example.css", find_all=True)
        """,
    )


def test_finders_attr_other_args():
    check_transformed(
        """\
        from django.contrib.staticfiles import finders

        finders.find(
            "example.css",
            path="static",
            all=True,
        )
        """,
        """\
        from django.contrib.staticfiles import finders

        finders.find(
            "example.css",
            path="static",
            find_all=True,
        )
        """,
    )


def test_not_finders_attr():
    check_noop(
        """\
        from django.contrib import staticfiles

        staticfiles.find("example.css", all=True)
        """,
    )
