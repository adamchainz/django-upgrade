"""
USE_L10N setting is deprecated:
https://docs.djangoproject.com/en/4.0/releases/4.0/#localization
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import erase_node

fixer = Fixer(
    __name__,
    min_version=(4, 0),
    condition=lambda state: state.looks_like_settings_file,
)


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "USE_L10N"
        and isinstance(node.value, ast.Constant)
        and node.value.value is True
        and (
            isinstance(parents[-1], ast.Module)
            or (
                isinstance(parents[-1], ast.ClassDef)
                and isinstance(parents[-2], ast.Module)
            )
        )
    ):
        yield ast_start_offset(node), partial(erase_node, node=node)
