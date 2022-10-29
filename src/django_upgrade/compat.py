from __future__ import annotations

import sys

if sys.version_info >= (3, 9):
    str_removeprefix = str.removeprefix
    str_removesuffix = str.removesuffix
else:

    def str_removeprefix(self: str, prefix: str, /) -> str:  # pragma: no cover
        if self.startswith(prefix):
            return self[len(prefix) :]
        else:
            return self[:]

    def str_removesuffix(self: str, suffix: str, /) -> str:
        # suffix='' should not call self[:-0].
        if suffix and self.endswith(suffix):
            return self[: -len(suffix)]
        else:
            return self[:]
