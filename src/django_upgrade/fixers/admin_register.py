"""
Replace `admin.site.register` with the new `@register` decorator syntax:
https://docs.djangoproject.com/en/stable/releases/1.7/#minor-features
"""
from __future__ import annotations

import ast
from functools import partial
from typing import cast
from typing import Iterable
from typing import Literal
from typing import MutableMapping
from weakref import WeakKeyDictionary

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import erase_node
from django_upgrade.tokens import extract_indent
from django_upgrade.tokens import insert
from django_upgrade.tokens import OP
from django_upgrade.tokens import reverse_find

fixer = Fixer(
    __name__,
    min_version=(1, 7),
)

# Keep track of classes that could be decorated with `@admin.register()`
# For each class name, store the associated model class names inferred from
# eligible `admin.site.register` calls.


class AdminDetails:
    __slots__ = ("parent", "model_names_per_site")

    def __init__(self, parent: ast.AST) -> None:
        self.parent = parent
        self.model_names_per_site: dict[str, set[str]] = {}


decorable_admins: MutableMapping[State, dict[str, AdminDetails]] = WeakKeyDictionary()
# Name of site to set of unregistered model names, or True if potentially all
# models have been unregistered
unregistered_site_models: MutableMapping[
    State, dict[str, set[str] | Literal[True]]
] = WeakKeyDictionary()


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


def uses_full_super_in_init_or_new(node: ast.ClassDef) -> bool:
    """
    We cannot convert classes using py2 style `super(MyAdmin, self)`
    in the `__init__` or `__new__` method.
    https://docs.djangoproject.com/en/stable/ref/contrib/admin/#the-register-decorator
    """
    visitor = FullSuperVisitor()
    visitor.generic_visit(node)
    return visitor.found_full_super


class FullSuperVisitor(ast.NodeVisitor):
    __slots__ = ("found_full_super",)

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

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        # Avoid descending into a new scope
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Avoid descending into a new scope
        return None


def update_class_def(
    tokens: list[Token], i: int, *, name: str, state: State, decorated: bool
) -> None:
    admin_details = decorable_admins.get(state, {})[name]
    if not admin_details.model_names_per_site:
        return

    if decorated:
        i = reverse_find(tokens, i, name=OP, src="@")
    j, indent = extract_indent(tokens, i)

    new_src = ""
    for custom_site, model_names in sorted(admin_details.model_names_per_site.items()):
        joined_names = ", ".join(sorted(model_names))
        custom_site_src = f", site={custom_site}" if custom_site else ""
        new_src += f"{indent}@admin.register({joined_names}{custom_site_src})\n"

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
    ):
        if (
            node.func.attr == "register"
            and (
                (  # admin.site.register(...)
                    isinstance(node.func.value, ast.Attribute)
                    and node.func.value.attr == "site"
                    and isinstance(node.func.value.value, ast.Name)
                    and node.func.value.value.id == "admin"
                    and (site_name := "") == ""  # force assign
                )
                or (  # custom_site.register(...)
                    state.looks_like_admin_file
                    and isinstance(node.func.value, ast.Name)
                    and (site_name := node.func.value.id).endswith("site")
                )
            )
            and (
                (
                    len(node.args) == 2
                    and len(node.keywords) == 0
                    and isinstance((admin_arg := node.args[1]), ast.Name)
                )
                or (
                    len(node.args) == 1
                    and len(node.keywords) == 1
                    and node.keywords[0].arg == "admin_class"
                    and isinstance((admin_arg := node.keywords[0].value), ast.Name)
                )
            )
            and (
                isinstance((first_arg := node.args[0]), ast.Name)
                or (
                    isinstance(first_arg, (ast.Tuple, ast.List))
                    and all(isinstance(elt, ast.Name) for elt in first_arg.elts)
                )
            )
        ):
            if isinstance(first_arg, ast.Name):
                model_names = {first_arg.id}
            else:
                # cast() could be removed by using TypeGuard func above
                model_names = {cast(ast.Name, elt).id for elt in first_arg.elts}
            admin_name = admin_arg.id
            admin_details = decorable_admins.get(state, {}).get(admin_name, None)
            unregistered_models = unregistered_site_models.get(state, {}).get(
                site_name, set()
            )
            if (
                unregistered_models is not True
                and not unregistered_models.intersection(model_names)
                and admin_details is not None
                and admin_details.parent == parents[-2]
                and not (site_name and not admin_name.endswith("Admin"))
            ):
                admin_details.model_names_per_site.setdefault(site_name, set()).update(
                    model_names
                )
                yield ast_start_offset(node), partial(erase_node, node=parents[-1])
        elif node.func.attr == "unregister" and (
            (  # admin.site.unregister(...)
                isinstance(node.func.value, ast.Attribute)
                and node.func.value.attr == "site"
                and isinstance(node.func.value.value, ast.Name)
                and node.func.value.value.id == "admin"
                and (site_name := "") == ""  # force assign
            )
            or (  # custom_site.unregister(...)
                state.looks_like_admin_file
                and isinstance(node.func.value, ast.Name)
                and (site_name := node.func.value.id).endswith("site")
            )
        ):
            # potentially all models unregistered, but in some cases we can
            # detect unregistered names
            unregistered_names: set[str] | Literal[True] = True
            if len(node.args) == 1:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Name):
                    unregistered_names = {first_arg.id}
                elif isinstance(first_arg, (ast.Tuple, ast.List)) and all(
                    isinstance(elt, ast.Name) for elt in first_arg.elts
                ):
                    # argument is a sequence of models
                    unregistered_names = {
                        cast(ast.Name, elt).id for elt in first_arg.elts
                    }

            state_details = unregistered_site_models.get(state, None)
            if state_details is None:
                state_details = {}
                unregistered_site_models[state] = state_details

            if unregistered_names is True:
                state_details[site_name] = True
            else:
                existing_names = state_details.get(site_name, None)
                if existing_names is None:
                    state_details[site_name] = unregistered_names
                elif existing_names is not True:
                    existing_names.update(unregistered_names)
