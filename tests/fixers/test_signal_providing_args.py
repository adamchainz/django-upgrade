from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 1))


def test_no_deprecated_arg():
    check_noop(
        """\
        from django.dispatch import Signal
        Signal(use_caching=True)
        """,
        settings,
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
        settings,
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
        settings,
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
        settings,
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
        settings,
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
        settings,
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
        settings,
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
        settings,
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
        settings,
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
        settings,
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
        settings,
    )
