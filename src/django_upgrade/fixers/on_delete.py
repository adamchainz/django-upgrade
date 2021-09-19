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
from django_upgrade.tokens import OP, find, insert, parse_call_args

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
        yield ast_start_offset(node), partial(
            add_on_delete_keyword, num_pos_args=len(node.args)
        )


def add_on_delete_keyword(tokens: List[Token], i: int, *, num_pos_args: int) -> None:
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, close_idx = parse_call_args(tokens, open_idx)

    new_src = "on_delete=models.CASCADE"
    if num_pos_args < len(func_args):
        new_src += ", "

    if num_pos_args == 0:
        insert_idx = open_idx + 1
    else:
        new_src = " " + new_src
        pos_start_idx, pos_end_idx = func_args[num_pos_args - 1]

        insert_idx = pos_end_idx + 1

        arg_has_comma = (
            tokens[pos_end_idx].name == OP and tokens[pos_end_idx].src == ","
        )
        if not arg_has_comma:
            new_src = "," + new_src
            insert_idx -= 1

    insert(tokens, insert_idx, new_src=new_src)
