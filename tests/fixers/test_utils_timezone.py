from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(4, 1))


def test_unmatched_import():
    check_noop(
        """\
        from datetime.timezone import utc
        """,
        settings,
    )


def test_unmatched_import_name():
    check_noop(
        """\
        from django.utils.timezone import now
        """,
        settings,
    )


def test_unrecognized_import_format():
    check_noop(
        """\
        from django.utils import timezone

        def foo():
            print(timezone.utc)
        """,
        settings,
    )


def test_fixed():
    check_transformed(
        """\
        from django.utils.timezone import utc
        """,
        """\
        from datetime.timezone import utc
        """,
        settings,
    )
