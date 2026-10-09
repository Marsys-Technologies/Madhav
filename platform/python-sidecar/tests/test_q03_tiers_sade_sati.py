"""
test_q03_tiers_sade_sati.py -- Q03 / SS N-62 honest tiers for ga_sade_sati (TS-SADE).

The six examined keys (cycle_start_iso, cycle_end_iso, duration_days, duration_years on
`sade_sati_cycle`; the same four on `sade_sati_phase`, i.e. phase_start_iso/phase_end_iso/
duration_days/duration_years) are backed ONLY by `two_pass_verify_cycles`, a +/-600 day duration
bound and date-ordering check over the engine's own output. That is a plausibility guard: not a
match against a classical reference table and not a second derivation, so it earns NO tier above
`single` (SS ruling, S-L1 follow-up: demoted from the earlier `classical_match`). A cycle outside
the bound halts the build; the verifier still marks the cycles it examined (an audit record).

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


def test_checked_cycle_examined_keys_are_single_not_classical_match():
    cycles = _cycles()
    assert W.two_pass_verify_cycles(cycles) == []
    assert cycles[0].get(W.CYCLE_INVARIANTS_CHECKED_KEY) is True  # the guard ran and passed
    rows = _emit(cycles[0])
    ex = _examined(rows)
    # 4 cycle keys + 4 phase keys x 3 phases
    assert len(ex) == 4 + 4 * 3
    assert {r["verification_pass_status"] for r in ex} == {T.SINGLE}
    tiers = {r["verification_pass_status"] for r in rows}
    assert not {T.TWO_PASS_VERIFIED, T.CLASSICAL_MATCH} & tiers


def test_unchecked_cycle_is_single_too():
    rows = _emit(_cycles()[0])
    assert {r["verification_pass_status"] for r in _examined(rows)} == {T.SINGLE}


def test_mutant_marker_gated_classical_match_is_caught(monkeypatch):
    """MUTANT (the pre-ruling behaviour): re-introduce a marker-gated classical_match on the examined
    keys. The two tests above fail on it; this one proves the mutant is visible (rows would be
    classical_match after the verifier ran)."""
    real = W._emit_cycle_rows

    def mutant(*a, **k):
        rows = real(*a, **k)
        cy = a[3]
        if cy.get(W.CYCLE_INVARIANTS_CHECKED_KEY):
            for r in rows:
                if (r["fact_category"], r["fact_key"]) in _EXAMINED:
                    r["verification_pass_status"] = T.CLASSICAL_MATCH
        return rows

    monkeypatch.setattr(W, "_emit_cycle_rows", mutant)
    cycles = _cycles()
    W.two_pass_verify_cycles(cycles)
    ex = _examined(W._emit_cycle_rows(CHART_ID, AYA, BUILD, cycles[0], [], dict(_NATAL), AT))
    assert {r["verification_pass_status"] for r in ex} == {T.CLASSICAL_MATCH}


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


# ── summary telemetry flag (CLAUDE.md §N.8): was initialised True before any check ran ───────────


def _run_build(monkeypatch, verifier=None):
    moon = {a: "Aquarius" for a in W.CANONICAL_AYANAMSHAS}
    monkeypatch.setattr(W, "_write_halt_log", lambda *a, **k: None)
    monkeypatch.setattr(W, "_verify_upstream_rows", lambda conn, cid: {"ga3": True})
    monkeypatch.setattr(W, "_read_moon_sign_per_ayanamsha", lambda conn, cid: moon)
    monkeypatch.setattr(W, "_read_moon_pada_per_ayanamsha", lambda conn, cid: {})
    monkeypatch.setattr(W, "_detect_saturn_sign_changes", lambda a, b: list(_SIGN_CHANGES))
    monkeypatch.setattr(W, "_detect_saturn_retrogrades", lambda a, b: [])
    monkeypatch.setattr(W, "_build_static_natal_facts", lambda *a, **k: dict(_NATAL))
    monkeypatch.setattr(W, "_lookup_dasha_lord_at", lambda *a, **k: None)
    monkeypatch.setattr(W, "_lookup_tara_bala_for_saturn_at", lambda *a, **k: None)
    monkeypatch.setattr(W, "_lookup_argala_for_sign", lambda *a, **k: [])
    monkeypatch.setattr(W, "_emit_dhaiya_rows", lambda *a, **k: [])
    monkeypatch.setattr(W, "_insert_rows", lambda conn, rows: len(rows))
    monkeypatch.setattr(W, "_refresh_mv", lambda conn: None)
    monkeypatch.setattr(W, "ayanamshas_for_chart", lambda conn, cid: list(W.CANONICAL_AYANAMSHAS))   # opaque conn: the default set (ONE_AYANAMSHA)
    if verifier is not None:
        monkeypatch.setattr(W, "two_pass_verify_cycles", verifier)
    return W.build_ga_sade_sati("chart-q03-not-canonical", "b", conn=object())


def test_build_summary_two_pass_flag_is_null_even_after_the_real_check_passes(monkeypatch):
    summary = _run_build(monkeypatch)
    assert summary["total_chart_facts_rows"] > 0  # the real two_pass_verify_cycles ran and passed
    assert summary["two_pass_verified"] is None  # plausibility guard: earns no tier above single, not this flag
    assert summary["divergent_flagged"] is False  # a real detector result: it would be True before the raise


def test_build_halts_on_a_divergence_instead_of_returning_a_true_flag(monkeypatch):
    with pytest.raises(RuntimeError, match="TWO-PASS DIVERGENCE"):
        _run_build(monkeypatch, verifier=lambda cycles: ["forced divergence"])
