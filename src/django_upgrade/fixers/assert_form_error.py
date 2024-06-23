"""
Update calls to assertFormError() / assertFormSetError() to pass the
form/formset instead of the response.

https://docs.djangoproject.com/en/4.1/releases/4.1/#tests
"""

from __future__ import annotations

import ast
from functools import partial
from typing import Any
from typing import Iterable

from tokenize_rt import UNIMPORTANT_WS
from tokenize_rt import Offset
from tokenize_rt import Token
from tokenize_rt import tokens_to_src

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import looks_like_test_client_call
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import OP
from django_upgrade.tokens import PHYSICAL_NEWLINE
from django_upgrade.tokens import consume
from django_upgrade.tokens import find_first_token
from django_upgrade.tokens import find_last_token
from django_upgrade.tokens import replace
from django_upgrade.tokens import reverse_consume

fixer = Fixer(
    __name__,
    min_version=(4, 1),
    condition=lambda state: state.looks_like_test_file,
)


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Attribute)
        and (func_name := node.func.attr) in ("assertFormError", "assertFormsetError")
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        and arguments_match(node, func_name)
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

        if func_name == "assertFormError":
            errors_idx = 3
        else:
            errors_idx = 4
        try:
            errors_arg = node.args[errors_idx]
        except IndexError:
            errors_arg = [k.value for k in node.keywords if k.arg == "errors"][0]

        if isinstance(errors_arg, ast.Constant) and errors_arg.value is None:
            yield ast_start_offset(errors_arg), partial(replace, src="[]")


def arguments_match(node: ast.Call, func_name: str) -> bool:
    arg_count = len(node.args)
    kwarg_count = len(node.keywords)
    total_args = arg_count + kwarg_count
    kwarg_names = [k.arg for k in node.keywords]

    if func_name == "assertFormError":
        return (
            total_args == 4
            and (arg_count == 4 or (arg_count == 3 and kwarg_names == ["errors"]))
        ) or (
            total_args == 5
            and (
                arg_count == 5
                or (arg_count == 4 and node.keywords[0].arg == "msg_prefix")
                or (arg_count == 3 and kwarg_names == ["errors", "msg_prefix"])
            )
        )
    else:
        # assertFormsetError
        return (
            total_args == 5
            and (arg_count == 5 or (arg_count == 4 and kwarg_names == ["errors"]))
        ) or (
            total_args == 6
            and (
                arg_count == 6
                or (arg_count == 5 and kwarg_names == ["msg_prefix"])
                or (arg_count == 4 and kwarg_names == ["errors", "msg_prefix"])
            )
        )


class ResponseAssignmentVisitor(ast.NodeVisitor):
    __slots__ = ("funcdef", "name", "before", "stop_search", "looks_like_response")

    def __init__(
        self,
        funcdef: ast.FunctionDef | ast.AsyncFunctionDef,
        name: str,
        before: ast.Expr,
    ) -> None:
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

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        # Avoid descending into a new scope
        return None

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
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == self.name
            and (
                looks_like_test_client_call(node.value, "client")
                or (
                    isinstance(node.value, ast.Await)
                    and looks_like_test_client_call(node.value.value, "async_client")
                )
            )
        ):
            self.stop_search = True
            self.looks_like_response = True
        return None


def is_response_from_client(
    parents: tuple[ast.AST, ...],
    node: ast.Call,
    name: str,
) -> bool:
    if not (
        isinstance(parents[-1], ast.Expr)
        and isinstance(
            (funcdef := parents[-2]), (ast.AsyncFunctionDef, ast.FunctionDef)
        )
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
    k = find_last_token(tokens, j, node=form_arg)
    ftokens = tokens[j : k + 1]
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
