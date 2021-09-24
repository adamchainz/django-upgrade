"""
Replace django.utils.functional.lru_cache with functools.lru_cache
Undocumented change
"""
import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import update_import_modules

fixer = Fixer(
    __name__,
    min_version=(2, 0),
)

MODULE = "django.utils.functional"
MODULE_REWRITES = {
    "lru_cache": "functools",
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
        and any(alias.name == "lru_cache" for alias in node.names)
    ):
        yield ast_start_offset(node), partial(
            update_import_modules,
            node=node,
            module_rewrites={"lru_cache": "functools"},
        )
