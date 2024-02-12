from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(2, 2))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_no_deprecated_alias():
    check_noop(
        """\
        from django.contrib.postgres.fields import ArrayField

        ArrayField("My array field")
        """,
    )


def test_unmatched_import():
    check_noop(
        """\
        from example import FloatRangeField

        FloatRangeField("My range of numbers")
        """,
    )


def test_direct_import():
    check_transformed(
        """\
        from django.db.models import Model
        from django.contrib.postgres.fields import FloatRangeField

        class MyModel(Model):
            my_field = FloatRangeField("My range of numbers")
        """,
        """\
        from django.db.models import Model
        from django.contrib.postgres.fields import DecimalRangeField

        class MyModel(Model):
            my_field = DecimalRangeField("My range of numbers")
        """,
    )


def test_success_alias():
    check_transformed(
        """\
        from django.contrib.postgres.forms.ranges import FloatRangeField as FRF

        FRF("yada")
        """,
        """\
        from django.contrib.postgres.forms.ranges import DecimalRangeField as FRF

        FRF("yada")
        """,
    )
