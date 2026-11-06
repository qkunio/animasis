"""Flight-explainer overlays: aircraft, force arrows and animated airfoil flow."""

from __future__ import annotations

import math
from typing import Any, Callable

from . import palette as pal

Put = Callable[[int, int, int], None]
Pix = tuple[int, int]
FLIGHT_KINDS = {"flight_plane", "airfoil", "force"}


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _smooth(v: float) -> float:
    v = _clamp(v)
    return v * v * (3 - 2 * v)


def _circle(put: Put, cx: float, cy: float, rx: float, ry: float, color: int) -> None:
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / max(rx, 0.1)) ** 2 + ((y + 0.5 - cy) / max(ry, 0.1)) ** 2 <= 1:
                put(x, y, color)


def _line(put: Put, a: tuple[float, float], b: tuple[float, float], color: int,
          width: int = 1, dash: tuple[int, int] | None = None, prog: float = 1.0) -> None:
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = max(1, int(math.ceil(max(abs(dx), abs(dy)))))
    on, off = dash or (n + 1, 0)
    for i in range(int(n * _clamp(prog)) + 1):
        if dash and i % (on + off) >= on:
            continue
        u = i / n
        x, y = int(round(a[0] + dx * u)), int(round(a[1] + dy * u))
        for oy in range(-(width // 2), width - width // 2):
            for ox in range(-(width // 2), width - width // 2):
                put(x + ox, y + oy, color)


def _polygon_mask(points: list[tuple[float, float]]) -> set[Pix]:
    x0 = math.floor(min(p[0] for p in points))
    x1 = math.ceil(max(p[0] for p in points))
    y0 = math.floor(min(p[1] for p in points))
    y1 = math.ceil(max(p[1] for p in points))
    out: set[Pix] = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px, py = x + 0.5, y + 0.5
            inside = False
            j = len(points) - 1
            for i, (xi, yi) in enumerate(points):
                xj, yj = points[j]
                if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
            if inside:
                out.add((x, y))
    return out


def _paint(put: Put, mask: set[Pix], color: int, outline: int | None = pal.OUTLINE_SOFT) -> None:
    if outline is not None:
        ring: set[Pix] = set()
        for x, y in mask:
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q not in mask:
                    ring.add(q)
        for x, y in ring:
            put(x, y, outline)
    for x, y in mask:
        put(x, y, color)


def _arrow(put: Put, x: float, y: float, dx: float, dy: float, length: float,
           color: int, width: int = 2, prog: float = 1.0) -> None:
    mag = max(0.001, math.hypot(dx, dy))
    ux, uy = dx / mag, dy / mag
    ex, ey = x + ux * length * _clamp(prog), y + uy * length * _clamp(prog)
    _line(put, (x, y), (ex, ey), color, width)
    if prog < 0.85:
        return
    head = min(8.0, max(4.0, length * 0.2))
    px, py = -uy, ux
    _line(put, (ex, ey), (ex - ux * head + px * head * 0.55, ey - uy * head + py * head * 0.55), color, width)
    _line(put, (ex, ey), (ex - ux * head - px * head * 0.55, ey - uy * head - py * head * 0.55), color, width)


def draw_force(put: Put, o: Any, t: float) -> None:
    p = o.p
    directions = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    dx, dy = directions.get(str(p.get("dir", "up")), (float(p.get("dx", 0)), float(p.get("dy", -1))))
    delay = float(p.get("delay", 0))
    grow = float(p.get("grow", 0.35))
    prog = _smooth((t - o.t - delay) / grow) if grow > 0 else float(t >= o.t + delay)
    _arrow(put, float(p.get("x", 160)), float(p.get("y", 90)), dx, dy,
           float(p.get("length", 30)), int(p.get("color", 7)), int(p.get("width", 2)), prog)


def draw_plane(put: Put, o: Any, t: float) -> None:
    p = o.p
    x, y = float(p.get("x", 160)), float(p.get("y", 80))
    pitch = float(p.get("pitch", 0))
    if "move" in p:
        t0, t1 = (float(v) for v in p["move"])
        u = _smooth((t - t0) / max(0.001, t1 - t0))
        x += (float(p.get("x1", x)) - x) * u
        y += (float(p.get("y1", y)) - y) * u
        pitch += float(p.get("pitch1", pitch)) * u
    else:
        x += float(p.get("drift", 0)) * max(0.0, t - o.t)
    y += float(p.get("bob", 0)) * math.sin(t * 1.8)
    scale = float(p.get("scale", 1))
    a = math.radians(pitch)
    ca, sa = math.cos(a), math.sin(a)

    def tr(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
        return [(x + scale * (px * ca - py * sa), y + scale * (px * sa + py * ca)) for px, py in points]

    speed = float(p.get("speed", 0))
    if speed:
        for i in range(7):
            span = 70 + i % 3 * 14
            sx = x - scale * (62 + ((t * speed + i * 19) % span))
            sy = y + scale * (-22 + i * 7)
            _line(put, (sx - scale * (8 + i % 3 * 4), sy), (sx, sy), 3 if i % 2 else 9)

    far_wing = tr([(2, -3), (20, -2), (-5, -24), (-17, -23)])
    tail = tr([(-48, -5), (-54, -28), (-45, -27), (-28, -5)])
    tailplane = tr([(-46, 1), (-28, 1), (-45, 12), (-56, 10)])
    body = tr([(-57, -4), (-45, -8), (25, -8), (42, -6), (53, -3), (59, 1),
               (54, 5), (35, 8), (-39, 8), (-54, 4)])
    near_wing = tr([(-10, -1), (18, 0), (-9, 25), (-25, 23)])
    _paint(put, _polygon_mask(far_wing), 2)
    _paint(put, _polygon_mask(tail), 5)
    _paint(put, _polygon_mask(tailplane), 3)
    _paint(put, _polygon_mask(body), 4)
    shade = tr([(-52, 3), (52, 2), (47, 6), (33, 8), (-39, 8), (-52, 5)])
    _paint(put, _polygon_mask(shade), 3, None)
    _paint(put, _polygon_mask(near_wing), 3)
    stripe = tr([(-48, -1), (46, -1), (48, 1), (-48, 1)])
    _paint(put, _polygon_mask(stripe), 5, None)

    for wx in range(-31, 30, 8):
        window = tr([(wx, -5), (wx + 4, -5), (wx + 4, -2), (wx, -2)])
        _paint(put, _polygon_mask(window), 10, None)
    cockpit = tr([(40, -5), (48, -3), (52, -1), (43, -1)])
    _paint(put, _polygon_mask(cockpit), 9, None)

    engine_center = tr([(2, 14)])[0]
    _circle(put, engine_center[0], engine_center[1], 9 * scale, 5 * scale, 16)
    _circle(put, engine_center[0], engine_center[1] - 0.5 * scale, 7 * scale, 3.5 * scale, 2)
    intake = tr([(8, 11), (10, 13), (10, 16), (8, 17)])
    _paint(put, _polygon_mask(intake), 1, None)

    if p.get("gear"):
        for gx, gy in ((-30, 7), (30, 7)):
            a0 = tr([(gx, gy)])[0]
            a1 = tr([(gx, gy + 15)])[0]
            _line(put, a0, a1, 16, 2)
            _circle(put, a1[0], a1[1], 3 * scale, 3 * scale, 16)
            _circle(put, a1[0], a1[1], 1.2 * scale, 1.2 * scale, 3)


def _airfoil_point(cx: float, cy: float, chord: float, s: float, side: float,
                   angle: float, camber: float) -> tuple[float, float]:
    s = _clamp(s)
    yt = 5 * 0.12 * chord * (0.2969 * math.sqrt(s) - 0.126 * s - 0.3516 * s * s
                             + 0.2843 * s ** 3 - 0.1036 * s ** 4)
    lx = (s - 0.5) * chord
    ly = -camber * math.sin(math.pi * s) + side * yt
    a = math.radians(angle)
    return cx + lx * math.cos(a) - ly * math.sin(a), cy + lx * math.sin(a) + ly * math.cos(a)


def _flow_y(x: float, base: float, cx: float, cy: float, chord: float,
            wash: float, stall: float, t: float, index: int) -> float:
    near = math.exp(-((x - cx) / (chord * 0.58)) ** 4)
    sign = -1 if base < 0 else 1
    clearance = max(0.0, 19.0 - abs(base)) * near * sign
    downstream = _smooth((x - (cx + chord * 0.15)) / (chord * 0.75))
    down = wash * downstream * math.exp(-abs(base) / 75)
    separated = stall * downstream
    wave = math.sin((x - cx) * 0.12 - t * 5 + index * 1.7) * 7 * separated
    lift_away = -18 * separated * near if base < 0 else 0
    return cy + base + clearance + down * (1 - stall * 0.85) + wave + lift_away


def draw_airfoil(put: Put, o: Any, t: float) -> None:
    p = o.p
    cx, cy = float(p.get("x", 160)), float(p.get("y", 88))
    chord = float(p.get("chord", 126))
    angle = float(p.get("angle", 6))
    if "angle_move" in p:
        t0, t1 = (float(v) for v in p["angle_move"])
        u = _smooth((t - t0) / max(0.001, t1 - t0))
        angle += (float(p.get("angle1", angle)) - angle) * u
    camber = float(p.get("camber", 3.2))
    wash = float(p.get("wash", max(8, angle * 1.7)))
    stall = _clamp(float(p.get("stall", 0)))
    if "stall_move" in p:
        t0, t1 = (float(v) for v in p["stall_move"])
        u = _smooth((t - t0) / max(0.001, t1 - t0))
        stall += (float(p.get("stall1", 1)) - stall) * u
    x0, x1 = cx - chord * 0.9, cx + chord * 1.0
    bases = (-48, -33, -21, -10, 10, 22, 35, 49)

    for j, base in enumerate(bases):
        col = 9 if base < 0 else 3
        previous = None
        for xx in range(int(x0), int(x1) + 1, 2):
            yy = _flow_y(xx, base, cx, cy, chord, wash, stall, t, j)
            if previous is not None:
                _line(put, previous, (xx, yy), col)
            previous = (xx, yy)
        speed = float(p.get("flow_speed", 42)) * (1.55 if p.get("pressure") and base < 0 else 1)
        phase = ((max(0.0, t - o.t) * speed + j * 23) % (x1 - x0))
        px = x0 + phase
        py = _flow_y(px, base, cx, cy, chord, wash, stall, t, j)
        _circle(put, px, py, 1.7, 1.7, 31 if base < 0 else 4)
        if j in (1, 6):
            ey = _flow_y(x1 - 3, base, cx, cy, chord, wash, stall, t, j)
            _arrow(put, x1 - 12, ey, 1, 0.15 * (1 - stall), 9, col, 1)

    if p.get("race"):
        for base, speed, col in ((-21, 64, 31), (22, 39, 30)):
            px = min(x1, x0 + max(0.0, t - o.t) * speed)
            j = bases.index(base)
            py = _flow_y(px, base, cx, cy, chord, wash, stall, t, j)
            _circle(put, px, py, 3.3, 3.3, 16)
            _circle(put, px, py, 2.1, 2.1, col)

    upper = [_airfoil_point(cx, cy, chord, i / 40, -1, angle, camber) for i in range(41)]
    lower = [_airfoil_point(cx, cy, chord, i / 40, 1, angle, camber) for i in range(40, -1, -1)]
    mask = _polygon_mask(upper + lower)
    _paint(put, mask, 4)
    leading = _airfoil_point(cx, cy, chord, 0.02, -1, angle, camber)
    _circle(put, leading[0] + 3, leading[1] + 2, 5, 3, 3)
    trailing = _airfoil_point(cx, cy, chord, 0.97, -1, angle, camber)
    _line(put, trailing, _airfoil_point(cx, cy, chord, 0.97, 1, angle, camber), 2)

    if p.get("pressure"):
        for i in range(5):
            xx = cx - chord * 0.34 + i * chord * 0.16
            top = _airfoil_point(cx, cy, chord, 0.16 + i * 0.16, -1, angle, camber)
            bottom = _airfoil_point(cx, cy, chord, 0.16 + i * 0.16, 1, angle, camber)
            _arrow(put, top[0], top[1] - 10, 0, -1, 7, 9, 1)
            _arrow(put, bottom[0], bottom[1] + 10, 0, 1, 7, 7, 1)

    if p.get("wash_arrows"):
        for dy in (-13, 17):
            _arrow(put, cx + chord * 0.67, cy + dy + 10, 0.15, 1, 19 + wash * 0.35, 7, 2)

    if p.get("angle_guide"):
        _line(put, (cx - chord * 0.75, cy), (cx + chord * 0.72, cy), 2, dash=(3, 3))
        _line(put, _airfoil_point(cx, cy, chord, -0.18, 0, angle, 0),
              _airfoil_point(cx, cy, chord, 1.18, 0, angle, 0), 7, dash=(4, 3))
        radius = chord * 0.58
        for deg in range(max(1, int(angle)) + 1):
            a = -math.pi + math.radians(deg)
            put(int(round(cx + radius * math.cos(a))), int(round(cy + radius * math.sin(a))), 7)

    if stall:
        for k in range(4):
            ex = cx + chord * 0.48 + k * 15
            ey = cy - 28 + (k % 2) * 18
            for i in range(18):
                a0 = t * (1.5 if k % 2 else -1.4) + i * 0.34 + k
                r = 1.5 + i * 0.22
                put(int(round(ex + r * math.cos(a0))), int(round(ey + r * math.sin(a0))), 5)


def draw_flight(put: Put, o: Any, t: float, W: int = 320, H: int = 180) -> None:
    if o.kind == "flight_plane":
        draw_plane(put, o, t)
    elif o.kind == "airfoil":
        draw_airfoil(put, o, t)
    elif o.kind == "force":
        draw_force(put, o, t)
