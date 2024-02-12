from __future__ import annotations

from functools import partial

import pytest

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(1, 9))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


@pytest.mark.parametrize("field_class", ["ForeignKey", "OneToOneField"])
def test_argument_already_set(field_class: str) -> None:
    check_noop(
        f"""\
        from django.db import models
        models.{field_class}("auth.User", on_delete=models.SET_NULL)
        """,
    )


@pytest.mark.parametrize("field_class", ["ForeignKey", "OneToOneField"])
def test_argument_already_set_other_import_style(field_class: str) -> None:
    check_noop(
        f"""\
        from django.db.models import {field_class}
        {field_class}("auth.User", on_delete=models.SET_NULL)
        """,
    )


def test_foreign_key_with_two_args():
    check_noop(
        """\
        from django.db import models
        models.ForeignKey("auth.User", models.SET_NULL)
        """,
    )


def test_foreign_key_unused() -> None:
    check_noop(
        """\
        from django.db.models import IntegerField
        IntegerField()
        """,
    )


@pytest.mark.parametrize("field_class", ["ForeignKey", "OneToOneField"])
def test_field_class_imported(field_class: str) -> None:
    check_transformed(
        f"""\
        from django.db.models import {field_class}
        {field_class}("auth.User")
        """,
        f"""\
        from django.db.models import CASCADE
        from django.db.models import {field_class}
        {field_class}("auth.User", on_delete=CASCADE)
        """,
    )


def test_both_field_classes_imported() -> None:
    check_transformed(
        """\
        from django.db.models import ForeignKey
        from django.db.models import OneToOneField
        ForeignKey("auth.User")
        OneToOneField("auth.User")
        """,
        """\
        from django.db.models import ForeignKey
        from django.db.models import CASCADE
        from django.db.models import OneToOneField
        ForeignKey("auth.User", on_delete=CASCADE)
        OneToOneField("auth.User", on_delete=CASCADE)
        """,
    )


@pytest.mark.parametrize("field_class", ["ForeignKey", "OneToOneField"])
def test_field_class_with_args(field_class):
    check_transformed(
        f"""\
        from django.db import models
        models.{field_class}("auth.User")
        """,
        f"""\
        from django.db import models
        models.{field_class}("auth.User", on_delete=models.CASCADE)
        """,
    )


def test_foreignkey_with_args_ending_comma():
    check_transformed(
        """\
        from django.db import models
        models.ForeignKey("auth.User",)
        """,
        """\
        from django.db import models
        models.ForeignKey("auth.User", on_delete=models.CASCADE)
        """,
    )


def test_foreignkey_with_args_and_kwargs():
    check_transformed(
        """\
        from django.db import models
        models.ForeignKey("auth.User", blank=True, null=True)
        """,
        """\
        from django.db import models
        models.ForeignKey("auth.User", on_delete=models.CASCADE, blank=True, null=True)
        """,
    )


def test_foreignkey_without_args():
    check_transformed(
        """\
        from django.db import models
        models.ForeignKey()
        """,
        """\
        from django.db import models
        models.ForeignKey(on_delete=models.CASCADE)
        """,
    )


def test_foreignkey_with_kwargs():
    check_transformed(
        """\
        from django.db import models

        models.ForeignKey(to="auth.User", null=True)
        """,
        """\
        from django.db import models

        models.ForeignKey(on_delete=models.CASCADE, to="auth.User", null=True)
        """,
    )


def test_foreignkey_with_kwargs_ending_comma():
    check_transformed(
        """\
        from django.db import models

        models.ForeignKey(to="auth.User", null=True,)
        """,
        """\
        from django.db import models

        models.ForeignKey(on_delete=models.CASCADE, to="auth.User", null=True,)
        """,
    )


def test_one_to_one_with_arg_whitespace():
    check_transformed(
        """\
        from django.db import models

        models.OneToOneField(
            "auth.User"
        )
        """,
        """\
        from django.db import models

        models.OneToOneField(
            "auth.User"
        , on_delete=models.CASCADE)
        """,
    )


def test_multiline_foreign_key_def():
    check_transformed(
        """\
        from django.db import models

        models.ForeignKey(
            "auth.User",
            verbose_name="User"
        )
        """,
        """\
        from django.db import models

        models.ForeignKey(
            "auth.User", on_delete=models.CASCADE,
            verbose_name="User"
        )
        """,
    )


def test_one_to_one_with_kwargs():
    check_transformed(
        """\
        from django.db import models

        models.OneToOneField(to="auth.User")
        """,
        """\
        from django.db import models

        models.OneToOneField(on_delete=models.CASCADE, to="auth.User")
        """,
    )


def test_mixed_imports():
    check_transformed(
        """\
        from django.db import models
        from django.db.models import ForeignKey

        models.OneToOneField(to="auth.User")
        ForeignKey(to="auth.User", null=True, blank=True)
        """,
        """\
        from django.db import models
        from django.db.models import CASCADE
        from django.db.models import ForeignKey

        models.OneToOneField(on_delete=models.CASCADE, to="auth.User")
        ForeignKey(on_delete=CASCADE, to="auth.User", null=True, blank=True)
        """,
    )
