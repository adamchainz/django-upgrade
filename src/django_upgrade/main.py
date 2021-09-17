import argparse
import sys
import tokenize
from typing import List, Optional, Sequence, Tuple, cast

from tokenize_rt import (
    UNIMPORTANT_WS,
    Token,
    reversed_enumerate,
    src_to_tokens,
    tokens_to_src,
)

from django_upgrade.ast import ast_parse
from django_upgrade.data import Settings, visit
from django_upgrade.tokens import DEDENT


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    parser.add_argument("--exit-zero-even-if-changed", action="store_true")
    parser.add_argument(
        "--target-version",
        default="2.2",
        choices=[
            "1.9",
            "1.10",
            "1.11",
            "2.0",
            "2.1",
            "2.2",
            "3.0",
            "3.1",
            "3.2",
        ],
    )
    args = parser.parse_args(argv)

    target_version: Tuple[int, int] = cast(
        Tuple[int, int],
        tuple(int(x) for x in args.target_version.split(".", 1)),
    )
    settings = Settings(
        target_version=target_version,
    )

    ret = 0
    for filename in args.filenames:
        ret |= fix_file(
            filename,
            settings,
            exit_zero_even_if_changed=args.exit_zero_even_if_changed,
        )

    return ret


def fix_file(
    filename: str,
    settings: Settings,
    exit_zero_even_if_changed: bool,
) -> int:
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

    contents_text = apply_fixers(contents_text, settings, filename)

    if filename == "-":
        print(contents_text, end="")
    elif contents_text != contents_text_orig:
        print(f"Rewriting {filename}", file=sys.stderr)
        with open(filename, "w", encoding="UTF-8", newline="") as f:
            f.write(contents_text)

    if exit_zero_even_if_changed:
        return 0
    return contents_text != contents_text_orig


def apply_fixers(contents_text: str, settings: Settings, filename: str) -> str:
    try:
        ast_obj = ast_parse(contents_text)
    except SyntaxError:
        return contents_text

    callbacks = visit(ast_obj, settings, filename)

    if not callbacks:
        return contents_text

    try:
        tokens = src_to_tokens(contents_text)
    except tokenize.TokenError:  # pragma: no cover (bpo-2180)
        return contents_text

    fixup_dedent_tokens(tokens)

    for i, token in reversed_enumerate(tokens):
        if not token.src:
            continue
        # though this is a defaultdict, by using `.get()` this function's
        # self time is almost 50% faster
        for callback in callbacks.get(token.offset, ()):
            callback(tokens, i)

    return tokens_to_src(tokens)


def fixup_dedent_tokens(tokens: List[Token]) -> None:
    """For whatever reason the DEDENT / UNIMPORTANT_WS tokens are misordered

    | if True:
    |     if True:
    |         pass
    |     else:
    |^    ^- DEDENT
    |+----UNIMPORTANT_WS
    """
    for i, token in enumerate(tokens):
        if token.name == UNIMPORTANT_WS and tokens[i + 1].name == DEDENT:
            tokens[i], tokens[i + 1] = tokens[i + 1], tokens[i]
