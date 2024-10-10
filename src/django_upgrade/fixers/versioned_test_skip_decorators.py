from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_passing_comparison
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import OP
from django_upgrade.tokens import erase_node
from django_upgrade.tokens import reverse_find

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


@fixer.register(ast.FunctionDef)
def visit_FunctionDef(
    state: State,
    node: ast.FunctionDef,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    for decorator in node.decorator_list:
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "unittest"
            and decorator.func.attr in ("skipIf", "skipUnless")
            and len(decorator.args) == 2
            and isinstance(decorator.args[0], ast.Compare)
            and (
                (pass_fail := is_passing_comparison(decorator.args[0], state))
                is not None
            )
            and (
                (decorator.func.attr == "skipIf" and pass_fail == "fail")
                or (decorator.func.attr == "skipUnless" and pass_fail == "pass")
            )
        ):
            yield ast_start_offset(decorator), partial(erase_decorator, node=decorator)


def erase_decorator(
    tokens: list[Token],
    i: int,
    *,
    node: ast.Call,
) -> None:
    erase_node(tokens, i, node=node)
    at_j = reverse_find(tokens, i, name=OP, src="@")
    del tokens[at_j:i]
