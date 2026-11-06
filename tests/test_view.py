"""Multi-angle body facing (view / 体位): front, side, three_quarter, back."""
from __future__ import annotations

import pytest

from animasis.builder import SceneBuilder
from animasis.poses import apply_pose
from animasis.scene import scene_from_dict
from animasis.skeleton import VIEWS, Character, normalize_view
from animasis.sprite import draw_sprite

GROUND = 100


@pytest.mark.parametrize(
    "alias,canon",
    [
        ("front", "front"),
        ("正", "front"),
        ("正面", "front"),
        ("正体位", "front"),
        ("side", "side"),
        ("侧", "side"),
        ("3/4", "three_quarter"),
        ("three_quarter", "three_quarter"),
        ("back", "back"),
        ("背", "back"),
        (None, "side"),
        ("", "side"),
    ],
)
def test_normalize_view(alias, canon):
    assert normalize_view(alias) == canon


def test_unknown_view_raises():
    with pytest.raises(KeyError):
        normalize_view("diagonal")


def _pixels(view: str, pose: str = "idle", facing: int = 1):
    ch = Character.create("h", x=50, y=GROUND, preset="hero", view=view, facing=facing)
    apply_pose(ch.skeleton, pose)
    return ch, dict(draw_sprite(ch).color)


@pytest.mark.parametrize("view", list(VIEWS))
def test_front_back_side_connected(view):
    ch, px = _pixels(view, "idle")
    assert px
    assert ch.rig().view == ("side" if view == "side" else view) or ch.view == view
    # one connected component
    pts = set(px)
    seen, comps = set(), 0
    for p in pts:
        if p in seen:
            continue
        comps += 1
        stack = [p]
        seen.add(p)
        while stack:
            x, y = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (x + dx, y + dy)
                    if q in pts and q not in seen:
                        seen.add(q)
                        stack.append(q)
    assert comps == 1, (view, comps)


@pytest.mark.parametrize("view", list(VIEWS))
def test_feet_grounded_all_views(view):
    _, px = _pixels(view, "sit" if view in ("front", "back") else "idle")
    lowest = max(y for _, y in px)
    assert lowest in (GROUND - 1, GROUND), (view, lowest)


def test_front_wider_than_side():
    _, side = _pixels("side", "idle")
    _, front = _pixels("front", "idle")
    ws = max(x for x, _ in side) - min(x for x, _ in side)
    wf = max(x for x, _ in front) - min(x for x, _ in front)
    assert wf >= ws - 1  # front silhouette at least as wide


def test_front_face_is_centered():
    """Front view paints both eyes symmetrically around the head centre."""
    ch, px = _pixels("front", "idle")
    rig = ch.rig()
    hx = int(rig.points["head_c"][0])
    # eye colour index
    from animasis import palette as pal
    eyes = [(x, y) for (x, y), c in px.items() if c == pal.EYE]
    assert eyes, "no eyes drawn on front face"
    left = [x for x, _ in eyes if x < hx]
    right = [x for x, _ in eyes if x > hx]
    assert left and right
    assert abs((hx - max(left)) - (min(right) - hx)) <= 1


def test_back_has_no_face():
    """Back view skips facial features (mouth / blush); occiput hair remains."""
    from animasis import palette as pal
    ch, px = _pixels("back", "idle")
    assert ch.rig().view == "back"
    # mouth + blush are face-only colours; outline shares the eye index so ignore EYE
    face_cols = {pal.MOUTH, pal.BLUSH}
    assert not any(c in face_cols for c in px.values())


def test_yaml_and_builder_view():
    sc = scene_from_dict({
        "name": "v",
        "characters": [{"name": "a", "view": "正体位", "pose": "sit", "x": 80}],
        "timeline": [
            {"t": 0.0, "action": "view", "target": "a", "name": "side"},
        ],
    })
    assert sc.characters["a"].view == "front"
    from animasis.scene import TimelineEvent, _apply_event
    _apply_event(sc, TimelineEvent(0.0, "view", "a", {"name": "side"}))
    assert sc.characters["a"].view == "side"

    b = SceneBuilder("b").character("hero", view="front", pose="sit")
    assert b.scene.characters["hero"].view == "front"


def test_side_walk_still_works():
    """Existing demos rely on side-view walking — keep the silhouette narrow-ish."""
    ch, px = _pixels("side", "walk_a", facing=1)
    assert px
    w = max(x for x, _ in px) - min(x for x, _ in px)
    assert 10 <= w <= 22
