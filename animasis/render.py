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


BG_DRAWERS = {
    "indoor": draw_bg_indoor,
    "outdoor": draw_bg_outdoor,
    "room": draw_bg_room,
    "market": draw_bg_market,
}


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
        if ch.held_item and ch.held_item in world.bodies:
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
    fps: int = 12,
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
