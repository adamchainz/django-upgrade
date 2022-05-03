from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 2))


def test_invalid_assign_target():
    check_noop(
        """\
        app_config = 'nope'
        """,
        settings,
        filename="__init__.py",
    )


def test_invalid_filename():
    check_noop(
        """\
        default_app_config = 'myapp.apps.MyAppConfig'
        """,
        settings,
        filename="my_app.py",
    )


def test_simple_case():
    check_transformed(
        """\
        default_app_config = 'myapp.apps.MyAppConfig'
        """,
        """\

        """,
        settings,
        filename="__init__.py",
    )
