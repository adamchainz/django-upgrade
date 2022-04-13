from __future__ import annotations

import sys

if sys.version_info >= (3, 9):
    str_removeprefix = str.removeprefix
else:

    def str_removeprefix(self: str, prefix: str, /) -> str:  # pragma: no cover
        if self.startswith(prefix):
            return self[len(prefix) :]
        else:
            return self[:]
