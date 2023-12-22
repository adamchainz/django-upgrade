from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(5, 0))


def test_noop_reverse_with_urlconf():
    check_noop(
        """\
        redirect(reverse("my_app:my_view", urlconf="bbb"))
        """,
        settings,
    )


def test_noop_reverse_with_current_app():
    check_noop(
        """\
        redirect(reverse("my_app:my_view", current_app="myapp"))
        """,
        settings,
    )


def test_noop_reverse_with_kwargs():
    # We would have to splat kwargs in redirect which makes the function
    # call hard to understand and is not safe if one the kwargs happens
    # to be named `permanent` (which is one of `redirect` kwargs)
    check_noop(
        """\
        redirect(reverse("my_app:my_view", kwargs={"tag": "youou"}))
        """,
        settings,
    )


def test_noop_reverse_with_args():
    check_noop(
        """\
        redirect(reverse("arch-summary", args=[1945]))
        """,
        settings,
    )


def test_transform():
    check_transformed(
        """\
        redirect(reverse("my_app:my_view"))
        """,
        """\
        redirect("my_app:my_view")
        """,
        settings,
    )


def test_transform_multiline():
    check_transformed(
        """\
        redirect(
            reverse(
                "my_app:my_view",
            )
        )
        """,
        """\
        redirect(
                "my_app:my_view"
        )
        """,
        settings,
    )


def test_transform_redirect_permanent():
    check_transformed(
        """\
        redirect(reverse("my_app:my_view"), permanent=True)
        """,
        """\
        redirect("my_app:my_view", permanent=True)
        """,
        settings,
    )


def test_transform_redirect_permanent_multiline():
    check_transformed(
        """\
        redirect(
            reverse(
                "my_app:my_view",
            ),
            permanent=True,
        )
        """,
        """\
        redirect(
                "my_app:my_view",
            permanent=True,
        )
        """,
        settings,
    )
