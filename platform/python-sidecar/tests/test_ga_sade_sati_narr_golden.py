"""
tests/test_ga_sade_sati_narr_golden.py -- Narr golden-value test for ga_sade_sati

``chart_facts.citation_human`` is narration: the sentence a reader sees for a Sade Sati
cycle / phase fact (CLAUDE.md section N.7 item 5: verified fact != verified prose).

What this pins, on the pure function ``_emit_cycle_rows`` (no database, hand-built cycle
dict, hand-built natal_facts): for a Moon-in-Aquarius cycle (12th = Capricorn, janma =
Aquarius, 2nd = Pisces) the cycle-level and phase-level sentences state the cycle start
date, the Saturn entry sign, the 12H relation to the natal Moon sign, the duration, and
the Saturn sign and dignity in each phase. Saturn in Capricorn is own-sign (Capricorn is
a Saturn-ruled sign), and Saturn in Pisces is a neutral sign (Jupiter's sign; Saturn is
neutral to Jupiter).

The dates / durations are fixture values chosen to be internally consistent; they are
not claimed to be the true ephemeris.
"""
from __future__ import annotations

from datetime import datetime, timezone

from ga_writers.ga_sade_sati_writer import _emit_cycle_rows

CYCLE = {
    "cycle_num": 1,
    "cycle_id": "CYCLE_1",
    "moon_sign": "Aquarius",
    "vis_sign": "Capricorn",
    "jan_sign": "Aquarius",
    "anu_sign": "Pisces",
    "vishakha_entry": datetime(2020, 1, 24, 6, 0, tzinfo=timezone.utc),
    "janma_entry": datetime(2023, 1, 17, 18, 0, tzinfo=timezone.utc),
    "anumukha_entry": datetime(2025, 3, 29, 12, 0, tzinfo=timezone.utc),
    "cycle_end": datetime(2027, 5, 21, 6, 0, tzinfo=timezone.utc),
    "cycle_type": "full",
    "duration_days": 2687.0,
}


def test_sade_sati_citation_human_cycle_and_phase_sentences() -> None:
    rows = _emit_cycle_rows(
        "chart-fixture", "lahiri", "build-fixture", CYCLE, [], {},
        "2026-01-01T00:00:00+00:00",
    )
    by_key = {(r["fact_category"], r["fact_subject"], r["fact_key"]): r for r in rows}

    assert by_key[("sade_sati_cycle", "CYCLE_1", "cycle_start_iso")]["citation_human"] == (
        "Sade Sati CYCLE_1 starts 2020-01-24 (Saturn enters Capricorn, "
        "12H from natal Moon in Aquarius, lahiri)."
    )
    assert by_key[("sade_sati_cycle", "CYCLE_1", "duration_years")]["citation_human"] == (
        "Sade Sati CYCLE_1 duration: 7.36 years (lahiri)."
    )

    assert by_key[("sade_sati_phase", "CYCLE_1.VISHAKHA", "saturn_dignity")]["citation_human"] == (
        "Saturn dignity during CYCLE_1 VISHAKHA: own (lahiri)."
    )
    assert by_key[("sade_sati_phase", "CYCLE_1.ANUMUKHA", "saturn_sign")]["citation_human"] == (
        "Saturn sign during CYCLE_1 ANUMUKHA: Pisces (lahiri)."
    )
