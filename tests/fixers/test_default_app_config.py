from __future__ import annotations

import pytest

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


def test_gated():
    check_noop(
        """\
        if 1:
            default_app_config = 'something'
        """,
        settings,
        filename="__init__.py",
    )


def test_not_string():
    check_noop(
        """\
        default_app_config = 123
        """,
        settings,
        filename="__init__.py",
    )


def test_dynamic():
    check_noop(
        """\
        default_app_config = "a" + "b"
        """,
        settings,
        filename="__init__.py",
    )


@pytest.mark.parametrize("filename", ["my_app.py", "my_app__init__.py"])
def test_invalid_filename(filename: str) -> None:
    check_noop(
        """\
        default_app_config = 'myapp.apps.MyAppConfig'
        """,
        settings,
        filename=filename,
    )


@pytest.mark.parametrize(
    "filename", ["__init__.py", "app/__init__.py", "project/app/__init__.py"]
)
def test_simple_case(filename: str) -> None:
    check_transformed(
        """\
        default_app_config = 'myapp.apps.MyAppConfig'
        """,
        "",
        settings,
        filename=filename,
    )


def test_with_comment() -> None:
    check_transformed(
        """\
        default_app_config = 'myapp.apps.MyAppConfig'  # django < 3.2
        """,
        "",
        settings,
        filename="__init__.py",
    )


def test_with_other_lines():
    check_transformed(
        """\
        import django
        default_app_config = 'myapp.apps.MyAppConfig'
        widgets = 12
        """,
        """\
        import django
        widgets = 12
        """,
        settings,
        filename="__init__.py",
    )
