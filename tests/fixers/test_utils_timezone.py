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


def test_untouched_utc_attribute():
    check_noop(
        """\
        timezone.utc
        """,
        settings,
    )


def test_not_imported_utc_name():
    check_noop(
        """\
        utc = 1
        utc
        """,
        settings,
    )


def test_fixed():
    check_transformed(
        """\
        from django.utils.timezone import utc
        foo(utc)
        """,
        """\
        from datetime import timezone
        foo(timezone.utc)
        """,
        settings,
    )


def test_fix_skips_other_utc_names():
    check_transformed(
        """\
        from django.utils.timezone import utc
        utc
        myobj.utc
        """,
        """\
        from datetime import timezone
        timezone.utc
        myobj.utc
        """,
        settings,
    )


def test_fix_inner_import():
    check_transformed(
        """\
        def do_something():
            from django.utils.timezone import utc
            something(utc)
        """,
        """\
        def do_something():
            from datetime import timezone
            something(timezone.utc)
        """,
        settings,
    )
