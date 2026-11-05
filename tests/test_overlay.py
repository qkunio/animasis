"""Overlay layer: pixel text, story props, title cards in the scene DSL."""

from __future__ import annotations

from pathlib import Path

from animasis import palette as pal
from animasis.overlay import draw_overlays, overlay_from_dict, text_mask
from animasis.render import FrameBuffer
from animasis.scene import load_scene

ROOT = Path(__file__).resolve().parents[1]


def test_text_mask_has_pixels():
    w, h, pts = text_mask("机会成本 ¥10", 12)
    assert w > 20 and len(pts) > 30


def test_card_covers_frame_and_stays_on_palette():
    fb = FrameBuffer(320, 180)
    o = overlay_from_dict({"kind": "card", "t": 0, "until": 2, "bg": 25,
                           "items": ["标题", {"icons": ["icecream", "VS", "console"]}]})
    draw_overlays(fb.put, [o], 1.0, "front", width=320, height=180, ground_y=150, characters={})
    flat = [c for row in fb.buf for c in row]
    assert flat.count(25) > 320 * 180 * 0.8
    assert all(0 <= c < len(pal.PALETTE) for c in flat)
    fb2 = FrameBuffer(320, 180)
    draw_overlays(fb2.put, [o], 2.5, "front", width=320, height=180, ground_y=150, characters={})
    assert all(c == 0 for row in fb2.buf for c in row)  # inactive after `until`


def test_econ_scene_loads():
    sc = load_scene(ROOT / "demos" / "econ_opportunity_cost.yaml")
    assert sc.overlays and {"xiaoming", "vendor", "xiaohong"} <= set(sc.characters)
    assert 20 <= sc.duration <= 40
