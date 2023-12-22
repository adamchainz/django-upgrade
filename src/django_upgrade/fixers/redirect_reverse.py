from __future__ import annotations

import ast
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import find
from django_upgrade.tokens import OP
from django_upgrade.tokens import parse_call_args

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Name)
        and node.func.id == "redirect"
        and len(node.args) == 1
        and (
            len(node.keywords) == 0
            or len(node.keywords) == 1
            and node.keywords[0].arg == "permanent"
        )
        and isinstance(node.args[0], ast.Call)
        and isinstance(node.args[0].func, ast.Name)
        and node.args[0].func.id == "reverse"
        and len(node.args[0].args) == 1
        and len(node.args[0].keywords) == 0
    ):
        yield ast_start_offset(node), remove_nested_reverse


def remove_nested_reverse(tokens: list[Token], i: int) -> None:
    redirect_open_idx = find(tokens, i, name=OP, src="(")
    func_args, _ = parse_call_args(tokens, redirect_open_idx)

    reverse_open_idx = find(tokens, func_args[0][0], name=OP, src="(")
    reverse_args, reverse_close_idx = parse_call_args(tokens, reverse_open_idx)

    del tokens[reverse_args[-1][1] : reverse_close_idx]
    del tokens[redirect_open_idx:reverse_open_idx]
