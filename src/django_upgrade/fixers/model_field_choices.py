"""
Drop `.choices` for model field `choices` parameters:
https://docs.djangoproject.com/en/5.0/releases/5.0/#forms
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
from django_upgrade.tokens import OP
from django_upgrade.tokens import find_last_token
from django_upgrade.tokens import reverse_find

fixer = Fixer(
    __name__,
    min_version=(5, 0),
)


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        state.looks_like_models_file
        and (
            (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.attr.endswith("Field")
            )
            or (isinstance(node.func, ast.Name) and node.func.id.endswith("Field"))
        )
        and any(
            kw.arg == "choices"
            and isinstance(kw.value, ast.Attribute)
            and (target_node := kw.value).attr == "choices"
            for kw in node.keywords
        )
    ):
        yield ast_start_offset(target_node), partial(remove_choices, node=target_node)


def remove_choices(tokens: list[Token], i: int, node: ast.Attribute) -> None:
    j = find_last_token(tokens, i, node=node)
    i = reverse_find(tokens, j, name=OP, src=".")
    del tokens[i : j + 1]
