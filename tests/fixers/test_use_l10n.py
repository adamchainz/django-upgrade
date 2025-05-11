from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(4, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_not_settings_file():
    check_noop(
        """\
        USE_L10N = True
        """,
    )


def test_false():
    check_noop(
        """\
        USE_L10N = False
        """,
        filename="myapp/settings.py",
    )


def test_dynamic():
    check_noop(
        """\
        import os
        USE_L10N = os.environ["USE_L10N"]
        """,
        filename="myapp/settings.py",
    )


def test_ignore_conditional():
    check_noop(
        """\
        if something:
            USE_L10N = True
        """,
        filename="myapp/settings.py",
    )


def test_success():
    check_transformed(
        """\
        USE_L10N = True
        """,
        "",
        filename="myapp/settings.py",
    )


def test_success_comment():
    check_transformed(
        """\
        USE_L10N = True  # localization
        """,
        "",
        filename="myapp/settings.py",
    )


def test_success_settings_subfolder():
    check_transformed(
        """\
        USE_L10N = True
        """,
        "",
        filename="myapp/settings/prod.py",
    )


def test_success_function_call_multiline():
    check_transformed(
        """\
        USE_L10N = \
            True
        """,
        "",
        filename="myapp/settings.py",
    )


def test_success_with_other_lines():
    check_transformed(
        """\
        import os
        USE_L10N = True
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
            USE_L10N = True
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
            USE_L10N = True

        class ProdSettings(BaseSettings):
            SETTINGS_2 = True
            USE_L10N = True
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
        USE_L10N = True

        class Dev(Configuration):
            DEBUG = True
            USE_L10N = True
        """,
        """\
        DEBUG = False

        class Dev(Configuration):
            DEBUG = True
        """,
        filename="myapp/settings/base.py",
    )
