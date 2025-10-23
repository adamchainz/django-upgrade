from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(6, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_setting_no_assignment():
    check_noop(
        """\
        foo = "bar"
        """,
        filename="myapp/settings.py",
    )


def test_setting_not_settings_file():
    check_noop(
        """\
        DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
        """,
    )


def test_setting_not_constant():
    check_noop(
        """\
        DEFAULT_AUTO_FIELD = pick_auto_field()
        """,
        filename="myapp/settings.py",
    )


def test_setting_not_str():
    check_noop(
        """\
        DEFAULT_AUTO_FIELD = 123
        """,
        filename="myapp/settings.py",
    )


def test_setting_not_big_auto_field():
    check_noop(
        """\
        DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
        """,
        filename="myapp/settings.py",
    )


def test_setting_class_not_big_auto_field():
    check_noop(
        """\
        class Settings:
            DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
        """,
        filename="myapp/settings.py",
    )


def test_setting_not_in_module_or_classdef():
    check_noop(
        """\
        def foo():
            DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
        """,
        filename="myapp/settings.py",
    )


def test_setting_class_only_assignment():
    check_noop(
        """\
        class Settings:
            DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
        """,
        filename="myapp/settings.py",
    )


def test_setting():
    check_transformed(
        """\
        DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
        """,
        """\
        """,
        filename="myapp/settings.py",
    )


def test_setting_multiline():
    check_transformed(
        """\
        DEFAULT_AUTO_FIELD = (
            "django.db.models.BigAutoField"
        )
        """,
        """\
        """,
        filename="myapp/settings.py",
    )


def test_setting_class():
    check_transformed(
        """\
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


def test_setting_class_multiline():
    check_transformed(
        """\
        class Settings:
            foo = "bar"
            DEFAULT_AUTO_FIELD = (
                "django.db.models.BigAutoField"
            )
        """,
        """\
        class Settings:
            foo = "bar"
        """,
        filename="myapp/settings.py",
    )


def test_app_config_untouched():
    # Previously, this fixer would transform AppConfig definitions, but that
    # turned out to be unsafe.
    check_noop(
        """\
        from django.apps import AppConfig

        class PineappleConfig(AppConfig):
            name = "pineapple"
            default_auto_field = "django.db.models.BigAutoField"
        """,
        filename="myapp/apps.py",
    )
