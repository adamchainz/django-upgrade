"""
Convert positional arguments to keyword arguments for Django email APIs:
https://docs.djangoproject.com/en/6.0/releases/6.0/#positional-arguments-in-django-core-mail-apis
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import CODE, OP, find, parse_call_args

fixer = Fixer(
    __name__,
    min_version=(6, 0),
)

MODULE = "django.core.mail"

# Map function names to their allowed positional parameters count and keyword-only parameter names
EMAIL_FUNCTION_CONFIG = {
    "send_mail": {
        "max_positional": 4,  # subject, message, from_email, recipient_list
        "keyword_params": ["fail_silently", "auth_user", "auth_password", "connection", "html_message"]
    },
    "send_mass_mail": {
        "max_positional": 1,  # datatuple
        "keyword_params": ["fail_silently", "auth_user", "auth_password", "connection"]
    },
    "mail_admins": {
        "max_positional": 2,  # subject, message
        "keyword_params": ["fail_silently", "connection", "html_message"]
    },
    "mail_managers": {
        "max_positional": 2,  # subject, message
        "keyword_params": ["fail_silently", "connection", "html_message"]
    },
}


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    func_name = None
    
    # Check for direct import: from django.core.mail import send_mail
    if (
        isinstance(node.func, ast.Name)
        and node.func.id in EMAIL_FUNCTION_CONFIG
        and node.func.id in state.from_imports[MODULE]
    ):
        func_name = node.func.id
    # Check for module import: from django.core import mail; mail.send_mail(...)
    elif (
        isinstance(node.func, ast.Attribute)
        and node.func.attr in EMAIL_FUNCTION_CONFIG
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "mail"
        and "mail" in state.from_imports["django.core"]
    ):
        func_name = node.func.attr
    
    if func_name is not None:
        config = EMAIL_FUNCTION_CONFIG[func_name]
        num_positional_args = len(node.args)
        max_allowed_positional = config["max_positional"]
        
        # Only transform if there are more positional args than allowed
        if num_positional_args > max_allowed_positional:
            yield (
                ast_start_offset(node),
                partial(
                    convert_excess_positional_to_keyword,
                    func_name=func_name,
                    num_pos_args=num_positional_args,
                    max_allowed_positional=max_allowed_positional,
                ),
            )


def convert_excess_positional_to_keyword(
    tokens: list[Token], 
    i: int, 
    *, 
    func_name: str, 
    num_pos_args: int,
    max_allowed_positional: int,
) -> None:
    """
    Convert excess positional arguments to keyword arguments for email functions.
    Only converts arguments beyond the allowed positional count.
    """
    # Find the opening parenthesis
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, close_idx = parse_call_args(tokens, open_idx)
    
    # Get the configuration for this function
    config = EMAIL_FUNCTION_CONFIG[func_name]
    keyword_params = config["keyword_params"]
    
    # Convert excess positional arguments to keyword arguments, in reverse order
    # to avoid messing up indices as we insert tokens
    for pos_idx in reversed(range(max_allowed_positional, num_pos_args)):
        keyword_param_idx = pos_idx - max_allowed_positional
        if keyword_param_idx >= len(keyword_params):
            continue
            
        arg_start, arg_end = func_args[pos_idx]
        param_name = keyword_params[keyword_param_idx]
        
        # Find the first non-whitespace token in the argument range
        actual_arg_start = arg_start
        while (actual_arg_start < arg_end and 
               tokens[actual_arg_start].name in ("UNIMPORTANT_WS", "NL")):
            actual_arg_start += 1
        
        # Insert the parameter name before the actual argument
        tokens.insert(actual_arg_start, Token(name=CODE, src=f"{param_name}="))