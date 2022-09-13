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


@fixer.register(ast.Module)
def visit_Module(
    state: State,
    node: ast.Module,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    yield from visit_Module_or_ClassDef(state, node, parent)


@fixer.register(ast.ClassDef)
def visit_ClassDef(
    state: State,
    node: ast.ClassDef,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    yield from visit_Module_or_ClassDef(state, node, parent)


# Map from old assigned names to new decorator names, which were changed to be
# shorter
ACTION_NAMES = {
    "short_description": "description",
    "allowed_permissions": "permissions",
}


class FunctionDetails:
    def __init__(self, node: ast.FunctionDef):
        self.node = node
        # Discovered attribute assignments to the given function
        self.assignments: dict[str, ast.Assign] = {}
        # Source strings for the values assigned to attributes, used in
        # adding the decorator
        self.values: dict[str, str] = {}


def visit_Module_or_ClassDef(
    state: State,
    node: ast.Module | ast.ClassDef,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    # Store potential action functions and details of the assigned attributes
    action_funcs: dict[str, FunctionDetails] = {}

    # Check for 'from django.contrib import admin' from state.from_imports,
    # but also directly when visiting a module. state.from_imports isn’t
    # populated yet when visiting a module... (could fix by doing two passes?)
    admin_imported = "admin" in state.from_imports["django.contrib"]

    for subnode in ast.iter_child_nodes(node):
        # coverage bug
        # https://github.com/nedbat/coveragepy/issues/1333
        if (  # pragma: no cover
            not admin_imported
            and isinstance(subnode, ast.ImportFrom)
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
            # TODO: check that no admin.action decorator already applied
        ):
            action_funcs[subnode.name] = FunctionDetails(subnode)
        elif (
            isinstance(subnode, ast.Assign)
            and len(subnode.targets) == 1
            and isinstance((target := subnode.targets[0]), ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id in action_funcs
            and target.attr in ACTION_NAMES
        ):
            new_name = ACTION_NAMES[target.attr]
            action_funcs[target.value.id].assignments[new_name] = subnode

    if not admin_imported:
        return

    for name, funcdetails in action_funcs.items():
        if funcdetails.assignments:
            yield ast_start_offset(funcdetails.node), partial(
                decorate_action_function, funcdetails=funcdetails
            )
            for name, assignnode in funcdetails.assignments.items():
                yield ast_start_offset(assignnode), partial(erase_node, node=assignnode)
                yield ast_start_offset(assignnode.value), partial(
                    store_value_src,
                    node=assignnode.value,
                    name=name,
                    funcdetails=funcdetails,
                )


def decorate_action_function(
    tokens: list[Token], i: int, *, funcdetails: FunctionDetails
) -> None:
    j, indent = extract_indent(tokens, i)
    dec_src = f"{indent}@admin.action(\n"
    for name in ACTION_NAMES.values():  # Use predefined order
        if name not in funcdetails.values:
            continue
        source = funcdetails.values[name]
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
    funcdetails: FunctionDetails,
) -> None:
    j = find_final_token(tokens, i, node=node)
    funcdetails.values[name] = tokens_to_src(tokens[i:j])
