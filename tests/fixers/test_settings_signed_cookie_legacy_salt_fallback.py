from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(7, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_not_settings_file():
    check_noop(
        """\
        SIGNED_COOKIE_LEGACY_SALT_FALLBACK = True
        """,
    )


def test_false():
    check_noop(
        """\
        SIGNED_COOKIE_LEGACY_SALT_FALLBACK = False
        """,
        filename="myapp/settings.py",
    )


def test_dynamic():
    check_noop(
        """\
        import os
        SIGNED_COOKIE_LEGACY_SALT_FALLBACK = os.environ["SIGNED_COOKIE_LEGACY_SALT_FALLBACK"]
        """,
        filename="myapp/settings.py",
    )


def test_ignore_conditional():
    check_noop(
        """\
        if something:
            SIGNED_COOKIE_LEGACY_SALT_FALLBACK = True
        """,
        filename="myapp/settings.py",
    )


def test_success():
    check_transformed(
        """\
        SIGNED_COOKIE_LEGACY_SALT_FALLBACK = True
        """,
        "",
        filename="myapp/settings.py",
    )


def test_success_comment():
    check_transformed(
        """\
        SIGNED_COOKIE_LEGACY_SALT_FALLBACK = True  # legacy salt compat
        """,
        "",
        filename="myapp/settings.py",
    )


def test_success_settings_subfolder():
    check_transformed(
        """\
        SIGNED_COOKIE_LEGACY_SALT_FALLBACK = True
        """,
        "",
        filename="myapp/settings/prod.py",
    )


def test_success_function_call_multiline():
    check_transformed(
        """\
        SIGNED_COOKIE_LEGACY_SALT_FALLBACK = \
            True
        """,
        "",
        filename="myapp/settings.py",
    )


def test_success_with_other_lines():
    check_transformed(
        """\
        import os
        SIGNED_COOKIE_LEGACY_SALT_FALLBACK = True
        ANOTHER_SETTING = True
        """,
        """\
        import os
        ANOTHER_SETTING = True
        """,
        filename="myapp/settings.py",
    )


def test_class_not_settings_file():
    check_noop(
        """\
        class Settings:
            ADMINS = []
            SIGNED_COOKIE_LEGACY_SALT_FALLBACK = True
        """,
    )


def test_class_false():
    check_noop(
        """\
        class Settings:
            ADMINS = []
            SIGNED_COOKIE_LEGACY_SALT_FALLBACK = False
        """,
        filename="myapp/settings.py",
    )


def test_class_dynamic():
    check_noop(
        """\
        import os
        class Settings:
            ADMINS = []
            SIGNED_COOKIE_LEGACY_SALT_FALLBACK = os.environ["SIGNED_COOKIE_LEGACY_SALT_FALLBACK"]
        """,
        filename="myapp/settings.py",
    )


def test_class_ignore_conditional():
    check_noop(
        """\
        class Settings:
            ADMINS = []
            if something:
                SIGNED_COOKIE_LEGACY_SALT_FALLBACK = True
        """,
        filename="myapp/settings.py",
    )


def test_class_only_assignment():
    check_noop(
        """\
        class Settings:
            SIGNED_COOKIE_LEGACY_SALT_FALLBACK = True
        """,
        filename="myapp/settings.py",
    )


def test_class_success():
    check_transformed(
        """\
        class Settings:
            ADMINS = []
            SIGNED_COOKIE_LEGACY_SALT_FALLBACK = True
        """,
        """\
        class Settings:
            ADMINS = []
        """,
        filename="myapp/settings.py",
    )


def test_class_success_with_inheritance():
    check_transformed(
        """\
        class BaseSettings:
            ADMINS = []
            SIGNED_COOKIE_LEGACY_SALT_FALLBACK = True

        class ProdSettings(BaseSettings):
            ADMINS = []
            SIGNED_COOKIE_LEGACY_SALT_FALLBACK = True
        """,
        """\
        class BaseSettings:
            ADMINS = []

        class ProdSettings(BaseSettings):
            ADMINS = []
        """,
        filename="myapp/settings/base.py",
    )
