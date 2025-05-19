from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(5, 0))


def test_untransformed_in_migration_file():
    # No `.choices` in migrations, every option gets listed.
    check_noop(
        """\
        from django.db import models
        models.CharField(choices=[(1, 2), (3, 4)])
        """,
        settings,
        filename="example/core/migrations/0001_initial.py",
    )


def test_untransformed_wrong_argument():
    check_noop(
        """\
        from django.db import models
        models.CharField(default=Card.choices)
        """,
        settings,
        filename="models.py",
    )


def test_untransformed_not_defined_in_same_file():
    check_noop(
        """\
        from django.db import models
        from my_enums import Card
        models.CharField(choices=Card.choices)
        """,
        settings,
        filename="models.py",
    )


def test_untransformed_defined_after_usage():
    check_noop(
        """\
        from django.db import models

        class MyModel(models.Model):
            field = CharField(choices=Card.choices)

        class Card(models.IntegerChoices):
            HEARTS = 1
        """,
        settings,
        filename="models.py",
    )


def test_untransformed_not_choice_type():
    check_noop(
        """\
        from django.db import models

        class Suit:
            choices = [(1, 'Hearts')]

        class Card(models.Model):
            suit = CharField(choices=Suit.choices)
        """,
        settings,
        filename="models.py",
    )


def test_transform_defined_before_usage():
    check_transformed(
        """\
        from django.db import models

        class Suit(models.IntegerChoices):
            HEARTS = 1

        class Card(models.Model):
            suit = CharField(choices=Suit.choices)
        """,
        """\
        from django.db import models

        class Suit(models.IntegerChoices):
            HEARTS = 1

        class Card(models.Model):
            suit = CharField(choices=Suit)
        """,
        settings,
        filename="models.py",
    )


def test_transform_full_import():
    check_transformed(
        """\
        from django.db import models

        class Suit(models.IntegerChoices):
            HEARTS = 1

        models.CharField(choices=Suit.choices)
        """,
        """\
        from django.db import models

        class Suit(models.IntegerChoices):
            HEARTS = 1

        models.CharField(choices=Suit)
        """,
        settings,
        filename="models.py",
    )


def test_transform_module_import():
    check_transformed(
        """\
        from django.db import models

        class Suit(models.IntegerChoices):
            HEARTS = 1

        models.BooleanField(choices=Suit.choices)
        """,
        """\
        from django.db import models

        class Suit(models.IntegerChoices):
            HEARTS = 1

        models.BooleanField(choices=Suit)
        """,
        settings,
        filename="models.py",
    )


def test_transform_direct_import():
    check_transformed(
        """\
        from django.db.models import IntegerChoices, CharField

        class Suit(IntegerChoices):
            HEARTS = 1

        CharField(choices=Suit.choices)
        """,
        """\
        from django.db.models import IntegerChoices, CharField

        class Suit(IntegerChoices):
            HEARTS = 1

        CharField(choices=Suit)
        """,
        settings,
        filename="models.py",
    )


def test_transform_with_text_choices():
    check_transformed(
        """\
        from django.db import models

        class Suit(models.TextChoices):
            HEARTS = 'H', 'Hearts'

        models.CharField(choices=Suit.choices)
        """,
        """\
        from django.db import models

        class Suit(models.TextChoices):
            HEARTS = 'H', 'Hearts'

        models.CharField(choices=Suit)
        """,
        settings,
        filename="models.py",
    )


def test_transform_with_choices_base():
    check_transformed(
        """\
        from django.db import models

        class Suit(models.Choices):
            HEARTS = 'H', 'Hearts'

        models.CharField(choices=Suit.choices)
        """,
        """\
        from django.db import models

        class Suit(models.Choices):
            HEARTS = 'H', 'Hearts'

        models.CharField(choices=Suit)
        """,
        settings,
        filename="models.py",
    )


def test_transform_from_enums_module():
    check_transformed(
        """\
        from django.db import models
        from django.db.models.enums import IntegerChoices

        class Suit(IntegerChoices):
            HEARTS = 1

        models.CharField(choices=Suit.choices)
        """,
        """\
        from django.db import models
        from django.db.models.enums import IntegerChoices

        class Suit(IntegerChoices):
            HEARTS = 1

        models.CharField(choices=Suit)
        """,
        settings,
        filename="models.py",
    )


def test_transform_choices_module_reference_fails():
    # This shouldn't transform because enums.Card is not defined in this file
    check_noop(
        """\
        from django.db import models
        import enums
        field = models.IntegerField(choices=enums.Card.choices)
        """,
        settings,
        filename="models.py",
    )


def test_transform_with_kwarg_ending_comma():
    check_transformed(
        """\
        from django.db import models

        class Card(models.IntegerChoices):
            HEARTS = 1

        models.IntegerField(choices=Card.choices,)
        """,
        """\
        from django.db import models

        class Card(models.IntegerChoices):
            HEARTS = 1

        models.IntegerField(choices=Card,)
        """,
        settings,
        filename="models.py",
    )


def test_transform_with_kwargs_multiline():
    check_transformed(
        """\
        from django.db import models

        class Card(models.IntegerChoices):
            HEARTS = 1

        models.IntegerField(
            choices=Card.choices,
        )
        """,
        """\
        from django.db import models

        class Card(models.IntegerChoices):
            HEARTS = 1

        models.IntegerField(
            choices=Card,
        )
        """,
        settings,
        filename="models.py",
    )


def test_transform_with_weird_syntax():
    check_transformed(
        """\
        from django.db import models

        class Card(models.IntegerChoices):
            HEARTS = 1

        models.IntegerField(
            choices=Card. choices,
        )
        models.IntegerField(
            choices=Card.
            choices,
        )
        """,
        """\
        from django.db import models

        class Card(models.IntegerChoices):
            HEARTS = 1

        models.IntegerField(
            choices=Card,
        )
        models.IntegerField(
            choices=Card,
        )
        """,
        settings,
        filename="models.py",
    )


def test_transform_external_package():
    check_transformed(
        """\
        from django.db import models
        from multiselectfield import MultiSelectField

        class Card(models.IntegerChoices):
            HEARTS = 1

        MultiSelectField(choices=Card.choices)
        """,
        """\
        from django.db import models
        from multiselectfield import MultiSelectField

        class Card(models.IntegerChoices):
            HEARTS = 1

        MultiSelectField(choices=Card)
        """,
        settings,
        filename="models.py",
    )
