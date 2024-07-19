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
from typing import Mapping

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

REPLACEMENTS_EXACT = {
    (1, 7): {
        "django.contrib.admin": {
            "ACTION_CHECKBOX_NAME": "django.contrib.admin.helpers",
        },
        "django.template.base": {
            "BaseContext": "django.template.context",
            "Context": "django.template.context",
            "ContextPopException": "django.template.context",
            "RequestContext": "django.template.context",
        },
    },
    (1, 9): {
        "django.forms.forms": {
            "pretty_name": "django.forms.utils",
            "BoundField": "django.forms.boundfield",
        },
        "django.forms.extras": {"SelectDateWidget": "django.forms.widgets"},
    },
    (1, 10): {
        "django.contrib.staticfiles.templatetags.staticfiles": {
            "static": "django.templatetags.static",
        },
        "django.core.urlresolvers": dict.fromkeys(
            # Objects moved from django.core.resolvers to django.urls in
            # Django 1.10:
            # https://github.com/django/django/blob/stable/1.10.x/django/urls/__init__.py
            # The following are excluded because they were removed in Django
            # 2.0: RegexURLPattern, LocaleRegexURLResolver, RegexURLResolver
            # and LocaleRegexProvider. See:
            # https://github.com/django/django/pull/7482#discussion_r121311884
            (
                "NoReverseMatch",
                "Resolver404",
                "ResolverMatch",
                "clear_script_prefix",
                "clear_url_caches",
                "get_callable",
                "get_mod_func",
                "get_ns_resolver",
                "get_resolver",
                "get_script_prefix",
                "get_urlconf",
                "is_valid_path",
                "resolve",
                "reverse",
                "reverse_lazy",
                "set_script_prefix",
                "set_urlconf",
                "translate_url",
            ),
            "django.urls",
        ),
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
        "django.test.runner": {"setup_databases": "django.test.utils"},
    },
    (2, 0): {
        "django.utils.functional": {"lru_cache": "functools"},
        "django.utils.decorators": {"ContextDecorator": "contextlib"},
    },
    (3, 1): {
        "django.contrib.postgres.forms": {
            "JSONField": "django.forms",
        },
        "django.contrib.postgres.forms.jsonb": {
            "JSONField": "django.forms",
        },
    },
    (4, 0): {
        "django.template.base": {
            "TRANSLATOR_COMMENT_MARK": "django.utils.translation.template"
        }
    },
}
REPLACEMENTS_EXCEPT_MIGRATIONS = {
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
def _get_replacements(
    version: tuple[int, int], looks_like_migrations_file: bool
) -> Mapping[str, dict[str, str]]:
    replacements: defaultdict[str, dict[str, str]] = defaultdict(dict)
    for target_version, target_replacements in REPLACEMENTS_EXACT.items():
        if target_version <= version:
            for old_module, rewrite in target_replacements.items():
                replacements[old_module].update(rewrite)

    if not looks_like_migrations_file:
        for (
            target_version,
            target_replacements,
        ) in REPLACEMENTS_EXCEPT_MIGRATIONS.items():
            if target_version <= version:
                for old_module, rewrite in target_replacements.items():
                    replacements[old_module].update(rewrite)

    replacements.default_factory = None
    return replacements


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if not is_rewritable_import_from(node) or node.module is None:
        return

    replacements = _get_replacements(
        state.settings.target_version, state.looks_like_migrations_file
    )

    if node.module in replacements and any(
        alias.name in replacements[node.module] for alias in node.names
    ):
        yield ast_start_offset(node), partial(
            update_import_modules,
            node=node,
            module_rewrites=replacements[node.module],
        )
