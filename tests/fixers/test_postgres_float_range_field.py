from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(2, 2))


def test_no_deprecated_alias():
    check_noop(
        """\
        from django.contrib.postgres.fields import ArrayField

        ArrayField("My array field")
        """,
        settings,
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
        settings,
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
        settings,
    )
