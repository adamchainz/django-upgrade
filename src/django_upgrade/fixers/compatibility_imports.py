"""
- Replace compatibility imports for
    - `django.core.exceptions.EmptyResultSet`
    - `django.core.exceptions.FieldDoesNotExist`
    - `django.forms.utils.pretty_name`
    - `django.forms.boundfield.BoundField`
  See https://docs.djangoproject.com/en/3.1/releases/3.1/#id1

- Replace `JSONField` imports:
  See https://docs.djangoproject.com/en/3.1/releases/3.1/#features-deprecated-in-3-1

- Replace `django.utils.functional.lru_cache` with `functools.lru_cache`
  Undocumented change
"""
from __future__ import annotations

import ast
from collections import defaultdict
from functools import lru_cache
from functools import partial
from typing import Iterable

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_rewritable_import_from
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import update_import_modules

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)

REPLACE_EXACT = {
    (1, 9): {
        "django.forms.forms": {
            "pretty_name": "django.forms.utils",
            "BoundField": "django.forms.boundfield",
        },
    },
    (1, 11): {
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
    },
    (2, 0): {"django.utils.functional": {"lru_cache": "functools"}},
    (3, 1): {
        "django.contrib.postgres.forms": {
            "JSONField": "django.forms",
        },
        "django.contrib.postgres.forms.jsonb": {
            "JSONField": "django.forms",
        },
    },
}
REPLACE_EXACT_EXCEPT_MIGRATIONS = {
    (3, 1): {
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
    }
}


@lru_cache(maxsize=None)
def _for_version(
    version: tuple[int, int], looks_like_migrations_file: bool
) -> defaultdict[str, dict[str, str]]:

    exact: defaultdict[str, dict[str, str]] = defaultdict(dict)
    for ver, replace_exact in REPLACE_EXACT.items():
        if ver <= version:
            for old_module, rewrite in replace_exact.items():
                exact[old_module].update(rewrite)

    if not looks_like_migrations_file:
        for ver, replace_exact in REPLACE_EXACT_EXCEPT_MIGRATIONS.items():
            if ver <= version:
                for old_module, rewrite in replace_exact.items():
                    exact[old_module].update(rewrite)

    return exact


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if not is_rewritable_import_from(node) or node.module is None:
        return

    exact = _for_version(
        state.settings.target_version, state.looks_like_migrations_file
    )

    if node.module in exact and any(
        alias.name in exact[node.module] for alias in node.names
    ):
        yield ast_start_offset(node), partial(
            update_import_modules, node=node, module_rewrites=exact[node.module]
        )
