from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(4, 1))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_empty():
    check_noop(
        "",
    )


def test_unmatched_import():
    check_noop(
        """\
        from datetime.timezone import utc
        """,
    )


def test_unmatched_import_name():
    check_noop(
        """\
        from django.utils.timezone import now
        """,
    )


def test_import_used_otherwise():
    check_noop(
        """\
        from django.utils import timezone
        timezone.now()
        """,
    )


def test_no_datetime_import():
    check_noop(
        """\
        from django.utils import timezone

        do_a_thing(timezone.utc)
        """,
    )


def test_attr_no_import():
    check_noop(
        """\
        import datetime as dt
        timezone.utc
        """,
    )


def test_not_imported_utc_name():
    check_noop(
        """\
        utc = 1
        utc
        """,
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
    )


def test_other_imports():
    check_transformed(
        """\
        import datetime
        from django.utils.timezone import utc
        from myapp import timezone
        do_a_thing(utc)
        """,
        """\
        import datetime
        from myapp import timezone
        do_a_thing(datetime.timezone.utc)
        """,
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
    )


def test_import_paired():
    check_transformed(
        """\
        import datetime, os
        from django.utils.timezone import utc
        do_a_thing(utc)
        """,
        """\
        import datetime, os
        do_a_thing(datetime.timezone.utc)
        """,
    )


def test_import_paired_alias():
    check_transformed(
        """\
        import numpy as np, datetime as dt
        from django.utils.timezone import utc
        do_a_thing(utc)
        """,
        """\
        import numpy as np, datetime as dt
        do_a_thing(dt.timezone.utc)
        """,
    )


def test_multiple():
    check_transformed(
        """\
        import datetime
        from django.utils.timezone import utc
        do_a_thing(utc)
        do_a_thing(utc)
        """,
        """\
        import datetime
        do_a_thing(datetime.timezone.utc)
        do_a_thing(datetime.timezone.utc)
        """,
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
    )
