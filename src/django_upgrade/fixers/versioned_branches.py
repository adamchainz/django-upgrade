"""
Drop branches for old Django versions like:
if django.VERSION >= (1, 8):
    ...
else:
    ...
"""
from __future__ import annotations

import ast
from typing import Iterable, cast

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


@fixer.register(ast.If)
def visit_If(
    state: State,
    node: ast.If,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.test, ast.Compare)
        and isinstance(left := node.test.left, ast.Attribute)
        and isinstance(left.value, ast.Name)
        and left.value.id == "django"
        and left.attr == "VERSION"
        and _is_valid_gt_tuple(node.test, state)
    ):
        yield ast_start_offset(node), _fix_block


def _is_valid_gt_tuple(test: ast.Compare, state: State) -> bool:
    if not (
        len(test.ops) == 1
        and isinstance(test.ops[0], ast.GtE)
        and isinstance(test.comparators[0], ast.Tuple)
        and len(test.comparators[0].elts) == 2
        and all(isinstance(n, ast.Num) for n in test.comparators[0].elts)
    ):
        return False

    nums = cast(tuple[ast.Num], test.comparators[0].elts)
    min_version = tuple(e.n for e in nums)
    return min_version <= state.settings.target_version


def _fix_block(tokens: list[Token], i: int) -> None:
    # TODO
    pass
