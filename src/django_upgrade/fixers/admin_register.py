"""
Replace `admin.site.register` with the new `@register` decorator syntax:
https://docs.djangoproject.com/en/stable/releases/1.7/#minor-features
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable, MutableMapping
from weakref import WeakKeyDictionary

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import erase_node, extract_indent, insert

fixer = Fixer(
    __name__,
    min_version=(1, 7),
)

# Keep track of classes that could be decorated with `@admin.register()`
# For each class name, store the associated custom ModelAdmin class
# inferred from eligible `admin.site.register` calls.
decorable_admins: MutableMapping[State, dict[str, set[str]]] = WeakKeyDictionary()


@fixer.register(ast.ClassDef)
def visit_ClassDef(
    state: State,
    node: ast.ClassDef,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        "admin" in state.from_imports["django.contrib"]
        and not node.decorator_list
        and not uses_full_super_in_init_or_new(node)
    ):
        decorable_admins.setdefault(state, {})[node.name] = set()
        yield ast_start_offset(node), partial(
            update_class_def,
            name=node.name,
            state=state,
        )


class FullSuperVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.found_full_super = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name in ("__init__", "__new__"):
            for subnode in ast.walk(node):
                if (
                    isinstance(subnode, ast.Call)
                    and isinstance(subnode.func, ast.Name)
                    and subnode.func.id == "super"
                    and len(subnode.args) == 2
                ):
                    self.found_full_super = True


def uses_full_super_in_init_or_new(node: ast.ClassDef) -> bool:
    """
    We cannot convert classes using py2 style `super(MyAdmin, self)`
    in the `__init__` or `__new__` method.
    https://docs.djangoproject.com/en/stable/ref/contrib/admin/#the-register-decorator
    """
    visitor = FullSuperVisitor()
    visitor.visit(node)
    return visitor.found_full_super


def update_class_def(tokens: list[Token], i: int, *, name: str, state: State) -> None:
    model_names = decorable_admins.get(state, {}).pop(name, set())
    if len(model_names) == 1:
        j, indent = extract_indent(tokens, i)
        insert(
            tokens,
            j,
            new_src=f"{indent}@admin.register({model_names.pop()})\n",
        )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        "admin" in state.from_imports["django.contrib"]
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "register"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "site"
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "admin"
        and not node.keywords
        and (
            len(node.args) == 2
            and isinstance(node.args[0], ast.Name)
            and isinstance(node.args[1], ast.Name)
        )
    ):
        admin_name = node.args[1].id
        to_decorate = decorable_admins.get(state, {})
        if admin_name in to_decorate:
            model_name = node.args[0].id
            to_decorate[admin_name].add(model_name)
            yield ast_start_offset(node), partial(
                erase_register_node,
                node=parent,
                admin_name=admin_name,
                state=state,
            )


def erase_register_node(
    tokens: list[Token], i: int, *, node: ast.Call, admin_name: str, state: State
) -> None:
    model_names = decorable_admins.get(state, {}).get(admin_name, set())
    if len(model_names) == 1:
        erase_node(tokens, i, node=node)
