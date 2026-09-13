"""Geometry tests: overlap logic, label placement, arrows, wrapping."""

from __future__ import annotations

import unittest

from PIL import Image, ImageDraw

from loader import load_renderer

mod = load_renderer()

CANVAS = (1600, 1200)
MARGIN = 20


class OverlapTests(unittest.TestCase):
    def test_disjoint_boxes_do_not_overlap(self):
        self.assertFalse(mod.overlaps((0, 0, 100, 100), (200, 200, 300, 300), gap=10))

    def test_gap_counts_as_overlap(self):
        # Boxes 5px apart with a 10px required gap collide.
        self.assertTrue(mod.overlaps((0, 0, 100, 100), (105, 0, 200, 100), gap=10))

    def test_containment_overlaps(self):
        self.assertTrue(mod.overlaps((0, 0, 300, 300), (100, 100, 150, 150), gap=0))


class PlaceBoxTests(unittest.TestCase):
    def test_preferred_spot_used_when_free(self):
        rect = mod.place_box(400, 400, 300, 120, CANVAS, occupied=[], protected=[], margin=MARGIN)
        self.assertEqual(rect, (400, 400, 700, 520))

    def test_avoids_occupied_boxes(self):
        occupied = [(400, 400, 700, 520)]
        rect = mod.place_box(400, 400, 300, 120, CANVAS, occupied, protected=[], margin=MARGIN)
        self.assertFalse(mod.overlaps(rect, occupied[0], gap=0))

    def test_avoids_protected_feature_bounds(self):
        protected = [(380, 380, 720, 540)]
        rect = mod.place_box(400, 400, 300, 120, CANVAS, occupied=[], protected=protected, margin=MARGIN)
        self.assertFalse(mod.overlaps(rect, protected[0], gap=0))

    def test_clamps_to_canvas_margins(self):
        rect = mod.place_box(-500, -500, 300, 120, CANVAS, occupied=[], protected=[], margin=MARGIN)
        left, top, right, bottom = rect
        self.assertGreaterEqual(left, MARGIN)
        self.assertGreaterEqual(top, MARGIN)
        self.assertLessEqual(right, CANVAS[0] - MARGIN)
        self.assertLessEqual(bottom, CANVAS[1] - MARGIN)


class ConnectionPointTests(unittest.TestCase):
    def test_connects_on_side_facing_target(self):
        box = (500, 500, 800, 620)
        x, y = mod.connection_point((100, 560), box)
        self.assertEqual(x, 500)  # left edge faces a target on the left
        self.assertEqual(y, 560)

    def test_connects_on_top_when_target_above(self):
        box = (500, 500, 800, 620)
        x, y = mod.connection_point((650, 100), box)
        self.assertEqual(y, 500)
        self.assertEqual(x, 650)


class WrapTextTests(unittest.TestCase):
    def test_wrapped_lines_fit_max_width(self):
        image = Image.new("RGB", (400, 100))
        draw = ImageDraw.Draw(image)
        font = mod.load_font(16)
        text = "value engineering has clearly visited this rainscreen more than once"
        wrapped = mod.wrap_text(draw, text, font, max_width=140)
        lines = wrapped.split("\n")
        self.assertGreater(len(lines), 1)
        for line in lines:
            self.assertLessEqual(mod.text_width(draw, line, font), 140)

    def test_preserves_blank_lines(self):
        image = Image.new("RGB", (400, 100))
        draw = ImageDraw.Draw(image)
        font = mod.load_font(16)
        wrapped = mod.wrap_text(draw, "a\n\nb", font, max_width=300)
        self.assertEqual(wrapped, "a\n\nb")


if __name__ == "__main__":
    unittest.main()
