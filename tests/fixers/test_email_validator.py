from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 2))


def test_unmatched_import():
    check_noop(
        """\
        from example import EmailValidator
        EmailValidator(whitelist=["example.org"])
        """,
        settings,
    )


def test_no_keyword_arguments():
    check_noop(
        """\
        from django.core.validators import EmailValidator
        EmailValidator("a", "b", ["example.org"])
        """,
        settings,
    )


def test_whitelist():
    check_transformed(
        """\
        from django.core.validators import EmailValidator
        EmailValidator(whitelist=["example.com"])
        """,
        """\
        from django.core.validators import EmailValidator
        EmailValidator(allowlist=["example.com"])
        """,
        settings,
    )


def test_other_args():
    check_transformed(
        """\
        from django.core.validators import EmailValidator
        EmailValidator(
            "hi", code="abc",
            whitelist=["example.com"],
        )
        """,
        """\
        from django.core.validators import EmailValidator
        EmailValidator(
            "hi", code="abc",
            allowlist=["example.com"],
        )
        """,
        settings,
    )
