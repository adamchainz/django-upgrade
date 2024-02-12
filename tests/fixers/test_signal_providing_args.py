from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(3, 1))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_no_deprecated_arg():
    check_noop(
        """\
        from django.dispatch import Signal
        Signal(use_caching=True)
        """,
    )


def test_pos_arg_alone():
    check_transformed(
        """\
        from django.dispatch import Signal
        Signal(["documented", "arg"])
        """,
        """\
        from django.dispatch import Signal
        Signal()
        """,
    )


def test_pos_arg_alone_module_imported():
    check_transformed(
        """\
        from django import dispatch
        dispatch.Signal(["documented", "arg"])
        """,
        """\
        from django import dispatch
        dispatch.Signal()
        """,
    )


def test_pos_arg_alone_multiline():
    check_transformed(
        """\
        from django.dispatch import Signal
        my_signal = Signal(
            [
                "documented", "arg"
                             ])
        """,
        """\
        from django.dispatch import Signal
        my_signal = Signal()
        """,
    )


def test_pos_arg_with_caching():
    check_transformed(
        """\
        from django.dispatch import Signal
        Signal(["documented", "arg"], True)
        """,
        """\
        from django.dispatch import Signal
        Signal(None, True)
        """,
    )


def test_kwarg_alone():
    check_transformed(
        """\
        from django.dispatch import Signal
        Signal(providing_args=["documented", "arg"])
        """,
        """\
        from django.dispatch import Signal
        Signal()
        """,
    )


def test_kwarg_with_caching():
    check_transformed(
        """\
        from django.dispatch import Signal
        Signal(providing_args=["documented", "arg"], use_caching=True)
        """,
        """\
        from django.dispatch import Signal
        Signal(use_caching=True)
        """,
    )


def test_kwarg_with_caching_no_space():
    check_transformed(
        """\
        from django.dispatch import Signal
        Signal(providing_args=["documented", "arg"],use_caching=True)
        """,
        """\
        from django.dispatch import Signal
        Signal(use_caching=True)
        """,
    )


def test_kwarg_with_caching_reordered():
    check_transformed(
        """\
        from django.dispatch import Signal
        Signal(use_caching=True, providing_args=["documented", "arg"])
        """,
        """\
        from django.dispatch import Signal
        Signal(use_caching=True)
        """,
    )


def test_kwarg_with_caching_multiline():
    check_transformed(
        """\
        from django.dispatch import Signal
        Signal(
            providing_args=["documented", "arg"],
            use_caching=True,
        )
        """,
        """\
        from django.dispatch import Signal
        Signal(
            use_caching=True,
        )
        """,
    )


def test_kwarg_with_all_extras():
    check_transformed(
        """\
        from django.dispatch import Signal
        Signal(
              providing_args=[
                "documented",
                        "arg",
            ]  ,  # documents the arguments
            use_caching=True,
        )
        """,
        """\
        from django.dispatch import Signal
        Signal(
            use_caching=True,
        )
        """,
    )
