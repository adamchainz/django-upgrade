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


def test_not_settings_file():
    check_noop(
        """\
        DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
        """,
    )


def test_apps_no_assignment():
    check_noop(
        """\
        from django.apps import AppConfig

        class DefaultConfig(AppConfig):
            name = "default"
        """,
        filename="myapp/apps.py",
    )


def test_settings_no_assignment():
    check_noop(
        """\
        foo = "bar"
        """,
        filename="myapp/settings.py",
    )


def test_apps_not_in_classdef():
    check_noop(
        """\
        from django.apps import AppConfig

        class DefaultConfig(AppConfig):
            name = "default"
        default_auto_field = "django.db.models.BigAutoField"
        """,
        filename="myapp/apps.py",
    )


def test_settings_not_in_module_or_classdef():
    check_noop(
        """\
        def foo():
            DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
        """,
        filename="myapp/settings.py",
    )


def test_apps_not_default_big_auto_field():
    check_noop(
        """\
        from django.apps import AppConfig

        class DefaultConfig(AppConfig):
            name = "default"
            default_auto_field = "django.db.models.AutoField"
        """,
        filename="myapp/apps.py",
    )


def test_apps_default_big_auto_field():
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


def test_settings_not_default_big_auto_field():
    check_noop(
        """\
        DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
        class Settings:
            DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
        """,
        filename="myapp/settings.py",
    )


def test_settings_default_big_auto_field():
    check_transformed(
        """\
        DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
        class Settings:
            foo = "bar"
            DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
        """,
        """\
        class Settings:
            foo = "bar"
        """,
        filename="myapp/settings.py",
    )
