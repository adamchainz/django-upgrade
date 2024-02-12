from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(3, 2))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_unmatched_import():
    check_noop(
        """\
        from example import EmailValidator
        EmailValidator(whitelist=["example.org"])
        """,
    )


def test_no_keyword_arguments():
    check_noop(
        """\
        from django.core.validators import EmailValidator
        EmailValidator("a", "b", ["example.org"])
        """,
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
    )
