#!/usr/bin/env python3
"""Generate a synthetic facade and run the real renderer over it.

Produces a coordinate grid and an annotated image in --output, using the
canonical script exactly as an agent would invoke it. CI uploads the result
so every run leaves a visible rendering proof.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER = ROOT / "skills" / "architecturehell" / "scripts" / "annotate_architecture.py"

MANIFEST = {
    "title": "CI Smoke Facade",
    "subtitle": "generated fixture, rendered by tools/render_smoke.py",
    "roast_level": 6,
    "callouts": [
        {
            "text": "Window bays negotiate three rhythms and commit to none.",
            "target": [0.37, 0.55],
            "feature_bounds": [0.26, 0.42, 0.5, 0.75],
            "kind": "issue",
        },
        {
            "text": "The parapet line is honest work.",
            "target": [0.5, 0.36],
            "kind": "merit",
        },
        {
            "text": "A downspout with main-character energy.",
            "target": [0.79, 0.68],
            "width": 0.2,
            "kind": "oddity",
        },
    ],
}


def make_facade(path: Path) -> None:
    from PIL import Image, ImageDraw

    width, height = 1400, 1000
    image = Image.new("RGB", (width, height), (168, 185, 199))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, height * 0.82, width, height), fill=(96, 104, 92))
    draw.rectangle((width * 0.24, height * 0.34, width * 0.78, height * 0.86), fill=(189, 170, 146))
    draw.rectangle((width * 0.24, height * 0.34, width * 0.78, height * 0.38), fill=(140, 122, 102))
    for wx in range(4):
        for wy in range(3):
            left = width * (0.29 + wx * 0.12)
            top = height * (0.44 + wy * 0.13)
            draw.rectangle(
                (left, top, left + width * 0.07, top + height * 0.09), fill=(66, 84, 110)
            )
    draw.rectangle((width * 0.795, height * 0.4, width * 0.805, height * 0.86), fill=(88, 82, 76))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=Path("smoke"), help="output directory")
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    facade = out / "facade.png"
    manifest_path = out / "callouts.json"
    make_facade(facade)
    manifest_path.write_text(json.dumps(MANIFEST, indent=2), encoding="utf-8")
    for extra in (
        ["--grid-output", out / "grid.png"],
        ["--manifest", manifest_path, "--output", out / "annotated.png"],
    ):
        command = [sys.executable, str(RENDERER), "--input", str(facade), *map(str, extra)]
        result = subprocess.run(command)
        if result.returncode != 0:
            return result.returncode
    print(f"smoke render complete: {out / 'annotated.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
