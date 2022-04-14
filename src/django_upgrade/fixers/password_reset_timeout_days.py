"""
Replace imports from django.utils.encoding:
https://docs.djangoproject.com/en/3.0/releases/3.0/#django-utils-encoding-force-text-and-smart-text  # noqa: E501
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import CODE, OP, find

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
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == OLD_NAME
        and state.looks_like_settings_file()
    ):
        yield ast_start_offset(node), partial(rewrite_setting, node=node)


def rewrite_setting(tokens: list[Token], i: int, *, node: ast.Assign) -> None:
    tokens[i] = tokens[i]._replace(name=CODE, src=NEW_NAME)
    j = find(tokens, i, name=OP, src="=")
    tokens.insert(j + 1, Token(name=CODE, src=" 60 * 60 * 24 *"))
