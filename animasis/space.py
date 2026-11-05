"""Space & navigation-diagram overlays (GNSS explainer): planet, orbit, satellite, range, ring,
pin, phone, glyph.  All are world-space ``back`` layer kinds drawn by :func:`draw_space`.

Satellites can sit at ``x``/``y`` (with optional ``bob``) or fly an ``orbit: [cx, cy, rx, ry]``
with ``period`` seconds and ``phase`` degrees; the upper half of an orbit is the far side and is
hidden behind a planet given by ``occlude: [cx, cy, r]``.  Give an overlay an ``id`` and the
camera can target it (orbiting satellites are tracked live).
"""

from __future__ import annotations

import math
from typing import Any, Callable

Put = Callable[[int, int, int], None]

SPACE_KINDS = {"planet", "orbit", "satellite", "range", "ring", "pin", "phone", "glyph"}

_W, _H = 320, 180


def _fill_circle(put: Put, cx: float, cy: float, r: float, c: int) -> None:
    for yy in range(int(cy - r) - 1, int(cy + r) + 2):
        for xx in range(int(cx - r) - 1, int(cx + r) + 2):
            if (xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2 <= r * r:
                put(xx, yy, c)


def _rect(put: Put, x0: float, y0: float, x1: float, y1: float, c: int) -> None:
    for yy in range(int(y0), int(y1)):
        for xx in range(int(x0), int(x1)):
            put(xx, yy, c)


def _line(put: Put, x0: float, y0: float, x1: float, y1: float, c: int, dash: tuple[int, int] | None = None,
          prog: float = 1.0, width: int = 1) -> None:
    n = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
    on, off = dash or (n + 1, 0)
    for i in range(int(n * prog) + 1):
        if dash and i % (on + off) >= on:
            continue
        u = i / n
        x, y = int(round(x0 + (x1 - x0) * u)), int(round(y0 + (y1 - y0) * u))
        put(x, y, c)
        if width > 1:
            put(x + 1, y, c)
            put(x, y + 1, c)


def _ramp(t: float, t0: float, dur: float) -> float:
    if dur <= 0:
        return 1.0 if t >= t0 else 0.0
    return min(1.0, max(0.0, (t - t0) / dur))


# --------------------------------------------------------------------------- satellites

def sat_pos(o: Any, t: float) -> tuple[float, float, bool]:
    p = o.p
    if "orbit" in p:
        cx, cy, rx, ry = (float(v) for v in p["orbit"])
        th = math.radians(float(p.get("phase", 0))) + 2 * math.pi * t / float(p.get("period", 12))
        return cx + rx * math.cos(th), cy + ry * math.sin(th), math.sin(th) < 0
    x, y = float(p.get("x", 160)), float(p.get("y", 60))
    bob = float(p.get("bob", 0))
    if bob:
        y += bob * math.sin(t * 1.7 + x * 0.05)
    if "drift" in p:
        x += float(p["drift"]) * (t - o.t)
    return x, y, False


def _hidden_behind(p: dict, x: float, y: float, behind: bool) -> bool:
    if not behind or "occlude" not in p:
        return False
    ocx, ocy, orr = (float(v) for v in p["occlude"])
    return (x - ocx) ** 2 + (y - ocy) ** 2 < (orr + 1) ** 2


def draw_satellite(put: Put, x: float, y: float, s: int = 1, body: int = 7, t: float = 0.0,
                   panel: int = 10, blink: bool = True) -> None:
    """Gold-foil bus, two blue solar wings, nadir antenna, blinking beacon."""
    s = max(1, int(s))
    x, y = int(round(x)), int(round(y))
    # wings + booms
    _rect(put, x - 5 * s, y - 0, x + 5 * s, y + max(1, s // 2 + 0) + 0 if s > 1 else y + 1, 3)
    for side in (-1, 1):
        x0 = x + side * 4 * s
        xa, xb = (x0 - 8 * s, x0) if side < 0 else (x0 + 1, x0 + 1 + 8 * s)
        _rect(put, xa - 1, y - 3 * s - 1, xb + 1, y + 3 * s + 1, 16)
        _rect(put, xa, y - 3 * s, xb, y + 3 * s, panel)
        for gx in range(xa + 2 * s, xb, 2 * s + 1):
            _rect(put, gx, y - 3 * s, gx + 1, y + 3 * s, 25)
        _rect(put, xa, y, xb, y + 1, 25)
        put(xa + 1, y - 3 * s, 9)
    # bus
    _rect(put, x - 3 * s - 1, y - 3 * s - 1, x + 3 * s + 1, y + 3 * s + 1, 16)
    _rect(put, x - 3 * s, y - 3 * s, x + 3 * s, y + 3 * s, body)
    _rect(put, x - 3 * s, y - 3 * s, x - 3 * s + max(1, s), y + 3 * s, 31 if body == 7 else 4)
    _rect(put, x + 3 * s - max(1, s), y - 3 * s, x + 3 * s, y + 3 * s, 6 if body == 7 else 2)
    # antenna dish (points down at Earth)
    _rect(put, x - 2 * s, y + 3 * s + 1, x + 2 * s, y + 3 * s + 1 + max(1, s), 3)
    _rect(put, x - s, y + 3 * s + 1 + max(1, s), x + s, y + 3 * s + 1 + 2 * max(1, s), 4)
    if blink and int(t * 2) % 2 == 0:
        put(x, y - 3 * s - 2, 5)
        if s > 1:
            put(x, y - 3 * s - 3, 26)


def _draw_signal(put: Put, x: float, y: float, t: float, p: dict) -> None:
    """Expanding arcs from a satellite toward ``aim`` (default straight down)."""
    ax, ay = p.get("aim", [x, y + 100])
    base = math.atan2(float(ay) - y, float(ax) - x)
    spread = math.radians(float(p.get("spread", 32)))
    maxr = float(p.get("reach", 60))
    spacing = maxr / 3
    sp = float(p.get("wave_speed", 30))
    for k in range(3):
        r = (t * sp + k * spacing) % maxr + 6
        c = 31 if r < maxr * 0.4 else (7 if r < maxr * 0.75 else 6)
        n = max(6, int(r * spread * 2 / 1.6))
        for i in range(n + 1):
            a = base - spread + 2 * spread * i / n
            put(int(round(x + r * math.cos(a))), int(round(y + r * math.sin(a))), c)


# --------------------------------------------------------------------------- planet

def _land(lon: float, lat: float) -> float:
    return (math.sin(2 * lon + 0.5) * math.cos(1.5 * lat) + 0.55 * math.sin(3 * lon - 2 * lat + 1.3)
            + 0.35 * math.sin(5 * lon + 4 * lat + 0.7) + 0.25 * math.cos(7 * lon - 5 * lat))


def _cloud(lon: float, lat: float) -> float:
    return math.sin(4 * lon + 3 * lat) * math.cos(3 * lat - lon * 2 + 1) + 0.4 * math.sin(9 * lon - 2 * lat)


def draw_planet(put: Put, p: dict, t: float) -> None:
    cx, cy, r = float(p.get("x", 160)), float(p.get("y", 90)), float(p.get("r", 40))
    spin = float(p.get("spin", 0.12))
    L = (-0.55, -0.45, 0.70)
    ln = math.sqrt(sum(v * v for v in L))
    L = tuple(v / ln for v in L)
    halo = 2.5 / r + 1
    x0, x1 = max(0, int(cx - r * halo) - 1), min(_W, int(cx + r * halo) + 2)
    y0, y1 = max(0, int(cy - r * halo) - 1), min(_H, int(cy + r * halo) + 2)
    for yy in range(y0, y1):
        dy = (yy + 0.5 - cy) / r
        for xx in range(x0, x1):
            dx = (xx + 0.5 - cx) / r
            d2 = dx * dx + dy * dy
            if d2 > 1:
                if d2 < halo * halo and (dx * L[0] + dy * L[1] < 0.25):
                    put(xx, yy, 9 if d2 < (1 + 1.2 / r) ** 2 else 10)
                continue
            z = math.sqrt(1 - d2)
            lat = math.asin(max(-1.0, min(1.0, -dy)))
            lon = math.atan2(dx, z) + spin * t
            light = dx * L[0] + dy * L[1] + z * L[2]
            land = _land(lon, lat) > 0.3
            ice = abs(lat) > 1.22
            cloud = _cloud(lon * 2.6 + t * 0.03, lat * 2.2) > 1.05 and (xx * 3 + yy) % 3 != 0
            dither = (xx + yy) % 2 == 0
            if light < 0.02:  # night side, with a few city lights on land
                c = 16 if land else 0
                if land and ((xx * 13 + yy * 7) % 23 == 0):
                    c = 7
            elif light < 0.3:
                c = 3 if ice else (15 if land else 25)
                if cloud and dither:
                    c = 2
            else:
                c = 4 if ice else (8 if land else 10)
                if land and light > 0.85 and dither:
                    c = 30
                if not land and not ice and light > 0.9:
                    c = 9
                if cloud:
                    c = 4 if light > 0.5 else 3
            if d2 > 0.9 and light > 0.1 and not cloud:  # thin limb haze
                c = 9 if dither else c
            put(xx, yy, c)


def draw_orbit(put: Put, p: dict) -> None:
    cx, cy, rx, ry = (float(v) for v in p["orbit"])
    half = str(p.get("half", "all"))
    c = int(p.get("color", 2))
    n = int(2 * math.pi * max(rx, ry) / 2)
    for k in range(n):
        if k % 3 == 2:
            continue
        th = 2 * math.pi * k / n
        back = math.sin(th) < 0
        if (half == "back" and not back) or (half == "front" and back):
            continue
        x, y = cx + rx * math.cos(th), cy + ry * math.sin(th)
        if _hidden_behind(p, x, y, back):
            continue
        put(int(round(x)), int(round(y)), c)


# --------------------------------------------------------------------------- diagram parts

def draw_range(put: Put, o: Any, t: float) -> None:
    p = o.p
    x0, y0, x1, y1 = (float(p[k]) for k in ("x0", "y0", "x1", "y1"))
    prog = _ramp(t, o.t, float(p.get("draw", 0.8)))
    dash = tuple(p.get("dash", (3, 2))) if p.get("dash", True) else None
    _line(put, x0, y0, x1, y1, int(p.get("color", 31)), dash=dash, prog=prog, width=int(p.get("width", 1)))
    sp = float(p.get("pulse", 0))
    if sp and prog >= 1:
        length = math.hypot(x1 - x0, y1 - y0)
        for k in range(3):
            u = ((t - o.t) * sp / max(1, length) + k / 3) % 1
            px, py = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            _rect(put, px - 1, py - 1, px + 2, py + 2, 7)
            put(int(px), int(py), 4)


def draw_ring(put: Put, o: Any, t: float) -> None:
    p = o.p
    cx, cy, r = float(p.get("x", 160)), float(p.get("y", 90)), float(p.get("r", 40))
    prog = _ramp(t, o.t, float(p.get("grow", 1.2)))
    a0 = math.radians(float(p.get("start", 90)))
    c = int(p.get("color", 31))
    fuzz = float(p.get("fuzz", 0))
    if "sharpen" in p:  # [t0, dur] fuzz -> 0
        s0, sd = (float(v) for v in p["sharpen"])
        fuzz *= 1 - _ramp(t, s0, sd)
    n = max(24, int(2 * math.pi * r / 0.8))
    for i in range(int(n * prog) + 1):
        a = a0 + 2 * math.pi * i / n
        if fuzz >= 1:
            for k, dr in enumerate(range(-int(fuzz), int(fuzz) + 1)):
                if (i + k) % 3 == 0:
                    put(int(round(cx + (r + dr) * math.cos(a))), int(round(cy + (r + dr) * math.sin(a))), c)
        elif i % 4 != 3:
            put(int(round(cx + r * math.cos(a))), int(round(cy + r * math.sin(a))), c)
    if p.get("center", True) and prog > 0:
        _fill_circle(put, cx, cy, 1.6, c)


def draw_pin(put: Put, o: Any, t: float) -> None:
    p = o.p
    x, y = float(p.get("x", 160)), float(p.get("y", 120))
    drop = float(p.get("drop", 0.4))
    u = _ramp(t, o.t, drop)
    y_off = -(1 - u) ** 2 * 30
    c = int(p.get("color", 5))
    if u >= 1 and p.get("pulse", True):
        rr = ((t - o.t - drop) * 14) % 14 + 2
        for i in range(36):
            a = 2 * math.pi * i / 36
            if i % 2 == 0:
                put(int(x + rr * 1.6 * math.cos(a)), int(y + rr * 0.6 * math.sin(a)), c)
    s = float(p.get("size", 1))
    yy = y + y_off
    _fill_circle(put, x, yy - 9 * s, 5.2 * s, 16)
    _fill_circle(put, x, yy - 9 * s, 4.4 * s, c)
    for k in range(int(6 * s)):  # tapered tip
        w = (6 * s - k) * 0.55
        _rect(put, x - w, yy - 6 * s + k, x + w + 1, yy - 5 * s + k, c)
        put(int(x - w) - 1, int(yy - 6 * s + k), 16)
        put(int(x + w) + 1, int(yy - 6 * s + k), 16)
    _fill_circle(put, x, yy - 9 * s, 1.8 * s, 4)


def draw_phone(put: Put, o: Any, t: float) -> None:
    """Smartphone with a map app: roads, park, river, blue location dot (searching -> locked)."""
    p = o.p
    cx, cy = float(p.get("x", 160)), float(p.get("y", 90))
    w, h = int(p.get("w", 50)), int(p.get("h", 92))
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    x1, y1 = x0 + w, y0 + h
    _rect(put, x0 + 1, y0, x1 - 1, y1, 16)
    _rect(put, x0, y0 + 1, x1, y1 - 1, 16)
    _rect(put, x0 + 1, y0 + 1, x1 - 1, y1 - 1, 1)
    sx0, sy0, sx1, sy1 = x0 + 3, y0 + 8, x1 - 3, y1 - 6
    # map
    _rect(put, sx0, sy0, sx1, sy1, 4)
    for yy in range(sy0, sy1):
        for xx in range(sx0, sx1):
            if (xx * 3 + yy * 5) % 11 == 0:
                put(xx, yy, 3)
    _rect(put, sx0 + 3, sy0 + 6, sx0 + 18, sy0 + 22, 30)            # park
    for k in range(sy1 - sy0):                                      # river
        rx = sx1 - 12 + int(4 * math.sin(k / 7))
        _rect(put, rx, sy0 + k, rx + 6, sy0 + k + 1, 9)
    for gy in range(sy0 + 28, sy1, 22):                             # streets
        _rect(put, sx0, gy, sx1, gy + 2, 3)
    for gx in range(sx0 + 10, sx1, 16):
        _rect(put, gx, sy0, gx + 2, sy1, 3)
    mx = int((sx0 + sx1) / 2) - 1
    _rect(put, mx - 1, sy0, mx + 3, sy1, 7)                         # main road
    _rect(put, mx - 1, sy0, mx, sy1, 6)
    dx, dy = (sx0 + sx1) / 2, (sy0 + sy1) / 2 + 6
    locked = t >= float(p.get("lock", o.t))
    if locked:
        u = ((t - float(p.get("lock", o.t))) * 1.2) % 1
        rr = (3 + 9 * u) * max(1.0, w / 50)
        for i in range(40):
            a = 2 * math.pi * i / 40
            if i % 2 == 0:
                put(int(round(dx + rr * math.cos(a))), int(round(dy + rr * math.sin(a))), 9)
        k = max(1.0, w / 50)
        _fill_circle(put, dx, dy, 4.2 * k, 4)
        _fill_circle(put, dx, dy, 3.0 * k, 10)
        put(int(dx) - 1, int(dy) - 1, 9)
    else:  # searching spinner
        for i in range(8):
            a = 2 * math.pi * i / 8 + t * 6
            c = 10 if i < 3 else 3
            put(int(round(dx + 5 * math.cos(a))), int(round(dy + 5 * math.sin(a))), c)
    # status bar with satellite count dots + home bar
    _rect(put, x0 + 3, y0 + 3, x1 - 3, y0 + 7, 16)
    nsat = int(p.get("sats", 0))
    if "sats_from" in p:  # [t0, every]
        s0, every = (float(v) for v in p["sats_from"])
        nsat = max(0, min(nsat or 4, int((t - s0) / every) + 1)) if t >= s0 else 0
    for i in range(nsat):
        _rect(put, x1 - 6 - i * 3, y0 + 4, x1 - 4 - i * 3, y0 + 6, 30)
    _rect(put, int(cx) - 6, y1 - 4, int(cx) + 6, y1 - 3, 3)
    _rect(put, int(cx) - 3, y0 + 4, int(cx) + 3, y0 + 5, 2)


def _glyph(put: Put, name: str, x: float, y: float, s: int, t: float) -> None:
    """Simple procedural pictograms: car, scooter, bike, tripod, clock, tower, plane, ship."""
    x, y = int(x), int(y)
    if name == "car":
        _rect(put, x - 13 * s, y - 9 * s, x + 13 * s, y - 2 * s, 16)
        _rect(put, x - 12 * s, y - 8 * s, x + 12 * s, y - 3 * s, 5)
        _rect(put, x - 7 * s, y - 14 * s, x + 6 * s, y - 8 * s, 16)
        _rect(put, x - 6 * s, y - 13 * s, x + 5 * s, y - 8 * s, 9)
        _rect(put, x - 1, y - 13 * s, x + 1, y - 8 * s, 16)
        _rect(put, x + 10 * s, y - 7 * s, x + 12 * s, y - 5 * s, 31)
        for wx in (x - 7 * s, x + 7 * s):
            _fill_circle(put, wx, y - 2 * s, 3.4 * s, 16)
            _fill_circle(put, wx, y - 2 * s, 1.5 * s, 3)
    elif name in ("bike", "scooter"):
        for wx in (x - 8 * s, x + 8 * s):
            _fill_circle(put, wx, y - 5 * s, 5 * s, 16)
            _fill_circle(put, wx, y - 5 * s, 3.6 * s, 4 if name == "bike" else 3)
            _fill_circle(put, wx, y - 5 * s, 1, 16)
        col = 30 if name == "bike" else 6
        _line(put, x - 8 * s, y - 5 * s, x, y - 5 * s, col, width=2)
        _line(put, x, y - 5 * s, x - 3 * s, y - 13 * s, col, width=2)
        _line(put, x - 8 * s, y - 5 * s, x - 3 * s, y - 13 * s, col, width=2)
        _line(put, x + 8 * s, y - 5 * s, x + 5 * s, y - 15 * s, col, width=2)
        _line(put, x - 3 * s, y - 13 * s, x + 5 * s, y - 13 * s, col, width=2)
        _rect(put, x - 6 * s, y - 15 * s, x - 1 * s, y - 13 * s, 16)
        _rect(put, x + 3 * s, y - 16 * s, x + 8 * s, y - 15 * s, 16)
        if name == "scooter":  # delivery box
            _rect(put, x - 13 * s, y - 22 * s, x - 3 * s, y - 13 * s, 16)
            _rect(put, x - 12 * s, y - 21 * s, x - 4 * s, y - 14 * s, 7)
            _rect(put, x - 12 * s, y - 18 * s, x - 4 * s, y - 17 * s, 6)
    elif name == "tripod":
        _line(put, x, y - 14 * s, x - 7 * s, y, 14, width=2)
        _line(put, x, y - 14 * s, x + 7 * s, y, 14, width=2)
        _line(put, x, y - 14 * s, x, y, 14, width=2)
        _rect(put, x - 5 * s, y - 20 * s, x + 5 * s, y - 14 * s, 16)
        _rect(put, x - 4 * s, y - 19 * s, x + 4 * s, y - 15 * s, 7)
        _rect(put, x + 4 * s, y - 18 * s, x + 7 * s, y - 16 * s, 2)
        _fill_circle(put, x, y - 21 * s, 1.5 * s, 5)
    elif name == "clock":
        r = 10 * s
        _fill_circle(put, x, y - r, r + 1, 16)
        _fill_circle(put, x, y - r, r, 4)
        for k in range(12):
            a = 2 * math.pi * k / 12
            put(int(x + (r - 2) * math.cos(a)), int(y - r + (r - 2) * math.sin(a)), 2)
        for length, rate, c in ((r * 0.5, 0.25, 16), (r * 0.8, 3.0, 16), (r * 0.85, 12.0, 5)):
            a = t * rate - math.pi / 2
            _line(put, x, y - r, x + length * math.cos(a), y - r + length * math.sin(a), c)
        _fill_circle(put, x, y - r, 1.2, 5)
    elif name == "plane":
        _rect(put, x - 14 * s, y - 3 * s, x + 12 * s, y + 1 * s, 4)
        _line(put, x - 2 * s, y - 2 * s, x - 8 * s, y - 11 * s, 3, width=2)
        _line(put, x - 2 * s, y, x - 8 * s, y + 8 * s, 3, width=2)
        _rect(put, x - 14 * s, y - 8 * s, x - 11 * s, y - 2 * s, 5)
        _rect(put, x + 10 * s, y - 3 * s, x + 14 * s, y, 9)
    elif name == "ship":
        _rect(put, x - 14 * s, y - 6 * s, x + 14 * s, y, 5)
        _rect(put, x - 12 * s, y - 2 * s, x + 12 * s, y, 22)
        _rect(put, x - 6 * s, y - 12 * s, x + 4 * s, y - 6 * s, 4)
        _rect(put, x - 4 * s, y - 11 * s, x + 2 * s, y - 9 * s, 9)
        _rect(put, x + 6 * s, y - 16 * s, x + 8 * s, y - 6 * s, 2)


def draw_space(put: Put, o: Any, t: float, W: int = 320, H: int = 180) -> None:
    global _W, _H
    _W, _H = W, H
    k, p = o.kind, o.p
    if k == "planet":
        draw_planet(put, p, t)
    elif k == "orbit":
        draw_orbit(put, p)
    elif k == "satellite":
        x, y, behind = sat_pos(o, t)
        if _hidden_behind(p, x, y, behind):
            return
        s = int(p.get("scale", 1))
        if behind and p.get("dim_behind", True) and s == 1:
            s = 1
        if p.get("signal"):
            if not isinstance(p.get("signal"), (list, tuple)) or (p["signal"][0] <= t < p["signal"][1]):
                _draw_signal(put, x, y, t, p)
        draw_satellite(put, x, y, s, int(p.get("body", 7)), t, int(p.get("panel", 10)))
    elif k == "range":
        draw_range(put, o, t)
    elif k == "ring":
        draw_ring(put, o, t)
    elif k == "pin":
        draw_pin(put, o, t)
    elif k == "phone":
        draw_phone(put, o, t)
    elif k == "glyph":
        _glyph(put, str(p.get("name", "car")), float(p.get("x", 160)), float(p.get("y", 120)),
               int(p.get("scale", 1)), t)
