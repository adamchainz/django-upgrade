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


def test_only_postgres_import_no_calls():
    check_noop(
        """\
        from django.contrib.postgres.aggregates import StringAgg
        """,
    )


def test_unsafe_delimiter_variable():
    # Should not transform because delimiter uses variable
    check_noop(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        delimiter_var = ", "
        StringAgg("name", delimiter=delimiter_var)
        """,
    )


def test_unsafe_delimiter_expression():
    # Should not transform because delimiter uses expression
    check_noop(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", delimiter=get_delimiter())
        """,
    )


def test_mixed_safe_and_unsafe_delimiters():
    # Should not transform because one call has unsafe delimiter
    check_noop(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", delimiter=", ")
        StringAgg("title", delimiter=some_var)
        """,
    )


def test_safe_no_delimiter():
    # Should transform when StringAgg has no delimiter
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name")
        """,
        """\
        from django.db.models import StringAgg

        StringAgg("name")
        """,
    )


def test_safe_string_literal_delimiter():
    # Should transform when all delimiters are string literals
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", delimiter=", ")
        """,
        """\
        from django.db.models import StringAgg, Value

        StringAgg("name", delimiter=Value(", "))
        """,
    )


def test_safe_value_wrapped_delimiter():
    # Should transform when delimiter is already wrapped in Value
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg
        from django.db.models import Value

        StringAgg("name", delimiter=Value(", "))
        """,
        """\
        from django.db.models import StringAgg, Value

        StringAgg("name", delimiter=Value(", "))
        """,
    )


def test_multiple_safe_calls_mixed_delimiters():
    # Should transform when all calls have safe delimiters (mix of string literals and Value)
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg
        from django.db.models import Value

        StringAgg("name", delimiter=", ")
        StringAgg("title", delimiter=Value(" | "))
        StringAgg("description")
        """,
        """\
        from django.db.models import StringAgg, Value

        StringAgg("name", delimiter=Value(", "))
        StringAgg("title", delimiter=Value(" | "))
        StringAgg("description")
        """,
    )


def test_general_import():
    # Should transform imports from .general submodule
    check_transformed(
        """\
        from django.contrib.postgres.aggregates.general import StringAgg

        StringAgg("name", delimiter=", ")
        """,
        """\
        from django.db.models import StringAgg, Value

        StringAgg("name", delimiter=Value(", "))
        """,
    )


def test_multiple_imports_with_stringagg():
    # Should transform only StringAgg import, keeping others
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import ArrayAgg, StringAgg, JSONBAgg

        StringAgg("name", delimiter=", ")
        """,
        """\
        from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
        from django.db.models import StringAgg, Value

        StringAgg("name", delimiter=Value(", "))
        """,
    )


def test_existing_db_models_import():
    # Should add to existing django.db.models import
    check_transformed(
        """\
        from django.db.models import Model
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", delimiter=", ")
        """,
        """\
        from django.db.models import Model, StringAgg, Value

        StringAgg("name", delimiter=Value(", "))
        """,
    )


def test_attr_import_postgres():
    check_transformed(
        """\
        from django.contrib import postgres

        postgres.aggregates.StringAgg("name", delimiter=", ")
        """,
        """\
        from django.contrib import postgres
        from django.db.models import StringAgg, Value

        StringAgg("name", delimiter=Value(", "))
        """,
    )


def test_attr_import_aggregates():
    check_transformed(
        """\
        from django.contrib.postgres import aggregates

        aggregates.StringAgg("name", delimiter=", ")
        """,
        """\
        from django.contrib.postgres import aggregates
        from django.db.models import StringAgg, Value

        StringAgg("name", delimiter=Value(", "))
        """,
    )


def test_attr_import_unsafe_delimiter():
    # Should not transform attribute-style call with unsafe delimiter
    check_noop(
        """\
        from django.contrib.postgres import aggregates

        aggregates.StringAgg("name", delimiter=some_var)
        """,
    )


def test_single_quoted_string():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", delimiter=', ')
        """,
        """\
        from django.db.models import StringAgg, Value

        StringAgg("name", delimiter=Value(', '))
        """,
    )


def test_with_other_arguments():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg("name", delimiter=", ", distinct=True, ordering=["id"])
        """,
        """\
        from django.db.models import StringAgg, Value

        StringAgg("name", delimiter=Value(", "), distinct=True, ordering=["id"])
        """,
    )


def test_multiline_call():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg(
            "name",
            delimiter=", ",
            distinct=True,
        )
        """,
        """\
        from django.db.models import StringAgg, Value

        StringAgg(
            "name",
            delimiter=Value(", "),
            distinct=True,
        )
        """,
    )


def test_stringagg_with_alias():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg as PgStringAgg

        PgStringAgg("name", delimiter=", ")
        """,
        """\
        from django.db.models import StringAgg as PgStringAgg, Value

        PgStringAgg("name", delimiter=Value(", "))
        """,
    )


def test_existing_value_import():
    # Should not duplicate Value import
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg
        from django.db.models import Value

        StringAgg("name", delimiter=", ")
        """,
        """\
        from django.db.models import StringAgg, Value

        StringAgg("name", delimiter=Value(", "))
        """,
    )
