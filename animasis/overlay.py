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
    cy = int(y)
    for line in lines:
        w, h, pts = text_mask(line, size, bold)
        if align == "center":
            x0 = int(round(x - w / 2))
        elif align == "right":
            x0 = int(round(x - w))
        else:
            x0 = int(x)
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
    return cy - int(y) - line_gap


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


BACK_KINDS = {"stall", "cabinet", "rect", "icon_back"}


def overlay_from_dict(d: dict[str, Any]) -> Overlay:
    kind = str(d["kind"])
    t = float(d.get("t", 0.0))
    until = float(d["until"]) if "until" in d else (t + float(d["dur"]) if "dur" in d else 1e9)
    layer = str(d.get("layer", "back" if kind in BACK_KINDS else "front"))
    p = {k: v for k, v in d.items() if k not in ("kind", "t", "until", "dur", "layer")}
    return Overlay(kind=kind, t=t, until=until, layer=layer, p=p)


def _anchor(o: Overlay, chars: dict[str, Any]) -> tuple[float, float]:
    x, y = float(o.p.get("x", 160)), float(o.p.get("y", 90))
    who = o.p.get("follow")
    if who and who in chars:
        ch = chars[who]
        x = ch.x + float(o.p.get("dx", 0)) * (ch.facing if o.p.get("mirror") else 1)
        y = ch.y + float(o.p.get("dy", -48))
    return x, y


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
    x, y = _anchor(o, chars)
    text = str(o.p.get("text", ""))
    size = int(o.p.get("size", 12))
    bold = bool(o.p.get("bold", True))
    w = text_width(text, size, bold)
    x0, y0 = int(x - w / 2) - 3, int(y)
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
            put(int(x), yy, 16)


def _draw_bubble(put: Put, o: Overlay, t: float, chars: dict[str, Any]) -> None:
    x, y = _anchor(o, chars)
    icons = list(o.p.get("icons", [o.p["icon"]] if "icon" in o.p else []))
    text = str(o.p.get("text", ""))
    gap = 4
    sizes = [icon_size(n) for n in icons if n in ICONS]
    tw = text_width(text, 12, True) if text else 0
    inner_w = sum(w for w, _ in sizes) + gap * max(0, len(sizes) - 1) + (tw + (gap if sizes else 0) if text else 0)
    inner_h = max([h for _, h in sizes] + [12 if text else 0])
    rx, ry = inner_w / 2 + 7, inner_h / 2 + 5
    # tail dots toward the head (below-behind)
    tx = -1 if o.p.get("tail", "left") == "left" else 1
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


def draw_overlays(put: Put, overlays: list[Overlay], t: float, layer: str, *, width: int, height: int,
                  ground_y: float, characters: dict[str, Any]) -> None:
    """Draw every active overlay on ``layer`` ('back' or 'front').

    Front pass order: stall counters -> labels/bubbles/HUD/captions -> full-screen cards,
    so a card always hides the scene behind it.
    """
    g = int(ground_y)
    live = [o for o in overlays if o.active(t)]
    if layer == "back":
        for o in live:
            if o.layer != "back":
                continue
            k = o.kind
            if k == "stall":
                _draw_stall_back(put, o, g, t)
            elif k == "cabinet":
                _draw_cabinet(put, o, g, t)
            elif k == "rect":
                frame_rect(put, int(o.p["x0"]), int(o.p["y0"]), int(o.p["x1"]), int(o.p["y1"]),
                           int(o.p.get("color", 4)), int(o.p.get("border", 16)))
            elif k in ("icon", "icon_back"):
                x, y = _anchor(o, characters)
                blit_icon(put, str(o.p.get("name")), x, y, scale=int(o.p.get("scale", 1)))
        return
    for o in live:
        if o.kind == "stall":
            _draw_stall_front(put, o, g, t)
    for o in live:
        if o.layer != "front" or o.kind == "card":
            continue
        k = o.kind
        if k == "caption":
            _draw_caption(put, o, t, width, height)
        elif k == "text":
            x, y = _anchor(o, characters)
            draw_text(put, x, y, _reveal(str(o.p.get("text", "")), o, t), size=int(o.p.get("size", 12)),
                      color=int(o.p.get("color", 4)), outline=o.p.get("outline", 0),
                      bold=bool(o.p.get("bold", False)), align=str(o.p.get("align", "center")))
        elif k == "tag":
            _draw_tag(put, o, t, characters)
        elif k == "bubble":
            _draw_bubble(put, o, t, characters)
        elif k == "hud":
            _draw_hud(put, o, t)
        elif k == "icon":
            x, y = _anchor(o, characters)
            blit_icon(put, str(o.p.get("name")), x, y, scale=int(o.p.get("scale", 1)))
    for o in live:
        if o.kind == "card":
            _draw_card(put, o, t, width, height)
