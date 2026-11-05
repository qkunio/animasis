"""Hierarchical 2D humanoid rig for small (~30px) pixel characters.

Conventions (all angles in radians, stored in ``Skeleton.angles``):

* The rig is authored in *body space* facing right; ``facing=-1`` mirrors it.
* ``torso`` – lean, positive = lean forward.  ``head`` – extra tilt.
* Limb angles are measured from *straight down*; positive swings the limb
  forward (towards ``facing``).  Child angles (``lower_*``, ``hand_*``) are
  relative to their parent, so an elbow of +30° bends the forearm forward and a
  knee of −40° bends the shin backward.
* ``*_r`` limbs are the *near* (front) arm / leg, ``*_l`` the far (back) ones.
* ``foot_*`` – 0 = sole flat, positive = toe pointing down.

``Character.y`` is the ground line under the feet: the rig is solved hip-first
and then shifted vertically so the lowest shoe pixel sits exactly on it.  Feet
therefore always touch the floor (or the jump arc height) whatever the pose.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from . import palette as pal

Vec = tuple[float, float]

BONE_NAMES = [
    "root", "torso", "head",
    "upper_arm_l", "lower_arm_l", "hand_l",
    "upper_arm_r", "lower_arm_r", "hand_r",
    "upper_leg_l", "lower_leg_l", "foot_l",
    "upper_leg_r", "lower_leg_r", "foot_r",
]

_PARENT = {
    "root": None, "torso": "root", "head": "torso",
    "upper_arm_l": "torso", "lower_arm_l": "upper_arm_l", "hand_l": "lower_arm_l",
    "upper_arm_r": "torso", "lower_arm_r": "upper_arm_r", "hand_r": "lower_arm_r",
    "upper_leg_l": "root", "lower_leg_l": "upper_leg_l", "foot_l": "lower_leg_l",
    "upper_leg_r": "root", "lower_leg_r": "upper_leg_r", "foot_r": "lower_leg_r",
}

D = math.radians

REST_POSE: dict[str, float] = {
    "root": 0.0,
    "torso": 0.0,
    "head": 0.0,
    # relaxed arms: slight elbow bend, forearm drifts forward (never a straight stick)
    "upper_arm_r": D(6), "lower_arm_r": D(26), "hand_r": D(8),
    "upper_arm_l": D(-6), "lower_arm_l": D(24), "hand_l": D(8),
    "upper_leg_r": D(5), "lower_leg_r": D(-3), "foot_r": 0.0,
    "upper_leg_l": D(-5), "lower_leg_l": D(-2), "foot_l": 0.0,
}

# Proportions in logical pixels at scale 1.  Head ≈ torso ≈ legs (≈ 10px each).
BODY_TYPES: dict[str, dict[str, float]] = {
    "default": dict(
        torso_len=8.0, hw_top=4.0, hw_bot=3.6,
        head_rx=5.5, head_ry=5.3,
        upper_arm=4.0, lower_arm=3.5, hand=1.2, arm_r=1.1,
        upper_leg=4.5, lower_leg=4.5, leg_r=1.6, hip_dx=2.0, foot_len=2.5,
        shoulder_drop=1.3, shoulder_r=1.45,
    ),
    "slim": dict(
        torso_len=8.0, hw_top=3.5, hw_bot=3.0,
        head_rx=5.5, head_ry=5.3,
        upper_arm=4.0, lower_arm=3.5, hand=1.1, arm_r=1.0,
        upper_leg=5.0, lower_leg=5.0, leg_r=1.5, hip_dx=1.8, foot_len=2.3,
        shoulder_drop=1.3, shoulder_r=1.45,
    ),
    "stocky": dict(
        torso_len=8.0, hw_top=4.6, hw_bot=4.6,
        head_rx=5.5, head_ry=5.3,
        upper_arm=4.0, lower_arm=3.5, hand=1.3, arm_r=1.3,
        upper_leg=4.0, lower_leg=4.0, leg_r=1.7, hip_dx=2.2, foot_len=2.7,
        shoulder_drop=1.3, shoulder_r=1.45,
    ),
}


@dataclass
class Bone:
    name: str
    length: float
    angle: float = 0.0
    parent: str | None = None
    thickness: float = 3.0
    color: int = pal.SKIN


def _rot(v: Vec, a: float) -> Vec:
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def _down(a: float) -> Vec:
    """Unit vector at angle ``a`` from straight down, positive = forward."""
    return (math.sin(a), math.cos(a))


def _add(a: Vec, b: Vec, k: float = 1.0) -> Vec:
    return (a[0] + b[0] * k, a[1] + b[1] * k)


@dataclass
class Rig:
    """Solved world-space rig (screen coords, y down)."""

    points: dict[str, Vec]
    facing: int
    lean: float
    head_tilt: float
    props: dict[str, float]
    foot_angles: dict[str, float]

    def joints(self) -> dict[str, tuple[Vec, Vec]]:
        p = self.points
        return {
            "root": (p["hip"], p["hip"]),
            "torso": (p["hip"], p["neck"]),
            "head": (p["neck"], p["head_top"]),
            "upper_arm_l": (p["shoulder_l"], p["elbow_l"]),
            "lower_arm_l": (p["elbow_l"], p["wrist_l"]),
            "hand_l": (p["wrist_l"], p["hand_l"]),
            "upper_arm_r": (p["shoulder_r"], p["elbow_r"]),
            "lower_arm_r": (p["elbow_r"], p["wrist_r"]),
            "hand_r": (p["wrist_r"], p["hand_r"]),
            "upper_leg_l": (p["hipj_l"], p["knee_l"]),
            "lower_leg_l": (p["knee_l"], p["ankle_l"]),
            "foot_l": (p["heel_l"], p["toe_l"]),
            "upper_leg_r": (p["hipj_r"], p["knee_r"]),
            "lower_leg_r": (p["knee_r"], p["ankle_r"]),
            "foot_r": (p["heel_r"], p["toe_r"]),
        }


@dataclass
class Skeleton:
    bones: dict[str, Bone] = field(default_factory=dict)
    angles: dict[str, float] = field(default_factory=dict)
    scale: float = 1.0
    body: str = "default"

    @classmethod
    def humanoid(
        cls,
        scale: float = 1.0,
        cloth: int = pal.CLOTH_A,
        pants: int = pal.CLOTH_B,
        body: str = "default",
    ) -> "Skeleton":
        pr = BODY_TYPES.get(body, BODY_TYPES["default"])
        lengths = {
            "root": 0, "torso": pr["torso_len"], "head": pr["head_ry"] * 2,
            "upper_arm_l": pr["upper_arm"], "lower_arm_l": pr["lower_arm"], "hand_l": pr["hand"],
            "upper_arm_r": pr["upper_arm"], "lower_arm_r": pr["lower_arm"], "hand_r": pr["hand"],
            "upper_leg_l": pr["upper_leg"], "lower_leg_l": pr["lower_leg"], "foot_l": pr["foot_len"],
            "upper_leg_r": pr["upper_leg"], "lower_leg_r": pr["lower_leg"], "foot_r": pr["foot_len"],
        }
        bones = {}
        for n in BONE_NAMES:
            color = pal.SKIN
            if n == "torso":
                color = cloth
            elif "leg" in n:
                color = pants
            elif n.startswith("foot"):
                color = pal.SHOE
            bones[n] = Bone(name=n, length=float(lengths[n]) * scale, parent=_PARENT[n],
                            thickness=2.0 * scale, color=color)
        return cls(bones=bones, angles=dict(REST_POSE), scale=scale, body=body)

    @property
    def props(self) -> dict[str, float]:
        pr = BODY_TYPES.get(self.body, BODY_TYPES["default"])
        return {k: v * self.scale for k, v in pr.items()}

    def set_pose(self, pose: dict[str, float]) -> None:
        for k, v in pose.items():
            if k in self.angles:
                self.angles[k] = float(v)

    def blend_pose(self, pose: dict[str, float], t: float) -> None:
        t = max(0.0, min(1.0, t))
        for k, target in pose.items():
            if k in self.angles:
                a = self.angles[k]
                d = (target - a + math.pi) % (2 * math.pi) - math.pi
                self.angles[k] = a + d * t

    # ------------------------------------------------------------------ solve
    def solve(self, origin: Vec, facing: int = 1) -> Rig:
        """Solve the rig; ``origin`` = (x, ground line under the feet)."""
        pr = self.props
        A = self.angles
        f = 1 if facing >= 0 else -1
        lean = A.get("torso", 0.0)
        up = (math.sin(lean), -math.cos(lean))
        fwd = (math.cos(lean), math.sin(lean))
        hip: Vec = (0.0, 0.0)
        neck = _add(hip, up, pr["torso_len"])
        head_a = lean + A.get("head", 0.0)
        head_up = (math.sin(head_a), -math.cos(head_a))
        head_c = _add(neck, head_up, pr["head_ry"] - 0.6)
        head_top = _add(head_c, head_up, pr["head_ry"] + 1.0)
        sh_base = _add(hip, up, pr["torso_len"] - pr["shoulder_drop"])
        pts: dict[str, Vec] = {"hip": hip, "neck": neck, "head_c": head_c, "head_top": head_top}
        # shoulder socket sits on the torso's top corner: the arm's outer edge is
        # flush with the torso side, so the deltoid cap reads as one silhouette
        corner = pr["hw_top"] - pr["arm_r"]
        # 3/4 side view: the arm socket sits just in front of the torso centre
        # line (the rounded deltoid caps stay on the torso corners), so the near
        # arm swings out past the chest *and* past the back instead of lying
        # flat on the belly.
        inset = 1.0 * self.scale
        for side, sgn in (("r", 1.0), ("l", -1.0)):
            pts[f"shcap_{side}"] = _add(sh_base, fwd, sgn * corner)
            sh = _add(sh_base, fwd, sgn * inset)
            a1 = lean + A.get(f"upper_arm_{side}", 0.0)
            el = _add(sh, _down(a1), pr["upper_arm"])
            a2 = a1 + A.get(f"lower_arm_{side}", 0.0)
            wr = _add(el, _down(a2), pr["lower_arm"])
            a3 = a2 + A.get(f"hand_{side}", 0.0)
            hd = _add(wr, _down(a3), pr["hand"])
            pts[f"shoulder_{side}"], pts[f"elbow_{side}"] = sh, el
            pts[f"wrist_{side}"], pts[f"hand_{side}"] = wr, hd
        foot_angles: dict[str, float] = {}
        for side, sgn in (("r", 1.0), ("l", -1.0)):
            hj = (hip[0] + sgn * pr["hip_dx"] * 0.5, hip[1])
            a1 = A.get(f"upper_leg_{side}", 0.0)
            kn = _add(hj, _down(a1), pr["upper_leg"])
            a2 = a1 + A.get(f"lower_leg_{side}", 0.0)
            an = _add(kn, _down(a2), pr["lower_leg"])
            fa = A.get(f"foot_{side}", 0.0)
            heel = _add(an, _rot((-0.6 * self.scale, 0.9 * self.scale), fa))
            toe = _add(an, _rot((pr["foot_len"], 0.9 * self.scale), fa))
            pts[f"hipj_{side}"], pts[f"knee_{side}"], pts[f"ankle_{side}"] = hj, kn, an
            pts[f"heel_{side}"], pts[f"toe_{side}"] = heel, toe
            foot_angles[side] = fa
        # ground: the lowest shoe centre-line sits half a pixel above the ground line
        lowest = max(pts["heel_r"][1], pts["toe_r"][1], pts["heel_l"][1], pts["toe_l"][1])
        ox = origin[0]
        # shoes are 2px capsules centred on an integer row boundary Y, covering
        # rows Y-1 and Y; we want the bottom row to be ground-1  =>  Y = ground-1
        gy = round(origin[1]) - 1.0
        shift = gy - lowest
        world = {k: (ox + v[0] * f, v[1] + shift) for k, v in pts.items()}
        return Rig(points=world, facing=f, lean=lean, head_tilt=A.get("head", 0.0),
                   props=pr, foot_angles=foot_angles)

    def world_joints(self, origin: Vec, facing: int = 1) -> dict[str, tuple[Vec, Vec]]:
        return self.solve(origin, facing).joints()

    def attach_point(self, bone_name: str, t: float, origin: Vec, facing: int = 1) -> Vec:
        joints = self.world_joints(origin, facing)
        if bone_name not in joints:
            return origin
        a, b = joints[bone_name]
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ---------------------------------------------------------------- appearance
@dataclass
class Look:
    """Layered appearance: skin / hair / clothes, each shaded with a 3-tone ramp."""

    skin: int = pal.SKIN
    hair: int = pal.HAIR
    hair_style: str = "short"      # short | spiky | long | bob | ponytail | buzz | topknot
    shirt: int = pal.CLOTH_A
    pants: int = pal.CLOTH_B
    shoes: int = pal.SHOE
    sleeves: str = "short"         # short | long
    skirt: bool = False
    belt: int | None = None
    hat: int | None = None
    blush: bool = True
    lashes: bool = False
    beard: str | None = None       # None | short | long  (drawn in the hair colour)


PRESETS: dict[str, dict[str, Any]] = {
    # sturdy adventurer: spiky brown hair, blue tunic, belt, brown trousers
    "hero": dict(hair=14, hair_style="spiky", shirt=10, pants=14, shoes=24, belt=24,
                 sleeves="short", body="default"),
    # girl: long blonde hair, purple dress, navy leggings, red shoes
    "alice": dict(hair=7, hair_style="long", shirt=11, pants=25, shoes=27, skirt=True,
                  sleeves="short", body="slim", lashes=True),
    # big guy: short black hair, red long-sleeve shirt, blue jeans
    "bob": dict(hair=1, hair_style="short", shirt=5, pants=10, shoes=24, sleeves="long",
                body="stocky", skin=12, belt=24),
    # sporty: ginger ponytail, green tee, brown shorts-ish trousers
    "runner": dict(hair=32, hair_style="ponytail", shirt=8, pants=14, shoes=5, sleeves="short",
                   body="slim", lashes=True),
    # bob-cut kid in orange
    "kid": dict(hair=24, hair_style="bob", shirt=6, pants=10, shoes=24, sleeves="short",
                body="default"),
}


@dataclass
class Character:
    name: str
    skeleton: Skeleton
    x: float = 0.0
    y: float = 0.0
    facing: int = 1  # 1 right, -1 left
    expression: str = "neutral"
    hair_color: int = pal.HAIR
    held_item: str | None = None
    apparel: dict[str, Any] = field(default_factory=dict)
    visible: bool = True
    look: Look = field(default_factory=Look)

    @classmethod
    def create(
        cls,
        name: str,
        x: float = 80,
        y: float = 100,
        scale: float = 1.0,
        cloth: int | None = None,
        pants: int | None = None,
        hair: int | None = None,
        expression: str = "neutral",
        facing: int = 1,
        preset: str | None = None,
        hair_style: str | None = None,
        body: str | None = None,
        skin: int | str | None = None,
        shoes: int | None = None,
        sleeves: str | None = None,
        skirt: bool | None = None,
        hat: int | None = None,
        belt: int | None = None,
        beard: str | None = None,
    ) -> "Character":
        spec: dict[str, Any] = dict(PRESETS.get(preset or "", {}))
        overrides = dict(shirt=cloth, pants=pants, hair=hair, hair_style=hair_style, body=body,
                         skin=skin, shoes=shoes, sleeves=sleeves, skirt=skirt, hat=hat, belt=belt, beard=beard)
        for k, v in overrides.items():
            if v is not None:
                spec[k] = v
        if isinstance(spec.get("skin"), str):
            spec["skin"] = pal.SKIN_TONES.get(spec["skin"], pal.SKIN)
        body_type = str(spec.pop("body", "default"))
        look = Look(**{k: v for k, v in spec.items() if k in Look.__dataclass_fields__})
        return cls(
            name=name,
            skeleton=Skeleton.humanoid(scale=scale, cloth=look.shirt, pants=look.pants, body=body_type),
            x=x,
            y=y,
            facing=facing,
            expression=expression,
            hair_color=look.hair,
            look=look,
        )

    @property
    def origin(self) -> Vec:
        return (self.x, self.y)

    def rig(self) -> Rig:
        return self.skeleton.solve(self.origin, self.facing)

    def joints(self) -> dict[str, tuple[Vec, Vec]]:
        return self.rig().joints()
