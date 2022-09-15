"""
Replace compatibility imports for django.core.exceptions.EmptyResultSet:
https://docs.djangoproject.com/en/3.1/releases/3.1/#id1
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
    min_version=(1, 11),
)

REWRITES = {
    "django.db.models.fields": {
        "FieldDoesNotExist": "django.core.exceptions",
    },
    "django.db.models.query": {
        "EmptyResultSet": "django.core.exceptions",
    },
    "django.db.models.sql": {
        "EmptyResultSet": "django.core.exceptions",
    },
    "django.db.models.sql.datastructures": {
        "EmptyResultSet": "django.core.exceptions",
    },
}


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.module in REWRITES
        and is_rewritable_import_from(node)
        and any(alias.name in REWRITES[node.module] for alias in node.names)
    ):
        yield ast_start_offset(node), partial(
            update_import_modules, node=node, module_rewrites=REWRITES[node.module]
        )
