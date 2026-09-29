"""test_r70_l0v3_stale_figures_datestamped.py — R70 (NIKASHA_CHANGE_REGISTER_v2_0.md).

L0 v3.0's §1.1 ("NO_BRIEF = 40/40 ...") and pilot-findings ("Ledger after five pilots: 30 gap rows,
18 opportunity rows ...") status figures no longer reproduce against the live ledger (measured
2026-09-26: 40 GAPS_REGISTERED / 243 gap + 19 opportunity rows at the time of T5_LEDGER_DRIFT.md,
and the ledger has only grown since — 830+ lines by wave 3). Rather than restate a number that
goes stale on the next census run, both figures are date-stamped as a pre-census-emission
snapshot with an explicit pointer to re-measure from the live ledger. Fails against the pre-fix
text, which had no such date-stamp or pointer.
"""
from __future__ import annotations

import pathlib

L0V3 = pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md"


def test_section_1_1_figure_is_datestamped():
    text = L0V3.read_text(encoding="utf-8")
    assert "gates certified 0/360** (pre-census-emission snapshot" in text


def test_pilot_ledger_figure_is_datestamped_and_points_to_live_ledger():
    text = L0V3.read_text(encoding="utf-8")
    assert "Ledger after five pilots (pre-census-emission snapshot" in text
    assert "does not reproduce against the live ledger" in text
    assert "re-measure from the live ledger" in text


def test_original_raw_figures_still_present_as_historical_record():
    """The point is to date-stamp, not delete — the 30/18/5/35 figures are a real historical
    measurement and must survive verbatim inside the now-qualified sentence."""
    text = L0V3.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    assert "30 gap rows, 18 opportunity rows" in normalized
    assert "NO_BRIEF = 40/40" in normalized
