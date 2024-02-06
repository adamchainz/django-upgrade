from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(1, 10))


def test_not_request():
    check_noop(
        """\
        user.is_authenticated()
        """,
        settings,
    )


def test_not_self_request():
    check_noop(
        """\
        self.user.is_authenticated()
        """,
        settings,
    )


def test_not_user():
    check_noop(
        """\
        request.is_authenticated()
        """,
        settings,
    )


def test_not_self_user():
    check_noop(
        """\
        self.request.is_authenticated()
        """,
        settings,
    )


def test_request_user_simple():
    check_transformed(
        """\
        request.user.is_authenticated()
        """,
        """\
        request.user.is_authenticated
        """,
        settings,
    )


def test_self_request_user_simple():
    check_transformed(
        """\
        self.request.user.is_authenticated()
        """,
        """\
        self.request.user.is_authenticated
        """,
        settings,
    )


def test_request_user_assigned():
    check_transformed(
        """\
        auth = request.user.is_authenticated()
        """,
        """\
        auth = request.user.is_authenticated
        """,
        settings,
    )


def test_self_request_user_assigned():
    check_transformed(
        """\
        auth = self.request.user.is_authenticated()
        """,
        """\
        auth = self.request.user.is_authenticated
        """,
        settings,
    )


def test_if_request_user():
    check_transformed(
        """\
        if request.user.is_authenticated():
            ...
        """,
        """\
        if request.user.is_authenticated:
            ...
        """,
        settings,
    )


def test_if_self_request_user():
    check_transformed(
        """\
        if self.request.user.is_authenticated():
            ...
        """,
        """\
        if self.request.user.is_authenticated:
            ...
        """,
        settings,
    )


def test_if_request_user_warlus():
    check_transformed(
        """\
        if auth:= request.user.is_authenticated():
            ...
        """,
        """\
        if auth:= request.user.is_authenticated:
            ...
        """,
        settings,
    )


def test_if_self_request_user_warlus():
    check_transformed(
        """\
        if auth:= self.request.user.is_authenticated():
            ...
        """,
        """\
        if auth:= self.request.user.is_authenticated:
            ...
        """,
        settings,
    )


def test_if_request_user_equal():
    check_transformed(
        """\
        if request.user.is_authenticated() == True:
            ...
        """,
        """\
        if request.user.is_authenticated == True:
            ...
        """,
        settings,
    )


def test_if_self_request_user_equal():
    check_transformed(
        """\
        if request.user.is_authenticated() == True:
            ...
        """,
        """\
        if request.user.is_authenticated == True:
            ...
        """,
        settings,
    )
