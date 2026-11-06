"""Smoke tests for Animasis."""

from __future__ import annotations

from pathlib import Path

from animasis.builder import SceneBuilder
from animasis.poses import list_poses
from animasis.scene import load_scene, render_scene


def test_poses_nonempty():
    assert "idle" in list_poses()
    assert "jump" in list_poses()


def test_builder_render_gif(tmp_path: Path):
    out = tmp_path / "t.gif"
    path = (
        SceneBuilder("t")
        .duration(0.5)
        .fps(8)
        .scale(2)
        .background("outdoor")
        .character("a", x=50)
        .object("ball", x=100, y=40)
        .at(0.0, "pose", "a", name="wave")
        .render(str(out))
    )
    assert Path(path).exists()
    assert Path(path).stat().st_size > 100


def test_load_yaml():
    root = Path(__file__).resolve().parents[1]
    sc = load_scene(root / "demos" / "econ_opportunity_cost.yaml")
    assert sc.name == "econ_opportunity_cost"
    assert sc.overlays


def test_narration_default_voice():
    from animasis.narrate import load_narration

    root = Path(__file__).resolve().parents[1]
    nar = load_narration(root / "demos" / "econ_opportunity_cost.yaml")
    assert nar["voice"] == "zh-CN-YunjianNeural"
