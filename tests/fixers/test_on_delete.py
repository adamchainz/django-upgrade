import pytest

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(1, 9))


@pytest.mark.parametrize("field_class", ["ForeignKey", "OneToOneField"])
def test_argument_already_set(field_class):
    check_noop(
        f"""\
        from django.db import models
        models.{field_class}("auth.User", on_delete=models.SET_NULL)
        """,
        settings,
    )


@pytest.mark.parametrize("field_class", ["ForeignKey", "OneToOneField"])
def test_field_class_imported(field_class):
    check_noop(
        f"""\
        from django.db.models import {field_class}
        {field_class}("auth.User")
        """,
        settings,
    )


def test_foreignkey_with_args():
    check_transformed(
        """\
        from django.db import models
        models.ForeignKey("auth.User")
        """,
        """\
        from django.db import models
        models.ForeignKey("auth.User", on_delete=models.CASCADE)
        """,
        settings,
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
        settings,
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
        settings,
    )


def test_foreignkey_with_kwargs():
    check_transformed(
        """\
        from django.db import models

        models.ForeignKey(to="auth.User", null=True)
        """,
        """\
        from django.db import models

        models.ForeignKey(to="auth.User", null=True, on_delete=models.CASCADE)
        """,
        settings,
    )


def test_foreignkey_with_kwargs_ending_comma():
    check_transformed(
        """\
        from django.db import models

        models.ForeignKey(to="auth.User", null=True,)
        """,
        """\
        from django.db import models

        models.ForeignKey(to="auth.User", null=True, on_delete=models.CASCADE)
        """,
        settings,
    )


def test_one_to_one_with_args():
    check_transformed(
        """\
        from django.db import models

        models.OneToOneField("auth.User")
        """,
        """\
        from django.db import models

        models.OneToOneField("auth.User", on_delete=models.CASCADE)
        """,
        settings,
    )


def test_one_to_one_with_kwargs():
    check_transformed(
        """\
        from django.db import models

        models.OneToOneField(to="auth.User")
        """,
        """\
        from django.db import models

        models.OneToOneField(to="auth.User", on_delete=models.CASCADE)
        """,
        settings,
    )
