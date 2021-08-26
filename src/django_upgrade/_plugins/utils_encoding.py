"""
Replace imports from django.utils.encoding:
https://docs.djangoproject.com/en/3.0/releases/3.0/#django-utils-encoding-force-text-and-smart-text  # noqa: B950
"""
import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade._ast_helpers import ast_start_offset
from django_upgrade._data import Plugin, State, TokenFunc
from django_upgrade._token_helpers import find_and_replace_name

plugin = Plugin(
    __name__,
    min_version=(3, 0),
)

NAMES = {
    "force_text": "force_str",
    "smart_text": "smart_str",
}


@plugin.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if node.level == 0 and node.module == "django.utils.encoding":
        for alias in node.names:
            name = alias.name
            if name in NAMES:
                yield ast_start_offset(node), partial(
                    find_and_replace_name, name=name, new=NAMES[name]
                )


@plugin.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    name = node.id
    if name in NAMES and name in state.from_imports["django.utils.encoding"]:
        yield ast_start_offset(node), partial(
            find_and_replace_name, name=name, new=NAMES[name]
        )
