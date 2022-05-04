"""
Remove default_app_config:
https://docs.djangoproject.com/en/stable/releases/3.2/#features-deprecated-in-3-2
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import LOGICAL_NEWLINE, find

fixer = Fixer(
    __name__,
    min_version=(3, 2),
)


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        state.looks_like_dunder_init_file()
        and isinstance(parent, ast.Module)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "default_app_config"
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ):
        yield ast_start_offset(node), partial(remove_assignment, node=node)


def remove_assignment(tokens: list[Token], i: int, *, node: ast.Assign) -> None:
    j = find(tokens, i, name=LOGICAL_NEWLINE)
    tokens[i : j + 1] = []
