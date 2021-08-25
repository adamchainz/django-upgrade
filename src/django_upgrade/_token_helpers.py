from typing import List

from tokenize_rt import Token


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
