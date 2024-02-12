from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(3, 2))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_not_command_file():
    check_noop(
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            requires_system_checks = False
        """,
    )


def test_no_assignment():
    check_noop(
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            pass
        """,
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
        filename="myapp/management/commands/do_thing.py",
    )


def test_already_empty_list():
    check_noop(
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            requires_system_checks = []
        """,
        filename="myapp/management/commands/do_thing.py",
    )


def test_already_all():
    check_noop(
        """\
        from django.core.management.base import BaseCommand

        class Command(BaseCommand):
            requires_system_checks = "__all__"
        """,
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
        filename="myapp/management/commands/do_thing.py",
    )
