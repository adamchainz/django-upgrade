from __future__ import annotations

import pytest

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(4, 1))


class TestForm:
    def test_new_signature(self):
        check_noop(
            """\
            self.assertFormError(form, "user", "woops")
            """,
            settings,
        )

    def test_new_signature_msg_prefix(self):
        check_noop(
            """\
            self.assertFormError(form, "user", "woops", "My form")
            """,
            settings,
        )

    def test_bad_signature_too_many_args(self):
        check_noop(
            """\
            self.assertFormError(response, "form", "user", "woops", "!!!", None)
            """,
            settings,
        )

    def test_bad_signature_too_few_args(self):
        check_noop(
            """\
            self.assertFormError(response, "form")
            """,
            settings,
        )

    def test_bad_signature_bad_errors_kwarg(self):
        check_noop(
            """\
            self.assertFormError(response, "form", "user", err="woops")
            """,
            settings,
        )

    def test_bad_signature_bad_msg_prefix_kwarg(self):
        check_noop(
            """\
            self.assertFormError(response, "form", "user", "woops", msg="!!!")
            """,
            settings,
        )

    def test_unsupported_basic_name(self):
        check_noop(
            """\
            self.assertFormError(page, form, "user", "woops")
            """,
            settings,
        )

    def test_response_from_unknown_client_method(self):
        check_noop(
            """\
            def test_something():
                page = self.client.poke()
                self.assertFormError(page, "form", "user", "woops")
            """,
            settings,
        )

    def test_response_from_custom_client_use(self):
        check_noop(
            """\
            def test_something():
                page = Client().get()
                self.assertFormError(page, "form", "user", "woops")
            """,
            settings,
        )

    def test_response_from_client_assigned_after(self):
        check_noop(
            """\
            def test_something():
                self.assertFormError(page, "form", "user", "woops")
                page = self.client.get()
            """,
            settings,
        )

    def test_response_from_client_inner_async_func(self):
        check_noop(
            """\
            def test_something():
                async def f():
                    page = self.client.get()
                self.assertFormError(page, "form", "user", "woops")
            """,
            settings,
        )

    def test_response_from_client_inner_func(self):
        check_noop(
            """\
            def test_something():
                def f():
                    page = self.client.get()
                self.assertFormError(page, "form", "user", "woops")
            """,
            settings,
        )

    def test_response_from_client_inner_class(self):
        check_noop(
            """\
            def test_something():
                class Wtf:
                    page = self.client.get()
                self.assertFormError(page, "form", "user", "woops")
            """,
            settings,
        )

    def test_response_from_client_no_match(self):
        check_noop(
            """\
            def test_something():
                page = "whatever"
                self.assertFormError(page, "form", "user", "woops")
            """,
            settings,
        )

    def test_assert_called_in_func_kw_default(self):
        check_noop(
            """\
            def f(n = self.assertFormError(page, "form", "user", "woops")):
                ...
            """,
            settings,
        )

    def test_basic(self):
        check_transformed(
            """\
            self.assertFormError(response, "form", "user", "woops")
            """,
            """\
            self.assertFormError(response.context["form"], "user", "woops")
            """,
            settings,
        )

    def test_basic_with_msg_prefix(self):
        check_transformed(
            """\
            self.assertFormError(response, "form", "user", "woops", "My form")
            """,
            """\
            self.assertFormError(response.context["form"], "user", "woops", "My form")
            """,
            settings,
        )

    def test_longer_name(self):
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
    def test_short_names(self, name):
        check_transformed(
            f"""\
            self.assertFormError({name}, "form", "user", "woops")
            """,
            f"""\
            self.assertFormError({name}.context["form"], "user", "woops")
            """,
            settings,
        )

    def test_response_from_client(self):
        check_transformed(
            """\
            def test_something():
                f()
                page = self.client.get()
                self.assertFormError(page, "form", "user", "woops")
            """,
            """\
            def test_something():
                f()
                page = self.client.get()
                self.assertFormError(page.context["form"], "user", "woops")
            """,
            settings,
        )

    def test_response_from_client_async(self):
        check_transformed(
            """\
            async def test_something():
                page = await self.async_client.get()
                self.assertFormError(page, "form", "user", "woops")
            """,
            """\
            async def test_something():
                page = await self.async_client.get()
                self.assertFormError(page.context["form"], "user", "woops")
            """,
            settings,
        )

    def test_response_from_gated_client_use(self):
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

    def test_response_from_context_manager_client_use(self):
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

    def test_form_name_var(self):
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

    def test_spaced_args(self):
        check_transformed(
            """\
            self.assertFormError( response , "form", "user", "woops")
            """,
            """\
            self.assertFormError( response.context["form"] , "user", "woops")
            """,
            settings,
        )

    def test_second_arg_end_of_line(self):
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

    def test_second_arg_end_of_line_no_space(self):
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

    def test_second_arg_own_line(self):
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

    def test_kwarg_errors(self):
        check_transformed(
            """\
            self.assertFormError(response, "form", "user", errors="woops")
            """,
            """\
            self.assertFormError(response.context["form"], "user", errors="woops")
            """,
            settings,
        )

    def test_kwarg_msg_prefix(self):
        check_transformed(
            """\
            self.assertFormError(
                response, "form", "user", "woops", msg_prefix="!!!"
            )
            """,
            """\
            self.assertFormError(
                response.context["form"], "user", "woops", msg_prefix="!!!"
            )
            """,
            settings,
        )

    def test_kwarg_errors_msg_prefix(self):
        check_transformed(
            """\
            self.assertFormError(
                response, "form", "user", errors="woops", msg_prefix="!!!"
            )
            """,
            """\
            self.assertFormError(
                response.context["form"], "user", errors="woops", msg_prefix="!!!"
            )
            """,
            settings,
        )

    def test_errors_none(self):
        check_transformed(
            """\
            self.assertFormError(response, "form", "user", None)
            """,
            """\
            self.assertFormError(response.context["form"], "user", [])
            """,
            settings,
        )

    def test_errors_none_kwarg(self):
        check_transformed(
            """\
            self.assertFormError(response, "form", "user", errors=None)
            """,
            """\
            self.assertFormError(response.context["form"], "user", errors=[])
            """,
            settings,
        )


