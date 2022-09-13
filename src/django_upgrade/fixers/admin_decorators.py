"""
Update functions with admin attributes attached to use the new decorator forms:

https://docs.djangoproject.com/en/3.2/ref/contrib/admin/actions/#django.contrib.admin.action
https://docs.djangoproject.com/en/3.2/ref/contrib/admin/#django.contrib.admin.display
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset, Token, tokens_to_src

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import erase_node, extract_indent, find_final_token, insert

fixer = Fixer(
    __name__,
    min_version=(3, 2),
)

# Map from old assigned names to new decorator names, which were changed to be
# shorter
ACTION_NAMES = {
    "short_description": "description",
    "allowed_permissions": "permissions",
}


@fixer.register(ast.Module)
def visit_Module(
    state: State,
    node: ast.Module,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    # Store potential action functions, by name, keeping also their ast node
    # and a dict of attributes. The attributes are initially the ast.Assign
    # nodes that can be moved into the decorator, replaced with the source of
    # the attribute value during the token modification phase
    action_funcs: dict[str, tuple[ast.FunctionDef, dict[str, ast.Assign | str]]] = {}

    # Check for 'from django.contrib import admin'
    # We cannot use state.from_imports within a visit_Module since it's not
    # at all populated yet... (could fix by doing two passes?)
    admin_imported = False

    for subnode in ast.iter_child_nodes(node):
        if (
            isinstance(subnode, ast.ImportFrom)
            and subnode.module == "django.contrib"
            and any(
                alias.name == "admin" and alias.asname is None
                for alias in subnode.names
            )
        ):
            admin_imported = True
        elif (
            isinstance(subnode, ast.FunctionDef)
            # Django calls action functions with exactly three arguments,
            # positionally (modeladmin, request, queryset)
            and (len(subnode.args.posonlyargs) + len(subnode.args.args)) == 3
            and len(subnode.args.kwonlyargs) == 0
        ):
            action_funcs[subnode.name] = (subnode, {})
        elif (
            isinstance(subnode, ast.Assign)
            and len(subnode.targets) == 1
            and isinstance((target := subnode.targets[0]), ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id in action_funcs
            and target.attr in ACTION_NAMES
        ):
            new_name = ACTION_NAMES[target.attr]
            action_funcs[target.value.id][1][new_name] = subnode

    if not admin_imported:
        return

    for name, (funcnode, attrs) in action_funcs.items():
        if attrs:
            yield ast_start_offset(funcnode), partial(
                decorate_action_function, attrs=attrs
            )
            for name, assignnode in attrs.items():
                assert isinstance(assignnode, ast.Assign)
                yield ast_start_offset(assignnode), partial(erase_node, node=assignnode)
                yield ast_start_offset(assignnode.value), partial(
                    store_value_src,
                    node=assignnode.value,
                    name=name,
                    attrs=attrs,
                )


def decorate_action_function(
    tokens: list[Token], i: int, *, attrs: dict[str, ast.AST | str]
) -> None:
    j, indent = extract_indent(tokens, i)
    dec_src = f"{indent}@admin.action(\n"
    for name in ACTION_NAMES.values():  # Use predefined order
        if name not in attrs:
            continue
        source = attrs[name]
        assert isinstance(source, str)
        source = source.replace("\n", f"\n{indent}    ")
        dec_src += f"{indent}    {name}={source},\n"
    dec_src += f"{indent})\n"
    insert(tokens, j, new_src=dec_src)


def store_value_src(
    tokens: list[Token],
    i: int,
    *,
    node: ast.AST,
    name: str,
    attrs: dict[str, ast.AST | str],
) -> None:
    j = find_final_token(tokens, i, node=node)
    attrs[name] = tokens_to_src(tokens[i:j])
