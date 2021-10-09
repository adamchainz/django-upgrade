from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(1, 11))


def test_unmatched_import():
    check_noop(
        """\
        from example import EmptyResultSet
        EmptyResultSet()
        """,
        settings,
    )


def test_unmatched_import_name():
    check_noop(
        """\
        from django.db.models.fields import something
        """,
        settings,
    )


def test_unrecognized_import_format():
    check_noop(
        """\
        from django.db.models import query

        query.EmptyResultSet()
        """,
        settings,
    )


def test_exception_class_imported():
    check_transformed(
        """\
        from django.db.models.query import EmptyResultSet

        EmptyResultSet()
        """,
        """\
        from django.core.exceptions import EmptyResultSet

        EmptyResultSet()
        """,
        settings,
    )


def test_exception_class_imported_as_other_name():
    check_transformed(
        """\
        from django.db.models.query import EmptyResultSet as EmptyResultSetExc

        EmptyResultSetExc()
        """,
        """\
        from django.core.exceptions import EmptyResultSet as EmptyResultSetExc

        EmptyResultSetExc()
        """,
        settings,
    )
