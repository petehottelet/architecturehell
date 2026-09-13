# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-13

### Added

- MIT license, at the repository root and inside every skill copy.
- `tools/sync_skills.py`: the discovery copies under `.claude/skills/` and
  `.agents/skills/` are now generated from the canonical skill via a fixed
  file manifest, never edited by hand; `--check` mode verifies them.
- Renderer test suite (`tests/`, stdlib unittest, Pillow-only): manifest
  validation contract, label placement and overlap invariants, end-to-end
  rendering, EXIF orientation, font fallback, CLI exit codes, and sync-tool
  behavior. All fixture images are generated in-test.
- CI across Linux, macOS, and Windows on Python 3.10 and 3.12, with a
  discovery-copy drift gate and an uploaded rendered smoke image on every
  run (`tools/render_smoke.py`). Actions are SHA-pinned; Dependabot watches
  them.
- `VERSION` and this changelog.

### Fixed

- `references/manifest-schema.md` now documents the validator's actual
  callout text limit of 180 characters (it previously claimed 140).

### Removed

- Stray 2.5 MB `house.png` from the `.agents` discovery copy, which existed
  in no other copy — the drift the sync tool now prevents.
