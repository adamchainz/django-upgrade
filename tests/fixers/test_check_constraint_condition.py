from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(5, 1))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_name_no_import():
    check_noop(
        """\
        CheckConstraint(check=Q(id=1))
        """,
    )


def test_attr_multilevel():
    check_noop(
        """\
        from django import db

        db.models.CheckConstraint(check=db.models.Q(id=1))
        """
    )


def test_attr_not_models():
    check_noop(
        """\
        from django.db import shmodels

        shmodels.CheckConstraint(check=shmodels.Q(id=1))
        """
    )


def test_attr_no_import():
    check_noop(
        """\
        models.CheckConstraint(check=models.Q(id=1))
        """
    )


def test_no_check_kwarg():
    check_noop(
        """\
        from django.db.models import CheckConstraint

        CheckConstraint(
            name="monomodel_id",
        )
        """,
    )


def test_condition_present():
    check_noop(
        """\
        from django.db.models import CheckConstraint

        CheckConstraint(
            check=Q(id=1),
            condition=Q(id=1),
        )
        """,
    )


def test_success_name():
    check_transformed(
        """\
        from django.db.models import CheckConstraint

        CheckConstraint(check=Q(id=1))
        """,
        """\
        from django.db.models import CheckConstraint

        CheckConstraint(condition=Q(id=1))
        """,
    )


def test_success_name_gis():
    check_transformed(
        """\
        from django.contrib.gis.db.models import CheckConstraint

        CheckConstraint(check=Q(id=1))
        """,
        """\
        from django.contrib.gis.db.models import CheckConstraint

        CheckConstraint(condition=Q(id=1))
        """,
    )


def test_success_attr():
    check_transformed(
        """\
        from django.db import models

        models.CheckConstraint(check=models.Q(id=1))
        """,
        """\
        from django.db import models

        models.CheckConstraint(condition=models.Q(id=1))
        """,
    )


def test_success_attr_gis():
    check_transformed(
        """\
        from django.contrib.gis.db import models

        models.CheckConstraint(check=models.Q(id=1))
        """,
        """\
        from django.contrib.gis.db import models

        models.CheckConstraint(condition=models.Q(id=1))
        """,
    )


def test_success_other_args():
    check_transformed(
        """\
        from django.db.models import CheckConstraint

        CheckConstraint(
            name="monomodel_id",
            check=Q(id=1),
        )
        """,
        """\
        from django.db.models import CheckConstraint

        CheckConstraint(
            name="monomodel_id",
            condition=Q(id=1),
        )
        """,
    )
