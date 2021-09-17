import ast
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from tokenize_rt import UNIMPORTANT_WS, Token, tokens_to_src

# Token name aliases
CODE = "CODE"  # Token name meaning 'replaced by us'
COMMENT = "COMMENT"
DEDENT = "DEDENT"
INDENT = "INDENT"
LOGICAL_NEWLINE = "NEWLINE"
NAME = "NAME"
OP = "OP"
PHYSICAL_NEWLINE = "NL"
STRING = "STRING"


# Basic functions


def find(tokens: List[Token], i: int, *, name: str, src: Optional[str] = None) -> int:
    """
    Find the next token matching name and src.
    """
    while tokens[i].name != name or (src is not None and tokens[i].src != src):
        i += 1
    return i


def reverse_find(
    tokens: List[Token], i: int, *, name: str, src: Optional[str] = None
) -> int:
    """
    Find the previous token matching name and src.
    """
    while tokens[i].name != name or (src is not None and tokens[i].src != src):
        i -= 1
    return i


def consume(
    tokens: List[Token], i: int, *, name: str, src: Optional[str] = None
) -> int:
    """
    Move past any tokens matching name and src.
    """
    while tokens[i + 1].name == name and (src is None or tokens[i + 1].src == src):
        i += 1
    return i


def reverse_consume(
    tokens: List[Token], i: int, *, name: str, src: Optional[str] = None
) -> int:
    """
    Rewind past any tokens matching name and src.
    """
    while tokens[i - 1].name == name and (src is None or tokens[i - 1].src == src):
        i -= 1
    return i


def find_final_token(tokens: List[Token], i: int, *, node: ast.AST) -> int:
    """
    Find the last token corresponding to the given ast node.
    """
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
    """
    If the previous token is and indent, return its position and the
    indentation string. Otherwise return the current position and "".
    """
    j = i
    if j > 0 and tokens[j - 1].name == INDENT:
        j -= 1
        indent = tokens[j].src
    else:
        indent = ""
    return (j, indent)


def alone_on_line(tokens: List[Token], start_idx: int, end_idx: int) -> bool:
    """
    Return if the given set of tokens is on its own physical line.
    """
    return (
        tokens[start_idx - 2].name == PHYSICAL_NEWLINE
        and tokens[start_idx - 1].name == UNIMPORTANT_WS
        and tokens[end_idx + 1].name == PHYSICAL_NEWLINE
    )


# More complex mini-parser functions


BRACES = {"(": ")", "[": "]", "{": "}"}


def parse_call_args(
    tokens: List[Token],
    i: int,
) -> Tuple[List[Tuple[int, int]], int]:
    """
    Given the index of the opening bracket of a function call, step through
    and parse its arguments into a list of tuples of start, end indices.
    Return this list plus the position of the token after.
    """
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


# Rewriting functions


def insert(tokens: List[Token], i: int, *, new_src: str) -> None:
    """
    Insert a generated token with the given new source.
    """
    tokens.insert(i, Token(CODE, new_src))


def replace(tokens: List[Token], i: int, *, src: str) -> None:
    """
    Replace the token at position i with a generated token with the given new
    source.
    """
    tokens[i] = tokens[i]._replace(name=CODE, src=src)


def erase_node(tokens: List[Token], i: int, *, node: ast.AST) -> None:
    """
    Erase all tokens corresponding to the given ast node.
    """
    j = find_final_token(tokens, i, node=node)
    if tokens[j].name == LOGICAL_NEWLINE:  # pragma: no branch
        j += 1
    i, _ = extract_indent(tokens, i)
    del tokens[i:j]


def find_and_replace_name(tokens: List[Token], i: int, *, name: str, new: str) -> None:
    j = find(tokens, i, name=NAME, src=name)
    tokens[j] = tokens[j]._replace(name="CODE", src=new)


def replace_argument_names(
    tokens: List[Token],
    i: int,
    *,
    node: ast.Call,
    arg_map: Dict[str, str],
) -> None:
    """
    Update an ast.Call node’s keyword argument names, where arg_map maps old to
    new names.
    """
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


def update_import_names(
    tokens: List[Token],
    i: int,
    *,
    node: ast.ImportFrom,
    name_map: Dict[str, str],
) -> None:
    """
    Replace an ast.ImportFrom node’s imported names, where name_map maps old to
    new names. If a new name entry is the empty string, remove the import.
    """
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


def update_import_modules(
    tokens: List[Token],
    i: int,
    *,
    node: ast.ImportFrom,
    module_rewrites: Dict[str, str],
) -> None:
    """
    Replace import names from an ast.ImportFrom with new import statements from
    elsewhere. rewrites should map import names to the new modules they should
    be imported from.
    """
    assert node.module is not None
    imports_to_add = defaultdict(list)
    name_map = {}
    for alias in node.names:
        name = alias.name
        if name in module_rewrites:
            name_map[name] = ""
            new_name = f"{name} as {alias.asname}" if alias.asname else name
            imports_to_add[module_rewrites[name]].append(new_name)

    j, indent = extract_indent(tokens, i)
    update_import_names(tokens, i, node=node, name_map=name_map)
    for module, names in reversed(imports_to_add.items()):
        joined_names = ", ".join(sorted(names))
        insert(tokens, j, new_src=f"{indent}from {module} import {joined_names}\n")
