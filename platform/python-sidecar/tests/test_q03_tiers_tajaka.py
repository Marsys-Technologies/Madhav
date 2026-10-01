"""
test_q03_tiers_tajaka.py -- Q03 / SS N-62 honest tiers for `l1_tajik_varsha_year_lords` (TD-TAJ).

The three checks behind a varsha row (`muntha_ok`: the same +1-per-year arithmetic; `year_lord_ok`:
two winners are non-empty; `sr_ok`: the solar-return root-finder's own residual) are relay-grade
invariants, not an independent re-derivation of the year lord -> `classical_match`, never
`two_pass_verified`; a failed check -> `divergent_flagged` (the build halts on it).

Spec: AUDIT_L1_TIERS_PER_EMITTER_v1_0.md v1.1 §3 / §5.
"""
from __future__ import annotations

import itertools
from datetime import datetime
from unittest.mock import patch

import pytest

from brahmagyan import verification_tiers as T
from ga_writers import ga_tajaka_writer as W

_BP = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.27, "longitude_deg": 85.84,
       "tz_offset_hours": 5.5}


@pytest.mark.parametrize("muntha,year_lord,sr", list(itertools.product([True, False], repeat=3)))
def test_varsha_verification_truth_table(muntha, year_lord, sr):
    got = W._varsha_verification(muntha, year_lord, sr)
    assert got == (T.CLASSICAL_MATCH if (muntha and year_lord and sr) else T.DIVERGENT_FLAGGED)
    assert got != T.TWO_PASS_VERIFIED


def _annual_chart():
    names = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    return {
        "ascendant": {"sign_id": 3, "longitude_deg": 75.0},
        "grahas": [{"name": n, "longitude": 10.0 + 33.0 * i, "house": 1 + (i % 12)}
                   for i, n in enumerate(names)],
    }


def _row(sr_audit: dict, natal_sun_long: float = 291.0) -> dict:
    natal = {"ascendant": {"sign_id": 1, "degree_in_sign": 5.0}}
    inst = datetime(2026, 2, 4, 10, 43, 0)
    with patch.object(W, "_solar_return", return_value=(inst, sr_audit)), \
         patch.object(W, "compute_chart", return_value=_annual_chart()), \
         patch.object(W, "_read_trirashipathi", return_value="Jupiter"), \
         patch.object(W, "_tajik_yogas", return_value=[]):
        return W._compute_one(None, "c", "lahiri_chitrapaksha", "lahiri", 43, natal,
                              natal_sun_long, "b", birth=_BP)


_GOOD_SR = {"converged": True, "diff_deg": 0.0001}


def test_compute_one_converged_solar_return_is_classical_match():
    row = _row(_GOOD_SR)
    assert row["verification_pass_status"] == T.CLASSICAL_MATCH
    assert row["ephemeris_audit_jsonb"]["muntha_two_pass_match"] is True


def test_compute_one_unconverged_solar_return_is_divergent_flagged():
    row = _row({"converged": False, "diff_deg": None})
    assert row["verification_pass_status"] == T.DIVERGENT_FLAGGED


def test_compute_one_solar_return_residual_beyond_tolerance_is_divergent_flagged():
    row = _row({"converged": True, "diff_deg": 5.0})
    assert row["verification_pass_status"] == T.DIVERGENT_FLAGGED


def test_compute_one_tier_comes_from_the_checks_not_a_constant(monkeypatch):
    """MUTANT (hard-coded tier return): with the helper replaced by a constant, an unconverged
    solar return would still read classical_match -- this asserts the mutant masks the failure
    (so the unconverged test above would FAIL on it)."""
    monkeypatch.setattr(W, "_varsha_verification", lambda *a: T.CLASSICAL_MATCH)
    assert _row({"converged": False, "diff_deg": None})["verification_pass_status"] == T.CLASSICAL_MATCH