class TestFormset:
    def test_new_signature(self):
        check_noop(
            """\
            self.assertFormsetError(formset, "user", 0, "woops")
            """,
            settings,
        )

    def test_new_signature_msg_prefix(self):
        check_noop(
            """\
            self.assertFormsetError(formset, "user", 0, "woops", "My form")
            """,
            settings,
        )

    def test_unsupported_basic_name(self):
        check_noop(
            """\
            self.assertFormsetError(page, formset, 0, "user", "woops")
            """,
            settings,
        )

    def test_bad_signature_too_many_args(self):
        check_noop(
            """\
            self.assertFormsetError(
                response, "formset", 0, "user", "woops", "!!!", None
            )
            """,
            settings,
        )

    def test_bad_signature_too_few_args(self):
        check_noop(
            """\
            self.assertFormsetError(response, "formset", 0)
            """,
            settings,
        )

    def test_bad_signature_bad_errors_kwarg(self):
        check_noop(
            """\
            self.assertFormsetError(response, "formset", 0, "user", err="woops")
            """,
            settings,
        )

    def test_bad_signature_bad_msg_prefix_kwarg(self):
        check_noop(
            """\
            self.assertFormsetError(response, "formset", 0, "user", "woops", msg="!!!")
            """,
            settings,
        )

    def test_response_from_unknown_client_method(self):
        check_noop(
            """\
            def test_something():
                page = self.client.poke()
                self.assertFormsetError(page, "formset", 0, "user", "woops")
            """,
            settings,
        )

    def test_response_from_custom_client_use(self):
        check_noop(
            """\
            def test_something():
                page = Client().get()
                self.assertFormsetError(page, "formset", 0, "user", "woops")
            """,
            settings,
        )

    def test_response_from_client_assigned_after(self):
        check_noop(
            """\
            def test_something():
                self.assertFormsetError(page, "formset", 0, "user", "woops")
                page = self.client.get()
            """,
            settings,
        )

    def test_response_from_client_inner_async_func(self):
        check_noop(
            """\
            def test_something():
                async def f():
                    page = self.client.get()
                self.assertFormsetError(page, "formset", 0, "user", "woops")
            """,
            settings,
        )

    def test_response_from_client_inner_func(self):
        check_noop(
            """\
            def test_something():
                def f():
                    page = self.client.get()
                self.assertFormsetError(page, "formset", 0, "user", "woops")
            """,
            settings,
        )

    def test_response_from_client_inner_class(self):
        check_noop(
            """\
            def test_something():
                class Wtf:
                    page = self.client.get()
                self.assertFormsetError(page, "formset", 0, "user", "woops")
            """,
            settings,
        )

    def test_response_from_client_no_match(self):
        check_noop(
            """\
            def test_something():
                page = "whatever"
                self.assertFormsetError(page, "formset", 0, "user", "woops")
            """,
            settings,
        )

    def test_assert_called_in_func_kw_default(self):
        check_noop(
            """\
            def f(n = self.assertFormsetError(page, "formset", 0, "user", "woops")):
                ...
            """,
            settings,
        )

    def test_basic(self):
        check_transformed(
            """\
            self.assertFormsetError(response, "formset", 0, "user", "woops")
            """,
            """\
            self.assertFormsetError(response.context["formset"], 0, "user", "woops")
            """,
            settings,
        )

    def test_basic_with_msg_prefix(self):
        check_transformed(
            """\
            self.assertFormsetError(
                response, "formset", 0, "user", "woops", "My form",
            )
            """,
            """\
            self.assertFormsetError(
                response.context["formset"], 0, "user", "woops", "My form",
            )
            """,
            settings,
        )

    def test_basic_with_none(self):
        check_transformed(
            """\
            self.assertFormsetError(
                response, "formset", 0, None, "woops"
            )
            """,
            """\
            self.assertFormsetError(
                response.context["formset"], 0, None, "woops"
            )
            """,
            settings,
        )

    def test_longer_name(self):
        check_transformed(
            """\
            self.assertFormsetError(
                page_response1, "formset", 0, "user", "woops"
            )
            """,
            """\
            self.assertFormsetError(
                page_response1.context["formset"], 0, "user", "woops"
            )
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
    def test_short_names(self, name):
        check_transformed(
            f"""\
            self.assertFormsetError({name}, "formset", 0, "user", "woops")
            """,
            f"""\
            self.assertFormsetError({name}.context["formset"], 0, "user", "woops")
            """,
            settings,
        )

    def test_response_from_client(self):
        check_transformed(
            """\
            def test_something():
                page = self.client.get()
                self.assertFormsetError(page, "formset", 0, "user", "woops")
            """,
            """\
            def test_something():
                page = self.client.get()
                self.assertFormsetError(page.context["formset"], 0, "user", "woops")
            """,
            settings,
        )

    def test_response_from_client_async(self):
        check_transformed(
            """\
            async def test_something():
                page = await self.async_client.get()
                self.assertFormsetError(page, "formset", 0, "user", "woops")
            """,
            """\
            async def test_something():
                page = await self.async_client.get()
                self.assertFormsetError(page.context["formset"], 0, "user", "woops")
            """,
            settings,
        )

    def test_response_from_gated_client_use(self):
        check_transformed(
            """\
            def test_something():
                if True:
                    page = self.client.get()
                self.assertFormsetError(page, "formset", 0, "user", "woops")
            """,
            """\
            def test_something():
                if True:
                    page = self.client.get()
                self.assertFormsetError(page.context["formset"], 0, "user", "woops")
            """,
            settings,
        )

    def test_response_from_context_manager_client_use(self):
        check_transformed(
            """\
            def test_something():
                with some_mock:
                    page = self.client.get()
                self.assertFormsetError(page, "formset", 0, "user", "woops")
            """,
            """\
            def test_something():
                with some_mock:
                    page = self.client.get()
                self.assertFormsetError(page.context["formset"], 0, "user", "woops")
            """,
            settings,
        )

    def test_form_name_var(self):
        check_transformed(
            """\
            setname = "magicform"
            self.assertFormsetError(response, setname, 0, "user", "woops")
            """,
            """\
            setname = "magicform"
            self.assertFormsetError(response.context[setname], 0, "user", "woops")
            """,
            settings,
        )

    def test_spaced_args(self):
        check_transformed(
            """\
            self.assertFormsetError( response , "formset", 0, "user", "woops")
            """,
            """\
            self.assertFormsetError( response.context["formset"] , 0, "user", "woops")
            """,
            settings,
        )

    def test_second_arg_end_of_line(self):
        check_transformed(
            """\
            self.assertFormsetError(response, "formset",
                0, "user", "woops")
            """,
            """\
            self.assertFormsetError(response.context["formset"],
                0, "user", "woops")
            """,
            settings,
        )

    def test_second_arg_end_of_line_no_space(self):
        check_transformed(
            """\
            self.assertFormsetError(response,"formset",
                0, "user", "woops")
            """,
            """\
            self.assertFormsetError(response.context["formset"],
                0, "user", "woops")
            """,
            settings,
        )

    def test_second_arg_own_line(self):
        check_transformed(
            """\
            self.assertFormsetError(
                response,
                "formset",
                0,
                "user",
                "woops",
            )
            """,
            """\
            self.assertFormsetError(
                response.context["formset"],
                0,
                "user",
                "woops",
            )
            """,
            settings,
        )

    def test_kwarg_errors(self):
        check_transformed(
            """\
            self.assertFormsetError(
                response, "formset", 0, "user", errors="woops"
            )
            """,
            """\
            self.assertFormsetError(
                response.context["formset"], 0, "user", errors="woops"
            )
            """,
            settings,
        )

    def test_kwarg_msg_prefix(self):
        check_transformed(
            """\
            self.assertFormsetError(
                response, "formset", 0, "user", "woops", msg_prefix="!!!"
            )
            """,
            """\
            self.assertFormsetError(
                response.context["formset"], 0, "user", "woops", msg_prefix="!!!"
            )
            """,
            settings,
        )

    def test_kwarg_errors_msg_prefix(self):
        check_transformed(
            """\
            self.assertFormsetError(
                response, "formset", 0, "user", errors="woops", msg_prefix="!!!"
            )
            """,
            """\
            self.assertFormsetError(
                response.context["formset"], 0, "user", errors="woops", msg_prefix="!!!"
            )
            """,
            settings,
        )

    def test_errors_none(self):
        check_transformed(
            """\
            self.assertFormsetError(response, "formset", 0, "user", None)
            """,
            """\
            self.assertFormsetError(response.context["formset"], 0, "user", [])
            """,
            settings,
        )

    def test_errors_none_kwarg(self):
        check_transformed(
            """\
            self.assertFormsetError(response, "formset", 0, "user", errors=None)
            """,
            """\
            self.assertFormsetError(response.context["formset"], 0, "user", errors=[])
            """,
            settings,
        )
