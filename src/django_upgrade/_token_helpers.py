import ast
from typing import List, Optional

from tokenize_rt import UNIMPORTANT_WS, Token

NAME = "NAME"
OP = "OP"
NL = "NL"
COMMENT = "COMMENT"
CODE = "CODE"  # Token name meaning 'replaced by us'


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


def erase_node(tokens: List[Token], i: int, *, node: ast.AST) -> None:
    j = i
    while (tokens[j].line is None or tokens[j].line <= node.end_lineno) and (
        tokens[j].utf8_byte_offset is None
        or tokens[j].utf8_byte_offset < node.end_col_offset
    ):
        j += 1
    if tokens[j].name == "NEWLINE":
        j += 1
    del tokens[i:j]


def consume(
    tokens: List[Token], i: int, *, name: str, src: Optional[str] = None
) -> int:
    while tokens[i + 1].name == name and (src is None or tokens[i + 1].src == src):
        i += 1
    return i


def alone_on_line(tokens: List[Token], start_idx: int, end_idx: int) -> bool:
    return (
        tokens[start_idx - 2].name == NL
        and tokens[start_idx - 1].name == UNIMPORTANT_WS
        and tokens[end_idx + 1].name == NL
    )


def insert(tokens: List[Token], i: int, *, new_src: str) -> None:
    tokens.insert(i, Token(CODE, new_src))


def insert_after(
    tokens: List[Token], i: int, *, name: str, src: Optional[str] = None, new_src: str
) -> None:
    j = find(tokens, i, name=name, src=src)
    print(j)
    tokens.insert(j + 1, Token(CODE, new_src))
    print(tokens[j + 1])


def replace(tokens: List[Token], i: int, *, src: str) -> None:
    tokens[i] = Token(CODE, src)


def erase_from_import_name(
    tokens: List[Token],
    i: int,
    *,
    names: List[ast.alias],
    to_erase: str,
) -> None:
    i = find(tokens, i, name=NAME, src="from")
    i = find(tokens, i, name=NAME, src="import")

    found_index: int
    found_alias: ast.alias
    for alias_idx, alias in enumerate(names):
        if alias.name == to_erase:
            found_index = alias_idx
            found_alias = alias
            break

        i = find(tokens, i, name=NAME, src=alias.name)
        if alias.asname is not None:
            i = find(tokens, i, name=NAME, src="as")
            i = find(tokens, i, name=NAME, src=alias.asname)

    start_idx = find(tokens, i, name=NAME, src=to_erase)

    end_idx = start_idx
    if found_alias.asname is not None:
        end_idx = find(tokens, end_idx, name=NAME, src="as")
        end_idx = find(tokens, end_idx, name=NAME, src=found_alias.asname)

    if found_index < len(names) - 1:
        end_idx = find(tokens, end_idx, name=OP, src=",")
    else:
        start_idx = reverse_find(tokens, start_idx, name=OP, src=",")

    end_idx = consume(tokens, end_idx, name=UNIMPORTANT_WS)
    end_idx = consume(tokens, end_idx, name=COMMENT)

    if alone_on_line(tokens, start_idx, end_idx):
        start_idx -= 1
        end_idx += 1

    tokens[start_idx : end_idx + 1] = []
