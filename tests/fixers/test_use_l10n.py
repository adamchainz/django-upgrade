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
