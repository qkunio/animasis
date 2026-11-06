"""Timed 2D overlay layer: pixel text, captions, title cards, story props.

Overlays are drawn straight into the palette frame buffer (no alpha, no
anti-aliasing) so they stay on the fixed palette like everything else.
Each overlay is active for ``t <= time < until`` and lives on a layer:

* ``back``  – after the background, before characters (stalls, cabinets)
* ``front`` – after characters/props (captions, tags, bubbles, HUD, cards)

A ``stall`` additionally draws its counter on the front layer so a vendor
can stand *behind* it.

YAML example::

    overlays:
      - { kind: caption, t: 3.5, until: 7.5, text: "小明口袋里只有 ¥10" }
      - { kind: tag, t: 3.5, until: 30, x: 50, y: 120, text: "¥10" }
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Callable

from PIL import Image, ImageDraw, ImageFont

from .icons import ICONS, blit_icon, icon_size

Put = Callable[[int, int, int], None]

# --------------------------------------------------------------------------- text

_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-{w}.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-{w}.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "C:/Windows/Fonts/msyh.ttc",
]


@lru_cache(maxsize=32)
def _font(size: int, bold: bool) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    env = os.environ.get("ANIMASIS_FONT")
    paths = ([env] if env else []) + [p.format(w="Bold" if bold else "Regular") for p in _FONT_CANDIDATES]
    for p in paths:
        if p and os.path.exists(p):
            for idx in (2, 0):  # Noto CJK .ttc: index 2 = Simplified Chinese
                try:
                    return ImageFont.truetype(p, size, index=idx)
                except OSError:
                    continue
    try:  # Pillow >= 10.1: scalable default (Latin only)
        return ImageFont.load_default(size=size)
    except TypeError:  # pragma: no cover
        return ImageFont.load_default()


@lru_cache(maxsize=512)
def text_mask(text: str, size: int = 12, bold: bool = False) -> tuple[int, int, frozenset[tuple[int, int]]]:
    """Rasterise one line without anti-aliasing -> (width, height, pixel set)."""
    font = _font(size, bold)
    if not text:
        return 0, size, frozenset()
    im = Image.new("1", (size * (len(text) + 2) + 8, size * 2 + 8), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    d.text((4, 4), text, font=font, fill=1)
    px = im.load()
    pts = {(x, y) for y in range(im.height) for x in range(im.width) if px[x, y]}
    if not pts:
        return 0, size, frozenset()
    adv = int(math.ceil(d.textlength(text, font=font)))
    top = 4 + int(size * 0.15)  # stable baseline box regardless of glyphs
    pts2 = frozenset((x - 4, y - top) for x, y in pts)
    return adv, size, pts2


def text_width(text: str, size: int = 12, bold: bool = False) -> int:
    return text_mask(text, size, bold)[0]


def draw_text(put: Put, x: float, y: float, text: str, size: int = 12, color: int = 4,
              outline: int | None = 0, bold: bool = False, align: str = "left",
              line_gap: int = 3) -> int:
    """Draw (multi-line) text; ``y`` is the top of the first line. Returns total height."""
    lines = str(text).split("\n")
    cy = int(round(y))
    for line in lines:
        w, h, pts = text_mask(line, size, bold)
        if align == "center":
            x0 = int(round(x - w / 2))
        elif align == "right":
            x0 = int(round(x - w))
        else:
            x0 = int(round(x))
        if outline is not None:
            ring = set()
            for (px, py) in pts:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        ring.add((px + dx, py + dy))
            for (px, py) in ring - pts:
                put(x0 + px, cy + py, outline)
        for (px, py) in pts:
            put(x0 + px, cy + py, color)
        cy += h + line_gap
    return cy - int(round(y)) - line_gap


# --------------------------------------------------------------------------- primitives

def fill_rect(put: Put, x0: int, y0: int, x1: int, y1: int, c: int) -> None:
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            put(x, y, c)


def frame_rect(put: Put, x0: int, y0: int, x1: int, y1: int, fill: int, border: int = 16) -> None:
    fill_rect(put, x0, y0, x1, y1, border)
    fill_rect(put, x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)


def fill_ellipse(put: Put, cx: float, cy: float, rx: float, ry: float, c: int) -> None:
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                put(x, y, c)


def _reveal(text: str, o: "Overlay", t: float) -> str:
    cps = float(o.p.get("reveal", 0) or 0)
    if cps <= 0:
        return text
    n = int((t - o.t) * cps) + 1
    out, k = [], 0
    for ch in text:
        if ch != "\n":
            k += 1
            if k > n:
                break
        out.append(ch)
    return "".join(out)


# --------------------------------------------------------------------------- overlay kinds

@dataclass
class Overlay:
    kind: str
    t: float = 0.0
    until: float = 1e9
    layer: str = "front"
    p: dict[str, Any] = field(default_factory=dict)

    def active(self, t: float) -> bool:
        return self.t <= t + 1e-9 < self.until


BACK_KINDS = {"stall", "cabinet", "rect", "icon_back", "hut", "fence",
              "planet", "orbit", "satellite", "range", "ring", "pin", "phone", "glyph",
              "throne", "plaque", "banner", "lantern", "candle"}


def overlay_from_dict(d: dict[str, Any]) -> Overlay:
    kind = str(d["kind"])
    t = float(d.get("t", 0.0))
    until = float(d["until"]) if "until" in d else (t + float(d["dur"]) if "dur" in d else 1e9)
    layer = str(d.get("layer", "back" if kind in BACK_KINDS else "front"))
    p = {k: v for k, v in d.items() if k not in ("kind", "t", "until", "dur", "layer")}
    return Overlay(kind=kind, t=t, until=until, layer=layer, p=p)


# camera hand-off for the screen pass: world point -> screen point, and mirror flag
_XF: dict[str, Any] = {"f": None, "flip": False, "W": 320, "H": 180}


def _palace():
    from . import palace
    return palace


def _draw_palace_back(put: Put, o: "Overlay", g: int, t: float, flip: bool, chars: dict[str, Any]) -> None:
    pm = _palace()
    k = o.kind
    if k == "throne":
        pm.draw_throne(put, o.p, g, t)
    elif k == "plaque":
        pm.draw_plaque(put, o.p, t, mirror_text=flip)
    elif k == "banner":
        p = dict(o.p)
        if p.get("follow") in chars:
            ch = chars[p["follow"]]
            if not ch.visible:
                return
            p["x"] = ch.x + float(p.get("dx", 0))
        pm.draw_banner(put, p, g, t, mirror_text=flip)
    elif k == "lantern":
        pm.draw_lantern(put, o.p, t)
    elif k == "candle":
        pm.draw_candle(put, o.p, g, t)


def _draw_bars(put: Put, o: "Overlay", g: int, t: float, chars: dict[str, Any]) -> None:
    who = o.p.get("follow")
    if who in chars:
        if not chars[who].visible:
            return
        x = chars[who].x + float(o.p.get("dx", 0))
    else:
        x = float(o.p.get("x", 160))
    _palace().draw_bars(put, {**o.p, "_t0": o.t}, x, g, t)


def _space():
    from . import space
    return space


def _text_value(o: Overlay, t: float) -> str:
    """``fmt`` + ``from``/``to``/``count`` (seconds): animated number, e.g. a distance counting up."""
    fmt = str(o.p["fmt"])
    a, b = float(o.p.get("from", 0)), float(o.p.get("to", 0))
    dur = float(o.p.get("count", 1.0))
    u = 1.0 if dur <= 0 else min(1.0, max(0.0, (t - o.t - float(o.p.get("delay", 0))) / dur))
    u = 1 - (1 - u) ** 3
    return fmt.format(v=a + (b - a) * u)


def _anchor(o: Overlay, chars: dict[str, Any]) -> tuple[float, float]:
    x, y = float(o.p.get("x", 160)), float(o.p.get("y", 90))
    who = o.p.get("follow")
    world = o.p.get("space") == "world"
    if who and who in chars:
        ch = chars[who]
        x = ch.x + float(o.p.get("dx", 0)) * (ch.facing if o.p.get("mirror") else 1)
        y = ch.y + float(o.p.get("dy", -48))
        world = o.p.get("space", "world") == "world"
    if world and _XF["f"] is not None:
        x, y = _XF["f"](x, y)
    return x, y


def _offscreen(o: Overlay, chars: dict[str, Any], margin: float = 24) -> bool:
    """Under a camera: hide labels whose speaker/anchor is hidden or out of the shot."""
    if _XF["f"] is None:
        return False
    who = o.p.get("follow")
    if who and who in chars:
        ch = chars[who]
        if not getattr(ch, "visible", True):
            return True
        # Use the label's own world point (incl. dy), not just the feet — a close-up
        # can keep the body in frame while the tag above the head is gone.
        ax = ch.x + float(o.p.get("dx", 0)) * (ch.facing if o.p.get("mirror") else 1)
        ay = ch.y + float(o.p.get("dy", -48))
        sx, sy = _XF["f"](ax, ay)
        return not (-margin <= sx <= _XF["W"] + margin and -margin <= sy <= _XF["H"] + margin)
    if o.p.get("space") == "world":  # pinned to a world point that the shot does not include
        sx, sy = _XF["f"](float(o.p.get("x", 160)), float(o.p.get("y", 90)))
        m = 12
        return not (-m <= sx <= _XF["W"] + m and -m <= sy <= _XF["H"] + m)
    return False


def _draw_caption(put: Put, o: Overlay, t: float, W: int, H: int) -> None:
    text = _reveal(str(o.p.get("text", "")), o, t)
    full = str(o.p.get("text", ""))
    size = int(o.p.get("size", 12))
    n_lines = full.count("\n") + 1
    bar_h = n_lines * (size + 3) + 5
    y1 = int(o.p.get("bottom", H - 2))
    y0 = y1 - bar_h
    frame_rect(put, 4, y0, W - 4, y1, int(o.p.get("bg", 1)), int(o.p.get("border", 0)))
    # highlight keyword colour support: "accent" applies to whole caption
    draw_text(put, W / 2, y0 + 3, text, size=size, color=int(o.p.get("color", 4)),
              outline=None, bold=bool(o.p.get("bold", False)), align="center")


def _draw_tag(put: Put, o: Overlay, t: float, chars: dict[str, Any]) -> None:
    blink = float(o.p.get("blink", 0) or 0)
    if blink and int((t - o.t) * blink * 2) % 2 == 1:
        return
    if _offscreen(o, chars):
        return
    x, y = _anchor(o, chars)
    text = str(o.p.get("text", ""))
    size = int(o.p.get("size", 12))
    bold = bool(o.p.get("bold", True))
    w = text_width(text, size, bold)
    # Do NOT clamp to the frame: under a moving/flipped camera that stuck labels to the
    # edge (world tags "sliding" along the border, HUD tags like y=6 shoved to y=26).
    # Off-screen labels are hidden by _offscreen; partially-off ones clip via put().
    if o.p.get("align") == "left":
        x0 = int(round(x))
    else:
        x0 = int(round(x - w / 2)) - 3
    y0 = int(round(y))
    x1, y1 = x0 + w + 6, y0 + size + 4
    frame_rect(put, x0, y0, x1, y1, int(o.p.get("bg", 4)), int(o.p.get("border", 16)))
    draw_text(put, x0 + 3, y0 + 1, text, size=size, color=int(o.p.get("color", 16)), outline=None, bold=bold)
    if o.p.get("strike"):
        for dx in range(x0 - 1, x1 + 1):
            yy = y0 + (y1 - y0) // 2 + int((dx - x0) * -0.12) + 2
            put(dx, yy, 5)
            put(dx, yy + 1, 5)
    if o.p.get("pin"):  # little string to the thing it labels
        for yy in range(y1, y1 + int(o.p["pin"])):
            put(int(round(x)), yy, 16)


def _draw_bubble(put: Put, o: Overlay, t: float, chars: dict[str, Any]) -> None:
    if _offscreen(o, chars):
        return
    x, y = _anchor(o, chars)
    icons = list(o.p.get("icons", [o.p["icon"]] if "icon" in o.p else []))
    text = str(o.p.get("text", ""))
    gap = 4
    sizes = [icon_size(n) for n in icons if n in ICONS]
    tw = text_width(text, 12, True) if text else 0
    inner_w = sum(w for w, _ in sizes) + gap * max(0, len(sizes) - 1) + (tw + (gap if sizes else 0) if text else 0)
    inner_h = max([h for _, h in sizes] + [12 if text else 0])
    rx, ry = inner_w / 2 + 7, inner_h / 2 + 5
    # No edge-clamp under camera (same as tags) — track the anchor or clip/hide.
    # tail dots toward the head (below-behind)
    tx = -1 if o.p.get("tail", "left") == "left" else 1
    if _XF["flip"]:
        tx = -tx
    fill_ellipse(put, x + tx * 4, y + ry + 4, 2.6, 2.2, 16)
    fill_ellipse(put, x + tx * 4, y + ry + 4, 1.6, 1.3, 4)
    fill_ellipse(put, x + tx * 7, y + ry + 9, 1.8, 1.5, 16)
    fill_ellipse(put, x + tx * 7, y + ry + 9, 0.9, 0.8, 4)
    fill_ellipse(put, x, y, rx + 1, ry + 1, 16)
    fill_ellipse(put, x, y, rx, ry, 4)
    cx = x - inner_w / 2
    for n, (w, h) in zip([n for n in icons if n in ICONS], sizes):
        blit_icon(put, n, cx + w / 2, y, anchor="center")
        if o.p.get("cross") and (o.p.get("cross") is True or o.p.get("cross") == n):
            blit_icon(put, "cross", cx + w / 2, y, anchor="center")
        cx += w + gap
    if text:
        draw_text(put, cx, y - 7, text, size=12, color=int(o.p.get("color", 16)), outline=None, bold=True)


def _draw_hud(put: Put, o: Overlay, t: float) -> None:
    x, y = float(o.p.get("x", 6)), float(o.p.get("y", 6))
    text = str(o.p.get("text", ""))
    label = str(o.p.get("label", ""))
    lw = text_width(label, 12, False) + 4 if label else 0
    w = 14 + lw + text_width(text, 16, True) + 6
    frame_rect(put, int(x), int(y), int(x + w), int(y + 22), 1, 0)
    blit_icon(put, "coin", x + 8, y + 11)
    if label:
        draw_text(put, x + 15, y + 4, label, size=12, color=3, outline=None)
    draw_text(put, x + 15 + lw, y + 1, text, size=16, color=int(o.p.get("color", 7)), outline=None, bold=True)


def _draw_card(put: Put, o: Overlay, t: float, W: int, H: int) -> None:
    bg = int(o.p.get("bg", 25))
    fill_rect(put, 0, 0, W, H, bg)
    stripe = o.p.get("stripe")
    if stripe is not None:  # retro border stripes
        for x in range(W):
            for y in list(range(0, 6)) + list(range(H - 6, H)):
                if ((x + y) // 4) % 2 == 0:
                    put(x, y, int(stripe))
    items = list(o.p.get("items", []))
    heights = []
    for it in items:
        if isinstance(it, str):
            it = {"text": it}
        if "icons" in it:
            s = int(it.get("scale", 2))
            hs = [icon_size(n, s)[1] for n in it["icons"] if n in ICONS] or [12]
            heights.append(max(hs))
        else:
            size = int(it.get("size", 12))
            heights.append((str(it.get("text", "")).count("\n") + 1) * (size + 3) - 3)
    gap = int(o.p.get("gap", 6))
    total = sum(heights) + gap * max(0, len(items) - 1)
    y = (H - total) / 2 + float(o.p.get("offset", 0))
    for idx, (it, h) in enumerate(zip(items, heights)):
        if isinstance(it, str):
            it = {"text": it}
        appear = float(it.get("at", 0))
        if t - o.t >= appear:
            if "icons" in it:
                s = int(it.get("scale", 2))
                names = [n for n in it["icons"]]
                ws = [icon_size(n, s)[0] if n in ICONS else text_width(n, 16, True) for n in names]
                sp = int(it.get("spacing", 14))
                tot = sum(ws) + sp * (len(ws) - 1)
                cx = W / 2 - tot / 2
                for n, w in zip(names, ws):
                    if n in ICONS:
                        blit_icon(put, n, cx + w / 2, y + h / 2, scale=s)
                    else:  # literal word between icons, e.g. "VS"
                        draw_text(put, cx + w / 2, y + h / 2 - 9, n, size=16, color=int(it.get("color", 7)),
                                  outline=0, bold=True, align="center")
                    cx += w + sp
            else:
                size = int(it.get("size", 12))
                draw_text(put, W / 2, y, str(it.get("text", "")), size=size,
                          color=int(it.get("color", 4)), outline=it.get("outline", 0),
                          bold=bool(it.get("bold", size >= 16)), align="center")
        y += h + gap


def _draw_stall_back(put: Put, o: Overlay, ground: int, t: float) -> None:
    x = float(o.p.get("x", 60))
    w = int(o.p.get("w", 56))
    h = int(o.p.get("h", 66))
    c = int(o.p.get("color", 5))
    x0, x1 = int(x - w / 2), int(x + w / 2)
    top = ground - h
    # back panel
    fill_rect(put, x0 + 2, top + 8, x1 - 2, ground, int(o.p.get("wall", 23)))
    for yy in range(top + 8, ground, 6):
        fill_rect(put, x0 + 2, yy, x1 - 2, yy + 1, 14)
    # posts
    for px in (x0, x1 - 3):
        frame_rect(put, px, top + 4, px + 3, ground, 14, 16)
    # awning stripes with scalloped edge
    sw = 6
    for i, sx in enumerate(range(x0 - 3, x1 + 3, sw)):
        col = c if i % 2 == 0 else 4
        fill_rect(put, sx, top, min(sx + sw, x1 + 3), top + 9, col)
        for dx in range(sw):
            if sx + dx > x1 + 2:
                break
            dd = abs(dx - (sw - 1) / 2)
            if dd < 2.2:
                put(sx + dx, top + 9, col)
            if dd < 1.2:
                put(sx + dx, top + 10, col)
    fill_rect(put, x0 - 3, top - 1, x1 + 3, top, 16)
    # sign board
    sign = str(o.p.get("sign", ""))
    if sign:
        sw_ = text_width(sign, 13, True)
        sx0 = int(x - sw_ / 2) - 5
        frame_rect(put, sx0, top - 19, sx0 + sw_ + 10, top - 1, int(o.p.get("sign_bg", 4)), 16)
        draw_text(put, sx0 + 5, top - 18, sign, size=13, color=int(o.p.get("sign_color", 16)), outline=None, bold=True)
        for px in (sx0 + 3, sx0 + sw_ + 6):
            put(px, top - 1, 16)


def _draw_stall_front(put: Put, o: Overlay, ground: int, t: float) -> None:
    x = float(o.p.get("x", 60))
    w = int(o.p.get("w", 56))
    ch = int(o.p.get("counter", 22))
    x0, x1 = int(x - w / 2), int(x + w / 2)
    y0 = ground - ch
    frame_rect(put, x0 - 2, y0, x1 + 2, ground, 14, 16)
    fill_rect(put, x0 - 1, y0 + 1, x1 + 1, y0 + 3, 23)
    for xx in range(x0 + 6, x1, 9):
        fill_rect(put, xx, y0 + 4, xx + 1, ground - 1, 24)
    goods = o.p.get("goods")
    if goods and goods in ICONS:
        offs = o.p.get("goods_x")  # explicit x offsets keep the vendor's face clear
        if offs is None:
            n = int(o.p.get("goods_n", 3))
            gw = icon_size(goods)[0] + 3
            offs = [-(n * gw) / 2 + gw / 2 + i * gw for i in range(n)]
        for dx in offs:
            blit_icon(put, goods, x + float(dx), y0 + 1, anchor="bottom")


def _draw_cabinet(put: Put, o: Overlay, ground: int, t: float) -> None:
    x = float(o.p.get("x", 280))
    w, h = int(o.p.get("w", 22)), int(o.p.get("h", 44))
    body = int(o.p.get("color", 11))
    x0, x1, top = int(x - w / 2), int(x + w / 2), ground - h
    frame_rect(put, x0, top, x1, ground, body, 16)
    fill_rect(put, x0 + 1, top + 1, x0 + 3, ground - 1, 28)        # rim light
    fill_rect(put, x1 - 3, top + 1, x1 - 1, ground - 1, 29)        # shade
    frame_rect(put, x0 + 2, top + 2, x1 - 2, top + 8, 7, 16)        # marquee
    for xx in range(x0 + 4, x1 - 4, 3):
        put(xx, top + 5, 31 if (xx + int(t * 8)) % 2 else 6)
    frame_rect(put, x0 + 3, top + 10, x1 - 3, top + 24, 1, 16)      # screen
    k = int(t * 6)
    for i in range(6):                                              # little game sprites
        sx = x0 + 5 + (i * 5 + k) % max(1, (w - 10))
        sy = top + 12 + (i * 7 + k * 3) % 10
        put(sx, sy, 30 if i % 2 else 9)
    fill_rect(put, x0 + 1, top + 25, x1 - 1, top + 30, 29)          # control panel
    put(x0 + 6, top + 25, 5); put(x0 + 6, top + 24, 5); put(x0 + 6, top + 26, 16)
    put(x1 - 8, top + 27, 7); put(x1 - 5, top + 27, 9)


def _door_open(o: Overlay, t: float) -> bool:
    for span in o.p.get("open", []) or []:
        if float(span[0]) <= t < float(span[1]):
            return True
    return False


def _draw_hut(put: Put, o: Overlay, ground: int, t: float, mirror_text: bool = False) -> None:
    """草庐: thatched cottage on a stone base, lattice window, plank door (``open`` spans), plaque."""
    x = float(o.p.get("x", 240))
    w = int(o.p.get("w", 92))
    wall = int(o.p.get("wall", 40))
    roof = int(o.p.get("roof", 30))
    snow = bool(o.p.get("snow", False))
    x0, x1 = int(x - w / 2), int(x + w / 2)
    top = ground - wall
    # stone footing
    fill_rect(put, x0 - 2, ground - 4, x1 + 2, ground, 2)
    for xx in range(x0 - 2, x1 + 2, 5):
        put(xx, ground - 3, 1)
        put(xx + 2, ground - 2, 3)
    fill_rect(put, x0 - 2, ground - 5, x1 + 2, ground - 4, 16)
    # mud wall with timber frame
    fill_rect(put, x0, top, x1, ground - 5, 23)
    for yy in range(top + 2, ground - 5):
        for xx in range(x0, x1):
            if (xx * 7 + yy * 13) % 29 == 0:
                put(xx, yy, 14)
    for px in (x0, x0 + w // 2 - 1, x1 - 3):
        fill_rect(put, px, top, px + 3, ground - 5, 14)
        fill_rect(put, px, top, px + 1, ground - 5, 24)
    fill_rect(put, x0, top, x1, top + 2, 14)
    # door
    dcx = int(x + float(o.p.get("door_dx", -20)))
    dw, dh = int(o.p.get("door_w", 16)), int(o.p.get("door_h", 30))
    dx0, dx1, dy0 = dcx - dw // 2, dcx + dw // 2, ground - 5 - dh
    frame_rect(put, dx0 - 2, dy0 - 2, dx1 + 2, ground - 5, 24, 16)
    if _door_open(o, t):
        fill_rect(put, dx0, dy0, dx1, ground - 5, 16)
        fill_rect(put, dx0, dy0, dx0 + 3, ground - 5, 14)  # door leaf swung inward
    else:
        fill_rect(put, dx0, dy0, dx1, ground - 5, 14)
        for xx in range(dx0 + 3, dx1, 4):
            fill_rect(put, xx, dy0, xx + 1, ground - 5, 24)
        put(dx1 - 3, dy0 + dh // 2, 7)
        put(dx1 - 3, dy0 + dh // 2 + 1, 6)
    # lattice window
    wcx = int(x + float(o.p.get("window_dx", 22)))
    wy0 = top + 8
    frame_rect(put, wcx - 9, wy0, wcx + 9, wy0 + 15, 14, 16)
    fill_rect(put, wcx - 7, wy0 + 2, wcx + 7, wy0 + 13, 1 if not o.p.get("lamp") else 7)
    for xx in range(wcx - 7, wcx + 7, 3):
        fill_rect(put, xx, wy0 + 2, xx + 1, wy0 + 13, 23)
    for yy in (wy0 + 5, wy0 + 9):
        fill_rect(put, wcx - 7, yy, wcx + 7, yy + 1, 23)
    # thatched roof: trapezoid with an overhang and a ragged straw fringe
    ov = int(o.p.get("overhang", 10))
    rb, rt = top + 2, top + 2 - roof
    for yy in range(rt, rb + 1):
        k = (yy - rt) / max(1, roof)
        half = (w / 2 - 12) + (ov + 12) * k
        for xx in range(int(x - half), int(x + half) + 1):
            edge = yy == rt or abs(xx - x) > half - 1
            if edge:
                c = 16
            elif snow and (yy - rt) < 4 + ((xx * 3) % 3):
                c = 4 if (xx + yy) % 5 else 3
            else:
                streak = (xx * 3 + (yy // 2) * 5) % 7
                c = 31 if streak == 0 else (6 if streak in (3, 4) else 7)
                if yy - rt > roof - 4 and streak in (1, 5):
                    c = 23
            put(xx, yy, c)
    # ridge bundle + ragged fringe
    fill_rect(put, int(x - w / 2 + 10), rt - 2, int(x + w / 2 - 10), rt, 4 if snow else 23)
    fill_rect(put, int(x - w / 2 + 10), rt - 3, int(x + w / 2 - 10), rt - 2, 16)
    for xx in range(x0 - ov, x1 + ov):
        if (xx * 5) % 3 != 0:
            put(xx, rb + 1, 6 if not snow else 3)
        if (xx * 7) % 5 == 0:
            put(xx, rb + 2, 6 if not snow else 3)
    # plaque
    sign = str(o.p.get("sign", ""))
    if sign:
        sw = text_width(sign, 12, True)
        sx0 = int(x + float(o.p.get("sign_dx", 0)) - sw / 2) - 4
        sy0 = rt + int(o.p.get("sign_dy", roof - 16))
        frame_rect(put, sx0, sy0, sx0 + sw + 8, sy0 + 14, 24, 16)
        tput = put
        if mirror_text:  # pre-mirrored so a reverse-angle (flipped) shot still reads correctly
            m = 2 * sx0 + sw + 8
            tput = lambda px, py, c: put(m - px - 1, py, c)  # noqa: E731
        draw_text(tput, sx0 + 4, sy0 + 1, sign, size=12, color=7, outline=None, bold=True)


def _draw_fence(put: Put, o: Overlay, ground: int, t: float) -> None:
    """Low bamboo fence between x0..x1."""
    x0, x1 = int(o.p.get("x0", 0)), int(o.p.get("x1", 60))
    hh = int(o.p.get("h", 16))
    snow = bool(o.p.get("snow", False))
    for xx in range(x0, x1, 6):
        top = ground - hh - (1 if (xx // 6) % 2 else 0)
        fill_rect(put, xx, top, xx + 2, ground, 23)
        put(xx + 1, top, 14)
        put(xx, top - 1, 16)
        put(xx + 1, top - 1, 4 if snow else 16)
        put(xx + 2, top + 1, 16)
        for yy in range(top + 1, ground):
            put(xx + 2, yy, 14)
    for ry in (ground - hh + 4, ground - 5):
        fill_rect(put, x0 - 1, ry, x1, ry + 2, 14)
        fill_rect(put, x0 - 1, ry, x1, ry + 1, 23)
        if snow and ry == ground - hh + 4:
            fill_rect(put, x0 - 1, ry - 1, x1, ry, 4)


def _draw_weather(put: Put, o: Overlay, t: float, W: int, H: int, ground: int) -> None:
    """Falling snow (``snow``) or drifting peach petals (``petals``), deterministic per t."""
    petals = o.kind == "petals"
    n = int(o.p.get("n", 70 if not petals else 26))
    speed = float(o.p.get("speed", 22 if not petals else 14))
    for i in range(n):
        seed = (i * 7919) % 1000 / 1000.0
        x0 = (i * 37.3) % W
        y = ((seed * (H + 20)) + (t - o.t + 50) * speed * (0.7 + 0.6 * seed)) % (H + 20) - 10
        x = x0 + math.sin((t - o.t) * (1.1 + seed) + i) * (6 if petals else 3) + (t - o.t) * (8 if petals else 2)
        x %= W
        if y > ground + 26:
            continue
        xi, yi = int(x), int(y)
        if petals:
            c = 21 if i % 3 else 26
            put(xi, yi, c)
            put(xi + 1, yi, c if i % 2 else 4)
        else:
            c = 4 if i % 4 else 3
            put(xi, yi, c)
            if i % 3 == 0:
                put(xi + 1, yi, c)
                put(xi, yi + 1, c)
                put(xi + 1, yi + 1, c)


def draw_overlays(put: Put, overlays: list[Overlay], t: float, layer: str, *, width: int, height: int,
                  ground_y: float, characters: dict[str, Any],
                  to_screen: Callable[[float, float], tuple[float, float]] | None = None,
                  flip: bool = False) -> None:
    """Draw every active overlay on ``layer`` ('back', 'front', or under a camera 'world_front' / 'screen').

    Front pass order: stall counters -> labels/bubbles/HUD/captions -> full-screen cards,
    so a card always hides the scene behind it.

    With a camera the front pass is split: ``world_front`` (stall counters, drawn on the
    stage before cropping) and ``screen`` (everything else, on the output frame; anchored
    items are mapped through ``to_screen``).
    """
    g = int(ground_y)
    live = [o for o in overlays if o.active(t)]
    if layer == "world_front":
        for o in live:
            if o.kind == "stall":
                _draw_stall_front(put, o, g, t)
            elif o.kind == "bars":
                _draw_bars(put, o, g, t, characters)
        return
    if layer == "screen":
        _XF.update(f=to_screen, flip=flip, W=width, H=height)
        try:
            _draw_front(put, live, t, width, height, g, characters, stalls=False)
        finally:
            _XF.update(f=None, flip=False)
        return
    if layer == "back":
        for o in live:
            if o.layer != "back":
                continue
            k = o.kind
            if k == "stall":
                _draw_stall_back(put, o, g, t)
            elif k == "cabinet":
                _draw_cabinet(put, o, g, t)
            elif k == "hut":
                _draw_hut(put, o, g, t, mirror_text=flip)
            elif k == "fence":
                _draw_fence(put, o, g, t)
            elif k in _palace().PALACE_BACK:
                _draw_palace_back(put, o, g, t, flip, characters)
            elif k in _space().SPACE_KINDS:
                _space().draw_space(put, o, t, width, height)
            elif k == "rect":
                frame_rect(put, int(o.p["x0"]), int(o.p["y0"]), int(o.p["x1"]), int(o.p["y1"]),
                           int(o.p.get("color", 4)), int(o.p.get("border", 16)))
            elif k in ("icon", "icon_back"):
                x, y = _anchor(o, characters)
                blit_icon(put, str(o.p.get("name")), x, y, scale=int(o.p.get("scale", 1)))
        return
    _draw_front(put, live, t, width, height, g, characters, stalls=True)


def _draw_front(put: Put, live: list[Overlay], t: float, width: int, height: int, g: int,
                characters: dict[str, Any], stalls: bool) -> None:
    if stalls:
        for o in live:
            if o.kind == "stall":
                _draw_stall_front(put, o, g, t)
            elif o.kind == "bars":
                _draw_bars(put, o, g, t, characters)
    for o in live:
        if o.layer != "front" or o.kind == "card":
            continue
        k = o.kind
        if k == "caption":
            _draw_caption(put, o, t, width, height)
        elif k == "text":
            if _offscreen(o, characters):
                continue
            x, y = _anchor(o, characters)
            txt = _text_value(o, t) if "fmt" in o.p else _reveal(str(o.p.get("text", "")), o, t)
            draw_text(put, x, y, txt, size=int(o.p.get("size", 12)),
                      color=int(o.p.get("color", 4)), outline=o.p.get("outline", 0),
                      bold=bool(o.p.get("bold", False)), align=str(o.p.get("align", "center")))
        elif k == "tag":
            _draw_tag(put, o, t, characters)
        elif k == "bubble":
            _draw_bubble(put, o, t, characters)
        elif k == "hud":
            _draw_hud(put, o, t)
        elif k in ("snow", "petals"):
            _draw_weather(put, o, t, width, height, g)
        elif k == "icon":
            x, y = _anchor(o, characters)
            blit_icon(put, str(o.p.get("name")), x, y, scale=int(o.p.get("scale", 1)))
    for o in live:
        if o.kind == "card":
            _draw_card(put, o, t, width, height)
