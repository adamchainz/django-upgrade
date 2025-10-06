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
        ADMINS = [('Admin', 'admin@example.com')]
        """,
    )


def test_two_targets():
    check_noop(
        """\
        ADMINS, MANAGERS = [('Admin', 'admin@example.com')], [('Manager', 'manager@example.com')]
        """,
    )


def test_other_setting():
    check_noop(
        """\
        ADMINS_YEAH = [('Admin', 'admin@example.com')]
        """,
    )


def test_empty():
    check_noop(
        """\
        ADMINS = []
        """,
    )


def test_not_all_tuples():
    check_noop(
        """\
        ADMINS = [('Admin', 'admin@example.com'), other]
        """,
    )


def test_not_all_length_2():
    check_noop(
        """\
        ADMINS = [('Admin', 'admin@example.com'), ('admin@example.com',)]
        """,
    )


def test_admins_success():
    check_transformed(
        """\
        ADMINS = [('Admin', 'admin@example.com')]
        """,
        """\
        ADMINS = ['admin@example.com']
        """,
        filename="settings.py",
    )


def test_admins_class_settings_success():
    check_transformed(
        """\
        class Settings:
            ADMINS = [('Admin', 'admin@example.com')]
            APPEND_SLASH = True
        """,
        """\
        class Settings:
            ADMINS = ['admin@example.com']
            APPEND_SLASH = True
        """,
        filename="settings.py",
    )


def test_admins_indented():
    check_transformed(
        """\
        ADMINS = [
            ('Admin', 'admin@example.com')
        ]
        """,
        """\
        ADMINS = [
            'admin@example.com'
        ]
        """,
        filename="settings.py",
    )


def test_admins_variables():
    check_transformed(
        """\
        ADMINS = [(admin_name, admin_email)]
        """,
        """\
        ADMINS = [admin_email]
        """,
        filename="settings.py",
    )


def test_admins_environment_variables():
    check_transformed(
        """\
        import os
        ADMINS = [(os.environ["ADMIN_NAME"], os.environ["ADMIN_EMAIL"])]
        """,
        """\
        import os
        ADMINS = [os.environ["ADMIN_EMAIL"]]
        """,
        filename="settings.py",
    )


def test_managers_success():
    check_transformed(
        """\
        MANAGERS = [('Manager', 'manager@example.com')]
        """,
        """\
        MANAGERS = ['manager@example.com']
        """,
        filename="settings.py",
    )


def test_both():
    check_transformed(
        """\
        ADMINS = [('Admin', 'admin@example.com')]
        MANAGERS = [('Manager', 'manager@example.com')]
        """,
        """\
        ADMINS = ['admin@example.com']
        MANAGERS = ['manager@example.com']
        """,
        filename="settings.py",
    )


def test_both_class_based():
    check_transformed(
        """\
        class Settings:
            ADMINS = [('Admin', 'admin@example.com')]
            MANAGERS = [('Manager', 'manager@example.com')]
        """,
        """\
        class Settings:
            ADMINS = ['admin@example.com']
            MANAGERS = ['manager@example.com']
        """,
        filename="settings.py",
    )
