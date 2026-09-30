"""test_r69_l0v3_0_360_gates.py — R69 (NIKASHA_CHANGE_REGISTER_v2_0.md).

L0 v3.0 (MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md) self-contradicted: 4 places said
"0/320 gates" (the stale eight-gate figure: 8 x 40 = 320) while one place (the "Nine gates x 40
assets = 360" line) already had the post-ruling-17 figure. Replaced the 4 stale occurrences with
0/360, leaving the already-correct derivation line untouched. Fails against the pre-fix text.
"""
from __future__ import annotations

import pathlib

L0V3 = pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md"


def test_no_stale_0_320_figure():
    text = L0V3.read_text(encoding="utf-8")
    assert "0/320" not in text


def test_four_0_360_occurrences_present():
    text = L0V3.read_text(encoding="utf-8")
    assert text.count("0/360") == 4


def test_derivation_line_still_says_nine_times_forty_equals_360():
    text = L0V3.read_text(encoding="utf-8")
    assert "Nine gates × 40 assets = 360" in text
