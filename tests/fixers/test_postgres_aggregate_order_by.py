from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(5, 2))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_name_no_import():
    check_noop(
        """\
        ArrayAgg('field', ordering=('name',))
        """,
    )


def test_attr_multilevel():
    check_noop(
        """\
        from django.contrib import postgres

        postgres.aggregates.ArrayAgg('field', ordering=('name',))
        """
    )


def test_attr_not_aggregates():
    check_noop(
        """\
        from django.contrib.postgres import shmaggregates

        shmaggregates.ArrayAgg('field', ordering=('name',))
        """
    )


def test_attr_no_import():
    check_noop(
        """\
        aggregates.ArrayAgg('field', ordering=('name',))
        """
    )


def test_no_ordering_kwarg():
    check_noop(
        """\
        from django.contrib.postgres.aggregates import ArrayAgg

        ArrayAgg('field')
        """,
    )


def test_order_by_present():
    check_noop(
        """\
        from django.contrib.postgres.aggregates import ArrayAgg

        ArrayAgg('field', ordering=('name',), order_by=('id',))
        """,
    )


def test_success_name():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import ArrayAgg

        ArrayAgg('field', ordering=('name',))
        """,
        """\
        from django.contrib.postgres.aggregates import ArrayAgg

        ArrayAgg('field', order_by=('name',))
        """,
    )


def test_success_name_general():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates.general import ArrayAgg

        ArrayAgg('field', ordering=('name',))
        """,
        """\
        from django.contrib.postgres.aggregates.general import ArrayAgg

        ArrayAgg('field', order_by=('name',))
        """,
    )


def test_success_attr():
    check_transformed(
        """\
        from django.contrib.postgres import aggregates

        aggregates.ArrayAgg('field', ordering=('name',))
        """,
        """\
        from django.contrib.postgres import aggregates

        aggregates.ArrayAgg('field', order_by=('name',))
        """,
    )


def test_success_attr_general():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import general

        general.ArrayAgg('field', ordering=('name',))
        """,
        """\
        from django.contrib.postgres.aggregates import general

        general.ArrayAgg('field', order_by=('name',))
        """,
    )


def test_success_jsonbagg():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import JSONBAgg

        JSONBAgg('field', ordering=('name',))
        """,
        """\
        from django.contrib.postgres.aggregates import JSONBAgg

        JSONBAgg('field', order_by=('name',))
        """,
    )


def test_success_stringagg():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg('field', delimiter=',', ordering=('name',))
        """,
        """\
        from django.contrib.postgres.aggregates import StringAgg

        StringAgg('field', delimiter=',', order_by=('name',))
        """,
    )


def test_success_other_args():
    check_transformed(
        """\
        from django.contrib.postgres.aggregates import ArrayAgg

        ArrayAgg(
            'field',
            distinct=True,
            ordering=('name',),
        )
        """,
        """\
        from django.contrib.postgres.aggregates import ArrayAgg

        ArrayAgg(
            'field',
            distinct=True,
            order_by=('name',),
        )
        """,
    )
