"""Narration: synthesize a scene's ``narration:`` lines with edge-tts and mux them into the MP4.

Scene YAML::

    narration:
      voice: zh-CN-YunxiNeural     # any `edge-tts --list-voices` name
      rate: "+5%"
      lines:
        - { t: 0.8, text: "三顾茅庐。" }

Each line is synthesized once (cached by voice/rate/text under ``audio_dir``),
placed at its ``t`` with ffmpeg ``adelay``, mixed to one narration track,
padded with silence to the video length and muxed as AAC.

    python -m animasis.narrate demos/sangu_maolu.yaml -o demos/output/sangu_maolu.mp4
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

DEFAULT_VOICE = "zh-CN-YunxiNeural"


def probe_duration(path: str | Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def load_narration(scene_path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(scene_path).read_text(encoding="utf-8"))
    nar = dict(data.get("narration") or {})
    nar.setdefault("voice", DEFAULT_VOICE)
    nar.setdefault("rate", "+0%")
    nar.setdefault("volume", "+0%")
    nar["lines"] = [dict(l) for l in nar.get("lines", [])]
    nar["duration"] = float(data.get("duration", 0))
    nar["name"] = str(data.get("name", Path(scene_path).stem))
    return nar


def synthesize(nar: dict[str, Any], audio_dir: str | Path) -> list[dict[str, Any]]:
    """TTS every line (cached); returns lines with ``file`` and ``dur`` filled in."""
    audio_dir = Path(audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    exe = shutil.which("edge-tts") or str(Path(sys.executable).with_name("edge-tts"))
    out = []
    for i, line in enumerate(nar["lines"]):
        voice = str(line.get("voice", nar["voice"]))
        rate = str(line.get("rate", nar["rate"]))
        text = str(line["text"])
        h = hashlib.sha1(json.dumps([voice, rate, nar["volume"], text]).encode()).hexdigest()[:10]
        f = audio_dir / f"{i + 1:02d}_{h}.mp3"
        if not f.exists():
            subprocess.run([exe, "--voice", voice, f"--rate={rate}", f"--volume={nar['volume']}",
                            "--text", text, "--write-media", str(f)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        out.append({**line, "file": str(f), "dur": probe_duration(f), "t": float(line["t"])})
    return out


def check_timing(lines: list[dict[str, Any]], duration: float) -> list[str]:
    warns = []
    for a, b in zip(lines, lines[1:]):
        if a["t"] + a["dur"] > b["t"] + 1e-3:
            warns.append(f"line at {a['t']:.1f}s ends {a['t'] + a['dur']:.2f}s, overlaps next at {b['t']:.1f}s")
    if lines and lines[-1]["t"] + lines[-1]["dur"] > duration:
        warns.append(f"last line ends {lines[-1]['t'] + lines[-1]['dur']:.2f}s > video {duration:.2f}s")
    return warns


def mix_track(lines: list[dict[str, Any]], duration: float, out_wav: str | Path) -> Path:
    """One mono 24 kHz WAV of all lines placed at their start times, silence-padded to ``duration``."""
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for l in lines:
        cmd += ["-i", l["file"]]
    parts = []
    for i, l in enumerate(lines):
        ms = int(round(l["t"] * 1000))
        parts.append(f"[{i}:a]aresample=24000,aformat=channel_layouts=mono,adelay={ms}:all=1[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(lines)))
    parts.append(f"{mix}amix=inputs={len(lines)}:normalize=0:dropout_transition=0,apad,atrim=0:{duration:.3f}[out]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[out]", "-ac", "1", "-ar", "24000", str(out_wav)]
    subprocess.run(cmd, check=True)
    return Path(out_wav)


def mux(video: str | Path, audio: str | Path, out: str | Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                    "-shortest", "-movflags", "+faststart", str(out)], check=True)
    return Path(out)


def narrate_scene(scene_path: str | Path, output: str | Path, video: str | Path | None = None,
                  audio_dir: str | Path | None = None) -> Path:
    scene_path, output = Path(scene_path), Path(output)
    nar = load_narration(scene_path)
    audio_dir = Path(audio_dir) if audio_dir else scene_path.parent / "audio" / nar["name"]
    lines = synthesize(nar, audio_dir)
    with tempfile.TemporaryDirectory() as td:
        if video is None:
            from .scene import load_scene, render_scene
            video = render_scene(load_scene(scene_path), Path(td) / "silent.mp4")
        dur = probe_duration(video)
        for w in check_timing(lines, dur):
            print("narration warning:", w, file=sys.stderr)
        wav = mix_track(lines, dur, audio_dir.parent / f"{nar['name']}_narration.wav")
        output.parent.mkdir(parents=True, exist_ok=True)
        mux(video, wav, output)
    for l in lines:
        print(f"  {l['t']:6.2f}s +{l['dur']:.2f}s  {l['text']}", file=sys.stderr)
    return output


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="animasis.narrate", description=__doc__.split("\n")[0])
    ap.add_argument("scene")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--video", default=None, help="use an already-rendered silent video instead of rendering")
    ap.add_argument("--audio-dir", default=None)
    a = ap.parse_args(argv)
    print(narrate_scene(a.scene, a.output, a.video, a.audio_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
