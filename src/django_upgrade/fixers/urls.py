"""
Replace django.conf.urls with django.urls
"""
import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import find_and_replace_name, update_import_modules

fixer = Fixer(
    __name__,
    min_version=(2, 2),
)

REWRITES = {
    "django.conf.urls": {
        "url": "django.urls",
        "include": "django.urls",
    },
}
MODULES = {
    "django.conf.urls",
    "django.urls",
}
NAME_MAP = {
    "url": "re_path",
}


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        node.level == 0
        and node.module in REWRITES
        and any(alias.name in REWRITES[node.module] for alias in node.names)
    ):
        yield ast_start_offset(node), partial(
            update_import_modules, node=node, module_rewrites=REWRITES[node.module]
        )


@fixer.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (name := node.id) in NAME_MAP and any(
        name in state.from_imports[m] for m in MODULES
    ):
        yield ast_start_offset(node), partial(
            find_and_replace_name, name=name, new=NAME_MAP[name]
        )
