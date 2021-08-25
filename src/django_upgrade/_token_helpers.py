from typing import List

from tokenize_rt import Token


def find_token(tokens: List[Token], i: int, src: str) -> int:
    while tokens[i].src != src:
        i += 1
    return i


def find_and_replace_name(i: int, tokens: List[Token], *, name: str, new: str) -> None:
    j = find_token(tokens, i, name)
    tokens[j] = tokens[j]._replace(name="CODE", src=new)
