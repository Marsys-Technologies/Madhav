"""
test_q03_tiers_sade_sati.py -- Q03 / SS N-62 honest tiers for ga_sade_sati (TS-SADE).

The six examined keys (cycle_start_iso, cycle_end_iso, duration_days, duration_years on
`sade_sati_cycle`; the same four on `sade_sati_phase`, i.e. phase_start_iso/phase_end_iso/
duration_days/duration_years) are backed ONLY by `two_pass_verify_cycles`, a +/-600 day duration
bound and date-ordering check over the engine's own output. That is a bounds/ordering invariant,
not an independent re-derivation, so the tier is `classical_match`, and only when the check
actually ran and passed for that cycle (the verifier marks the cycle it examined).

Spec: AUDIT_L1_TIERS_PER_EMITTER_v1_0.md v1.1 §2.2 / §5.
"""
from __future__ import annotations

import sys
import pathlib
from datetime import datetime, timezone

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from brahmagyan import verification_tiers as T
from ga_writers import ga_sade_sati_writer as W

CHART_ID = W.CANONICAL_CHART_ID
AYA = "lahiri_chitrapaksha"
BUILD = "q03-build"
AT = "2026-10-02T00:00:00+00:00"


def _dt(y, m=1, d=1):
    return datetime(y, m, d, tzinfo=timezone.utc)


# Saturn: Sagittarius->Capricorn (12H from an Aquarius Moon), Capricorn->Aquarius, Aquarius->Pisces,
# Pisces->Aries : one full Sade Sati (2017-10-26 .. 2025-03-29).
_SIGN_CHANGES = [
    {"date_utc": _dt(2017, 10, 26), "sign_from": "Sagittarius", "sign_to": "Capricorn"},
    {"date_utc": _dt(2020, 1, 23), "sign_from": "Capricorn", "sign_to": "Aquarius"},
    {"date_utc": _dt(2022, 4, 28), "sign_from": "Aquarius", "sign_to": "Pisces"},
    {"date_utc": _dt(2025, 3, 29), "sign_from": "Pisces", "sign_to": "Aries"},
]

_NATAL = {
    "moon_pada": 4, "saturn_yoga_karaka": False, "natal_saturn_aspects_natal_moon": False,
    "saturn_moon_parivartana": False, "moon_sign_lord_strong": False,
    "jupiter_aspects_saturn_during_cycle": False, "d10_karya_bhava_activation_flag": False,
    "d10_karya_activation_facts": [], "argala_during_period": [],
    "tara_bala_at_janma_peak": "PENDING_GA4_LOOKUP", "mars_aspect_during_period": False,
    "jupiter_aspect_during_period": False, "saturn_rahu_axis_flag": False,
    "eclipse_during_period": False, "concurrent_saturn_return": False,
    "saturn_vargottama_natal": False,
}

_EXAMINED = {
    ("sade_sati_cycle", "cycle_start_iso"), ("sade_sati_cycle", "cycle_end_iso"),
    ("sade_sati_cycle", "duration_days"), ("sade_sati_cycle", "duration_years"),
    ("sade_sati_phase", "phase_start_iso"), ("sade_sati_phase", "phase_end_iso"),
    ("sade_sati_phase", "duration_days"), ("sade_sati_phase", "duration_years"),
}


def _cycles():
    cycles = W.build_sade_sati_cycles("Aquarius", _SIGN_CHANGES)
    assert len(cycles) == 1
    return cycles


def _emit(cycle) -> list[dict]:
    return W._emit_cycle_rows(CHART_ID, AYA, BUILD, cycle, [], dict(_NATAL), AT)


def _examined(rows):
    return [r for r in rows if (r["fact_category"], r["fact_key"]) in _EXAMINED]


def test_checked_cycle_stamps_classical_match_on_exactly_the_examined_keys():
    cycles = _cycles()
    assert W.two_pass_verify_cycles(cycles) == []
    rows = _emit(cycles[0])
    ex = _examined(rows)
    assert ex and {r["verification_pass_status"] for r in ex} == {T.CLASSICAL_MATCH}
    # 4 cycle keys + 4 phase keys x 3 phases
    assert len(ex) == 4 + 4 * 3
    others = [r for r in rows if (r["fact_category"], r["fact_key"]) not in _EXAMINED]
    assert others
    assert T.TWO_PASS_VERIFIED not in {r["verification_pass_status"] for r in rows}
    assert T.CLASSICAL_MATCH not in {r["verification_pass_status"] for r in others}


def test_unchecked_cycle_never_gets_the_tier():
    """The emitter alone cannot stamp the tier: a cycle the verifier did not examine is `single`."""
    rows = _emit(_cycles()[0])
    assert {r["verification_pass_status"] for r in _examined(rows)} == {T.SINGLE}


def test_stubbed_verifier_mutant_drops_the_six_keys_to_single(monkeypatch):
    """MUTANT: `two_pass_verify_cycles` stubbed to return [] without running. The marker is never
    set, so the examined keys must be `single` (a tier stamped WITHOUT the check having run)."""
    monkeypatch.setattr(W, "two_pass_verify_cycles", lambda cycles: [])
    cycles = _cycles()
    assert W.two_pass_verify_cycles(cycles) == []  # the stub "passes"
    assert {r["verification_pass_status"] for r in _examined(_emit(cycles[0]))} == {T.SINGLE}


def test_900_day_cycle_is_a_divergence_and_is_not_marked():
    cy = _cycles()[0]
    cy["duration_days"] = 900.0  # expected ~2737 +/- 600
    divs = W.two_pass_verify_cycles([cy])
    assert divs and "duration" in divs[0]
    assert W.CYCLE_INVARIANTS_CHECKED_KEY not in cy
    assert {r["verification_pass_status"] for r in _examined(_emit(cy))} == {T.SINGLE}


def test_janma_not_after_vishakha_is_a_divergence_and_is_not_marked():
    cy = _cycles()[0]
    cy["janma_entry"] = cy["vishakha_entry"]
    divs = W.two_pass_verify_cycles([cy])
    assert any("janma_entry" in d for d in divs)
    assert W.CYCLE_INVARIANTS_CHECKED_KEY not in cy


def test_marker_is_per_cycle_and_reset_on_recheck():
    good, bad = _cycles()[0], _cycles()[0]
    bad["duration_days"] = 900.0
    W.two_pass_verify_cycles([good, bad])
    assert good.get(W.CYCLE_INVARIANTS_CHECKED_KEY) is True
    assert W.CYCLE_INVARIANTS_CHECKED_KEY not in bad
    good["duration_days"] = 900.0  # a re-check of a now-bad cycle must clear a stale marker
    W.two_pass_verify_cycles([good])
    assert W.CYCLE_INVARIANTS_CHECKED_KEY not in good
