from django_upgrade._data import Settings
from tests.plugins.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 0))


def test_no_deprecated_alias():
    check_noop(
        """\
        from django.core.paginator import Paginator
        """,
        settings,
    )


def test_unrecognized_import_format():
    check_noop(
        """\
        from django.core import paginator

        paginator.QuerySetPaginator
        """,
        settings,
    )


def test_success():
    check_transformed(
        """\
        from django.core.paginator import QuerySetPaginator

        QuerySetPaginator(...)
        """,
        """\
        from django.core.paginator import Paginator

        Paginator(...)
        """,
        settings,
    )
