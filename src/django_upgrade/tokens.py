import ast
from typing import Dict, List, Optional, Tuple

from tokenize_rt import UNIMPORTANT_WS, Token, tokens_to_src

# Token name aliases
INDENT = "INDENT"
DEDENT = "DEDENT"
NAME = "NAME"
OP = "OP"
LOGICAL_NEWLINE = "NEWLINE"
PHYSICAL_NEWLINE = "NL"
COMMENT = "COMMENT"
CODE = "CODE"  # Token name meaning 'replaced by us'


BRACES = {"(": ")", "[": "]", "{": "}"}


def find(tokens: List[Token], i: int, *, name: str, src: Optional[str] = None) -> int:
    while tokens[i].name != name or (src is not None and tokens[i].src != src):
        i += 1
    return i


def reverse_find(
    tokens: List[Token], i: int, *, name: str, src: Optional[str] = None
) -> int:
    while tokens[i].name != name or (src is not None and tokens[i].src != src):
        i -= 1
    return i


def find_and_replace_name(tokens: List[Token], i: int, *, name: str, new: str) -> None:
    j = find(tokens, i, name=NAME, src=name)
    tokens[j] = tokens[j]._replace(name="CODE", src=new)


def find_final_token(tokens: List[Token], i: int, *, node: ast.AST) -> int:
    j = i
    while tokens[j].line is None or tokens[j].line < node.end_lineno:
        j += 1
    while (
        tokens[j].utf8_byte_offset is None
        or tokens[j].utf8_byte_offset < node.end_col_offset
    ):
        j += 1
    return j


def extract_indent(tokens: List[Token], i: int) -> Tuple[int, str]:
    j = i
    if j > 0 and tokens[j - 1].name == INDENT:
        j -= 1
        indent = tokens[j].src
    else:
        indent = ""
    return (j, indent)


def erase_node(tokens: List[Token], i: int, *, node: ast.AST) -> None:
    j = find_final_token(tokens, i, node=node)
    if tokens[j].name == LOGICAL_NEWLINE:  # pragma: no branch
        j += 1
    if i > 0 and tokens[i - 1].name == INDENT:
        i -= 1
    del tokens[i:j]


def consume(
    tokens: List[Token], i: int, *, name: str, src: Optional[str] = None
) -> int:
    while tokens[i + 1].name == name and (src is None or tokens[i + 1].src == src):
        i += 1
    return i


def reverse_consume(
    tokens: List[Token], i: int, *, name: str, src: Optional[str] = None
) -> int:
    while tokens[i - 1].name == name and (src is None or tokens[i - 1].src == src):
        i -= 1
    return i


def alone_on_line(tokens: List[Token], start_idx: int, end_idx: int) -> bool:
    return (
        tokens[start_idx - 2].name == PHYSICAL_NEWLINE
        and tokens[start_idx - 1].name == UNIMPORTANT_WS
        and tokens[end_idx + 1].name == PHYSICAL_NEWLINE
    )


def insert(tokens: List[Token], i: int, *, new_src: str) -> None:
    tokens.insert(i, Token(CODE, new_src))


def insert_after(
    tokens: List[Token], i: int, *, name: str, src: Optional[str] = None, new_src: str
) -> None:
    j = find(tokens, i, name=name, src=src)
    tokens.insert(j + 1, Token(CODE, new_src))


def replace(tokens: List[Token], i: int, *, src: str) -> None:
    tokens[i] = tokens[i]._replace(name=CODE, src=src)


def parse_call_args(
    tokens: List[Token],
    i: int,
) -> Tuple[List[Tuple[int, int]], int]:
    args = []
    stack = [i]
    i += 1
    arg_start = i

    while stack:
        token = tokens[i]

        if len(stack) == 1 and token.src == ",":
            args.append((arg_start, i))
            arg_start = i + 1
        elif token.src in BRACES:
            stack.append(i)
        elif token.src == BRACES[tokens[stack[-1]].src]:
            stack.pop()
            # if we're at the end, append that argument
            if not stack and tokens_to_src(tokens[arg_start:i]).strip():
                args.append((arg_start, i))

        i += 1

    return args, i


def replace_arguments(
    tokens: List[Token],
    i: int,
    *,
    node: ast.Call,
    arg_map: Dict[str, str],
) -> None:
    j = find(tokens, i, name=OP, src="(")
    func_args, _ = parse_call_args(tokens, j)
    kwarg_func_args = func_args[len(node.args) :]

    for n, keyword in reversed(list(enumerate(node.keywords))):
        if keyword.arg in arg_map:
            x, y = kwarg_func_args[n]
            for k in range(*kwarg_func_args[n]):
                if tokens[k].src == keyword.arg:
                    tokens[k] = tokens[k]._replace(src=arg_map[keyword.arg])
                    break
            else:  # pragma: no cover
                raise AssertionError(f"{keyword.arg} argument not found")


def update_imports(
    tokens: List[Token],
    i: int,
    *,
    node: ast.ImportFrom,
    name_map: Dict[str, str],
) -> None:
    j = find(tokens, i, name=NAME, src="from")
    j = find(tokens, j, name=NAME, src="import")

    existing_unaliased_names = {
        alias.name for alias in node.names if alias.asname is None
    }

    replacements: List[Tuple[int, int, List[Token]]] = []  # start, end, new tokens
    remove_all = True
    for alias_idx, alias in enumerate(node.names):
        if alias.name not in name_map:
            # Skip over
            remove_all = False
            j = find(tokens, j, name=NAME, src=alias.name)
            if alias.asname is not None:  # pragma: no branch
                j = find(tokens, j, name=NAME, src="as")
                j = find(tokens, j, name=NAME, src=alias.asname)
            continue

        new_name = name_map[alias.name]
        if new_name == "" or new_name in existing_unaliased_names:
            # Erase
            start_idx = find(tokens, j, name=NAME, src=alias.name)

            end_idx = start_idx
            if alias.asname is not None:  # pragma: no cover
                end_idx = find(tokens, end_idx, name=NAME, src="as")
                end_idx = find(tokens, end_idx, name=NAME, src=alias.asname)

            if len(node.names) > 1:
                if alias_idx < len(node.names) - 1:
                    end_idx = find(tokens, end_idx, name=OP, src=",")
                else:
                    start_idx = reverse_find(tokens, start_idx, name=OP, src=",")

            end_idx = consume(tokens, end_idx, name=UNIMPORTANT_WS)
            end_idx = consume(tokens, end_idx, name=COMMENT)

            if alone_on_line(tokens, start_idx, end_idx):
                start_idx -= 1
                end_idx += 1

            replacements.append((start_idx, end_idx, []))
            j = end_idx
        else:
            # Replace
            remove_all = False
            start_idx = find(tokens, j, name=NAME, src=alias.name)
            replacements.append(
                (
                    start_idx,
                    start_idx,
                    [tokens[start_idx]._replace(name="CODE", src=new_name)],
                )
            )
            j = start_idx

    if remove_all:
        erase_node(tokens, i, node=node)
    else:
        for start_idx, end_idx, replacement in reversed(replacements):
            tokens[start_idx : end_idx + 1] = replacement
