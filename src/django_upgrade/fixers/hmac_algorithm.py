"""
Add an explicit ``algorithm`` to salted_hmac() and base64_hmac() calls:
https://docs.djangoproject.com/en/6.1/releases/6.1/#:~:text=The%20default%20value%20of%20the%20algorithm%20argument
"""

from __future__ import annotations

import ast
from collections.abc import Iterable

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import CODE, OP, find, parse_call_args

fixer = Fixer(
    __name__,
    min_version=(6, 1),
)

CRYPTO_MODULE = "django.utils.crypto"
SIGNING_MODULE = "django.core.signing"

# base64_hmac() takes algorithm as its fourth argument.
ALGORITHM_ARG_NUMBER = 4


@fixer.register(ast.Call, names=("salted_hmac",))
def visit_salted_hmac(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if matched_import(
        state, node, module=CRYPTO_MODULE, module_name="crypto"
    ) and not passes_algorithm(node):
        yield ast_start_offset(node), add_algorithm_keyword


@fixer.register(ast.Call, names=("base64_hmac",))
def visit_base64_hmac(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        matched_import(state, node, module=SIGNING_MODULE, module_name="signing")
        and not passes_algorithm(node)
        and len(node.args) < ALGORITHM_ARG_NUMBER
        # * unpacking may provide algorithm positionally
        and not any(isinstance(arg, ast.Starred) for arg in node.args)
    ):
        yield ast_start_offset(node), add_algorithm_keyword


def matched_import(
    state: State,
    node: ast.Call,
    *,
    module: str,
    module_name: str,
) -> bool:
    """
    Check the call targets a function imported from module, either directly, or
    through its module.
    """
    if isinstance(node.func, ast.Name):
        return node.func.id in state.from_imports[module]
    return (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == module_name
        and module_name in state.from_imports[module.rpartition(".")[0]]
    )


def passes_algorithm(node: ast.Call) -> bool:
    # algorithm may be hidden in ** unpacking
    return any(kw.arg in (None, "algorithm") for kw in node.keywords)


def add_algorithm_keyword(tokens: list[Token], i: int) -> None:
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, close_idx = parse_call_args(tokens, open_idx)

    new_src = 'algorithm="sha1"'
    if len(func_args) > 0:
        new_src = " " + new_src
        final_token = tokens[func_args[-1][1]]
        final_has_comma = final_token.name == OP and final_token.src == ","
        if not final_has_comma:
            new_src = "," + new_src

    tokens.insert(close_idx - 1, Token(name=CODE, src=new_src))
