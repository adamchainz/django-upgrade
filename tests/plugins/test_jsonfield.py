from django_upgrade.data import Settings
from tests.plugins.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 1))


def test_no_deprecated_alias():
    check_noop(
        """\
        from django.contrib.postgres.fields import IntegerRangeField
        """,
        settings,
    )


def test_unrecognized_import_format():
    check_noop(
        """\
        from django.contrib.postgres import fields

        fields.JSONField()
        """,
        settings,
    )


def test_full():
    check_transformed(
        """\
        from django.contrib.postgres.fields import (
            JSONField, KeyTransform,  KeyTextTransform,
        )
        """,
        """\
        from django.db.models import JSONField
        from django.db.models.fields.json import KeyTextTransform, KeyTransform
        """,
        settings,
    )


def test_model_field():
    check_transformed(
        """\
        from django.contrib.postgres.fields import JSONField
        """,
        """\
        from django.db.models import JSONField
        """,
        settings,
    )


def test_model_field_submodule():
    check_transformed(
        """\
        from django.contrib.postgres.fields.jsonb import JSONField
        """,
        """\
        from django.db.models import JSONField
        """,
        settings,
    )


def test_form_field():
    check_transformed(
        """\
        from django.contrib.postgres.forms import JSONField
        """,
        """\
        from django.forms import JSONField
        """,
        settings,
    )


def test_form_field_submodule():
    check_transformed(
        """\
        from django.contrib.postgres.forms.jsonb import JSONField
        """,
        """\
        from django.forms import JSONField
        """,
        settings,
    )


def test_transforms():
    check_transformed(
        """\
        from django.contrib.postgres.fields import KeyTextTransform
        yada = 1
        from django.contrib.postgres.fields.jsonb import KeyTransform
        """,
        """\
        from django.db.models.fields.json import KeyTextTransform
        yada = 1
        from django.db.models.fields.json import KeyTransform
        """,
        settings,
    )
