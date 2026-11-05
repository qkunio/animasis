"""Animasis CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .scene import load_scene, render_scene


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="animasis",
        description="Animasis — pixel animation for AI agents",
    )
    parser.add_argument("--version", action="version", version=f"animasis {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_render = sub.add_parser("render", help="Render a scene YAML/JSON to MP4 or GIF")
    p_render.add_argument("scene", type=str, help="Path to scene.yaml / scene.json")
    p_render.add_argument("-o", "--output", type=str, required=True, help="Output path (.mp4/.gif)")
    p_render.add_argument("--fps", type=int, default=None)
    p_render.add_argument("--scale", type=int, default=None)
    p_render.add_argument("--duration", type=float, default=None)

    p_poses = sub.add_parser("poses", help="List built-in poses")
    p_demos = sub.add_parser("demos", help="Render bundled demo scenes")
    p_demos.add_argument("-o", "--output-dir", type=str, default=None)

    args = parser.parse_args(argv)

    if args.cmd == "poses":
        from .poses import CYCLES, list_poses

        print("Poses:", ", ".join(list_poses()))
        print("Cycles:", ", ".join(sorted(CYCLES)))
        return 0

    if args.cmd == "demos":
        from .demos import render_all_demos

        out = render_all_demos(args.output_dir)
        for p in out:
            print(p)
        return 0

    if args.cmd == "render":
        scene = load_scene(args.scene)
        if args.fps:
            scene.fps = args.fps
        if args.scale:
            scene.scale = args.scale
        if args.duration:
            scene.duration = args.duration
        path = render_scene(scene, args.output)
        print(str(path))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
