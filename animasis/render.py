"""Pixel renderer: fixed palette, nearest-neighbor upscale, MP4/GIF export."""

from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Iterable, Sequence

from PIL import Image

from . import palette as pal
from .apparel import draw_prop, resolve_hang
from .sprite import draw_shadow, draw_sprite
from .physics import Body, World
from .skeleton import Character


def _draw_line(
    put: Callable[[int, int, int], None],
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    thickness: float,
    color: int,
) -> None:
    dx = x1 - x0
    dy = y1 - y0
    dist = math.hypot(dx, dy)
    steps = max(1, int(dist) + 1)
    r = max(1, int(round(thickness / 2)))
    for i in range(steps + 1):
        t = i / steps
        cx = x0 + dx * t
        cy = y0 + dy * t
        ix, iy = int(round(cx)), int(round(cy))
        for oy in range(-r, r + 1):
            for ox in range(-r, r + 1):
                if ox * ox + oy * oy <= r * r + 0.5:
                    put(ix + ox, iy + oy, color)


def draw_character(
    put: Callable[[int, int, int], None],
    ch: Character,
    get: Callable[[int, int], int] | None = None,
    ground_y: float | None = None,
) -> None:
    """Rasterise a layered, shaded, outlined sprite for ``ch`` (see sprite.py)."""
    if not ch.visible:
        return
    if get is not None and ground_y is not None:
        draw_shadow(put, get, ch, ground_y)
    hat = ch.look.hat
    others = []
    for item in ch.apparel.get("items", []):
        if item.get("kind") == "hat" and item.get("hang", "head") == "head":
            hat = int(item.get("color", pal.ACCENT))
        else:
            others.append(item)
    cv = draw_sprite(ch, hat=hat)
    for (x, y), c in cv.color.items():
        put(x, y, c)
    for item in others:
        hang = item.get("hang", "chest")
        kind = item.get("kind", "hat")
        px, py = resolve_hang(ch, hang)
        draw_prop(put, kind, px, py, **{k: v for k, v in item.items() if k not in ("hang", "kind")})


def draw_body(put: Callable[[int, int, int], None], body: Body) -> None:
    if body.attached_to:
        return  # drawn via character hold
    draw_prop(put, body.kind, body.x, body.y, r=int(body.w / 2), w=int(body.w), h=int(body.h), color=body.color)


def draw_bg_indoor(buf: list[list[int]], w: int, h: int, ground_y: int) -> None:
    for y in range(h):
        for x in range(w):
            if y < ground_y - 40:
                buf[y][x] = 1  # dark wall shadow
            elif y < ground_y:
                buf[y][x] = pal.WALL
            else:
                buf[y][x] = pal.FLOOR
    # window
    for y in range(20, 55):
        for x in range(20, 55):
            buf[y][x] = pal.SKY if 22 <= x <= 52 and 22 <= y <= 52 else pal.WOOD
    for y in range(22, 53):
        for x in range(22, 53):
            buf[y][x] = 4 if (x + y) % 7 == 0 else pal.SKY
    # shelf
    for x in range(200, 300):
        buf[ground_y - 50][x] = pal.WOOD
        buf[ground_y - 49][x] = pal.WOOD


