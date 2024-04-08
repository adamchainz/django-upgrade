from __future__ import annotations

import ast
import pkgutil
import re
from collections import defaultdict
from functools import cached_property
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import DefaultDict
from typing import Iterable
from typing import List
from typing import Tuple
from typing import TypeVar

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade import fixers


class Settings:
    __slots__ = (
        "target_version",
        "specific_fixture_names",
    )

    def __init__(
        self,
        target_version: tuple[int, int],
        only_fixers: list[str] | None = None,
        skip_fixers: list[str] | None = None,
    ) -> None:
        self.target_version = target_version
        self.specific_fixture_names = self._calculate_specific_fixtures(
            only_fixers, skip_fixers
        )

    def _calculate_specific_fixtures(
        self,
        only_fixers: list[str] | None,
        skip_fixers: list[str] | None,
    ) -> list[str]:
        fixer_names: list[str] = [f.name for f in FIXERS]
        if only_fixers is not None:
            fixer_names = [f for f in fixer_names if f in only_fixers]
        if skip_fixers is not None:
            fixer_names = [f for f in fixer_names if f not in skip_fixers]
        return fixer_names


admin_re = re.compile(r"(\b|_)admin(\b|_)")
commands_re = re.compile(r"(^|[\\/])management[\\/]commands[\\/]")
dunder_init_re = re.compile(r"(^|[\\/])__init__\.py$")
migrations_re = re.compile(r"(^|[\\/])migrations([\\/])")
settings_re = re.compile(r"(\b|_)settings(\b|_)")
test_re = re.compile(r"(\b|_)tests?(\b|_)")
models_re = re.compile(r"(^|[\\/])models([\\/]|\.py)")


class State:
    __slots__ = ("settings", "filename", "from_imports", "__weakref__", "__dict__")

    def __init__(
        self,
        settings: Settings,
        filename: str,
        from_imports: DefaultDict[str, set[str]],
    ) -> None:
        self.settings = settings
        self.filename = filename
        self.from_imports = from_imports

    @cached_property
    def looks_like_admin_file(self) -> bool:
        return admin_re.search(self.filename) is not None

    @cached_property
    def looks_like_command_file(self) -> bool:
        return commands_re.search(self.filename) is not None

    @cached_property
    def looks_like_dunder_init_file(self) -> bool:
        return dunder_init_re.search(self.filename) is not None

    @cached_property
    def looks_like_migrations_file(self) -> bool:
        return migrations_re.search(self.filename) is not None

    @cached_property
    def looks_like_settings_file(self) -> bool:
        return settings_re.search(self.filename) is not None

    @cached_property
    def looks_like_test_file(self) -> bool:
        return test_re.search(self.filename) is not None

    @cached_property
    def looks_like_models_file(self) -> bool:
        return models_re.search(self.filename) is not None


AST_T = TypeVar("AST_T", bound=ast.AST)
TokenFunc = Callable[[List[Token], int], None]
ASTFunc = Callable[[State, AST_T, List[ast.AST]], Iterable[Tuple[Offset, TokenFunc]]]

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
    initial_state = State(
        settings=settings,
        filename=filename,
        from_imports=defaultdict(set),
    )
    ast_funcs = get_ast_funcs(initial_state, settings)

    nodes: list[tuple[State, ast.AST, ast.AST]] = [(initial_state, tree, tree)]
    parents: list[ast.AST] = [tree]
    ret = defaultdict(list)
    while nodes:
        state, node, parent = nodes.pop()
        if len(parents) > 1 and parent == parents[-2]:
            parents.pop()
        elif parent != parents[-1]:
            parents.append(parent)

        for ast_func in ast_funcs[type(node)]:
            for offset, token_func in ast_func(state, node, parents):
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


def list_fixers() -> None:
    for fixer in sorted(FIXERS, key=lambda f: f.name):
        print(fixer.name)


class Fixer:
    __slots__ = (
        "name",
        "module",
        "min_version",
        "ast_funcs",
        "condition",
    )

    def __init__(
        self,
        module: str,
        min_version: tuple[int, int],
        condition: Callable[[State], bool] | None = None,
    ) -> None:
        self.module = module
        self.name: str = module.rpartition(".")[2]
        self.min_version = min_version
        self.ast_funcs: ASTCallbackMapping = defaultdict(list)
        self.condition = condition

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


def get_ast_funcs(state: State, settings: Settings) -> ASTCallbackMapping:
    ast_funcs: ASTCallbackMapping = defaultdict(list)
    for fixer in FIXERS:
        if fixer.name not in settings.specific_fixture_names:
            continue
        if fixer.min_version <= state.settings.target_version and (
            fixer.condition is None or fixer.condition(state)
        ):
            for type_, type_funcs in fixer.ast_funcs.items():
                ast_funcs[type_].extend(type_funcs)
    return ast_funcs
