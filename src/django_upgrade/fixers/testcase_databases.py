"""
Replace declarations of database support in test cases:
https://docs.djangoproject.com/en/2.2/releases/2.2/#features-deprecated-in-2-2
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
    min_version=(2, 2),
)


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(parent, ast.ClassDef)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in ("allow_database_queries", "multi_db")
        and isinstance(node.value, ast.Constant)
        and (node.value.value is True or node.value.value is False)
        and state.looks_like_test_file()
    ):
        yield ast_start_offset(node), partial(
            replace_assignment, node=node, value=node.value.value
        )


def replace_assignment(
    tokens: list[Token], i: int, *, node: ast.Assign, value: bool
) -> None:
    print("???", value)
    new_src = "databases = "
    if value:
        new_src += '"__all__"'
    else:
        new_src += "[]"
    j = find_final_token(tokens, i, node=node)
    tokens[i:j] = [Token(name=CODE, src=new_src)]
