"""Bundled demos — indoor pickup, two-person handoff, outdoor jump physics."""

from __future__ import annotations

import sys
from pathlib import Path

from .builder import SceneBuilder
from .scene import load_scene, render_scene


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def demo_dir() -> Path:
    return _root() / "demos"


def output_dir() -> Path:
    d = demo_dir() / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d


def build_indoor_pickup() -> SceneBuilder:
    """Indoor: walk to ball, pick it up, stand happy."""
    b = (
        SceneBuilder("indoor_pickup")
        .size(320, 180)
        .fps(12)
        .duration(5.0)
        .background("indoor")
        .ground(145)
        .scale(3)
        .character("hero", x=40, preset="hero", hat="red", expression="neutral")
        .object("ball", kind="ball", x=200, y=40, bounce=0.6, color="orange")
        .at(0.0, "cycle", "hero", name="idle", speed=0.6)
        .at(0.3, "walk_to", "hero", x=185, speed=55)
        .at(2.2, "pose", "hero", name="pickup")
        .at(2.2, "expression", "hero", name="surprise")
        .at(2.5, "pickup", "hero", object="ball")
        .at(2.8, "pose", "hero", name="idle")
        .at(2.8, "expression", "hero", name="happy")
        .at(3.2, "cycle", "hero", name="wave", speed=1.5)
    )
    return b


def build_two_person_handoff() -> SceneBuilder:
    """Two characters: wave, walk closer, hand over a gift."""
    b = (
        SceneBuilder("two_person_handoff")
        .size(320, 180)
        .fps(12)
        .duration(6.0)
        .background("room")
        .ground(145)
        .scale(3)
        .character("alice", x=60, preset="alice", facing=1, expression="happy")
        .character("bob", x=250, preset="bob", facing=-1, expression="neutral", hat="navy")
        .object("gift", kind="gift", x=60, y=100, held_by="alice", color="gold")
        .at(0.2, "cycle", "alice", name="wave", speed=1.4)
        .at(0.2, "cycle", "bob", name="wave", speed=1.2)
        .at(1.5, "walk_to", "alice", x=140, speed=45)
        .at(1.5, "walk_to", "bob", x=180, speed=40)
        .at(3.2, "pose", "alice", name="give")
        .at(3.2, "pose", "bob", name="receive")
        .at(3.5, "give", "alice", to="bob", object="gift")
        .at(3.5, "expression", "bob", name="happy")
        .at(3.5, "expression", "alice", name="happy")
        .at(4.2, "cycle", "bob", name="wave", speed=1.5)
        .at(4.5, "pose", "alice", name="idle")
    )
    return b


def build_outdoor_jump() -> SceneBuilder:
    """Outdoor: run, jump, ball bounce with gravity."""
    b = (
        SceneBuilder("outdoor_jump")
        .size(320, 180)
        .fps(12)
        .duration(5.5)
        .background("outdoor")
        .ground(150)
        .scale(3)
        .character("runner", x=30, preset="runner", expression="happy")
        .object("ball", kind="ball", x=100, y=40, vx=35, vy=-20, bounce=0.7, color="orange")
        .object("crate", kind="box", x=240, y=150 - 6, w=14, h=12, bounce=0.2, color="brown", dynamic=False)
        .at(0.0, "walk_to", "runner", x=120, speed=60)
        .at(1.8, "jump", "runner", vy=-240)
        .at(1.8, "expression", "runner", name="surprise")
        .at(2.8, "expression", "runner", name="happy")
        .at(3.0, "walk_to", "runner", x=220, speed=55)
        .at(4.5, "cycle", "runner", name="wave", speed=1.6)
        .at(2.0, "impulse", "ball", vx=50, vy=-180)
    )
    return b


DEMOS = {
    "indoor_pickup": build_indoor_pickup,
    "two_person_handoff": build_two_person_handoff,
    "outdoor_jump": build_outdoor_jump,
}


def write_demo_yaml() -> list[Path]:
    """Write YAML companions for the three demos (hand-authored for clarity)."""
    # YAML files are maintained separately under demos/; this ensures they exist.
    return sorted(demo_dir().glob("*.yaml"))


def render_all_demos(out_dir: str | Path | None = None) -> list[Path]:
    out = Path(out_dir) if out_dir else output_dir()
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    # Prefer YAML files if present; else builder
    yaml_files = {
        "indoor_pickup": demo_dir() / "indoor_pickup.yaml",
        "two_person_handoff": demo_dir() / "two_person_handoff.yaml",
        "outdoor_jump": demo_dir() / "outdoor_jump.yaml",
    }
    for key, builder_fn in DEMOS.items():
        ypath = yaml_files[key]
        out_path = out / f"{key}.mp4"
        if ypath.exists():
            scene = load_scene(ypath)
            paths.append(render_scene(scene, out_path))
        else:
            paths.append(Path(builder_fn().render(str(out_path))))
        print(f"rendered {paths[-1]}", file=sys.stderr)
    # story / explainer scenes (YAML only), e.g. demos/econ_opportunity_cost.yaml
    for ypath in sorted(demo_dir().glob("econ_*.yaml")):
        paths.append(render_scene(load_scene(ypath), out / f"{ypath.stem}.mp4"))
        print(f"rendered {paths[-1]}", file=sys.stderr)
    return paths


def main() -> int:
    paths = render_all_demos()
    for p in paths:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
