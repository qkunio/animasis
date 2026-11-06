"""Petroleum explainer kit: oilfield/shelf backgrounds, pumpjack/column/molecule/cutbar overlays."""

from __future__ import annotations

from pathlib import Path

from animasis import palette as pal
from animasis.overlay import draw_overlays, overlay_from_dict
from animasis.petro import PETRO_KINDS
from animasis.render import FrameBuffer
from animasis.scene import load_scene

ROOT = Path(__file__).resolve().parents[1]


def _draw(items, t=1.0, layer="back", **kw):
    fb = FrameBuffer(320, 180)
    draw_overlays(fb.put, [overlay_from_dict(d) for d in items], t, layer, width=320, height=180,
                  ground_y=150, characters={}, **kw)
    return [c for row in fb.buf for c in row]


def test_backgrounds():
    for name in ("oilfield", "shelf"):
        fb = FrameBuffer(320, 180)
        fb.fill_bg(name, 150)
        flat = [c for row in fb.buf for c in row]
        assert len(set(flat)) >= 3 and all(0 <= c < len(pal.PALETTE) for c in flat)


def test_every_petro_kind_draws_on_palette():
    items = [
        {"kind": "pumpjack", "x": 240, "y": 150, "scale": 1.5},
        {"kind": "barrel", "x": 70, "y": 150, "scale": 1.5},
        {"kind": "droplet", "x": 70, "y": 90, "r": 24},
        {"kind": "molecule", "x": 160, "y": 60, "n": 7},
        {"kind": "molecule", "x": 200, "y": 110, "style": "ring"},
        {"kind": "column", "t": 0, "x": 100, "y": 150, "w": 42, "h": 112,
         "cuts": [{"top": True, "text": "石油气", "t": 0},
                  {"at": 0.5, "text": "柴油", "t": 0},
                  {"bottom": True, "text": "沥青", "t": 0}]},
        {"kind": "cutbar", "t": 0, "x": 10, "y": 80, "w": 200, "h": 20,
         "segments": [{"label": "汽油", "pct": 46, "color": 30},
                      {"label": "柴油", "pct": 54, "color": 6}]},
        {"kind": "product", "x": 280, "y": 80, "name": "bottle", "label": "塑料瓶"},
        {"kind": "kinetic", "t": 0, "x": 160, "y": 80, "text": "一桶石油", "size": 12},
        {"kind": "splash", "t": 0, "x": 160, "y": 120, "n": 12},
    ]
    assert {d["kind"] for d in items} == PETRO_KINDS
    for d in items:
        flat = _draw([d], t=0.3)
        assert sum(c != 0 for c in flat) > 15, d["kind"]
        assert all(0 <= c < len(pal.PALETTE) for c in flat)


def test_cutbar_grows_in_segments():
    bar = {"kind": "cutbar", "t": 0, "x": 10, "y": 80, "w": 200, "h": 20,
           "segments": [{"label": "汽油", "pct": 46, "color": 30},
                        {"label": "柴油", "pct": 54, "color": 6}]}
    early = _draw([bar], t=0.05).count(30)
    late = _draw([bar], t=3.0).count(30)
    assert late > early


def test_petroleum_scene_loads_with_camera_and_narration():
    sc = load_scene(ROOT / "demos" / "petroleum.yaml")
    assert 85 <= sc.duration <= 95
    assert len(sc.camera.keys) >= 30
    kinds = {o.kind for o in sc.overlays}
    assert {"pumpjack", "barrel", "droplet", "molecule", "column", "cutbar", "product"} <= kinds
    from animasis.narrate import load_narration
    nar = load_narration(ROOT / "demos" / "petroleum.yaml")
    assert nar["voice"] == "zh-CN-YunjianNeural" and len(nar["lines"]) == 13
