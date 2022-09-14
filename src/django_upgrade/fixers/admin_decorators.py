"""
Update functions with admin attributes attached to use the new decorator forms:

https://docs.djangoproject.com/en/3.2/ref/contrib/admin/actions/#django.contrib.admin.action
https://docs.djangoproject.com/en/3.2/ref/contrib/admin/#django.contrib.admin.display
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable, Literal

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
NAME_MAPS = {
    "action": {
        "short_description": "description",
        "allowed_permissions": "permissions",
    },
    "display": {
        "short_description": "description",
        "boolean": "boolean",
        "empty_value_display": "empty_value",
        "admin_order_field": "ordering",
    },
}


class FunctionDetails:
    def __init__(self, node: ast.FunctionDef, decorator: Literal["action", "display"]):
        self.node = node
        self.decorator = decorator
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
    # Potential action and display functions to details of assigned attributes
    funcs: dict[str, FunctionDetails] = {}

    # Display functions take one arg (the model instance), but will also take
    # self inside classes
    if isinstance(node, ast.Module):
        display_func_args = 1
    else:
        display_func_args = 2

    # Check for 'from django.contrib import admin' from state.from_imports,
    # but also directly when visiting a module. state.from_imports isn’t
    # populated yet when visiting a module... (could fix by doing two passes?)
    admin_imported = (
        "admin" in state.from_imports["django.contrib"]
        or "admin" in state.from_imports["django.contrib.gis"]
    )

    for subnode in ast.iter_child_nodes(node):
        # coverage bug
        # https://github.com/nedbat/coveragepy/issues/1333
        if (  # pragma: no cover
            not admin_imported
            and isinstance(subnode, ast.ImportFrom)
            and subnode.module in ("django.contrib", "django.contrib.gis")
            and any(
                alias.name == "admin" and alias.asname is None
                for alias in subnode.names
            )
        ):
            admin_imported = True
        elif isinstance(subnode, ast.FunctionDef):
            if (
                # Django calls action functions with exactly three arguments,
                # positionally (modeladmin, request, queryset)
                (len(subnode.args.posonlyargs) + len(subnode.args.args)) == 3
                and len(subnode.args.kwonlyargs) == 0
                # TODO: check that no admin.action decorator already applied
            ):
                funcs[subnode.name] = FunctionDetails(subnode, "action")
            elif (
                (len(subnode.args.posonlyargs) + len(subnode.args.args))
                == display_func_args
                and len(subnode.args.kwonlyargs) == 0
                # TODO: check that no admin.display decorator already applied
            ):
                funcs[subnode.name] = FunctionDetails(subnode, "display")
        elif (
            isinstance(subnode, ast.Assign)
            and len(subnode.targets) == 1
            and isinstance((target := subnode.targets[0]), ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id in funcs
            and target.attr in NAME_MAPS[funcs[target.value.id].decorator]
        ):
            names = NAME_MAPS[funcs[target.value.id].decorator]
            new_name = names[target.attr]
            funcs[target.value.id].assignments[new_name] = subnode

    if not admin_imported:
        return

    for name, funcdetails in funcs.items():
        if funcdetails.assignments:
            yield ast_start_offset(funcdetails.node), partial(
                decorate_function, funcdetails=funcdetails
            )
            for name, assignnode in funcdetails.assignments.items():
                yield ast_start_offset(assignnode), partial(erase_node, node=assignnode)
                yield ast_start_offset(assignnode.value), partial(
                    store_value_src,
                    node=assignnode.value,
                    name=name,
                    funcdetails=funcdetails,
                )


def decorate_function(
    tokens: list[Token], i: int, *, funcdetails: FunctionDetails
) -> None:
    j, indent = extract_indent(tokens, i)
    dec_src = f"{indent}@admin.{funcdetails.decorator}(\n"
    names = NAME_MAPS[funcdetails.decorator]
    for name in names.values():  # Use predefined order
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
