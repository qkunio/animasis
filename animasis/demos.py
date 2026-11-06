"""Bundled story and explainer demos."""

from __future__ import annotations

import sys
from pathlib import Path

from .scene import load_scene, render_scene


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def demo_dir() -> Path:
    return _root() / "demos"


def output_dir() -> Path:
    d = demo_dir() / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_demo_yaml() -> list[Path]:
    """List the hand-authored YAML demo scenes."""
    return sorted(demo_dir().glob("*.yaml"))


def render_all_demos(out_dir: str | Path | None = None) -> list[Path]:
    out = Path(out_dir) if out_dir else output_dir()
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for ypath in write_demo_yaml():
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
