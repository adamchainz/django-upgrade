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
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True)
        """,
    )


def test_unmatched_mail_import():
    check_noop(
        """\
        from example import mail
        mail.send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True)
        """,
    )


def test_unknown_mail_function():
    check_noop(
        """\
        from django.core.mail import send_chainmail
        send_chainmail("Subject", "Message", "from@example.com", ["to@example.com"], True)
        """,
    )


def test_unknown_mail_function_mail_import():
    check_noop(
        """\
        from django.core import mail
        mail.send_chainmail("Subject", "Message", "from@example.com", ["to@example.com"], True)
        """,
    )


def test_no_deprecated_positional_arguments():
    check_noop(
        """\
        from django.core.mail import get_connection, mail_admins, mail_managers, send_mail, send_mass_mail
        get_connection("example.backend")
        mail_admins("Subject", "Message")
        mail_managers("Subject", "Message")
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"])
        send_mass_mail([("Subject", "Message", "from@example.com", ["to@example.com"])])
        """,
    )


def test_already_using_keywords():
    check_noop(
        """\
        from django.core.mail import get_connection, mail_admins, mail_managers, send_mail, send_mass_mail
        get_connection("example.backend", fail_silently=True)
        mail_admins("Subject", "Message", fail_silently=True)
        mail_managers("Subject", "Message", fail_silently=True)
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], fail_silently=True)
        send_mass_mail([("Subject", "Message", "from@example.com", ["to@example.com"])], fail_silently=True)
        """,
    )


def test_too_many_positional_arguments():
    check_noop(
        """\
        from django.core.mail import send_mail
        send_mail("1", "2", "3", "4", "5", "6", "7", "8", "9", "10")
        """,
    )


def test_positional_also_keyword():
    check_noop(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True, fail_silently=False)
        """,
    )


def test_unknown_keyword_argument():
    check_noop(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True, skwibble_dwibble="skworg")
        """,
    )


def test_get_connection():
    check_transformed(
        """\
        from django.core.mail import get_connection
        get_connection("example.backend", True)
        """,
        """\
        from django.core.mail import get_connection
        get_connection("example.backend", fail_silently=True)
        """,
    )


def test_get_connection_indented():
    check_transformed(
        """\
        from django.core.mail import get_connection
        get_connection(
            "example.backend",
            True,
        )
        """,
        """\
        from django.core.mail import get_connection
        get_connection(
            "example.backend",
            fail_silently=True,
        )
        """,
    )


def test_get_connection_indented_sameline():
    check_transformed(
        """\
        from django.core.mail import get_connection
        get_connection(
            "example.backend", True
        )
        """,
        """\
        from django.core.mail import get_connection
        get_connection(
            "example.backend", fail_silently=True
        )
        """,
    )


def test_get_connection_indented_weird():
    check_transformed(
        """\
        from django.core.mail import get_connection
        get_connection(
            "example.backend",
              True,
        )
        """,
        """\
        from django.core.mail import get_connection
        get_connection(
            "example.backend",
              fail_silently=True,
        )
        """,
    )


def test_get_connection_extra_kwargs():
    check_transformed(
        """\
        from django.core.mail import get_connection
        get_connection("example.backend", True, extra="kwargy")
        """,
        """\
        from django.core.mail import get_connection
        get_connection("example.backend", fail_silently=True, extra="kwargy")
        """,
    )


def test_get_connection_module_import():
    check_transformed(
        """\
        from django.core import mail
        mail.get_connection("example.backend", False)
        """,
        """\
        from django.core import mail
        mail.get_connection("example.backend", fail_silently=False)
        """,
    )


def test_mail_admins_1():
    check_transformed(
        """\
        from django.core.mail import mail_admins
        mail_admins("Subject", "Message", True)
        """,
        """\
        from django.core.mail import mail_admins
        mail_admins("Subject", "Message", fail_silently=True)
        """,
    )


def test_mail_admins_2():
    check_transformed(
        """\
        from django.core.mail import mail_admins
        mail_admins("Subject", "Message", True, connection)
        """,
        """\
        from django.core.mail import mail_admins
        mail_admins("Subject", "Message", fail_silently=True, connection=connection)
        """,
    )


def test_mail_admins_3():
    check_transformed(
        """\
        from django.core.mail import mail_admins
        mail_admins("Subject", "Message", True, connection, "<p>HTML</p>")
        """,
        """\
        from django.core.mail import mail_admins
        mail_admins("Subject", "Message", fail_silently=True, connection=connection, html_message="<p>HTML</p>")
        """,
    )


def test_mail_admins_module_import():
    check_transformed(
        """\
        from django.core import mail
        mail.mail_admins("Subject", "Message", True, connection, "<p>HTML</p>")
        """,
        """\
        from django.core import mail
        mail.mail_admins("Subject", "Message", fail_silently=True, connection=connection, html_message="<p>HTML</p>")
        """,
    )


def test_mail_managers_1():
    check_transformed(
        """\
        from django.core.mail import mail_managers
        mail_managers("Subject", "Message", True)
        """,
        """\
        from django.core.mail import mail_managers
        mail_managers("Subject", "Message", fail_silently=True)
        """,
    )


def test_mail_managers_2():
    check_transformed(
        """\
        from django.core.mail import mail_managers
        mail_managers("Subject", "Message", True, connection)
        """,
        """\
        from django.core.mail import mail_managers
        mail_managers("Subject", "Message", fail_silently=True, connection=connection)
        """,
    )


def test_mail_managers_3():
    check_transformed(
        """\
        from django.core.mail import mail_managers
        mail_managers("Subject", "Message", True, connection, "<p>HTML</p>")
        """,
        """\
        from django.core.mail import mail_managers
        mail_managers("Subject", "Message", fail_silently=True, connection=connection, html_message="<p>HTML</p>")
        """,
    )


def test_mail_managers_module_import():
    check_transformed(
        """\
        from django.core import mail
        mail.mail_managers("Subject", "Message", True, connection, "<p>HTML</p>")
        """,
        """\
        from django.core import mail
        mail.mail_managers("Subject", "Message", fail_silently=True, connection=connection, html_message="<p>HTML</p>")
        """,
    )


def test_send_mail_1():
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


def test_send_mail_2():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True, "user")
        """,
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], fail_silently=True, auth_user="user")
        """,
    )


def test_send_mail_3():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True, "user", "pw")
        """,
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], fail_silently=True, auth_user="user", auth_password="pw")
        """,
    )


def test_send_mail_4():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True, "user", "pw", conn)
        """,
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], fail_silently=True, auth_user="user", auth_password="pw", connection=conn)
        """,
    )


def test_send_mail_5():
    check_transformed(
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], True, "user", "pw", conn, "<p>HTML</p>")
        """,
        """\
        from django.core.mail import send_mail
        send_mail("Subject", "Message", "from@example.com", ["to@example.com"], fail_silently=True, auth_user="user", auth_password="pw", connection=conn, html_message="<p>HTML</p>")
        """,
    )


