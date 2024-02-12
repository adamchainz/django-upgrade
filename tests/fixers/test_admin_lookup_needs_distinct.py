from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(4, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_no_deprecated_alias():
    check_noop(
        """\
        from django.contrib.admin.utils import something

        something
        """,
    )


def test_one_local_name():
    check_transformed(
        """\
        from django.contrib.admin.utils import lookup_needs_distinct

        x = lookup_needs_distinct(y)
        """,
        """\
        from django.contrib.admin.utils import lookup_spawns_duplicates

        x = lookup_spawns_duplicates(y)
        """,
    )


def test_with_alias():
    check_transformed(
        """\
        from django.contrib.admin.utils import lookup_needs_distinct as lnd

        v = lnd("x")
        """,
        """\
        from django.contrib.admin.utils import lookup_spawns_duplicates as lnd

        v = lnd("x")
        """,
    )