def draw_bg_outdoor(buf: list[list[int]], w: int, h: int, ground_y: int) -> None:
    for y in range(h):
        for x in range(w):
            if y < ground_y:
                # sky gradient via two bands
                buf[y][x] = pal.SKY if y > 40 else 10
            else:
                buf[y][x] = pal.GROUND if (x // 4 + y) % 3 else 8
    # sun
    cx, cy, r = w - 40, 28, 10
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if 0 <= cy + dy < h and 0 <= cx + dx < w and dx * dx + dy * dy <= r * r:
                buf[cy + dy][cx + dx] = pal.ACCENT
    # hills
    for x in range(w):
        hill = int(8 * math.sin(x / 28.0) + 6 * math.sin(x / 11.0))
        gy = ground_y - 8 - hill
        for y in range(max(0, gy), ground_y):
            buf[y][x] = pal.GROUND


def draw_bg_room(buf: list[list[int]], w: int, h: int, ground_y: int) -> None:
    for y in range(h):
        for x in range(w):
            if y < ground_y:
                buf[y][x] = 3 if y > ground_y - 30 else 2
            else:
                buf[y][x] = 14
    # door
    for y in range(ground_y - 55, ground_y):
        for x in range(w // 2 - 18, w // 2 + 18):
            buf[y][x] = 13 if x in (w // 2 - 18, w // 2 + 17) or y == ground_y - 55 else 12


def draw_bg_market(buf: list[list[int]], w: int, h: int, ground_y: int) -> None:
    """Street market: warm sky, distant town silhouettes with lit windows, tiled pavement."""
    for y in range(h):
        for x in range(w):
            if y < ground_y:
                buf[y][x] = 10 if y < 30 else (pal.SKY if y < 95 else 3)
            else:
                buf[y][x] = 3 if ((x // 12 + (y - ground_y) // 6) % 2) else 2
    for x in range(w):
        buf[ground_y][x] = 16
        if ground_y + 1 < h:
            buf[ground_y + 1][x] = 4
    # clouds
    for cx, cy, r in ((40, 22, 7), (52, 20, 9), (66, 23, 6), (220, 34, 6), (232, 31, 8), (244, 35, 5)):
        for yy in range(cy - r, cy + r):
            for xx in range(cx - r, cx + r):
                if 0 <= yy < h and 0 <= xx < w and (xx - cx) ** 2 + (yy - cy) ** 2 * 2.2 <= r * r:
                    buf[yy][xx] = 4
    # town silhouettes
    rng = [(0, 34, 46), (34, 26, 62), (60, 40, 38), (100, 30, 70), (130, 44, 50), (174, 28, 64),
           (202, 36, 44), (238, 30, 58), (268, 52, 40)]
    for x0, bw, bh in rng:
        top = ground_y - bh
        for yy in range(max(0, top), ground_y):
            for xx in range(x0, min(w, x0 + bw)):
                edge = xx in (x0, x0 + bw - 1) or yy == top
                buf[yy][xx] = 16 if edge else (2 if (x0 // 10) % 2 else 1)
        for yy in range(top + 5, ground_y - 6, 8):
            for xx in range(x0 + 4, min(w - 2, x0 + bw - 4), 7):
                lit = (xx * 7 + yy * 3) % 5 < 2
                for dy in range(3):
                    for dx in range(3):
                        buf[yy + dy][xx + dx] = pal.ACCENT if lit else 25


_COTTAGE_CACHE: dict[tuple[str, int, int, int], list[list[int]]] = {}


def draw_bg_cottage(buf: list[list[int]], w: int, h: int, ground_y: int, season: str = "autumn") -> None:
    """隆中 countryside: layered mountains, bamboo grove, earth path.  season: autumn | snow | spring."""
    key = (season, w, h, ground_y)
    if key not in _COTTAGE_CACHE:
        _COTTAGE_CACHE[key] = _make_cottage(w, h, ground_y, season)
    src = _COTTAGE_CACHE[key]
    for y in range(h):
        buf[y][:] = src[y]


def _make_cottage(w: int, h: int, g: int, season: str) -> list[list[int]]:
    snow = season == "snow"
    spring = season == "spring"
    b = [[0] * w for _ in range(h)]
    # sky bands with a dithered seam between each
    bands = [(0, 2), (34, 3), (80, 3)] if snow else [(0, 10), (30, 9), (88, 4 if spring else 9)]
    for y in range(g):
        for x in range(w):
            c = bands[0][1]
            for y0, col in bands:
                if y >= y0 + 3 or (y >= y0 and (x + y) % 2 == 0):
                    c = col
            b[y][x] = c
    # sun / clouds
    if not snow:
        for cx, cy, r in ((48, 24, 6), (60, 21, 8), (73, 25, 5), (196, 30, 6), (208, 27, 8), (220, 31, 5)):
            for yy in range(cy - r, cy + r):
                for xx in range(cx - r, cx + r):
                    if 0 <= xx < w and (xx - cx) ** 2 + (yy - cy) ** 2 * 2.2 <= r * r:
                        b[yy][xx] = 4
        sx, sy = 280, 22
        for yy in range(sy - 7, sy + 8):
            for xx in range(sx - 7, sx + 8):
                d = (xx - sx) ** 2 + (yy - sy) ** 2
                if d <= 49:
                    b[yy][xx] = 31 if d < 20 else 7
    # far mountains (two ridges)
    for x in range(w):
        far = int(g - 62 - 16 * math.sin(x / 37.0 + 1.3) - 9 * math.sin(x / 13.0) - 6 * math.sin(x / 7.1 + 2))
        near = int(g - 34 - 10 * math.sin(x / 29.0 + 0.4) - 5 * math.sin(x / 9.3 + 1))
        for y in range(max(0, far), g):
            peak = y - far
            if snow:
                c = 4 if peak < 4 else 3
            else:
                c = (3 if peak < 2 else 2) if not spring else (30 if peak < 2 else 8)
            b[y][x] = c
        for y in range(max(0, near), g):
            peak = y - near
            if snow:
                c = 4 if peak < 3 else (3 if (x + y) % 3 else 2)
            else:
                c = (8 if peak < 2 else 15) if not spring else (30 if peak < 2 else (8 if (x + y) % 4 else 15))
            b[y][x] = c
    # bamboo grove on the left and far right
    stalks = [6, 14, 21, 30, 38, 47, 55, 300, 309, 316]
    for i, sx in enumerate(stalks):
        top = g - 96 + (i * 17) % 23
        lean = ((i * 5) % 3 - 1) * 0.04
        for y in range(top, g):
            x = int(sx + (g - y) * lean)
            for dx, c in ((0, 30 if not snow else 3), (1, 8), (2, 15)):
                if 0 <= x + dx < w:
                    b[y][x + dx] = c
            if (y - top) % 11 == 0 and 0 <= x + 2 < w:  # node rings
                b[y][x] = 15
                b[y][x + 1] = 15
                if x + 3 < w:
                    b[y][x + 3] = 15
        # leaf sprays
        for k in range(5):
            ly = top + 4 + k * 12
            lx = int(sx + (g - ly) * lean)
            d = 1 if (k + i) % 2 else -1
            for j in range(7):
                xx, yy = lx + 1 + d * (2 + j), ly + j // 2
                if 0 <= xx < w:
                    b[yy][xx] = 4 if (snow and j < 3) else (15 if j % 3 == 0 else 8)
                if 0 <= xx < w and j > 1:
                    b[yy + 1][xx] = 15
    # ground: earth path with a grass verge (snow cover / spring flowers)
    for y in range(g, h):
        for x in range(w):
            dy = y - g
            if snow:
                c = 4 if (x * 3 + y * 5) % 11 else 3
            elif dy < 3:
                c = 30 if spring else 8
            else:
                c = 23 if ((x // 6 + dy // 3) % 3) else 14
            b[y][x] = c
    for x in range(w):
        b[g][x] = 16 if not snow else 3
    if spring:
        for x in range(3, w, 13):
            y = g + 1 + (x * 7) % 2
            b[y][x] = 21 if (x // 13) % 2 else 7
    elif not snow:
        for x in range(5, w, 17):  # pebbles
            y = g + 7 + (x * 5) % 18
            if y < h:
                b[y][x] = 3
                if x + 1 < w:
                    b[y][x + 1] = 2
    return b


_SPACE_CACHE: dict[tuple[str, int, int], list[list[int]]] = {}


def draw_bg_space(buf: list[list[int]], w: int, h: int, ground_y: int, style: str = "space") -> None:
    """Deep space starfield with a faint nebula (``space``), or a navy blueprint grid (``blueprint``)."""
    key = (style, w, h)
    if key not in _SPACE_CACHE:
        g = [[0] * w for _ in range(h)]
        if style == "blueprint":
            for y in range(h):
                for x in range(w):
                    c = 25
                    if x % 40 == 0 or y % 40 == 0:
                        c = 10 if (x + y) % 2 == 0 else 25
                    elif x % 10 == 0 and y % 10 == 0:
                        c = 10
                    g[y][x] = c
        else:
            for y in range(h):
                for x in range(w):
                    n = math.sin(x / 31.0 + y / 47.0) + math.sin(x / 19.0 - y / 23.0 + 1.7) * 0.7
                    g[y][x] = 25 if (n > 1.45 and (x * 3 + y * 5) % 7 == 0) else (16 if (n > 1.2 and (x + y) % 5 == 0) else 0)
            for i in range(170):
                x, y = (i * 97 + (i * i) % 53) % w, (i * 61 + (i * i * 7) % 89) % h
                c = (4, 3, 2, 31, 28)[i % 5]
                g[y][x] = c
                if i % 17 == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        if 0 <= x + dx < w and 0 <= y + dy < h:
                            g[y + dy][x + dx] = 2
        _SPACE_CACHE[key] = g
    src = _SPACE_CACHE[key]
    for y in range(h):
        buf[y][:] = src[y]


BG_DRAWERS = {
    "space": draw_bg_space,
    "blueprint": lambda b, w, h, g: draw_bg_space(b, w, h, g, "blueprint"),
    "indoor": draw_bg_indoor,
    "outdoor": draw_bg_outdoor,
    "room": draw_bg_room,
    "market": draw_bg_market,
    "cottage": draw_bg_cottage,
    "cottage_snow": lambda b, w, h, g: draw_bg_cottage(b, w, h, g, "snow"),
    "cottage_spring": lambda b, w, h, g: draw_bg_cottage(b, w, h, g, "spring"),
}
from .palace import BG as _PALACE_BG  # noqa: E402

BG_DRAWERS.update(_PALACE_BG)


class FrameBuffer:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.buf = [[0 for _ in range(width)] for _ in range(height)]

    def fill_bg(self, kind: str, ground_y: int) -> None:
        drawer = BG_DRAWERS.get(kind, draw_bg_outdoor)
        drawer(self.buf, self.width, self.height, ground_y)

    def get(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.buf[y][x]
        return 0

    def put(self, x: int, y: int, color: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buf[y][x] = int(color) % len(pal.PALETTE)

    def to_image(self, scale: int = 4) -> Image.Image:
        scale = max(1, int(scale))
        img = Image.new("RGB", (self.width, self.height))
        px = img.load()
        for y in range(self.height):
            row = self.buf[y]
            for x in range(self.width):
                px[x, y] = pal.color(row[x])
        if scale != 1:
            img = img.resize((self.width * scale, self.height * scale), Image.NEAREST)
        return img


_CLEAR = 255  # "transparent" palette slot for screen-space overlay buffers


def fb_to_image(fb: FrameBuffer, transparent: int | None = None) -> Image.Image:
    """Palette buffer -> RGB (or RGBA with ``transparent`` index cleared) at 1x, fast path."""
    flat = bytes(c for row in fb.buf for c in row)
    img = Image.frombytes("P", (fb.width, fb.height), flat)
    pal_bytes = []
    for i in range(256):
        pal_bytes += list(pal.color(i)) if i < len(pal.PALETTE) else [0, 0, 0]
    img.putpalette(pal_bytes)
    if transparent is None:
        return img.convert("RGB")
    img.info["transparency"] = transparent
    return img.convert("RGBA")


def composite_frame(
    characters: Sequence[Character],
    world: World,
    bg: str = "outdoor",
    width: int = 320,
    height: int = 180,
    held: dict[str, str] | None = None,
    under: Callable[[FrameBuffer], None] | None = None,
    over: Callable[[FrameBuffer], None] | None = None,
) -> FrameBuffer:
    """held: object_name -> character_name.

    ``under`` / ``over`` are optional hooks drawn right after the background and
    after all characters/props (used by the timed overlay layer).
    """
    fb = FrameBuffer(width, height)
    fb.fill_bg(bg, int(world.ground_y))
    put = fb.put
    if under:
        under(fb)

    # sync attached bodies to hang points
    held = held or {}
    for obj_name, ch_name in held.items():
        if obj_name in world.bodies:
            ch = next((c for c in characters if c.name == ch_name), None)
            if ch:
                body = world.bodies[obj_name]
                hx, hy = resolve_hang(ch, body.hang)
                body.x, body.y = hx, hy
                body.attached_to = ch_name

    # sort by y for crude depth
    chars = sorted(characters, key=lambda c: c.y)
    for ch in chars:  # contact shadows first, so they never cover a neighbour's feet
        if ch.visible:
            draw_shadow(put, fb.get, ch, world.ground_y)
    for ch in chars:
        draw_character(put, ch)
        if ch.visible and ch.held_item and ch.held_item in world.bodies:
            body = world.bodies[ch.held_item]
            hx, hy = resolve_hang(ch, body.hang)
            draw_prop(put, body.kind, hx, hy, r=int(body.w / 2), w=int(body.w), h=int(body.h), color=body.color)

    for body in world.bodies.values():
        draw_body(put, body)

    if over:
        over(fb)
    return fb


def export_frames(
    frames: Iterable[Image.Image],
    output: str | Path,
    fps: int = 60,
    fmt: str | None = None,
) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frames = list(frames)
    if not frames:
        raise ValueError("No frames to export")
    fmt = (fmt or output.suffix.lstrip(".")).lower()
    if fmt == "gif":
        frames[0].save(
            output,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / fps),
            loop=0,
            optimize=False,
        )
        return output

    # mp4 via ffmpeg (preferred) or gif fallback
    if fmt not in ("mp4", "mov", "webm"):
        fmt = "mp4"
        output = output.with_suffix(".mp4")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        gif_path = output.with_suffix(".gif")
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / fps),
            loop=0,
        )
        return gif_path

    with tempfile.TemporaryDirectory(prefix="animasis_") as td:
        td_path = Path(td)
        for i, im in enumerate(frames):
            im.save(td_path / f"frame_{i:05d}.png")
        cmd = [
            ffmpeg,
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(td_path / "frame_%05d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "20",
            str(output),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    return output


def stream_mp4(frames: Iterable[Image.Image], output: str | Path, fps: int = 60) -> Path:
    """Encode frames as they are produced (rawvideo -> ffmpeg stdin); same H.264 settings as export_frames."""
    output = Path(output)
    if output.suffix.lower() not in (".mp4", ".mov", ".webm"):
        output = output.with_suffix(".mp4")
    output.parent.mkdir(parents=True, exist_ok=True)
    it = iter(frames)
    first = next(it, None)
    if first is None:
        raise ValueError("No frames to export")
    w, h = first.size
    cmd = [shutil.which("ffmpeg") or "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{w}x{h}", "-framerate", str(fps), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "20", str(output)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        proc.stdin.write(first.convert("RGB").tobytes())
        for im in it:
            proc.stdin.write(im.convert("RGB").tobytes())
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg exited with {code}")
    return output


stream_mp4.available = lambda: shutil.which("ffmpeg") is not None  # type: ignore[attr-defined]
