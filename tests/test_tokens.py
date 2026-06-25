from __future__ import annotations

import ast

import pytest
from tokenize_rt import Token, src_to_tokens, tokens_to_src

from django_upgrade.tokens import (
    erase_def,
    find_call_arg,
    find_first_token,
    parse_call_args,
    remove_call_arg,
    replace_argument_names,
    str_repr_matching,
    update_import_names,
)


@pytest.mark.parametrize(
    "text,match_quotes,expected",
    (
        ("ball", "'bat'", "'ball'"),
        ("ball", '"bat"', '"ball"'),
        ("ball", 'r"bat"', '"ball"'),
        ("quote: 'hi'", "'bat'", "\"quote: 'hi'\""),
        ('quote: "hi"', "'bat'", "'quote: \"hi\"'"),
        ('quote: "hi"', '"bat"', '"quote: \\"hi\\""'),
    ),
)
def test_str_repr_matching(text, match_quotes, expected):
    assert str_repr_matching(text, match_quotes=match_quotes) == expected


def tokenize_and_parse(source: str) -> tuple[list[Token], ast.Module]:
    return src_to_tokens(source), ast.parse(source)


class TestRemoveCallArg:
    def check_transformed(self, *, before: str, arg_index: int, after: str) -> None:
        tokens, mod = tokenize_and_parse(before)
        expr = mod.body[0]
        assert isinstance(expr, ast.Expr)
        call = expr.value
        assert isinstance(call, ast.Call)

        open_paren = next(i for i, token in enumerate(tokens) if token.src == "(")
        func_args, _ = parse_call_args(tokens, open_paren)
        args: list[ast.expr | ast.keyword] = [*call.args, *call.keywords]
        start_idx, end_idx = find_call_arg(tokens, func_args, args[arg_index])
        remove_call_arg(tokens, start_idx, end_idx)

        assert tokens_to_src(tokens) == after

    def test_single_arg(self):
        self.check_transformed(before="f(old=1)\n", arg_index=0, after="f()\n")

    def test_first_arg(self):
        self.check_transformed(
            before="f(old=1, new=2)\n", arg_index=0, after="f(new=2)\n"
        )

    def test_last_arg(self):
        self.check_transformed(
            before="f(old=1, new=2)\n", arg_index=1, after="f(old=1)\n"
        )

    def test_first_multiline_arg(self):
        self.check_transformed(
            before="f(\n    old=1,\n    new=2,\n)\n",
            arg_index=0,
            after="f(\n    new=2,\n)\n",
        )

    def test_first_arg_with_inline_comment(self):
        self.check_transformed(
            before="f(\n    old=1,  # comment\n    new=2,\n)\n",
            arg_index=0,
            after="f(\n    new=2,\n)\n",
        )

    def test_first_arg_with_inline_comment_starting_on_same_line(self):
        self.check_transformed(
            before="f(old=1,  # comment\n    new=2)\n",
            arg_index=0,
            after="f(new=2)\n",
        )


class TestReplaceArgumentNames:
    def check_transformed(
        self, *, before: str, arg_map: dict[str, str], after: str
    ) -> None:
        tokens, mod = tokenize_and_parse(before)
        expr = mod.body[0]
        assert isinstance(expr, ast.Expr)
        call = expr.value
        assert isinstance(call, ast.Call)

        replace_argument_names(tokens, 0, node=call, arg_map=arg_map)

        assert tokens_to_src(tokens) == after

    def test_single_keyword(self):
        self.check_transformed(
            before="f(old=1)\n",
            arg_map={"old": "new"},
            after="f(new=1)\n",
        )

    def test_keyword_after_positional_argument(self):
        self.check_transformed(
            before="f(1, old=2)\n",
            arg_map={"old": "new"},
            after="f(1, new=2)\n",
        )

    def test_multiple_keywords(self):
        self.check_transformed(
            before="f(old=1, unchanged=2, older=3)\n",
            arg_map={"old": "new", "older": "newer"},
            after="f(new=1, unchanged=2, newer=3)\n",
        )

    def test_keyword_before_starred_argument(self):
        self.check_transformed(
            before="f(old=1, *args)\n",
            arg_map={"old": "new"},
            after="f(new=1, *args)\n",
        )

    def test_keyword_after_starred_argument(self):
        self.check_transformed(
            before="f(*args, old=1)\n",
            arg_map={"old": "new"},
            after="f(*args, new=1)\n",
        )

    def test_keyword_before_kwargs_unpacking(self):
        self.check_transformed(
            before="f(old=1, **kwargs)\n",
            arg_map={"old": "new"},
            after="f(new=1, **kwargs)\n",
        )

    def test_keyword_after_kwargs_unpacking(self):
        self.check_transformed(
            before="f(**kwargs, old=1)\n",
            arg_map={"old": "new"},
            after="f(**kwargs, new=1)\n",
        )

    def test_no_matching_keyword(self):
        self.check_transformed(
            before="f(old=1)\n",
            arg_map={"other": "new"},
            after="f(old=1)\n",
        )


