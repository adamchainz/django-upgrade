from __future__ import annotations

import pytest

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(4, 1))


def test_new_form():
    check_noop(
        """\
        self.assertFormError(form, "user", ["woops"])
        """,
        settings,
    )


def test_unsupported_name():
    check_noop(
        """\
        self.assertFormError(page, form, "user", ["woops"])
        """,
        settings,
    )


def test_basic():
    check_transformed(
        """\
        self.assertFormError(response, "form", "user", ["woops"])
        """,
        """\
        self.assertFormError(response.context["form"], "user", ["woops"])
        """,
        settings,
    )


def test_longer_name():
    check_transformed(
        """\
        self.assertFormError(page_response1, "form", "user", ["woops"])
        """,
        """\
        self.assertFormError(page_response1.context["form"], "user", ["woops"])
        """,
        settings,
    )


@pytest.mark.parametrize(
    "name",
    (
        "resp",
        "res",
        "r",
    ),
)
def test_short_names(name):
    check_transformed(
        f"""\
        self.assertFormError({name}, "form", "user", ["woops"])
        """,
        f"""\
        self.assertFormError({name}.context["form"], "user", ["woops"])
        """,
        settings,
    )


def test_form_name_var():
    check_transformed(
        """\
        formname = "magicform"
        self.assertFormError(response, formname, "user", ["woops"])
        """,
        """\
        formname = "magicform"
        self.assertFormError(response.context[formname], "user", ["woops"])
        """,
        settings,
    )


def test_spaced_args():
    check_transformed(
        """\
        self.assertFormError( response , "form", "user", ["woops"])
        """,
        """\
        self.assertFormError( response.context["form"] , "user", ["woops"])
        """,
        settings,
    )


def test_second_arg_end_of_line():
    check_transformed(
        """\
        self.assertFormError(response, "form",
            "user", ["woops"])
        """,
        """\
        self.assertFormError(response.context["form"],
            "user", ["woops"])
        """,
        settings,
    )


def test_second_arg_end_of_line_no_space():
    check_transformed(
        """\
        self.assertFormError(response,"form",
            "user", ["woops"])
        """,
        """\
        self.assertFormError(response.context["form"],
            "user", ["woops"])
        """,
        settings,
    )


def test_second_arg_own_line():
    check_transformed(
        """\
        self.assertFormError(
            response,
            "form",
            "user",
            ["woops"],
        )
        """,
        """\
        self.assertFormError(
            response.context["form"],
            "user",
            ["woops"],
        )
        """,
        settings,
    )
