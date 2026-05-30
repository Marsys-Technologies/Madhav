"""
Tests for pipeline.writers.salience — G4-01 (minimum 20 tests).
"""
import pytest
from pipeline.writers.salience import (
    SALIENCE_FORMULA_VERSION,
    deterministic_strength,
    verification_certainty,
    computed_salience,
)


# ── SALIENCE_FORMULA_VERSION ──────────────────────────────────────────────────

def test_version_string():
    assert SALIENCE_FORMULA_VERSION == "v1"


# ── deterministic_strength ────────────────────────────────────────────────────

def test_det_strength_all_ones():
    assert deterministic_strength(1.0, 1.0, 1.0) == pytest.approx(1.0)


def test_det_strength_all_zeros():
    assert deterministic_strength(0.0, 0.0, 0.0) == pytest.approx(0.0)


def test_det_strength_weights():
    # 0.4*1 + 0.3*0 + 0.3*0 = 0.4
    assert deterministic_strength(1.0, 0.0, 0.0) == pytest.approx(0.4)
    # 0.4*0 + 0.3*1 + 0.3*0 = 0.3
    assert deterministic_strength(0.0, 1.0, 0.0) == pytest.approx(0.3)
    # 0.4*0 + 0.3*0 + 0.3*1 = 0.3
    assert deterministic_strength(0.0, 0.0, 1.0) == pytest.approx(0.3)


def test_det_strength_mid():
    result = deterministic_strength(0.5, 0.5, 0.5)
    assert result == pytest.approx(0.5)


def test_det_strength_clamp_above():
    # values > 1.0 are clamped to 1.0
    result = deterministic_strength(2.0, 2.0, 2.0)
    assert result == pytest.approx(1.0)


def test_det_strength_clamp_below():
    # values < 0.0 are clamped to 0.0
    result = deterministic_strength(-1.0, -1.0, -1.0)
    assert result == pytest.approx(0.0)


def test_det_strength_returns_float():
    result = deterministic_strength(0.5, 0.6, 0.7)
    assert isinstance(result, float)


def test_det_strength_range():
    for orb in [0.0, 0.25, 0.5, 0.75, 1.0]:
        for shad in [0.0, 0.5, 1.0]:
            for dig in [0.0, 0.5, 1.0]:
                result = deterministic_strength(orb, shad, dig)
                assert 0.0 <= result <= 1.0


# ── verification_certainty ────────────────────────────────────────────────────

def test_vc_zero_sources():
    assert verification_certainty(0) == pytest.approx(0.25)


def test_vc_negative_sources():
    assert verification_certainty(-5) == pytest.approx(0.25)


def test_vc_one_source():
    assert verification_certainty(1) == pytest.approx(0.5)


def test_vc_two_sources():
    assert verification_certainty(2) == pytest.approx(0.75)


def test_vc_three_sources():
    assert verification_certainty(3) == pytest.approx(0.875)


def test_vc_four_sources():
    assert verification_certainty(4) == pytest.approx(0.9375)


def test_vc_asymptotic():
    # Should get progressively closer to 1.0 but never reach it
    prev = verification_certainty(1)
    for n in range(2, 10):
        curr = verification_certainty(n)
        assert curr > prev
        assert curr < 1.0
        prev = curr


def test_vc_returns_float():
    assert isinstance(verification_certainty(1), float)


# ── computed_salience ─────────────────────────────────────────────────────────

def test_cs_defaults():
    # base = 0.5*0.5 + 0.3*0.5 = 0.4; mods = 0.1*0.5 + 0.05*0.5 + 0.05*0.5 = 0.1
    result = computed_salience(0.5, 0.5)
    assert result == pytest.approx(0.5)


def test_cs_max_output_capped_at_one():
    result = computed_salience(1.0, 1.0, 1.0, 1.0, 1.0)
    assert result == pytest.approx(1.0)


def test_cs_min_output():
    result = computed_salience(0.0, 0.0, 0.0, 0.0, 0.0)
    assert result == pytest.approx(0.0)


def test_cs_range_all_inputs():
    for ds in [0.0, 0.5, 1.0]:
        for vc in [0.0, 0.5, 1.0]:
            result = computed_salience(ds, vc)
            assert 0.0 <= result <= 1.0


def test_cs_dasha_proximity_effect():
    low = computed_salience(0.5, 0.5, dasha_proximity=0.0)
    high = computed_salience(0.5, 0.5, dasha_proximity=1.0)
    assert high > low
    assert high - low == pytest.approx(0.1)


def test_cs_house_weight_effect():
    low = computed_salience(0.5, 0.5, house_weight=0.0)
    high = computed_salience(0.5, 0.5, house_weight=1.0)
    assert high - low == pytest.approx(0.05)


def test_cs_ashtakavarga_effect():
    low = computed_salience(0.5, 0.5, ashtakavarga_support=0.0)
    high = computed_salience(0.5, 0.5, ashtakavarga_support=1.0)
    assert high - low == pytest.approx(0.05)


def test_cs_returns_float():
    result = computed_salience(0.3, 0.7)
    assert isinstance(result, float)


def test_cs_deterministic_dominates():
    # 0.5 weight on det_str vs 0.3 on ver_cert
    r1 = computed_salience(1.0, 0.0, 0.0, 0.0, 0.0)
    r2 = computed_salience(0.0, 1.0, 0.0, 0.0, 0.0)
    assert r1 > r2


def test_cs_full_formula():
    # Manual: base=0.5*0.8+0.3*0.6=0.58, mods=0.1*0.9+0.05*0.7+0.05*0.4=0.09+0.035+0.02=0.145
    result = computed_salience(0.8, 0.6, 0.9, 0.7, 0.4)
    assert result == pytest.approx(min(1.0, 0.58 + 0.145), rel=1e-5)
