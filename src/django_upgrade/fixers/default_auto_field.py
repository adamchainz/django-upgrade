"""
Remove the DEFAULT_AUTO_FIELD setting or default_auto_field AppConfig attribute
if set to the new default of django.db.models.BigAutoField:
https://docs.djangoproject.com/en/6.0/releases/6.0/#default-auto-field-setting-now-defaults-to-bigautofield
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
    min_version=(6, 0),
    condition=(
        lambda state: state.looks_like_apps_file or state.looks_like_settings_file
    ),
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
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        and node.value.value == "django.db.models.BigAutoField"
        and (
            (
                state.looks_like_settings_file
                and node.targets[0].id == "DEFAULT_AUTO_FIELD"
                and (
                    isinstance(parents[-1], ast.Module)
                    or (
                        isinstance(parents[-1], ast.ClassDef)
                        and len(parents[-1].body) > 1
                        and isinstance(parents[-2], ast.Module)
                    )
                )
            )
            or (
                state.looks_like_apps_file
                and node.targets[0].id == "default_auto_field"
                and isinstance(parents[-1], ast.ClassDef)
                and len(parents[-1].body) > 1
                and isinstance(parents[-2], ast.Module)
            )
        )
    ):
        yield ast_start_offset(node), partial(erase_node, node=node)
