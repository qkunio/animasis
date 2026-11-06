"""Tiny palette-indexed pixel icons (props, HUD, title cards).

Each icon is a list of strings; every character maps to a palette index via
``KEY`` ('.' is transparent).  ``blit_icon`` draws one with an integer
upscale so the same art works as a held prop (1x) or on a title card (3x).
"""

from __future__ import annotations

from typing import Callable

Put = Callable[[int, int, int], None]

# char -> palette index
KEY: dict[str, int] = {
    "o": 16,  # soft outline
    "K": 0,   # hard black
    "W": 4,   # paper white
    "R": 26,  # strawberry light
    "S": 5,   # red
    "C": 7,   # gold (cone / coin)
    "c": 6,   # orange (cone shade)
    "Y": 31,  # pale yellow highlight
    "L": 3,   # light grey
    "D": 2,   # grey
    "k": 1,   # charcoal
    "B": 9,   # sky screen
    "G": 30,  # green light
    "g": 8,   # green
    "P": 11,  # purple
    "p": 29,  # purple shade
    "N": 14,  # wood brown
    "T": 10,  # deep blue
}

ICONS: dict[str, list[str]] = {
    "icecream": [
        "...ooo...",
        "..oRRRo..",
        ".oRWRRRo.",
        ".oRRRRRo.",
        "oRRRRRRSo",
        "oSRRRSRSo",
        ".oCCCCCo.",
        ".oCcCcCo.",
        "..oCCCo..",
        "..ocCco..",
        "...oCo...",
        "...oco...",
        "....o....",
    ],
    "console": [
        ".ooooooooooooo.",
        "oLLLLLLLLLLLLLo",
        "oLLLoooooooLLLo",
        "oLkLoBBBBBoLLLo",
        "okkkoBGBBBoLSLo",
        "oLkLoBBBgBoSLLo",
        "oLLLoBBBBBoLLLo",
        "oLLLoooooooLLLo",
        "oDDDDDDDDDDDDDo",
        ".ooooooooooooo.",
    ],
    "coin": [
        "..ooo..",
        ".oYYCo.",
        "oYCCCco",
        "oYCcCco",
        "oCCCCco",
        ".occco.",
        "..ooo..",
    ],
    "fan": [                 # 羽扇: white feather fan, brown handle (held from below)
        "..ooooo..",
        ".oWWWWWo.",
        "oWWLWLWWo",
        "oWLWWWLWo",
        "oWWWLWWWo",
        ".oWWLWWo.",
        "..oWLWo..",
        "...oSo...",
        "...oNo...",
        "...oNo...",
        "....o....",
    ],
    "letter": [              # 书信: rolled scroll with a red tie
        ".ooooooooo.",
        "oNWWWSWWWNo",
        "oNWWWSWWWNo",
        "oNWWWSWWWNo",
        ".ooooooooo.",
    ],
    "phone": [               # 手机: black slab, map screen with a blue dot
        "ooooo",
        "oBBBo",
        "oBWBo",
        "oWTWo",
        "oBWBo",
        "oBBBo",
        "ooooo",
    ],
    "edict": [               # 圣旨: imperial-yellow scroll on dark rollers
        "o.........o",
        "ooooooooooo",
        "oNYCCCCCCNo",
        "oNCCcCcCCNo",
        "oNCCCCCCCNo",
        "ooooooooooo",
        "o.........o",
    ],
    "seal": [                # 太子印: gold seal with a knob
        "..ooo..",
        "..oCo..",
        ".ooCoo.",
        "oYCCCCo",
        "oCCSCco",
        "occccco",
        "ooooooo",
    ],
    "doll": [                # 巫蛊人偶: straw doll stuck with a red pin
        "..ooo..",
        ".oNNNoS",
        ".oNNNSo",
        "ooNNSoo",
        "oNNNNNo",
        "o.oNo.o",
        "..oNo..",
        ".oNoNo.",
        ".oo.oo.",
    ],
    "beads": [               # 念珠: prayer beads with a red tassel
        "..ooooo..",
        ".oNo.oNo.",
        "oN.....No",
        "o.......o",
        "oN.....No",
        ".oNo.oNo.",
        "..ooSoo..",
        "...oSo...",
        "..oSSSo..",
    ],
    "flag": [                # 帅旗: red banner with a gold disc, on a pole (held from below)
        "oo.......",
        "oNoooooo.",
        "oNSSSSSSo",
        "oNSSCCSSo",
        "oNSCCCSo.",
        "oNSSCSSo.",
        "oNSSSSo..",
        "oNoooo...",
        "oNo......",
        "oNo......",
        "oNo......",
        "oNo......",
        "oNo......",
        ".o.......",
    ],
    "casket": [              # 锦匣: brocade box for the secret succession edict
        ".ooooooooo.",
        "oCCCCCCCCCo",
        "ooooooooooo",
        "oSSSSCSSSSo",
        "oSSSCYCSSSo",
        "oSSSSCSSSSo",
        "oSSSSSSSSSo",
        ".ooooooooo.",
    ],
    "cross": [
        "SS.....SS",
        "SSS...SSS",
        ".SSS.SSS.",
        "..SSSSS..",
        "...SSS...",
        "..SSSSS..",
        ".SSS.SSS.",
        "SSS...SSS",
        "SS.....SS",
    ],
}


def icon_size(name: str, scale: int = 1) -> tuple[int, int]:
    art = ICONS[name]
    return len(art[0]) * scale, len(art) * scale


def blit_icon(put: Put, name: str, x: float, y: float, scale: int = 1, anchor: str = "center") -> None:
    """Draw icon ``name``; ``anchor`` is 'center', 'bottom' (x centre, y bottom) or 'topleft'."""
    art = ICONS.get(name)
    if not art:
        return
    s = max(1, int(scale))
    w, h = len(art[0]) * s, len(art) * s
    if anchor == "center":
        x0, y0 = int(round(x - w / 2)), int(round(y - h / 2))
    elif anchor == "bottom":
        x0, y0 = int(round(x - w / 2)), int(round(y - h))
    else:
        x0, y0 = int(x), int(y)
    for j, row in enumerate(art):
        for i, ch in enumerate(row):
            c = KEY.get(ch)
            if c is None:
                continue
            for dy in range(s):
                for dx in range(s):
                    put(x0 + i * s + dx, y0 + j * s + dy, c)
