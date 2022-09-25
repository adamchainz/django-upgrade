from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 1))


def test_unmatched_import():
    check_noop(
        """\
        from example import NullBooleanField
        NullBooleanField()
        """,
        settings,
    )


def test_untransformed_in_migration_file():
    check_noop(
        """\
        from django.db.models import NullBooleanField
        field = NullBooleanField()
        """,
        settings,
        filename="example/core/migrations/0001_initial.py",
    )


def test_transform_in_class():
    check_transformed(
        """\
        from django.db.models import Model, NullBooleanField

        class Book(Model):
            valuable = NullBooleanField("Valuable")
        """,
        """\
        from django.db.models import Model, BooleanField

        class Book(Model):
            valuable = BooleanField("Valuable", null=True)
        """,
        settings,
    )


def test_transform():
    check_transformed(
        """\
        from django.db.models import NullBooleanField
        field = NullBooleanField()
        """,
        """\
        from django.db.models import BooleanField
        field = BooleanField(null=True)
        """,
        settings,
    )


def test_transform_import_exists():
    check_transformed(
        """\
        from django.db.models import BooleanField, NullBooleanField
        field = NullBooleanField()
        """,
        """\
        from django.db.models import BooleanField
        field = BooleanField(null=True)
        """,
        settings,
    )


def test_transform_import_exists_second():
    check_transformed(
        """\
        from django.db.models import NullBooleanField, BooleanField
        field = NullBooleanField()
        """,
        """\
        from django.db.models import BooleanField
        field = BooleanField(null=True)
        """,
        settings,
    )


def test_transform_module_import():
    check_transformed(
        """\
        from django.db import models
        field = models.NullBooleanField()
        """,
        """\
        from django.db import models
        field = models.BooleanField(null=True)
        """,
        settings,
    )


def test_transform_with_pos_arg():
    check_transformed(
        """\
        from django.db.models import NullBooleanField
        field = NullBooleanField("My Field")
        """,
        """\
        from django.db.models import BooleanField
        field = BooleanField("My Field", null=True)
        """,
        settings,
    )


def test_transform_with_kwarg():
    check_transformed(
        """\
        from django.db.models import NullBooleanField
        field = NullBooleanField(verbose_name="My Field")
        """,
        """\
        from django.db.models import BooleanField
        field = BooleanField(verbose_name="My Field", null=True)
        """,
        settings,
    )


def test_transform_with_kwarg_ending_comma():
    check_transformed(
        """\
        from django.db.models import NullBooleanField
        field = NullBooleanField(verbose_name="My Field",)
        """,
        """\
        from django.db.models import BooleanField
        field = BooleanField(verbose_name="My Field", null=True)
        """,
        settings,
    )


def test_transform_with_kwargs():
    check_transformed(
        """\
        from django.db.models import NullBooleanField
        field = NullBooleanField(verbose_name="My Field", validators=[])
        """,
        """\
        from django.db.models import BooleanField
        field = BooleanField(verbose_name="My Field", validators=[], null=True)
        """,
        settings,
    )


def test_transform_with_kwargs_multiline():
    check_transformed(
        """\
        from django.db.models import NullBooleanField
        field = NullBooleanField(
            verbose_name="My Field",
        )
        """,
        """\
        from django.db.models import BooleanField
        field = BooleanField(
            verbose_name="My Field",
         null=True)
        """,
        settings,
    )


def test_transform_with_star_pos_arg():
    check_transformed(
        """\
        from django.db.models import NullBooleanField
        field = NullBooleanField(*names)
        """,
        """\
        from django.db.models import BooleanField
        field = BooleanField(*names, null=True)
        """,
        settings,
    )


def test_transform_with_star_kwargs():
    check_transformed(
        """\
        from django.db.models import NullBooleanField
        field = NullBooleanField(**kwargs)
        """,
        """\
        from django.db.models import BooleanField
        field = BooleanField(**kwargs, null=True)
        """,
        settings,
    )


def test_transform_with_null_is_true_kwarg_relative_import():
    check_transformed(
        """\
        from django.db import models
        models.NullBooleanField(null=True)
        """,
        """\
        from django.db import models
        models.BooleanField(null=True)
        """,
        settings,
    )


def test_transform_with_null_is_true_kwarg_absolute_import_renamed():
    check_transformed(
        """\
        from django.db.models import NullBooleanField
        NullBooleanField(null=True)
        """,
        """\
        from django.db.models import BooleanField
        BooleanField(null=True)
        """,
        settings,
    )


def test_transform_with_null_is_true_kwarg_absolute_import_removed():
    check_transformed(
        """\
        from django.db.models import BooleanField, NullBooleanField
        NullBooleanField(null=True)
        """,
        """\
        from django.db.models import BooleanField
        BooleanField(null=True)
        """,
        settings,
    )


def test_transform_with_null_is_function():
    check_transformed(
        """\
        from django.db.models import NullBooleanField
        NullBooleanField(null=f())
        """,
        """\
        from django.db.models import BooleanField
        BooleanField(null=f())
        """,
        settings,
    )
