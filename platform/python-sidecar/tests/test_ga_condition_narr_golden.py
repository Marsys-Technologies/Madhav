"""
tests/test_ga_condition_narr_golden.py -- Narr golden-value test for ga_condition

``chart_facts.citation_human`` is narration: the sentence a reader sees for a per-varga
Deeptaadi avastha fact (CLAUDE.md section N.7 item 5: verified fact != verified prose).

What this pins, on ``_build_per_varga_avastha_rows`` over a FAKE connection (no database):
a Sun that is Exalted in D9 is classically the Deepta ("radiant") state (Phaladeepika:
exalted or own sign = deepta), so the sentence must name the graha, the avastha family,
the varga, and the state "deepta", and a graha Debilitated in D9 is the Khala state.

Not pinned here (deliberately, see the lane report): the Baladi rule in this builder is
sign-parity blind (it reads only degree_in_sign), which the classical odd/even-sign
reversal contradicts, so it is not enshrined.
"""
from __future__ import annotations

from ga_writers.ga_condition_writer import _build_per_varga_avastha_rows


class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeConn:
    """Answers the single chart_divisionals SELECT the builder issues."""

    def __init__(self, rows):
        self._rows = rows

    def execute(self, *_args, **_kwargs):
        return _FakeCursor(self._rows)


def test_per_varga_deeptaadi_citation_human_names_graha_varga_and_state() -> None:
    divisional_rows = [
        ("Sun", "D9", "dignity", "Exalted", None),
        ("Saturn", "D9", "dignity", "Debilitated", None),
    ]
    rows = _build_per_varga_avastha_rows(
        _FakeConn(divisional_rows), "chart-fixture", "build-fixture", "lahiri",
        "2026-01-01T00:00:00+00:00", "test-eng",
    )
    deeptaadi = {
        r["fact_subject"]: r for r in rows
        if r["fact_category"] == "graha_avastha_deeptaadi_per_varga"
    }

    assert deeptaadi["SUN"]["citation_human"] == "Sun deeptaadi avastha in D9: deepta"
    assert deeptaadi["SAT"]["citation_human"] == "Saturn deeptaadi avastha in D9: khala"
