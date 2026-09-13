"""Tests for the discovery-copy sync tool."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from loader import ROOT, load_sync

sync_mod = load_sync()


def make_repo_fixture(tmp: Path) -> Path:
    """Build a miniature repo tree with a canonical skill and a root LICENSE."""
    root = tmp / "repo"
    canonical = root / sync_mod.CANONICAL
    for name in sync_mod.FILES:
        if name == "LICENSE":
            continue
        target = canonical / name
        target.parent.mkdir(parents=True, exist_ok=True)
        source = ROOT / sync_mod.CANONICAL / name
        if source.is_file():
            shutil.copy2(source, target)
        else:
            target.write_text(f"fixture: {name}\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT fixture license\n", encoding="utf-8")
    return root


class SyncSkillsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = make_repo_fixture(Path(self._tmp.name))

    def test_sync_creates_identical_copies_with_license(self):
        problems = sync_mod.sync(self.root, check=False)
        self.assertEqual(problems, [])
        for copy_rel in sync_mod.COPIES:
            for name in sync_mod.FILES:
                src = self.root / sync_mod.CANONICAL / name
                dst = self.root / copy_rel / name
                self.assertTrue(dst.is_file(), f"missing {dst}")
                self.assertEqual(src.read_bytes(), dst.read_bytes(), f"differs: {name}")
        # LICENSE was sourced from the repo root into the canonical copy too.
        self.assertEqual(
            (self.root / sync_mod.CANONICAL / "LICENSE").read_text(encoding="utf-8"),
            "MIT fixture license\n",
        )

    def test_sync_removes_stray_files(self):
        sync_mod.sync(self.root, check=False)
        stray = self.root / sync_mod.COPIES[1] / "assets" / "house.png"
        stray.parent.mkdir(parents=True, exist_ok=True)
        stray.write_bytes(b"not a real png")
        sync_mod.sync(self.root, check=False)
        self.assertFalse(stray.exists(), "stray file survived a sync")

    def test_check_mode_reports_drift_without_writing(self):
        sync_mod.sync(self.root, check=False)
        self.assertEqual(sync_mod.sync(self.root, check=True), [])
        drifted = self.root / sync_mod.COPIES[0] / "SKILL.md"
        original = drifted.read_bytes()
        drifted.write_text("hand-edited drift\n", encoding="utf-8")
        problems = sync_mod.sync(self.root, check=True)
        self.assertTrue(any("SKILL.md" in problem for problem in problems))
        # Check mode must not repair the drift.
        self.assertNotEqual(drifted.read_bytes(), original)

    def test_missing_canonical_file_is_fatal(self):
        (self.root / sync_mod.CANONICAL / "SKILL.md").unlink()
        with self.assertRaises(SystemExit):
            sync_mod.sync(self.root, check=False)

    def test_real_repo_is_in_sync(self):
        """The actual working tree must always pass check mode."""
        self.assertEqual(sync_mod.sync(ROOT, check=True), [])


if __name__ == "__main__":
    unittest.main()
