from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 1))


def test_unmatched_import():
    check_noop(
        """\
        from test import ModelMultipleChoiceField
        ModelMultipleChoiceField(error_messages={"list": "Enter values!"})
        """,
        settings,
    )


def test_variable():
    check_noop(
        """\
        from test import ModelMultipleChoiceField

        msg = {"list": "Enter values!"}
        ModelMultipleChoiceField(error_messages=msg)
        """,
        settings,
    )


def test_from_django_forms_import():
    check_transformed(
        """\
        from django.forms import ModelMultipleChoiceField

        ModelMultipleChoiceField(error_messages={"list": "Enter values!"})
        """,
        """\
        from django.forms import ModelMultipleChoiceField

        ModelMultipleChoiceField(error_messages={"invalid_list": "Enter values!"})
        """,
        settings,
    )


def test_from_django_import():
    check_transformed(
        """\
        from django import forms

        forms.ModelMultipleChoiceField(error_messages={"list": "Enter values!"})
        """,
        """\
        from django import forms

        forms.ModelMultipleChoiceField(error_messages={"invalid_list": "Enter values!"})
        """,
        settings,
    )


def test_mixed_import():
    check_transformed(
        """\
        from django import forms
        from django.forms import ModelMultipleChoiceField

        ModelMultipleChoiceField(error_messages={"invalid_list": "Enter values!"})
        forms.ModelMultipleChoiceField(error_messages={"list": "Enter values!"})
        """,
        """\
        from django import forms
        from django.forms import ModelMultipleChoiceField

        ModelMultipleChoiceField(error_messages={"invalid_list": "Enter values!"})
        forms.ModelMultipleChoiceField(error_messages={"invalid_list": "Enter values!"})
        """,
        settings,
    )


def test_with_queryset_arg():
    check_transformed(
        """\
        from django.forms import ModelMultipleChoiceField
        from django.contrib.auth.models import User

        ModelMultipleChoiceField(
            User.objects.all(),
            error_messages={"list": "Enter values!"}
        )
        """,
        """\
        from django.forms import ModelMultipleChoiceField
        from django.contrib.auth.models import User

        ModelMultipleChoiceField(
            User.objects.all(),
            error_messages={"invalid_list": "Enter values!"}
        )
        """,
        settings,
    )


def test_with_queryset_kwarg():
    check_transformed(
        """\
        from django.forms import ModelMultipleChoiceField
        from django.contrib.auth.models import User

        ModelMultipleChoiceField(
            queryset=User.objects.all(),
            error_messages={"list": "Enter values!"}
        )
        """,
        """\
        from django.forms import ModelMultipleChoiceField
        from django.contrib.auth.models import User

        ModelMultipleChoiceField(
            queryset=User.objects.all(),
            error_messages={"invalid_list": "Enter values!"}
        )
        """,
        settings,
    )


def test_starargs():
    check_transformed(
        """\
        from django.forms import ModelMultipleChoiceField
        msg = {"required": "This is required."}

        ModelMultipleChoiceField(
            error_messages={**msg, "list": "Enter values!"}
        )
        """,
        """\
        from django.forms import ModelMultipleChoiceField
        msg = {"required": "This is required."}

        ModelMultipleChoiceField(
            error_messages={**msg, "invalid_list": "Enter values!"}
        )
        """,
        settings,
    )
