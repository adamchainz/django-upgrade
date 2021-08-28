"""
Rewrite django.core.validator.EmailValidator arguments:
https://docs.djangoproject.com/en/3.2/releases/3.2/#features-deprecated-in-3-2
"""
import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import replace_arguments

fixer = Fixer(
    __name__,
    min_version=(3, 2),
)

MODULE = "django.core.validators"
NAME = "EmailValidator"
KWARGS = {
    "whitelist": "allowlist",
    "domain_whitelist": "domain_allowlist",
}


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        NAME in state.from_imports[MODULE]
        and isinstance(node.func, ast.Name)
        and node.func.id == NAME
        and any(k.arg in KWARGS for k in node.keywords)
    ):
        yield ast_start_offset(node), partial(
            replace_arguments,
            node=node,
            arg_map=KWARGS,
        )
