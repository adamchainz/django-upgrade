from __future__ import annotations

import ast
import re
from collections import defaultdict

from tokenize_rt import NON_CODING_TOKENS
from tokenize_rt import UNIMPORTANT_WS
from tokenize_rt import Token
from tokenize_rt import tokens_to_src

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


def find(tokens: list[Token], i: int, *, name: str, src: str | None = None) -> int:
    """
    Find the next token matching name and src.
    """
    while tokens[i].name != name or (src is not None and tokens[i].src != src):
        i += 1
    return i


def reverse_find(
    tokens: list[Token], i: int, *, name: str, src: str | None = None
) -> int:
    """
    Find the previous token matching name and src.
    """
    while tokens[i].name != name or (src is not None and tokens[i].src != src):
        i -= 1
    return i


def consume(tokens: list[Token], i: int, *, name: str, src: str | None = None) -> int:
    """
    Move past any tokens matching name and src.
    """
    while tokens[i + 1].name == name and (src is None or tokens[i + 1].src == src):
        i += 1
    return i


def reverse_consume(
    tokens: list[Token], i: int, *, name: str, src: str | None = None
) -> int:
    """
    Rewind past any tokens matching name and src.
    """
    while tokens[i - 1].name == name and (src is None or tokens[i - 1].src == src):
        i -= 1
    return i


def find_first_token(
    tokens: list[Token], i: int, *, node: ast.expr | ast.keyword | ast.stmt
) -> int:
    """
    Find the first token corresponding to the given ast node.
    """
    while tokens[i].line is None or tokens[i].line < node.lineno:
        i += 1
    while (
        tokens[i].utf8_byte_offset is None
        or tokens[i].utf8_byte_offset < node.col_offset
    ):
        i += 1
    return i


def find_last_token(
    tokens: list[Token], i: int, *, node: ast.expr | ast.keyword | ast.stmt
) -> int:
    """
    Find the last token corresponding to the given ast node.
    """
    while tokens[i].line is None or tokens[i].line < node.end_lineno:
        i += 1
    while (
        tokens[i].utf8_byte_offset is None
        or tokens[i].utf8_byte_offset < node.end_col_offset
    ):
        i += 1
    return i - 1


def extract_indent(tokens: list[Token], i: int) -> tuple[int, str]:
    """
    If the previous token is an indent, return its position and the
    indentation string. Otherwise return the current position and "".
    """
    if i > 0 and tokens[i - 1].name in (INDENT, UNIMPORTANT_WS):
        i -= 1
        indent = tokens[i].src
    else:
        indent = ""
    return (i, indent)


def alone_on_line(tokens: list[Token], start_idx: int, end_idx: int) -> bool:
    """
    Return if the given set of tokens is on its own physical line.
    """
    # no types for tokenize-rt
    return (  # type: ignore [no-any-return]
        tokens[start_idx - 2].name == PHYSICAL_NEWLINE
        and tokens[start_idx - 1].name == UNIMPORTANT_WS
        and tokens[end_idx + 1].name == PHYSICAL_NEWLINE
    )


# More complex mini-parsers

BRACES = {"(": ")", "[": "]", "{": "}"}
OPENING, CLOSING = frozenset(BRACES), frozenset(BRACES.values())


def parse_call_args(
    tokens: list[Token],
    i: int,
) -> tuple[list[tuple[int, int]], int]:
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


def find_block_start(tokens: list[Token], i: int) -> int:
    depth = 0
    while depth or tokens[i].src != ":":
        if tokens[i].src in OPENING:
            depth += 1
        elif tokens[i].src in CLOSING:
            depth -= 1
        i += 1
    return i


