"""Tang-dynasty set dressing for the Li Shimin biography.

Backgrounds (cached, 320x180 stage): 武功庭院、雁门雪原、晋阳军营、军帐、霍邑雨城、
浅水原、柏壁雪原、虎牢关、长安城门、秦王府书房、宫廊、玄武门、太极殿、贞观农田、
长安西市、突厥草原、丝路、昭陵。

World-space overlays: 战马（可带骑手）、骆驼、军帐、篝火、箭雨、尘土、雨、军阵。
"""

from __future__ import annotations

import math
from typing import Any, Callable

from . import palette as pal

Put = Callable[[int, int, int], None]
Pix = tuple[int, int]

TANG_KINDS = {"horse", "camel", "tent", "campfire", "arrow", "dust", "army"}
BG: dict[str, Callable[[list[list[int]], int, int, int], None]] = {}
_CACHE: dict[tuple[str, int, int, int], list[list[int]]] = {}


# --------------------------------------------------------------------------- primitives

def _new(w: int, h: int, c: int = 0) -> list[list[int]]:
    return [[c] * w for _ in range(h)]


def _rect(b: list[list[int]], x0: float, y0: float, x1: float, y1: float, c: int) -> None:
    h, w = len(b), len(b[0])
    for y in range(max(0, int(y0)), min(h, int(y1))):
        row = b[y]
        for x in range(max(0, int(x0)), min(w, int(x1))):
            row[x] = c


def _px(b: list[list[int]], x: int, y: int, c: int) -> None:
    if 0 <= y < len(b) and 0 <= x < len(b[0]):
        b[y][x] = c


