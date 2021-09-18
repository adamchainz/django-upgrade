"""
Add on_delete=models.CASCADE to ForeignKey and OneToOneField:
https://docs.djangoproject.com/en/stable/releases/1.9/#features-deprecated-in-1-9
"""
import ast
from functools import partial
from typing import Iterable, List, Tuple

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import CODE, OP, find, parse_call_args

fixer = Fixer(
    __name__,
    min_version=(1, 9),
)


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr in {"ForeignKey", "OneToOneField"}
        and "models" in state.from_imports["django.db"]
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "models"
        and len(node.args) < 2
        and all(kw.arg != "on_delete" for kw in node.keywords)
    ):
        yield ast_start_offset(node), partial(add_on_delete_keyword)


def add_on_delete_keyword(tokens: List[Token], i: int) -> None:
    j = find(tokens, i, name=OP, src="(")
    func_args, j = parse_call_args(tokens, j)

    new_src = "on_delete=models.CASCADE"
    if len(func_args) > 0:
        new_src = " " + new_src
        final_start_idx, final_end_idx = func_args[-1]
        final_has_comma = any(
            t.name == OP and t.src == ","
            for t in tokens[final_start_idx : final_end_idx + 1]
        )
        if not final_has_comma:
            new_src = "," + new_src

    tokens.insert(j - 1, Token(name=CODE, src=new_src))
