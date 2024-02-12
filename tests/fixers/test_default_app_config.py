from __future__ import annotations

from functools import partial

import pytest

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(3, 2))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_invalid_assign_target():
    check_noop(
        """\
        app_config = 'nope'
        """,
        filename="__init__.py",
    )


def test_gated():
    check_noop(
        """\
        if 1:
            default_app_config = 'something'
        """,
        filename="__init__.py",
    )


def test_not_string():
    check_noop(
        """\
        default_app_config = 123
        """,
        filename="__init__.py",
    )


def test_dynamic():
    check_noop(
        """\
        default_app_config = "a" + "b"
        """,
        filename="__init__.py",
    )


@pytest.mark.parametrize("filename", ["my_app.py", "my_app__init__.py"])
def test_invalid_filename(filename: str) -> None:
    check_noop(
        """\
        default_app_config = 'myapp.apps.MyAppConfig'
        """,
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
        filename=filename,
    )


def test_with_comment() -> None:
    check_transformed(
        """\
        default_app_config = 'myapp.apps.MyAppConfig'  # django < 3.2
        """,
        "",
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
        filename="__init__.py",
    )
