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


def test_request_user_is_anonymous_simple():
    check_transformed(
        """\
        request.user.is_anonymous()
        """,
        """\
        request.user.is_anonymous
        """,
        settings,
    )


def test_request_user_is_authenticated_simple():
    check_transformed(
        """\
        request.user.is_authenticated()
        """,
        """\
        request.user.is_authenticated
        """,
        settings,
    )


def test_self_request_user_is_anonymous_simple():
    check_transformed(
        """\
        self.request.user.is_anonymous()
        """,
        """\
        self.request.user.is_anonymous
        """,
        settings,
    )


def test_self_request_user_is_authenticated_simple():
    check_transformed(
        """\
        self.request.user.is_authenticated()
        """,
        """\
        self.request.user.is_authenticated
        """,
        settings,
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
        settings,
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
        settings,
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
        settings,
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
        settings,
    )


def test_spaces_between_noop():
    check_noop(
        "request . user . is_authenticated ",
        settings,
    )


def test_spaces_between():
    check_transformed(
        "request . user . is_authenticated ( )",
        "request . user . is_authenticated ",
        settings,
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
        settings,
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
        settings,
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
        settings,
    )
