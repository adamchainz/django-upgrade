"""
Replace imports from django.utils.translation:
https://docs.djangoproject.com/en/3.0/releases/3.0/#features-deprecated-in-3-0
"""
import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import find_and_replace_name, insert, update_imports

fixer = Fixer(
    __name__,
    min_version=(3, 0),
)

MODULE = "django.utils.text"
OLD_NAME = "unescape_entities"
NAME_MAP = {
    "unescape_entities": "",
}


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        node.level == 0
        and node.module == MODULE
        and any(
            (alias.name == OLD_NAME and alias.asname is None) for alias in node.names
        )
    ):
        offset = ast_start_offset(node)
        yield offset, partial(update_imports, node=node, name_map={OLD_NAME: ""})
        yield offset, partial(insert, new_src="import html\n")


@fixer.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if node.id == OLD_NAME and OLD_NAME in state.from_imports[MODULE]:
        yield ast_start_offset(node), partial(
            find_and_replace_name, name=OLD_NAME, new="html.escape"
        )
