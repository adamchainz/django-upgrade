"""
Rename 'email_backend' to 'using' in AdminEmailHandler LOGGING config:
https://docs.djangoproject.com/en/6.1/releases/6.1/#:~:text=email_backend%20argument
"""

from __future__ import annotations

import ast
from collections.abc import Iterable

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import str_repr_matching

fixer = Fixer(
    __name__,
    min_version=(6, 1),
    condition=lambda state: state.looks_like_settings_file,
)


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "LOGGING"
        and isinstance(node.value, ast.Dict)
        and (
            isinstance(parents[-1], ast.Module)
            or (
                isinstance(parents[-1], ast.ClassDef)
                and len(parents[-1].body) > 1
                and isinstance(parents[-2], ast.Module)
            )
        )
    ):
        for key_node in _find_handler_email_backend_keys(node.value):
            yield ast_start_offset(key_node), rename_email_backend_key


def _find_handler_email_backend_keys(
    logging_dict: ast.Dict,
) -> Iterable[ast.Constant]:
    """
    Follow LOGGING["handlers"][*] and yield the 'email_backend' key node for
    each handler dict that configures AdminEmailHandler with that argument.
    """
    handlers_dict = _get_dict_value(logging_dict, "handlers")
    if handlers_dict is None:
        return
    for handler_value in handlers_dict.values:
        if not isinstance(handler_value, ast.Dict):
            continue
        if not any(
            (
                isinstance(k, ast.Constant)
                and k.value == "class"
                and isinstance(v, ast.Constant)
                and v.value == "django.utils.log.AdminEmailHandler"
            )
            for k, v in zip(handler_value.keys, handler_value.values)
        ):
            continue
        for hkey in handler_value.keys:
            if isinstance(hkey, ast.Constant) and hkey.value == "email_backend":
                yield hkey


def _get_dict_value(node: ast.Dict, key: str) -> ast.Dict | None:
    """
    Return the value for a string-literal key in a dict literal, if it is
    itself a dict literal.
    """
    for k, v in zip(node.keys, node.values):
        if isinstance(k, ast.Constant) and k.value == key and isinstance(v, ast.Dict):
            return v
    return None


def rename_email_backend_key(tokens: list[Token], i: int) -> None:
    tokens[i] = tokens[i]._replace(
        src=str_repr_matching("using", match_quotes=tokens[i].src)
    )
