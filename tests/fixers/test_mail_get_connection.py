from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(6, 1))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


# ---- get_connection() → mailers.default (module import form) ----


def test_old_target_version():
    tools.check_noop(
        """\
        from django.core import mail
        x = mail.get_connection()
        """,
        settings=Settings(target_version=(6, 0)),
    )


def test_unrelated_mail_import():
    check_noop(
        """\
        from example import mail
        x = mail.get_connection()
        """,
    )


def test_get_connection_with_args():
    check_noop(
        """\
        from django.core import mail
        x = mail.get_connection("myapp.EmailBackend")
        """,
    )


def test_get_connection_with_kwargs():
    check_noop(
        """\
        from django.core import mail
        x = mail.get_connection(fail_silently=True)
        """,
    )


def test_get_connection_module_import():
    check_transformed(
        """\
        from django.core import mail
        x = mail.get_connection()
        """,
        """\
        from django.core import mail
        x = mail.mailers.default
        """,
    )


def test_get_connection_module_import_inline_expression():
    check_transformed(
        """\
        from django.core import mail
        mail.get_connection().send_messages([msg])
        """,
        """\
        from django.core import mail
        mail.mailers.default.send_messages([msg])
        """,
    )


# ---- get_connection() → mailers.default (direct import form) ----


def test_direct_import_unrelated():
    check_noop(
        """\
        from example import get_connection
        x = get_connection()
        """,
    )


def test_direct_import_aliased():
    check_noop(
        """\
        from django.core.mail import get_connection as gc
        x = gc()
        """,
    )


def test_direct_import_with_args():
    check_noop(
        """\
        from django.core.mail import get_connection
        x = get_connection("myapp.EmailBackend")
        """,
    )


def test_direct_import_with_kwargs():
    check_noop(
        """\
        from django.core.mail import get_connection
        x = get_connection(fail_silently=True)
        """,
    )


def test_direct_import_mixed_args():
    """When some calls have args, no transformation at all."""
    check_noop(
        """\
        from django.core.mail import get_connection
        x = get_connection()
        y = get_connection(fail_silently=True)
        """,
    )


def test_direct_import_standalone():
    check_transformed(
        """\
        from django.core.mail import get_connection
        x = get_connection()
        """,
        """\
        from django.core.mail import mailers
        x = mailers.default
        """,
    )


def test_direct_import_standalone_with_other_names():
    check_transformed(
        """\
        from django.core.mail import get_connection, send_mail
        x = get_connection()
        """,
        """\
        from django.core.mail import mailers, send_mail
        x = mailers.default
        """,
    )


def test_direct_import_mailers_already_imported():
    check_transformed(
        """\
        from django.core.mail import get_connection, mailers
        x = get_connection()
        """,
        """\
        from django.core.mail import mailers
        x = mailers.default
        """,
    )


def test_direct_import_inline_only():
    """Only inline kwarg usages → import removed entirely."""
    check_transformed(
        """\
        from django.core.mail import get_connection, send_mail
        send_mail("s", "m", "f", ["t"], connection=get_connection())
        """,
        """\
        from django.core.mail import send_mail
        send_mail("s", "m", "f", ["t"])
        """,
    )


def test_direct_import_standalone_and_inline():
    check_transformed(
        """\
        from django.core.mail import get_connection, send_mail
        conn = get_connection()
        send_mail("s", "m", "f", ["t"], connection=get_connection())
        """,
        """\
        from django.core.mail import mailers, send_mail
        conn = mailers.default
        send_mail("s", "m", "f", ["t"])
        """,
    )


# Test removing connection=get_connection() from mail functions


def test_send_mail_unrelated_import():
    check_noop(
        """\
        from example import send_mail, mail
        send_mail("s", "m", "f", ["t"], connection=mail.get_connection())
        """,
    )


def test_send_mail_connection_not_get_connection():
    check_transformed(
        """\
        from django.core import mail
        conn = mail.get_connection()
        mail.send_mail("s", "m", "f", ["t"], connection=conn)
        """,
        """\
        from django.core import mail
        conn = mail.mailers.default
        mail.send_mail("s", "m", "f", ["t"], connection=conn)
        """,
    )


def test_send_mail_connection_get_connection_with_kwargs():
    check_noop(
        """\
        from django.core import mail
        mail.send_mail("s", "m", "f", ["t"], connection=mail.get_connection(fail_silently=True))
        """,
    )


def test_send_mail_module_import():
    check_transformed(
        """\
        from django.core import mail
        mail.send_mail("s", "m", "f", ["t"], connection=mail.get_connection())
        """,
        """\
        from django.core import mail
        mail.send_mail("s", "m", "f", ["t"])
        """,
    )


def test_send_mail_direct_import():
    check_transformed(
        """\
        from django.core.mail import get_connection, send_mail
        send_mail("s", "m", "f", ["t"], connection=get_connection())
        """,
        """\
        from django.core.mail import send_mail
        send_mail("s", "m", "f", ["t"])
        """,
    )


def test_send_mail_connection_not_last():
    check_transformed(
        """\
        from django.core import mail
        mail.send_mail("s", "m", "f", ["t"], connection=mail.get_connection(), html_message="<p>Hi</p>")
        """,
        """\
        from django.core import mail
        mail.send_mail("s", "m", "f", ["t"], html_message="<p>Hi</p>")
        """,
    )


def test_send_mail_multiline():
    check_transformed(
        """\
        from django.core import mail
        mail.send_mail(
            "s",
            "m",
            "f",
            ["t"],
            connection=mail.get_connection(),
        )
        """,
        """\
        from django.core import mail
        mail.send_mail(
            "s",
            "m",
            "f",
            ["t"],
        )
        """,
    )


def test_send_mass_mail_module_import():
    check_transformed(
        """\
        from django.core import mail
        mail.send_mass_mail((msg1, msg2), connection=mail.get_connection())
        """,
        """\
        from django.core import mail
        mail.send_mass_mail((msg1, msg2))
        """,
    )


def test_mail_admins_module_import():
    check_transformed(
        """\
        from django.core import mail
        mail.mail_admins("subject", "message", connection=mail.get_connection())
        """,
        """\
        from django.core import mail
        mail.mail_admins("subject", "message")
        """,
    )


def test_mail_managers_module_import():
    check_transformed(
        """\
        from django.core import mail
        mail.mail_managers("subject", "message", connection=mail.get_connection())
        """,
        """\
        from django.core import mail
        mail.mail_managers("subject", "message")
        """,
    )


def test_send_mail_direct_import_all_functions():
    check_transformed(
        """\
        from django.core.mail import get_connection, mail_admins, mail_managers, send_mail, send_mass_mail
        send_mail("s", "m", "f", ["t"], connection=get_connection())
        send_mass_mail((m,), connection=get_connection())
        mail_admins("s", "m", connection=get_connection())
        mail_managers("s", "m", connection=get_connection())
        """,
        """\
        from django.core.mail import mail_admins, mail_managers, send_mail, send_mass_mail
        send_mail("s", "m", "f", ["t"])
        send_mass_mail((m,))
        mail_admins("s", "m")
        mail_managers("s", "m")
        """,
    )
