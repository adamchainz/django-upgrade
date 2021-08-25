"""
Rewrite django.core.paginator’s alias QuerySetPaginator of Paginator:
https://docs.djangoproject.com/en/2.2/releases/2.2/#features-deprecated-in-2-2
"""
import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade._ast_helpers import ast_to_offset
from django_upgrade._data import Plugin, State, TokenFunc
from django_upgrade._token_helpers import find_and_replace_name

plugin = Plugin(
    __name__,
    min_version=(2, 2),
)

MODULE = "django.core.paginator"
OLD_NAME = "QuerySetPaginator"
NEW_NAME = "Paginator"


@plugin.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if node.level == 0 and node.module == MODULE:
        for alias in node.names:
            name = alias.name
            if name == OLD_NAME:
                yield ast_to_offset(node), partial(
                    find_and_replace_name, name=OLD_NAME, new=NEW_NAME
                )


@plugin.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    name = node.id
    if name == OLD_NAME and name in state.from_imports[MODULE]:
        yield ast_to_offset(node), partial(
            find_and_replace_name, name=OLD_NAME, new=NEW_NAME
        )
