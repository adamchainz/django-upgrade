from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(6, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


# NOOP tests first

def test_unmatched_import():
    check_noop(
        """\
        from example import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True)
        """,
    )


def test_no_excess_positional_arguments():
    # These should NOT be transformed - all args are within allowed positional count
    check_noop(
        """\
        from django.core.mail import send_mail, mail_admins, send_mass_mail, mail_managers
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"])
        mail_admins("Subject", "Message")
        send_mass_mail([("S", "M", "F", ["T"])])
        mail_managers("Subject", "Message")
        """,
    )


def test_already_using_keywords():
    # Should not transform if already using keyword arguments
    check_noop(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], fail_silently=True)
        """,
    )


def test_too_many_positional_arguments():
    # Should not transform if there are more args than we know about
    check_noop(
        """\
        from django.core.mail import send_mail
        send_mail("1", "2", "3", "4", "5", "6", "7", "8", "9", "10")
        """,
    )


def test_existing_keyword_only_as_keyword():
    # Should not transform if any keyword-only params that would be positional are already keywords
    check_noop(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True, fail_silently=False)
        """,
    )


def test_mail_not_from_django_core():
    # Should not transform non-Django mail module
    check_noop(
        """\
        from other_module import mail
        mail.send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True)
        """,
    )


def test_different_attribute_name():
    # Should not transform if attribute isn't a mail function
    check_noop(
        """\
        from django.core import mail
        mail.other_function("Subject", "Message", "from@example.com", ["to@example.com"], True)
        """,
    )


# Transformation tests - one per email function

def test_send_mail_excess_positional():
    # 5th argument (fail_silently) should be converted to keyword
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True)
        """,
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], fail_silently=True)
        """,
    )


def test_send_mail_multiple_excess_args():
    # 5th, 6th, 7th arguments should be converted to keywords
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], False, "user", "pass")
        """,
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], fail_silently=False, auth_user="user", auth_password="pass")
        """,
    )


def test_send_mass_mail_excess_positional():
    # 2nd argument (fail_silently) should be converted to keyword
    check_transformed(
        """\
        from django.core.mail import send_mass_mail
        send_mass_mail([("S1", "M1", "F", ["T1"]), ("S2", "M2", "F", ["T2"])], True)
        """,
        """\
        from django.core.mail import send_mass_mail
        send_mass_mail([("S1", "M1", "F", ["T1"]), ("S2", "M2", "F", ["T2"])], fail_silently=True)
        """,
    )


def test_mail_admins_excess_positional():
    # 3rd argument (fail_silently) should be converted to keyword
    check_transformed(
        """\
        from django.core.mail import mail_admins
        mail_admins("Admin Subject", "Admin Message", False)
        """,
        """\
        from django.core.mail import mail_admins
        mail_admins("Admin Subject", "Admin Message", fail_silently=False)
        """,
    )


def test_mail_managers_excess_positional():
    # 3rd argument (fail_silently) should be converted to keyword
    check_transformed(
        """\
        from django.core.mail import mail_managers
        mail_managers("Manager Subject", "Manager Message", True)
        """,
        """\
        from django.core.mail import mail_managers
        mail_managers("Manager Subject", "Manager Message", fail_silently=True)
        """,
    )


def test_module_import_excess_args():
    check_transformed(
        """\
        from django.core import mail
        mail.send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True)
        """,
        """\
        from django.core import mail
        mail.send_mail("Subject", "Message", "from@example.com", ["to@example.com"], fail_silently=True)
        """,
    )


def test_mixed_excess_and_keyword_args():
    # 5th positional arg should become keyword, existing keywords preserved
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], False, connection=None)
        """,
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], fail_silently=False, connection=None)
        """,
    )


# Test various indentation patterns

def test_multiline_with_excess_args():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail(
            "Subject",
            "Message", 
            "from@example.com",
            ["to@example.com"],
            True
        )
        """,
        """\
        from django.core.mail import send_mail
        send_mail(
            "Subject",
            "Message", 
            "from@example.com",
            ["to@example.com"],
            fail_silently=True
        )
        """,
    )


def test_multiline_indented_args():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail(
            "Subject",
            "Message",
            "from@example.com",
            ["to@example.com"],
            True,
            "user",
        )
        """,
        """\
        from django.core.mail import send_mail
        send_mail(
            "Subject",
            "Message",
            "from@example.com",
            ["to@example.com"],
            fail_silently=True,
            auth_user="user",
        )
        """,
    )


def test_multiline_various_whitespace():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail(
            "Subject",
                "Message",
              "from@example.com",
                  ["to@example.com"],
            True
        )
        """,
        """\
        from django.core.mail import send_mail
        send_mail(
            "Subject",
                "Message",
              "from@example.com",
                  ["to@example.com"],
            fail_silently=True
        )
        """,
    )