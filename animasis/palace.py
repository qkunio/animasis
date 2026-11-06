"""Qing-court set dressing (九子夺嫡): palace backgrounds + throne / plaque / banner / lantern / bars overlays.

Backgrounds (``background:`` or the ``background`` timeline action):

* ``palace_hall``        乾清宫-style throne hall: painted beams, red pillars, lattice doors, 金砖 floor
* ``palace_hall_night``  same hall by night (darkened palette, moonlit windows)
* ``palace_court``       太和殿-style courtyard: yellow glazed double-eave roof on a marble terrace
* ``palace_court_dusk``  courtyard at dusk
* ``frontier``           西北 frontier: snowy peaks, dunes, a beacon tower

Overlays (stage/world space):

* ``throne``  (back)   dais + dragon throne + gilded screen at ``x``
* ``plaque``  (back)   匾额 with gold text at ``x, y`` (``text``), mirrored for reverse-angle shots
* ``banner``  (back)   standing war banner (``text``) that flutters
* ``lantern`` (back)   hanging palace lantern at ``x, y`` (``lit``)
* ``candle``  (back)   candle stand with a flickering flame at ``x``
* ``bars``    (front)  圈禁 cage drawn over a character (``follow``) or at ``x``
"""

from __future__ import annotations

import math
from typing import Any, Callable

Put = Callable[[int, int, int], None]

_CACHE: dict[tuple[str, int, int, int], list[list[int]]] = {}

_NIGHT = {4: 2, 3: 1, 2: 1, 1: 16, 5: 27, 26: 27, 27: 16, 7: 6, 31: 6, 6: 32, 9: 25, 10: 25,
          15: 16, 8: 1, 14: 24, 23: 14, 30: 15, 24: 16, 25: 16, 32: 27}


def _rect(b: list[list[int]], x0: int, y0: int, x1: int, y1: int, c: int) -> None:
    h, w = len(b), len(b[0])
    for y in range(max(0, y0), min(h, y1)):
        row = b[y]
        for x in range(max(0, x0), min(w, x1)):
            row[x] = c


def _px(b: list[list[int]], x: int, y: int, c: int) -> None:
    if 0 <= y < len(b) and 0 <= x < len(b[0]):
        b[y][x] = c


def draw_bg_palace(buf: list[list[int]], w: int, h: int, ground_y: int, style: str = "palace_hall") -> None:
    key = (style, w, h, ground_y)
    if key not in _CACHE:
        if style.startswith("palace_hall"):
            src = _make_hall(w, h, ground_y)
        elif style.startswith("palace_court"):
            src = _make_court(w, h, ground_y, dusk=style.endswith("_dusk"))
        else:
            src = _make_frontier(w, h, ground_y)
        remap = _NIGHT if style.endswith("_night") else None
        if remap:
            src = [[remap.get(c, c) for c in row] for row in src]
            if style == "palace_hall_night":  # moonlight through the lattice
                for x0 in (44, 252):
                    for y in range(40, 72):
                        for x in range(x0, x0 + 24):
                            if (x - x0) % 4 and (y - 40) % 4:
                                src[y][x] = 9 if (x + y) % 5 else 3
        _CACHE[key] = src
    src = _CACHE[key]
    for y in range(h):
        buf[y][:] = src[y]


# --------------------------------------------------------------------------- hall

