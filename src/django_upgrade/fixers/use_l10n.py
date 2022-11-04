"""
USE_L10N setting is deprecated:
https://docs.djangoproject.com/en/4.0/releases/4.0/#localization
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
    min_version=(4, 0),
)


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
        and node.targets[0].id == "USE_L10N"
        and isinstance(node.value, ast.Constant)
        and node.value.value is True
        and isinstance(parents[-1], ast.Module)
    ):
        yield ast_start_offset(node), partial(erase_node, node=node)
