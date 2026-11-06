"""Pixel faces for ~11px heads: two eyes, brows, mouth, optional blush/lashes.

Layout (``n``/``m`` = centre column/row of the head, ``f`` = facing):

    m-2  brows            m+2  blush
    m..m+1 eyes (1x2)     m+3  mouth

Eyes and mouth are shifted one pixel toward ``facing`` for a 3/4 side view.
Pass ``view="front"`` for a centred 正体位 face (no shift); ``view="back"``
skips the face entirely (occiput / queue only).
"""

from __future__ import annotations

from typing import Callable

from . import palette as pal

# expression -> parts
EXPRESSIONS: dict[str, dict] = {
    "neutral": {"eyes": "open", "brow": "flat", "mouth": "smile_small"},
    "happy": {"eyes": "happy", "brow": "up", "mouth": "smile"},
    "sad": {"eyes": "open", "brow": "sad", "mouth": "frown"},
    "surprise": {"eyes": "wide", "brow": "up", "mouth": "o"},
    "angry": {"eyes": "open", "brow": "angry", "mouth": "flat"},
    "blink": {"eyes": "closed", "brow": "flat", "mouth": "smile_small"},
}

Put = Callable[[int, int, int], None]


def draw_face(
    put: Put,
    n: int,
    m: int,
    facing: int = 1,
    expression: str = "neutral",
    brow_color: int = pal.HAIR,
    blush: bool = True,
    lashes: bool = False,
    skin_shade: int = pal.SKIN_SHADE,
    view: str = "side",
) -> None:
    """Draw a face onto ``put`` around head centre pixel (n, m)."""
    from .skeleton import normalize_view
    view = normalize_view(view)
    if view == "back":
        return
    expr = EXPRESSIONS.get(expression, EXPRESSIONS["neutral"])
    if view == "front":
        f = 0
        c = n                       # centred 正体位
        e1, e2 = n - 2, n + 2
    else:
        f = 1 if facing >= 0 else -1
        c = n + f                   # face centre column (3/4 view)
        e1, e2 = c - 2, c + 2
    E = pal.EYE

    eyes = expr["eyes"]
    for e in (e1, e2):
        if eyes == "closed":
            put(e - 1 if e == e1 else e, m + 1, E)
            put(e if e == e1 else e + 1, m + 1, E)
        elif eyes == "happy":       # ^ ^  (arched, smiling eyes)
            put(e, m, E)
            put(e - 1, m + 1, E)
            put(e + 1, m + 1, E)
        elif eyes == "wide":
            put(e, m - 1, E)
            put(e, m, E)
            put(e, m + 1, E)
        else:
            put(e, m, E)
            put(e, m + 1, E)
    if lashes and eyes in ("open", "wide"):
        put(e1 - 1, m, E)
        put(e2 + 1, m, E)

    brow = expr["brow"]
    rows = {
        "flat": ((m - 2, m - 2), (m - 2, m - 2)),
        "up": ((m - 3, m - 3), (m - 3, m - 3)),
        "sad": ((m - 2, m - 3), (m - 3, m - 2)),     # inner ends raised
        "angry": ((m - 3, m - 2), (m - 2, m - 3)),   # inner ends lowered
    }[brow]
    (l_out, l_in), (r_in, r_out) = rows
    put(e1 - 1, l_out, brow_color)
    put(e1, l_in, brow_color)
    put(e2, r_in, brow_color)
    put(e2 + 1, r_out, brow_color)

    if blush and eyes != "wide":
        put(e1 - 1, m + 2, pal.BLUSH)
        put(e2 + 1, m + 2, pal.BLUSH)

    mouth = expr["mouth"]
    M = pal.MOUTH
    if mouth == "smile":            # open smile
        put(c - 1, m + 3, M)
        put(c, m + 3, M)
        put(c + 1, m + 3, M)
        put(c, m + 4, pal.BLUSH)
    elif mouth == "smile_small":
        put(c - 1, m + 3, skin_shade)
        put(c, m + 3, M)
        put(c + 1, m + 3, skin_shade)
    elif mouth == "frown":
        put(c - 1, m + 4, M)
        put(c, m + 3, M)
        put(c + 1, m + 4, M)
    elif mouth == "o":
        put(c, m + 3, M)
        put(c, m + 4, M)
    else:  # flat
        put(c - 1, m + 3, M)
        put(c, m + 3, M)
