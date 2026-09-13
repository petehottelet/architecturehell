"""Command-line contract tests: exit codes, outputs, non-destructiveness."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from loader import RENDERER, make_image, valid_manifest, write_manifest


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(RENDERER), *map(str, args)],
        capture_output=True,
        text=True,
        timeout=120,
    )


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.input_path = make_image(self.tmp / "facade.png")

    def test_grid_mode(self):
        grid = self.tmp / "grid.png"
        result = run_cli("--input", self.input_path, "--grid-output", grid)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Wrote coordinate grid", result.stdout)
        with Image.open(grid) as image:
            self.assertEqual(image.size, (1200, 900))

    def test_full_render_is_non_destructive(self):
        before = self.input_path.read_bytes()
        manifest = write_manifest(self.tmp / "callouts.json", valid_manifest())
        output = self.tmp / "annotated.png"
        result = run_cli("--input", self.input_path, "--manifest", manifest, "--output", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Wrote annotated image", result.stdout)
        self.assertEqual(self.input_path.read_bytes(), before, "input image was modified")
        with Image.open(output) as image:
            self.assertEqual(image.size, (1200, 900))

    def test_jpeg_output(self):
        manifest = write_manifest(self.tmp / "callouts.json", valid_manifest())
        output = self.tmp / "annotated.jpg"
        result = run_cli("--input", self.input_path, "--manifest", manifest, "--output", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(output) as image:
            self.assertEqual(image.mode, "RGB")

    def test_missing_input_exits_nonzero(self):
        result = run_cli("--input", self.tmp / "nope.png", "--grid-output", self.tmp / "g.png")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Input image not found", result.stderr)

    def test_requires_manifest_and_output_or_grid(self):
        result = run_cli("--input", self.input_path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("--grid-output", result.stderr)

    def test_invalid_json_manifest_exits_2(self):
        manifest = self.tmp / "broken.json"
        manifest.write_text("{not json", encoding="utf-8")
        result = run_cli(
            "--input", self.input_path, "--manifest", manifest, "--output", self.tmp / "o.png"
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)

    def test_validation_failure_exits_2(self):
        bad = valid_manifest()
        bad["callouts"][0]["text"] = "x" * 181
        manifest = write_manifest(self.tmp / "long.json", bad)
        result = run_cli(
            "--input", self.input_path, "--manifest", manifest, "--output", self.tmp / "o.png"
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("exceeds 180", result.stderr)

    def test_roast_level_override_is_applied(self):
        # Manifest has non-merit callouts; forcing level 1 must fail validation,
        # proving the CLI override reaches the validator.
        manifest = write_manifest(self.tmp / "callouts.json", valid_manifest())
        result = run_cli(
            "--input", self.input_path,
            "--manifest", manifest,
            "--output", self.tmp / "o.png",
            "--roast-level", "1",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Roast Level 1", result.stderr)

    def test_grid_and_render_in_one_invocation(self):
        manifest = write_manifest(self.tmp / "callouts.json", valid_manifest())
        grid = self.tmp / "grid.png"
        output = self.tmp / "annotated.png"
        result = run_cli(
            "--input", self.input_path,
            "--grid-output", grid,
            "--manifest", manifest,
            "--output", output,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(grid.is_file())
        self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
