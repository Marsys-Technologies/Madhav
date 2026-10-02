"""
test_ga_condition_dasha_cuts.py -- SS ruling 2026-10-02 (band/X2 lane, decision b).

`_PEAK_CONDITION_THRESHOLD` (0.65) and `_WEAK_CONDITION_THRESHOLD` (0.35), the cut points that
classify a graha's mahadasha periods as peak / weak in ga_condition, moved into
`ga_writers/ga_condition_bands.py` as a SEPARATELY named table, `DASHA_PERIOD_CONDITION_CUTS`:
values unchanged, a project convention with provenance `unsourced`, a different concept from the
three-band label (0.4 / 0.7) and NOT merged into it.

This file pins (1) the values, provenance and separateness, (2) that ga_condition reads them from
there, and (3) that NO OUTPUT CHANGES: over a fine score sweep (edges included) the classification
the writer produces equals the classification of the previous hard-coded 0.65 / 0.35 rule.

DB-free: a fake cursor returns one canned mahadasha row.
"""
from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_condition_bands as bands  # noqa: E402
from ga_writers import ga_condition_writer as w  # noqa: E402


class _Cur:
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a, **k):
        pass

    def fetchall(self):
        return self._rows


class _Conn:
    def __init__(self, rows):
        self._rows = rows

    def cursor(self, *a, **k):
        return _Cur(self._rows)


_ROWS = [(
    "11111111-1111-4111-8111-111111111111", "vimshottari", "lahiri_chitrapaksha", "build-1", 1, "Saturn",
    datetime(2000, 1, 1, tzinfo=timezone.utc), datetime(2019, 1, 1, tzinfo=timezone.utc),
)]


def _classify_via_writer(score):
    peak, weak = w._load_dasha_periods(
        _Conn(_ROWS), "482012f1-710e-4a25-994a-93821f5871aa", "Saturn",
        "lahiri_chitrapaksha", "build-1", condition_score=score, dignity_d1="exalted",
    )
    return ("peak" if peak else "weak" if weak else "none"), peak, weak


def _classify_old_rule(score):
    """The previous in-writer rule, with its hard-coded literals."""
    if score is None:
        return "none"
    if score >= 0.65:
        return "peak"
    if score <= 0.35:
        return "weak"
    return "none"


def test_values_provenance_and_name_are_pinned():
    cuts = bands.DASHA_PERIOD_CONDITION_CUTS
    assert cuts.peak_at_or_above == 0.65
    assert cuts.weak_at_or_below == 0.35
    assert cuts.provenance == "unsourced"


def test_it_is_a_separate_concept_from_the_three_band_label():
    cuts = bands.DASHA_PERIOD_CONDITION_CUTS
    assert cuts is not bands.SCORE_BANDS and not isinstance(cuts, tuple)
    assert {cuts.peak_at_or_above, cuts.weak_at_or_below}.isdisjoint({bands.CUT_LOW_MID, bands.CUT_MID_HIGH})
    # the band table is unchanged by the move
    assert (bands.CUT_LOW_MID, bands.CUT_MID_HIGH) == (0.4, 0.7)


def test_ga_condition_reads_the_cuts_from_the_bands_module():
    assert w.DASHA_PERIOD_CONDITION_CUTS is bands.DASHA_PERIOD_CONDITION_CUTS
    assert w._PEAK_CONDITION_THRESHOLD == bands.DASHA_PERIOD_CONDITION_CUTS.peak_at_or_above
    assert w._WEAK_CONDITION_THRESHOLD == bands.DASHA_PERIOD_CONDITION_CUTS.weak_at_or_below


def test_no_output_change_old_and_new_constants_classify_every_score_identically():
    scores = [i / 2000.0 for i in range(0, 2001)] + [0.35, 0.3500001, 0.3499999, 0.65, 0.6500001, 0.6499999, None]
    for s in scores:
        assert _classify_via_writer(s)[0] == _classify_old_rule(s), s


def test_period_payloads_are_unchanged_at_the_edges():
    kind, peak, weak = _classify_via_writer(0.65)
    assert kind == "peak" and weak is None
    assert peak[0]["dasha_label"] == "Saturn Mahadasha" and "strong" in peak[0]["reason"]
    kind, peak, weak = _classify_via_writer(0.35)
    assert kind == "weak" and peak is None
    assert "weak" in weak[0]["reason"]
    assert _classify_via_writer(0.5)[0] == "none"
