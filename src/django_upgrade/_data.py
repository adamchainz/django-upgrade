import ast
import pkgutil
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Set,
    Tuple,
    Type,
    TypeVar,
)

from tokenize_rt import Offset, Token

from django_upgrade import _plugins


class Settings(NamedTuple):
    target_version: Tuple[int, int]


class State(NamedTuple):
    settings: Settings
    from_imports: Dict[str, Set[str]]


AST_T = TypeVar("AST_T", bound=ast.AST)
TokenFunc = Callable[[int, List[Token]], None]
ASTFunc = Callable[[State, AST_T, ast.AST], Iterable[Tuple[Offset, TokenFunc]]]

if TYPE_CHECKING:  # pragma: no cover
    from typing import Protocol
else:
    Protocol = object


class ASTCallbackMapping(Protocol):
    def __getitem__(self, tp: Type[AST_T]) -> List[ASTFunc[AST_T]]:  # pragma: no cover
        ...


def visit(
    tree: ast.Module,
    settings: Settings,
) -> Dict[Offset, List[TokenFunc]]:
    ast_funcs = get_ast_funcs(settings.target_version)
    initial_state = State(
        settings=settings,
        from_imports=defaultdict(set),
    )

    nodes: List[Tuple[State, ast.AST, ast.AST]] = [(initial_state, tree, tree)]
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
                name.name for name in node.names if not name.asname
            )

        for name in reversed(node._fields):
            value = getattr(node, name)
            next_state = state

            if isinstance(value, ast.AST):
                nodes.append((next_state, value, node))
            elif isinstance(value, list):
                for value in reversed(value):
                    if isinstance(value, ast.AST):
                        nodes.append((next_state, value, node))
    return ret


class Plugin:
    def __init__(self, min_version: Tuple[int, int]) -> None:
        global PLUGINS
        self.min_version = min_version
        self.ast_funcs: ASTCallbackMapping = defaultdict(list)

        PLUGINS.append(self)

    def register(
        self, type_: Type[AST_T]
    ) -> Callable[[ASTFunc[AST_T]], ASTFunc[AST_T]]:
        def decorator(func: ASTFunc[AST_T]) -> ASTFunc[AST_T]:
            self.ast_funcs[type_].append(func)
            return func

        return decorator


PLUGINS: List[Plugin] = []


def _import_plugins() -> None:
    # https://github.com/python/mypy/issues/1422
    plugins_path: str = _plugins.__path__  # type: ignore
    mod_infos = pkgutil.walk_packages(plugins_path, f"{_plugins.__name__}.")
    for _, name, _ in mod_infos:
        __import__(name, fromlist=["_trash"])


_import_plugins()


def get_ast_funcs(target_version: Tuple[int, int]) -> ASTCallbackMapping:
    ast_funcs: ASTCallbackMapping = defaultdict(list)
    for plugin in PLUGINS:
        if target_version >= plugin.min_version:
            ast_funcs.update(plugin.ast_funcs)  # type: ignore [attr-defined]
    return ast_funcs
