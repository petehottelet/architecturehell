"""Manifest validation contract tests."""

from __future__ import annotations

import unittest

from loader import load_renderer, valid_manifest

mod = load_renderer()


class ManifestValidationTests(unittest.TestCase):
    def test_valid_manifest_normalizes_defaults(self):
        result = mod.validate_manifest(valid_manifest())
        self.assertEqual(result["roast_level"], 6)
        self.assertEqual(len(result["callouts"]), 3)
        third = result["callouts"][2]
        self.assertEqual(third["kind"], "oddity")
        self.assertEqual(third["width"], 0.2)
        # Defaults applied where omitted.
        self.assertEqual(result["callouts"][0]["width"], 0.23)
        self.assertIsNone(result["callouts"][2]["label"])

    def test_text_is_stripped(self):
        manifest = valid_manifest()
        manifest["callouts"][0]["text"] = "  padded copy  "
        result = mod.validate_manifest(manifest)
        self.assertEqual(result["callouts"][0]["text"], "padded copy")

    def test_manifest_must_be_object(self):
        with self.assertRaisesRegex(ValueError, "JSON object"):
            mod.validate_manifest(["not", "an", "object"])

    def test_roast_level_range(self):
        for bad in (0, 12, True, "6", 2.5):
            manifest = valid_manifest(roast_level=bad)
            with self.assertRaisesRegex(ValueError, "roast_level"):
                mod.validate_manifest(manifest)
        manifest = valid_manifest(roast_level=11)
        self.assertEqual(mod.validate_manifest(manifest)["roast_level"], 11)

    def test_callout_count_bounds(self):
        base = valid_manifest()["callouts"][1]  # merit works at any level
        for count, ok in ((0, False), (1, True), (18, True), (19, False)):
            manifest = valid_manifest(callouts=[dict(base) for _ in range(count)])
            if ok:
                mod.validate_manifest(manifest)
            else:
                with self.assertRaisesRegex(ValueError, "1 to 18"):
                    mod.validate_manifest(manifest)

    def test_text_required_and_non_empty(self):
        manifest = valid_manifest()
        del manifest["callouts"][0]["text"]
        with self.assertRaisesRegex(ValueError, r"callout 1\.text"):
            mod.validate_manifest(manifest)
        manifest = valid_manifest()
        manifest["callouts"][1]["text"] = "   "
        with self.assertRaisesRegex(ValueError, r"callout 2\.text"):
            mod.validate_manifest(manifest)

    def test_text_length_contract_is_180(self):
        manifest = valid_manifest()
        manifest["callouts"][0]["text"] = "x" * 180
        mod.validate_manifest(manifest)  # exactly at the limit passes
        manifest["callouts"][0]["text"] = "x" * 181
        with self.assertRaisesRegex(ValueError, "exceeds 180 characters"):
            mod.validate_manifest(manifest)

    def test_target_validation(self):
        manifest = valid_manifest()
        manifest["callouts"][0]["target"] = [0.5]
        with self.assertRaisesRegex(ValueError, "two-number JSON array"):
            mod.validate_manifest(manifest)
        manifest = valid_manifest()
        manifest["callouts"][0]["target"] = [0.5, 1.2]
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            mod.validate_manifest(manifest)

    def test_feature_bounds_require_positive_area(self):
        manifest = valid_manifest()
        manifest["callouts"][0]["feature_bounds"] = [0.6, 0.4, 0.5, 0.7]
        with self.assertRaisesRegex(ValueError, "positive area"):
            mod.validate_manifest(manifest)

    def test_width_bounds(self):
        manifest = valid_manifest()
        manifest["callouts"][0]["width"] = 0.11
        with self.assertRaisesRegex(ValueError, "between 0.12 and 0.50"):
            mod.validate_manifest(manifest)
        manifest = valid_manifest()
        manifest["callouts"][0]["width"] = 0.50
        mod.validate_manifest(manifest)

    def test_kind_vocabulary(self):
        manifest = valid_manifest()
        manifest["callouts"][0]["kind"] = "insult"
        with self.assertRaisesRegex(ValueError, "issue, oddity, or merit"):
            mod.validate_manifest(manifest)

    def test_roast_level_one_is_complimentary_only(self):
        manifest = valid_manifest(roast_level=1)
        with self.assertRaisesRegex(ValueError, "merit at Roast Level 1"):
            mod.validate_manifest(manifest)
        for callout in manifest["callouts"]:
            callout["kind"] = "merit"
        result = mod.validate_manifest(manifest)
        self.assertTrue(all(c["kind"] == "merit" for c in result["callouts"]))


if __name__ == "__main__":
    unittest.main()