class TestEraseDef:
    def check_transformed(
        self, *, before: str, after: str, node_index: int = 0
    ) -> None:
        tokens, mod = tokenize_and_parse(before)
        node = mod.body[node_index]
        assert isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef))
        i = find_first_token(tokens, 0, node=node.decorator_list[0])
        erase_def(tokens, i, node=node)
        assert tokens_to_src(tokens) == after

    def test_function(self):
        self.check_transformed(
            before="@dec\ndef foo():\n    pass\n",
            after="",
        )

    def test_two_decorators(self):
        self.check_transformed(
            before="@dec1\n@dec2\ndef foo():\n    pass\n",
            after="",
        )

    def test_preceding_statement(self):
        self.check_transformed(
            before="x = 1\n\n@dec\ndef foo():\n    pass\n",
            after="x = 1\n",
            node_index=1,
        )

    def test_async_function(self):
        self.check_transformed(
            before="@dec\nasync def foo():\n    pass\n",
            after="",
        )

    def test_class(self):
        self.check_transformed(
            before="@dec\nclass Foo:\n    pass\n",
            after="",
        )


class TestUpdateImportNames:
    def check_transformed(
        self, *, before: str, name_map: dict[str, str], after: str
    ) -> None:
        tokens, mod = tokenize_and_parse(before)
        node = mod.body[0]
        assert isinstance(node, ast.ImportFrom)
        update_import_names(tokens, 0, node=node, name_map=name_map)
        assert tokens_to_src(tokens) == after

    def test_rename_one(self):
        self.check_transformed(
            before="from a import b",
            name_map={"b": "c"},
            after="from a import c",
        )

    def test_rename_one_head(self):
        self.check_transformed(
            before="from a import b, c",
            name_map={"b": "d"},
            after="from a import d, c",
        )

    def test_rename_one_tail(self):
        self.check_transformed(
            before="from a import b, c",
            name_map={"c": "d"},
            after="from a import b, d",
        )

    def test_removing_one_head(self):
        self.check_transformed(
            before="from a import b, c",
            name_map={"b": ""},
            after="from a import c",
        )

    def test_removing_one_tail(self):
        self.check_transformed(
            before="from a import b, c",
            name_map={"c": ""},
            after="from a import b",
        )

    def test_removing_two_head(self):
        self.check_transformed(
            before="from a import b, c, d",
            name_map={"b": "", "c": ""},
            after="from a import d",
        )

    def test_removing_two_tail(self):
        self.check_transformed(
            before="from a import b, c, d",
            name_map={"c": "", "d": ""},
            after="from a import b",
        )

    def test_removing_one_as_head(self):
        self.check_transformed(
            before="from a import b as c, d",
            name_map={"b": ""},
            after="from a import d",
        )

    def test_removing_one_as_tail(self):
        self.check_transformed(
            before="from a import b, c as d",
            name_map={"c": ""},
            after="from a import b",
        )

    def test_removing_one_after_as(self):
        self.check_transformed(
            before="from a import b as c, d",
            name_map={"d": ""},
            after="from a import b as c",
        )

    def test_removing_one_before_as(self):
        self.check_transformed(
            before="from a import b, c as d",
            name_map={"b": ""},
            after="from a import c as d",
        )

    def test_removing_two_with_prior_comma(self):
        self.check_transformed(
            before="from a import b, c, d",
            name_map={"b": "", "c": ""},
            after="from a import d",
        )
