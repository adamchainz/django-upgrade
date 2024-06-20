from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(4, 2))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_success_indexes_present():
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
        filename="example/models.py",
    )
