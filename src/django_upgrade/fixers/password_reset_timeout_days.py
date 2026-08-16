"""
PASSWORD_RESET_TIMEOUT_DAYS setting replaced with PASSWORD_RESET_TIMEOUT:
https://docs.djangoproject.com/en/3.1/releases/3.1/#django-contrib-auth
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
    find_first_token,
    find_last_token,
    insert,
)

fixer = Fixer(
    __name__,
    min_version=(3, 1),
    condition=lambda state: state.looks_like_settings_file,
)

OLD_NAME = "PASSWORD_RESET_TIMEOUT_DAYS"
NEW_NAME = "PASSWORD_RESET_TIMEOUT"


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == OLD_NAME
    ):
        yield ast_start_offset(node), partial(rewrite_setting, node=node)


def rewrite_setting(tokens: list[Token], i: int, *, node: ast.Assign) -> None:
    tokens[i] = tokens[i]._replace(name=CODE, src=NEW_NAME)
    j = find(tokens, i, name=OP, src="=")
    if not isinstance(
        node.value, (ast.Attribute, ast.Call, ast.Constant, ast.Name, ast.Subscript)
    ):
        # Parenthesize values that may bind less tightly than '*'
        start = find_first_token(tokens, j, node=node.value)
        end = find_last_token(tokens, start, node=node.value)
        insert(tokens, end + 1, new_src=")")
        insert(tokens, start, new_src="(")
    tokens.insert(j + 1, Token(name=CODE, src=" 60 * 60 * 24 *"))
