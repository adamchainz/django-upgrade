"""
Add the 'length' argument to get_random_string():
https://docs.djangoproject.com/en/3.1/releases/3.1/#features-deprecated-in-3-1
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
from django_upgrade.tokens import OP
from django_upgrade.tokens import find

fixer = Fixer(
    __name__,
    min_version=(3, 1),
)

MODULE = "django.utils.crypto"
NAME = "get_random_string"


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        (
            (
                isinstance(node.func, ast.Name)
                and NAME in state.from_imports[MODULE]
                and node.func.id == NAME
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == NAME
                and "crypto" in state.from_imports["django.utils"]
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "crypto"
            )
        )
        and len(node.args) == 0
        and not any(k.arg == "length" for k in node.keywords)
    ):
        yield ast_start_offset(node), partial(
            add_length_argument,
            has_kwargs=(len(node.keywords) > 0),
        )


def add_length_argument(tokens: list[Token], i: int, *, has_kwargs: bool) -> None:
    j = find(tokens, i, name=OP, src="(")
    new_src = "length=12"
    if has_kwargs:
        new_src += ", "
    tokens.insert(j + 1, Token(name=CODE, src=new_src))
