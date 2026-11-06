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

    p_nar = sub.add_parser("narrate", help="Render a scene and mix its `narration:` (edge-tts) into the MP4")
    p_nar.add_argument("scene", type=str)
    p_nar.add_argument("-o", "--output", type=str, required=True)
    p_nar.add_argument("--video", type=str, default=None, help="reuse an already-rendered silent video")

    p_shots = sub.add_parser("shots", help="Print a scene's camera shot list (分镜表)")
    p_shots.add_argument("scene", type=str)
    p_shots.add_argument("--markdown", action="store_true")

    p_poses = sub.add_parser("poses", help="List built-in poses")
    p_demos = sub.add_parser("demos", help="Render bundled demo scenes")
    p_demos.add_argument("-o", "--output-dir", type=str, default=None)

    p_publish = sub.add_parser("publish", help="Publish videos, notes, and articles through SAU")
    p_publish.add_argument("sau_args", nargs=argparse.REMAINDER)

    args = parser.parse_args(argv)

    if args.cmd == "publish":
        from .publishing import main as publish_main

        return publish_main(args.sau_args)

    if args.cmd == "poses":
        from .poses import CYCLES, list_poses

        print("Poses:", ", ".join(list_poses()))
        print("Cycles:", ", ".join(sorted(CYCLES)))
        return 0

    if args.cmd == "shots":
        scene = load_scene(args.scene)
        if scene.camera is None:
            print("(no camera: single locked-off wide shot)")
            return 0
        rows = scene.camera.shot_list(scene.duration)
        if args.markdown:
            print("| # | 时间 | 镜头 | 目标 | 运动 | 转场 | 说明 |")
            print("|---|---|---|---|---|---|---|")
        for i, r in enumerate(rows, 1):
            span = f"{r['t']:.1f}–{r['end']:.1f}s"
            tgt = r["target"] if isinstance(r["target"], str) else ",".join(map(str, r["target"]))
            if args.markdown:
                print(f"| {i} | {span} | {r['shot']} (×{r['zoom']:g}) | {tgt} | {r['move']} | {r['transition']} | {r['name']} |")
            else:
                print(f"{i:2d} {span:>12}  {r['shot']:<8} x{r['zoom']:<4g} {tgt:<20} {r['move']:<10} {r['transition']:<22} {r['name']}")
        return 0

    if args.cmd == "demos":
        from .demos import render_all_demos

        out = render_all_demos(args.output_dir)
        for p in out:
            print(p)
        return 0

    if args.cmd == "narrate":
        from .narrate import narrate_scene

        print(str(narrate_scene(args.scene, args.output, args.video)))
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
