from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(6, 1))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_unrelated_import():
    check_noop(
        """\
        from example import savepoint
        """,
    )


def test_already_new_name():
    check_noop(
        """\
        from django.db.transaction import savepoint_create
        """,
    )


def test_old_target_version():
    tools.check_noop(
        """\
        from django.db.transaction import savepoint
        """,
        settings=Settings(target_version=(6, 0)),
    )


def test_attribute_access_unrelated_module():
    check_noop(
        """\
        from example import transaction

        transaction.savepoint("name")
        """,
    )


def test_import_renamed():
    check_transformed(
        """\
        from django.db.transaction import savepoint

        savepoint("name")
        """,
        """\
        from django.db.transaction import savepoint_create

        savepoint_create("name")
        """,
    )


def test_import_renamed_aliased():
    check_transformed(
        """\
        from django.db.transaction import savepoint as sp
        """,
        """\
        from django.db.transaction import savepoint_create as sp
        """,
    )


def test_import_with_other_names():
    check_transformed(
        """\
        from django.db.transaction import atomic, savepoint
        """,
        """\
        from django.db.transaction import atomic, savepoint_create
        """,
    )


def test_attribute_access():
    check_transformed(
        """\
        from django.db import transaction

        transaction.savepoint("name")
        """,
        """\
        from django.db import transaction

        transaction.savepoint_create("name")
        """,
    )
