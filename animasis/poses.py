"""Pose library with smooth blending.

Angle conventions (see ``skeleton.py``): limbs are measured from straight down,
positive = forward; ``lower_*`` are relative to the parent (elbows bend
forward = positive, knees bend backward = negative).  ``*_r`` is the near limb.
Feet are re-grounded after every solve, so poses never float or sink.
"""

from __future__ import annotations

import math
from typing import Iterable

from .skeleton import REST_POSE, Skeleton

Deg = math.radians


def _pose(**kwargs: float) -> dict[str, float]:
    base = dict(REST_POSE)
    base.update({k: Deg(v) for k, v in kwargs.items()})
    return base


POSES: dict[str, dict[str, float]] = {
    "idle": _pose(),
    "idle_breathe": _pose(torso=-1.5, head=2, upper_arm_r=10, lower_arm_r=30,
                          upper_arm_l=-9, lower_arm_l=28),
    # --- walk: contact / passing / contact / passing (arms counter-swing on an arc)
    "walk_a": _pose(
        torso=5, head=-3,
        upper_leg_r=28, lower_leg_r=-6, foot_r=-12,
        upper_leg_l=-24, lower_leg_l=-14, foot_l=18,
        upper_arm_r=-48, lower_arm_r=30, hand_r=10,
        upper_arm_l=34, lower_arm_l=50, hand_l=12,
    ),
    "walk_pass_a": _pose(
        torso=3, head=-1,
        upper_leg_r=-2, lower_leg_r=0, foot_r=0,
        upper_leg_l=20, lower_leg_l=-58, foot_l=10,
        upper_arm_r=-14, lower_arm_r=46, hand_r=8,
        upper_arm_l=10, lower_arm_l=70, hand_l=8,
    ),
    "walk_b": _pose(
        torso=5, head=-3,
        upper_leg_r=-24, lower_leg_r=-14, foot_r=18,
        upper_leg_l=28, lower_leg_l=-6, foot_l=-12,
        upper_arm_r=34, lower_arm_r=50, hand_r=12,
        upper_arm_l=-48, lower_arm_l=30, hand_l=10,
    ),
    "walk_pass_b": _pose(
        torso=3, head=-1,
        upper_leg_r=20, lower_leg_r=-58, foot_r=10,
        upper_leg_l=-2, lower_leg_l=0, foot_l=0,
        upper_arm_r=10, lower_arm_r=70, hand_r=8,
        upper_arm_l=-14, lower_arm_l=46, hand_l=8,
    ),
    # --- jump family
    "crouch": _pose(
        torso=18, head=-12,
        upper_leg_r=62, lower_leg_r=-100, foot_r=0,
        upper_leg_l=48, lower_leg_l=-92, foot_l=0,
        upper_arm_r=-38, lower_arm_r=20,
        upper_arm_l=-46, lower_arm_l=20,
    ),
    "jump": _pose(
        torso=-4, head=4,
        upper_leg_r=55, lower_leg_r=-80, foot_r=25,
        upper_leg_l=10, lower_leg_l=-55, foot_l=35,
        upper_arm_r=118, lower_arm_r=25,
        upper_arm_l=140, lower_arm_l=20,
    ),
    "land": _pose(
        torso=14, head=-8,
        upper_leg_r=45, lower_leg_r=-75, foot_r=0,
        upper_leg_l=30, lower_leg_l=-68, foot_l=0,
        upper_arm_r=55, lower_arm_r=25,
        upper_arm_l=-50, lower_arm_l=25,
    ),
    # --- greetings / interaction
    # elbow out in front at shoulder height, forearm swings on an arc above it
    "wave": _pose(
        torso=-3, head=5,
        upper_arm_r=92, lower_arm_r=64, hand_r=10,
        upper_arm_l=-12, lower_arm_l=16,
    ),
    "wave_b": _pose(
        torso=-2, head=3,
        upper_arm_r=100, lower_arm_r=30, hand_r=-6,
        upper_arm_l=-10, lower_arm_l=14,
    ),
    "pickup": _pose(
        torso=32, head=-18,
        upper_leg_r=58, lower_leg_r=-88,
        upper_leg_l=30, lower_leg_l=-80,
        upper_arm_r=18, lower_arm_r=12,
        upper_arm_l=-15, lower_arm_l=20,
    ),
    "reach": _pose(
        torso=6, head=-6,
        upper_arm_r=100, lower_arm_r=-8,
    ),
    "give": _pose(
        torso=6, head=-4,
        upper_arm_r=60, lower_arm_r=32,
        upper_leg_r=12, lower_leg_r=-4,
        upper_leg_l=-8, lower_leg_l=-4,
    ),
    "receive": _pose(
        torso=4, head=4,
        upper_arm_r=58, lower_arm_r=34,
        upper_arm_l=52, lower_arm_l=36,
    ),
    # 作揖: lean forward, both hands clasped in front of the chest
    "bow": _pose(
        torso=22, head=6,
        upper_arm_r=34, lower_arm_r=62, hand_r=10,
        upper_arm_l=28, lower_arm_l=66, hand_l=10,
        upper_leg_r=-6, upper_leg_l=-6,
    ),
    # hand raised to knock on a door
    "knock": _pose(
        torso=2, head=2,
        upper_arm_r=70, lower_arm_r=70, hand_r=20,
    ),
    "phone": _pose(          # looking down at a phone held at chest height
        head=10,
        upper_arm_r=12, lower_arm_r=118, hand_r=-10,
    ),
    "hold": _pose(
        upper_arm_r=20, lower_arm_r=70,
    ),
}


CYCLES: dict[str, list[str]] = {
    "idle": ["idle", "idle_breathe"],
    "walk": ["walk_a", "walk_pass_a", "walk_b", "walk_pass_b"],
    "wave": ["wave", "wave_b"],
    "jump": ["crouch", "jump", "land", "idle"],
    "pickup": ["idle", "pickup", "idle"],
}


def get_pose(name: str) -> dict[str, float]:
    if name not in POSES:
        raise KeyError(f"Unknown pose '{name}'. Available: {sorted(POSES)}")
    return dict(POSES[name])


def apply_pose(skeleton: Skeleton, name: str, blend: float = 1.0) -> None:
    pose = get_pose(name)
    if blend >= 0.999:
        skeleton.set_pose(pose)
    else:
        skeleton.blend_pose(pose, blend)


def _ease(t: float) -> float:
    """Smoothstep — keyframes hold slightly, giving arcs instead of linear jerks."""
    return t * t * (3 - 2 * t)


def sample_cycle(cycle: str, t: float) -> dict[str, float]:
    """t in [0,1) over one cycle; returns blended pose dict."""
    names = CYCLES.get(cycle, [cycle])
    n = len(names)
    if n == 1:
        return get_pose(names[0])
    t = t % 1.0
    idx = t * n
    i0 = int(idx) % n
    i1 = (i0 + 1) % n
    frac = _ease(idx - int(idx))
    a = get_pose(names[i0])
    b = get_pose(names[i1])
    out = {}
    for k in a:
        av, bv = a[k], b[k]
        d = (bv - av + math.pi) % (2 * math.pi) - math.pi
        out[k] = av + d * frac
    return out


def list_poses() -> Iterable[str]:
    return sorted(POSES.keys())
