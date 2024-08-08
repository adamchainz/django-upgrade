from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(5, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_not_imported():
    check_noop(
        """\
        format_html("<marquee>{}</marquee>".format(message))
        """,
    )


def test_has_arg():
    check_noop(
        """\
        format_html("<marquee>{} {{}}</marquee>".format(message), name)
        """,
    )


def test_has_kwarg():
    check_noop(
        """\
        format_html("<marquee>{} {{name}}</marquee>".format(message), name=name)
        """,
    )


def test_variable_format_call():
    check_noop(
        """\
        format_html(template.format(message))
        """,
    )


def test_int_format_call():
    check_noop(
        """\
        format_html((1).format(message))
        """,
    )


def test_not_format():
    check_noop(
        """\
        format_html("<marquee>{}</marquee>".fmt(message))
        """,
    )


def test_pos_arg_single():
    check_transformed(
        """\
        from django.utils.html import format_html
        format_html("<marquee>{}</marquee>".format(message))
        """,
        """\
        from django.utils.html import format_html
        format_html("<marquee>{}</marquee>", message)
        """,
    )


def test_pos_arg_double():
    check_transformed(
        """\
        from django.utils.html import format_html
        format_html("<marquee>{} {}</marquee>".format(message, name))
        """,
        """\
        from django.utils.html import format_html
        format_html("<marquee>{} {}</marquee>", message, name)
        """,
    )


def test_kwarg_single():
    check_transformed(
        """\
        from django.utils.html import format_html
        format_html("<marquee>{m}</marquee>".format(m=message))
        """,
        """\
        from django.utils.html import format_html
        format_html("<marquee>{m}</marquee>", m=message)
        """,
    )


def test_kwarg_double():
    check_transformed(
        """\
        from django.utils.html import format_html
        format_html("<marquee>{m} {n}</marquee>".format(m=message, n=name))
        """,
        """\
        from django.utils.html import format_html
        format_html("<marquee>{m} {n}</marquee>", m=message, n=name)
        """,
    )


def test_pos_kwarg_mixed():
    check_transformed(
        """\
        from django.utils.html import format_html
        format_html("<marquee>{} {n}</marquee>".format(message, n=name))
        """,
        """\
        from django.utils.html import format_html
        format_html("<marquee>{} {n}</marquee>", message, n=name)
        """,
    )


def test_indented():
    check_transformed(
        """\
        from django.utils.html import format_html
        format_html(
            "<marquee>{}</marquee>".format(message)
        )
        """,
        """\
        from django.utils.html import format_html
        format_html(
            "<marquee>{}</marquee>", message
        )
        """,
    )


def test_indented_double():
    check_transformed(
        """\
        from django.utils.html import format_html
        format_html(
            "<marquee>{}</marquee>".format(
                message
            )
        )
        """,
        """\
        from django.utils.html import format_html
        format_html(
            "<marquee>{}</marquee>",\x20
                message
        )
        """,
    )
