"""Camera: YAML parsing, shot presets, cuts vs moves, fades, reverse angles, rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

from animasis.camera import SHOTS, Camera, CameraError, make_resolver, parse_key
from animasis.scene import iter_frames, load_scene, scene_from_dict

ROOT = Path(__file__).resolve().parents[1]


def test_parse_key_presets_and_overrides():
    k = parse_key({"t": 2, "shot": "close", "target": "liubei", "offset": [4, -6]})
    assert k.zoom == SHOTS["close"] and k.target == "liubei" and k.offset == (4.0, -6.0)
    assert k.move == 0 and k.transition == "cut" and not k.flip
    k = parse_key({"t": 1, "shot": "medium", "zoom": 2.2, "move": 1.5, "ease": "out",
                   "transition": "fade", "fade": 0.4, "flip": True, "name": "反打"})
    assert k.zoom == 2.2 and k.move == 1.5 and k.ease == "out"
    assert k.transition == "fade" and k.fade == 0.4 and k.flip and k.name == "反打"
    assert parse_key({"t": 0, "shot": "近景"}).zoom == SHOTS["close"]
    assert parse_key({"t": 3, "until": 5}).move == 2.0
    assert parse_key({"t": 0, "offset": {"x": 3, "y": 1}}).offset == (3.0, 1.0)


@pytest.mark.parametrize("bad", [
    {"shot": "wide"},                      # no t
    {"t": 0, "shot": "panorama"},          # unknown preset
    {"t": 0, "zoom": 0.5},                 # wider than the stage
    {"t": 0, "offset": [1, 2, 3]},
    {"t": 0, "ease": "bounce"},
    {"t": 0, "transition": "wipe"},
    "not a mapping",
])
def test_parse_key_rejects_bad_input(bad):
    with pytest.raises(CameraError):
        parse_key(bad)


def test_cut_move_clamp_and_fade():
    cam = Camera.from_yaml([
        {"t": 0, "shot": "wide"},
        {"t": 2, "zoom": 2, "target": [100, 90]},                       # hard cut
        {"t": 4, "zoom": 2, "target": [200, 90], "move": 2, "ease": "linear"},  # pan
        {"t": 7, "zoom": 4, "target": [0, 0], "transition": "fade", "fade": 1.0},  # clamped
    ])
    assert [k.t for k in cam.keys] == [0, 2, 4, 7]
    s = cam.state(1.0)
    assert (s.cx, s.cy, s.zoom) == (160, 90, 1.0)
    s = cam.state(2.0)
    assert (s.cx, s.zoom) == (100, 2.0)
    assert cam.state(5.0).cx == pytest.approx(150)  # halfway through the pan
    assert cam.state(6.5).cx == pytest.approx(200)
    s = cam.state(7.6)
    assert s.cx == pytest.approx(40) and s.cy == pytest.approx(22.5)  # view kept inside stage
    assert cam.state(7.0).brightness == pytest.approx(0.0)
    assert cam.state(6.75).brightness == pytest.approx(0.5)
    assert cam.state(3.0).brightness == 1.0


def test_unsorted_keys_and_dict_form():
    cam = Camera.from_yaml({"keys": [{"t": 5, "shot": "close"}, {"t": 0, "shot": "wide"}]})
    assert [k.t for k in cam.keys] == [0, 5]
    with pytest.raises(CameraError):
        Camera.from_yaml("wide")


def test_flip_and_to_screen():
    cam = Camera.from_yaml([{"t": 0, "zoom": 2, "target": [160, 90]},
                            {"t": 1, "zoom": 2, "target": [160, 90], "flip": True}])
    f = cam.to_screen(cam.state(0.5))
    assert f(160, 90) == (160, 90) and f(170, 90) == (180, 90)
    s = cam.state(1.5)
    assert s.flip and cam.to_screen(s)(170, 90) == (140, 90)
    assert cam.view_box(s) == (80, 45, 240, 135)


def test_resolver_targets():
    class C:
        def __init__(self, x):
            self.x, self.y, self.scale = x, 150, 1.0
    res = make_resolver({"a": C(100), "b": C(200)}, ground_y=150)
    assert res("a") == (100, 130)
    assert res(["a", "b"]) == (150, 130)
    assert res([10, 20]) == (10, 20) and res({"x": 5, "y": 6}) == (5, 6)
    with pytest.raises(CameraError):
        res("nobody")


def test_scene_rejects_unknown_target():
    with pytest.raises(CameraError):
        scene_from_dict({"characters": [{"name": "a"}], "camera": [{"t": 0, "target": "ghost"}]})


def test_sangu_has_real_shot_list():
    sc = load_scene(ROOT / "demos" / "sangu_maolu.yaml")
    keys = sc.camera.keys
    assert len(keys) >= 20
    zooms = {k.zoom for k in keys}
    assert min(zooms) == 1.0 and max(zooms) >= 2.8              # wide ... close-up
    assert any(k.flip for k in keys)                            # reverse angle
    assert any(k.move > 0 for k in keys)                        # pans / pushes
    assert any(k.transition == "fade" for k in keys)            # dips to black
    assert sum(1 for k in keys if k.move == 0) >= 15            # plenty of hard cuts
    rows = sc.camera.shot_list(sc.duration)
    assert rows[-1]["end"] == sc.duration and all(r["name"] for r in rows)


def test_camera_render_crops_and_keeps_screen_text():
    sc = scene_from_dict({
        "duration": 1.0, "fps": 4, "scale": 1, "ground_y": 150,
        "characters": [{"name": "a", "x": 100}],
        "overlays": [{"kind": "caption", "t": 0, "until": 1, "text": "字幕"}],
        "camera": [{"t": 0, "shot": "wide"}, {"t": 0.5, "shot": "close", "target": "a"}],
    })
    frames = list(iter_frames(sc))
    assert len(frames) == 4 and all(img.size == (320, 180) for _, img in frames)
    wide, close = frames[0][1], frames[3][1]
    assert wide.tobytes() != close.tobytes()
    # caption bar is screen-space: identical bottom strip in both shots
    assert wide.crop((6, 160, 314, 176)).tobytes() == close.crop((6, 160, 314, 176)).tobytes()

def test_tags_track_anchor_under_camera_no_edge_clamp():
    """World tags must follow to_screen (not stick to the frame edge); HUD tags keep y.

    Regression for "镜头扭转/横摇时文字标签异动": an old clamp shoved near-edge world
    tags onto the border and pushed corner HUD tags (y=6) down to y=26.
    """
    from animasis.overlay import draw_overlays, text_width
    from animasis.render import FrameBuffer, _CLEAR

    sc = scene_from_dict({
        "duration": 0.5, "fps": 10, "scale": 1, "ground_y": 150,
        "characters": [{"name": "a", "x": 100}],
        "overlays": [
            {"kind": "tag", "t": 0, "until": 1, "x": 26, "y": 6, "text": "一顾",
             "bg": 5, "border": 0, "align": "left"},
            {"kind": "tag", "t": 0, "until": 1, "x": 48, "y": 84, "space": "world",
             "text": "GPS · 美国", "bg": 9},
        ],
        # zoomed so world (48,84) maps near the left edge (sx≈17) — old clamp moved it to 38
        "camera": [{"t": 0, "zoom": 2.4, "target": [107.58, 90]}],
    })
    st = sc.camera.state(0.0)
    f = sc.camera.to_screen(st)
    screen = FrameBuffer(320, 180)
    screen.buf = [[_CLEAR] * 320 for _ in range(180)]
    draw_overlays(screen.put, sc.overlays, 0.0, "screen", to_screen=f, flip=False,
                  width=320, height=180, ground_y=150, characters=sc.characters)

    def pts(color):
        return [(x, y) for y in range(180) for x in range(320) if screen.buf[y][x] == color]

    hud = pts(5)
    assert hud and min(y for _, y in hud) <= 8  # still at y≈6, not clamped to 26

    raw = f(48, 84)
    w = text_width("GPS · 美国", 12, True)
    x0 = int(round(raw[0] - w / 2)) - 3
    x1 = x0 + w + 6
    world = pts(9)
    assert world, "world tag near the edge should still draw (clipped)"
    assert min(x for x, _ in world) == 0  # clipped against the left edge
    assert max(x for x, _ in world) <= x1 + 1
    assert max(x for x, _ in world) < 60  # clamped placement would extend to ~73
