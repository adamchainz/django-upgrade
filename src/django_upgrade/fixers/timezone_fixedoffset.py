"""
Rewrite django.utils.timezone.FixedOffset to datetime.timezone.
https://docs.djangoproject.com/en/2.2/releases/2.2/#features-deprecated-in-2-2
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    OP,
    extract_indent,
    find,
    find_call_arg,
    insert,
    parse_call_args,
    replace,
    update_import_names,
)

fixer = Fixer(
    __name__,
    min_version=(2, 2),
)

MODULE = "django.utils.timezone"
OLD_NAME = "FixedOffset"


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.module == MODULE
        and is_rewritable_import_from(node)
        and any(alias.name == OLD_NAME for alias in node.names)
    ):
        yield ast_start_offset(node), partial(fix_import_from, node=node)


def fix_import_from(tokens: list[Token], i: int, *, node: ast.ImportFrom) -> None:
    j, indent = extract_indent(tokens, i)
    update_import_names(tokens, i, node=node, name_map={OLD_NAME: ""})
    insert(tokens, j, new_src=f"{indent}from datetime import timedelta, timezone\n")


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        OLD_NAME in state.from_imports[MODULE]
        and isinstance(node.func, ast.Name)
        and node.func.id == OLD_NAME
    ):
        arg: ast.expr | ast.keyword | None
        if len(node.args) >= 1 and not isinstance(node.args[0], ast.Starred):
            arg = node.args[0]
        else:
            arg = next((k for k in node.keywords if k.arg == "offset"), None)

        if arg is not None:
            yield ast_start_offset(node), partial(fix_offset_arg, arg=arg)


def fix_offset_arg(
    tokens: list[Token],
    i: int,
    *,
    arg: ast.expr | ast.keyword,
) -> None:
    j = find(tokens, i, name=OP, src="(")
    func_args, _ = parse_call_args(tokens, j)
    start_idx, end_idx = find_call_arg(tokens, func_args, arg)

    insert(tokens, end_idx, new_src=")")
    if isinstance(arg, ast.keyword):
        equal_idx = find(tokens, start_idx, name=OP, src="=")
        insert(tokens, equal_idx + 1, new_src="timedelta(minutes=")
    else:
        insert(tokens, start_idx, new_src="timedelta(minutes=")

    replace(tokens, i, src="timezone")
