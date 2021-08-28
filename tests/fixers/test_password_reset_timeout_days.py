from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 1))


def test_not_settings_file():
    check_noop(
        """\
        PASSWORD_RESET_TIMEOUT_DAYS = 4
        """,
        settings,
    )


def test_success():
    check_transformed(
        """\
        PASSWORD_RESET_TIMEOUT_DAYS = 4
        """,
        """\
        PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 4
        """,
        settings,
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
        settings,
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
        settings,
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
        settings,
        filename="myapp/settings.py",
    )
