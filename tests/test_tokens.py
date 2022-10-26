from __future__ import annotations

import ast

import pytest
from tokenize_rt import Token, src_to_tokens, tokens_to_src

from django_upgrade.tokens import str_repr_matching, update_import_names


def tokenize_and_parse(source: str) -> tuple[list[Token], ast.Module]:
    return src_to_tokens(source), ast.parse(source)


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
