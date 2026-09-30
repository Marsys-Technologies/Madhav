"""test_r65_tracker_build_check_count.py — R65 (tracker-comment half only; NIKASHA_CHANGE_REGISTER_v2_0.md).

Build check-count disagreement: T3 §5.2/changelog and the tracker's GATES comment for the Build
gate both said "six static checks [plus a dry-run proof]" while T4 §4.2 already lists nine. D2
ruling 2026-09-27 released only the tracker-comment half now (the T3 §5.2/changelog half is D2
reopen work, out of scope for this wave). This test covers the tracker half only: it fails against
the pre-fix "six static checks" text and passes once the tracker's Build-gate description reads
nine, aligned with T4 §4.2 (already fixed by R64 in this same wave).
"""
from __future__ import annotations

import pathlib

TRACKER_PATH = pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE/control/asset_elevation_tracker.py"


def test_tracker_no_longer_says_six_static_checks():
    text = TRACKER_PATH.read_text(encoding="utf-8")
    assert "six static checks" not in text


def test_tracker_build_gate_says_nine():
    import importlib.util
    spec = importlib.util.spec_from_file_location("asset_elevation_tracker", TRACKER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    build = [g for g in mod.GATES if g[0] == "Build"]
    assert len(build) == 1
    assert "nine static checks" in build[0][3]
