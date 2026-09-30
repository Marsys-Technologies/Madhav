"""
Tests for W2.3 engine-level wiring parity: tara_bala modifier in production lambda.

Acceptance criteria (engine-level), REWORKED under S-04 / O-P6-TARA
(ASTRA_REVIEW_A5_4 P1-6 — tārā is a P6 testimony operator):
  T1: when _W23_TARA_BALA_ENABLED is True AND a non-janma tara fires, the
      term_breakdown carries a NON-SCORING tara_annotation (class, name,
      would-be modifier) and raw_lambda is BIT-IDENTICAL to the disabled run.
  T2: when disabled, the annotation is an honest skip (would-be 1.0).
  T3: a favourable tārā (would-be 1.20) is likewise never applied.
  T4: the formula string still names tara_modifier (N-16 wiring trace);
      its value in the product is 1.0.

Strategy: call _evaluate_single_from_context directly with a minimal ClassContext
that has natal_facts populated (Moon longitude in nak 1), then assert on the
IntensityResult fields. We monkeypatch:
  - _W23_TARA_BALA_ENABLED in engine module for AC-E2
  - swisseph.calc_ut to return a controlled Moon longitude (nak 7 = naidhana,
    modifier 0.70) so the tara modifier is deterministic and != 1.0 for AC-E1.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import patch, MagicMock

import pytest

import services.gochara_v3.engine as engine_module
from services.gochara_v3.engine import _evaluate_single_from_context
from services.gochara_v3.context import ClassContext, NatalFacts


# ---------------------------------------------------------------------------
# Fixtures: minimal ClassContext with natal Moon in nak 1 (Ashwini, 0–13.33°)
# ---------------------------------------------------------------------------

def _build_minimal_context(*, moon_lon_deg: float = 5.0) -> ClassContext:
    """Build a minimal ClassContext with Moon at moon_lon_deg, zero targets.

    promise=0.0, permission irrelevant (will be forced via pre-fetched data),
    no dasha periods, no AV rows. Sufficient to exercise the tara_bala path.
    """
    natal = NatalFacts(
        # DISCLOSURE (Pravāha A5.4 tara_key, #5): pre-repair this fixture used
        # the title-case 'Moon' key, matching the mechanism's buggy lookup —
        # the parity test passed while production (canonical system-A subject
        # codes from chart_facts.fact_subject) never fired. Keys corrected to
        # the canonical 'MOON'.
        graha_longitudes={"MOON": moon_lon_deg},
        graha_signs={"MOON": "Aries"},
        lagna_sign=None,
        lagna_longitude=None,
    )
    return ClassContext(
        chart_id="test-chart-tara-parity",
        event_class="career",
        resonance_targets=(),
        promise=0.5,        # non-zero so raw_lambda can show modifier effect
        promise_detail={},
        dasha_periods=(),
        relevant_grahas=frozenset(),
        relevant_signs=frozenset(),
        temporal_shape="point",
        valence="neutral",
        is_adverse=False,
        beta_e=0.45,
        weight_by_target_ref={},
        natal_facts=natal,
        av_gate_rows=(),
        sade_sati_phases=(),
        vedha_rows=(),
    )


# ---------------------------------------------------------------------------
# Fake swe object that provides calc_ut returning Moon at a given longitude
# ---------------------------------------------------------------------------

class _FakeSwe:
    """Minimal swe stub for _evaluate_single_from_context.

    - calc_ut: returns a controlled Moon longitude so the tara nak is deterministic.
    - Other attributes delegate to real swisseph so primitives work.
    """
    def __init__(self, moon_transit_lon_deg: float):
        self._moon_lon = moon_transit_lon_deg
        import swisseph as _real_swe
        self._swe = _real_swe
        # Expose constants from real swe
        self.MOON = _real_swe.MOON
        self.SUN = _real_swe.SUN
        self.FLG_SIDEREAL = _real_swe.FLG_SIDEREAL
        self.FLG_SPEED = _real_swe.FLG_SPEED
        self.NODBIT_MEAN = _real_swe.NODBIT_MEAN
        self.TRUE_NODE = _real_swe.TRUE_NODE
        self.MEAN_NODE = _real_swe.MEAN_NODE
        self.MARS = _real_swe.MARS
        self.MERCURY = _real_swe.MERCURY
        self.JUPITER = _real_swe.JUPITER
        self.VENUS = _real_swe.VENUS
        self.SATURN = _real_swe.SATURN
        self.SE_CALC_SET = getattr(_real_swe, 'SE_CALC_SET', 0)

    def calc_ut(self, jd, body, flags=0):
        # Return controlled Moon longitude when asked for Moon; delegate rest
        if body == self._swe.MOON:
            return ([self._moon_lon, 0.0, 1.0, 0.0, 0.0, 0.0], 0)
        return self._swe.calc_ut(jd, body, flags)

    def __getattr__(self, name):
        return getattr(self._swe, name)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _run_single(swe_stub, context: ClassContext) -> object:
    """Call _evaluate_single_from_context with v1_parity_mode=False (W1.1 path)."""
    T_JD = 2460000.0  # arbitrary JD
    return _evaluate_single_from_context(
        swe_stub,
        context,
        T_JD,
        targets=[],  # no targets: promise drives raw_lambda
        v1_parity_mode=False,
        source="test_parity",
    )


# ---------------------------------------------------------------------------
# S-04 / O-P6-TARA (ASTRA_REVIEW_A5_4 P1-6): tārā is P6 TESTIMONY. The engine
# records the mechanism's class and would-be modifier as a non-scoring
# annotation; the λ product receives 1.0. The pre-rework AC-E1 asserted the
# prohibited weighting (raw_lambda × 0.70) — replaced.
# ---------------------------------------------------------------------------

def test_tara_annotation_present_and_lambda_unweighted():
    """Natal Moon 5° (nak 1), transit Moon 85° (nak 7) ⇒ position 7
    (naidhana). The annotation must carry the class and the would-be 0.70;
    tara_modifier in the product must be 1.0; raw_lambda must be
    BIT-IDENTICAL to the mechanism-disabled evaluation (O-RR-7 shape).
    Mutation caught: any λ delta from the tārā term."""
    ctx = _build_minimal_context(moon_lon_deg=5.0)
    swe_stub = _FakeSwe(moon_transit_lon_deg=85.0)

    with patch.object(engine_module, "_W23_TARA_BALA_ENABLED", True):
        with_tara = _run_single(swe_stub, ctx)
    with patch.object(engine_module, "_W23_TARA_BALA_ENABLED", False):
        without = _run_single(swe_stub, ctx)

    tb = with_tara.term_breakdown
    ann = tb["tara_annotation"]
    assert ann["scoring"] is False and ann["operator_role"] == "testimony"
    assert ann["tara_position"] == 7 and ann["tara_name"] == "naidhana"
    assert abs(ann["would_be_modifier"] - 0.70) < 1e-6
    assert tb["tara_modifier"] == 1.0
    assert with_tara.raw_lambda == without.raw_lambda  # bitwise
    assert with_tara.x_t_detail["tara_detail"]["scoring"] is False
    assert with_tara.x_t_detail["tara_modifier"] == 1.0


def test_disabled_mechanism_annotation_is_a_skip_not_a_weight():
    ctx = _build_minimal_context(moon_lon_deg=5.0)
    swe_stub = _FakeSwe(moon_transit_lon_deg=85.0)
    with patch.object(engine_module, "_W23_TARA_BALA_ENABLED", False):
        result = _run_single(swe_stub, ctx)
    tb = result.term_breakdown
    assert tb["tara_modifier"] == 1.0
    assert tb["tara_annotation"]["skipped"] is True
    assert tb["tara_annotation"]["would_be_modifier"] == 1.0


def test_favourable_tara_never_amplifies_lambda():
    """paramamitra (position 9, would-be 1.20) — the amplification is
    recorded, never applied."""
    ctx = _build_minimal_context(moon_lon_deg=5.0)           # nak 1
    swe_stub = _FakeSwe(moon_transit_lon_deg=110.0)          # nak 9 (106.67–120)
    with patch.object(engine_module, "_W23_TARA_BALA_ENABLED", True):
        result = _run_single(swe_stub, ctx)
    with patch.object(engine_module, "_W23_TARA_BALA_ENABLED", False):
        baseline = _run_single(swe_stub, ctx)
    ann = result.term_breakdown["tara_annotation"]
    assert ann["tara_position"] == 9 and ann["would_be_modifier"] > 1.0
    assert result.raw_lambda == baseline.raw_lambda


def test_formula_string_still_names_the_term_and_the_wiring_is_annotation():
    """The N-16 wiring detector keeps seeing `tara_modifier` in the product
    line (formula string); its value is pinned to 1.0 by S-04."""
    ctx = _build_minimal_context(moon_lon_deg=5.0)
    swe_stub = _FakeSwe(moon_transit_lon_deg=85.0)
    with patch.object(engine_module, "_W23_TARA_BALA_ENABLED", True):
        result = _run_single(swe_stub, ctx)
    assert "tara_modifier" in result.x_t_detail.get("formula", "")
    assert result.term_breakdown["tara_modifier"] == 1.0
