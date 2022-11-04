"""
Drop branches for old Django versions like:
if django.VERSION >= (1, 8):
    ...
else:
    ...
"""
from __future__ import annotations

import ast
from functools import partial
from typing import cast
from typing import Iterable
from typing import Literal

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
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
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.test, ast.Compare)
        and isinstance(left := node.test.left, ast.Attribute)
        and isinstance(left.value, ast.Name)
        and left.value.id == "django"
        and left.attr == "VERSION"
        and (keep_branch := _is_passing_comparison(node.test, state)) is not None
        and (
            # do not handle 'if ... elif ...'
            not node.orelse
            or not isinstance(node.orelse[0], ast.If)
        )
    ):
        yield ast_start_offset(node), partial(
            _fix_block, node=node, keep_branch=keep_branch
        )


def _is_passing_comparison(
    test: ast.Compare, state: State
) -> Literal["first", "second", None]:
    if not (
        len(test.ops) == 1
        and isinstance(test.ops[0], (ast.Gt, ast.GtE, ast.Lt, ast.LtE))
        and len(test.comparators) == 1
        and isinstance((comparator := test.comparators[0]), ast.Tuple)
        and len(comparator.elts) == 2
        and all(isinstance(e, ast.Num) for e in comparator.elts)
        and all(isinstance(cast(ast.Num, e).n, int) for e in comparator.elts)
    ):
        return None

    min_version = tuple(cast(ast.Num, e).n for e in comparator.elts)
    if isinstance(test.ops[0], ast.Gt):
        if state.settings.target_version > min_version:
            return "first"
    elif isinstance(test.ops[0], ast.GtE):
        if state.settings.target_version >= min_version:
            return "first"
    elif isinstance(test.ops[0], ast.Lt):
        if state.settings.target_version >= min_version:
            return "second"
    else:  # ast.LtE
        if state.settings.target_version > min_version:
            return "second"
    return None


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
        if_block = Block.find(tokens, i)
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
