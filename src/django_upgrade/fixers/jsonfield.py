"""
Replace JSONField imports:
https://docs.djangoproject.com/en/3.1/releases/3.1/#features-deprecated-in-3-1
"""
import ast
from collections import defaultdict
from functools import partial
from typing import Iterable, List, Tuple

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import INDENT, insert, update_imports

fixer = Fixer(
    __name__,
    min_version=(3, 1),
)

REWRITES = {
    "django.contrib.postgres.fields": {
        "JSONField": "django.db.models",
        "KeyTextTransform": "django.db.models.fields.json",
        "KeyTransform": "django.db.models.fields.json",
    },
    "django.contrib.postgres.fields.jsonb": {
        "JSONField": "django.db.models",
        "KeyTextTransform": "django.db.models.fields.json",
        "KeyTransform": "django.db.models.fields.json",
    },
    "django.contrib.postgres.forms": {
        "JSONField": "django.forms",
    },
    "django.contrib.postgres.forms.jsonb": {
        "JSONField": "django.forms",
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

    update_imports(tokens, i, node=node, name_map=name_map)

    j = i
    if j > 0 and tokens[j - 1].name == INDENT:
        indent = tokens[j - 1].src
        j -= 1
    else:
        indent = ""

    for module, names in reversed(imports_to_add.items()):
        joined_names = ", ".join(sorted(names))
        insert(tokens, j, new_src=f"{indent}from {module} import {joined_names}\n")
