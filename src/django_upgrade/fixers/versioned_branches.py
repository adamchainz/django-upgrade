"""
Drop branches for old Django versions like:
if django.VERSION >= (1, 8):
    ...
else:
    ...
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial
from typing import Literal

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_passing_comparison
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import Block

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


@fixer.register(ast.If)
def visit_If(
    state: State,
    node: ast.If,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.test, ast.Compare)
        and (pass_fail := is_passing_comparison(node.test, state)) is not None
        and (
            # do not handle 'if ... elif ...'
            not node.orelse
            or not isinstance(node.orelse[0], ast.If)
        )
    ):
        yield ast_start_offset(node), partial(
            _fix_block,
            node=node,
            keep_branch=("first" if pass_fail == "pass" else "second"),
        )


def _fix_block(
    tokens: list[Token],
    i: int,
    *,
    node: ast.If,
    keep_branch: Literal["first", "second"],
) -> None:
    if tokens[i].src != "if":
        # do not handle 'elif'
        return

    if node.orelse:
        if_block, else_block = _find_if_else_block(tokens, i)
        if keep_branch == "first":
            if_block.dedent(tokens)
            del tokens[if_block.end : else_block.end]
            del tokens[if_block.start : if_block.block]
        else:
            else_block.dedent(tokens)
            del tokens[if_block.start : else_block.block]
    else:
        if_block = Block.find(tokens, i, trim_end=True)
        if keep_branch == "first":
            if_block.dedent(tokens)
            del tokens[if_block.start : if_block.block]
        else:
            del tokens[if_block.start : if_block.end]


def _find_if_else_block(tokens: list[Token], i: int) -> tuple[Block, Block]:
    if_block = Block.find(tokens, i)
    i = if_block.end
    while tokens[i].src != "else":  # pragma: no cover
        i += 1
    else_block = Block.find(tokens, i, trim_end=True)
    return if_block, else_block
