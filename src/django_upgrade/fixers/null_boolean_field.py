"""
Rewrite django.db.models.NullBooleanField to BooleanField:
https://docs.djangoproject.com/en/3.1/releases/3.1/#features-deprecated-in-3-1
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    CODE,
    OP,
    find,
    find_and_replace_name,
    parse_call_args,
    update_import_names,
)

fixer = Fixer(
    __name__,
    min_version=(3, 1),
)


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        is_rewritable_import_from(node)
        and node.module == "django.db.models"
        and not state.looks_like_migrations_file()
    ):
        yield ast_start_offset(node), partial(
            update_import_names,
            node=node,
            name_map={"NullBooleanField": "BooleanField"},
        )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        (
            isinstance(node.func, ast.Name)
            and "NullBooleanField" in state.from_imports["django.db.models"]
            and node.func.id == "NullBooleanField"
        )
        or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "NullBooleanField"
            and "models" in state.from_imports["django.db"]
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "models"
        )
    ) and not state.looks_like_migrations_file():
        yield ast_start_offset(node), partial(fix_null_boolean_field, node=node)


def fix_null_boolean_field(tokens: list[Token], i: int, *, node: ast.Call) -> None:
    if "null" not in [keyword.arg for keyword in node.keywords]:
        j = find(tokens, i, name=OP, src="(")
        func_args, j = parse_call_args(tokens, j)

        new_src = "null=True"
        if len(func_args) > 0:
            new_src = " " + new_src
            final_start_idx, final_end_idx = func_args[-1]
            final_has_comma = any(
                t.name == OP and t.src == ","
                for t in tokens[final_start_idx : final_end_idx + 1]
            )
            if not final_has_comma:
                new_src = "," + new_src

        tokens.insert(j - 1, Token(name=CODE, src=new_src))

    find_and_replace_name(tokens, i, name="NullBooleanField", new="BooleanField")
