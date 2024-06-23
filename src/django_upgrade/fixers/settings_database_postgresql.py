"""
Update settings.DATABASES backend path 'django.db.backends.postgresql_psycopg2'
to the new 'django.db.backends.postgresql'.
https://docs.djangoproject.com/en/2.0/releases/2.0/#id1
"""

from __future__ import annotations

import ast
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import replace
from django_upgrade.tokens import str_repr_matching

fixer = Fixer(
    __name__,
    min_version=(1, 9),
    condition=lambda state: state.looks_like_settings_file,
)


@fixer.register(ast.Dict)
def visit_Dict(
    state: State,
    node: ast.Dict,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        len(parents) >= 2
        and isinstance(parents[-1], ast.Dict)
        and isinstance((db_setting := parents[-2]), ast.Assign)
        and len(db_setting.targets) == 1
        and isinstance(db_setting.targets[0], ast.Name)
        and db_setting.targets[0].id == "DATABASES"
        and any(
            (
                isinstance(key, ast.Constant)
                and key.value == "ENGINE"
                and isinstance(val, ast.Constant)
                and (target_node := val).value
                == "django.db.backends.postgresql_psycopg2"
            )
            for key, val in zip(node.keys, node.values)
        )
    ):
        yield ast_start_offset(target_node), replace_engine


def replace_engine(tokens: list[Token], i: int) -> None:
    src = str_repr_matching("django.db.backends.postgresql", match_quotes=tokens[i].src)
    replace(tokens, i, src=src)
