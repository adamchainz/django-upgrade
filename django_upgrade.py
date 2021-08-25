import argparse
import collections
import ast
import sys
import warnings
import tokenize
from functools import partial
from tokenize_rt import src_to_tokens
from tokenize_rt import tokens_to_src
from tokenize_rt import Token
from tokenize_rt import UNIMPORTANT_WS
from tokenize_rt import Offset
from tokenize_rt import reversed_enumerate
from typing import (
    Dict,
    Optional,
    Sequence,
    List,
    Callable,
    Iterable,
    Tuple,
    TypeVar,
    NamedTuple,
    TYPE_CHECKING,
    Type,
    Set,
    Union,
)

# _main


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    parser.add_argument("--exit-zero-even-if-changed", action="store_true")
    args = parser.parse_args(argv)

    ret = 0
    for filename in args.filenames:
        ret |= _fix_file(filename, args)
    return ret


def _fix_file(filename: str, args: argparse.Namespace) -> int:
    if filename == "-":
        contents_bytes = sys.stdin.buffer.read()
    else:
        with open(filename, "rb") as fb:
            contents_bytes = fb.read()

    try:
        contents_text_orig = contents_text = contents_bytes.decode()
    except UnicodeDecodeError:
        print(f"{filename} is non-utf-8 (not supported)")
        return 1

    contents_text = _fix_plugins(contents_text)

    if filename == "-":
        print(contents_text, end="")
    elif contents_text != contents_text_orig:
        print(f"Rewriting {filename}", file=sys.stderr)
        with open(filename, "w", encoding="UTF-8", newline="") as f:
            f.write(contents_text)

    if args.exit_zero_even_if_changed:
        return 0
    else:
        return contents_text != contents_text_orig


def _fix_plugins(contents_text: str) -> str:
    try:
        ast_obj = ast_parse(contents_text)
    except SyntaxError:
        return contents_text

    callbacks = visit(FUNCS, ast_obj)

    if not callbacks:
        return contents_text

    try:
        tokens = src_to_tokens(contents_text)
    except tokenize.TokenError:  # pragma: no cover (bpo-2180)
        return contents_text

    _fixup_dedent_tokens(tokens)

    for i, token in reversed_enumerate(tokens):
        if not token.src:
            continue
        # though this is a defaultdict, by using `.get()` this function's
        # self time is almost 50% faster
        for callback in callbacks.get(token.offset, ()):
            callback(i, tokens)

    return tokens_to_src(tokens)


def _fixup_dedent_tokens(tokens: List[Token]) -> None:
    """For whatever reason the DEDENT / UNIMPORTANT_WS tokens are misordered

    | if True:
    |     if True:
    |         pass
    |     else:
    |^    ^- DEDENT
    |+----UNIMPORTANT_WS
    """
    for i, token in enumerate(tokens):
        if token.name == UNIMPORTANT_WS and tokens[i + 1].name == "DEDENT":
            tokens[i], tokens[i + 1] = tokens[i + 1], tokens[i]


# _data


class State(NamedTuple):
    from_imports: Dict[str, Set[str]]


AST_T = TypeVar("AST_T", bound=ast.AST)
TokenFunc = Callable[[int, List[Token]], None]
ASTFunc = Callable[[State, AST_T, ast.AST], Iterable[Tuple[Offset, TokenFunc]]]

if TYPE_CHECKING:
    from typing import Protocol
else:
    Protocol = object


class ASTCallbackMapping(Protocol):
    def __getitem__(self, tp: Type[AST_T]) -> List[ASTFunc[AST_T]]:
        ...


def visit(
    funcs: ASTCallbackMapping,
    tree: ast.Module,
) -> Dict[Offset, List[TokenFunc]]:
    initial_state = State(
        from_imports=collections.defaultdict(set),
    )

    nodes: List[Tuple[State, ast.AST, ast.AST]] = [(initial_state, tree, tree)]

    ret = collections.defaultdict(list)
    while nodes:
        state, node, parent = nodes.pop()

        tp = type(node)
        for ast_func in funcs[tp]:
            for offset, token_func in ast_func(state, node, parent):
                ret[offset].append(token_func)

        if (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and (node.module.startswith("django.") or node.module == "django")
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


FUNCS: ASTCallbackMapping = collections.defaultdict(list)


def register(tp: Type[AST_T]) -> Callable[[ASTFunc[AST_T]], ASTFunc[AST_T]]:
    def register_decorator(func: ASTFunc[AST_T]) -> ASTFunc[AST_T]:
        FUNCS[tp].append(func)
        return func

    return register_decorator


# _ast_helpers


def ast_parse(contents_text: str) -> ast.Module:
    # intentionally ignore warnings, we can't do anything about them
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(contents_text.encode())


def ast_to_offset(node: Union[ast.expr, ast.stmt]) -> Offset:
    return Offset(node.lineno, node.col_offset)


# _token_helpers


def replace_name(i: int, tokens: List[Token], *, name: str, new: str) -> None:
    # preserve token offset in case we need to match it later
    new_token = tokens[i]._replace(name="CODE", src=new)
    j = i
    while tokens[j].src != name:
        # timid: if we see a parenthesis here, skip it
        if tokens[j].src == ")":
            return
        j += 1
    tokens[i : j + 1] = [new_token]


def find_token(tokens: List[Token], i: int, src: str) -> int:
    while tokens[i].src != src:
        i += 1
    return i


def find_and_replace_name(i: int, tokens: List[Token], *, name: str, new: str) -> None:
    j = find_token(tokens, i, name)
    tokens[j] = tokens[j]._replace(name="CODE", src=new)


# plugin
NAMES = {"force_text": "force_str", "smart_text": "smart_str"}


@register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if node.level == 0 and node.module == "django.utils.encoding":
        for alias in node.names:
            name = alias.name
            if name in NAMES and alias.asname is None:
                yield ast_to_offset(node), partial(
                    find_and_replace_name, name=name, new=NAMES[name]
                )


@register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    name = node.id
    if name in NAMES and name in state.from_imports["django.utils.encoding"]:
        new = NAMES[name]

        func = partial(replace_name, name=name, new=new)
        yield ast_to_offset(node), func


if __name__ == "__main__":
    exit(main())
