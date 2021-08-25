import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade._ast_helpers import ast_to_offset
from django_upgrade._data import State, TokenFunc, register
from django_upgrade._token_helpers import find_and_replace_name, replace_name

NAMES = {"force_text": "force_str", "smart_text": "smart_str"}


@register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if node.level == 0 and node.module == "django.utils.encoding":
        for alias in node.names:
            name = alias.name
            if name in NAMES and alias.asname is None:
                yield ast_to_offset(node), partial(
                    find_and_replace_name, name=name, new=NAMES[name]
                )


@register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    name = node.id
    if name in NAMES and name in state.from_imports["django.utils.encoding"]:
        new = NAMES[name]

        func = partial(replace_name, name=name, new=new)
        yield ast_to_offset(node), func
