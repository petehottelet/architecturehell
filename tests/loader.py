"""Shared helpers: load the canonical renderer script as a module."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER = ROOT / "skills" / "architecturehell" / "scripts" / "annotate_architecture.py"
SYNC = ROOT / "tools" / "sync_skills.py"


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_renderer():
    return _load(RENDERER, "annotate_architecture")


def load_sync():
    return _load(SYNC, "sync_skills")


def make_image(path: Path, size=(1200, 900), color=(120, 130, 140)):
    """Write a synthetic photo-like image and return its path."""
    from PIL import Image, ImageDraw

    image = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(image)
    width, height = size
    # A crude facade so renders have plausible content.
    draw.rectangle((width * 0.2, height * 0.35, width * 0.8, height * 0.95), fill=(180, 160, 140))
    for wx in range(3):
        for wy in range(2):
            left = width * (0.28 + wx * 0.18)
            top = height * (0.45 + wy * 0.22)
            draw.rectangle((left, top, left + width * 0.08, top + height * 0.12), fill=(70, 90, 120))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return path


def valid_manifest(**overrides):
    manifest = {
        "title": "Test Facade",
        "subtitle": "unit fixture",
        "roast_level": 6,
        "callouts": [
            {
                "text": "Window rhythm abandons the datum line without notice.",
                "target": [0.35, 0.5],
                "feature_bounds": [0.28, 0.45, 0.42, 0.62],
                "kind": "issue",
            },
            {
                "text": "The cornice is doing honest work here.",
                "target": [0.5, 0.36],
                "label": [0.05, 0.05],
                "kind": "merit",
            },
            {
                "text": "An oddly confident downspout.",
                "target": [0.78, 0.7],
                "width": 0.2,
                "kind": "oddity",
            },
        ],
    }
    manifest.update(overrides)
    return manifest


def write_manifest(path: Path, manifest) -> Path:
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path
