"""Flight overlays: procedural aircraft and airfoil flow."""

import pytest

from animasis import palette as pal
from animasis.overlay import draw_overlays, overlay_from_dict
from animasis.render import FrameBuffer


def _draw(item, t):
    fb = FrameBuffer(320, 180)
    overlay = overlay_from_dict(item)
    draw_overlays(fb.put, [overlay], t, "back", width=320, height=180, ground_y=150, characters={})
    return [c for row in fb.buf for c in row]


@pytest.mark.parametrize("item", [
    {"kind": "flight_plane", "t": 0, "x": 160, "y": 85, "scale": 1.1, "gear": True},
    {"kind": "airfoil", "t": 0, "x": 160, "y": 85, "angle": 8, "wash_arrows": True},
    {"kind": "force", "t": 0, "x": 160, "y": 90, "dir": "up", "length": 40},
])
def test_flight_overlays_draw_on_palette(item):
    flat = _draw(item, 1.0)
    assert sum(c != 0 for c in flat) > 20
    assert all(0 <= c < len(pal.PALETTE) for c in flat)


def test_airfoil_stall_and_plane_motion_change_pixels():
    base = {"kind": "airfoil", "t": 0, "x": 160, "y": 85, "angle": 20}
    assert _draw({**base, "stall": 0}, 2.0) != _draw({**base, "stall": 1}, 2.0)
    plane = {"kind": "flight_plane", "t": 0, "x": 35, "y": 128, "move": [0, 8],
             "x1": 260, "y1": 66, "pitch1": -10}
    assert _draw(plane, 0.0) != _draw(plane, 8.0)
