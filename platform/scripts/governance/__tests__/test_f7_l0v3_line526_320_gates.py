"""test_f7_l0v3_line526_320_gates.py — F7 (W3-1_REVIEW.md §7/§10, gate review, non-blocking).

R69 fixed 4 occurrences of the stale "0/320 gates" figure (8 gates x 40 assets) in
MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md, but missed a fifth, differently-worded instance
of the same self-contradiction: §"Priority order" item 5, "Briefs and gates — 40 briefs, 320
gates". Same defect class (the pre-ruling-17 eight-gate arithmetic, 8 x 40 = 320, not caught by
R69's literal "0/320" string match since this line has no "0/" prefix), fixed here to 360 (the
post-ruling-17, nine-gate figure R69's own fix already uses elsewhere in this file).

Fails against the pre-fix text.
"""
from __future__ import annotations

import pathlib

L0V3 = pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md"


def test_priority_order_item_5_no_longer_says_320_gates():
    text = L0V3.read_text(encoding="utf-8")
    assert "320 gates" not in text


def test_priority_order_item_5_says_360_gates():
    text = L0V3.read_text(encoding="utf-8")
    assert "40 briefs, 360 gates" in text
