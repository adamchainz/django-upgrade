"""
Drop lines that set `allow_tags` to `True` on functions.

https://docs.djangoproject.com/en/2.0/releases/2.0/#features-removed-in-2-0
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import erase_node

fixer = Fixer(
    __name__,
    min_version=(2, 0),
)


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        (
            "admin" in state.from_imports["django.contrib"]
            or "admin" in state.from_imports["django.contrib.gis"]
        )
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Attribute)
        and node.targets[0].attr == "allow_tags"
        and isinstance(node.value, ast.Constant)
        and node.value.value is True
    ):
        yield ast_start_offset(node), partial(erase_node, node=node)
