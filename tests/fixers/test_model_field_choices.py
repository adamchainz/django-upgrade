from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(5, 0))


def test_untransformed_in_migration_file():
    # No `.choices` in migrations anyway, every option are listed automatically.
    check_noop(
        """\
        from django.db.models import CharField
        CharField(choices=[(1, 2), (3, 4)])
        """,
        settings,
        filename="example/core/migrations/0001_initial.py",
    )


def test_untransformed_wrong_argument():
    check_noop(
        """\
        from django.db.models import CharField
        CharField(default=Card.choices)
        """,
        settings,
        filename="models/blog.py",
    )


def test_transform_full_import():
    check_transformed(
        """\
        from django.db.models import CharField
        CharField(choices=Card.choices)
        """,
        """\
        from django.db.models import CharField
        CharField(choices=Card)
        """,
        settings,
        filename="models/blog.py",
    )


def test_transform_module_import():
    check_transformed(
        """\
        from django.db import models
        field = models.BooleanField(choices=Card.choices)
        """,
        """\
        from django.db import models
        field = models.BooleanField(choices=Card)
        """,
        settings,
        filename="models/blog.py",
    )


def test_transform_gis_models_import():
    check_transformed(
        """\
        from django.contrib.postgres.fields import ArrayField
        field = ArrayField(choices=Card.choices)
        """,
        """\
        from django.contrib.postgres.fields import ArrayField
        field = ArrayField(choices=Card)
        """,
        settings,
        filename="models/blog.py",
    )


def test_transform_with_kwarg_ending_comma():
    check_transformed(
        """\
        from django.db import models
        field = models.IntegerField(choices=Card.choices,)
        """,
        """\
        from django.db import models
        field = models.IntegerField(choices=Card,)
        """,
        settings,
        filename="models/blog.py",
    )


def test_transform_with_kwargs_multiline():
    check_transformed(
        """\
        from django.db import models
        field = models.IntegerField(
            choices=Card.choices,
        )
        """,
        """\
        from django.db import models
        field = models.IntegerField(
            choices=Card,
        )
        """,
        settings,
        filename="models/blog.py",
    )


def test_transform_with_weird_syntax():
    check_transformed(
        """\
        from django.db import models
        field = models.IntegerField(
            choices=Card. choices,
        )
        field2 = models.IntegerField(
            choices=Card.
            choices,
        )
        """,
        """\
        from django.db import models
        field = models.IntegerField(
            choices=Card,
        )
        field2 = models.IntegerField(
            choices=Card,
        )
        """,
        settings,
        filename="models/blog.py",
    )


def test_transform_external_package():
    check_transformed(
        """\
        from multiselectfield import MultiSelectField
        field = MultiSelectField(choices=Card.choices)
        """,
        """\
        from multiselectfield import MultiSelectField
        field = MultiSelectField(choices=Card)
        """,
        settings,
        filename="models/blog.py",
    )


def test_transform_other_app_package():
    check_transformed(
        """\
        from my_app import custom_models
        from example import CustomCharField
        field = custom_models.MyField(choices=Card.choices)
        field2 = CharField(choices=Card.choices)
        """,
        """\
        from my_app import custom_models
        from example import CustomCharField
        field = custom_models.MyField(choices=Card)
        field2 = CharField(choices=Card)
        """,
        settings,
        filename="models/blog.py",
    )
