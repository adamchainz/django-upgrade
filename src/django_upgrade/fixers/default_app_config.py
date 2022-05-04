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
from django_upgrade.tokens import CODE, find_final_token

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
        state.filename == "__init__.py"
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "default_app_config"
    ):
        yield ast_start_offset(node), partial(remove_assignment, node=node)


def remove_assignment(tokens: list[Token], i: int, *, node: ast.Assign) -> None:
    j = find_final_token(tokens, i, node=node)
    tokens[i:j] = [Token(name=CODE, src="")]
