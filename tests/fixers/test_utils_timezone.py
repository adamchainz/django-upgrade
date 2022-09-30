from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(4, 1))


def test_empty():
    check_noop(
        "",
        settings,
    )


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


def test_import_used_otherwise():
    check_noop(
        """\
        from django.utils import timezone
        timezone.now()
        """,
        settings,
    )


def test_no_datetime_import():
    check_noop(
        """\
        from django.utils import timezone

        do_a_thing(timezone.utc)
        """,
        settings,
    )


def test_attr_no_import():
    check_noop(
        """\
        import datetime as dt
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


def test_basic():
    check_transformed(
        """\
        import datetime
        from django.utils.timezone import utc
        do_a_thing(utc)
        """,
        """\
        import datetime
        do_a_thing(datetime.timezone.utc)
        """,
        settings,
    )


def test_docstring():
    check_transformed(
        """\
        '''my module'''
        from django.utils.timezone import utc
        import datetime
        do_a_thing(utc)
        """,
        """\
        '''my module'''
        import datetime
        do_a_thing(datetime.timezone.utc)
        """,
        settings,
    )


def test_import_aliased():
    check_transformed(
        """\
        import datetime as dt
        from django.utils.timezone import utc
        do_a_thing(utc)
        """,
        """\
        import datetime as dt
        do_a_thing(dt.timezone.utc)
        """,
        settings,
    )


def test_fix_skips_other_utc_names():
    check_transformed(
        """\
        import datetime as dt
        from django.utils.timezone import utc
        utc
        myobj.utc
        """,
        """\
        import datetime as dt
        dt.timezone.utc
        myobj.utc
        """,
        settings,
    )


def test_attr():
    check_transformed(
        """\
        import datetime
        from django.utils import timezone

        do_a_thing(timezone.utc)
        """,
        """\
        import datetime
        from django.utils import timezone

        do_a_thing(datetime.timezone.utc)
        """,
        settings,
    )


def test_attr_import_aliased():
    check_transformed(
        """\
        import datetime as dt
        from django.utils import timezone

        do_a_thing(timezone.utc)
        """,
        """\
        import datetime as dt
        from django.utils import timezone

        do_a_thing(dt.timezone.utc)
        """,
        settings,
    )
