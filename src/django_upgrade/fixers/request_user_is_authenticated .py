"""
Update use of request.user.is_authenticated() to use request.user.is_authenticated
https://docs.djangoproject.com/en/1.10/releases/1.10/#using-user-is-authenticated-and-user-is-anonymous-as-methods
"""
from __future__ import annotations

import ast
import sys
from functools import partial
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import find
from django_upgrade.tokens import NAME
from django_upgrade.tokens import OP


fixer = Fixer(
    __name__,
    min_version=(1, 10),
)


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "is_authenticated"
        and is_request_user_or_self_request_user(node.func.value)
        and len(node.args) == 0
    ):
        yield (
            ast_start_offset(node),
            partial(rewrite_user_is_auth),
        )


def is_request_user_or_self_request_user(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "user"
        and (
            (isinstance(node.value, ast.Name) and node.value.id == "request")
            or (
                isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "self"
                and node.value.attr == "request"
            )
        )
    )


if sys.version_info >= (3, 9):

    def extract_constant(node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

else:

    def extract_constant(node: ast.AST) -> str | None:
        if (
            isinstance(node, ast.Index)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
        return None


def rewrite_user_is_auth(tokens: list[Token], i: int) -> None:
    j = find(tokens, i, name=NAME, src="is_authenticated")
    y = find(tokens, i, name=OP, src=")")
    del tokens[j + 1 : y + 1]
