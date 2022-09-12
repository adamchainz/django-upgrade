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
class_to_decorate: MutableMapping[State, dict[str, set[str]]] = WeakKeyDictionary()


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
        class_to_decorate.setdefault(state, {})[node.name] = set()
        yield ast_start_offset(node), partial(
            update_class_def,
            name=node.name,
            state=state,
        )


def uses_full_super_in_init_or_new(node: ast.ClassDef) -> bool:
    """
    We cannot convert classes using py2 style `super(MyAdmin, self)`
    in the `__init__` or `__new__` method.
    https://docs.djangoproject.com/en/stable/ref/contrib/admin/#the-register-decorator
    """
    for body_node in node.body:
        if isinstance(body_node, ast.FunctionDef) and body_node.name in {
            "__init__",
            "__new__",
        }:
            for target_node in ast.walk(body_node):
                if (
                    isinstance(target_node, ast.Attribute)
                    and target_node.attr in {"__init__", "__new__"}
                    and isinstance(target_node.value, ast.Call)
                    and isinstance(target_node.value.func, ast.Name)
                    and target_node.value.func.id == "super"
                    and len(target_node.value.args) == 2
                    and isinstance(target_node.value.args[0], ast.Name)
                    and isinstance(target_node.value.args[1], ast.Name)
                ):
                    return True
    return False


def update_class_def(tokens: list[Token], i: int, *, name: str, state: State) -> None:
    model_names = class_to_decorate.get(state, {}).pop(name, set())
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
        admin_model_name = node.args[1].id
        if admin_model_name in class_to_decorate.get(state, {}):
            class_to_decorate[state][admin_model_name].add(node.args[0].id)
            yield ast_start_offset(node), partial(
                erase_register_node,
                node=parent,
                admin_model_name=admin_model_name,
                state=state,
            )


def erase_register_node(
    tokens: list[Token], i: int, *, node: ast.Call, admin_model_name: str, state: State
) -> None:
    model_names = class_to_decorate.get(state, {}).get(admin_model_name, set())
    if len(model_names) == 1:
        erase_node(tokens, i, node=node)