def _make_hall(w: int, h: int, g: int) -> list[list[int]]:
    b = [[27] * w for _ in range(h)]
    # ceiling + painted beams (和玺彩画)
    _rect(b, 0, 0, w, 8, 16)
    for x in range(0, w, 6):
        _rect(b, x, 2, x + 3, 6, 25)          # coffer squares
        _px(b, x + 1, 3, 7)
    _rect(b, 0, 8, w, 20, 10)
    for x0 in range(0, w, 40):
        _rect(b, x0, 9, x0 + 20, 19, 15)
        for k in range(6):                      # gold zig-zag (bracket line)
            _px(b, x0 + 20 + k * 3, 10 + (k % 2) * 6, 7)
            _px(b, x0 + 21 + k * 3, 11 + (k % 2) * 4, 7)
        for yy in range(11, 17):                # gold 'dragon' lozenge
            dx = 3 - abs(yy - 14)
            for xx in range(x0 + 10 - dx, x0 + 10 + dx + 1):
                _px(b, xx, yy, 7 if (xx + yy) % 2 else 31)
    _rect(b, 0, 8, w, 9, 7)
    _rect(b, 0, 19, w, 20, 7)
    _rect(b, 0, 20, w, 23, 16)
    # back wall: lattice door panels (格扇) between pillars
    for x0 in range(30, w - 30, 24):
        _rect(b, x0, 30, x0 + 22, g - 4, 5)
        _rect(b, x0 + 2, 34, x0 + 20, 82, 24)
        for y in range(34, 82):
            for x in range(x0 + 2, x0 + 20):
                if (x - x0) % 4 == 2 or (y - 34) % 4 == 0 or (x - x0 + y) % 8 == 0:
                    b[y][x] = 27 if (x + y) % 2 else 5
        _rect(b, x0 + 2, 86, x0 + 20, 100, 27)       # 绦环板
        _rect(b, x0 + 4, 88, x0 + 18, 98, 5)
        _rect(b, x0 + 2, 104, x0 + 20, g - 8, 27)    # 裙板
        for xx in range(x0 + 4, x0 + 18):
            _px(b, xx, 106, 7)
            _px(b, xx, g - 10, 7)
        for yy in range(106, g - 9):
            _px(b, x0 + 4, yy, 7)
            _px(b, x0 + 17, yy, 7)
        _px(b, x0 + 11, (106 + g - 10) // 2, 31)
        _rect(b, x0, 30, x0 + 22, 31, 16)
    _rect(b, 0, 24, w, 30, 5)
    for x in range(0, w, 8):
        _px(b, x, 27, 7)
    # pillars
    for cx in (12, 108, 212, 308):
        _rect(b, cx - 6, 20, cx + 6, g, 5)
        _rect(b, cx - 6, 20, cx - 3, g, 26)
        _rect(b, cx + 3, 20, cx + 6, g, 27)
        _rect(b, cx - 7, 20, cx - 6, g, 16)
        _rect(b, cx + 6, 20, cx + 7, g, 16)
        for yy in range(40, g - 10, 18):           # coiled gold dragon hint
            for k in range(6):
                _px(b, cx - 4 + k * 2, yy + int(2 * math.sin(k)), 7)
        _rect(b, cx - 9, g - 5, cx + 9, g, 3)      # stone base
        _rect(b, cx - 9, g - 5, cx + 9, g - 4, 4)
        for k in range(6):                         # 雀替 brackets
            _rect(b, cx - 7 - (5 - k) * 2, 23 + k, cx - 7, 24 + k, 7 if k % 2 else 6)
            _rect(b, cx + 7, 23 + k, cx + 7 + (5 - k) * 2, 24 + k, 7 if k % 2 else 6)
    # 金砖 floor
    for y in range(g, h):
        dy = y - g
        row = dy // 5
        for x in range(w):
            off = 10 if row % 2 else 0
            if dy % 5 == 0 or (x + off) % 20 == 0:
                c = 1
            elif dy % 5 == 1:
                c = 3
            else:
                c = 2
            b[y][x] = c
    for x in range(w):
        b[g][x] = 16
    # red carpet down the middle
    for y in range(g + 1, h):
        k = (y - g) * 0.5
        x0, x1 = int(128 - k), int(192 + k)
        for x in range(x0, x1):
            edge = x - x0 < 2 or x1 - x <= 2
            b[y][x] = 7 if edge else (5 if (x + y) % 9 else 26)
    return b


# --------------------------------------------------------------------------- court

def _make_court(w: int, h: int, g: int, dusk: bool = False) -> list[list[int]]:
    b = [[9] * w for _ in range(h)]
    top, mid, low, cloud = (29, 11, 6, 26) if dusk else (10, 9, 4, 4)
    for y in range(g):
        for x in range(w):
            b[y][x] = top if y < 22 or (y < 25 and (x + y) % 2) else (mid if y < 70 or (y < 73 and (x + y) % 2) else low)
    for cx, cy, r in ((40, 26, 6), (52, 23, 8), (66, 27, 5), (250, 20, 6), (262, 17, 8), (276, 21, 5)):
        for yy in range(cy - r, cy + r):
            for xx in range(cx - r, cx + r):
                if 0 <= xx < w and (xx - cx) ** 2 + (yy - cy) ** 2 * 2.2 <= r * r:
                    b[yy][xx] = cloud
    cx = w // 2
    # side palace walls with yellow tile caps
    for x0, x1 in ((0, 64), (w - 64, w)):
        _rect(b, x0, g - 46, x1, g, 5)
        for y in range(g - 46, g):
            for x in range(x0, x1):
                if (x * 7 + y * 3) % 23 == 0:
                    b[y][x] = 27
        _rect(b, x0, g - 52, x1, g - 46, 7)
        _rect(b, x0, g - 53, x1, g - 52, 16)
        for x in range(x0, x1, 3):
            _px(b, x, g - 47, 6)
            _px(b, x, g - 50, 31)
        _rect(b, x0, g - 46, x1, g - 45, 16)
    # marble terrace (须弥座), three tiers with balustrades
    tiers = [(cx - 118, cx + 118, g - 8, g), (cx - 104, cx + 104, g - 16, g - 8), (cx - 90, cx + 90, g - 24, g - 16)]
    for x0, x1, y0, y1 in tiers:
        _rect(b, x0, y0, x1, y1, 4)
        _rect(b, x0, y1 - 2, x1, y1, 3)
        _rect(b, x0, y0, x1, y0 + 1, 3)
        for x in range(x0, x1, 6):              # balustrade posts
            _rect(b, x, y0 - 4, x + 2, y0, 4)
            _px(b, x + 1, y0 - 4, 3)
        _rect(b, x0, y0 - 2, x1, y0 - 1, 3)
    # central stair (御路)
    for i in range(24):
        y = g - 1 - i
        hw = 14 - i // 6
        _rect(b, cx - hw, y, cx + hw, y + 1, 4 if i % 2 else 3)
    _rect(b, cx - 5, g - 24, cx + 5, g, 3)
    for yy in range(g - 22, g, 4):
        _px(b, cx - 2, yy, 7)
        _px(b, cx + 1, yy + 2, 7)
    # hall body: red columns + lattice doors
    hb, ht = g - 28, g - 60
    _rect(b, cx - 80, ht, cx + 80, hb, 27)
    for x in range(cx - 80, cx + 80, 12):
        _rect(b, x, ht, x + 3, hb, 5)
        _rect(b, x, ht, x + 1, hb, 26)
        for y in range(ht + 4, hb - 2):
            for xx in range(x + 4, x + 11):
                if (xx + y) % 3 == 0:
                    b[y][xx] = 24 if y > hb - 9 else 6
    # bracket band (斗拱) in blue-green
    _rect(b, cx - 84, ht - 6, cx + 84, ht, 15)
    for x in range(cx - 84, cx + 84, 4):
        _rect(b, x, ht - 5, x + 2, ht - 2, 10)
        _px(b, x + 1, ht - 1, 7)
    # roofs: lower and upper eaves (yellow glazed tiles, flared ends)
    def roof(y0: int, y1: int, xl: int, xr: int, flare: int) -> None:
        for y in range(y0, y1):
            k = (y - y0) / max(1, y1 - y0 - 1)
            ext = int(flare * k * k)
            a, c = xl - ext, xr + ext
            for x in range(a, c):
                if y == y1 - 1:
                    col = 6
                elif (x - a) % 3 == 0:
                    col = 6
                else:
                    col = 7 if (y - y0) % 4 else 31
                _px(b, x, y, col)
            _px(b, a - 1, y, 16)
            _px(b, c, y, 16)
        # flared eave tips
        _px(b, xl - flare - 1, y1 - 2, 6)
        _px(b, xl - flare - 2, y1 - 3, 6)
        _px(b, xr + flare, y1 - 2, 6)
        _px(b, xr + flare + 1, y1 - 3, 6)
    roof(ht - 16, ht - 6, cx - 82, cx + 82, 10)
    _rect(b, cx - 64, ht - 26, cx + 64, ht - 16, 27)  # upper storey wall
    for x in range(cx - 64, cx + 64, 10):
        _rect(b, x, ht - 26, x + 2, ht - 16, 5)
    _rect(b, cx - 66, ht - 28, cx + 66, ht - 26, 15)
    roof(ht - 48, ht - 28, cx - 50, cx + 50, 22)
    _rect(b, cx - 52, ht - 50, cx + 52, ht - 48, 6)      # main ridge
    _rect(b, cx - 52, ht - 51, cx + 52, ht - 50, 16)
    for sx in (cx - 54, cx + 50):                         # 吻兽 ridge beasts
        _rect(b, sx, ht - 57, sx + 4, ht - 49, 6)
        _rect(b, sx + 1, ht - 58, sx + 3, ht - 57, 16)
        _px(b, sx + 1, ht - 55, 16)
    # little plaque under the upper eave
    _rect(b, cx - 9, ht - 25, cx + 9, ht - 17, 25)
    _rect(b, cx - 10, ht - 26, cx + 10, ht - 25, 7)
    _rect(b, cx - 10, ht - 17, cx + 10, ht - 16, 7)
    for k in range(3):
        _rect(b, cx - 6 + k * 5, ht - 23, cx - 4 + k * 5, ht - 19, 7)
    # stone-paved plaza
    for y in range(g, h):
        dy = y - g
        row = dy // 6
        for x in range(w):
            off = 12 if row % 2 else 0
            if dy % 6 == 0 or (x + off) % 24 == 0:
                c = 2
            else:
                c = 3 if dy % 6 > 1 else 4
            b[y][x] = c
    for y in range(g, h):                                  # 御道 lighter centre strip
        k = (y - g) * 0.4
        for x in range(int(cx - 14 - k), int(cx + 14 + k)):
            b[y][x] = 4 if (y - g) % 6 else 3
    for x in range(w):
        b[g][x] = 16
    return b


# --------------------------------------------------------------------------- frontier

def _make_frontier(w: int, h: int, g: int) -> list[list[int]]:
    b = [[9] * w for _ in range(h)]
    for y in range(g):
        for x in range(w):
            b[y][x] = 9 if y < 50 or (y < 53 and (x + y) % 2) else (4 if y < 100 or (y < 103 and (x + y) % 2) else 31)
    sx, sy = 70, 30
    for yy in range(sy - 7, sy + 8):
        for xx in range(sx - 7, sx + 8):
            d = (xx - sx) ** 2 + (yy - sy) ** 2
            if d <= 49:
                b[yy][xx] = 31 if d < 20 else 7
    for x in range(w):   # snowy far range (祁连 / 天山 feel)
        far = int(g - 58 - 22 * abs(math.sin(x / 31.0 + 0.6)) - 8 * math.sin(x / 9.0))
        for y in range(max(0, far), g):
            pk = y - far
            b[y][x] = 4 if pk < 5 + (x % 3) else (3 if pk < 9 else 2)
    for x in range(w):   # dunes
        d1 = int(g - 26 - 9 * math.sin(x / 23.0 + 1.0) - 4 * math.sin(x / 7.0))
        for y in range(max(0, d1), g):
            pk = y - d1
            b[y][x] = 31 if pk < 2 else (6 if (x + y) % 5 else 23)
    # beacon tower (烽火台) on the right
    for y in range(g - 44, g - 18):
        k = (y - (g - 44)) // 4
        _rect(b, 262 - k, y, 282 + k, y + 1, 23 if (y // 3) % 2 else 14)
    _rect(b, 260, g - 48, 284, g - 44, 14)
    for x in range(260, 284, 4):
        _rect(b, x, g - 50, x + 2, g - 48, 14)
    for k in range(5):   # smoke
        _rect(b, 270 + k * 2, g - 56 - k * 5, 274 + k * 2, g - 52 - k * 5, 3 if k % 2 else 2)
    for y in range(g, h):
        for x in range(w):
            dy = y - g
            b[y][x] = 6 if ((x // 5 + dy // 2) % 4) else 23
    for x in range(4, w, 15):
        y = g + 5 + (x * 7) % 20
        if y < h:
            _px(b, x, y, 14)
            _px(b, x + 1, y, 24)
    for x in range(w):
        b[g][x] = 23
    return b


BG = {
    "palace_hall": lambda bf, w, h, g: draw_bg_palace(bf, w, h, g, "palace_hall"),
    "palace_hall_night": lambda bf, w, h, g: draw_bg_palace(bf, w, h, g, "palace_hall_night"),
    "palace_court": lambda bf, w, h, g: draw_bg_palace(bf, w, h, g, "palace_court"),
    "palace_court_dusk": lambda bf, w, h, g: draw_bg_palace(bf, w, h, g, "palace_court_dusk"),
    "frontier": lambda bf, w, h, g: draw_bg_palace(bf, w, h, g, "frontier"),
}


# --------------------------------------------------------------------------- overlays

PALACE_BACK = {"throne", "plaque", "banner", "lantern", "candle"}
PALACE_FRONT = {"bars"}


def _fill(put: Put, x0: int, y0: int, x1: int, y1: int, c: int) -> None:
    for y in range(y0, y1):
        for x in range(x0, x1):
            put(x, y, c)


def draw_throne(put: Put, p: dict[str, Any], ground: int, t: float) -> None:
    x = int(p.get("x", 160))
    # gilded five-panel screen (屏风)
    sw, st = 33, ground - 74
    _fill(put, x - sw - 1, st - 1, x + sw + 1, ground - 9, 16)
    for i in range(5):
        px0 = x - sw + i * (2 * sw // 5)
        px1 = px0 + 2 * sw // 5 - 1
        top = st + (0 if i == 2 else (3 if i in (1, 3) else 6))
        _fill(put, px0, top, px1, ground - 9, 32)
        _fill(put, px0 + 1, top + 1, px1 - 1, ground - 10, 6)
        for k in range(top + 4, ground - 12, 5):       # cloud / dragon scrolls
            for j in range(px0 + 2, px1 - 1):
                if (j + k) % 4 == 0:
                    put(j, k + int(math.sin(j * 0.9) * 1.2), 7)
        _fill(put, px0, top, px1, top + 1, 7)
    _fill(put, x - 4, st - 5, x + 4, st - 1, 7)
    put(x, st - 6, 31)
    # dais: three marble steps
    for i, (hw, y0) in enumerate(((34, ground - 3), (28, ground - 6), (22, ground - 9))):
        _fill(put, x - hw, y0, x + hw, y0 + 3, 4)
        _fill(put, x - hw, y0 + 2, x + hw, y0 + 3, 3)
        _fill(put, x - hw - 1, y0, x - hw, y0 + 3, 16)
        _fill(put, x + hw, y0, x + hw + 1, y0 + 3, 16)
    # dragon throne (龙椅)
    by = ground - 9
    _fill(put, x - 11, by - 32, x + 11, by - 14, 16)
    _fill(put, x - 10, by - 31, x + 10, by - 14, 7)
    for k in range(-8, 9, 4):
        put(x + k, by - 29, 31)
    _fill(put, x - 3, by - 35, x + 3, by - 31, 7)        # crest
    put(x, by - 36, 31)
    _fill(put, x - 6, by - 27, x + 6, by - 18, 6)        # carved back panel
    for yy in range(by - 26, by - 19):
        put(x + int(3 * math.sin(yy * 0.8)), yy, 31)
    _fill(put, x - 19, by - 14, x + 19, by - 4, 16)       # seat + arms
    _fill(put, x - 18, by - 13, x + 18, by - 5, 7)
    _fill(put, x - 12, by - 15, x + 12, by - 12, 5)       # red cushion
    _fill(put, x - 12, by - 15, x + 12, by - 14, 26)
    for sx in (x - 19, x + 15):                           # dragon-head arm rests
        _fill(put, sx, by - 24, sx + 4, by - 13, 16)
        _fill(put, sx + 1, by - 23, sx + 3, by - 13, 7)
        put(sx + 2, by - 21, 5)
    _fill(put, x - 17, by - 4, x - 13, by, 6)
    _fill(put, x + 13, by - 4, x + 17, by, 6)


def draw_plaque(put: Put, p: dict[str, Any], t: float, mirror_text: bool = False) -> None:
    from .overlay import draw_text, text_width

    text = str(p.get("text", "正大光明"))
    size = int(p.get("size", 12))
    tw = text_width(text, size, True)
    x, y = float(p.get("x", 160)), int(p.get("y", 36))
    x0, x1 = int(x - tw / 2) - 6, int(x + tw / 2) + 6
    y0, y1 = y, y + size + 8
    _fill(put, x0 - 3, y0 - 3, x1 + 3, y1 + 3, 16)
    _fill(put, x0 - 2, y0 - 2, x1 + 2, y1 + 2, 6)
    for xx in range(x0 - 2, x1 + 2, 3):              # carved gold dragon frame
        put(xx, y0 - 2, 31)
        put(xx + 1, y1 + 1, 31)
    _fill(put, x0, y0, x1, y1, int(p.get("bg", 25)))
    _fill(put, x0, y0, x1, y0 + 1, 10)
    tput = put
    if mirror_text:
        m = x0 + x1
        tput = lambda px, py, c: put(m - px - 1, py, c)  # noqa: E731
    draw_text(tput, x0 + 6, y0 + 3, text, size=size, color=int(p.get("color", 7)), outline=None, bold=True)
    if p.get("glow") and int(t * 4) % 2 == 0:
        for xx in range(x0, x1, 2):
            put(xx, y1 + 4, 31)


def draw_banner(put: Put, p: dict[str, Any], ground: int, t: float, mirror_text: bool = False) -> None:
    from .overlay import draw_text

    x = int(p.get("x", 60))
    hgt = int(p.get("h", 70))
    top = ground - hgt
    _fill(put, x - 1, top, x + 1, ground, 14)
    put(x, top - 1, 7)
    put(x, top - 2, 7)
    fw, fh = int(p.get("w", 22)), int(p.get("fh", 26))
    color = int(p.get("color", 5))
    d = -1 if p.get("left") else 1
    for i in range(fw):
        wave = int(round(1.6 * math.sin(t * 6 + i * 0.45) * (i / fw)))
        for j in range(fh - (i * 3 // fw)):
            xx = x + d * (2 + i)
            yy = top + 2 + j + wave
            edge = j == 0 or j == fh - (i * 3 // fw) - 1 or i == fw - 1
            put(xx, yy, 16 if edge else (7 if (i < 2 or j < 2) else color))
    text = str(p.get("text", ""))
    if text:
        tput = put
        cx = x + d * (2 + fw // 2)
        if mirror_text:
            tput = lambda px, py, c: put(2 * cx - px - 1, py, c)  # noqa: E731
        draw_text(tput, cx, top + 2 + fh // 2 - 7, text, size=12, color=7, outline=None, bold=True, align="center")


def draw_lantern(put: Put, p: dict[str, Any], t: float) -> None:
    x, y = int(p.get("x", 60)), int(p.get("y", 40))
    for yy in range(0, y - 6):
        put(x, yy, 16)
    sway = int(round(math.sin(t * 1.7 + x) * 0.6))
    lit = p.get("lit", True)
    for dy in range(-6, 7):
        hw = int(5 * math.sqrt(max(0.0, 1 - (dy / 7) ** 2)))
        for dx in range(-hw, hw + 1):
            c = 16 if abs(dx) == hw else ((31 if lit else 26) if abs(dx) < 2 and abs(dy) < 3 else 5)
            put(x + dx + sway, y + dy, c)
    _fill(put, x - 3 + sway, y - 8, x + 4 + sway, y - 6, 7)
    _fill(put, x - 3 + sway, y + 6, x + 4 + sway, y + 8, 7)
    for k in range(4):
        put(x + sway - 1 + (k % 2) * 2, y + 9 + k, 5)


def draw_candle(put: Put, p: dict[str, Any], ground: int, t: float) -> None:
    x = int(p.get("x", 60))
    _fill(put, x - 4, ground - 2, x + 5, ground, 6)
    _fill(put, x - 1, ground - 22, x + 2, ground - 2, 6)
    _fill(put, x - 4, ground - 24, x + 5, ground - 22, 7)
    _fill(put, x - 1, ground - 31, x + 2, ground - 24, 4)
    fl = int(t * 9) % 3
    put(x, ground - 32, 7)
    put(x, ground - 33 - (1 if fl else 0), 31)
    put(x + (1 if fl == 2 else 0), ground - 34, 6)
    put(x - 1, ground - 32, 6)


def draw_bars(put: Put, p: dict[str, Any], x: float, ground: int, t: float) -> None:
    """圈禁: a wooden cage dropped over the anchor (slides down over ``drop`` seconds)."""
    w2 = int(p.get("w", 22)) // 2
    hgt = int(p.get("h", 46))
    drop = float(p.get("drop", 0.35))
    u = 1.0 if drop <= 0 else min(1.0, max(0.0, (t - float(p.get("_t0", 0))) / drop))
    u = 1 - (1 - u) ** 2
    off = int(round((1 - u) * -60))
    x0, x1 = int(x) - w2, int(x) + w2
    top = ground - hgt + off
    bot = ground + off
    for xx in range(x0, x1 + 1, 4):
        _fill(put, xx, top, xx + 2, bot, 14)
        _fill(put, xx, top, xx + 1, bot, 23)
    _fill(put, x0 - 2, top - 3, x1 + 3, top, 24)
    _fill(put, x0 - 2, top - 3, x1 + 3, top - 2, 14)
    _fill(put, x0 - 2, bot - 3, x1 + 3, bot, 24)
    _fill(put, int(x) - 2, top + hgt // 2, int(x) + 3, top + hgt // 2 + 4, 7)  # lock
    put(int(x), top + hgt // 2 + 2, 16)
