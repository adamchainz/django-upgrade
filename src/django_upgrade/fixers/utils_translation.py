"""
Replace imports from django.utils.translation:
https://docs.djangoproject.com/en/3.0/releases/3.0/#features-deprecated-in-3-0
"""
import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import find_and_replace_name, update_import_names

fixer = Fixer(
    __name__,
    min_version=(3, 0),
)

MODULE = "django.utils.translation"
NAME_MAP = {
    "ugettext": "gettext",
    "ugettext_lazy": "gettext_lazy",
    "ugettext_noop": "gettext_noop",
    "ungettext": "ngettext",
    "ungettext_lazy": "ngettext_lazy",
}


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        node.module == MODULE
        and is_rewritable_import_from(node)
        and any(alias.name in NAME_MAP for alias in node.names)
    ):
        yield ast_start_offset(node), partial(
            update_import_names, node=node, name_map=NAME_MAP
        )


@fixer.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (name := node.id) in NAME_MAP and name in state.from_imports[MODULE]:
        yield ast_start_offset(node), partial(
            find_and_replace_name, name=name, new=NAME_MAP[name]
        )


@fixer.register(ast.Attribute)
def visit_Attribute(
    state: State,
    node: ast.Attribute,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        (name := node.attr) in NAME_MAP
        and isinstance(node.value, ast.Name)
        and node.value.id == "translation"
        and "translation" in state.from_imports["django.utils"]
    ):
        yield ast_start_offset(node), partial(
            find_and_replace_name, name=name, new=NAME_MAP[name]
        )
