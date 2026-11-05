"""三顾茅庐 demo: cottage backgrounds, hut/fence/weather overlays, show/hide/attach, narration config."""

from __future__ import annotations

from pathlib import Path

from animasis import palette as pal
from animasis.narrate import check_timing, load_narration
from animasis.overlay import draw_overlays, overlay_from_dict
from animasis.render import BG_DRAWERS, FrameBuffer
from animasis.scene import TimelineEvent, _apply_event, load_scene
from animasis.skeleton import Character

ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "demos" / "sangu_maolu.yaml"


def _flat(fb):
    return [c for row in fb.buf for c in row]


def test_cottage_backgrounds_differ_and_stay_on_palette():
    seen = []
    for name in ("cottage", "cottage_snow", "cottage_spring"):
        assert name in BG_DRAWERS
        fb = FrameBuffer(320, 180)
        fb.fill_bg(name, 150)
        flat = _flat(fb)
        assert all(0 <= c < len(pal.PALETTE) for c in flat)
        assert len(set(flat)) >= 4
        seen.append(tuple(flat))
    assert len(set(seen)) == 3


def test_hut_door_opens_and_fence_weather_draw():
    hut = overlay_from_dict({"kind": "hut", "t": 0, "until": 10, "x": 242, "sign": "草庐",
                             "open": [[2, 4]], "snow": True})
    fence = overlay_from_dict({"kind": "fence", "t": 0, "until": 10, "x0": 293, "x1": 320})
    snow = overlay_from_dict({"kind": "snow", "t": 0, "until": 10})
    frames = {}
    for t in (1.0, 3.0):
        fb = FrameBuffer(320, 180)
        draw_overlays(fb.put, [hut, fence], t, "back", width=320, height=180, ground_y=150, characters={})
        frames[t] = _flat(fb)
        assert sum(c != 0 for c in frames[t]) > 2000
    assert frames[1.0] != frames[3.0]  # door open vs closed
    fb = FrameBuffer(320, 180)
    draw_overlays(fb.put, [snow], 5.0, "front", width=320, height=180, ground_y=150, characters={})
    assert sum(c != 0 for c in _flat(fb)) > 20


def test_show_hide_attach_background_actions():
    sc = load_scene(SCENE)
    assert not sc.characters["shutong"].visible
    _apply_event(sc, TimelineEvent(1.0, "show", "shutong"))
    assert sc.characters["shutong"].visible
    _apply_event(sc, TimelineEvent(1.0, "hide", "shutong"))
    assert not sc.characters["shutong"].visible
    _apply_event(sc, TimelineEvent(1.0, "attach", "liubei", {"object": "letter"}))
    assert sc.held["letter"] == "liubei" and sc.characters["liubei"].held_item == "letter"
    _apply_event(sc, TimelineEvent(1.1, "attach", "shutong", {"object": "letter"}))
    assert sc.held["letter"] == "shutong" and sc.characters["liubei"].held_item is None
    _apply_event(sc, TimelineEvent(2.0, "background", None, {"name": "cottage_snow"}))
    assert sc.background == "cottage_snow"


def test_beard_option_passes_through():
    c = Character.create("gy", x=50, y=60, preset="bob", beard="long")
    assert c.look.beard == "long"


def test_narration_block_loads_without_network():
    nar = load_narration(SCENE)
    assert nar["voice"].startswith("zh-CN-")
    assert len(nar["lines"]) >= 8
    ts = [float(l["t"]) for l in nar["lines"]]
    assert ts == sorted(ts) and ts[-1] < nar["duration"]
    fake = [{"t": 0.0, "dur": 2.0}, {"t": 1.0, "dur": 1.0}]
    assert check_timing(fake, 1.5) and not check_timing([{"t": 0.0, "dur": 1.0}], 2.0)