def test_send_mail_module_import():
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


def test_send_mass_mail_1():
    check_transformed(
        """\
        from django.core.mail import send_mass_mail
        send_mass_mail([("Subject", "Message", "from@example.com", ["to@example.com"])], True)
        """,
        """\
        from django.core.mail import send_mass_mail
        send_mass_mail([("Subject", "Message", "from@example.com", ["to@example.com"])], fail_silently=True)
        """,
    )


def test_send_mass_mail_2():
    check_transformed(
        """\
        from django.core.mail import send_mass_mail
        send_mass_mail([("Subject", "Message", "from@example.com", ["to@example.com"])], True, "user")
        """,
        """\
        from django.core.mail import send_mass_mail
        send_mass_mail([("Subject", "Message", "from@example.com", ["to@example.com"])], fail_silently=True, auth_user="user")
        """,
    )


def test_send_mass_mail_3():
    check_transformed(
        """\
        from django.core.mail import send_mass_mail
        send_mass_mail([("Subject", "Message", "from@example.com", ["to@example.com"])], True, "user", "pw")
        """,
        """\
        from django.core.mail import send_mass_mail
        send_mass_mail([("Subject", "Message", "from@example.com", ["to@example.com"])], fail_silently=True, auth_user="user", auth_password="pw")
        """,
    )


def test_send_mass_mail_4():
    check_transformed(
        """\
        from django.core.mail import send_mass_mail
        send_mass_mail([("Subject", "Message", "from@example.com", ["to@example.com"])], True, "user", "pw", conn)
        """,
        """\
        from django.core.mail import send_mass_mail
        send_mass_mail([("Subject", "Message", "from@example.com", ["to@example.com"])], fail_silently=True, auth_user="user", auth_password="pw", connection=conn)
        """,
    )


def test_send_mass_mail_module_import():
    check_transformed(
        """\
        from django.core import mail
        mail.send_mass_mail([("Subject", "Message", "from@example.com", ["to@example.com"])], True)
        """,
        """\
        from django.core import mail
        mail.send_mass_mail([("Subject", "Message", "from@example.com", ["to@example.com"])], fail_silently=True)
        """,
    )
