"""Petroleum-explainer overlays: pumpjack, barrel, oil droplet, molecules, fractionating column, yield bar.

All kinds are world-space ``back`` layer props (draw before characters), so a camera can
push in and pan along them.  Geometry is authored on the 320x180 pixel stage.
"""

from __future__ import annotations

import math
from typing import Any, Callable

from .icons import blit_icon, icon_size
from .overlay import draw_text, fill_rect, frame_rect, text_width

Put = Callable[[int, int, int], None]

PETRO_KINDS = {"pumpjack", "barrel", "droplet", "molecule", "column", "cutbar", "product",
               "kinetic", "splash"}

# palette shortcuts
INK = 16
PAPER = 4
GREY = 3
STONE = 2
DARK = 1
GOLD = 7
PALE = 31
SKY = 9
BLUE = 25
RED = 5
ORANGE = 6
GREEN = 30
BROWN = 14
BROWN_D = 24


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _ellipse(put: Put, cx: float, cy: float, rx: float, ry: float, c: int) -> None:
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / max(rx, 0.1)) ** 2 + ((y + 0.5 - cy) / max(ry, 0.1)) ** 2 <= 1.0:
                put(x, y, c)


def _line(put: Put, x0: float, y0: float, x1: float, y1: float, c: int, width: int = 1) -> None:
    n = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
    r = max(1, width // 2)
    for i in range(n + 1):
        u = i / n
        x, y = int(round(x0 + (x1 - x0) * u)), int(round(y0 + (y1 - y0) * u))
        for oy in range(-r, r + 1):
            for ox in range(-r, r + 1):
                if ox * ox + oy * oy <= r * r + 0.5:
                    put(x + ox, y + oy, c)


def _dot(put: Put, x: float, y: float, r: float, c: int) -> None:
    _ellipse(put, x, y, r, r, c)


def _label(put: Put, x: float, y: float, text: str, bg: int, color: int = PAPER, size: int = 11,
           stripe: int | None = None) -> int:
    """Small framed label; x,y is the top-left.  Returns its width."""
    tw = text_width(text, size, True)
    x0, y0 = int(round(x)), int(round(y))
    x1, y1 = x0 + tw + 10, y0 + size + 4
    frame_rect(put, x0, y0, x1, y1, bg, INK)
    if stripe is not None:
        fill_rect(put, x0, y0, x0 + 3, y1, stripe)
    draw_text(put, x0 + 5, y0 + 1, text, size=size, color=color, outline=None, bold=True)
    return x1 - x0


# --------------------------------------------------------------------------- oil field props

def draw_pumpjack(put: Put, o: Any, t: float) -> None:
    p = o.p
    x, gy = float(p.get("x", 238)), float(p.get("y", 150))
    s = float(p.get("scale", 1.4))
    period = float(p.get("period", 3.6))
    ph = 2 * math.pi * (t - o.t) / max(0.1, period)
    ang = math.sin(ph) * float(p.get("swing", 0.22))

    px, py = x, gy - 34 * s
    hx, hy = px - 30 * s * math.cos(ang), py + 30 * s * math.sin(ang)
    rx, ry = px + 30 * s * math.cos(ang), py - 30 * s * math.sin(ang)
    well_x = x - 40 * s

    # ground pad and oil puddle
    _ellipse(put, x, gy, 30 * s, 2.6 * s, 0)
    fill_rect(put, x - 25 * s, gy - 3 * s, x + 25 * s, gy, STONE)
    fill_rect(put, x - 25 * s, gy - 4 * s, x + 25 * s, gy - 3 * s, GREY)
    _ellipse(put, well_x, gy - 1, 9 * s, 2.2 * s, DARK)
    _ellipse(put, well_x + 2 * s, gy - 2, 4 * s, 1.2 * s, 2)

    # A-frame
    _line(put, x - 14 * s, gy - 3 * s, px, py, INK, max(2, int(3 * s)))
    _line(put, x + 14 * s, gy - 3 * s, px, py, INK, max(2, int(3 * s)))
    _line(put, x - 14 * s, gy - 4 * s, px, py, GREY, max(1, int(1.4 * s)))
    _line(put, x + 14 * s, gy - 4 * s, px, py, STONE, max(1, int(1.4 * s)))
    _line(put, x - 13 * s, gy - 12 * s, x + 13 * s, gy - 12 * s, STONE, max(1, int(s)))
    _line(put, x - 8 * s, gy - 3 * s, x + 8 * s, gy - 3 * s, STONE, max(1, int(s)))

    # walking beam + horse head
    _line(put, hx, hy, rx, ry, INK, max(3, int(4 * s)))
    _line(put, hx, hy, rx, ry, GREY, max(2, int(2 * s)))
    _dot(put, px, py, 2.4 * s, INK)
    _dot(put, px, py, 1.3 * s, GOLD)
    fill_rect(put, hx - 3 * s, hy - 5 * s, hx + 4 * s, hy + 4 * s, INK)
    fill_rect(put, hx - 2 * s, hy - 4 * s, hx + 3 * s, hy + 3 * s, GREY)
    _ellipse(put, hx, hy + 1 * s, 3.2 * s, 1.6 * s, STONE)

    # counterweight on the rear end
    fill_rect(put, rx - 4 * s, ry - 4 * s, rx + 4 * s, ry + 3 * s, INK)
    fill_rect(put, rx - 3 * s, ry - 3 * s, rx + 3 * s, ry + 2 * s, STONE)
    fill_rect(put, rx - 2 * s, ry - 2 * s, rx + 2 * s, ry,
              GOLD if int(t * 2) % 2 else ORANGE)

    # crank, pitman arm, motor
    crank_x, crank_y = x + 16 * s, gy - 13 * s
    pin_x = crank_x + 6 * s * math.cos(ph)
    pin_y = crank_y + 6 * s * math.sin(ph)
    _line(put, rx, ry, pin_x, pin_y, STONE, max(1, int(2 * s)))
    _dot(put, crank_x, crank_y, 6 * s, INK)
    _dot(put, crank_x, crank_y, 4.6 * s, STONE)
    _dot(put, pin_x, pin_y, 1.4 * s, GOLD)
    fill_rect(put, x + 8 * s, gy - 8 * s, x + 21 * s, gy - 3 * s, INK)
    fill_rect(put, x + 9 * s, gy - 7 * s, x + 20 * s, gy - 4 * s, STONE)
    fill_rect(put, x + 10 * s, gy - 6 * s, x + 19 * s, gy - 5 * s, GOLD)
    _line(put, x + 12 * s, gy - 3 * s, crank_x - 4 * s, crank_y + 3 * s, DARK, max(1, int(s)))

    # horse-head cable to the wellhead
    _line(put, hx, hy + 4 * s, well_x, gy - 9 * s, INK, max(1, int(s)))
    fill_rect(put, well_x - 3 * s, gy - 9 * s, well_x + 3 * s, gy - 2 * s, STONE)
    fill_rect(put, well_x - 2 * s, gy - 8 * s, well_x + 2 * s, gy - 3 * s, GREY)
    fill_rect(put, well_x - 5 * s, gy - 6 * s, well_x + 5 * s, gy - 5 * s, INK)
    put(int(well_x), int(gy - 11 * s), RED)


def draw_barrel(put: Put, o: Any, t: float) -> None:
    p = o.p
    x, gy = float(p.get("x", 80)), float(p.get("y", 150))
    s = float(p.get("scale", 1.6))
    w, h = float(p.get("w", 22)) * s, float(p.get("h", 32)) * s
    rx, ry = w / 2, max(2.0, 3.0 * s)
    body = int(p.get("color", BROWN))
    body_d = int(p.get("shade", BROWN_D))
    top = gy - h
    _ellipse(put, x, gy - ry, rx, ry, INK)
    _ellipse(put, x, gy - ry, rx - 1, ry - 1, body_d)
    fill_rect(put, x - rx, top + ry, x + rx, gy - ry, INK)
    fill_rect(put, x - rx + 1, top + ry, x + rx - 1, gy - ry, body)
    fill_rect(put, x - rx + 2, top + ry, x - rx + 4, gy - ry, 23)
    fill_rect(put, x + rx - 4, top + ry, x + rx - 2, gy - ry, body_d)
    _ellipse(put, x, top + ry, rx, ry, INK)
    _ellipse(put, x, top + ry, rx - 1, ry - 1, GREY)
    _ellipse(put, x, top + ry, rx - 3, ry - 2, STONE)
    for k in (0.32, 0.68):
        yy = top + ry + (gy - ry - top - ry) * k
        fill_rect(put, x - rx + 1, yy, x + rx - 1, yy + 2, INK)
        fill_rect(put, x - rx + 2, yy, x + rx - 2, yy + 1, STONE)
    # label plate with a drop mark
    lw, lh = w * 0.58, h * 0.30
    lx0, ly0 = x - lw / 2, top + h * 0.42
    frame_rect(put, lx0, ly0, lx0 + lw, ly0 + lh, PAPER, INK)
    _dot(put, x, ly0 + lh * 0.55, lh * 0.22, INK)
    for i in range(int(lh * 0.22)):
        yy = ly0 + lh * 0.55 - lh * 0.22 - i
        half = (lh * 0.22 - i) * 0.7
        fill_rect(put, x - half, yy, x + half, yy + 1, INK)
    put(int(x), int(ly0 + lh * 0.35), PAPER)
    if int(t * 3) % 2 == 0:
        put(int(lx0 + lw * 0.72), int(ly0 + 3), PALE)


def draw_droplet(put: Put, o: Any, t: float) -> None:
    p = o.p
    x, y = float(p.get("x", 80)), float(p.get("y", 90))
    fall = float(p.get("fall", 0))
    if fall > 0:
        u = _clamp((t - o.t) / fall)
        y0 = float(p.get("y0", y - 80))
        y = y0 + (y - y0) * u * u
    r = float(p.get("r", 24))
    body = int(p.get("color", DARK))
    edge = int(p.get("edge", GREY))
    wob = 1 + 0.02 * math.sin(t * 2.2)
    r *= wob
    tip = y - r * 1.7
    _dot(put, x, y, r + 1.5, INK)
    _dot(put, x, y, r, edge)
    _dot(put, x, y, r - 1, body)
    # teardrop tip
    for i in range(int(r * 1.3)):
        yy = tip + i
        half = max(0.6, (i / (r * 1.3)) ** 0.8 * r * 0.48)
        fill_rect(put, x - half, yy, x + half, yy + 1, body)
        if i == 0:
            put(int(x), int(yy), INK)
    # rim highlight
    _ellipse(put, x - r * 0.35, y - r * 0.35, r * 0.18, r * 0.26, SKY)
    _ellipse(put, x - r * 0.25, y - r * 0.55, r * 0.07, r * 0.12, PAPER)
    _ellipse(put, x + r * 0.45, y + r * 0.35, r * 0.10, r * 0.16, 10)


# --------------------------------------------------------------------------- molecules

def draw_molecule(put: Put, o: Any, t: float) -> None:
    p = o.p
    style = str(p.get("style", "chain"))
    s = float(p.get("scale", 1))
    x, y = float(p.get("x", 160)), float(p.get("y", 90))
    color = int(p.get("color", GREY))
    atom = int(p.get("atom", PAPER))
    grow = float(p.get("grow", 0))
    if style == "ring":
        r = 7.5 * s
        pts = [(x + r * math.cos(math.radians(60 * i - 90)),
                y + r * math.sin(math.radians(60 * i - 90))) for i in range(6)]
        for i in range(3):
            _line(put, *pts[i * 2], pts[i * 2][0] * 0.35 + pts[i * 2 + 1][0] * 0.65,
                  pts[i * 2][1] * 0.35 + pts[i * 2 + 1][1] * 0.65, color, max(1, int(2 * s)))
        for i in range(6):
            _line(put, *pts[i], *pts[(i + 1) % 6], color, max(1, int(2 * s)))
        for pt in pts:
            _dot(put, pt[0], pt[1], 1.8 * s, atom)
        _dot(put, x, y, r * 0.46, PALE if int(t * 3) % 2 else GOLD)
        return
    n = max(2, int(p.get("n", 6)))
    step = 8.5 * s
    amp = 3.2 * s
    pts = []
    for i in range(n):
        wig = math.sin(t * 2.2 + i * 0.8) * 0.6 * s
        pts.append((x - (n - 1) * step / 2 + i * step, y + (amp if i % 2 else -amp) + wig))
    k = n
    if grow > 0:
        k = max(1, int((t - o.t) / grow * n) + 1)
    for i in range(min(k, n) - 1):
        _line(put, *pts[i], *pts[i + 1], color, max(1, int(2.3 * s)))
        if p.get("double") and abs(i - (n - 2) / 2) < 0.6:
            _line(put, pts[i][0], pts[i][1] + 2 * s, pts[i + 1][0], pts[i + 1][1] + 2 * s, color,
                  max(1, int(1.4 * s)))
    for i in range(min(k, n)):
        px, py = pts[i]
        _dot(put, px, py, 2.0 * s, atom)
        # hydrogens: one above and one below each carbon, sparser for long chains
        if n <= 9 or i % 2 == 0:
            _dot(put, px - 0.6 * s, py - 3.4 * s, 1.0 * s, PALE)
            _dot(put, px + 0.6 * s, py + 3.4 * s, 1.0 * s, PALE)
        if p.get("poly") and i in (0, n - 1):
            bx = px - 2.5 * s if i == 0 else px + 2.5 * s
            _line(put, bx, py - 4 * s, bx, py + 4 * s, color, max(1, int(1.3 * s)))
            tick = -1 if i == 0 else 1
            _line(put, bx, py - 4 * s, bx + tick * 2 * s, py - 4 * s, color, 1)
            _line(put, bx, py + 4 * s, bx + tick * 2 * s, py + 4 * s, color, 1)


# --------------------------------------------------------------------------- fractionating column

def _flow_dots(put: Put, x0: float, y0: float, x1: float, y1: float, t: float, t0: float,
               c: int, n: int = 4) -> None:
    if t < t0:
        return
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 4:
        return
    for k in range(n):
        u = ((t - t0) * 0.55 + k / n) % 1.0
        px, py = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
        _dot(put, px, py, 1.4, c)


def draw_column(put: Put, o: Any, t: float) -> None:
    p = o.p
    x, gy = float(p.get("x", 100)), float(p.get("y", 150))
    w, h = float(p.get("w", 42)), float(p.get("h", 112))
    top = gy - h
    bottom = gy - 6
    left, right = x - w / 2, x + w / 2
    label_x = float(p.get("label_x", 156))

    # ---- furnace + crude feed
    fx0, fx1 = left - 26, left + 8
    fill_rect(put, fx0, gy - 18, fx1, gy - 2, INK)
    fill_rect(put, fx0 + 1, gy - 17, fx1 - 1, gy - 3, 24)
    fill_rect(put, fx0 + 3, gy - 15, fx1 - 3, gy - 5, DARK)
    for i in range(5):
        fy = gy - 14 + i * 2
        fw = 4 + (i * 2) % 5
        fill_rect(put, fx0 + 8 - fw / 2, fy, fx0 + 8 + fw / 2, fy + 1, ORANGE if i % 2 else GOLD)
        fill_rect(put, fx1 - 8 - fw / 3, fy, fx1 - 8 + fw / 3, fy + 1, RED if i % 2 else ORANGE)
    _line(put, 18, gy - 9, fx0, gy - 9, 24, 3)
    _line(put, 18, gy - 9, fx0, gy - 9, STONE, 1)
    _flow_dots(put, 20, gy - 9, fx0 - 2, gy - 9, t, o.t, GOLD, 3)
    draw_text(put, 20, gy - 24, "原油", size=10, color=PAPER, outline=INK, bold=True)

    # ---- shell body
    _ellipse(put, x, top + 5, w / 2 + 1, 5.5, INK)
    _ellipse(put, x, top + 5, w / 2 - 1, 4.5, BLUE)
    for yy in range(int(top + 5), int(bottom)):
        u = (yy - (top + 5)) / max(1.0, bottom - top - 5)
        c = BLUE if u < 0.22 else 10 if u < 0.42 else 29 if u < 0.58 else 27 if u < 0.75 else RED if u < 0.9 else ORANGE
        if (yy * 7) % 11 == 0:
            c = BLUE if u < 0.3 else 29 if u < 0.62 else RED
        fill_rect(put, left + 2, yy, right - 2, yy + 1, c)
    # shell flanges
    fill_rect(put, left, top + 5, left + 2, bottom, INK)
    fill_rect(put, right - 2, top + 5, right, bottom, INK)
    fill_rect(put, left + 2, top + 5, left + 4, bottom, GREY)
    fill_rect(put, left + 4, top + 5, left + 5, bottom, STONE)
    fill_rect(put, right - 5, top + 5, right - 2, bottom, STONE)
    for yy in (top + 5, bottom - 2):
        fill_rect(put, left - 2, yy, right + 2, yy + 2, INK)
        fill_rect(put, left - 1, yy, right + 1, yy + 1, STONE)
    fill_rect(put, left - 3, bottom, right + 3, bottom + 4, INK)
    fill_rect(put, left - 2, bottom + 1, right + 2, bottom + 3, STONE)

    # ---- trays, vapor, reflux
    ntray = 7
    for i in range(1, ntray + 1):
        ty = top + 6 + (bottom - top - 8) * i / (ntray + 1)
        fill_rect(put, left + 4, ty, right - 4, ty + 1, STONE)
        for bx in range(int(left + 7), int(right - 6), 7):
            fill_rect(put, bx, ty - 1, bx + 3, ty, GREY)
            put(bx + 1, int(ty - 2), STONE)
        for k in range(2):
            dy = (t * 9 + i * 3 + k * 5) % 7
            yy = ty + dy
            if yy < bottom - 2:
                put(int(left + 8 + (i * 13 + k * 9) % max(1, int(w - 16))), int(yy),
                    PAPER if k % 2 else PALE)
    for i in range(16):
        u = (t * 0.085 + i * 0.0617) % 1.0
        yy = bottom - 4 - u * (bottom - top - 10)
        xx = left + 6 + ((i * 37) % max(1, int(w - 12))) + math.sin(t * 2.4 + i) * 1.2
        c = ORANGE if u < 0.3 else GOLD if u < 0.62 else SKY if u < 0.85 else PAPER
        if int(t * 12 + i) % 3:
            put(int(xx), int(yy), c)

    # ---- cuts / draw pipes
    cuts = list(p.get("cuts", []))
    for cut in cuts:
        ct = float(cut.get("t", o.t))
        if t < ct:
            continue
        c = int(cut.get("color", GOLD))
        txt = str(cut.get("text", ""))
        top_cut = bool(cut.get("top"))
        bottom_cut = bool(cut.get("bottom"))
        if top_cut:
            py = top - 12
            _line(put, x, top - 2, x, py, STONE, 3)
            _line(put, x, top - 2, x, py, INK, 1)
            _line(put, x, py, label_x - 4, py, STONE, 3)
            _line(put, x, py, label_x - 4, py, INK, 1)
            _flow_dots(put, x, py - 1, label_x - 6, py - 1, t, ct, c, 3)
            sx, sy, ex, ey = x, top, label_x - 4, py
            ly = py - 8
        elif bottom_cut:
            py = gy - 12
            _line(put, x, bottom + 2, x, py, STONE, 3)
            _line(put, right, py, label_x - 4, py, STONE, 3)
            _line(put, right, py, label_x - 4, py, INK, 1)
            _flow_dots(put, right + 2, py - 1, label_x - 6, py - 1, t, ct, c, 3)
            sx, sy, ex, ey = right, py, label_x - 4, py
            ly = py - 8
        else:
            py = bottom - float(cut.get("at", 0.5)) * (bottom - top)
            _line(put, right, py, label_x - 4, py, STONE, 3)
            _line(put, right, py, label_x - 4, py, INK, 1)
            _flow_dots(put, right + 2, py - 1, label_x - 6, py - 1, t, ct, c, 3)
            sx, sy, ex, ey = right, py, label_x - 4, py
            ly = py - 8
        # valve
        vx = (sx + ex) / 2
        _dot(put, vx, py, 3.4, INK)
        _dot(put, vx, py, 2.2, c)
        _dot(put, vx, py, 0.8, INK)
        # label
        size = 11
        tw = text_width(txt, size, True)
        frame_rect(put, label_x, ly, label_x + tw + 10, ly + size + 4, DARK, INK)
        fill_rect(put, label_x, ly, label_x + 3, ly + size + 4, c)
        draw_text(put, label_x + 5, ly + 1, txt, size=size, color=PAPER, outline=None, bold=True)

    # ---- temperature scale
    gx, gy0, gy1 = float(p.get("gauge_x", 44)), top + 8, bottom - 6
    fill_rect(put, gx - 4, gy0 - 4, gx + 5, gy1 + 4, INK)
    fill_rect(put, gx - 3, gy0 - 3, gx + 4, gy1 + 3, DARK)
    for yy in range(int(gy0), int(gy1)):
        u = (yy - gy0) / max(1.0, gy1 - gy0)
        c = SKY if u < 0.25 else 10 if u < 0.5 else GOLD if u < 0.72 else ORANGE
        fill_rect(put, gx - 1, yy, gx + 2, yy + 1, c)
    for k in range(5):
        yy = gy0 + (gy1 - gy0) * k / 4
        fill_rect(put, gx + 3, int(yy), gx + 7, int(yy) + 1, GREY)
    draw_text(put, gx - 1, gy0 - 15, "20°C", size=9, color=SKY, outline=INK, bold=True, align="center")
    draw_text(put, gx - 1, gy1 + 5, "400°C", size=9, color=ORANGE, outline=INK, bold=True, align="center")
    _dot(put, gx, gy1 + 1, 3.2, INK)
    _dot(put, gx, gy1 + 1, 2.2, RED)


# --------------------------------------------------------------------------- yield bar

def draw_cutbar(put: Put, o: Any, t: float) -> None:
    p = o.p
    x, y = float(p.get("x", 88)), float(p.get("y", 102))
    w, h = float(p.get("w", 212)), float(p.get("h", 20))
    segs = list(p.get("segments", []))
    if not segs:
        return
    total = sum(float(s.get("pct", 0)) for s in segs) or 1.0
    frame_rect(put, x - 2, y - 2, x + w + 2, y + h + 2, DARK, INK)
    fill_rect(put, x, y, x + w, y + h, 1)
    cx = x
    for i, seg in enumerate(segs):
        sw = w * float(seg.get("pct", 0)) / total
        t0 = o.t + 0.2 + i * float(p.get("stagger", 0.55))
        u = _clamp((t - t0) / max(0.01, float(p.get("grow", 0.7))))
        u = 1 - (1 - u) ** 2
        c = int(seg.get("color", GOLD))
        if u > 0:
            fill_rect(put, cx, y, cx + sw * u, y + h, c)
            if u < 1 and sw > 2:
                fill_rect(put, cx + sw * u - 1, y, cx + sw * u, y + h, PAPER)
        cx += sw
    # separators
    cx = x
    for seg in segs:
        sw = w * float(seg.get("pct", 0)) / total
        cx += sw
        if cx < x + w - 1:
            fill_rect(put, cx, y, cx + 1, y + h, INK)

    if not p.get("show_labels", True):
        draw_text(put, x + w, y + h + 2, "100%", size=9, color=GREY, outline=INK, align="right")
        return

    # labels: wide segments inside, narrow ones above with leaders
    cx = x
    for i, seg in enumerate(segs):
        sw = w * float(seg.get("pct", 0)) / total
        label = str(seg.get("label", ""))
        pct = float(seg.get("pct", 0))
        t0 = o.t + 0.2 + i * float(p.get("stagger", 0.55))
        if t < t0 + 0.25:
            cx += sw
            continue
        c = int(seg.get("color", GOLD))
        dark = c in (1, 2, 5, 10, 14, 16, 24, 25, 27, 29)
        txt = f"{label} {pct:g}%"
        size = 10
        tw = text_width(txt, size, True)
        if sw >= tw + 8:
            draw_text(put, cx + sw / 2, y + h / 2 - size / 2, txt, size=size,
                      color=PAPER if dark else INK, outline=None, bold=True, align="center")
        else:
            up = -18 if i % 2 == 0 else -31
            draw_text(put, cx + sw / 2, y + up, txt, size=size, color=PAPER, outline=INK,
                      bold=True, align="center")
            _line(put, cx + sw / 2, y + up + size + 2, cx + sw / 2, y - 2, GREY, 1)
        cx += sw
    # 100% cap
    draw_text(put, x + w, y + h + 2, "100%", size=9, color=GREY, outline=INK, align="right")


def draw_product(put: Put, o: Any, t: float) -> None:
    """A shelf product: pixel pictogram plus a caption, both in world space (scales with the camera)."""
    p = o.p
    name = str(p.get("name", "bottle"))
    x, y = float(p.get("x", 160)), float(p.get("y", 80))
    s = max(1, int(p.get("scale", 2)))
    w, h = icon_size(name, s)
    _ellipse(put, x, y + h / 2 + 1, w * 0.52, 1.8, 16)
    _ellipse(put, x, y + h / 2, w * 0.46, 1.2, 1)
    blit_icon(put, name, x, y, scale=s)
    label = str(p.get("label", ""))
    if label:
        draw_text(put, x, y + h / 2 + 10, label, size=int(p.get("label_size", 10)),
                  color=int(p.get("color", PAPER)), outline=INK, bold=True, align="center")


def draw_kinetic(put: Put, o: Any, t: float) -> None:
    """Short, punchy title text with a scale-pop and a tiny shake."""
    p = o.p
    u = _clamp((t - o.t) / max(0.06, float(p.get("pop", 0.18))))
    scale = 0.62 + 0.38 * u + 0.08 * math.sin(u * math.pi)
    size = max(1, int(round(float(p.get("size", 24)) * scale)))
    shake = math.sin((t - o.t) * 70) * 1.5 * (1 - u) if p.get("shake", True) else 0
    draw_text(put, float(p.get("x", 160)) + shake, float(p.get("y", 80)), str(p.get("text", "")),
              size=size, color=int(p.get("color", 7)), outline=p.get("outline", 16),
              bold=bool(p.get("bold", True)), align=str(p.get("align", "center")))


def draw_splash(put: Put, o: Any, t: float) -> None:
    """Oil splash: droplets fly out, fall under gravity, plus an expanding ring."""
    p = o.p
    x, y = float(p.get("x", 160)), float(p.get("y", 105))
    n = max(4, int(p.get("n", 18)))
    power = float(p.get("power", 60))
    dur = max(0.1, float(p.get("dur", 0.6)))
    u = _clamp((t - o.t) / dur)
    for i in range(n):
        ang = -math.pi + 2 * math.pi * i / n + 0.4 * math.sin(i * 2.3)
        sp = power * (0.35 + 0.65 * ((i * 37) % 100) / 100)
        dx = math.cos(ang) * sp * u
        dy = math.sin(ang) * sp * u + 55 * u * u
        r = max(0.6, (1 - u) * (1.2 + (i % 3) * 0.6))
        _dot(put, x + dx, y + dy, r, DARK if i % 4 else GOLD)
        if i % 5 == 0:
            _dot(put, x + dx, y + dy, max(0.4, r * 0.4), PALE)
    if u < 0.85:
        rr = 4 + u * 26
        for k in range(48):
            a = 2 * math.pi * k / 48
            put(int(x + math.cos(a) * rr), int(y + math.sin(a) * rr * 0.35), GREY if k % 3 else GOLD)


def draw_petro(put: Put, o: Any, t: float, W: int = 320, H: int = 180) -> None:
    k = o.kind
    if k == "pumpjack":
        draw_pumpjack(put, o, t)
    elif k == "barrel":
        draw_barrel(put, o, t)
    elif k == "droplet":
        draw_droplet(put, o, t)
    elif k == "molecule":
        draw_molecule(put, o, t)
    elif k == "column":
        draw_column(put, o, t)
    elif k == "cutbar":
        draw_cutbar(put, o, t)
    elif k == "product":
        draw_product(put, o, t)
    elif k == "kinetic":
        draw_kinetic(put, o, t)
    elif k == "splash":
        draw_splash(put, o, t)
