from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(2, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_false():
    check_noop(
        """\
        from django.contrib import admin

        def upper_case_name(obj):
            ...

        upper_case_name.allow_tags = False
        """,
    )


def test_self_attribute_in_method():
    check_noop(
        """\
        from django.contrib import admin


        class LegacyWidget:
            def __init__(self):
                self.allow_tags = True
        """,
    )


def test_in_conditional_block():
    check_noop(
        """\
        from django.contrib import admin

        def upper_case_name(obj):
            ...

        if True:
            upper_case_name.allow_tags = True
        """,
    )


def test_sole_statement_in_class():
    check_noop(
        """\
        from django.contrib import admin


        class MyAdmin:
            upper_case_name.allow_tags = True
        """,
    )


def test_not_name():
    check_noop(
        """\
        from django.contrib import admin

        def upper_case_name(obj):
            ...

        upper_case_name.allow_tags = maybe()
        """,
    )


def test_no_import():
    check_noop(
        """\
        def upper_case_name(obj):
            ...

        upper_case_name.allow_tags = True
        """,
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
    )
