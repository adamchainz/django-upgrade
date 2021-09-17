"""
Replace compatibility imports for django.core.exceptions.EmptyResultSet:
https://docs.djangoproject.com/en/3.1/releases/3.1/#id1
"""
import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import update_import_modules

fixer = Fixer(
    __name__,
    min_version=(1, 9),
)

REWRITES = {
    "django.forms.forms": {
        "pretty_name": "django.forms.utils",
        "BoundField": "django.forms.boundfield",
    },
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
