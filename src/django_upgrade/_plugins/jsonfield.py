"""
Replace JSONField imports:
https://docs.djangoproject.com/en/3.1/releases/3.1/#features-deprecated-in-3-1
"""
import ast
from collections import defaultdict
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade._ast_helpers import ast_start_offset
from django_upgrade._data import Plugin, State, TokenFunc
from django_upgrade._token_helpers import insert, update_imports

plugin = Plugin(
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


@plugin.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if node.level == 0 and node.module in REWRITES:
        module_rewrites = REWRITES[node.module]
        imports_to_add = defaultdict(list)
        name_map = {}
        for alias in node.names:
            name = alias.name
            if name in module_rewrites:
                name_map[name] = ""
                imports_to_add[module_rewrites[name]].append(name)

        offset = ast_start_offset(node)
        yield offset, partial(update_imports, node=node, name_map=name_map)
        for module, names in reversed(imports_to_add.items()):
            joined_names = ", ".join(sorted(names))
            yield offset, partial(
                insert, new_src=f"from {module} import {joined_names}\n"
            )