class Block:  # pragma: no cover
    """
    Adapted from pyupgrade:
    https://github.com/asottile/pyupgrade/blob/ad5d9db9a206bfd221760fd81e407bf6040c808c/pyupgrade/_token_helpers.py#L179

    Copyright (c) 2017 Anthony Sottile

    MIT Licensed
    """

    __slots__ = ("start", "colon", "block", "end", "line")

    def __init__(
        self, start: int, colon: int, block: int, end: int, line: bool
    ) -> None:
        self.start = start
        self.colon = colon
        self.block = block
        self.end = end
        self.line = line

    def _initial_indent(self, tokens: list[Token]) -> int:
        if tokens[self.start].src.isspace():
            return len(tokens[self.start].src)
        else:
            return 0

    def _minimum_indent(self, tokens: list[Token]) -> int:
        block_indent: int | None = None
        for i in range(self.block, self.end):
            if (
                tokens[i - 1].name in ("NL", "NEWLINE")
                and tokens[i].name in ("INDENT", UNIMPORTANT_WS)
                and
                # comments can have arbitrary indentation so ignore them
                tokens[i + 1].name != "COMMENT"
            ):
                token_indent = len(tokens[i].src)
                if block_indent is None:
                    block_indent = token_indent
                else:
                    block_indent = min(block_indent, token_indent)

        assert block_indent is not None
        return block_indent

    def dedent(self, tokens: list[Token]) -> None:
        if self.line:
            return
        initial_indent = self._initial_indent(tokens)
        diff = self._minimum_indent(tokens) - initial_indent
        for i in range(self.block, self.end):
            if tokens[i - 1].name in ("DEDENT", "NL", "NEWLINE") and tokens[i].name in (
                "INDENT",
                UNIMPORTANT_WS,
            ):
                # make sure we preserve *at least* the initial indent
                s = tokens[i].src
                s = s[:initial_indent] + s[initial_indent + diff :]
                tokens[i] = tokens[i]._replace(src=s)

    def replace_condition(self, tokens: list[Token], new: list[Token]) -> None:
        start = self.start
        while tokens[start].name == "UNIMPORTANT_WS":
            start += 1
        tokens[start : self.colon] = new

    def _trim_end(self, tokens: list[Token]) -> Block:
        """the tokenizer reports the end of the block at the beginning of
        the next block
        """
        i = last_token = self.end - 1
        while tokens[i].name in NON_CODING_TOKENS | {"DEDENT", "NEWLINE"}:
            # if we find an indented comment inside our block, keep it
            if (
                tokens[i].name in {"NL", "NEWLINE"}
                and tokens[i + 1].name == UNIMPORTANT_WS
                and len(tokens[i + 1].src) > self._initial_indent(tokens)
            ):
                break
            # otherwise we've found another line to remove
            elif tokens[i].name in {"NL", "NEWLINE"}:
                last_token = i
            i -= 1
        return self.__class__(
            start=self.start,
            colon=self.colon,
            block=self.block,
            end=last_token + 1,
            line=self.line,
        )

    @classmethod
    def find(
        cls,
        tokens: list[Token],
        i: int,
        trim_end: bool = False,
    ) -> Block:
        if i > 0 and tokens[i - 1].name in {"INDENT", UNIMPORTANT_WS}:
            i -= 1
        start = i
        colon = find_block_start(tokens, i)

        j = colon + 1
        while tokens[j].name != "NEWLINE" and tokens[j].name in NON_CODING_TOKENS:
            j += 1

        if tokens[j].name == "NEWLINE":  # multi line block
            block = j + 1
            while tokens[j].name != "INDENT":
                j += 1
            level = 1
            j += 1
            while level:
                level += {"INDENT": 1, "DEDENT": -1}.get(tokens[j].name, 0)
                j += 1
            ret = cls(start, colon, block, j, line=False)
            if trim_end:
                return ret._trim_end(tokens)
            else:
                return ret
        else:  # single line block
            block = j
            j = find_end(tokens, j)
            return cls(start, colon, block, j, line=True)


