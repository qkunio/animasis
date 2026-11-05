"""Scene YAML/JSON DSL loader and timeline playback."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import palette as pal
from .physics import Body, World
from .poses import apply_pose, get_pose, sample_cycle
from .overlay import Overlay, draw_overlays, overlay_from_dict
from .render import composite_frame, export_frames
from .skeleton import Character

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


@dataclass
class TimelineEvent:
    time: float
    action: str
    target: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Scene:
    name: str = "scene"
    width: int = 320
    height: int = 180
    fps: int = 12
    duration: float = 4.0
    background: str = "outdoor"
    ground_y: float = 140.0
    scale: int = 3  # nearest-neighbor export scale
    gravity: float = 420.0
    characters: dict[str, Character] = field(default_factory=dict)
    world: World = field(default_factory=World)
    timeline: list[TimelineEvent] = field(default_factory=list)
    held: dict[str, str] = field(default_factory=dict)  # object -> character
    overlays: list[Overlay] = field(default_factory=list)  # timed text / props / title cards
    _pose_state: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.world.ground_y = self.ground_y
        self.world.width = float(self.width)
        self.world.height = float(self.height)
        self.world.gravity = self.gravity


def _as_color(v: Any, default: int) -> int:
    if v is None:
        return default
    if isinstance(v, int):
        return v
    named = {
        "red": pal.CLOTH_B,
        "blue": pal.CLOTH_A,
        "navy": 25,
        "sky": 9,
        "green": 8,
        "forest": 15,
        "gold": pal.ACCENT,
        "yellow": pal.ACCENT,
        "blonde": pal.ACCENT,
        "brown": pal.HAIR,
        "dark_brown": 24,
        "black": 1,
        "grey": 2,
        "gray": 2,
        "white": 4,
        "skin": pal.SKIN,
        "orange": pal.BALL,
        "ginger": pal.GINGER,
        "purple": 11,
        "plum": 29,
        "maroon": 27,
    }
    return named.get(str(v).lower(), default)


def load_scene(path: str | Path) -> Scene:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        if yaml is None:
            raise RuntimeError("PyYAML is required for YAML scenes. pip install PyYAML")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return scene_from_dict(data)


def scene_from_dict(data: dict[str, Any]) -> Scene:
    sc = Scene(
        name=str(data.get("name", "scene")),
        width=int(data.get("width", 320)),
        height=int(data.get("height", 180)),
        fps=int(data.get("fps", 12)),
        duration=float(data.get("duration", 4.0)),
        background=str(data.get("background", "outdoor")),
        ground_y=float(data.get("ground_y", 140)),
        scale=int(data.get("scale", 3)),
        gravity=float(data.get("gravity", 420)),
    )
    for c in data.get("characters", []) or []:
        ch = Character.create(
            name=str(c["name"]),
            x=float(c.get("x", 80)),
            y=float(c.get("y", sc.ground_y)),
            scale=float(c.get("scale", 1.0)),
            cloth=_as_color(c.get("cloth"), None),
            pants=_as_color(c.get("pants"), None),
            hair=_as_color(c.get("hair"), None),
            expression=str(c.get("expression", "neutral")),
            facing=int(c.get("facing", 1)),
            preset=c.get("preset"),
            hair_style=c.get("hair_style"),
            body=c.get("body"),
            skin=c.get("skin"),
            shoes=_as_color(c.get("shoes"), None),
            sleeves=c.get("sleeves"),
            skirt=c.get("skirt"),
            hat=_as_color(c.get("hat"), None) if c.get("hat") else None,
            belt=_as_color(c.get("belt"), None),
        )
        if c.get("apparel"):
            ch.apparel["items"] = list(c.get("apparel") or [])
        pose = c.get("pose", "idle")
        apply_pose(ch.skeleton, pose)
        sc.characters[ch.name] = ch
        sc._pose_state[ch.name] = {"pose": pose, "cycle": None, "cycle_t0": 0.0}

    for o in data.get("objects", []) or []:
        body = Body(
            name=str(o["name"]),
            x=float(o.get("x", 160)),
            y=float(o.get("y", 80)),
            w=float(o.get("w", 8)),
            h=float(o.get("h", 8)),
            vx=float(o.get("vx", 0)),
            vy=float(o.get("vy", 0)),
            restitution=float(o.get("bounce", 0.55)),
            dynamic=bool(o.get("dynamic", True)),
            kind=str(o.get("kind", "ball")),
            color=_as_color(o.get("color"), pal.BALL),
            hang=str(o.get("hang", "hand_r")),
        )
        if o.get("held_by"):
            body.attached_to = str(o["held_by"])
            sc.held[body.name] = body.attached_to
            ch = sc.characters.get(body.attached_to)
            if ch:
                ch.held_item = body.name
        sc.world.add(body)

    for o in data.get("overlays", []) or []:
        sc.overlays.append(overlay_from_dict(o))

    for ev in data.get("timeline", []) or []:
        sc.timeline.append(
            TimelineEvent(
                time=float(ev.get("t", ev.get("time", 0))),
                action=str(ev["action"]),
                target=ev.get("target") or ev.get("who") or ev.get("on"),
                params={k: v for k, v in ev.items() if k not in ("t", "time", "action", "target", "who", "on")},
            )
        )
    sc.timeline.sort(key=lambda e: e.time)
    return sc


def _apply_event(scene: Scene, ev: TimelineEvent) -> None:
    a = ev.action
    who = ev.target
    p = ev.params

    if a == "pose" and who in scene.characters:
        apply_pose(scene.characters[who].skeleton, str(p.get("name", "idle")))
        scene._pose_state[who] = {"pose": p.get("name", "idle"), "cycle": None, "cycle_t0": ev.time}
    elif a == "cycle" and who in scene.characters:
        scene._pose_state[who] = {
            "pose": None,
            "cycle": str(p.get("name", "walk")),
            "cycle_t0": ev.time,
            "speed": float(p.get("speed", 1.0)),
        }
    elif a == "expression" and who in scene.characters:
        scene.characters[who].expression = str(p.get("name", "neutral"))
    elif a == "face" and who in scene.characters:
        scene.characters[who].facing = int(p.get("dir", p.get("facing", 1)))
    elif a == "move" and who in scene.characters:
        ch = scene.characters[who]
        if "x" in p:
            ch.x = float(p["x"])
        if "y" in p:
            ch.y = float(p["y"])
        if "dx" in p:
            ch.x += float(p["dx"])
        if "dy" in p:
            ch.y += float(p["dy"])
    elif a == "walk_to" and who in scene.characters:
        # store destination; continuous move handled in tick
        scene._pose_state[who]["walk_to"] = float(p.get("x", scene.characters[who].x))
        scene._pose_state[who]["walk_speed"] = float(p.get("speed", 40))
        scene._pose_state[who]["cycle"] = "walk"
        scene._pose_state[who]["cycle_t0"] = ev.time
        scene._pose_state[who]["speed"] = 1.2
    elif a == "pickup" and who in scene.characters:
        obj = str(p.get("object", p.get("item", "")))
        if obj in scene.world.bodies:
            scene.held[obj] = who
            scene.world.bodies[obj].attached_to = who
            scene.characters[who].held_item = obj
            apply_pose(scene.characters[who].skeleton, "pickup")
            scene._pose_state[who] = {"pose": "pickup", "cycle": None, "cycle_t0": ev.time}
    elif a == "drop" and who in scene.characters:
        obj = scene.characters[who].held_item or p.get("object")
        if obj and obj in scene.held:
            del scene.held[obj]
            body = scene.world.bodies[obj]
            body.attached_to = None
            body.vx = float(p.get("vx", scene.characters[who].facing * 30))
            body.vy = float(p.get("vy", -40))
            scene.characters[who].held_item = None
    elif a == "give":
        # give object from giver to receiver
        giver = who or str(p.get("from"))
        recv = str(p.get("to"))
        obj = str(p.get("object", p.get("item", "")))
        if giver in scene.characters and recv in scene.characters and obj in scene.world.bodies:
            scene.held[obj] = recv
            scene.world.bodies[obj].attached_to = recv
            scene.characters[giver].held_item = None
            scene.characters[recv].held_item = obj
            apply_pose(scene.characters[giver].skeleton, "give")
            apply_pose(scene.characters[recv].skeleton, "receive")
    elif a == "impulse":
        obj = who or str(p.get("object"))
        if obj in scene.world.bodies:
            scene.world.impulse(obj, float(p.get("vx", 0)), float(p.get("vy", 0)))
    elif a == "jump" and who in scene.characters:
        ch = scene.characters[who]
        apply_pose(ch.skeleton, "jump")
        scene._pose_state[who] = {
            "pose": "jump",
            "cycle": None,
            "cycle_t0": ev.time,
            "air_vy": float(p.get("vy", -220)),
            "air_y0": ch.y,
            "air_t0": ev.time,
            "jumping": True,
        }
    elif a == "say" and who in scene.characters:
        scene.characters[who].expression = str(p.get("expression", "happy"))


def _tick_continuous(scene: Scene, t: float, dt: float) -> None:
    for name, ch in scene.characters.items():
        st = scene._pose_state.setdefault(name, {})
        # walk_to
        if "walk_to" in st:
            target = float(st["walk_to"])
            speed = float(st.get("walk_speed", 40))
            dx = target - ch.x
            if abs(dx) < 1.5:
                ch.x = target
                del st["walk_to"]
                st["cycle"] = None
                apply_pose(ch.skeleton, "idle")
                st["pose"] = "idle"
            else:
                step = min(abs(dx), speed * dt) * (1 if dx > 0 else -1)
                ch.x += step
                ch.facing = 1 if dx > 0 else -1
        # jump arc (character root y)
        if st.get("jumping"):
            elapsed = t - float(st["air_t0"])
            g = scene.gravity
            y = float(st["air_y0"]) + float(st["air_vy"]) * elapsed + 0.5 * g * elapsed * elapsed
            if y >= scene.ground_y and elapsed > 0.05:
                ch.y = scene.ground_y
                st["jumping"] = False
                apply_pose(ch.skeleton, "land")
                st["pose"] = "land"
            else:
                ch.y = y
                apply_pose(ch.skeleton, "jump")
        # cycle poses
        if st.get("cycle"):
            speed = float(st.get("speed", 1.0))
            ct = (t - float(st.get("cycle_t0", 0))) * speed
            pose = sample_cycle(str(st["cycle"]), ct)
            ch.skeleton.set_pose(pose)


def render_scene(scene: Scene, output: str | Path) -> Path:
    n_frames = max(1, int(scene.duration * scene.fps))
    dt = 1.0 / scene.fps
    events = list(scene.timeline)
    ei = 0
    frames = []

    for i in range(n_frames):
        t = i * dt
        while ei < len(events) and events[ei].time <= t + 1e-9:
            _apply_event(scene, events[ei])
            ei += 1
        _tick_continuous(scene, t, dt)
        scene.world.step(dt)
        hooks = {}
        if scene.overlays:
            def _layer(name: str, t: float = t):
                def run(fb):
                    draw_overlays(fb.put, scene.overlays, t, name, width=scene.width, height=scene.height,
                                  ground_y=scene.ground_y, characters=scene.characters)
                return run
            hooks = {"under": _layer("back"), "over": _layer("front")}
        fb = composite_frame(
            list(scene.characters.values()),
            scene.world,
            bg=scene.background,
            width=scene.width,
            height=scene.height,
            held=scene.held,
            **hooks,
        )
        frames.append(fb.to_image(scale=scene.scale))

    return export_frames(frames, output, fps=scene.fps)
