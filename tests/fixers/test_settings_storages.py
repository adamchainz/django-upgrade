from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(4, 2))


def test_not_settings_file():
    check_noop(
        """\
        DEFAULT_FILE_STORAGE = "example.backend"
        """,
        settings,
    )


def test_not_within_module():
    check_noop(
        """\
        if PRODUCTION:
            DEFAULT_FILE_STORAGE = "example.backend"
        """,
        settings,
    )


def test_not_constant():
    check_noop(
        """\
        DEFAULT_FILE_STORAGE = get_storage_backend()
        """,
        settings,
        filename="settings.py",
    )


def test_not_string():
    check_noop(
        """\
        DEFAULT_FILE_STORAGE = 1
        """,
        settings,
        filename="settings.py",
    )


def test_one_not_string():
    check_noop(
        """\
        DEFAULT_FILE_STORAGE = get_storage_backend()
        STATICFILES_STORAGE = "example.backend"
        """,
        settings,
        filename="settings.py",
    )


def test_duplicated():
    check_noop(
        """\
        DEFAULT_FILE_STORAGE = "example.backend"
        DEFAULT_FILE_STORAGE = "example.other.backend"
        """,
        settings,
        filename="settings.py",
    )


def test_already_up_to_date():
    check_noop(
        """\
        STORAGES = {
            "default": {
                "BACKEND": "example.backend",
            },
        }
        """,
        settings,
        filename="settings.py",
    )


def test_setting_exists():
    check_noop(
        """\
        STORAGES = {
            "default": {
                "BACKEND": "example.backend",
            },
        }
        STATICFILES_STORAGE = "example.other.backend"
        """,
        settings,
        filename="settings.py",
    )


def test_one():
    check_transformed(
        """\
        DEFAULT_FILE_STORAGE = "example.backend"
        """,
        """\
        STORAGES = {
            "default": {
                "BACKEND": "example.backend",
            },
        }
        """,
        settings,
        filename="settings.py",
    )


def test_both():
    check_transformed(
        """\
        DEFAULT_FILE_STORAGE = "example.backend"
        STATICFILES_STORAGE = "example.other.backend"
        """,
        """\
        STORAGES = {
            "default": {
                "BACKEND": "example.backend",
            },
            "staticfiles": {
                "BACKEND": "example.other.backend",
            },
        }
        """,
        settings,
        filename="settings.py",
    )


def test_both_staticfiles_first():
    check_transformed(
        """\
        STATICFILES_STORAGE = "example.other.backend"
        DEFAULT_FILE_STORAGE = "example.backend"
        """,
        """\
        STORAGES = {
            "default": {
                "BACKEND": "example.backend",
            },
            "staticfiles": {
                "BACKEND": "example.other.backend",
            },
        }
        """,
        settings,
        filename="settings.py",
    )


def test_retains_quoting():
    check_transformed(
        """\
        DEFAULT_FILE_STORAGE = 'example.backend'
        """,
        """\
        STORAGES = {
            "default": {
                "BACKEND": 'example.backend',
            },
        }
        """,
        settings,
        filename="settings.py",
    )


def test_star_import_not_settings():
    check_transformed(
        """\
        from example import *
        DEFAULT_FILE_STORAGE = "example.backend"
        """,
        """\
        from example import *
        STORAGES = {
            "default": {
                "BACKEND": "example.backend",
            },
        }
        """,
        settings,
        filename="settings.py",
    )


def test_star_import_base_settings():
    check_transformed(
        """\
        from base_settings import *
        DEFAULT_FILE_STORAGE = "example.backend"
        """,
        """\
        from base_settings import *
        STORAGES = {
            **STORAGES,
            "default": {
                "BACKEND": "example.backend",
            },
        }
        """,
        settings,
        filename="settings.py",
    )


def test_star_import_extended_module_path():
    check_transformed(
        """\
        from example.settings.base import *
        DEFAULT_FILE_STORAGE = "example.backend"
        """,
        """\
        from example.settings.base import *
        STORAGES = {
            **STORAGES,
            "default": {
                "BACKEND": "example.backend",
            },
        }
        """,
        settings,
        filename="settings.py",
    )
