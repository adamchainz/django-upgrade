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

# Map function names to their positional parameter names
EMAIL_FUNCTION_ARGS = {
    "send_mail": ["subject", "message", "from_email", "recipient_list"],
    "send_mass_mail": ["datatuple"],
    "mail_admins": ["subject", "message"],
    "mail_managers": ["subject", "message"],
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
        and node.func.id in EMAIL_FUNCTION_ARGS
        and node.func.id in state.from_imports[MODULE]
    ):
        func_name = node.func.id
    # Check for module import: from django.core import mail; mail.send_mail(...)
    elif (
        isinstance(node.func, ast.Attribute)
        and node.func.attr in EMAIL_FUNCTION_ARGS
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "mail"
        and "mail" in state.from_imports["django.core"]
    ):
        func_name = node.func.attr
    
    if (
        func_name is not None
        and len(node.args) > 0  # Has positional arguments
        and len(node.args) <= len(EMAIL_FUNCTION_ARGS[func_name])  # Not more than expected
    ):
        yield (
            ast_start_offset(node),
            partial(
                convert_positional_to_keyword,
                func_name=func_name,
                num_pos_args=len(node.args),
                num_keywords=len(node.keywords),
            ),
        )


def convert_positional_to_keyword(
    tokens: list[Token], 
    i: int, 
    *, 
    func_name: str, 
    num_pos_args: int,
    num_keywords: int,
) -> None:
    """
    Convert positional arguments to keyword arguments for email functions.
    """
    # Find the opening parenthesis
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, close_idx = parse_call_args(tokens, open_idx)
    
    # Get the parameter names for this function
    param_names = EMAIL_FUNCTION_ARGS[func_name]
    
    # Convert each positional argument to keyword argument, in reverse order
    # to avoid messing up indices as we insert tokens
    for pos_idx in reversed(range(num_pos_args)):
        if pos_idx >= len(param_names):
            continue
            
        arg_start, arg_end = func_args[pos_idx]
        param_name = param_names[pos_idx]
        
        # Find the first non-whitespace token in the argument range
        actual_arg_start = arg_start
        while (actual_arg_start < arg_end and 
               tokens[actual_arg_start].name in ("UNIMPORTANT_WS", "NL")):
            actual_arg_start += 1
        
        # Insert the parameter name before the actual argument
        tokens.insert(actual_arg_start, Token(name=CODE, src=f"{param_name}="))