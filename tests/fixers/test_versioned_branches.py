from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(4, 0))


def test_future_version_gt():
    check_noop(
        """\
        import django

        if django.VERSION >= (4, 1):
            foo()
        else:
            bar()
        """,
        settings,
    )


def test_current_version_gt():
    check_transformed(
        """\
        import django

        if django.VERSION >= (4, 0):
            foo()
        else:
            bar()
        """,
        """
        import django

        foo()
        """,
        settings,
    )
