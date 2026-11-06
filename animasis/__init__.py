"""Animasis — pixel animation toolkit for AI agents."""

from __future__ import annotations

__version__ = "0.2.0"

from .builder import SceneBuilder
from .scene import Scene, load_scene, render_scene
from .skeleton import Character, Skeleton, normalize_view, VIEWS
from .palette import PALETTE, nearest_palette

__all__ = [
    "SceneBuilder",
    "Scene",
    "load_scene",
    "render_scene",
    "Character",
    "Skeleton",
    "normalize_view",
    "VIEWS",
    "PALETTE",
    "nearest_palette",
    "__version__",
]
