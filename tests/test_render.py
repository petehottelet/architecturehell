"""End-to-end rendering tests against generated fixture images."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from loader import load_renderer, make_image, valid_manifest

mod = load_renderer()


class RenderAnnotationsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def render(self, manifest=None, size=(1200, 900)):
        source_path = make_image(self.tmp / "facade.png", size=size)
        manifest = mod.validate_manifest(manifest or valid_manifest())
        with Image.open(source_path) as source:
            source.load()
            return mod.render_annotations(source, manifest, preferred_font=None)

    def test_output_matches_input_dimensions_and_mode(self):
        result = self.render()
        self.assertEqual(result.size, (1200, 900))
        self.assertEqual(result.mode, "RGBA")

    def test_render_changes_pixels(self):
        source_path = make_image(self.tmp / "facade.png")
        manifest = mod.validate_manifest(valid_manifest())
        with Image.open(source_path) as source:
            source.load()
            base = source.convert("RGBA")
            result = mod.render_annotations(source, manifest, preferred_font=None)
        self.assertNotEqual(base.tobytes(), result.tobytes())

    def test_cards_stay_on_canvas_and_off_protected_features(self):
        """Placement invariants, observed through the real placement calls."""
        placed = []
        original = mod.place_box

        def recording_place_box(*args, **kwargs):
            rect = original(*args, **kwargs)
            placed.append(rect)
            return rect

        manifest = valid_manifest()
        with mock.patch.object(mod, "place_box", recording_place_box):
            result = self.render(manifest=manifest, size=(1600, 1200))
        width, height = result.size
        validated = mod.validate_manifest(manifest)
        protected = []
        for callout in validated["callouts"]:
            if callout["feature_bounds"]:
                left, top, right, bottom = callout["feature_bounds"]
                protected.append(
                    (round(left * width), round(top * height), round(right * width), round(bottom * height))
                )
        self.assertEqual(len(placed), len(validated["callouts"]))
        for rect in placed:
            self.assertGreaterEqual(rect[0], 0)
            self.assertGreaterEqual(rect[1], 0)
            self.assertLessEqual(rect[2], width)
            self.assertLessEqual(rect[3], height)
            for feature in protected:
                self.assertFalse(
                    mod.overlaps(rect, feature, gap=0),
                    f"card {rect} overlaps protected feature {feature}",
                )
        for i, a in enumerate(placed):
            for b in placed[i + 1 :]:
                self.assertFalse(mod.overlaps(a, b, gap=0), f"cards {a} and {b} overlap")

    def test_render_without_title_or_optional_fields(self):
        manifest = valid_manifest(title=None, subtitle=None)
        result = self.render(manifest=manifest)
        self.assertEqual(result.size, (1200, 900))

    def test_exif_orientation_is_respected(self):
        path = self.tmp / "rotated.jpg"
        image = Image.new("RGB", (800, 500), (90, 100, 110))
        exif = Image.Exif()
        exif[0x0112] = 6  # rotate 90 CW on display
        image.save(path, "JPEG", exif=exif)
        with Image.open(path) as source:
            source.load()
            grid = mod.render_grid(source, preferred_font=None)
        self.assertEqual(grid.size, (500, 800))

    def test_font_fallback_without_any_system_font(self):
        with mock.patch.object(mod, "font_candidates", lambda bold: []):
            font = mod.load_font(20, bold=True)
            self.assertIsNotNone(font)
            result = self.render()
        self.assertEqual(result.size, (1200, 900))


class SaveImageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_jpeg_output_is_flattened_to_rgb(self):
        rgba = Image.new("RGBA", (64, 48), (255, 230, 0, 128))
        out = self.tmp / "nested" / "card.jpg"
        mod.save_image(rgba, out)
        with Image.open(out) as reloaded:
            self.assertEqual(reloaded.mode, "RGB")
            self.assertEqual(reloaded.size, (64, 48))

    def test_png_output_keeps_alpha(self):
        rgba = Image.new("RGBA", (64, 48), (255, 230, 0, 128))
        out = self.tmp / "card.png"
        mod.save_image(rgba, out)
        with Image.open(out) as reloaded:
            self.assertEqual(reloaded.mode, "RGBA")


if __name__ == "__main__":
    unittest.main()