def find_end(tokens: list[Token], i: int) -> int:  # pragma: no cover
    while tokens[i].name not in {"NEWLINE", "ENDMARKER"}:
        i += 1

    # depending on the version of python, some will not emit
    # NEWLINE('') at the end of a file which does not end with a
    # newline (for example 3.7.0)
    if tokens[i].name == "ENDMARKER":
        i -= 1
    else:
        i += 1

    return i


# Rewriting functions


def insert(tokens: list[Token], i: int, *, new_src: str) -> None:
    """
    Insert a generated token with the given new source.
    """
    tokens.insert(i, Token(CODE, new_src))


def replace(tokens: list[Token], i: int, *, src: str) -> None:
    """
    Replace the token at position i with a generated token with the given new
    source.
    """
    tokens[i] = tokens[i]._replace(name=CODE, src=src)


def erase_node(
    tokens: list[Token], i: int, *, node: ast.expr | ast.keyword | ast.stmt
) -> None:
    """
    Erase all tokens corresponding to the given ast node.
    """
    j = find_last_token(tokens, i, node=node)
    if tokens[j + 1].name == UNIMPORTANT_WS:
        j += 1
    if tokens[j + 1].name == COMMENT:
        j += 1
    if tokens[j + 1].name == LOGICAL_NEWLINE:  # pragma: no branch
        j += 1
    i, _ = extract_indent(tokens, i)
    del tokens[i : j + 1]


def find_and_replace_name(tokens: list[Token], i: int, *, name: str, new: str) -> None:
    j = find(tokens, i, name=NAME, src=name)
    tokens[j] = tokens[j]._replace(name=CODE, src=new)


def replace_argument_names(
    tokens: list[Token],
    i: int,
    *,
    node: ast.Call,
    arg_map: dict[str, str],
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
            for k in range(*kwarg_func_args[n]):
                if tokens[k].src == keyword.arg:
                    tokens[k] = tokens[k]._replace(src=arg_map[keyword.arg])
                    break
            else:  # pragma: no cover
                raise AssertionError(f"{keyword.arg} argument not found")


str_repr_single_to_double = str.maketrans(
    {
        "'": '"',
        '"': '\\"',
    }
)


def str_repr_matching(text: str, *, match_quotes: str) -> str:
    """
    Give the repr of a string, switching it to double quotes if the string
    literal represent in match_quotes uses double quotes.
    """
    result = repr(text)
    first_quote = re.search(r'[\'"]', match_quotes)
    assert first_quote is not None
    if first_quote[0] == '"' and result[0] != '"':
        result = result.translate(str_repr_single_to_double)
    return result


def update_import_names(
    tokens: list[Token],
    i: int,
    *,
    node: ast.ImportFrom,
    name_map: dict[str, str],
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

    replacements: list[tuple[int, int, list[Token]]] = []  # start, end, new tokens
    remove_all = True
    for alias_idx, alias in enumerate(node.names):
        if alias.name not in name_map:
            # Skip over
            remove_all = False
            j = find(tokens, j, name=NAME, src=alias.name)
            if alias.asname is not None:
                j = find(tokens, j, name=NAME, src="as")
                j = find(tokens, j, name=NAME, src=alias.asname)
            continue

        new_name = name_map[alias.name]
        if new_name == "" or new_name in existing_unaliased_names:
            # Erase
            start_idx = find(tokens, j, name=NAME, src=alias.name)

            end_idx = start_idx
            if alias.asname is not None:
                end_idx = find(tokens, end_idx, name=NAME, src="as")
                end_idx = find(tokens, end_idx, name=NAME, src=alias.asname)

            if len(node.names) > 1:
                if alias_idx == 0:
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
    tokens: list[Token],
    i: int,
    *,
    node: ast.ImportFrom,
    module_rewrites: dict[str, str],
) -> None:
    """
    Replace import names from an ast.ImportFrom with new import statements from
    elsewhere. rewrites should map import names to the new modules they should
    be imported from.
    """
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
