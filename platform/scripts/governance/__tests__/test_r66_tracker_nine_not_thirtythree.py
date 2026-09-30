"""test_r66_tracker_nine_not_thirtythree.py — R66 (NIKASHA_CHANGE_REGISTER_v2_0.md).

`00_ARCHITECTURE/control/asset_elevation_tracker.py:43`'s GATES comment said "Eight, not
thirty-three" — stale since native ruling 17 (2026-09-26) added the ninth (Build) gate, one line
above the actual GATES list this comment introduces (which the module itself already carries 9
tuples for). Fails against the pre-fix text.
"""
from __future__ import annotations

import pathlib
import re
import sys

TRACKER_PATH = pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE/control/asset_elevation_tracker.py"

sys.path.insert(0, str(TRACKER_PATH.parent))


def test_comment_says_nine_not_thirtythree():
    text = TRACKER_PATH.read_text(encoding="utf-8")
    assert "Eight, not thirty-three" not in text
    assert "Nine, not thirty-three" in text


def test_gates_list_actually_has_nine_entries():
    import importlib.util
    spec = importlib.util.spec_from_file_location("asset_elevation_tracker", TRACKER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # noqa: S102 — loading the tracker module itself, not eval'ing text
    assert len(mod.GATES) == 9, f"GATES has {len(mod.GATES)} entries, comment claims nine"
