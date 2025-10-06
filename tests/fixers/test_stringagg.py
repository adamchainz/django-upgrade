from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(6, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_unmatched_import():
    check_noop(
        """\
        from example import StringAgg
        """,
    )


def test_no_stringagg_import():
    check_noop(
        """\
        from django.contrib.postgres.aggregates import ArrayAgg
        """,
    )


def test_unsafe_delimiter_variable():
    check_noop(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        delimiter_var = ", "
        StringAgg("name", delimiter=delimiter_var)
        """,
    )


def test_unsafe_delimiter_expression():
    check_noop(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", delimiter=get_delimiter())
        """,
    )


def test_zero_arguments():
    check_noop(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg()
        """,
    )


def test_one_argument():
    check_noop(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name")
        """,
    )


def test_mixed_safe_and_unsafe_delimiters():
    check_noop(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", ", ")
        StringAgg("title", some_var)
        """,
    )


def test_import_aliased():
    check_noop(
        """\
        from django.contrib.postgres.aggregates import StringAgg as PgStringAgg

        PgStringAgg("name", delimiter=", ")
        """,
    )


def test_just_import():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg
        """,
        """\
        from django.db.models import StringAgg
        """,
    )


def test_existing_delimiter():
    check_transformed(
        """\
        from django.db.models import Value
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", delimiter=Value(", "))
        """,
        """\
        from django.db.models import Value
        from django.db.models import StringAgg

        StringAgg("name", delimiter=Value(", "))
        """,
    )


def test_success_models_value_imported():
    check_transformed(
        """\
        from django.db.models import Model, Value
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", delimiter=", ")
        """,
        """\
        from django.db.models import Model, Value
        from django.db.models import StringAgg

        StringAgg("name", delimiter=Value(", "))
        """,
    )


def test_safe_value_wrapped_delimiter():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg
        from django.db.models import Value

        StringAgg("name", delimiter=Value(", "))
        """,
        """\
        from django.db.models import StringAgg
        from django.db.models import Value

        StringAgg("name", delimiter=Value(", "))
        """,
    )


def test_multiple_safe_calls_mixed_delimiters():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg
        from django.db.models import Value

        StringAgg("name", delimiter=", ")
        StringAgg("title", delimiter=Value(" | "))
        StringAgg("description", ", ")
        """,
        """\
        from django.db.models import StringAgg
        from django.db.models import Value

        StringAgg("name", delimiter=Value(", "))
        StringAgg("title", delimiter=Value(" | "))
        StringAgg("description", Value(", "))
        """,
    )


def test_general_import():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates.general import StringAgg
        from django.db.models import Value

        StringAgg("name", delimiter=", ")
        """,
        """\
        from django.db.models import StringAgg
        from django.db.models import Value

        StringAgg("name", delimiter=Value(", "))
        """,
    )


def test_multiple_imports_with_stringagg():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import ArrayAgg, StringAgg, JSONBAgg
        from django.db.models import Value

        StringAgg("name", delimiter=", ")
        """,
        """\
        from django.db.models import StringAgg
        from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
        from django.db.models import Value

        StringAgg("name", delimiter=Value(", "))
        """,
    )


def test_existing_db_models_import():
    check_transformed(
        """\
        from django.db import models
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", delimiter=", ")
        """,
        """\
        from django.db import models
        from django.db.models import StringAgg

        StringAgg("name", delimiter=models.Value(", "))
        """,
    )


def test_single_quoted_string():
    check_transformed(
        """\
        from django.db.models import Value
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", delimiter=', ')
        """,
        """\
        from django.db.models import Value
        from django.db.models import StringAgg

        StringAgg("name", delimiter=Value(', '))
        """,
    )


def test_with_other_arguments():
    check_transformed(
        """\
        from django.db import models
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", delimiter=", ", distinct=True, order_by=["id"])
        """,
        """\
        from django.db import models
        from django.db.models import StringAgg

        StringAgg("name", delimiter=models.Value(", "), distinct=True, order_by=["id"])
        """,
    )


def test_multiline_call():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg
        from django.db import models

        StringAgg(
            "name",
            delimiter=", ",
            distinct=True,
        )
        """,
        """\
        from django.db.models import StringAgg
        from django.db import models

        StringAgg(
            "name",
            delimiter=models.Value(", "),
            distinct=True,
        )
        """,
    )


def test_existing_value_import():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg
        from django.db.models import Value

        StringAgg("name", delimiter=", ")
        """,
        """\
        from django.db.models import StringAgg
        from django.db.models import Value

        StringAgg("name", delimiter=Value(", "))
        """,
    )
