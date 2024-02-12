from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(2, 2))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_no_deprecated_alias():
    check_noop(
        """\
        from django.utils.timezone import now
        """,
    )


def test_unrecognized_import_format():
    check_noop(
        """\
        from django.utils import timezone

        timezone.FixedOffset
        """,
    )


def test_lone_import_erased():
    check_transformed(
        """\
        from django.utils.timezone import FixedOffset
        """,
        """\
        from datetime import timedelta, timezone
        """,
    )


def test_lone_import_erased_but_not_following():
    check_transformed(
        """\
        from django.utils.timezone import FixedOffset
        import sys
        """,
        """\
        from datetime import timedelta, timezone
        import sys
        """,
    )


def test_name_import_erased():
    check_transformed(
        """\
        from django.utils.timezone import FixedOffset, now
        """,
        """\
        from datetime import timedelta, timezone
        from django.utils.timezone import now
        """,
    )


def test_name_import_erased_other_order():
    check_transformed(
        """\
        from django.utils.timezone import now, FixedOffset
        """,
        """\
        from datetime import timedelta, timezone
        from django.utils.timezone import now
        """,
    )


def test_name_import_erased_alongside_alias():
    check_transformed(
        """\
        from django.utils.timezone import now as timezone_now, FixedOffset
        """,
        """\
        from datetime import timedelta, timezone
        from django.utils.timezone import now as timezone_now
        """,
    )


def test_name_import_erased_multiline():
    check_transformed(
        """\
        from django.utils.timezone import (
            FixedOffset,
            now,
        )
        """,
        """\
        from datetime import timedelta, timezone
        from django.utils.timezone import (
            now,
        )
        """,
    )


def test_added_import_matches_indentation():
    check_transformed(
        """\
        if True:
            from django.utils.timezone import FixedOffset, now
        """,
        """\
        if True:
            from datetime import timedelta, timezone
            from django.utils.timezone import now
        """,
    )


def test_name_import_erased_multiline_with_comments():
    check_transformed(
        """\
        from django.utils.timezone import (
            FixedOffset,  # love this
            now,  # this too
        )
        """,
        """\
        from datetime import timedelta, timezone
        from django.utils.timezone import (
            now,  # this too
        )
        """,
    )


def test_call_rewritten():
    check_transformed(
        """\
        from django.utils.timezone import FixedOffset
        FixedOffset(120)
        """,
        """\
        from datetime import timedelta, timezone
        timezone(timedelta(minutes=120))
        """,
    )


def test_call_with_extra_arg_rewritten():
    check_transformed(
        """\
        from django.utils.timezone import FixedOffset
        FixedOffset(120, "Super time")
        """,
        """\
        from datetime import timedelta, timezone
        timezone(timedelta(minutes=120), "Super time")
        """,
    )


def test_call_with_star_args_not_rewritten():
    # Leave *args form broken with ImportError
    check_transformed(
        """\
        from django.utils.timezone import FixedOffset
        FixedOffset(*(120,))
        """,
        """\
        from datetime import timedelta, timezone
        FixedOffset(*(120,))
        """,
    )


def test_call_with_star_star_args_not_rewritten():
    # Leave **kwargs form broken with ImportError
    check_transformed(
        """\
        from django.utils.timezone import FixedOffset
        FixedOffset(**{'offset': 120})
        """,
        """\
        from datetime import timedelta, timezone
        FixedOffset(**{'offset': 120})
        """,
    )


def test_call_with_keyword_arguments_rewritten():
    check_transformed(
        """\
        from django.utils.timezone import FixedOffset
        FixedOffset(offset=120, name="Super time")
        """,
        """\
        from datetime import timedelta, timezone
        timezone(offset=timedelta(minutes=120), name="Super time")
        """,
    )


def test_call_with_keyword_arguments_reordered_rewritten():
    check_transformed(
        """\
        from django.utils.timezone import FixedOffset
        FixedOffset(name="Super time",
            offset=120)
        """,
        """\
        from datetime import timedelta, timezone
        timezone(name="Super time",
            offset=timedelta(minutes=120))
        """,
    )


def test_call_different_class_not_rewritten():
    check_transformed(
        """\
        FixedOffset("hi")
        """,
        """\
        FixedOffset("hi")
        """,
    )