def _line(b: list[list[int]], x0: float, y0: float, x1: float, y1: float, c: int, width: int = 1) -> None:
    n = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
    r = max(0, width // 2)
    for i in range(n + 1):
        u = i / n
        x, y = int(round(x0 + (x1 - x0) * u)), int(round(y0 + (y1 - y0) * u))
        for oy in range(-r, r + 1):
            for ox in range(-r, r + 1):
                _px(b, x + ox, y + oy, c)


def _ellipse(b: list[list[int]], cx: float, cy: float, rx: float, ry: float, c: int) -> None:
    h, w = len(b), len(b[0])
    for y in range(max(0, int(cy - ry) - 1), min(h, int(cy + ry) + 2)):
        for x in range(max(0, int(cx - rx) - 1), min(w, int(cx + rx) + 2)):
            if ((x + 0.5 - cx) / max(rx, 0.1)) ** 2 + ((y + 0.5 - cy) / max(ry, 0.1)) ** 2 <= 1:
                b[y][x] = c


def _poly(b: list[list[int]], pts: list[tuple[float, float]], c: int) -> None:
    if not pts:
        return
    h, w = len(b), len(b[0])
    y0 = max(0, int(min(p[1] for p in pts)))
    y1 = min(h - 1, int(max(p[1] for p in pts)))
    for y in range(y0, y1 + 1):
        xs = []
        for i, (x1, y1p) in enumerate(pts):
            x2, y2 = pts[(i + 1) % len(pts)]
            if (y1p <= y < y2) or (y2 <= y < y1p):
                xs.append(x1 + (x2 - x1) * (y - y1p) / (y2 - y1p))
        xs.sort()
        for a, bb in zip(xs[0::2], xs[1::2]):
            for x in range(max(0, int(a)), min(w, int(bb) + 1)):
                b[y][x] = c


def _sky(b: list[list[int]], g: int, bands: list[tuple[int, int]], dither: bool = True) -> None:
    h, w = len(b), len(b[0])
    prev = 0
    for end, c in bands:
        for y in range(prev, min(g, end)):
            for x in range(w):
                b[y][x] = c
        if dither and prev > 0:
            for x in range(w):
                if (x + prev) % 3:
                    b[prev][x] = c
        prev = end


def _hills(b: list[list[int]], g: int, base: int, amp: float, freq: float, c: int, phase: float = 0.0) -> None:
    w = len(b[0])
    for x in range(w):
        y = base - int(amp * math.sin(x / freq + phase) + amp * 0.4 * math.sin(x / (freq * 0.37) + 1.3))
        _rect(b, x, max(0, y), x + 1, g, c)


def _mountain(b: list[list[int]], cx: int, base: int, half: int, height: int, c: int, snow: int | None = None) -> None:
    w, h = len(b[0]), len(b)
    for x in range(max(0, cx - half), min(w, cx + half + 1)):
        u = abs(x - cx) / max(1, half)
        y = base - int(height * (1 - u) ** 1.25)
        _rect(b, x, max(0, y), x + 1, min(h, base), c)
        if snow is not None:
            cap = y + max(3, int(height * 0.22 * (1 - u)))
            for yy in range(max(0, y), min(base, cap)):
                if (x + yy) % 3 != 0:
                    _px(b, x, yy, snow)


def _pine(b: list[list[int]], x: int, gy: int, h: int, c1: int = 15, c2: int = 8) -> None:
    _rect(b, x, gy - h, x + 1, gy, 14)
    for i in range(3):
        yy = gy - h + i * h // 3
        half = max(2, (h // 3) - i)
        _poly(b, [(x + 1, yy - 4), (x - half, yy + 5), (x + half + 2, yy + 5)], c1 if i % 2 else c2)


def _roof(b: list[list[int]], x0: int, y0: int, x1: int, hgt: int, c1: int = 24, c2: int = 14,
          ridge: int = 16) -> None:
    """Tiled Chinese roof with flared eaves; x0..x1 is the eave span, y0 its top edge."""
    for i in range(hgt):
        k = i / max(1, hgt - 1)
        inset = int((x1 - x0) * 0.18 * k)
        a, z = x0 + inset, x1 - inset
        _rect(b, a, y0 + i, z, y0 + i + 1, c1 if i % 3 else c2)
        _px(b, a - 1, y0 + i, 16)
        _px(b, z, y0 + i, 16)
    _rect(b, x0 - 1, y0 + hgt - 2, x1 + 1, y0 + hgt, 16)
    _rect(b, x0, y0 + hgt, x1, y0 + hgt + 1, c2)
    _rect(b, x0 + int((x1 - x0) * 0.15), y0 - 2, x1 - int((x1 - x0) * 0.15), y0, ridge)


def _wall(b: list[list[int]], x0: int, y0: int, x1: int, gy: int, c: int = 5, shade: int = 27,
          base: int = 3) -> None:
    _rect(b, x0, y0, x1, gy, c)
    for y in range(y0, gy):
        for x in range(x0, x1):
            if (x * 7 + y * 3) % 29 == 0:
                b[y][x] = shade
    _rect(b, x0, gy - 5, x1, gy, base)
    _rect(b, x0, gy - 5, x1, gy - 4, 4)
    _rect(b, x0, y0, x1, y0 + 2, 16)
    _rect(b, x0, y0, x0 + 2, gy, shade)
    _rect(b, x1 - 2, y0, x1, gy, shade)


def _lattice(b: list[list[int]], x0: int, y0: int, x1: int, y1: int, frame: int = 14,
             paper: int = 24, bar: int = 7) -> None:
    _rect(b, x0, y0, x1, y1, frame)
    _rect(b, x0 + 2, y0 + 2, x1 - 2, y1 - 2, paper)
    for x in range(x0 + 3, x1 - 2, 4):
        _rect(b, x, y0 + 3, x + 1, y1 - 3, bar)
    for y in range(y0 + 3, y1 - 2, 4):
        _rect(b, x0 + 3, y, x1 - 3, y + 1, bar)


def _tent_bg(b: list[list[int]], x: int, gy: int, w: int, hgt: int, c1: int = 24, c2: int = 23,
             lit: bool = False) -> None:
    _poly(b, [(x, gy - hgt), (x - w // 2, gy), (x + w // 2, gy)], c1)
    _poly(b, [(x, gy - hgt), (x - w // 2 + 3, gy - 2), (x, gy - 2)], c2)
    _line(b, x, gy - hgt, x, gy, 14, 1)
    _rect(b, x - 2, gy - 4, x + 2, gy, 7 if lit else 16)
    _px(b, x, gy - hgt - 1, 7)
    _line(b, x - w // 4, gy - hgt // 2, x - w // 2 - 2, gy, 14, 1)
    _line(b, x + w // 4, gy - hgt // 2, x + w // 2 + 2, gy, 14, 1)


def _banner_bg(b: list[list[int]], x: int, gy: int, hgt: int, c: int = 5) -> None:
    _rect(b, x, gy - hgt, x + 1, gy, 14)
    _px(b, x, gy - hgt - 1, 7)
    fw, fh = 8, 16
    for i in range(fw):
        for j in range(fh):
            _px(b, x + 2 + i, gy - hgt + 2 + j, 7 if (i == 0 or j == 0) else c)


def _crowd(b: list[list[int]], x0: int, x1: int, gy: int, color: int = 16, n: int = 20) -> None:
    for i in range(n):
        x = x0 + (x1 - x0) * i // max(1, n - 1)
        hh = 6 + (i * 7) % 4
        _rect(b, x, gy - hh, x + 2, gy, color)
        _px(b, x + 0, gy - hh - 1, color)
        _px(b, x + 1, gy - hh - 2, color)


def _stars(b: list[list[int]], g: int, n: int = 50) -> None:
    w = len(b[0])
    for i in range(n):
        x, y = (i * 83 + 7) % w, (i * 47 + 3) % max(1, g - 20)
        _px(b, x, y, (4, 3, 2, 31)[i % 4])


def _sun(b: list[list[int]], cx: int, cy: int, r: int, c: int = 7, halo: int = 6) -> None:
    _ellipse(b, cx, cy, r + 3, r + 3, halo)
    _ellipse(b, cx, cy, r, r, c)


# --------------------------------------------------------------------------- backgrounds

def _yard(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 9)
    _sky(b, g, [(0, 10), (38, 9), (82, 3), (150, 3)])
    _sun(b, 250, 34, 8, 7, 31)
    _hills(b, 118, 98, 5, 28, 15)
    _hills(b, 118, 108, 3, 17, 8, 1.2)
    # low white wall across the back
    _rect(b, 0, 108, 198, g, 4)
    for y in range(108, g):
        for x in range(0, 198):
            if (x * 5 + y * 3) % 31 == 0:
                b[y][x] = 3
    _rect(b, 0, 104, 198, 108, 24)
    _rect(b, 0, 103, 198, 104, 16)
    for x in range(0, 198, 6):
        _rect(b, x, 104, x + 3, 107, 14)
    # tiled-roof house on the right
    _rect(b, 196, 96, 320, g, 4)
    _rect(b, 220, 118, 260, g, 14)
    _rect(b, 222, 120, 258, g, 24)
    _rect(b, 228, 126, 252, 144, 5)
    _rect(b, 236, 126, 244, 144, 27)
    for j in range(5):
        _rect(b, 236, 128 + j * 4, 244, 129 + j * 4, 7)
    _lattice(b, 268, 116, 302, 140, 14, 24, 7)
    _roof(b, 190, 82, 320, 16, 24, 14, 16)
    # ground: packed earth, stone path, grass
    for y in range(g, h):
        for x in range(w):
            b[y][x] = 23 if (x // 7 + y) % 5 else 24
            if (x * 13 + y * 7) % 97 == 0:
                b[y][x] = 14
    for x in range(70, 250):
        _px(b, x, g + 7 + (x // 20), 3)
        _px(b, x, g + 8 + (x // 20), 2)
    for i in range(28):
        x, y = (i * 37 + 13) % w, g + 3 + (i * 19) % 24
        _px(b, x, y, 8 if i % 3 else 15)
    # archery target on a wooden stand
    tx, ty = 62, 116
    _rect(b, tx - 1, ty + 16, tx + 2, g, 14)
    _line(b, tx - 6, g - 2, tx, ty + 18, 14, 1)
    _line(b, tx + 7, g - 2, tx, ty + 18, 14, 1)
    _ellipse(b, tx, ty, 13, 13, 16)
    _ellipse(b, tx, ty, 12, 12, 31)
    _ellipse(b, tx, ty, 9, 9, 6)
    _ellipse(b, tx, ty, 6, 6, 31)
    _ellipse(b, tx, ty, 3, 3, 5)
    _ellipse(b, tx, ty, 1, 1, 16)
    # a few arrows in the target
    for dx, dy in ((-4, 3), (2, -2), (5, 5)):
        _line(b, tx + dx, ty + dy, tx + dx - 8, ty + dy + 5, 3, 1)
        _px(b, tx + dx - 8, ty + dy + 5, 5)
    # tree and stone table
    _rect(b, 172, 112, 175, g, 14)
    _ellipse(b, 172, 104, 14, 10, 15)
    _ellipse(b, 166, 99, 8, 6, 8)
    _rect(b, 118, 138, 142, 141, 3)
    _rect(b, 122, 141, 126, g, 2)
    _rect(b, 134, 141, 138, g, 2)
    for x in range(w):
        b[g][x] = 16
    return b


def _snow_frontier(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 25)
    _sky(b, g, [(0, 25), (36, 10), (70, 9), (98, 4), (150, 4)])
    _sun(b, 258, 34, 7, 4, 9)
    _mountain(b, 66, 112, 70, 52, 2, 4)
    _mountain(b, 160, 116, 80, 44, 2, 4)
    _mountain(b, 276, 112, 64, 50, 2, 4)
    _hills(b, 120, 108, 3, 19, 15)
    # Great Wall across the pass
    for x in range(0, w):
        wy = 104 + int(3 * math.sin(x / 26.0))
        _rect(b, x, wy, x + 1, wy + 16, 2)
        _rect(b, x, wy, x + 1, wy + 2, 3)
        if x % 7 < 3:
            _rect(b, x, wy - 3, x + 1, wy, 2)
    # watchtower
    _rect(b, 232, 78, 258, 122, 2)
    _rect(b, 230, 78, 260, 82, 3)
    _rect(b, 238, 88, 252, 108, 16)
    _lattice(b, 240, 90, 250, 102, 16, 9, 16)
    _roof(b, 224, 72, 266, 8, 24, 14, 16)
    _rect(b, 242, 70, 248, 78, 2)
    # pines
    for x, hh in ((24, 30), (44, 22), (288, 28), (304, 20)):
        _pine(b, x, 120, hh, 15, 16)
    # snow ground with blue shadows
    for y in range(g, h):
        for x in range(w):
            b[y][x] = 4 if (x // 9 + y // 3) % 7 else 3
            if (x * 5 + y * 7) % 61 == 0:
                b[y][x] = 9
    for x in range(0, w, 13):
        yy = g + 2 + (x * 7) % 20
        _rect(b, x, yy, x + 3, yy + 1, 25)
    for x in range(w):
        b[g][x] = 3
    # distant campfires
    for x, y in ((206, 112), (214, 110), (222, 113)):
        _px(b, x, y, 7)
        _px(b, x + 1, y, 6)
    return b


def _taiyuan_camp(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 25)
    _sky(b, g, [(0, 25), (46, 10), (92, 16), (150, 16)])
    _stars(b, 110, 60)
    _sun(b, 58, 28, 7, 4, 9)
    # distant Taiyuan wall with towers
    _rect(b, 0, 96, w, 128, 16)
    for x in range(0, w, 26):
        _rect(b, x, 92, x + 11, 128, 16)
        _rect(b, x + 2, 95, x + 9, 99, 7 if (x // 26) % 2 else 6)
        _rect(b, x + 4, 104, x + 6, 108, 7)
        _rect(b, x + 7, 112, x + 9, 115, 6)
    for x in range(0, w, 9):
        _rect(b, x, 94, x + 4, 96, 2)
    _rect(b, 0, 126, w, 130, 2)
    # ground
    for y in range(g, h):
        for x in range(w):
            b[y][x] = 24 if (x // 6 + y) % 4 else 16
            if (x * 11 + y * 5) % 83 == 0:
                b[y][x] = 2
    # tents: canvas with warm flaps
    _tent_bg(b, 54, g, 40, 30, 23, 24, False)
    _tent_bg(b, 108, g, 32, 24, 23, 24, True)
    _tent_bg(b, 176, g, 28, 22, 23, 24, False)
    _tent_bg(b, 246, g, 58, 38, 23, 24, True)
    # command tent banner and pennants
    _banner_bg(b, 276, g, 50, 5)
    _banner_bg(b, 30, g, 40, 7)
    # campfires with glow
    for cx in (34, 82, 150, 214):
        _ellipse(b, cx, g - 1, 8, 3, 6)
        _ellipse(b, cx, g - 2, 4, 2, 7)
        _rect(b, cx - 4, g - 3, cx + 5, g - 1, 24)
        _px(b, cx - 2, g - 5, 7)
        _px(b, cx, g - 6, 6)
        _px(b, cx + 2, g - 5, 7)
        _px(b, cx, g - 7, 31)
        _px(b, cx - 1, g - 10, 2)
        _px(b, cx + 1, g - 13, 3)
    for x in range(w):
        b[g][x] = 16
    return b


def _war_room(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 24)
    # canvas tent: dark ceiling, warm walls, wooden poles
    _rect(b, 0, 0, w, 12, 16)
    _rect(b, 0, 12, w, g - 16, 23)
    for x in range(0, w, 28):
        _rect(b, x, 12, x + 1, g - 16, 24)
    for y in range(12, g - 16, 20):
        _rect(b, 0, y, w, y + 1, 24)
    _rect(b, 0, 0, w, 3, 14)
    for x in range(0, w, 20):
        _rect(b, x, 3, x + 3, 12, 14)
    # hanging war map
    _rect(b, 44, 28, 276, 92, 16)
    _rect(b, 46, 30, 274, 90, 4)
    for x in range(48, 272, 5):
        _px(b, x, 31, 3)
    # map rivers / mountains / tokens
    _line(b, 56, 58, 92, 50, 9, 2)
    _line(b, 92, 50, 132, 60, 9, 2)
    _line(b, 132, 60, 176, 48, 9, 2)
    _line(b, 176, 48, 218, 58, 9, 2)
    for x, y in ((70, 50), (116, 55), (160, 52), (204, 54), (240, 48)):
        _poly(b, [(x, y), (x + 4, y + 5), (x + 8, y)], 16)
    for x, y, c in ((86, 56, 5), (126, 54, 5), (168, 58, 10), (208, 52, 10), (236, 58, 5)):
        _rect(b, x, y, x + 5, y + 3, c)
    _line(b, 168, 58, 195, 48, 7, 1)
    _line(b, 126, 54, 148, 62, 7, 1)
    # cords and scroll rack
    _line(b, 44, 28, 40, 20, 14, 1)
    _line(b, 276, 28, 280, 20, 14, 1)
    # side banners
    for x, c in ((20, 5), (300, 5)):
        _rect(b, x, 34, x + 10, 84, 16)
        _rect(b, x + 1, 35, x + 9, 83, c)
        for k in range(5):
            _px(b, x + 5, 42 + k * 7, 7)
    # floor: carpet and wooden edge
    _rect(b, 0, g - 6, w, h, 14)
    _rect(b, 0, g - 8, w, g - 2, 27)
    for x in range(0, w, 18):
        _rect(b, x, g - 7, x + 9, g - 6, 7 if x % 36 else 5)
    for x in range(w):
        b[g - 1][x] = 16
    # armor stand
    _rect(b, 282, 72, 285, g - 4, 14)
    _rect(b, 270, 70, 297, 72, 14)
    _rect(b, 272, 76, 295, 104, 16)
    _rect(b, 273, 77, 294, 103, 2)
    _rect(b, 276, 83, 291, 92, 3)
    _rect(b, 279, 86, 288, 90, 7)
    _ellipse(b, 283, 72, 9, 6, 3)
    _rect(b, 281, 64, 285, 70, 3)
    _px(b, 283, 62, 5)
    # scroll chest and lamp
    _rect(b, 14, 112, 44, g - 8, 14)
    _rect(b, 14, 112, 44, 116, 23)
    _rect(b, 26, 112, 32, g - 8, 7)
    for cx in (58, 250):
        _rect(b, cx - 1, 104, cx + 2, 118, 4)
        _rect(b, cx - 4, 118, cx + 5, 120, 6)
        _px(b, cx, 101, 7)
        _px(b, cx, 100, 31)
    # hanging lantern
    _rect(b, 160, 0, 161, 12, 16)
    _ellipse(b, 160, 18, 6, 7, 5)
    _rect(b, 155, 11, 165, 12, 7)
    _rect(b, 155, 24, 165, 25, 7)
    _px(b, 160, 18, 7)
    return b


def _huoyi_gate(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 2)
    _sky(b, g, [(0, 2), (36, 16), (80, 25), (150, 25)])
    _hills(b, 100, 88, 6, 21, 16)
    # city wall and gate
    _wall(b, 0, 78, w, 128, 2, 3, 3)
    _rect(b, 0, 74, w, 78, 16)
    for x in range(0, w, 12):
        _rect(b, x, 70, x + 6, 74, 2)
    _rect(b, 128, 84, 192, 128, 16)
    _poly(b, [(128, 84), (160, 66), (192, 84)], 2)
    _rect(b, 136, 92, 184, 128, 0)
    _rect(b, 140, 96, 180, 128, 16)
    # towers
    for cx in (48, 268):
        _rect(b, cx - 18, 56, cx + 18, 84, 2)
        _lattice(b, cx - 10, 62, cx + 10, 78, 14, 24, 5)
        _roof(b, cx - 24, 48, cx + 24, 10, 24, 14, 16)
        _banner_bg(b, cx + 22, 84, 32, 5)
    # wet ground / mud / puddles
    for y in range(g, h):
        for x in range(w):
            b[y][x] = 24 if (x // 5 + y) % 4 else 16
            if (x * 7 + y * 5) % 71 == 0:
                b[y][x] = 9
            if (x * 3 + y * 11) % 53 == 0:
                b[y][x] = 2
    for x in range(0, w, 17):
        _rect(b, x, g + 4 + (x * 5) % 18, x + 7, g + 6 + (x * 5) % 18, 9)
    # broken spears and fallen banner
    for x, y in ((60, 142), (86, 138), (220, 144), (244, 140)):
        _line(b, x, y, x + 12, y - 8, 14, 1)
        _px(b, x + 12, y - 9, 3)
    _line(b, 250, g - 2, 270, g - 2, 14, 1)
    _rect(b, 244, g - 6, 252, g - 2, 5)
    for x in range(w):
        b[g][x] = 16
    return b


def _loess(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 6)
    _sky(b, g, [(0, 6), (40, 7), (78, 31), (150, 31)])
    _sun(b, 76, 44, 11, 31, 7)
    # dusty horizon and loess terraces
    for x in range(w):
        yy = 88 + int(4 * math.sin(x / 27.0))
        _px(b, x, yy, 23)
        _px(b, x, yy + 1, 24)
    _hills(b, 118, 100, 8, 34, 23)
    _hills(b, 118, 112, 5, 19, 24, 2.1)
    for x in range(0, w, 9):
        yy = 108 + int(3 * math.sin(x / 13.0))
        _rect(b, x, yy, x + 4, yy + 1, 16)
    # deep gullies
    for x0, y0, x1, y1 in ((20, 112, 64, 132), (70, 108, 112, 130), (210, 110, 256, 134), (268, 106, 306, 130)):
        _line(b, x0, y0, x1, y1, 16, 2)
        _line(b, x0 + 2, y0 + 2, x1 - 2, y1 - 2, 14, 1)
    # distant enemy line: three ranks, spears, banners
    for row in (0, 1, 2):
        for i in range(30):
            x = 10 + i * 10 + row * 4
            y = 124 - row * 7
            _rect(b, x, y, x + 2, y + 6, 16)
            _px(b, x, y - 1, 16)
            _line(b, x - 2, y + 2, x - 2, y - 7 - row, 3, 1)
            if i % 5 == 0:
                _px(b, x + 1, y - 6, 7)
        _banner_bg(b, 56 + row * 100, 130 - row * 7, 22, 5)
        _banner_bg(b, 156 + row * 80, 130 - row * 7, 22, 7)
    # broken war cart
    _rect(b, 262, 132, 292, 138, 14)
    _ellipse(b, 268, 140, 5, 4, 2)
    _ellipse(b, 286, 140, 5, 4, 2)
    _line(b, 262, 132, 250, 122, 14, 2)
    _line(b, 292, 132, 300, 122, 14, 2)
    # rocks, dead tree, spears
    for x, y in ((30, 140), (52, 146), (300, 142), (88, 144)):
        _poly(b, [(x, y), (x + 8, y - 6), (x + 16, y)], 2)
    _rect(b, 36, 118, 38, 142, 14)
    _line(b, 37, 124, 28, 116, 14, 1)
    _line(b, 38, 128, 48, 120, 14, 1)
    for x, y in ((120, 142), (144, 140), (230, 144)):
        _line(b, x, y, x + 10, y - 9, 14, 1)
        _px(b, x + 10, y - 10, 3)
    # dusty ground
    for y in range(g, h):
        for x in range(w):
            b[y][x] = 23 if (x // 4 + y) % 5 else 24
            if (x * 7 + y * 3) % 89 == 0:
                b[y][x] = 6
    for x in range(w):
        b[g][x] = 16
    return b


def _snow_battle(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 3)
    _sky(b, g, [(0, 3), (50, 4), (95, 25), (150, 25)])
    _hills(b, 110, 92, 8, 30, 2)
    _hills(b, 110, 100, 4, 17, 16, 2.2)
    # pines
    for x, hh in ((16, 30), (40, 22), (284, 28), (306, 20), (76, 18)):
        _pine(b, x, 128, hh, 15, 16)
    # abandoned tents and banners
    _tent_bg(b, 210, 132, 30, 22, 24, 23, False)
    _tent_bg(b, 250, 136, 24, 18, 24, 23, False)
    _banner_bg(b, 186, 136, 26, 5)
    _line(b, 270, 138, 286, 132, 14, 1)
    # distant enemy line
    for i in range(18):
        x = 90 + i * 9
        _rect(b, x, 120, x + 2, 126, 16)
        _line(b, x - 2, 122, x - 2, 114, 3, 1)
    # snow
    for y in range(g, h):
        for x in range(w):
            b[y][x] = 4 if (x // 8 + y // 3) % 8 else 3
            if (x * 7 + y * 5) % 67 == 0:
                b[y][x] = 9
    for x in range(0, w, 11):
        yy = g + 2 + (x * 5) % 22
        _rect(b, x, yy, x + 4, yy + 1, 25)
    for x in range(w):
        b[g][x] = 3
    return b


def _hulao(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 6)
    _sky(b, g, [(0, 6), (34, 7), (72, 31), (150, 31)])
    for cx, cy, r in ((60, 28, 8), (78, 24, 5), (250, 20, 7), (270, 26, 4)):
        _ellipse(b, cx, cy, r + 4, max(2, r // 2), 26)
    _sun(b, 236, 50, 12, 7, 6)
    # mountain ridges: far, mid, near
    _mountain(b, 30, 138, 100, 74, 2, 16)
    _mountain(b, 292, 140, 100, 78, 2, 16)
    _mountain(b, 100, 140, 70, 50, 24, 16)
    _mountain(b, 220, 140, 70, 52, 24, 16)
    _mountain(b, 160, 142, 42, 34, 16, 24)
    _hills(b, 118, 108, 3, 26, 25)
    # fortress on the pass
    _rect(b, 146, 104, 176, 120, 2)
    for x in range(146, 176, 6):
        _rect(b, x, 100, x + 3, 104, 2)
    _rect(b, 156, 96, 166, 106, 16)
    _banner_bg(b, 178, 120, 22, 5)
    # valley floor
    _rect(b, 0, 116, w, 144, 15)
    for y in range(116, 144):
        for x in range(w):
            b[y][x] = 8 if (x // 4 + y) % 6 else 15
    # river winding through the valley
    pts = []
    for i in range(34):
        xx = 34 + i * 8
        yy = 140 - int(9 * math.sin(i / 5.0)) - i // 3
        pts.append((xx, yy))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        _line(b, x0, y0, x1, y1, 9, 4)
        _line(b, x0, y0 - 1, x1, y1 - 1, 10, 1)
    # enemy camp: many tents, fires, banners
    for i, (x, yy) in enumerate(((66, 126), (84, 122), (102, 128), (122, 123), (142, 127),
                                  (164, 122), (184, 126), (204, 121), (224, 125), (244, 122), (262, 127))):
        _tent_bg(b, x, yy + 10, 16, 12, 24, 23, False)
        if i % 2 == 0:
            _px(b, x, yy + 7, 7)
            _px(b, x + 1, yy + 6, 6)
            _px(b, x - 1, yy + 8, 6)
        _banner_bg(b, x + 10, yy + 10, 13, 5)
    # foreground cliff edge
    _poly(b, [(0, g), (0, 140), (36, 134), (72, 141), (112, 136), (160, 142),
              (208, 136), (252, 141), (286, 135), (320, 140), (320, g)], 16)
    for x in range(w):
        b[g - 1][x] = 16
    for x, y in ((20, 144), (48, 138), (92, 145), (270, 139), (300, 144)):
        _poly(b, [(x, y), (x + 7, y - 5), (x + 14, y)], 24)
    for x, hh in ((14, 20), (306, 18), (286, 14)):
        _pine(b, x, 142, hh, 15, 16)
    return b


def _changan_gate(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 9)
    _sky(b, g, [(0, 9), (48, 3), (86, 3), (150, 3)])
    _sun(b, 66, 32, 9, 7, 31)
    for cx, cy, r in ((130, 26, 5), (146, 22, 7), (164, 28, 4)):
        _ellipse(b, cx, cy, r + 3, max(2, r // 2), 4)
    # distant rooftops
    for x in range(0, w, 26):
        _rect(b, x, 86, x + 20, 104, 4)
        _roof(b, x - 2, 80, x + 22, 6, 24, 14, 16)
    # red wall with brick lines and stone base
    _wall(b, 0, 84, w, 130, 5, 27, 3)
    for x in range(0, w, 6):
        _rect(b, x, 86, x + 2, 128, 27)
    for y in range(90, 128, 6):
        _rect(b, 0, y, w, y + 1, 27)
    for x in range(0, w, 12):
        _rect(b, x, 82, x + 6, 86, 16)
        _rect(b, x + 2, 84, x + 4, 86, 7)
    # gate tower
    _rect(b, 108, 52, 212, 92, 5)
    for x in range(112, 208, 10):
        _rect(b, x, 56, x + 2, 90, 27)
        _rect(b, x + 3, 56, x + 4, 90, 26)
    _lattice(b, 124, 62, 152, 82, 14, 24, 7)
    _lattice(b, 168, 62, 196, 82, 14, 24, 7)
    _roof(b, 100, 42, 220, 12, 24, 14, 16)
    _roof(b, 92, 32, 228, 10, 24, 14, 16)
    for x in range(96, 224, 5):
        _px(b, x, 43, 16)
        _px(b, x, 33, 16)
    # gate arch with wooden doors and studs
    _rect(b, 134, 98, 186, 130, 16)
    _rect(b, 140, 104, 180, 130, 14)
    for x in range(142, 180, 4):
        _rect(b, x, 104, x + 1, 130, 24)
    for y in range(108, 128, 5):
        for x in range(144, 180, 6):
            _px(b, x, y, 7)
    # banners and lanterns
    _banner_bg(b, 88, 92, 34, 5)
    _banner_bg(b, 226, 92, 34, 5)
    for x in (120, 200):
        _rect(b, x, 88, x + 1, 98, 16)
        _ellipse(b, x, 102, 3, 4, 5)
        _px(b, x, 102, 7)
    # road and colored crowd
    for y in range(g, h):
        for x in range(w):
            b[y][x] = 3 if (x // 6 + y) % 4 else 2
    _rect(b, 142, g, 178, h, 5)
    for i in range(26):
        x = 4 + i * 12
        c = (16, 24, 27, 25, 5, 9, 7, 11)[i % 8]
        _crowd(b, x, x + 8, g - 1, c, 2)
    for x in (28, 292):
        _rect(b, x, 136, x + 9, 150, 3)
        _ellipse(b, x + 4, 134, 5, 4, 3)
        _px(b, x + 2, 131, 4)
        _px(b, x + 6, 131, 4)
    for x in range(w):
        b[g][x] = 16
    return b


def _qinwang_study(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 24)
    # wooden wall
    _rect(b, 0, 0, w, 12, 16)
    _rect(b, 0, 12, w, g - 10, 14)
    for x in range(0, w, 28):
        _rect(b, x, 12, x + 2, g - 10, 24)
        _rect(b, x + 2, 12, x + 3, g - 10, 23)
    # floor
    _rect(b, 0, g - 10, w, h, 24)
    for x in range(0, w, 16):
        _rect(b, x, g - 10, x + 1, h, 14)
    for y in range(g - 6, h, 5):
        _rect(b, 0, y, w, y + 1, 14)
    _rect(b, 0, g - 12, w, g - 8, 27)
    # moonlit lattice window
    _rect(b, 24, 30, 78, 88, 16)
    _rect(b, 26, 32, 76, 86, 25)
    _sun(b, 50, 48, 5, 4, 9)
    _lattice(b, 24, 30, 78, 88, 14, 25, 14)
    # wall map
    _rect(b, 158, 30, 300, 94, 16)
    _rect(b, 160, 32, 298, 92, 4)
    for x in range(162, 296, 6):
        _px(b, x, 33, 3)
    _line(b, 170, 62, 196, 52, 9, 2)
    _line(b, 196, 52, 232, 62, 9, 2)
    _line(b, 232, 62, 270, 50, 9, 2)
    for x, y in ((184, 52), (218, 56), (256, 48), (282, 56)):
        _poly(b, [(x, y), (x + 4, y + 5), (x + 8, y)], 16)
    for x, y, c in ((190, 60, 5), (224, 58, 10), (258, 60, 5)):
        _rect(b, x, y, x + 4, y + 3, c)
    _line(b, 224, 58, 246, 48, 7, 1)
    # bookshelf
    _rect(b, 86, 40, 148, 124, 14)
    for sy in (52, 72, 92, 112):
        _rect(b, 86, sy, 148, sy + 2, 23)
    for i, (bx, by) in enumerate(((90, 44), (98, 46), (108, 42), (120, 44), (132, 46),
                                  (90, 64), (102, 66), (116, 64), (130, 66),
                                  (92, 84), (110, 82), (126, 84),
                                  (94, 104), (110, 102), (126, 104))):
        _rect(b, bx, by, bx + 4, by + 8, (4, 3, 7, 31, 5)[i % 5])
        _rect(b, bx, by + 7, bx + 4, by + 8, 16)
    # books/scrolls on the desk
    _rect(b, 118, 126, 208, 132, 23)
    _rect(b, 118, 132, 208, 136, 14)
    for x in (124, 198):
        _rect(b, x, 136, x + 4, g, 14)
    _rect(b, 126, 128, 176, 131, 4)
    _line(b, 130, 129, 150, 129, 9, 1)
    _rect(b, 182, 124, 198, 128, 5)
    _rect(b, 186, 120, 194, 124, 4)
    # armor stand
    _rect(b, 282, 70, 285, g, 14)
    _rect(b, 270, 68, 298, 70, 14)
    _rect(b, 272, 74, 296, 104, 16)
    _rect(b, 273, 75, 295, 103, 2)
    _rect(b, 276, 82, 292, 92, 3)
    _rect(b, 279, 85, 289, 89, 7)
    _ellipse(b, 284, 70, 9, 6, 3)
    _rect(b, 282, 62, 286, 68, 3)
    _px(b, 284, 60, 5)
    # sword rack and chest
    _rect(b, 240, 112, 266, 114, 16)
    _line(b, 244, 112, 260, 104, 14, 1)
    _line(b, 244, 112, 260, 120, 14, 1)
    _rect(b, 18, 120, 52, g - 8, 14)
    _rect(b, 18, 120, 52, 124, 23)
    _rect(b, 31, 120, 37, g - 8, 7)
    # candles
    for cx in (110, 220):
        _rect(b, cx - 1, 108, cx + 2, 122, 4)
        _rect(b, cx - 4, 122, cx + 5, 124, 6)
        _px(b, cx, 105, 7)
        _px(b, cx, 104, 31)
    for x in range(180, 230):
        _px(b, x, g - 2, 6)
        _px(b, x, g - 3, 7)
    return b


def _corridor(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 25)
    # ceiling
    for y in range(0, 40):
        _rect(b, 0, y, w, y + 1, 16 if y > 10 else 25)
    for x in range(0, w, 24):
        _rect(b, x, 8, x + 4, 40, 14)
    # far wall
    _rect(b, 0, 40, w, g - 8, 24)
    _rect(b, 0, 40, w, 44, 14)
    # receding pillars: near, mid, far pairs
    for cx, half, top in ((18, 8, 34), (286, 8, 34), (58, 6, 46), (246, 6, 46), (102, 4, 62), (202, 4, 62)):
        _rect(b, cx - half, top, cx + half, g, 5)
        _rect(b, cx - half, top, cx - half + 2, g, 26)
        _rect(b, cx + half - 2, top, cx + half, g, 27)
        _rect(b, cx - half - 1, top, cx + half + 1, top + 2, 7)
        _rect(b, cx - half - 3, g - 8, cx + half + 3, g, 3)
        for yy in range(top + 8, g - 10, 16):
            _px(b, cx - 2, yy, 7)
            _px(b, cx + 2, yy + 3, 7)
    # lattice doors between pillars
    for x0, x1, y0 in ((26, 50, 48), (110, 194, 62), (270, 294, 48)):
        _lattice(b, x0, y0, x1, g - 12, 14, 24, 7)
    # floor perspective
    for y in range(g - 8, h):
        for x in range(w):
            b[y][x] = 3 if (x // 8 + y) % 5 else 2
    for i in range(-6, 7):
        _line(b, 160, g - 8, 160 + i * 34, h, 16, 1)
    for y in range(g - 8, h, 5):
        _rect(b, 0, y, w, y + 1, 16)
    # lanterns
    for cx, cy in ((58, 58), (160, 52), (246, 58)):
        _rect(b, cx, 0, cx + 1, cy - 6, 16)
        _ellipse(b, cx, cy, 5, 7, 5)
        _rect(b, cx - 3, cy - 8, cx + 4, cy - 6, 7)
        _rect(b, cx - 3, cy + 6, cx + 4, cy + 8, 7)
        _px(b, cx, cy, 7)
    for x in range(w):
        b[g - 1][x] = 16
    return b


def _xuanwu_gate(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 25)
    _sky(b, g, [(0, 25), (32, 10), (62, 9), (92, 6), (150, 6)])
    _sun(b, 160, 72, 10, 7, 6)
    _hills(b, 120, 96, 2, 31, 24)
    # massive wall
    _wall(b, 0, 74, w, 136, 5, 27, 3)
    for x in range(0, w, 9):
        _rect(b, x, 70, x + 5, 74, 16)
    # gate arch
    _poly(b, [(118, 136), (118, 96), (132, 80), (188, 80), (202, 96), (202, 136)], 16)
    _poly(b, [(126, 136), (126, 100), (138, 86), (182, 86), (194, 100), (194, 136)], 0)
    for x in range(136, 184, 12):
        _rect(b, x, 86, x + 2, 136, 16)
    # tunnel torches
    for x in (132, 188):
        _rect(b, x, 104, x + 2, 120, 14)
        _px(b, x + 1, 101, 7)
        _px(b, x + 1, 100, 6)
    # towers
    for cx in (56, 264):
        _rect(b, cx - 24, 52, cx + 24, 82, 5)
        for x in range(cx - 20, cx + 20, 8):
            _rect(b, x, 56, x + 2, 80, 27)
        _lattice(b, cx - 12, 60, cx + 12, 76, 14, 24, 7)
        _roof(b, cx - 32, 42, cx + 32, 12, 24, 14, 16)
        _banner_bg(b, cx + 26, 82, 30, 5)
    # fog and road
    for x in range(w):
        _rect(b, x, 128, x + 1, 134, 3 if x % 4 else 4)
    for y in range(g, h):
        for x in range(w):
            b[y][x] = 3 if (x // 7 + y) % 4 else 2
    for x in range(w):
        b[g][x] = 16
    # pine silhouettes
    for x, hh in ((8, 24), (312, 22)):
        _pine(b, x, 130, hh, 15, 16)
    return b


def _taiji_hall(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 10)
    # coffered ceiling with gold beams
    _rect(b, 0, 0, w, 18, 16)
    for x in range(0, w, 16):
        _rect(b, x, 2, x + 3, 18, 7 if (x // 16) % 2 else 6)
    _rect(b, 0, 18, w, 24, 7)
    _rect(b, 0, 24, w, 28, 6)
    # deep red back wall with gold trim
    _rect(b, 0, 28, w, 104, 25)
    for x in range(0, w, 10):
        _rect(b, x, 28, x + 1, 104, 27)
    _rect(b, 0, 28, w, 30, 7)
    _rect(b, 0, 100, w, 104, 7)
    # central gold screen
    _rect(b, 108, 36, 212, 108, 16)
    _rect(b, 110, 38, 210, 106, 7)
    for x in range(114, 206, 8):
        _rect(b, x, 42, x + 4, 102, 6)
        _rect(b, x + 1, 44, x + 3, 100, 31)
    # columns
    for cx in (28, 88, 232, 292):
        _rect(b, cx - 7, 26, cx + 7, g, 5)
        _rect(b, cx - 7, 26, cx - 4, g, 26)
        _rect(b, cx + 4, 26, cx + 7, g, 27)
        _rect(b, cx - 8, 26, cx - 7, g, 16)
        _rect(b, cx + 7, 26, cx + 8, g, 16)
        _rect(b, cx - 9, g - 5, cx + 9, g, 3)
        _rect(b, cx - 9, g - 5, cx + 9, g - 4, 4)
        for k in range(6):
            _rect(b, cx - 8 - k * 2, 22 + k, cx - 8, 23 + k, 7)
            _rect(b, cx + 8, 22 + k, cx + 8 + k * 2, 23 + k, 7)
    # side lattice doors with warm light
    for x0, x1 in ((102, 118), (202, 218)):
        _lattice(b, x0, 44, x1, 96, 14, 7, 16)
        for yy in range(46, 94, 6):
            for xx in range(x0 + 2, x1 - 2):
                if (xx + yy) % 5 == 0:
                    _px(b, xx, yy, 31)
    # banners
    for x in (54, 266):
        _rect(b, x, 36, x + 8, 92, 16)
        _rect(b, x + 1, 37, x + 7, 91, 5)
        for k in range(6):
            _px(b, x + 4, 44 + k * 7, 7)
    # dais: three marble tiers with red carpet
    for hw, y0 in ((54, g - 4), (46, g - 8), (38, g - 12)):
        _rect(b, 160 - hw, y0, 160 + hw, y0 + 4, 4)
        _rect(b, 160 - hw, y0 + 3, 160 + hw, y0 + 4, 3)
        _rect(b, 160 - hw - 1, y0, 160 - hw, y0 + 4, 16)
        _rect(b, 160 + hw, y0, 160 + hw + 1, y0 + 4, 16)
    _rect(b, 142, 118, 178, g, 5)
    _rect(b, 144, 120, 176, g, 27)
    for yy in range(120, g, 5):
        _rect(b, 150, yy, 170, yy + 1, 7)
    # throne: screen, seat, armrests
    _rect(b, 134, 86, 186, 124, 16)
    _rect(b, 136, 88, 184, 122, 7)
    _rect(b, 144, 92, 176, 118, 6)
    _rect(b, 148, 96, 172, 114, 5)
    _rect(b, 154, 100, 166, 114, 7)
    _rect(b, 138, 118, 182, 124, 7)
    _rect(b, 138, 124, 182, 126, 5)
    for sx in (134, 180):
        _rect(b, sx, 104, sx + 6, 122, 7)
        _rect(b, sx + 1, 106, sx + 5, 120, 6)
        _px(b, sx + 3, 103, 5)
    # incense burners
    for cx in (96, 224):
        _rect(b, cx - 5, 128, cx + 6, 136, 6)
        _rect(b, cx - 7, 126, cx + 8, 128, 7)
        _px(b, cx, 121, 3)
        _px(b, cx + 1, 119, 3)
        _px(b, cx - 1, 123, 4)
    # polished floor with red carpet
    for y in range(g - 4, h):
        for x in range(w):
            b[y][x] = 3 if (x // 8 + y) % 5 else 2
    _rect(b, 136, g - 4, 184, h, 5)
    _rect(b, 140, g - 2, 180, h, 27)
    for x in range(w):
        b[g - 1][x] = 16
    return b


def _farmland(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 9)
    _sky(b, g, [(0, 9), (34, 7), (70, 31), (150, 31)])
    _sun(b, 244, 38, 10, 7, 6)
    for cx, cy, r in ((60, 28, 6), (76, 24, 4), (96, 30, 5)):
        _ellipse(b, cx, cy, r + 3, max(2, r // 2), 4)
    _hills(b, 116, 88, 8, 30, 15)
    _hills(b, 116, 98, 4, 18, 8, 2.0)
    # fields in perspective: alternating green / gold bands
    for y in range(100, g):
        t = (y - 100) / max(1, g - 100)
        for x in range(w):
            band = int((x - 160) * (0.15 + t * 0.75) / 18) % 5
            b[y][x] = (30, 23, 8, 31, 15)[band] if (x + y) % 4 else (8 if band % 2 else 30)
    for i in range(6):
        y = 104 + i * 7
        for x in range(w):
            yy = y + int(2 * math.sin(x / 24.0 + i))
            _px(b, x, yy, 15)
            if (x + i) % 7 == 0:
                _px(b, x, yy - 1, 8)
    # irrigation canal
    _line(b, 0, 136, 80, 128, 9, 5)
    _line(b, 80, 128, 132, 136, 9, 5)
    _line(b, 0, 135, 80, 127, 10, 1)
    _line(b, 80, 127, 132, 135, 10, 1)
    # village houses
    for x, y in ((238, 112), (268, 108), (294, 114)):
        _rect(b, x, y, x + 20, y + 16, 4)
        _roof(b, x - 3, y - 7, x + 23, 6, 24, 14, 16)
        _rect(b, x + 7, y + 7, x + 13, y + 16, 14)
        _lattice(b, x + 2, y + 4, x + 6, y + 10, 14, 24, 7)
    # trees
    for x, hh in ((208, 18), (312, 20), (28, 22)):
        _rect(b, x, g - hh, x + 2, g, 14)
        _ellipse(b, x + 1, g - hh - 3, 8, 7, 15)
        _ellipse(b, x - 3, g - hh - 1, 5, 4, 8)
        _ellipse(b, x + 5, g - hh - 4, 4, 4, 30)
    # foreground grass / field edge below the ground line
    for y in range(g, h):
        for x in range(w):
            b[y][x] = 8 if (x // 5 + y) % 4 else 15
            if (x * 7 + y * 3) % 71 == 0:
                b[y][x] = 30
    # small farmer + ox
    _rect(b, 108, 136, 110, 144, 16)
    _ellipse(b, 108, 132, 2, 2, 18)
    _rect(b, 106, 130, 111, 132, 7)
    _line(b, 116, 140, 126, 140, 16, 1)
    _rect(b, 124, 137, 136, 142, 16)
    _ellipse(b, 136, 136, 3, 2, 16)
    for x in (125, 131, 134):
        _rect(b, x, 142, x + 1, 147, 16)
    for x in range(w):
        b[g][x] = 16
    for x, y in ((60, 34), (70, 30), (82, 36)):
        _px(b, x, y, 16)
        _px(b, x + 1, y - 1, 16)
        _px(b, x + 2, y, 16)
    return b


def _market(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 9)
    _sky(b, g, [(0, 9), (52, 3), (92, 3), (150, 3)])
    _sun(b, 270, 30, 8, 7, 31)
    # distant city wall
    _wall(b, 0, 88, w, 110, 5, 27, 3)
    for x in range(0, w, 22):
        _rect(b, x, 82, x + 10, 90, 16)
        _roof(b, x - 3, 78, x + 13, 6, 24, 14, 16)
    # shops on both sides
    for side, x0, x1 in ((0, 0, 110), (1, 210, 320)):
        _rect(b, x0, 110, x1, g, 4)
        _roof(b, x0 - 2, 98, x1 + 2, 12, 24, 14, 16)
        for x in range(x0 + 8, x1 - 4, 26):
            _rect(b, x, 112, x + 18, g, 23)
            _rect(b, x + 2, 116, x + 16, 134, 5)
            _rect(b, x + 5, 118, x + 13, 132, 27)
            _rect(b, x + 2, 136, x + 16, 140, 7)
    # stalls and awnings
    for x, c in ((124, 5), (164, 9), (204, 5)):
        _rect(b, x, 128, x + 26, g, 14)
        _rect(b, x - 2, 124, x + 28, 128, 7)
        for k in range(0, 28, 6):
            _rect(b, x - 2 + k, 124, x + 1 + k, 128, c if (k // 6) % 2 else 4)
    # goods
    for x, c in ((130, 5), (140, 9), (170, 7), (180, 11), (210, 30)):
        _rect(b, x, 122, x + 6, 126, c)
        _rect(b, x, 126, x + 6, 128, 16)
    # road
    for y in range(g, h):
        for x in range(w):
            b[y][x] = 3 if (x // 7 + y) % 4 else 2
    # crowd and traders
    for i in range(22):
        x = 8 + i * 14
        _crowd(b, x, x + 8, g - 1, (16, 24, 27, 25)[i % 4], 2)
    _crowd(b, 120, 220, g - 1, 16, 8)
    # camel silhouette
    _ellipse(b, 270, 132, 12, 5, 14)
    _ellipse(b, 264, 128, 4, 4, 14)
    _ellipse(b, 276, 128, 4, 4, 14)
    _line(b, 282, 130, 292, 118, 14, 3)
    _ellipse(b, 294, 116, 4, 3, 14)
    _line(b, 294, 118, 299, 113, 14, 1)
    for x in (260, 266, 274, 280):
        _line(b, x, 136, x + 1, 148, 14, 2)
    # lanterns / signs
    for x in (118, 196, 300):
        _rect(b, x, 104, x + 1, 114, 16)
        _ellipse(b, x, 118, 3, 4, 5)
        _px(b, x, 118, 7)
    for x in range(w):
        b[g][x] = 16
    return b


def _steppe(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 9)
    _sky(b, g, [(0, 9), (40, 10), (78, 3), (150, 3)])
    _sun(b, 250, 34, 9, 7, 31)
    for cx, cy, r in ((50, 34, 6), (64, 30, 4), (86, 36, 5)):
        _ellipse(b, cx, cy, r + 3, max(2, r // 2), 4)
    _mountain(b, 50, 112, 70, 34, 2, 3)
    _mountain(b, 130, 114, 60, 26, 2, 3)
    _hills(b, 118, 104, 4, 32, 15)
    _hills(b, 118, 112, 3, 19, 8, 1.5)
    # yurts
    for x, ww in ((54, 26), (100, 22)):
        _rect(b, x - ww // 2, g - 18, x + ww // 2, g, 4)
        _poly(b, [(x - ww // 2 - 2, g - 18), (x, g - 30), (x + ww // 2 + 2, g - 18)], 4)
        _rect(b, x - 3, g - 10, x + 3, g, 5)
        _rect(b, x - 1, g - 30, x + 1, g - 34, 7)
    # golden tent
    _tent_bg(b, 252, g, 72, 40, 7, 6, True)
    _rect(b, 240, g - 6, 264, g, 6)
    _banner_bg(b, 292, g, 46, 5)
    # horse herd silhouettes
    for x, s in ((150, 1.0), (172, 0.8), (190, 0.9)):
        _ellipse(b, x, g - 8 * s, 8 * s, 3 * s, 14)
        _rect(b, x - 6 * s, g - 8 * s, x + 5 * s, g - 4 * s, 14)
        _line(b, x + 5 * s, g - 8 * s, x + 8 * s, g - 16 * s, 14, 2)
        _ellipse(b, x + 8 * s, g - 17 * s, 3 * s, 2 * s, 14)
        for lx in (x - 5 * s, x - 2 * s, x + 2 * s, x + 5 * s):
            _line(b, lx, g - 4 * s, lx, g, 14, 1)
    # foreground grass
    for y in range(g, h):
        for x in range(w):
            b[y][x] = 8 if (x // 4 + y) % 5 else 15
            if (x * 11 + y * 7) % 59 == 0:
                b[y][x] = 30
    for i in range(60):
        x, y = (i * 37 + 11) % w, g + 2 + (i * 23) % 22
        _px(b, x, y, 15 if i % 3 else 8)
        _px(b, x + 1, y - 1, 15)
    for x in range(w):
        b[g][x] = 16
    return b


def _silk_road(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 6)
    _sky(b, g, [(0, 6), (36, 7), (76, 31), (150, 31)])
    _sun(b, 240, 54, 12, 7, 6)
    _mountain(b, 40, 118, 60, 28, 16)
    _mountain(b, 290, 120, 50, 24, 16)
    # dunes
    _hills(b, 120, 106, 8, 30, 23)
    _hills(b, 120, 116, 5, 18, 24, 1.8)
    # road
    _poly(b, [(0, 146), (90, 132), (230, 132), (320, 146), (320, 150), (0, 150)], 3)
    for x in range(0, w, 16):
        _px(b, x, 144 - (x // 8) % 6, 24)
    # caravan camels
    for i, (x, y, s) in enumerate(((60, 136, 1.0), (96, 138, 0.9), (132, 140, 0.8), (168, 142, 0.7))):
        _ellipse(b, x, y - 8 * s, 10 * s, 4 * s, 14)
        _ellipse(b, x - 6 * s, y - 12 * s, 3 * s, 3 * s, 14)
        _ellipse(b, x + 5 * s, y - 12 * s, 3 * s, 3 * s, 14)
        _line(b, x + 9 * s, y - 9 * s, x + 15 * s, y - 22 * s, 14, 2)
        _ellipse(b, x + 16 * s, y - 23 * s, 3 * s, 2 * s, 14)
        for lx in (x - 8 * s, x - 3 * s, x + 3 * s, x + 8 * s):
            _line(b, lx, y - 4 * s, lx + 1, y, 14, max(1, int(s)))
        _rect(b, x - 4 * s, y - 10 * s, x + 4 * s, y - 7 * s, 5)
    # monk and palanquin
    _rect(b, 220, 132, 224, 148, 6)
    _ellipse(b, 222, 128, 3, 3, 6)
    _line(b, 226, 134, 234, 126, 14, 1)
    _rect(b, 250, 132, 280, 144, 5)
    _rect(b, 252, 130, 278, 133, 7)
    _line(b, 250, 144, 250, 150, 14, 2)
    _line(b, 280, 144, 280, 150, 14, 2)
    # fort / pagoda
    _rect(b, 292, 106, 316, 118, 24)
    _roof(b, 288, 100, 320, 6, 24, 14, 16)
    for x in range(w):
        b[g][x] = 16
    return b


def _zhaoling(w: int, h: int, g: int) -> list[list[int]]:
    b = _new(w, h, 6)
    _sky(b, g, [(0, 6), (36, 7), (78, 31), (150, 31)])
    _sun(b, 224, 62, 14, 7, 6)
    for cx in (40, 70, 96):
        _ellipse(b, cx, 28 + cx // 4, 10, 3, 26)
    _mountain(b, 40, 140, 80, 48, 16)
    _mountain(b, 280, 142, 80, 52, 16)
    _mountain(b, 150, 150, 90, 78, 24, 16)
    _mountain(b, 150, 150, 62, 60, 16, 24)
    # pines
    for x, hh in ((22, 26), (48, 18), (286, 24), (306, 18)):
        _pine(b, x, 146, hh, 15, 16)
    # stone stele and lion
    _rect(b, 70, 120, 86, 146, 3)
    _rect(b, 72, 122, 84, 144, 2)
    _rect(b, 68, 118, 88, 122, 4)
    _rect(b, 64, 146, 92, 150, 2)
    _rect(b, 250, 138, 270, 146, 3)
    _ellipse(b, 260, 134, 10, 7, 3)
    _rect(b, 254, 130, 266, 138, 3)
    _px(b, 256, 128, 4)
    _px(b, 264, 128, 4)
    # ground
    for y in range(g, h):
        for x in range(w):
            b[y][x] = 24 if (x // 6 + y) % 4 else 16
    for x in range(w):
        b[g][x] = 16
    return b


# --------------------------------------------------------------------------- registry

def _bg(name: str, maker: Callable[[int, int, int], list[list[int]]]):
    def fn(buf: list[list[int]], w: int, h: int, g: int) -> None:
        key = (name, w, h, g)
        if key not in _CACHE:
            _CACHE[key] = maker(w, h, g)
        src = _CACHE[key]
        for y in range(h):
            buf[y][:] = src[y]
    BG[name] = fn


_bg("tang_yard", _yard)
_bg("snow_frontier", _snow_frontier)
_bg("taiyuan_camp", _taiyuan_camp)
_bg("war_room", _war_room)
_bg("huoyi_gate", _huoyi_gate)
_bg("loess_battlefield", _loess)
_bg("snow_battlefield", _snow_battle)
_bg("hulao_pass", _hulao)
_bg("changan_gate", _changan_gate)
_bg("qinwang_study", _qinwang_study)
_bg("palace_corridor", _corridor)
_bg("xuanwu_gate", _xuanwu_gate)
_bg("taiji_hall", _taiji_hall)
_bg("farmland", _farmland)
_bg("tang_market", _market)
_bg("steppe", _steppe)
_bg("silk_road", _silk_road)
_bg("zhaoling", _zhaoling)


# --------------------------------------------------------------------------- overlays

def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _smooth(v: float) -> float:
    v = _clamp(v)
    return v * v * (3 - 2 * v)


def _horse_pos(o: Any, t: float) -> tuple[float, float]:
    p = o.p
    x, y = float(p.get("x", 160)), float(p.get("y", 150))
    if "move" in p:
        t0, t1 = (float(v) for v in p["move"])
        u = _smooth((t - t0) / max(0.001, t1 - t0))
        x += (float(p.get("x1", x)) - x) * u
        y += (float(p.get("y1", y)) - y) * u
    if "drift" in p:
        x += float(p["drift"]) * max(0.0, t - o.t)
    return x, y


def _p_line(put: Put, x0: float, y0: float, x1: float, y1: float, c: int, w: int = 1) -> None:
    n = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
    r = max(0, w // 2)
    for i in range(n + 1):
        u = i / n
        x, y = int(round(x0 + (x1 - x0) * u)), int(round(y0 + (y1 - y0) * u))
        for oy in range(-r, r + 1):
            for ox in range(-r, r + 1):
                put(x + ox, y + oy, c)


def _p_ellipse(put: Put, cx: float, cy: float, rx: float, ry: float, c: int) -> None:
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / max(rx, 0.1)) ** 2 + ((y + 0.5 - cy) / max(ry, 0.1)) ** 2 <= 1:
                put(x, y, c)


def draw_horse(put: Put, o: Any, t: float) -> None:
    """Pixel warhorse, optional armored rider, galloping.  ``facing: -1`` mirrors it."""
    p = o.p
    x, y = _horse_pos(o, t)
    s = float(p.get("scale", 1.3))
    face = -1 if int(p.get("facing", 1)) < 0 else 1
    body = int(p.get("color", 14))
    shade = int(p.get("shade", 24))
    mane = int(p.get("mane", 24))
    saddle = int(p.get("saddle", 5))
    trim = int(p.get("trim", 7))
    gallop = float(p.get("gallop", 8.0))
    ph = t * gallop + float(p.get("phase", 0))

    def R(x0: float, y0: float, x1: float, y1: float, c: int) -> None:
        sx0, sx1 = x + face * x0 * s, x + face * x1 * s
        for yy in range(int(y + y0 * s), int(y + y1 * s) + 1):
            for xx in range(int(min(sx0, sx1)), int(max(sx0, sx1)) + 1):
                put(xx, yy, c)

    def L(x0: float, y0: float, x1: float, y1: float, c: int, w: int = 1) -> None:
        _p_line(put, x + face * x0 * s, y + y0 * s, x + face * x1 * s, y + y1 * s, c, max(1, w))

    def E(cx: float, cy: float, rx: float, ry: float, c: int) -> None:
        _p_ellipse(put, x + face * cx * s, y + cy * s, rx * s, ry * s, c)

    # tail
    for k in range(3):
        L(-8, -14 + k * 0.6, -12 - k * 0.6, -9 + k * 1.6 + math.sin(ph + k) * 1.2, mane, max(1, int(s + 0.4)))
    # far legs (darker)
    sw1 = math.sin(ph + 1.6)
    L(-6, -9, -6 + sw1 * 2.2, -4, shade, max(1, int(1.6 * s)))
    L(-6 + sw1 * 2.2, -4, -6 + sw1 * 1.4, 0, shade, max(1, int(1.6 * s)))
    sw2 = math.sin(ph + 3.4)
    L(3, -9, 3 + sw2 * 2.2, -4, shade, max(1, int(1.6 * s)))
    L(3 + sw2 * 2.2, -4, 3 + sw2 * 1.4, 0, shade, max(1, int(1.6 * s)))
    # body: outline then fill
    E(0, -11, 8.4, 5.0, 16)
    E(0, -11, 7.6, 4.2, body)
    E(-4, -12, 4.6, 3.6, body)
    E(4, -12, 4.6, 3.8, body)
    E(-5, -12.5, 2.0, 1.4, 23 if body == 14 else body)
    # saddle blanket
    R(-4, -16, 4, -12, 16)
    R(-3.6, -15.6, 3.6, -12.4, saddle)
    for k in range(-3, 4, 2):
        R(k, -15.6, k + 0.8, -12.4, trim)
    # neck (solid polygon) and head
    for i in range(7):
        hw = 2.4 - i * 0.18
        R(4.5 + i * 0.6 - hw, -13 - i * 1.15, 4.5 + i * 0.6 + hw, -12 - i * 1.15, body if i % 4 else 16)
    E(11.5, -21, 3.6, 2.8, 16)
    E(11.5, -21, 2.9, 2.1, body)
    R(12.5, -21.6, 15.5, -19.6, 16)
    R(12.8, -21.3, 15.2, -19.9, body)
    # ears + eye + nostril
    L(10.2, -23, 10.0, -25.2, body, max(1, int(s)))
    L(11.4, -23, 11.4, -25.2, body, max(1, int(s)))
    put(int(x + face * 11.5 * s), int(y - 21.3 * s), 16)
    put(int(x + face * 14.4 * s), int(y - 20.2 * s), 16)
    # mane
    L(5.0, -14, 9.4, -22.5, mane, max(1, int(1.8 * s)))
    for k in range(5):
        L(5.4 + k * 0.8, -14.5 - k * 1.4, 4.2 + k * 0.8, -13.2 - k * 1.4, mane, 1)
    # near legs
    sw3 = math.sin(ph + math.pi)
    L(-4, -9, -4 + sw3 * 2.4, -4, body, max(1, int(2.0 * s)))
    L(-4 + sw3 * 2.4, -4, -4 + sw3 * 1.6, 0, body, max(1, int(2.0 * s)))
    R(-4.8 + sw3 * 1.6, -0.8, -3.0 + sw3 * 1.6, 0.2, 16)
    sw4 = math.sin(ph + 1.9 + math.pi)
    L(6, -9, 6 + sw4 * 2.6, -4, body, max(1, int(2.0 * s)))
    L(6 + sw4 * 2.6, -4, 6 + sw4 * 1.8, 0, body, max(1, int(2.0 * s)))
    R(5.2 + sw4 * 1.8, -0.8, 7.2 + sw4 * 1.8, 0.2, 16)
    # rider
    if p.get("rider"):
        cloth = int(p.get("rider_color", 25))
        cloak = int(p.get("cloak", 5))
        helm = int(p.get("helm", 3))
        # cloak flowing behind
        for k in range(8):
            L(-2 - k * 0.8, -24 + k * 1.3 + math.sin(ph * 0.6 + k * 0.5) * 0.7,
              -3 - k * 1.1, -23 + k * 1.5 + math.sin(ph * 0.6 + k * 0.5) * 0.7, cloak, max(1, int(1.6 * s)))
        # rider leg + boot
        R(-1, -18, 1.4, -12, cloth)
        R(-1, -12, 2.2, -11, 16)
        # torso (solid, outlined)
        R(-2.4, -27, 2.4, -17, 16)
        R(-1.8, -26.6, 1.8, -17.4, cloth)
        R(-1.8, -19.4, 1.8, -18.4, trim)
        # arm to reins
        L(1.8, -24, 5.6, -19.5, cloth, max(1, int(1.8 * s)))
        put(int(x + face * 5.8 * s), int(y - 19.3 * s), 18)
        # head + helmet
        E(0, -30, 2.4, 2.5, 16)
        E(0, -30, 1.8, 1.9, 18)
        E(0, -31.6, 2.9, 1.9, 16)
        E(0, -31.6, 2.3, 1.3, helm)
        R(-2.2, -31.2, 2.2, -30.8, 7)
        L(0, -33.2, 0, -35.2, 5, max(1, int(s)))
        put(int(x + face * 0.8 * s), int(y - 30.2 * s), 16)
        if p.get("lance"):
            L(-4, -27, 18, -39, 14, max(1, int(1.6 * s)))
            for k in range(5):
                R(15 - k * 0.3, -38 + k * 0.6, 17 - k * 0.3, -36.5 + k * 0.6, 5)
    # rein
    L(8.5, -19.5, 14.5, -21, 14, 1)


def draw_camel(put: Put, o: Any, t: float) -> None:
    p = o.p
    x, y = _horse_pos(o, t)
    s = float(p.get("scale", 1.1))
    face = -1 if int(p.get("facing", 1)) < 0 else 1
    body = int(p.get("color", 23))
    shade = int(p.get("shade", 14))
    cargo = int(p.get("cargo", 5))
    ph = t * float(p.get("speed", 5.0)) + float(p.get("phase", 0))

    def R(x0: float, y0: float, x1: float, y1: float, c: int) -> None:
        sx0, sx1 = x + face * x0 * s, x + face * x1 * s
        for yy in range(int(y + y0 * s), int(y + y1 * s) + 1):
            for xx in range(int(min(sx0, sx1)), int(max(sx0, sx1)) + 1):
                put(xx, yy, c)

    def L(x0: float, y0: float, x1: float, y1: float, c: int, w: int = 1) -> None:
        _p_line(put, x + face * x0 * s, y + y0 * s, x + face * x1 * s, y + y1 * s, c, max(1, w))

    def E(cx: float, cy: float, rx: float, ry: float, c: int) -> None:
        _p_ellipse(put, x + face * cx * s, y + cy * s, rx * s, ry * s, c)

    # legs
    for i, lx in enumerate((-6, -3, 3, 6)):
        sw = math.sin(ph + i * 1.7) * 1.0
        L(lx, -8, lx + sw, -4, shade, max(1, int(1.5 * s)))
        L(lx + sw, -4, lx + sw - 0.4, 0, shade, max(1, int(1.5 * s)))
    # body + humps
    E(0, -10, 9, 4.2, 16)
    E(0, -10, 8.2, 3.5, body)
    E(-4, -13, 3.2, 2.3, 16)
    E(-4, -13, 2.5, 1.7, body)
    E(4, -13, 3.2, 2.3, 16)
    E(4, -13, 2.5, 1.7, body)
    # neck + head
    L(7.5, -11, 15, -22, 16, max(2, int(3.6 * s)))
    L(8.0, -11, 15.2, -21.5, body, max(1, int(2.5 * s)))
    E(16, -22.5, 3.0, 2.0, 16)
    E(16, -22.5, 2.3, 1.4, body)
    R(17.4, -22.4, 19.4, -21.4, 16)
    L(16, -24, 16, -25.2, body, 1)
    L(17, -24, 17, -25.2, body, 1)
    put(int(x + face * 18.2 * s), int(y - 22.2 * s), 16)
    # cargo blanket
    R(-5, -14, 5, -10, 16)
    R(-4.5, -13.6, 4.5, -10.4, cargo)
    for k in range(-4, 5, 2):
        R(k, -13.6, k + 1, -10.4, 7)
    # tail
    L(-9, -10, -12, -5, shade, 1)


def draw_tent(put: Put, o: Any, t: float) -> None:
    p = o.p
    x, y = float(p.get("x", 160)), float(p.get("y", 150))
    w, h = float(p.get("w", 46)), float(p.get("h", 34))
    s = float(p.get("scale", 1.0))
    w, h = w * s, h * s
    c1 = int(p.get("color", 23))
    c2 = int(p.get("shade", 24))
    lit = bool(p.get("lit", False))
    tip = (x, y - h)
    left, right = x - w / 2, x + w / 2
    for yy in range(int(tip[1]), int(y)):
        u = (yy - tip[1]) / max(1, h)
        half = (w / 2) * u
        for xx in range(int(x - half), int(x + half) + 1):
            c = c1 if (xx + yy) % 7 else c2
            if abs(xx - x) < 1.2:
                c = 14
            put(xx, yy, c)
    # entrance
    ew = max(3, int(w * 0.18))
    for yy in range(int(y - h * 0.58), int(y)):
        for xx in range(int(x - ew), int(x + ew)):
            put(xx, yy, 7 if lit and (xx + yy) % 3 else 16)
    # ridge + ropes
    for yy in range(int(tip[1]) - 3, int(tip[1]) + 2):
        put(int(x), yy, 14)
    for side in (-1, 1):
        for k in range(4):
            put(int(x + side * (w / 2 + k * 2)), int(y - 2 - k), 24)
    # pennant
    put(int(x), int(tip[1]) - 4, 7)
    for k in range(5):
        put(int(x + 1 + k), int(tip[1]) - 4 + (k % 2), 5)


def draw_campfire(put: Put, o: Any, t: float) -> None:
    p = o.p
    x, y = float(p.get("x", 160)), float(p.get("y", 150))
    s = float(p.get("scale", 1.0))
    # logs
    for dx, dy in ((-6, -2), (-4, -1), (4, -2), (6, -1)):
        for k in range(6):
            put(int(x + (dx * (1 - k / 6)) * s), int(y - 2 + (dy * k / 6) * s), 14 if k % 2 else 24)
    for k in range(6):
        put(int(x + (-6 + k * 2.4) * s), int(y - 1), 24)
    # flames
    for i in range(5):
        hh = (7 + (i * 3 + int(t * 7)) % 6) * s
        xx = x + (i - 2) * 3 * s
        for yy in range(int(y - 2 - hh), int(y - 1)):
            u = (y - 1 - yy) / max(1, hh)
            half = (1 - u) * 3 * s
            c = 7 if u > 0.65 else (6 if u > 0.3 else 5)
            if i % 2 == 0 and u > 0.8:
                c = 31
            for dx in range(int(-half), int(half) + 1):
                put(int(xx + dx), yy, c)
    # sparks + smoke
    for k in range(5):
        yy = y - 12 - ((t * 9 + k * 7) % 24)
        put(int(x + math.sin(t * 2 + k) * 4), int(yy), 7 if k % 2 else 6)
    for k in range(4):
        yy = y - 16 - ((t * 5 + k * 6) % 30)
        put(int(x + math.sin(t + k) * 5), int(yy), 2 if k % 2 else 3)


def draw_arrow(put: Put, o: Any, t: float) -> None:
    p = o.p
    x0, y0 = float(p.get("x0", 0)), float(p.get("y0", 60))
    x1, y1 = float(p.get("x1", 320)), float(p.get("y1", 120))
    n = max(1, int(p.get("n", 6)))
    spread = float(p.get("spread", 12))
    dur = max(0.05, float(p.get("dur", 0.45)))
    for i in range(n):
        off = (i - (n - 1) / 2) / max(1, (n - 1) / 2)
        sy = y0 + off * spread
        ey = y1 + off * spread * 1.5
        st = o.t + i * 0.035
        if t > st + dur + 0.14:
            continue
        u = _clamp((t - st) / dur)
        if u <= 0:
            continue
        ex, ey2 = x0 + (x1 - x0) * u, sy + (ey - sy) * u
        # shaft
        _p_line(put, x0 + (ex - x0) * 0.82, sy + (ey2 - sy) * 0.82, ex, ey2, int(p.get("color", 31)), 1)
        # head
        put(int(ex), int(ey2), 16)
        put(int(ex) - 1, int(ey2), 4)
        # fletch at the tail of the drawn segment
        tx, ty = x0 + (ex - x0) * 0.8, sy + (ey2 - sy) * 0.8
        put(int(tx), int(ty) - 1, 5)
        put(int(tx), int(ty) + 1, 5)
        if u >= 1 and t - (st + dur) < 0.12:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx or dy:
                        put(int(ex) + dx, int(ey2) + dy, 7)


def draw_dust(put: Put, o: Any, t: float) -> None:
    p = o.p
    x, y = float(p.get("x", 160)), float(p.get("y", 145))
    w, hh = float(p.get("w", 90)), float(p.get("h", 14))
    n = int(p.get("n", 40))
    c1 = int(p.get("color", 23))
    c2 = int(p.get("shade", 24))
    for i in range(n):
        u = ((t * 18 + i * 13) % max(1, w)) / max(1, w)
        xx = x - w / 2 + u * w
        yy = y - ((i * 17) % max(1, hh)) + math.sin(t * 3 + i) * 1.5
        r = 0.8 + (i % 2) * 0.7
        _p_ellipse(put, xx, yy, r, max(0.6, r * 0.6), c1 if i % 3 else c2)
        if i % 7 == 0:
            put(int(xx), int(yy), 6)


def draw_rain(put: Put, o: Any, t: float, W: int = 320, H: int = 180) -> None:
    p = o.p
    n = int(p.get("n", 60))
    speed = float(p.get("speed", 90))
    c = int(p.get("color", 3))
    for i in range(n):
        x = (i * 71 + int(t * speed * 0.5)) % (W + 40) - 20
        y = (i * 43 + int(t * speed)) % (H + 30) - 15
        for k in range(3):
            put(int(x - k), int(y - k), c if k < 2 else 9)
    for i in range(10):
        x = (i * 47) % W
        y = 150 + (i * 7) % 20
        if int(t * 12 + i) % 3 == 0:
            put(x, y, 4)
            put(x + 1, y, 3)


def draw_army(put: Put, o: Any, t: float) -> None:
    p = o.p
    x0, y = float(p.get("x0", 40)), float(p.get("y", 150))
    n = int(p.get("n", 10))
    gap = float(p.get("gap", 14))
    s = float(p.get("scale", 1.0))
    face = -1 if int(p.get("facing", 1)) < 0 else 1
    body = int(p.get("color", 25))
    spear = int(p.get("spear", 3))
    banner = int(p.get("banner", 5))
    for i in range(n):
        x = x0 + i * gap * face
        hh = (6 + (i * 5) % 4) * s
        for yy in range(int(y - hh), int(y)):
            put(int(x), yy, body)
            put(int(x + 1), yy, body if (i + yy) % 4 else 16)
        put(int(x), int(y - hh - 1), 18)
        # spear
        for k in range(int(10 * s)):
            put(int(x - 2), int(y - hh - k), spear)
        put(int(x - 2), int(y - hh - int(10 * s)), 4)
        # shield
        for yy in range(int(y - hh + 1), int(y - 1)):
            for xx in range(int(x + 2), int(x + 5)):
                put(xx, yy, 5 if (xx + yy) % 3 else 7)
        if i % 4 == 1:
            put(int(x + 3), int(y - hh - 2), banner)
            for k in range(4):
                put(int(x + 4 + k), int(y - hh - 2 + k % 2), banner)


def _poly_front(put: Put, pts: list[tuple[float, float]], c: int) -> None:
    ys = [p[1] for p in pts]
    for yy in range(int(min(ys)), int(max(ys)) + 1):
        xs = []
        for i, (x1, y1) in enumerate(pts):
            x2, y2 = pts[(i + 1) % len(pts)]
            if (y1 <= yy < y2) or (y2 <= yy < y1):
                xs.append(x1 + (x2 - x1) * (yy - y1) / (y2 - y1))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            for xx in range(int(a), int(b) + 1):
                put(xx, yy, c)


def draw_war_table(put: Put, o: Any, t: float) -> None:
    """Front-layer council table: drawn after characters so they stand behind it."""
    p = o.p
    x, y = float(p.get("x", 160)), float(p.get("y", 150))
    w, hh = float(p.get("w", 150)), float(p.get("h", 18))
    s = float(p.get("scale", 1.0))
    w, hh = w * s, hh * s
    top = y - hh
    # tabletop (thin), leaving the space below open
    for yy in range(int(top), int(top + 9 * s)):
        for xx in range(int(x - w / 2), int(x + w / 2)):
            c = 23 if yy < top + 3 * s else 14
            if yy == int(top):
                c = 16
            put(xx, yy, c)
    # edge and legs
    for xx in range(int(x - w / 2), int(x + w / 2)):
        put(xx, int(top + 9 * s), 16)
    for lx in (x - w / 2 + 5, x + w / 2 - 5):
        for yy in range(int(top + 9 * s), int(y)):
            put(int(lx), yy, 14)
            put(int(lx) + 1, yy, 24)
    # map on the tabletop (a narrow band)
    mx0, mx1 = int(x - w / 2 + 5), int(x + w / 2 - 5)
    my0, my1 = int(top + 2 * s), int(top + 7 * s)
    for yy in range(my0, my1):
        for xx in range(mx0, mx1):
            put(xx, yy, 4 if (xx + yy) % 7 else 3)
    for k in range(3):
        _p_line(put, mx0 + 4 + k * 12, my0 + 1, mx0 + 12 + k * 14, my1 - 1, 9, 1)
    for k in range(4):
        tx = mx0 + 14 + k * 22
        _poly_front(put, [(tx, my0 + 4), (tx + 3, my0), (tx + 6, my0 + 4)], 16)
    for tx, c in ((mx0 + 20, 5), (mx0 + 52, 5), (mx0 + 80, 10), (mx0 + 108, 10)):
        for yy in range(my0 + 2, my0 + 5):
            for xx in range(tx, tx + 4):
                put(xx, yy, c)
    # scrolls / cup on the table
    for xx in range(int(x + w / 2 - 22), int(x + w / 2 - 8)):
        put(xx, int(top) - 1, 4)
        put(xx, int(top) - 2, 31 if xx % 3 else 16)
    put(int(x - w / 2 + 14), int(top) - 2, 7)
    put(int(x - w / 2 + 14), int(top) - 3, 6)


def draw_desk(put: Put, o: Any, t: float) -> None:
    p = o.p
    x, y = float(p.get("x", 160)), float(p.get("y", 150))
    w, hh = float(p.get("w", 100)) * float(p.get("scale", 1)), float(p.get("h", 16)) * float(p.get("scale", 1))
    top = y - hh
    for yy in range(int(top), int(top + 7)):
        for xx in range(int(x - w / 2), int(x + w / 2)):
            c = 23 if yy < top + 2 else 14
            if yy == int(top):
                c = 16
            put(xx, yy, c)
    for xx in range(int(x - w / 2), int(x + w / 2)):
        put(xx, int(top + 7), 16)
    for lx in (x - w / 2 + 5, x + w / 2 - 5):
        for yy in range(int(top + 7), int(y)):
            put(int(lx), yy, 14)
            put(int(lx) + 1, yy, 24)
    # open scroll + brush + inkstone
    for xx in range(int(x - w / 2 + 8), int(x + w / 2 - 10)):
        put(xx, int(top) - 1, 4)
        put(xx, int(top) - 2, 31 if xx % 4 else 3)
    _p_line(put, int(x + w / 2 - 12), int(top) - 2, int(x + w / 2 - 4), int(top) - 10, 14, 1)
    put(int(x + w / 2 - 4), int(top) - 10, 4)
    put(int(x - w / 2 + 8), int(top) - 3, 16)
    put(int(x - w / 2 + 9), int(top) - 3, 2)


def draw_tang(put: Put, o: Any, t: float, W: int = 320, H: int = 180) -> None:
    k = o.kind
    if k == "horse":
        draw_horse(put, o, t)
    elif k == "camel":
        draw_camel(put, o, t)
    elif k == "tent":
        draw_tent(put, o, t)
    elif k == "campfire":
        draw_campfire(put, o, t)
    elif k == "arrow":
        draw_arrow(put, o, t)
    elif k == "dust":
        draw_dust(put, o, t)
    elif k == "army":
        draw_army(put, o, t)


def draw_tang_front(put: Put, o: Any, t: float, W: int = 320, H: int = 180) -> None:
    if o.kind == "war_table":
        draw_war_table(put, o, t)
    elif o.kind == "desk":
        draw_desk(put, o, t)


TANG_FRONT = {"war_table", "desk", "rain"}
