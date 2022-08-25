"""
Update functions with admin attributes attached to use the new decorator forms:

https://docs.djangoproject.com/en/3.2/ref/contrib/admin/actions/#django.contrib.admin.action
https://docs.djangoproject.com/en/3.2/ref/contrib/admin/#django.contrib.admin.display
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable, MutableMapping
from weakref import WeakKeyDictionary

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import extract_indent, insert

fixer = Fixer(
    __name__,
    min_version=(2, 0),
)


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        len(node.targets) == 1
        and isinstance(node.targets[0], ast.Attribute)
        and isinstance(node.targets[0].value, ast.Name)
        and node.targets[0].attr == "short_description"
        and isinstance(parent, (ast.Module, ast.ClassDef, ast.FunctionDef))
    ):
        assigned_name = node.targets[0].value.id
        funcnode: ast.FunctionDef | None = None
        for subnode in parent.body:
            # must be before
            if subnode == node:
                break

            if isinstance(subnode, ast.FunctionDef) and subnode.name == assigned_name:
                funcnode = subnode

        if funcnode is not None:
            func_map = attrs_to_add.setdefault(state, {})
            if funcnode not in func_map:
                attrs: dict[str, ast.AST] = {}
                func_map[funcnode] = attrs
                yield ast_start_offset(funcnode), partial(
                    decorate_action_function,
                    attrs=attrs,
                )
            else:
                attrs = func_map[funcnode]
            attrs["short_description"] = node.value


# Track which of path and re_path have been used for this current file
# Then when backtracking into an import statement, we can use the set of names
# to determine what names to import.
attrs_to_add: MutableMapping[
    State, dict[ast.FunctionDef, dict[str, ast.AST]]
] = WeakKeyDictionary()


def decorate_action_function(
    tokens: list[Token], i: int, *, attrs: dict[str, ast.AST]
) -> None:
    j, indent = extract_indent(tokens, i)
    dec_src = f"{indent}@admin.action(\n"
    dec_src += f"{indent}    description='yada'\n"
    dec_src += f"{indent})\n"
    insert(tokens, j, new_src=dec_src)
