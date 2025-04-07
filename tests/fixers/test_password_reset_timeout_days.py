from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(3, 1))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_not_settings_file():
    check_noop(
        """\
        PASSWORD_RESET_TIMEOUT_DAYS = 4
        """,
    )


def test_success():
    check_transformed(
        """\
        PASSWORD_RESET_TIMEOUT_DAYS = 4
        """,
        """\
        PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 4
        """,
        filename="myapp/settings.py",
    )


def test_success_settings_subfolder():
    check_transformed(
        """\
        PASSWORD_RESET_TIMEOUT_DAYS = 4
        """,
        """\
        PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 4
        """,
        filename="myapp/settings/prod.py",
    )


def test_success_function_call():
    check_transformed(
        """\
        import os
        PASSWORD_RESET_TIMEOUT_DAYS = int(os.environ["PASS_TIMEOUT"])
        """,
        """\
        import os
        PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * int(os.environ["PASS_TIMEOUT"])
        """,
        filename="myapp/settings.py",
    )


def test_success_function_call_multiline():
    check_transformed(
        """\
        import os
        PASSWORD_RESET_TIMEOUT_DAYS = int(
            os.environ["PASSWORD_RESET_TIMEOUT_DAYS"]
        )
        """,
        """\
        import os
        PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * int(
            os.environ["PASSWORD_RESET_TIMEOUT_DAYS"]
        )
        """,
        filename="myapp/settings.py",
    )


def test_success_class_based():
    check_transformed(
        """\
        class BaseSettings:
            PASSWORD_RESET_TIMEOUT_DAYS = 4
        """,
        """\
        class BaseSettings:
            PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 4
        """,
        filename="myapp/settings/base.py",
    )


def test_success_class_based_inherited():
    check_transformed(
        """\
        class BaseSettings:
            PASSWORD_RESET_TIMEOUT_DAYS = 4

        class DevSettings(BaseSettings):
            PASSWORD_RESET_TIMEOUT_DAYS = 2
        """,
        """\
        class BaseSettings:
            PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 4

        class DevSettings(BaseSettings):
            PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 2
        """,
        filename="myapp/settings/dev.py",
    )


def test_success_class_based_configurations():
    check_transformed(
        """\
        PASSWORD_RESET_TIMEOUT_DAYS = 4

        class Dev(Configurations):
            PASSWORD_RESET_TIMEOUT_DAYS = 2
        """,
        """\
        PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 4

        class Dev(Configurations):
            PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 2
        """,
        filename="myapp/settings.py",
    )
