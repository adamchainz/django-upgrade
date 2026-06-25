from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(6, 1))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


# No-ops


def test_old_target_version():
    check_noop(
        """\
        from django.core.mail import send_mail
        send_mail("s", "m", "f", ["t"], fail_silently=False)
        """,
        settings=Settings(target_version=(6, 0)),
    )


def test_unmatched_import():
    check_noop(
        """\
        from example import send_mail
        send_mail("s", "m", "f", ["t"], fail_silently=False)
        """,
    )


def test_unmatched_mail_import():
    check_noop(
        """\
        from example import mail
        mail.send_mail("s", "m", "f", ["t"], fail_silently=False)
        """,
    )


def test_fail_silently_true():
    check_noop(
        """\
        from django.core.mail import send_mail
        send_mail("s", "m", "f", ["t"], fail_silently=True)
        """,
    )


def test_no_fail_silently():
    check_noop(
        """\
        from django.core.mail import send_mail
        send_mail("s", "m", "f", ["t"])
        """,
    )


def test_fail_silently_true_module_import():
    check_noop(
        """\
        from django.core import mail
        mail.send_mail("s", "m", "f", ["t"], fail_silently=True)
        """,
    )


def test_email_message_send_fail_silently_true():
    check_noop(
        """\
        from django.core.mail import EmailMessage
        EmailMessage("s", "m", "f", ["t"]).send(fail_silently=True)
        """,
    )


def test_arbitrary_send_call_not_rewritten():
    # .send() on an arbitrary variable — not EmailMessage(...).send()
    check_noop(
        """\
        msg.send(fail_silently=False)
        """,
    )


# send_mail (direct import)


def test_send_mail_direct_import():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("s", "m", "f", ["t"], fail_silently=False)
        """,
        """\
        from django.core.mail import send_mail
        send_mail("s", "m", "f", ["t"])
        """,
    )


def test_send_mail_only_kwarg():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail(fail_silently=False)
        """,
        """\
        from django.core.mail import send_mail
        send_mail()
        """,
    )


def test_send_mail_first_kwarg_not_last_kwarg():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail(fail_silently=False, subject="s")
        """,
        """\
        from django.core.mail import send_mail
        send_mail(subject="s")
        """,
    )


def test_send_mail_kwarg_before_starred_arg():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail(fail_silently=False, *args)
        """,
        """\
        from django.core.mail import send_mail
        send_mail(*args)
        """,
    )


def test_send_mail_direct_import_not_last_kwarg():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("s", "m", "f", ["t"], fail_silently=False, html_message="<b>hi</b>")
        """,
        """\
        from django.core.mail import send_mail
        send_mail("s", "m", "f", ["t"], html_message="<b>hi</b>")
        """,
    )


def test_send_mail_not_last_kwarg_multiline():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail(
            "s",
            "m",
            "f",
            ["t"],
            fail_silently=False,
            html_message="<b>hi</b>",
        )
        """,
        """\
        from django.core.mail import send_mail
        send_mail(
            "s",
            "m",
            "f",
            ["t"],
            html_message="<b>hi</b>",
        )
        """,
    )


def test_send_mail_multiline():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail(
            "s",
            "m",
            "f",
            ["t"],
            fail_silently=False,
        )
        """,
        """\
        from django.core.mail import send_mail
        send_mail(
            "s",
            "m",
            "f",
            ["t"],
        )
        """,
    )


# send_mass_mail / mail_admins / mail_managers (direct import)


def test_all_send_functions_direct_import():
    check_transformed(
        """\
        from django.core.mail import mail_admins, mail_managers, send_mail, send_mass_mail
        send_mail("s", "m", "f", ["t"], fail_silently=False)
        send_mass_mail([(\"s\", \"m\", \"f\", [\"t\"])], fail_silently=False)
        mail_admins("s", "m", fail_silently=False)
        mail_managers("s", "m", fail_silently=False)
        """,
        """\
        from django.core.mail import mail_admins, mail_managers, send_mail, send_mass_mail
        send_mail("s", "m", "f", ["t"])
        send_mass_mail([(\"s\", \"m\", \"f\", [\"t\"])])
        mail_admins("s", "m")
        mail_managers("s", "m")
        """,
    )


# module import (mail.send_mail etc.)


def test_send_mail_module_import():
    check_transformed(
        """\
        from django.core import mail
        mail.send_mail("s", "m", "f", ["t"], fail_silently=False)
        """,
        """\
        from django.core import mail
        mail.send_mail("s", "m", "f", ["t"])
        """,
    )


def test_all_send_functions_module_import():
    check_transformed(
        """\
        from django.core import mail
        mail.send_mail("s", "m", "f", ["t"], fail_silently=False)
        mail.send_mass_mail([(\"s\", \"m\", \"f\", [\"t\"])], fail_silently=False)
        mail.mail_admins("s", "m", fail_silently=False)
        mail.mail_managers("s", "m", fail_silently=False)
        """,
        """\
        from django.core import mail
        mail.send_mail("s", "m", "f", ["t"])
        mail.send_mass_mail([(\"s\", \"m\", \"f\", [\"t\"])])
        mail.mail_admins("s", "m")
        mail.mail_managers("s", "m")
        """,
    )


# EmailMessage(...).send()


def test_email_message_unmatched_direct_import():
    check_noop(
        """\
        from example import EmailMessage
        EmailMessage("s", "m", "f", ["t"]).send(fail_silently=False)
        """,
    )


def test_email_message_send_direct():
    check_transformed(
        """\
        from django.core.mail import EmailMessage
        EmailMessage("s", "m", "f", ["t"]).send(fail_silently=False)
        """,
        """\
        from django.core.mail import EmailMessage
        EmailMessage("s", "m", "f", ["t"]).send()
        """,
    )


def test_email_message_send_message_module_import():
    check_transformed(
        """\
        from django.core.mail.message import EmailMessage
        EmailMessage("s", "m", "f", ["t"]).send(fail_silently=False)
        """,
        """\
        from django.core.mail.message import EmailMessage
        EmailMessage("s", "m", "f", ["t"]).send()
        """,
    )


def test_email_multi_alternatives_send_direct():
    check_transformed(
        """\
        from django.core.mail import EmailMultiAlternatives
        EmailMultiAlternatives("s", "m", "f", ["t"]).send(fail_silently=False)
        """,
        """\
        from django.core.mail import EmailMultiAlternatives
        EmailMultiAlternatives("s", "m", "f", ["t"]).send()
        """,
    )


def test_email_message_unrecognised_attr_import():
    check_noop(
        """\
        from myapp import something
        something.EmailMessage("s", "m", "f", ["t"]).send(fail_silently=False)
        """,
    )


def test_email_message_send_module_attr_import():
    check_transformed(
        """\
        from django.core import mail
        mail.EmailMessage("s", "m", "f", ["t"]).send(fail_silently=False)
        """,
        """\
        from django.core import mail
        mail.EmailMessage("s", "m", "f", ["t"]).send()
        """,
    )


def test_email_message_send_module_import():
    check_transformed(
        """\
        from django.core.mail import EmailMessage
        EmailMessage("s", "m", "f", ["t"]).send(fail_silently=False)
        """,
        """\
        from django.core.mail import EmailMessage
        EmailMessage("s", "m", "f", ["t"]).send()
        """,
    )
