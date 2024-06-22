from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(4, 2))
check_noop = partial(tools.check_noop, settings=settings, filename="example/models.py")
check_transformed = partial(
    tools.check_transformed, settings=settings, filename="example/models.py"
)


def test_not_meta_class():
    check_noop(
        """\
        from django.db import models

        class Duck(models.Model):
            class NotMeta:
                index_together = [["bill", "tail"]]
                indexes = []
        """,
    )


def test_not_in_classdef():
    check_noop(
        """\
        from django.db import models

        class Duck(models.Model):
            if True:
                class Meta:
                    index_together = [["bill", "tail"]]
                    indexes = []
        """,
    )


def test_no_index_together():
    check_noop(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [["bill", "tail"]]
        """,
    )


def test_multiple_index_togethers():
    check_noop(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [["bill", "tail"]]
                index_together = [["tail", "bill"]]
                indexes = []
        """,
    )


def test_not_sequence():
    check_noop(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = {
                    ["bill", "tail"]
                }
                indexes = []
        """,
    )


def not_sub_sequence():
    check_noop(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [{"bill", "tail"}]
                indexes = []
        """,
    )


def test_not_strings():
    check_noop(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [[f1, f2]]
                indexes = []
        """,
    )


def test_multiple_indexes():
    check_noop(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [["bill", "tail"]]
                indexes = []
                indexes = []
        """,
    )


def test_no_models_import():
    check_noop(
        """\
        class Duck:
            class Meta:
                index_together = [["bill", "tail"]]
                indexes = []
        """,
    )


def test_list_indexes_present():
    check_transformed(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [["bill", "tail"]]
                indexes = []
        """,
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [models.Index(fields=["bill", "tail"])]
        """,
    )


def test_tuple_indexes_present():
    check_transformed(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [("bill", "tail")]
                indexes = []
        """,
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [models.Index(fields=("bill", "tail"))]
        """,
    )


def test_mixed_indexes_present():
    check_transformed(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [
                    ("bill", "tail"),
                    ("nape", "mantle"),
                ]
                indexes = []
        """,
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [models.Index(fields=("bill", "tail")), models.Index(fields=("nape", "mantle"))]
        """,
    )


def test_indexes_nonempty_no_trailing_comma():
    check_transformed(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [("bill", "tail")]
                indexes = [models.Index("bill")]
        """,
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [models.Index("bill"), models.Index(fields=("bill", "tail"))]
        """,
    )


def test_indexes_nonempty_trailing_comma():
    check_transformed(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [("bill", "tail")]
                indexes = [models.Index("bill"),]
        """,
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [models.Index("bill"), models.Index(fields=("bill", "tail"))]
        """,
    )


def test_indexes_nonempty_multiline_dedented():
    check_transformed(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [("bill", "tail")]
                indexes = [
                    models.Index("bill"),
                ]
        """,
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [
                    models.Index("bill"),
                models.Index(fields=("bill", "tail"))]
        """,
    )


def test_indexes_nonempty_multiline_dedented_fully():
    check_transformed(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [("bill", "tail")]
                indexes = [
                    models.Index("bill"),
        ]
        """,
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [
                    models.Index("bill"),
        models.Index(fields=("bill", "tail"))]
        """,
    )


def test_indexes_nonempty_multiline_indented():
    check_transformed(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [("bill", "tail")]
                indexes = [
                    models.Index("bill"),
                        ]
        """,
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [
                    models.Index("bill"),
                        models.Index(fields=("bill", "tail"))]
        """,
    )


def test_indexes_nonempty_multiline_aligned():
    check_transformed(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [("bill", "tail")]
                indexes = [
                    models.Index("bill"),
                    ]
        """,
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [
                    models.Index("bill"),
                    models.Index(fields=("bill", "tail"))]
        """,
    )


def test_list_indexes_absent():
    check_transformed(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [["bill", "tail"]]
        """,
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [models.Index(fields=["bill", "tail"])]
        """,
    )


def test_tuple_indexes_absent():
    check_transformed(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [("bill", "tail")]
        """,
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [models.Index(fields=("bill", "tail"))]
        """,
    )


def test_mixed_indexes_absent():
    check_transformed(
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                index_together = [
                    ("bill", "tail"),
                    ("nape", "mantle"),
                ]
        """,
        """\
        from django.db import models

        class Duck(models.Model):
            class Meta:
                indexes = [models.Index(fields=("bill", "tail")), models.Index(fields=("nape", "mantle"))]
        """,
    )


def test_index_imported():
    check_transformed(
        """\
        from django.db.models import Index

        class Duck:
            class Meta:
                index_together = [["bill", "tail"]]
                indexes = []
        """,
        """\
        from django.db.models import Index

        class Duck:
            class Meta:
                indexes = [Index(fields=["bill", "tail"])]
        """,
    )


def test_single_quotes_rewritten():
    check_transformed(
        """\
        from django.db import models

        class Duck:
            class Meta:
                index_together = [['bill', 'tail']]
                indexes = []
        """,
        """\
        from django.db import models

        class Duck:
            class Meta:
                indexes = [models.Index(fields=["bill", "tail"])]
        """,
    )
