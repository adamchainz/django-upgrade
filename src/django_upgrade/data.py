from __future__ import annotations

import ast
import pkgutil
import re
from collections import defaultdict
from collections.abc import Callable, Collection, Iterable
from functools import cached_property
from typing import Any, TypeVar

from tokenize_rt import Offset, Token

from django_upgrade import fixers


class Settings:
    __slots__ = (
        "target_version",
        "enabled_fixers",
    )

    def __init__(
        self,
        target_version: tuple[int, int],
        only_fixers: set[str] | None = None,
        skip_fixers: set[str] | None = None,
    ) -> None:
        self.target_version = target_version
        self.enabled_fixers = {
            name
            for name in FIXERS
            if (only_fixers is None or name in only_fixers)
            and (skip_fixers is None or name not in skip_fixers)
        }


apps_re = re.compile(r"(^|[\\/])apps\.py$")
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
        from_imports: defaultdict[str, set[str]],
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
TokenFunc = Callable[[list[Token], int], None]
ASTFunc = Callable[
    [State, AST_T, tuple[ast.AST, ...]], Iterable[tuple[Offset, TokenFunc]]
]

# Fields that never contain child nodes we want to visit: plain values, or
# expression contexts (Load, Store, Del), which no fixer looks at.
_SKIP_FIELDS = frozenset(
    ("ctx", "id", "attr", "arg", "asname", "module", "level", "kind")
)


class _ChildFields(dict[type[ast.AST], tuple[str, ...]]):
    def __missing__(self, type_: type[ast.AST]) -> tuple[str, ...]:
        fields = tuple(
            name for name in reversed(type_._fields) if name not in _SKIP_FIELDS
        )
        self[type_] = fields
        return fields


_child_fields = _ChildFields()


def visit(
    tree: ast.Module,
    settings: Settings,
    filename: str,
) -> dict[Offset, list[TokenFunc]]:
    state = State(
        settings=settings,
        filename=filename,
        from_imports=defaultdict(set),
    )
    dispatch = get_ast_funcs(state, settings)

    nodes: list[tuple[ast.AST, tuple[ast.AST, ...]]] = [(tree, ())]
    ret = defaultdict(list)
    while nodes:
        node, parents = nodes.pop()
        node_type = type(node)

        if (type_dispatch := dispatch.get(node_type)) is not None:
            unfiltered_funcs, funcs_by_name = type_dispatch
            ast_funcs = unfiltered_funcs
            if funcs_by_name:
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name):
                        ast_funcs = funcs_by_name.get(func.id, unfiltered_funcs)
                    elif isinstance(func, ast.Attribute):
                        ast_funcs = funcs_by_name.get(func.attr, unfiltered_funcs)
                elif isinstance(node, ast.Name):
                    ast_funcs = funcs_by_name.get(node.id, unfiltered_funcs)
                else:
                    assert isinstance(node, ast.Attribute)
                    ast_funcs = funcs_by_name.get(node.attr, unfiltered_funcs)

            for ast_func in ast_funcs:
                for offset, token_func in ast_func(state, node, parents):
                    ret[offset].append(token_func)

        if (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and (
                node.module is not None
                and (
                    node.module.startswith("django.")
                    or node.module in ("django", "unittest")
                )
            )
        ):
            state.from_imports[node.module].update(
                name.name
                for name in node.names
                if name.asname is None and name.name != "*"
            )

        subparents = parents + (node,)
        for name in _child_fields[node_type]:
            value = getattr(node, name)

            if isinstance(value, ast.AST):
                nodes.append((value, subparents))
            elif isinstance(value, list):
                for subvalue in reversed(value):
                    if isinstance(subvalue, ast.AST):
                        nodes.append((subvalue, subparents))
    return ret


# A registered callback, and the names it is filtered to, if any.
Registration = tuple[ASTFunc[Any], frozenset[str] | None]

# Node types that support filtering callbacks by name, with register(names=...).
# The name is the called function's name for Call nodes (func.id or func.attr),
# the identifier for Name nodes, and the attribute name for Attribute nodes.
NAMED_TYPES = frozenset((ast.Call, ast.Name, ast.Attribute))


class Fixer:
    __slots__ = (
        "name",
        "min_version",
        "ast_funcs",
        "condition",
    )

    def __init__(
        self,
        module_name: str,
        min_version: tuple[int, int],
        condition: Callable[[State], bool] | None = None,
    ) -> None:
        self.name = module_name.rpartition(".")[2]
        self.min_version = min_version
        self.ast_funcs: defaultdict[type[ast.AST], list[Registration]] = defaultdict(
            list
        )
        self.condition = condition

        FIXERS[self.name] = self

    def register(
        self,
        type_: type[AST_T],
        *,
        names: Collection[str] | None = None,
    ) -> Callable[[ASTFunc[AST_T]], ASTFunc[AST_T]]:
        """
        Register a function to be called for nodes of the given type. If
        names is given, only call it for nodes with one of those names - see
        NAMED_TYPES.
        """
        if names is not None:
            if type_ not in NAMED_TYPES:
                raise TypeError(f"Cannot filter {type_.__name__} nodes by name.")
            if isinstance(names, str):
                raise TypeError("names must be a collection of strings, not a str.")

        def decorator(func: ASTFunc[AST_T]) -> ASTFunc[AST_T]:
            self.ast_funcs[type_].append(
                (func, None if names is None else frozenset(names))
            )
            return func

        return decorator


FIXERS: dict[str, Fixer] = {}


def _import_fixers() -> None:
    # https://github.com/python/mypy/issues/1422
    fixers_path: str = fixers.__path__  # type: ignore [assignment]
    mod_infos = pkgutil.walk_packages(fixers_path, f"{fixers.__name__}.")
    for _, name, _ in mod_infos:
        __import__(name, fromlist=["_trash"])


_import_fixers()


# For each node type: the callbacks registered without names, and a mapping
# from each registered name to all callbacks for nodes with that name. The
# latter include the unfiltered callbacks, in registration order, so visit()
# only has to pick one tuple.
TypeDispatch = tuple[
    tuple[ASTFunc[Any], ...],
    dict[str, tuple[ASTFunc[Any], ...]],
]
Dispatch = dict[type[ast.AST], TypeDispatch]

_dispatch_cache: dict[tuple[Fixer, ...], Dispatch] = {}


def get_ast_funcs(state: State, settings: Settings) -> Dispatch:
    enabled = tuple(
        fixer
        for fixer in FIXERS.values()
        if fixer.name in settings.enabled_fixers
        and fixer.min_version <= state.settings.target_version
        and (fixer.condition is None or fixer.condition(state))
    )
    try:
        return _dispatch_cache[enabled]
    except KeyError:
        pass

    registered: defaultdict[type[ast.AST], list[Registration]] = defaultdict(list)
    for fixer in enabled:
        for type_, type_funcs in fixer.ast_funcs.items():
            registered[type_].extend(type_funcs)

    dispatch: Dispatch = {}
    for type_, type_funcs in registered.items():
        all_names: set[str] = set()
        for _, names in type_funcs:
            if names is not None:
                all_names.update(names)
        dispatch[type_] = (
            tuple(func for func, names in type_funcs if names is None),
            {
                name: tuple(
                    func for func, names in type_funcs if names is None or name in names
                )
                for name in all_names
            },
        )

    _dispatch_cache[enabled] = dispatch
    return dispatch
