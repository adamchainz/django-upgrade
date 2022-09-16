from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(2, 0))


def test_false():
    check_noop(
        """\
        from django.contrib import admin

        def upper_case_name(obj):
            ...

        upper_case_name.allow_tags = False
        """,
        settings,
    )


def test_not_name():
    check_noop(
        """\
        from django.contrib import admin

        def upper_case_name(obj):
            ...

        upper_case_name.allow_tags = maybe()
        """,
        settings,
    )


def test_no_import():
    check_noop(
        """\
        def upper_case_name(obj):
            ...

        upper_case_name.allow_tags = True
        """,
        settings,
    )


def test_basic():
    check_transformed(
        """\
        from django.contrib import admin

        def upper_case_name(obj):
            ...

        upper_case_name.allow_tags = True
        """,
        """\
        from django.contrib import admin

        def upper_case_name(obj):
            ...

        """,
        settings,
    )


def test_basic_gis():
    check_transformed(
        """\
        from django.contrib.gis import admin

        def upper_case_name(obj):
            ...

        upper_case_name.allow_tags = True
        """,
        """\
        from django.contrib.gis import admin

        def upper_case_name(obj):
            ...

        """,
        settings,
    )
