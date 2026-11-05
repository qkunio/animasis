"""Fluent Python builder for scenes (agent-friendly API)."""

from __future__ import annotations

from typing import Any, Self

from . import palette as pal
from .physics import Body
from .poses import apply_pose
from .scene import Scene, TimelineEvent, render_scene
from .skeleton import Character


class SceneBuilder:
    def __init__(self, name: str = "scene") -> None:
        self.scene = Scene(name=name)

    def size(self, width: int = 320, height: int = 180) -> Self:
        self.scene.width = width
        self.scene.height = height
        self.scene.world.width = float(width)
        self.scene.world.height = float(height)
        return self

    def fps(self, fps: int) -> Self:
        self.scene.fps = fps
        return self

    def duration(self, seconds: float) -> Self:
        self.scene.duration = seconds
        return self

    def background(self, kind: str) -> Self:
        self.scene.background = kind
        return self

    def ground(self, y: float) -> Self:
        self.scene.ground_y = y
        self.scene.world.ground_y = y
        return self

    def scale(self, n: int) -> Self:
        self.scene.scale = n
        return self

    def character(
        self,
        name: str,
        *,
        x: float = 80,
        y: float | None = None,
        cloth: int | str | None = None,
        pants: int | str | None = None,
        hair: int | str | None = None,
        expression: str = "neutral",
        facing: int = 1,
        scale: float = 1.0,
        pose: str = "idle",
        hat: int | str | None = None,
        preset: str | None = None,
        hair_style: str | None = None,
        body: str | None = None,
        skin: int | str | None = None,
        shoes: int | str | None = None,
        sleeves: str | None = None,
        skirt: bool | None = None,
        belt: int | str | None = None,
    ) -> Self:
        from .scene import _as_color

        ch = Character.create(
            name=name,
            x=x,
            y=self.scene.ground_y if y is None else y,
            scale=scale,
            cloth=_as_color(cloth, None),
            pants=_as_color(pants, None),
            hair=_as_color(hair, None),
            expression=expression,
            facing=facing,
            preset=preset,
            hair_style=hair_style,
            body=body,
            skin=skin,
            shoes=_as_color(shoes, None),
            sleeves=sleeves,
            skirt=skirt,
            hat=_as_color(hat, None),
            belt=_as_color(belt, None),
        )
        apply_pose(ch.skeleton, pose)
        self.scene.characters[name] = ch
        self.scene._pose_state[name] = {"pose": pose, "cycle": None, "cycle_t0": 0.0}
        return self

    def object(
        self,
        name: str,
        *,
        kind: str = "ball",
        x: float = 160,
        y: float = 80,
        w: float = 8,
        h: float = 8,
        color: int | str = pal.BALL,
        bounce: float = 0.55,
        held_by: str | None = None,
        vx: float = 0,
        vy: float = 0,
        dynamic: bool = True,
    ) -> Self:
        from .scene import _as_color

        body = Body(
            name=name,
            x=x,
            y=y,
            w=w,
            h=h,
            kind=kind,
            color=_as_color(color, pal.BALL),
            restitution=bounce,
            vx=vx,
            vy=vy,
            dynamic=dynamic,
        )
        if held_by:
            body.attached_to = held_by
            self.scene.held[name] = held_by
            if held_by in self.scene.characters:
                self.scene.characters[held_by].held_item = name
        self.scene.world.add(body)
        return self

    def at(self, t: float, action: str, target: str | None = None, **params: Any) -> Self:
        self.scene.timeline.append(TimelineEvent(time=t, action=action, target=target, params=params))
        self.scene.timeline.sort(key=lambda e: e.time)
        return self

    def build(self) -> Scene:
        return self.scene

    def render(self, output: str) -> str:
        path = render_scene(self.scene, output)
        return str(path)
