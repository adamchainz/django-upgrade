from __future__ import annotations

import ast
import os
import pkgutil
import re
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, Iterable, List, Tuple, TypeVar

from tokenize_rt import Offset, Token

from django_upgrade import fixers


class Settings:
    def __init__(self, target_version: tuple[int, int]) -> None:
        self.target_version = target_version


settings_re = re.compile(r"\bsettings\b")

test_re = re.compile(r"(\b|_)tests?(\b|_)")

dunder_init_re = re.compile(r"(^|[\\/])__init__\.py$")


class State:
    def __init__(
        self,
        settings: Settings,
        filename: str,
        from_imports: dict[str, set[str]],
    ) -> None:
        self.settings = settings
        self.filename = filename
        self.from_imports = from_imports

    def looks_like_migrations_file(self) -> bool:
        return "migrations" in self.filename.split(os.path.sep)

    def looks_like_settings_file(self) -> bool:
        return settings_re.search(self.filename) is not None

    def looks_like_test_file(self) -> bool:
        return test_re.search(self.filename) is not None

    def looks_like_dunder_init_file(self) -> bool:
        return dunder_init_re.search(self.filename) is not None


AST_T = TypeVar("AST_T", bound=ast.AST)
TokenFunc = Callable[[int, List[Token]], None]
ASTFunc = Callable[[State, AST_T, ast.AST], Iterable[Tuple[Offset, TokenFunc]]]

if TYPE_CHECKING:  # pragma: no cover
    from typing import Protocol
else:
    Protocol = object


class ASTCallbackMapping(Protocol):
    def __getitem__(self, tp: type[AST_T]) -> list[ASTFunc[AST_T]]:  # pragma: no cover
        ...

    def items(self) -> Iterable[tuple[Any, Any]]:  # pragma: no cover
        ...


def visit(
    tree: ast.Module,
    settings: Settings,
    filename: str,
) -> dict[Offset, list[TokenFunc]]:
    ast_funcs = get_ast_funcs(settings.target_version)
    initial_state = State(
        settings=settings,
        filename=filename,
        from_imports=defaultdict(set),
    )

    nodes: list[tuple[State, ast.AST, ast.AST]] = [(initial_state, tree, tree)]
    ret = defaultdict(list)
    while nodes:
        state, node, parent = nodes.pop()

        for ast_func in ast_funcs[type(node)]:
            for offset, token_func in ast_func(state, node, parent):
                ret[offset].append(token_func)

        if (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and (
                node.module is not None
                and (node.module.startswith("django.") or node.module == "django")
            )
        ):
            state.from_imports[node.module].update(
                name.name
                for name in node.names
                if name.asname is None and name.name != "*"
            )

        for name in reversed(node._fields):
            value = getattr(node, name)
            next_state = state

            if isinstance(value, ast.AST):
                nodes.append((next_state, value, node))
            elif isinstance(value, list):
                for subvalue in reversed(value):
                    if isinstance(subvalue, ast.AST):
                        nodes.append((next_state, subvalue, node))
    return ret


class Fixer:
    def __init__(self, name: str, min_version: tuple[int, int]) -> None:
        self.name = name
        self.min_version = min_version
        self.ast_funcs: ASTCallbackMapping = defaultdict(list)

        FIXERS.append(self)

    def register(
        self, type_: type[AST_T]
    ) -> Callable[[ASTFunc[AST_T]], ASTFunc[AST_T]]:
        def decorator(func: ASTFunc[AST_T]) -> ASTFunc[AST_T]:
            self.ast_funcs[type_].append(func)
            return func

        return decorator


FIXERS: list[Fixer] = []


def _import_fixers() -> None:
    # https://github.com/python/mypy/issues/1422
    fixers_path: str = fixers.__path__  # type: ignore
    mod_infos = pkgutil.walk_packages(fixers_path, f"{fixers.__name__}.")
    for _, name, _ in mod_infos:
        __import__(name, fromlist=["_trash"])


_import_fixers()


def get_ast_funcs(target_version: tuple[int, int]) -> ASTCallbackMapping:
    ast_funcs: ASTCallbackMapping = defaultdict(list)
    for fixer in FIXERS:
        if target_version >= fixer.min_version:
            for type_, type_funcs in fixer.ast_funcs.items():
                ast_funcs[type_].extend(type_funcs)
    return ast_funcs
