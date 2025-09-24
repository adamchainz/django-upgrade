from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(6, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_unmatched_import():
    check_noop(
        """\
        from example import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"])
        """,
    )


def test_no_positional_arguments():
    check_noop(
        """\
        from django.core.mail import send_mail
        send_mail(
            subject="Subject", 
            message="Message", 
            from_email="from@example.com",
            recipient_list=["to@example.com"]
        )
        """,
    )


def test_send_mail_direct_import():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"])
        """,
        """\
        from django.core.mail import send_mail
        send_mail(subject="Subject", message="Message", from_email="from@example.com", recipient_list=["to@example.com"])
        """,
    )


def test_send_mail_module_import():
    check_transformed(
        """\
        from django.core import mail
        mail.send_mail("Subject", "Message", "from@example.com", ["to@example.com"])
        """,
        """\
        from django.core import mail
        mail.send_mail(subject="Subject", message="Message", from_email="from@example.com", recipient_list=["to@example.com"])
        """,
    )


def test_send_mail_partial_args():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message")
        """,
        """\
        from django.core.mail import send_mail
        send_mail(subject="Subject", message="Message")
        """,
    )


def test_send_mail_with_existing_kwargs():
    check_transformed(
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
        """\
        from django.core.mail import send_mail
        send_mail(
            subject="Subject", 
            message="Message", 
            from_email="from@example.com", 
            recipient_list=["to@example.com"],
            fail_silently=True
        )
        """,
    )


def test_send_mass_mail():
    check_transformed(
        """\
        from django.core.mail import send_mass_mail
        send_mass_mail([
            ("Subject1", "Message1", "from@example.com", ["to1@example.com"]),
            ("Subject2", "Message2", "from@example.com", ["to2@example.com"]),
        ])
        """,
        """\
        from django.core.mail import send_mass_mail
        send_mass_mail(datatuple=[
            ("Subject1", "Message1", "from@example.com", ["to1@example.com"]),
            ("Subject2", "Message2", "from@example.com", ["to2@example.com"]),
        ])
        """,
    )


def test_mail_admins():
    check_transformed(
        """\
        from django.core.mail import mail_admins
        mail_admins("Subject", "Message")
        """,
        """\
        from django.core.mail import mail_admins
        mail_admins(subject="Subject", message="Message")
        """,
    )


def test_mail_managers():
    check_transformed(
        """\
        from django.core.mail import mail_managers
        mail_managers("Subject", "Message")
        """,
        """\
        from django.core.mail import mail_managers
        mail_managers(subject="Subject", message="Message")
        """,
    )


def test_mail_admins_with_kwargs():
    check_transformed(
        """\
        from django.core.mail import mail_admins
        mail_admins("Subject", "Message", fail_silently=False)
        """,
        """\
        from django.core.mail import mail_admins
        mail_admins(subject="Subject", message="Message", fail_silently=False)
        """,
    )


def test_multiple_functions():
    check_transformed(
        """\
        from django.core.mail import send_mail, mail_admins
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"])
        mail_admins("Admin Subject", "Admin Message")
        """,
        """\
        from django.core.mail import send_mail, mail_admins
        send_mail(subject="Subject", message="Message", from_email="from@example.com", recipient_list=["to@example.com"])
        mail_admins(subject="Admin Subject", message="Admin Message")
        """,
    )


def test_mixed_positional_and_keyword_args():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", from_email="from@example.com", recipient_list=["to@example.com"])
        """,
        """\
        from django.core.mail import send_mail
        send_mail(subject="Subject", message="Message", from_email="from@example.com", recipient_list=["to@example.com"])
        """,
    )


def test_only_some_positional_args():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com")
        """,
        """\
        from django.core.mail import send_mail
        send_mail(subject="Subject", message="Message", from_email="from@example.com")
        """,
    )


def test_multiline_with_whitespace():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail(
            "Subject",
            "Message",
            "from@example.com",
            ["to@example.com"]
        )
        """,
        """\
        from django.core.mail import send_mail
        send_mail(
            subject="Subject",
            message="Message",
            from_email="from@example.com",
            recipient_list=["to@example.com"]
        )
        """,
    )


def test_already_has_keyword_args():
    # Should not transform if already has keyword arguments for positional params
    check_noop(
        """\
        from django.core.mail import send_mail
        send_mail(subject="Subject", message="Message", from_email="from@example.com", recipient_list=["to@example.com"])
        """,
    )