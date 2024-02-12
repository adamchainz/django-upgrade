from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(1, 10))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_not_request():
    check_noop(
        """\
        user.is_authenticated()
        """,
    )


def test_not_self_request():
    check_noop(
        """\
        self.user.is_authenticated()
        """,
    )


def test_not_user():
    check_noop(
        """\
        request.is_authenticated()
        """,
    )


def test_not_self_user():
    check_noop(
        """\
        self.request.is_authenticated()
        """,
    )


def test_request_user_is_anonymous_simple():
    check_transformed(
        """\
        request.user.is_anonymous()
        """,
        """\
        request.user.is_anonymous
        """,
    )


def test_request_user_is_authenticated_simple():
    check_transformed(
        """\
        request.user.is_authenticated()
        """,
        """\
        request.user.is_authenticated
        """,
    )


def test_self_request_user_is_anonymous_simple():
    check_transformed(
        """\
        self.request.user.is_anonymous()
        """,
        """\
        self.request.user.is_anonymous
        """,
    )


def test_self_request_user_is_authenticated_simple():
    check_transformed(
        """\
        self.request.user.is_authenticated()
        """,
        """\
        self.request.user.is_authenticated
        """,
    )


def test_if_request_user_is_anonymous():
    check_transformed(
        """\
        if request.user.is_anonymous():
            ...
        """,
        """\
        if request.user.is_anonymous:
            ...
        """,
    )


def test_if_request_user_is_authenticated():
    check_transformed(
        """\
        if request.user.is_authenticated():
            ...
        """,
        """\
        if request.user.is_authenticated:
            ...
        """,
    )


def test_if_self_request_user_is_anonymous():
    check_transformed(
        """\
        if self.request.user.is_anonymous():
            ...
        """,
        """\
        if self.request.user.is_anonymous:
            ...
        """,
    )


def test_if_self_request_user_is_authenticated():
    check_transformed(
        """\
        if self.request.user.is_authenticated():
            ...
        """,
        """\
        if self.request.user.is_authenticated:
            ...
        """,
    )


def test_spaces_between_noop():
    check_noop(
        "request . user . is_authenticated ",
    )


def test_spaces_between():
    check_transformed(
        "request . user . is_authenticated ( )",
        "request . user . is_authenticated ",
    )


def test_comment_between():
    check_transformed(
        """\
        request.user.is_anonymous(  # something
        )
        """,
        """\
        request.user.is_anonymous
        """,
    )


def test_spaces_and_comments_noop():
    check_noop(
        """\
        if (
            request
            .user
            .is_authenticated  # bla
        ):
            ...
        """,
    )


def test_spaces_and_comments():
    check_transformed(
        """\
        if (
            request
            .user
            .is_authenticated  # bla
            () # bla
        ):
            ...
        """,
        """\
        if (
            request
            .user
            .is_authenticated  # bla
             # bla
        ):
            ...
        """,
    )
