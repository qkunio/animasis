"""Clothing / prop attachment points on the skeleton."""

from __future__ import annotations

from typing import Any, Callable

from . import palette as pal
from .icons import ICONS, blit_icon
from .skeleton import Character


# Named hang points: (bone, t along bone 0..1)
HANG_POINTS: dict[str, tuple[str, float]] = {
    "head": ("head", 0.5),
    "chest": ("torso", 0.5),
    "hip": ("root", 0.0),
    "hand_l": ("hand_l", 1.0),
    "hand_r": ("hand_r", 1.0),
    "foot_l": ("foot_l", 1.0),
    "foot_r": ("foot_r", 1.0),
    "back": ("torso", 0.3),
}


def resolve_hang(character: Character, hang: str) -> tuple[float, float]:
    bone, t = HANG_POINTS.get(hang, ("hand_r", 1.0))
    return character.skeleton.attach_point(bone, t, character.origin, character.facing)


def draw_hat(put: Callable[[int, int, int], None], x: float, y: float, color: int = pal.ACCENT) -> None:
    hx, hy = int(x), int(y) - 6
    for dx in range(-5, 6):
        put(hx + dx, hy, color)
    for dx in range(-3, 4):
        put(hx + dx, hy - 1, color)
        put(hx + dx, hy - 2, color)
    put(hx, hy - 3, color)


def draw_ball(put: Callable[[int, int, int], None], x: float, y: float, r: int = 4, color: int = pal.BALL) -> None:
    cx, cy = int(x), int(y)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d2 = dx * dx + dy * dy
            if d2 <= r * r:
                put(cx + dx, cy + dy, pal.OUTLINE if d2 > (r - 1) * (r - 1) else color)
    put(cx - 1, cy - 1, 4)


def draw_box(put: Callable[[int, int, int], None], x: float, y: float, w: int = 8, h: int = 8, color: int = pal.WOOD) -> None:
    cx, cy = int(x - w / 2), int(y - h / 2)
    for dy in range(h):
        for dx in range(w):
            c = pal.OUTLINE if dy == 0 or dx == 0 or dy == h - 1 or dx == w - 1 else color
            put(cx + dx, cy + dy, c)


def draw_prop(put: Callable[[int, int, int], None], kind: str, x: float, y: float, **kw: Any) -> None:
    if kind == "ball":
        draw_ball(put, x, y, r=int(kw.get("r", 4)), color=int(kw.get("color", pal.BALL)))
    elif kind == "hat":
        draw_hat(put, x, y, color=int(kw.get("color", pal.ACCENT)))
    elif kind == "box":
        draw_box(put, x, y, w=int(kw.get("w", 8)), h=int(kw.get("h", 8)), color=int(kw.get("color", pal.WOOD)))
    elif kind == "gift":
        draw_box(put, x, y, w=6, h=6, color=pal.ACCENT)
        put(int(x), int(y) - 1, pal.CLOTH_B)
    elif kind in ICONS:  # pixel-art props (icecream, coin, console): held from below
        blit_icon(put, kind, x, y + 2, anchor="bottom" if kind == "icecream" else "center")
    else:
        draw_box(put, x, y, w=4, h=4, color=pal.PROP)
