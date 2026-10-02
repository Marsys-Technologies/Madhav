"""
test_q03_tiers_sensitive_degree.py -- Q03 / SS N-62 honest tiers for the Yogi-system rows of
ga_sensitive_degree (TS-YOGI): `single` on agreement (Pass B is the same sum in integer arcseconds
over the same longitudes, and no classical table is compared -- SS tier rule, S-L1 follow-up; demoted
from the earlier `classical_match`), `divergent_flagged` on disagreement, never `two_pass_verified`.

Spec: AUDIT_L1_TIERS_PER_EMITTER_v1_0.md v1.1 §2.2 / §5.
"""
from __future__ import annotations

import builtins

import pytest

from brahmagyan import verification_tiers as T
from ga_writers import ga_sensitive_degree_writer as sut

_SUN, _MOON = 295.4, 331.2  # Capricorn Sun, Purva Bhadrapada Moon (FORENSIC-consistent)


class _BrokenConn:
    """No L0 reference tables reachable -> the writer's classical fallback lord tables."""

    def cursor(self, *a, **k):
        raise RuntimeError("no DB in this test")


def _rows() -> list[dict]:
    return sut.build_yogi_points_rows(
        "c", "lahiri_chitrapaksha", "b",
        {"Sun": {"longitude_sidereal": _SUN}, "Moon": {"longitude_sidereal": _MOON}},
        _BrokenConn(),
    )


def _tiers(rows) -> set[str]:
    return {r["verification_pass_status"] for r in rows}


def test_yogi_rows_agreeing_paths_are_single():
    rows = _rows()
    assert rows and _tiers(rows) == {T.SINGLE}
    assert not {T.TWO_PASS_VERIFIED, T.CLASSICAL_MATCH} & _tiers(rows)


def test_yogi_pass_b_perturbed_is_divergent_flagged(monkeypatch):
    """The detector can fail: shift Pass B's integer-arcsecond arithmetic (module-level `round`
    is only used by Pass B and the row-value rounding) by 5 arcsec per term."""

    def shifted_round(x, ndigits=None):
        if ndigits is None:
            return builtins.round(x) + 5
        return builtins.round(x, ndigits)

    monkeypatch.setattr(sut, "round", shifted_round, raising=False)
    rows = _rows()
    assert T.DIVERGENT_FLAGGED in _tiers(rows)
    assert T.SINGLE not in {
        r["verification_pass_status"] for r in rows if (r["fact_subject"], r["fact_key"]) == ("YOGI", "point_longitude")
    }


def test_yogi_unconditional_pass_mutant_is_caught(monkeypatch):
    """MUTANT: stamp the passing tier unconditionally. With Pass B perturbed the rows must NOT
    be classical_match, so this mutant fails test_yogi_pass_b_perturbed_is_divergent_flagged;
    here we run the mutant and assert it really does mask the divergence."""

    def shifted_round(x, ndigits=None):
        return builtins.round(x) + 5 if ndigits is None else builtins.round(x, ndigits)

    monkeypatch.setattr(sut, "round", shifted_round, raising=False)
    monkeypatch.setattr(sut, "_yogi_pass_tier", lambda agrees: T.SINGLE)
    assert _tiers(_rows()) == {T.SINGLE}


def test_yogi_tier_mapping_is_exactly_agree_or_diverge():
    assert sut._yogi_pass_tier(True) == T.SINGLE
    assert sut._yogi_pass_tier(False) == T.DIVERGENT_FLAGGED


def test_mutant_yogi_classical_match_return_is_visible(monkeypatch):
    """MUTANT (the pre-ruling behaviour): _yogi_pass_tier returning classical_match on agreement is what
    the single-tier tests above reject."""
    monkeypatch.setattr(sut, "_yogi_pass_tier", lambda agrees: T.CLASSICAL_MATCH if agrees else T.DIVERGENT_FLAGGED)
    assert _tiers(_rows()) == {T.CLASSICAL_MATCH} != {T.SINGLE}
