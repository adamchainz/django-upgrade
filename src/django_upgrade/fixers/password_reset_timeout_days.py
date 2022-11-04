"""
PASSWORD_RESET_TIMEOUT_DAYS setting replaced with PASSWORD_RESET_TIMEOUT:
https://docs.djangoproject.com/en/3.1/releases/3.1/#django-contrib-auth
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import CODE
from django_upgrade.tokens import find
from django_upgrade.tokens import OP

fixer = Fixer(
    __name__,
    min_version=(3, 1),
)

OLD_NAME = "PASSWORD_RESET_TIMEOUT_DAYS"
NEW_NAME = "PASSWORD_RESET_TIMEOUT"


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        state.looks_like_settings_file
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == OLD_NAME
    ):
        yield ast_start_offset(node), partial(rewrite_setting, node=node)


def rewrite_setting(tokens: list[Token], i: int, *, node: ast.Assign) -> None:
    tokens[i] = tokens[i]._replace(name=CODE, src=NEW_NAME)
    j = find(tokens, i, name=OP, src="=")
    tokens.insert(j + 1, Token(name=CODE, src=" 60 * 60 * 24 *"))
