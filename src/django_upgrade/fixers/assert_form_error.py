"""
Update calls to assertFormError() / assertFormSetError() to pass the
form/formset instead of the response.

https://docs.djangoproject.com/en/4.1/releases/4.1/#tests
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Any, Iterable

from tokenize_rt import UNIMPORTANT_WS, Offset, Token, tokens_to_src

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    OP,
    PHYSICAL_NEWLINE,
    consume,
    find_final_token,
    find_first_token,
    reverse_consume,
)

fixer = Fixer(
    __name__,
    min_version=(4, 1),
)


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "assertFormError"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        and len(node.args) in (4, 5)
        and len(node.keywords) == 0
        and (
            (
                isinstance((second_arg := node.args[1]), ast.Constant)
                and isinstance(second_arg.value, str)
            )
            or isinstance(second_arg, ast.Name)
        )
        and isinstance((first_arg := node.args[0]), ast.Name)
        # Detect response arguments either from some hardcoded names, or by
        # looking back in current function for assignment from self.client.*()
        # Necessary because new signature with msg_prefix overlaps old one
        and (
            "response" in first_arg.id
            or first_arg.id in ("resp", "res", "r")
            or is_response_from_client(parents, node, first_arg.id)
        )
    ):
        yield ast_start_offset(first_arg), partial(
            rewrite_args,
            response_arg=first_arg,
            form_arg=second_arg,
        )


CLIENT_REQUEST_METHODS = frozenset(
    (
        "request",
        "get",
        "post",
        "head",
        "options",
        "put",
        "patch",
        "delete",
        "trace",
    )
)


class ResponseAssignmentVisitor(ast.NodeVisitor):
    def __init__(self, funcdef: ast.FunctionDef, name: str, before: ast.Expr) -> None:
        self.funcdef = funcdef
        self.name = name
        self.before = before
        self.stop_search = False
        self.looks_like_response = False

    def search(self) -> None:
        self.generic_visit(self.funcdef)

    def visit(self, node: ast.AST) -> Any:
        if self.stop_search:
            return None
        return super().visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Avoid descending into a new scope
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Avoid descending into a new scope
        return None

    def visit_Expr(self, node: ast.Expr) -> Any:
        if node == self.before:
            self.stop_search = True
            return None
        return self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> Any:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == self.name
            and isinstance((call := node.value), ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr in CLIENT_REQUEST_METHODS
            and isinstance(call.func.value, ast.Attribute)
            and call.func.value.attr == "client"
            and isinstance(call.func.value.value, ast.Name)
            and call.func.value.value.id == "self"
        ):
            self.stop_search = True
            self.looks_like_response = True
        return None


def is_response_from_client(
    parents: list[ast.AST],
    node: ast.Call,
    name: str,
) -> bool:
    if not (
        isinstance(parents[-1], ast.Expr)
        and isinstance((funcdef := parents[-2]), ast.FunctionDef)
    ):
        return False

    visitor = ResponseAssignmentVisitor(funcdef, name, parents[-1])
    visitor.search()
    return visitor.looks_like_response


def rewrite_args(
    tokens: list[Token],
    i: int,
    *,
    response_arg: ast.Name,
    form_arg: ast.Constant | ast.Name,
) -> None:
    j = find_first_token(tokens, i, node=form_arg)
    k = find_final_token(tokens, j, node=form_arg)
    ftokens = tokens[j:k]
    k = consume(tokens, k, name=OP, src=",")
    k = consume(tokens, k, name=UNIMPORTANT_WS)
    if tokens[k + 1].name == PHYSICAL_NEWLINE:
        j = reverse_consume(tokens, j, name=UNIMPORTANT_WS)
        j = reverse_consume(tokens, j, name=PHYSICAL_NEWLINE)
    del tokens[j : k + 1]
    rtoken = tokens[i]
    tokens[i] = rtoken._replace(
        src=rtoken.src + ".context[" + tokens_to_src(ftokens) + "]",
    )
