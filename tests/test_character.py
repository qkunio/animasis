"""Regression tests for character rig + sprite rasterisation.

Guards against the old failure modes: limbs drawn detached from the body,
shoes floating above / sinking below the ground line, and presets that
silently collapse to the same look.
"""
import pytest

from animasis.poses import POSES, apply_pose
from animasis.skeleton import PRESETS, Character
from animasis.sprite import draw_sprite

GROUND = 100


def _render(preset, pose, facing):
    ch = Character.create(preset, x=50, y=GROUND, preset=preset, facing=facing)
    apply_pose(ch.skeleton, pose)
    return dict(draw_sprite(ch).color)


def _components(pts):
    pts = set(pts)
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
    return comps


CASES = [(pr, po, f) for pr in PRESETS for po in POSES for f in (1, -1)]


@pytest.mark.parametrize("preset,pose,facing", CASES)
def test_sprite_is_one_connected_piece(preset, pose, facing):
    px = _render(preset, pose, facing)
    assert px, "nothing drawn"
    assert _components(px) == 1, f"{preset}/{pose}/{facing}: detached pixels"


@pytest.mark.parametrize("preset,pose,facing", CASES)
def test_feet_touch_ground(preset, pose, facing):
    px = _render(preset, pose, facing)
    lowest = max(y for _, y in px)
    # outline row sits exactly on the last row above the ground line
    assert lowest == GROUND - 1 or lowest == GROUND, (preset, pose, facing, lowest)


@pytest.mark.parametrize("preset", list(PRESETS))
def test_proportions(preset):
    px = _render(preset, "idle", 1)
    ys = [y for _, y in px]
    h = max(ys) - min(ys) + 1
    assert 22 <= h <= 36, h  # chibi but readable
    ch = Character.create(preset, x=50, y=GROUND, preset=preset)
    j = ch.rig().points
    head_h = 2 * ch.skeleton.props["head_ry"]
    leg_h = j["hipj_r"][1] - min(j["ankle_r"][1], j["ankle_l"][1])
    assert abs(leg_h) / head_h < 1.6


def test_presets_look_different():
    sigs = {pr: frozenset(_render(pr, "idle", 1).items()) for pr in PRESETS}
    assert len(set(sigs.values())) == len(PRESETS)
    assert len(PRESETS) >= 3


def test_facing_mirrors_silhouette():
    a = _render("hero", "walk_a", 1)
    b = _render("hero", "walk_a", -1)
    wa = max(x for x, _ in a) - min(x for x, _ in a)
    wb = max(x for x, _ in b) - min(x for x, _ in b)
    assert abs(wa - wb) <= 1
