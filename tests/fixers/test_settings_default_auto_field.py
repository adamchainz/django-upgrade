from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(6, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_not_settings_file():
    check_noop(
        """\
        DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
        """,
    )


def test_no_assignment():
    check_noop(
        """\
        foo = "bar"
        """,
        filename="myapp/settings.py",
    )


def test_not_in_module():
    check_noop(
        """\
        def foo():
            DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
        """,
        filename="myapp/settings.py",
    )


def test_not_default_big_auto_field():
    check_noop(
        """\
        DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
        """,
        filename="myapp/settings.py",
    )


def test_default_big_auto_field():
    check_transformed(
        """\
        DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
        foo = "bar"
        """,
        """\
        foo = "bar"
        """,
        filename="myapp/settings.py",
    )
