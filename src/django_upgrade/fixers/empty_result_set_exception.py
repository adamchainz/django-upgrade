"""
Replace compatibility imports for django.core.exceptions.EmptyResultSet:
https://docs.djangoproject.com/en/3.1/releases/3.1/#id1
"""
import ast
from collections import defaultdict
from functools import partial
from typing import Iterable, List, Tuple

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import extract_indent, insert, update_imports

fixer = Fixer(
    __name__,
    min_version=(1, 11),
)

REWRITES = {
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
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        node.level == 0
        and node.module in REWRITES
        and any(alias.name in REWRITES[node.module] for alias in node.names)
    ):
        yield ast_start_offset(node), partial(fix_import, node=node)


def fix_import(tokens: List[Token], i: int, *, node: ast.ImportFrom) -> None:
    assert node.module is not None
    module_rewrites = REWRITES[node.module]
    imports_to_add = defaultdict(list)
    name_map = {}
    for alias in node.names:
        name = alias.name
        if name in module_rewrites:
            name_map[name] = ""
            imports_to_add[module_rewrites[name]].append(name)

    j, indent = extract_indent(tokens, i)
    update_imports(tokens, i, node=node, name_map=name_map)
    for module, names in reversed(imports_to_add.items()):
        joined_names = ", ".join(sorted(names))
        insert(tokens, j, new_src=f"{indent}from {module} import {joined_names}\n")
