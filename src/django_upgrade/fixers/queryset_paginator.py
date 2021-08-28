"""
Rewrite django.core.paginator’s alias QuerySetPaginator of Paginator:
https://docs.djangoproject.com/en/2.2/releases/2.2/#features-deprecated-in-2-2
"""
import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import find_and_replace_name, update_imports

fixer = Fixer(
    __name__,
    min_version=(2, 2),
)

MODULE = "django.core.paginator"
NAMES = {
    "QuerySetPaginator": "Paginator",
}


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if node.level != 0 or node.module != MODULE:
        return

    yield ast_start_offset(node), partial(update_imports, node=node, name_map=NAMES)


@fixer.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    name = node.id
    if name in NAMES and name in state.from_imports[MODULE]:
        yield ast_start_offset(node), partial(
            find_and_replace_name, name=name, new=NAMES[name]
        )
