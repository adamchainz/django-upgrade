from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(6, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_not_apps_file():
    check_noop(
        """\
        from django.apps import AppConfig

        class DefaultConfig(AppConfig):
            name = "default"
            default_auto_field = "django.db.models.BigAutoField"
        """,
    )


def test_no_assignment():
    check_noop(
        """\
        from django.apps import AppConfig

        class DefaultConfig(AppConfig):
            name = "default"
        """,
        filename="myapp/apps.py",
    )


def test_not_in_classdef():
    check_noop(
        """\
        from django.apps import AppConfig

        class DefaultConfig(AppConfig):
            name = "default"
        default_auto_field = "django.db.models.BigAutoField"
        """,
        filename="myapp/apps.py",
    )


def test_not_default_big_auto_field():
    check_noop(
        """\
        from django.apps import AppConfig

        class DefaultConfig(AppConfig):
            name = "default"
            default_auto_field = "django.db.models.AutoField"
        """,
        filename="myapp/apps.py",
    )


def test_default_big_auto_field():
    check_transformed(
        """\
        from django.apps import AppConfig

        class DefaultConfig(AppConfig):
            name = "default"
            default_auto_field = "django.db.models.BigAutoField"
        """,
        """\
        from django.apps import AppConfig

        class DefaultConfig(AppConfig):
            name = "default"
        """,
        filename="myapp/apps.py",
    )
