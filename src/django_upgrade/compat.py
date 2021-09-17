import sys

if sys.version_info >= (3, 9):
    str_removeprefix = str.removeprefix
else:

    def removeprefix(string: str, prefix: str, /) -> str:  # pragma: no cover
        if string.startswith(prefix):
            return string[len(prefix) :]
        else:
            return string[:]
