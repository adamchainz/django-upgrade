"""
Rewrite django.core.validator.EmailValidator arguments:
https://docs.djangoproject.com/en/3.2/releases/3.2/#features-deprecated-in-3-2
"""
import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade._ast_helpers import ast_start_offset
from django_upgrade._data import Plugin, State, TokenFunc
from django_upgrade._token_helpers import replace

plugin = Plugin(
    __name__,
    min_version=(3, 2),
)

MODULE = "django.core.validators"
NAME = "EmailValidator"
KWARGS = {
    "whitelist": "allowlist",
    "domain_whitelist": "domain_allowlist",
}


@plugin.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        NAME in state.from_imports[MODULE]
        and isinstance(node.func, ast.Name)
        and node.func.id == NAME
    ):
        for keyword in node.keywords:
            if keyword.arg in KWARGS:
                yield ast_start_offset(keyword), partial(
                    replace,
                    src=KWARGS[keyword.arg],
                )
