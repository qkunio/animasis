"""Fixed retro pixel palette — readable silhouettes, warm midtones.

Indices 0–15 are the original environment colours (backgrounds rely on them).
Indices 16–32 extend the palette with character shading ramps (skin, hair,
cloth light/shade), a soft outline, blush and mouth colours.  The palette is
still *fixed*: every pixel the renderer emits is one of these entries.
"""

from __future__ import annotations

from typing import Sequence

PALETTE: list[tuple[int, int, int]] = [
    (15, 15, 25),       # 0  void / outline
    (48, 52, 72),       # 1  shadow
    (90, 98, 120),      # 2  stone
    (170, 178, 190),    # 3  light stone
    (240, 236, 220),    # 4  paper / highlight
    (196, 72, 72),      # 5  red
    (220, 140, 60),     # 6  orange
    (232, 200, 80),     # 7  gold
    (80, 160, 88),      # 8  green
    (64, 140, 180),     # 9  sky blue
    (72, 88, 180),      # 10 deep blue
    (148, 92, 180),     # 11 purple
    (220, 160, 140),    # 12 skin light (legacy)
    (180, 112, 88),     # 13 skin mid (legacy)
    (96, 64, 48),       # 14 brown / hair dark
    (40, 120, 80),      # 15 forest
    # --- character ramps -------------------------------------------------
    (40, 28, 46),       # 16 soft outline (dark plum, less harsh than 0)
    (252, 218, 190),    # 17 skin highlight
    (240, 182, 146),    # 18 skin base
    (206, 134, 106),    # 19 skin shade
    (130, 80, 62),      # 20 tan skin shade
    (238, 122, 118),    # 21 blush
    (146, 48, 62),      # 22 mouth
    (156, 104, 66),     # 23 brown light
    (62, 40, 36),       # 24 brown shade / shoe
    (44, 52, 120),      # 25 blue shade
    (236, 118, 98),     # 26 red light
    (128, 40, 58),      # 27 red shade
    (192, 142, 216),    # 28 purple light
    (94, 56, 130),      # 29 purple shade
    (138, 206, 112),    # 30 green light
    (252, 234, 152),    # 31 blonde light
    (186, 88, 44),      # 32 ginger
]

SKIN = 18
SKIN_SHADE = 19
SKIN_LIGHT = 17
OUTLINE = 0
OUTLINE_SOFT = 16
HAIR = 14
CLOTH_A = 10
CLOTH_B = 5
ACCENT = 7
GROUND = 15
SKY = 9
WALL = 2
FLOOR = 3
WOOD = 14
BALL = 6
PROP = 7
BLUSH = 21
MOUTH = 22
SHOE = 24
GINGER = 32
EYE = 16

# base colour -> (light, base, shade).  Used for 2–3 tone shading of any part.
RAMPS: dict[int, tuple[int, int, int]] = {
    18: (17, 18, 19),     # skin light
    12: (17, 12, 13),     # skin medium
    13: (12, 13, 20),     # skin tan
    14: (23, 14, 24),     # brown
    24: (14, 24, 16),     # dark brown / shoes
    10: (9, 10, 25),      # blue
    9: (4, 9, 10),        # sky
    5: (26, 5, 27),       # red
    11: (28, 11, 29),     # purple
    8: (30, 8, 15),       # green
    15: (8, 15, 1),       # forest
    7: (31, 7, 6),        # gold / blonde
    6: (7, 6, 32),        # orange
    32: (6, 32, 27),      # ginger
    1: (2, 1, 16),        # black / charcoal
    2: (3, 2, 1),         # grey
    3: (4, 3, 2),         # light grey
    4: (4, 4, 3),         # white
    25: (10, 25, 16),     # navy
    27: (5, 27, 16),      # maroon
    29: (11, 29, 16),     # plum
}

SKIN_TONES: dict[str, int] = {"light": 18, "medium": 12, "tan": 13}


def ramp(base: int) -> tuple[int, int, int]:
    """Return (light, base, shade) palette indices for a base colour."""
    if base in RAMPS:
        return RAMPS[base]
    return (base, base, darker(base))


def nearest_palette(rgb: Sequence[int]) -> tuple[int, int, int]:
    """Snap an RGB triple to the closest palette color (Euclidean)."""
    return PALETTE[nearest_index(rgb)]


def nearest_index(rgb: Sequence[int], exclude: int | None = None) -> int:
    r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
    best = 0
    best_d = 1e18
    for i, c in enumerate(PALETTE):
        if i == exclude:
            continue
        d = (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2
        if d < best_d:
            best_d = d
            best = i
    return best


_DARKER: dict[int, int] = {}


def darker(index: int, factor: float = 0.68) -> int:
    """Palette index of a darker tone of ``index`` (used for drop shadows)."""
    key = int(index) % len(PALETTE)
    if key not in _DARKER:
        c = PALETTE[key]
        _DARKER[key] = nearest_index((c[0] * factor, c[1] * factor, c[2] * factor), exclude=key)
    return _DARKER[key]


def color(index: int) -> tuple[int, int, int]:
    return PALETTE[int(index) % len(PALETTE)]
