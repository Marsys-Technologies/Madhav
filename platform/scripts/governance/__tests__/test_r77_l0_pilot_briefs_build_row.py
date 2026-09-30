"""test_r77_l0_pilot_briefs_build_row.py — R77 (NIKASHA_CHANGE_REGISTER_v2_0.md).

All five L0 pilot briefs carried eight gates with no Build row (`## §4 ... The eight gates`, 8 gate
rows each) while the tracker's REQUIRED_GATES (asset_elevation_tracker.py GATES, fixed by R66 this
wave) demands nine. Each brief gains a ninth (`Build`) gate row measured against a real, read-only
`asset_census.py --layer L0` run (2026-09-28), and BG_PANCHANGA's own N/A count is recomputed from
"six of eight" to "six of nine" (its Build gate resolves PASS via honest N/A dispositions, not
N/A itself, so the numerator is unchanged and only the denominator moves).

Fails against the pre-fix briefs (no Build row, stale "eight gates" headings).
"""
from __future__ import annotations

import pathlib
import re

BRIEFS_DIR = pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE/briefs/nirmana/l0_assets"

BRIEFS = [
    "BG_ONTOLOGY_ELEVATION_BRIEF_v1_0.md",
    "BG_EPHEMERIS_ELEVATION_BRIEF_v1_0.md",
    "BG_PANCHANGA_ELEVATION_BRIEF_v1_0.md",
    "BG_RULES_ELEVATION_BRIEF_v1_0.md",
    "BG_SARVATOBHADRA_GRID_ELEVATION_BRIEF_v1_0.md",
]

CLOSED_VERDICTS = ("PASS", "FAIL", "PARTIAL", "NO_DETECTOR", "N/A")


def _text(name: str) -> str:
    return (BRIEFS_DIR / name).read_text(encoding="utf-8")


def test_no_brief_still_says_eight_gates():
    for name in BRIEFS:
        text = _text(name)
        assert "the eight gates" not in text.lower(), f"{name} still says eight gates"


def test_every_brief_has_a_build_gate_row_with_a_closed_verdict():
    for name in BRIEFS:
        text = _text(name)
        m = re.search(r"\|\s*\*\*Build\*\*[^|]*\|\s*\*\*([A-Z_/]+)\*\*\s*\|", text)
        assert m, f"{name} has no Build gate row with a verdict cell right after the gate name"
        verdict = m.group(1)
        assert verdict in CLOSED_VERDICTS, (
            f"{name} Build gate's verdict cell is {verdict!r}, not one of the closed set {CLOSED_VERDICTS}"
        )


def test_panchanga_headline_and_heading_recomputed_to_nine():
    text = _text("BG_PANCHANGA_ELEVATION_BRIEF_v1_0.md")
    assert "six of eight gates" not in text
    assert "six of nine gates" in text
    assert re.search(r"## §4 .* the nine gates — six N/A", text, re.IGNORECASE)


def test_gate_table_now_has_nine_gate_rows_in_each_brief():
    gate_names = ["Ldgr", "Idem", "Earn", "Null", "Vocab", "Carr", "Narr", "Dens", "Build"]
    for name in BRIEFS:
        text = _text(name)
        for g in gate_names:
            assert re.search(rf"\|\s*\*\*{g}\*\*", text), f"{name} missing gate row {g}"
