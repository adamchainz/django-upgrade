from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(3, 2))


def test_not_command_file():
    check_noop(
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            requires_system_checks = False
        """,
        settings,
    )


def test_no_assignment():
    check_noop(
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            pass
        """,
        settings,
        filename="myapp/management/commands/do_thing.py",
    )


def test_not_in_classdef():
    check_noop(
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            pass
        requires_system_checks = False
        """,
        settings,
        filename="myapp/management/commands/do_thing.py",
    )


def test_already_empty_list():
    check_noop(
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            requires_system_checks = []
        """,
        settings,
        filename="myapp/management/commands/do_thing.py",
    )


def test_already_all():
    check_noop(
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            requires_system_checks = "__all__"
        """,
        settings,
        filename="myapp/management/commands/do_thing.py",
    )


def test_false():
    check_transformed(
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            requires_system_checks = False
        """,
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            requires_system_checks = []
        """,
        settings,
        filename="myapp/management/commands/do_thing.py",
    )


def test_true():
    check_transformed(
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            requires_system_checks = True
        """,
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            requires_system_checks = "__all__"
        """,
        settings,
        filename="myapp/management/commands/do_thing.py",
    )
