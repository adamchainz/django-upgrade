"""
Remove the 'providing_args' argument from Signal():
https://docs.djangoproject.com/en/3.1/releases/3.1/#features-deprecated-in-3-1
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    CODE,
    OP,
    find,
    find_call_arg,
    parse_call_args,
    remove_call_arg,
)

fixer = Fixer(
    __name__,
    min_version=(3, 1),
)

MODULE = "django.dispatch"
NAME = "Signal"


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Name)
        and NAME in state.from_imports[MODULE]
        and node.func.id == NAME
    ) or (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == NAME
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "dispatch"
        and "dispatch" in state.from_imports["django"]
    ):
        arg: ast.expr | ast.keyword | None
        if len(node.args) > 0 and not isinstance(node.args[0], ast.Starred):
            arg = node.args[0]
            replace_with_none = len(node.args) > 1
        else:
            arg = next((k for k in node.keywords if k.arg == "providing_args"), None)
            replace_with_none = False

        if arg is not None:
            yield (
                ast_start_offset(node),
                partial(
                    remove_providing_args,
                    node=node,
                    arg=arg,
                    replace_with_none=replace_with_none,
                ),
            )


def remove_providing_args(
    tokens: list[Token],
    i: int,
    *,
    node: ast.Call,
    arg: ast.expr | ast.keyword,
    replace_with_none: bool,
) -> None:
    j = find(tokens, i, name=OP, src="(")
    func_args, _ = parse_call_args(tokens, j)
    start_idx, end_idx = find_call_arg(tokens, func_args, arg)

    if replace_with_none:
        tokens[start_idx:end_idx] = [Token(name=CODE, src="None")]
    else:
        remove_call_arg(tokens, start_idx, end_idx)
