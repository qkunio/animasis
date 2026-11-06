"""GNSS explainer kit: space/blueprint backgrounds, planet/orbit/satellite/range/ring/pin/phone/glyph overlays."""

from __future__ import annotations

from pathlib import Path

from animasis import palette as pal
from animasis.camera import make_resolver
from animasis.overlay import _XF, draw_overlays, overlay_from_dict
from animasis.render import FrameBuffer
from animasis.scene import load_scene
from animasis.space import SPACE_KINDS, sat_pos

ROOT = Path(__file__).resolve().parents[1]


def _draw(items, t=1.0, layer="back", **kw):
    fb = FrameBuffer(320, 180)
    draw_overlays(fb.put, [overlay_from_dict(d) for d in items], t, layer, width=320, height=180,
                  ground_y=150, characters={}, **kw)
    return [c for row in fb.buf for c in row]


def test_backgrounds():
    for name in ("space", "blueprint"):
        fb = FrameBuffer(320, 180)
        fb.fill_bg(name, 150)
        flat = [c for row in fb.buf for c in row]
        assert len(set(flat)) >= 2 and all(0 <= c < len(pal.PALETTE) for c in flat)


def test_every_space_kind_draws_on_palette():
    items = [
        {"kind": "planet", "x": 160, "y": 90, "r": 30},
        {"kind": "orbit", "orbit": [160, 90, 60, 20]},
        {"kind": "satellite", "x": 40, "y": 30, "scale": 2, "signal": True},
        {"kind": "range", "t": 0, "x0": 10, "y0": 10, "x1": 100, "y1": 120, "pulse": 40},
        {"kind": "ring", "t": 0, "x": 200, "y": 60, "r": 30, "fuzz": 3},
        {"kind": "pin", "t": 0, "x": 250, "y": 140},
        {"kind": "phone", "t": 0, "x": 280, "y": 60, "w": 30, "h": 50, "lock": 0.5, "sats": 4},
    ] + [{"kind": "glyph", "name": n, "x": 30 + i * 40, "y": 170} for i, n in
         enumerate(("car", "scooter", "bike", "tripod", "clock", "plane", "ship"))]
    assert {d["kind"] for d in items} == SPACE_KINDS
    for d in items:
        flat = _draw([d])
        assert sum(c != 0 for c in flat) > 15, d["kind"]
        assert all(0 <= c < len(pal.PALETTE) for c in flat)


def test_satellite_orbit_and_occlusion():
    o = overlay_from_dict({"kind": "satellite", "orbit": [160, 90, 100, 30], "period": 8, "phase": 0,
                           "occlude": [160, 90, 40]})
    x, y, behind = sat_pos(o, 0.0)
    assert (round(x), round(y), behind) == (260, 90, False)
    x, y, behind = sat_pos(o, 6.0)  # 3/4 turn -> top of the ellipse = far side
    assert behind and round(x) == 160 and round(y) == 60
    hidden = [{"kind": "satellite", "orbit": [160, 90, 100, 30], "period": 8, "phase": 0, "occlude": [160, 90, 40]}]
    assert sum(c != 0 for c in _draw(hidden, t=6.0)) == 0  # behind the planet disk
    assert sum(c != 0 for c in _draw(hidden, t=0.0)) > 0
    # camera can track it
    res = make_resolver({}, [overlay_from_dict({"kind": "satellite", "id": "s", "orbit": [160, 90, 100, 30],
                                                 "period": 8})], t=2.0)
    assert [round(v) for v in res("s")] == [160, 120]


def test_ring_grows_and_sharpens():
    base = {"kind": "ring", "t": 0, "x": 160, "y": 90, "r": 40, "grow": 2.0}
    half, full = _draw([base], t=1.0), _draw([base], t=2.5)
    assert 0 < sum(c != 0 for c in half) < sum(c != 0 for c in full)
    fz = {"kind": "ring", "t": 0, "x": 160, "y": 90, "r": 40, "grow": 0, "fuzz": 4, "sharpen": [1, 1]}
    assert sum(c != 0 for c in _draw([fz], t=0.5)) > sum(c != 0 for c in _draw([fz], t=2.5))


def test_counting_text_and_offscreen_world_labels():
    d = {"kind": "text", "t": 0, "x": 160, "y": 80, "fmt": "{v:.0f}", "from": 0, "to": 100, "count": 1}
    assert _draw([d], t=0.0, layer="front") != _draw([d], t=2.0, layer="front")
    tag = {"kind": "tag", "t": 0, "x": 300, "y": 20, "space": "world", "text": "远处"}
    shown = _draw([tag], layer="screen", to_screen=lambda x, y: (x, y))
    hidden = _draw([tag], layer="screen", to_screen=lambda x, y: (x + 400, y))
    assert any(shown) and not any(hidden)
    assert _XF["f"] is None  # screen pass restores state


def test_gnss_scene_loads_with_camera_and_narration():
    sc = load_scene(ROOT / "demos" / "gnss_intro.yaml")
    assert 45 <= sc.duration <= 90
    assert len(sc.camera.keys) >= 30 and any(k.move for k in sc.camera.keys)
    kinds = {o.kind for o in sc.overlays}
    assert {"planet", "satellite", "ring", "range", "phone", "pin"} <= kinds
    from animasis.narrate import load_narration
    nar = load_narration(ROOT / "demos" / "gnss_intro.yaml")
    assert nar["voice"] == "zh-CN-YunjianNeural" and len(nar["lines"]) == 11
