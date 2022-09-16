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
from django_upgrade.tokens import OP, erase_node, extract_indent, insert, reverse_find

fixer = Fixer(
    __name__,
    min_version=(1, 7),
)

# Keep track of classes that could be decorated with `@admin.register()`
# For each class name, store the associated model class names inferred from
# eligible `admin.site.register` calls.


class AdminDetails:
    def __init__(self, parent: ast.AST) -> None:
        self.parent = parent
        self.model_names: set[str] = set()


decorable_admins: MutableMapping[State, dict[str, AdminDetails]] = WeakKeyDictionary()


def _is_django_admin_imported(state: State) -> bool:
    return (
        "admin" in state.from_imports["django.contrib"]
        or "admin" in state.from_imports["django.contrib.gis"]
    )


@fixer.register(ast.ClassDef)
def visit_ClassDef(
    state: State,
    node: ast.ClassDef,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if _is_django_admin_imported(state) and not uses_full_super_in_init_or_new(node):
        decorable_admins.setdefault(state, {})[node.name] = AdminDetails(parents[-1])
        if not node.decorator_list:
            offset = ast_start_offset(node)
            decorated = False
        else:
            offset = ast_start_offset(node.decorator_list[0])
            decorated = True
        yield offset, partial(
            update_class_def,
            name=node.name,
            state=state,
            decorated=decorated,
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


def update_class_def(
    tokens: list[Token], i: int, *, name: str, state: State, decorated: bool
) -> None:
    admin_details = decorable_admins.get(state, {})[name]
    if not admin_details.model_names:
        return

    if decorated:
        i = reverse_find(tokens, i, name=OP, src="@")
    j, indent = extract_indent(tokens, i)
    joined_names = ", ".join(sorted(admin_details.model_names))
    new_src = f"{indent}@admin.register({joined_names})\n"
    insert(tokens, j, new_src=new_src)


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        _is_django_admin_imported(state)
        and isinstance(parents[-1], ast.Expr)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "register"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "site"
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "admin"
    ):
        if (  # admin.site.register(MyModel, MyCustomAdmin)
            len(node.args) == 2
            and isinstance((model_arg := node.args[0]), ast.Name)
            and isinstance((admin_arg := node.args[1]), ast.Name)
            and not node.keywords
        ) or (  # admin.site.register(MyModel, admin_class=MyCustomAdmin)
            len(node.args) == 1
            and isinstance((model_arg := node.args[0]), ast.Name)
            and len(node.keywords) == 1
            and node.keywords[0].arg == "admin_class"
            and isinstance((admin_arg := node.keywords[0].value), ast.Name)
        ):
            model_names = {model_arg.id}

        elif (  # admin.site.register((MyModel1, MyModel2), MyCustomAdmin)
            len(node.args) == 2
            and isinstance((model_tuple := node.args[0]), (ast.Tuple, ast.List))
            and all(isinstance(elt, ast.Name) for elt in model_tuple.elts)
            and isinstance((admin_arg := node.args[1]), ast.Name)
            and not node.keywords
        ):
            model_names = {
                elt.id for elt in model_tuple.elts if isinstance(elt, ast.Name)
            }

        else:
            return

        admin_name = admin_arg.id
        admin_details = decorable_admins.get(state, {}).get(admin_name, None)

        if admin_details is not None and admin_details.parent == parents[-2]:
            admin_details.model_names.update(model_names)
            yield ast_start_offset(node), partial(erase_node, node=parents[-1])
