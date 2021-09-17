from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(1, 11))


def test_unmatched_import():
    check_noop(
        """\
        from example import EmptyResultSet
        """,
        settings,
    )


def test_unrecognized_import_format():
    check_noop(
        """\
        from django.db.models import fields

        fields.FieldDoesNotExist
        """,
        settings,
    )


def test_exception_class_imported():
    check_transformed(
        """\
        from django.db.models.fields import FieldDoesNotExist

        EmptyResultSet
        """,
        """\
        from django.core.exceptions import FieldDoesNotExist

        EmptyResultSet
        """,
        settings,
    )


def test_exception_class_imported_as_other_name():
    check_transformed(
        """\
        from django.db.models.fields import FieldDoesNotExist as FDNE

        FDNE
        """,
        """\
        from django.core.exceptions import FieldDoesNotExist as FDNE

        FDNE
        """,
        settings,
    )
