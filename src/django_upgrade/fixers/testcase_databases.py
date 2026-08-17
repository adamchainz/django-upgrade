"""
Replace declarations of database support in test cases:
https://docs.djangoproject.com/en/2.2/releases/2.2/#features-deprecated-in-2-2
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import CODE, find_last_token

fixer = Fixer(
    __name__,
    min_version=(2, 2),
    condition=lambda state: state.looks_like_test_file,
)


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(parents[-1], ast.ClassDef)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in ("allow_database_queries", "multi_db")
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, bool)
    ):
        if node.value.value:
            new_value = '"__all__"'
        elif node.targets[0].id == "multi_db":
            # multi_db = False meant the default database was still available
            new_value = '["default"]'
        else:
            new_value = "[]"
        yield (
            ast_start_offset(node),
            partial(replace_assignment, node=node, new_value=new_value),
        )


def replace_assignment(
    tokens: list[Token], i: int, *, node: ast.Assign, new_value: str
) -> None:
    j = find_last_token(tokens, i, node=node)
    tokens[i : j + 1] = [Token(name=CODE, src=f"databases = {new_value}")]
