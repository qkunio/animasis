"""Virtual camera: shots, pan/zoom moves, hard cuts, dip-to-black fades and reverse angles.

The world (background, props, characters) is still drawn on the scene's pixel stage
(``width`` x ``height``).  A camera crops a window of that stage and scales it to the
output frame, so a ``zoom: 2`` close-up shows half the stage width with every world
pixel twice as big.  Story overlays are split: world-anchored ones (huts, fences,
``follow``-ed bubbles/tags, ``space: world`` text) move with the camera, while captions,
cards, corner tags and weather stay fixed on screen and keep their native pixel size.

YAML::

    camera:
      - { t: 0,    shot: wide }                                   # hard cut (default)
      - { t: 9.2,  shot: medium, target: liubei, move: 4.0, ease: inout }   # push-in
      - { t: 13.8, shot: close, target: [liubei, guanyu], offset: [0, -6] }
      - { t: 19.0, shot: wide, transition: fade, fade: 0.6 }      # dip to black around t
      - { t: 27.6, shot: close, target: [210, 125], flip: true }  # reverse angle

Keys: ``t`` (start), ``shot`` (preset zoom), ``zoom`` (overrides the preset), ``target``
(character name, list of names -> midpoint, ``[x, y]``, ``{x:, y:}``, an overlay ``id``,
or ``stage``), ``offset`` ``[dx, dy]`` in world px, ``move`` seconds of eased pan/zoom
from the previous framing (0 = cut), ``ease`` (linear|in|out|inout), ``transition``
(cut|fade), ``fade`` seconds, ``flip`` mirror for a reverse-angle shot, ``name`` label.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

SHOTS: dict[str, float] = {
    "wide": 1.0, "establishing": 1.0, "远景": 1.0,
    "full": 1.3, "全景": 1.3,
    "medium": 1.7, "中景": 1.7,
    "close": 2.4, "近景": 2.4,
    "closeup": 3.0, "特写": 3.0,
    "ecu": 3.6, "extreme": 3.6, "大特写": 3.6,
}
EASES = ("linear", "in", "out", "inout")
TRANSITIONS = ("cut", "fade")

Resolver = Callable[[Any], "tuple[float, float] | None"]


class CameraError(ValueError):
    pass


@dataclass
class CameraKey:
    t: float
    zoom: float = 1.0
    target: Any = None
    offset: tuple[float, float] = (0.0, 0.0)
    move: float = 0.0
    ease: str = "inout"
    transition: str = "cut"
    fade: float = 0.5
    flip: bool = False
    shot: str | None = None
    name: str = ""


@dataclass
class CamState:
    cx: float
    cy: float
    zoom: float
    flip: bool = False
    brightness: float = 1.0


def _ease(u: float, kind: str) -> float:
    u = min(1.0, max(0.0, u))
    if kind == "in":
        return u * u
    if kind == "out":
        return 1 - (1 - u) * (1 - u)
    if kind == "inout":
        return u * u * (3 - 2 * u)
    return u


def parse_key(d: dict[str, Any]) -> CameraKey:
    if not isinstance(d, dict):
        raise CameraError(f"camera key must be a mapping, got {d!r}")
    if "t" not in d and "time" not in d:
        raise CameraError(f"camera key needs t: {d!r}")
    shot = d.get("shot")
    if shot is not None and str(shot) not in SHOTS:
        raise CameraError(f"unknown shot {shot!r}; use one of {sorted(SHOTS)}")
    zoom = float(d["zoom"]) if "zoom" in d else SHOTS[str(shot)] if shot is not None else 1.0
    if zoom < 1.0:
        raise CameraError(f"zoom must be >= 1 (whole stage), got {zoom}")
    off = d.get("offset", (0, 0))
    if isinstance(off, dict):
        off = (off.get("x", 0), off.get("y", 0))
    if not (isinstance(off, (list, tuple)) and len(off) == 2):
        raise CameraError(f"offset must be [dx, dy], got {off!r}")
    ease = str(d.get("ease", "inout"))
    if ease not in EASES:
        raise CameraError(f"unknown ease {ease!r}")
    trans = str(d.get("transition", "cut"))
    if trans not in TRANSITIONS:
        raise CameraError(f"unknown transition {trans!r}")
    move = float(d["move"]) if "move" in d else (float(d["until"]) - float(d.get("t", d.get("time"))) if "until" in d else 0.0)
    return CameraKey(
        t=float(d.get("t", d.get("time"))), zoom=zoom, target=d.get("target"),
        offset=(float(off[0]), float(off[1])), move=max(0.0, move), ease=ease, transition=trans,
        fade=float(d.get("fade", 0.5)), flip=bool(d.get("flip", False)),
        shot=str(shot) if shot is not None else None, name=str(d.get("name", "")),
    )


@dataclass
class Camera:
    keys: list[CameraKey] = field(default_factory=list)
    width: int = 320
    height: int = 180

    @classmethod
    def from_yaml(cls, data: Any, width: int = 320, height: int = 180) -> "Camera":
        if isinstance(data, dict):
            data = data.get("keys", [])
        if not isinstance(data, list):
            raise CameraError("camera: expects a list of keyframes")
        keys = sorted((parse_key(d) for d in data), key=lambda k: k.t)
        return cls(keys=keys, width=width, height=height)

    # ------------------------------------------------------------------ framing
    def _goal(self, k: CameraKey, resolve: Resolver) -> tuple[float, float, float]:
        p = resolve(k.target) if k.target not in (None, "stage") else None
        cx, cy = p if p is not None else (self.width / 2, self.height / 2)
        return cx + k.offset[0], cy + k.offset[1], k.zoom

    def _raw(self, t: float, resolve: Resolver, upto: int) -> tuple[float, float, float]:
        i = upto
        while i >= 0 and self.keys[i].t > t + 1e-9:
            i -= 1
        if i < 0:
            return self.width / 2, self.height / 2, 1.0
        k = self.keys[i]
        goal = self._goal(k, resolve)
        if k.move > 0 and t < k.t + k.move and i > 0:
            a = self._raw(t, resolve, i - 1)
            u = _ease((t - k.t) / k.move, k.ease)
            # zoom interpolates in log space so pushes feel uniform
            za, zb = a[2], goal[2]
            z = za * (zb / za) ** u
            return a[0] + (goal[0] - a[0]) * u, a[1] + (goal[1] - a[1]) * u, z
        return goal

    def clamp(self, cx: float, cy: float, zoom: float) -> tuple[float, float, float]:
        zoom = max(1.0, zoom)
        hw, hh = self.width / zoom / 2, self.height / zoom / 2
        cx = min(max(cx, hw), self.width - hw)
        cy = min(max(cy, hh), self.height - hh)
        return cx, cy, zoom

    def state(self, t: float, resolve: Resolver | None = None) -> CamState:
        resolve = resolve or (lambda target: _literal(target))
        if not self.keys:
            return CamState(self.width / 2, self.height / 2, 1.0)
        cx, cy, z = self.clamp(*self._raw(t, resolve, len(self.keys) - 1))
        cur = self.current_key(t)
        flip = bool(cur.flip) if cur else False
        b = 1.0
        for k in self.keys:
            if k.transition == "fade" and k.fade > 0:
                half = k.fade / 2
                d = abs(t - k.t)
                if d < half:
                    b = min(b, d / half)
        return CamState(cx, cy, z, flip, b)

    def current_key(self, t: float) -> CameraKey | None:
        cur = None
        for k in self.keys:
            if k.t <= t + 1e-9:
                cur = k
        return cur

    # ------------------------------------------------------------------ mapping
    def view_box(self, st: CamState) -> tuple[float, float, float, float]:
        hw, hh = self.width / st.zoom / 2, self.height / st.zoom / 2
        return st.cx - hw, st.cy - hh, st.cx + hw, st.cy + hh

    def to_screen(self, st: CamState) -> Callable[[float, float], tuple[float, float]]:
        W, H = self.width, self.height

        def f(x: float, y: float) -> tuple[float, float]:
            sx = (x - st.cx) * st.zoom + W / 2
            sy = (y - st.cy) * st.zoom + H / 2
            return (W - sx if st.flip else sx), sy

        return f

    def shot_list(self, duration: float | None = None) -> list[dict[str, Any]]:
        """One row per key: start, end, shot/zoom, target, movement, transition, label."""
        rows = []
        for i, k in enumerate(self.keys):
            end = self.keys[i + 1].t if i + 1 < len(self.keys) else duration
            kind = k.shot or f"zoom {k.zoom:g}"
            rows.append({
                "t": k.t, "end": end, "shot": kind, "zoom": k.zoom,
                "target": k.target if k.target is not None else "stage",
                "move": f"{'push' if i and k.zoom > self.keys[i - 1].zoom else 'pull' if i and k.zoom < self.keys[i - 1].zoom else 'pan'} {k.move:g}s" if k.move else "cut",
                "transition": k.transition + (" (reverse angle)" if k.flip else ""),
                "name": k.name,
            })
        return rows


def _literal(target: Any) -> tuple[float, float] | None:
    if isinstance(target, (list, tuple)) and len(target) == 2 and all(isinstance(v, (int, float)) for v in target):
        return float(target[0]), float(target[1])
    if isinstance(target, dict) and "x" in target:
        return float(target["x"]), float(target.get("y", 90))
    return None


def make_resolver(characters: dict[str, Any], overlays: Iterable[Any] = (), *,
                  ground_y: float = 140, body_h: float = 20, t: float = 0.0) -> Resolver:
    """Targets -> world point. Characters resolve to mid-body (feet - body_h*scale)."""
    by_id = {str(o.p["id"]): o for o in overlays if getattr(o, "p", None) and "id" in o.p}

    def one(target: Any) -> tuple[float, float] | None:
        lit = _literal(target)
        if lit is not None:
            return lit
        if isinstance(target, str):
            if target in characters:
                ch = characters[target]
                return float(ch.x), float(ch.y) - body_h * float(getattr(ch, "scale", 1.0) or 1.0)
            if target in by_id:
                o = by_id[target]
                if o.kind == "satellite":
                    from .space import sat_pos
                    x, y, _ = sat_pos(o, t)
                    return x, y
                return float(o.p.get("x", 160)), float(o.p.get("cy", o.p.get("y", ground_y - 30)))
            raise CameraError(f"unknown camera target {target!r}")
        if isinstance(target, (list, tuple)) and target:
            pts = [one(v) for v in target]
            pts = [p for p in pts if p is not None]
            if pts:
                return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        return None

    return one


def validate_targets(cam: Camera, characters: dict[str, Any], overlays: Iterable[Any] = ()) -> None:
    res = make_resolver(characters, overlays)
    for k in cam.keys:
        if k.target not in (None, "stage"):
            res(k.target)  # raises CameraError on unknown names
