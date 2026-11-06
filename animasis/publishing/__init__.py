"""Social media publishing through the vendored SAU runtime."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

_SAU_ROOT = Path(__file__).with_name("_sau")


def _activate_sau() -> None:
    root = str(_SAU_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def main(argv: Sequence[str] | None = None) -> int:
    _activate_sau()
    from ._sau.sau_cli import main as sau_main

    return sau_main(argv)
