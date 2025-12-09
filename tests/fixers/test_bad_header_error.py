from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(5, 1))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_no_bad_header_error():
    check_noop(
        """\
        from django.core.mail import send_mail

        send_mail('subject', 'message', 'from@example.com', ['to@example.com'])
        """,
    )


def test_bad_header_error_simple():
    check_transformed(
        """\
        from django.core.mail import BadHeaderError

        raise BadHeaderError("Invalid header")
        """,
        """\

        raise ValueError("Invalid header")
        """,
    )


def test_bad_header_error_with_other_imports():
    check_transformed(
        """\
        from django.core.mail import BadHeaderError, send_mail

        try:
            send_mail('subject', 'message', 'from@example.com', ['to@example.com'])
        except BadHeaderError:
            pass
        """,
        """\
        from django.core.mail import send_mail

        try:
            send_mail('subject', 'message', 'from@example.com', ['to@example.com'])
        except ValueError:
            pass
        """,
    )


def test_bad_header_error_in_except():
    check_transformed(
        """\
        from django.core.mail import BadHeaderError

        try:
            do_something()
        except BadHeaderError as e:
            handle_error(e)
        """,
        """\

        try:
            do_something()
        except ValueError as e:
            handle_error(e)
        """,
    )


def test_bad_header_error_raise_with_message():
    check_transformed(
        """\
        from django.core.mail import BadHeaderError

        if invalid_header:
            raise BadHeaderError("Header contains newline")
        """,
        """\

        if invalid_header:
            raise ValueError("Header contains newline")
        """,
    )


def test_bad_header_error_multiple_uses():
    check_transformed(
        """\
        from django.core.mail import BadHeaderError, EmailMessage

        try:
            msg = EmailMessage()
            msg.send()
        except BadHeaderError:
            raise BadHeaderError("Invalid header found")
        """,
        """\
        from django.core.mail import EmailMessage

        try:
            msg = EmailMessage()
            msg.send()
        except ValueError:
            raise ValueError("Invalid header found")
        """,
    )


def test_bad_header_error_with_alias():
    check_transformed(
        """\
        from django.core.mail import BadHeaderError as BHE

        raise BHE("Invalid")
        """,
        """\

        raise ValueError("Invalid")
        """,
    )


def test_bad_header_error_not_from_django():
    check_noop(
        """\
        from myapp.exceptions import BadHeaderError

        raise BadHeaderError("Custom error")
        """,
    )


def test_bad_header_error_builtin_ValueError_already_used():
    check_transformed(
        """\
        from django.core.mail import BadHeaderError

        try:
            int("not a number")
        except ValueError:
            pass

        raise BadHeaderError("Invalid header")
        """,
        """\

        try:
            int("not a number")
        except ValueError:
            pass

        raise ValueError("Invalid header")
        """,
    )

