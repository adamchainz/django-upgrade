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


def test_not_imported_utc_attr():
    check_noop(
        """\
        do_a_thing(timezone.utc)
        """,
        settings,
    )


def test_basic():
    check_transformed(
        """\
        from django.utils.timezone import utc
        do_a_thing(utc)
        """,
        """\
        from datetime import timezone
        do_a_thing(timezone.utc)
        """,
        settings,
    )


def test_reuse_datetime_import():
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


def test_reuse_datetime_aliased_import():
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


def test_extend_datetime_import():
    check_transformed(
        """\
        from datetime import datetime
        from django.utils.timezone import utc
        do_a_thing(utc)
        """,
        """\
        from datetime import datetime, timezone
        do_a_thing(timezone.utc)
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


def test_attr():
    check_transformed(
        """\
        from django.utils import timezone

        do_a_thing(timezone.utc)
        """,
        """\
        from datetime import timezone

        do_a_thing(timezone.utc)
        """,
        settings,
    )


def test_attr_other_import():
    check_transformed(
        """\
        from django.utils import html, timezone

        do_a_thing(timezone.utc)
        """,
        """\
        from datetime import timezone
        from django.utils import html

        do_a_thing(timezone.utc)
        """,
        settings,
    )


def test_attr_reuse_datetime_import():
    check_transformed(
        """\
        import datetime
        from django.utils import timezone

        do_a_thing(timezone.utc)
        """,
        """\
        import datetime

        do_a_thing(datetime.timezone.utc)
        """,
        settings,
    )


def test_attr_reuse_datetime_import_aliased():
    check_transformed(
        """\
        import datetime as dt
        from django.utils import timezone

        do_a_thing(timezone.utc)
        """,
        """\
        import datetime as dt

        do_a_thing(dt.timezone.utc)
        """,
        settings,
    )


def test_attr_insert_import_after_from():
    check_transformed(
        """\
        from __future__ import annotations
        from django.utils import timezone

        do_a_thing(timezone.utc)
        """,
        """\
        from __future__ import annotations
        from datetime import timezone

        do_a_thing(timezone.utc)
        """,
        settings,
    )
