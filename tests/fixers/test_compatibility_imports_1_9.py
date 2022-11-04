from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(1, 9))


def test_unmatched_import():
    check_noop(
        """\
        from example import pretty_name
        pretty_name()
        """,
        settings,
    )


def test_unmatched_name():
    check_noop(
        """\
        from django.forms.forms import something
        """,
        settings,
    )


def test_unrecognized_import_format():
    check_noop(
        """\
        from django.forms import forms

        forms.pretty_name()
        """,
        settings,
    )


def test_import_star():
    check_transformed(
        """\
        from django.forms.forms import *

        pretty_name()
        """,
        """\
        from django.forms.forms import *

        pretty_name()
        """,
        settings,
    )


def test_name_imported():
    check_transformed(
        """\
        from django.forms.forms import pretty_name

        pretty_name()
        """,
        """\
        from django.forms.utils import pretty_name

        pretty_name()
        """,
        settings,
    )


def test_name_imported_as_other_name():
    check_transformed(
        """\
        from django.forms.forms import pretty_name as pn

        pn()
        """,
        """\
        from django.forms.utils import pretty_name as pn

        pn()
        """,
        settings,
    )
