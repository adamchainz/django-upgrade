from __future__ import annotations

import pytest

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(4, 1))


def test_new_form():
    check_noop(
        """\
        self.assertFormError(form, "user", "woops")
        """,
        settings,
    )


def test_new_form_msg_prefix():
    check_noop(
        """\
        self.assertFormError(form, "user", "woops", "My form")
        """,
        settings,
    )


def test_unsupported_basic_name():
    check_noop(
        """\
        self.assertFormError(page, form, "user", "woops")
        """,
        settings,
    )


def test_response_from_unknown_client_method():
    check_noop(
        """\
        def test_something():
            page = self.client.poke()
            self.assertFormError(page, "form", "user", "woops")
        """,
        settings,
    )


def test_response_from_custom_client_use():
    check_noop(
        """\
        def test_something():
            page = Client().get()
            self.assertFormError(page, "form", "user", "woops")
        """,
        settings,
    )


def test_response_from_client_assigned_after():
    check_noop(
        """\
        def test_something():
            self.assertFormError(page, "form", "user", "woops")
            page = self.client.get()
        """,
        settings,
    )


def test_response_from_client_inner_func():
    check_noop(
        """\
        def test_something():
            def f():
                page = self.client.get()
            self.assertFormError(page, "form", "user", "woops")
        """,
        settings,
    )


def test_response_from_client_inner_class():
    check_noop(
        """\
        def test_something():
            class Wtf:
                page = self.client.get()
            self.assertFormError(page, "form", "user", "woops")
        """,
        settings,
    )


def test_assert_called_in_func_kw_default():
    check_noop(
        """\
        def f(n = self.assertFormError(page, "form", "user", "woops")):
            ...
        """,
        settings,
    )


def test_basic():
    check_transformed(
        """\
        self.assertFormError(response, "form", "user", "woops")
        """,
        """\
        self.assertFormError(response.context["form"], "user", "woops")
        """,
        settings,
    )


def test_basic_with_msg_prefix():
    check_transformed(
        """\
        self.assertFormError(response, "form", "user", "woops", "My form")
        """,
        """\
        self.assertFormError(response.context["form"], "user", "woops", "My form")
        """,
        settings,
    )


def test_longer_name():
    check_transformed(
        """\
        self.assertFormError(page_response1, "form", "user", "woops")
        """,
        """\
        self.assertFormError(page_response1.context["form"], "user", "woops")
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
        self.assertFormError({name}, "form", "user", "woops")
        """,
        f"""\
        self.assertFormError({name}.context["form"], "user", "woops")
        """,
        settings,
    )


def test_response_from_client():
    check_transformed(
        """\
        def test_something():
            url = "/"
            page = self.client.get(url)
            self.assertFormError(page, "form", "user", "woops")
        """,
        """\
        def test_something():
            url = "/"
            page = self.client.get(url)
            self.assertFormError(page.context["form"], "user", "woops")
        """,
        settings,
    )


def test_response_from_gated_client_use():
    check_transformed(
        """\
        def test_something():
            if True:
                page = self.client.get()
            self.assertFormError(page, "form", "user", "woops")
        """,
        """\
        def test_something():
            if True:
                page = self.client.get()
            self.assertFormError(page.context["form"], "user", "woops")
        """,
        settings,
    )


def test_response_from_context_manager_client_use():
    check_transformed(
        """\
        def test_something():
            with some_mock:
                page = self.client.get()
            self.assertFormError(page, "form", "user", "woops")
        """,
        """\
        def test_something():
            with some_mock:
                page = self.client.get()
            self.assertFormError(page.context["form"], "user", "woops")
        """,
        settings,
    )


def test_form_name_var():
    check_transformed(
        """\
        formname = "magicform"
        self.assertFormError(response, formname, "user", "woops")
        """,
        """\
        formname = "magicform"
        self.assertFormError(response.context[formname], "user", "woops")
        """,
        settings,
    )


def test_spaced_args():
    check_transformed(
        """\
        self.assertFormError( response , "form", "user", "woops")
        """,
        """\
        self.assertFormError( response.context["form"] , "user", "woops")
        """,
        settings,
    )


def test_second_arg_end_of_line():
    check_transformed(
        """\
        self.assertFormError(response, "form",
            "user", "woops")
        """,
        """\
        self.assertFormError(response.context["form"],
            "user", "woops")
        """,
        settings,
    )


def test_second_arg_end_of_line_no_space():
    check_transformed(
        """\
        self.assertFormError(response,"form",
            "user", "woops")
        """,
        """\
        self.assertFormError(response.context["form"],
            "user", "woops")
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
            "woops",
        )
        """,
        """\
        self.assertFormError(
            response.context["form"],
            "user",
            "woops",
        )
        """,
        settings,
    )
