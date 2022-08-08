"""
Replace django.utils.timezone.utc with datetime.timezone.utc
https://docs.djangoproject.com/en/4.1/releases/4.1/#id2
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import update_import_modules

fixer = Fixer(
    __name__,
    min_version=(4, 1),
)

MODULE = "django.utils.timezone"
MODULE_REWRITES = {
    "utc": "datetime.timezone",
}


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.module == MODULE
        and is_rewritable_import_from(node)
        and any(alias.name == "utc" for alias in node.names)
    ):
        yield ast_start_offset(node), partial(
            update_import_modules,
            node=node,
            module_rewrites=MODULE_REWRITES,
        )
