"""
USE_L10N setting is deprecated:
https://docs.djangoproject.com/en/4.0/releases/4.0/#localization
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
    min_version=(4, 0),
)


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "USE_L10N"
        and isinstance(node.value, ast.Constant)
        and node.value.value is True
        and state.looks_like_settings_file()
    ):
        yield ast_start_offset(node), partial(remove_assignment, node=node)


# TODO: copied from default_app_config.py - should we move this to a common
#  file to DRY out the code?
def remove_assignment(tokens: list[Token], i: int, *, node: ast.Assign) -> None:
    j = find(tokens, i, name=LOGICAL_NEWLINE)
    tokens[i : j + 1] = []
