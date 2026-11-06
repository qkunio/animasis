"""Tang-dynasty kit: 18 backgrounds, horse/camp/arrow overlays, front tables, futou/helmet hats."""

from __future__ import annotations

from animasis import palette as pal
from animasis.overlay import draw_overlays, overlay_from_dict
from animasis.render import FrameBuffer
from animasis.tang import BG, TANG_KINDS


def _draw(items, t=1.0, layer="back"):
    fb = FrameBuffer(320, 180)
    draw_overlays(fb.put, [overlay_from_dict(d) for d in items], t, layer, width=320, height=180,
                  ground_y=150, characters={})
    return [c for row in fb.buf for c in row]


def test_all_tang_backgrounds_stay_on_palette():
    assert len(BG) >= 18
    for name in BG:
        fb = FrameBuffer(320, 180)
        fb.fill_bg(name, 150)
        flat = [c for row in fb.buf for c in row]
        assert len(set(flat)) >= 3, name
        assert all(0 <= c < len(pal.PALETTE) for c in flat), name


def test_every_tang_overlay_draws():
    items = [
        {"kind": "horse", "x": 80, "y": 150, "scale": 1.5, "rider": True},
        {"kind": "camel", "x": 120, "y": 150, "scale": 1.0},
        {"kind": "tent", "x": 220, "y": 150, "w": 50, "h": 36, "lit": True},
        {"kind": "campfire", "x": 40, "y": 150, "scale": 1.2},
        {"kind": "arrow", "t": 0, "x0": 300, "y0": 60, "x1": 120, "y1": 120, "n": 5},
        {"kind": "dust", "x": 140, "y": 145, "w": 90, "h": 12, "n": 24},
        {"kind": "army", "x0": 240, "y": 150, "n": 6, "facing": -1},
    ]
    assert {d["kind"] for d in items} == TANG_KINDS
    for d in items:
        flat = _draw([d], t=0.25)
        assert sum(c != 0 for c in flat) > 15, d["kind"]
        assert all(0 <= c < len(pal.PALETTE) for c in flat)


def test_front_table_and_desk():
    for kind in ("war_table", "desk"):
        flat = _draw([{"kind": kind, "x": 160, "y": 150, "w": 110, "h": 12}], layer="world_front")
        assert sum(c != 0 for c in flat) > 20, kind


def test_arrow_vanishes_after_impact():
    arrow = {"kind": "arrow", "t": 0, "x0": 300, "y0": 60, "x1": 120, "y1": 120, "n": 5, "dur": 0.3}
    assert sum(c != 0 for c in _draw([arrow], t=0.2)) > 0
    assert sum(c != 0 for c in _draw([arrow], t=1.0)) == 0


def test_hat_styles_draw():
    from animasis.skeleton import Character
    from animasis.sprite import draw_sprite
    for style in ("futou", "helmet"):
        ch = Character.create(name=style, x=100, hat=3 if style == "helmet" else 1, hat_style=style)
        canvas = draw_sprite(ch)
        assert canvas.color
