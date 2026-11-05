"""Lightweight 2D physics: gravity, AABB ground/object collision, bounce."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Body:
    name: str
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    w: float = 8.0
    h: float = 8.0
    mass: float = 1.0
    restitution: float = 0.55  # bounce
    friction: float = 0.85
    dynamic: bool = True
    on_ground: bool = False
    kind: str = "ball"
    color: int = 6
    attached_to: str | None = None  # character name when held
    hang: str = "hand_r"

    @property
    def left(self) -> float:
        return self.x - self.w / 2

    @property
    def right(self) -> float:
        return self.x + self.w / 2

    @property
    def top(self) -> float:
        return self.y - self.h / 2

    @property
    def bottom(self) -> float:
        return self.y + self.h / 2


@dataclass
class World:
    gravity: float = 420.0  # px/s^2 (screen y+)
    ground_y: float = 140.0
    width: float = 320.0
    height: float = 180.0
    bodies: dict[str, Body] = field(default_factory=dict)
    walls: bool = True

    def add(self, body: Body) -> Body:
        self.bodies[body.name] = body
        return body

    def step(self, dt: float) -> None:
        dt = max(0.0, min(dt, 1 / 20))
        for b in self.bodies.values():
            if not b.dynamic or b.attached_to:
                b.vx = 0.0
                b.vy = 0.0
                b.on_ground = False
                continue
            b.vy += self.gravity * dt
            b.x += b.vx * dt
            b.y += b.vy * dt
            b.on_ground = False

            # ground
            if b.bottom >= self.ground_y:
                b.y = self.ground_y - b.h / 2
                if b.vy > 0:
                    b.vy = -b.vy * b.restitution
                    b.vx *= b.friction
                    if abs(b.vy) < 25:
                        b.vy = 0.0
                        b.on_ground = True

            # walls
            if self.walls:
                if b.left < 2:
                    b.x = 2 + b.w / 2
                    b.vx = abs(b.vx) * b.restitution
                if b.right > self.width - 2:
                    b.x = self.width - 2 - b.w / 2
                    b.vx = -abs(b.vx) * b.restitution

            # ceiling soft clamp
            if b.top < 2:
                b.y = 2 + b.h / 2
                b.vy = abs(b.vy) * 0.3

        # body-body AABB (simple sequential)
        names = [n for n, b in self.bodies.items() if b.dynamic and not b.attached_to]
        for i, na in enumerate(names):
            for nb in names[i + 1 :]:
                a, b = self.bodies[na], self.bodies[nb]
                if a.right < b.left or a.left > b.right or a.bottom < b.top or a.top > b.bottom:
                    continue
                # separate along smaller overlap axis
                ox = min(a.right - b.left, b.right - a.left)
                oy = min(a.bottom - b.top, b.bottom - a.top)
                if ox < oy:
                    push = ox / 2 + 0.1
                    if a.x < b.x:
                        a.x -= push
                        b.x += push
                    else:
                        a.x += push
                        b.x -= push
                    a.vx, b.vx = b.vx * 0.9, a.vx * 0.9
                else:
                    push = oy / 2 + 0.1
                    if a.y < b.y:
                        a.y -= push
                        b.y += push
                    else:
                        a.y += push
                        b.y -= push
                    a.vy, b.vy = -abs(a.vy) * a.restitution, -abs(b.vy) * b.restitution

    def impulse(self, name: str, vx: float = 0.0, vy: float = 0.0) -> None:
        b = self.bodies[name]
        b.vx += vx
        b.vy += vy
        b.attached_to = None
