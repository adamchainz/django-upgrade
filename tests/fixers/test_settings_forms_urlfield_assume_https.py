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
        FORMS_URLFIELD_ASSUME_HTTPS = True
        """,
    )


def test_false():
    check_noop(
        """\
        FORMS_URLFIELD_ASSUME_HTTPS = False
        """,
        filename="myapp/settings.py",
    )


def test_dynamic():
    check_noop(
        """\
        import os
        FORMS_URLFIELD_ASSUME_HTTPS = os.environ["FORMS_URLFIELD_ASSUME_HTTPS"]
        """,
        filename="myapp/settings.py",
    )


def test_ignore_conditional():
    check_noop(
        """\
        if something:
            FORMS_URLFIELD_ASSUME_HTTPS = True
        """,
        filename="myapp/settings.py",
    )


def test_success():
    check_transformed(
        """\
        FORMS_URLFIELD_ASSUME_HTTPS = True
        """,
        "",
        filename="myapp/settings.py",
    )


def test_success_comment():
    check_transformed(
        """\
        FORMS_URLFIELD_ASSUME_HTTPS = True  # forms future compat
        """,
        "",
        filename="myapp/settings.py",
    )


def test_success_settings_subfolder():
    check_transformed(
        """\
        FORMS_URLFIELD_ASSUME_HTTPS = True
        """,
        "",
        filename="myapp/settings/prod.py",
    )


def test_success_function_call_multiline():
    check_transformed(
        """\
        FORMS_URLFIELD_ASSUME_HTTPS = \
            True
        """,
        "",
        filename="myapp/settings.py",
    )


def test_success_with_other_lines():
    check_transformed(
        """\
        import os
        FORMS_URLFIELD_ASSUME_HTTPS = True
        ANOTHER_SETTING = True
        """,
        """\
        import os
        ANOTHER_SETTING = True
        """,
        filename="myapp/settings.py",
    )


def test_success_with_class_based_settings():
    check_transformed(
        """\
        class BaseSettings:
            SETTINGS_1 = True
            FORMS_URLFIELD_ASSUME_HTTPS = True
            SETTINGS_2 = True
        """,
        """\
        class BaseSettings:
            SETTINGS_1 = True
            SETTINGS_2 = True
        """,
        filename="myapp/settings/base.py",
    )


def test_success_with_class_based_settings_inherited():
    check_transformed(
        """\
        class BaseSettings:
            SETTINGS_1 = True
            FORMS_URLFIELD_ASSUME_HTTPS = True

        class ProdSettings(BaseSettings):
            SETTINGS_2 = True
            FORMS_URLFIELD_ASSUME_HTTPS = True
        """,
        """\
        class BaseSettings:
            SETTINGS_1 = True

        class ProdSettings(BaseSettings):
            SETTINGS_2 = True
        """,
        filename="myapp/settings/base.py",
    )


def test_success_with_class_based_configurations():
    check_transformed(
        """\
        DEBUG = False
        FORMS_URLFIELD_ASSUME_HTTPS = True

        class Dev(Configuration):
            DEBUG = True
            FORMS_URLFIELD_ASSUME_HTTPS = True
        """,
        """\
        DEBUG = False

        class Dev(Configuration):
            DEBUG = True
        """,
        filename="myapp/settings/base.py",
    )
