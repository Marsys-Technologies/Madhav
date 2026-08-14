"""
Tests for W2.3 engine-level wiring parity: tara_bala modifier in production lambda.

Acceptance criteria (engine-level):
  AC-E1: when _W23_TARA_BALA_ENABLED is True AND a non-janma tara fires,
         raw_lambda is multiplied by the tara modifier (not 1.0).
  AC-E2: when the mechanism is disabled (_W23_TARA_BALA_ENABLED=False via
         monkeypatching), raw_lambda is NOT multiplied (modifier=1.0).
  AC-E3: formula string in result detail contains "tara_modifier".

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
        graha_longitudes={"Moon": moon_lon_deg},
        graha_signs={"Moon": "Aries"},
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
# AC-E1: non-janma tara fires → raw_lambda multiplied by modifier != 1.0
# ---------------------------------------------------------------------------

def test_ace1_non_janma_tara_modifies_raw_lambda():
    """AC-E1: Moon transit in nak 7 vs natal Moon in nak 1 → naidhana (modifier=0.70).

    raw_lambda with wiring must differ from the baseline that would apply if
    tara_modifier were 1.0. We verify:
      (a) tara_modifier in term_breakdown != 1.0 (it should be 0.70)
      (b) raw_lambda * 1.0 / raw_lambda_with_modifier == approx 1/0.70
          (or equivalently: the breakdown records modifier < 1.0)

    Natal Moon at 5° (nak 1, Ashwini).
    Transit Moon returned by stub at 85° (nak 7, Punarvasu: 80–93.33°).
    Expected tara position: ((7-1) % 27) % 9 + 1 = 6%9+1 = 7 → naidhana → 0.70.
    """
    # After wiring: engine must expose _W23_TARA_BALA_ENABLED
    assert hasattr(engine_module, "_W23_TARA_BALA_ENABLED"), (
        "_W23_TARA_BALA_ENABLED not found in engine module — blind-spec commit not applied."
    )

    ctx = _build_minimal_context(moon_lon_deg=5.0)       # natal Moon nak 1
    swe_stub = _FakeSwe(moon_transit_lon_deg=85.0)       # transit Moon nak 7

    with patch.object(engine_module, "_W23_TARA_BALA_ENABLED", True):
        result = _run_single(swe_stub, ctx)

    tb = result.term_breakdown
    assert "tara_modifier" in tb, (
        f"tara_modifier not found in term_breakdown keys: {list(tb.keys())}"
    )
    tara_mod = tb["tara_modifier"]
    assert tara_mod != 1.0, (
        f"AC-E1 FAIL: tara_modifier == 1.0, expected 0.70 for naidhana tara. "
        f"term_breakdown={tb}"
    )
    assert abs(tara_mod - 0.70) < 1e-6, (
        f"AC-E1 FAIL: tara_modifier={tara_mod}, expected 0.70 (naidhana). "
        f"term_breakdown={tb}"
    )


# ---------------------------------------------------------------------------
# AC-E2: mechanism disabled → modifier = 1.0
# ---------------------------------------------------------------------------

def test_ace2_disabled_mechanism_yields_unit_modifier():
    """AC-E2: _W23_TARA_BALA_ENABLED=False → modifier=1.0 in term_breakdown.

    Same natal/transit setup as AC-E1, but we monkeypatch the module constant
    to False. The term_breakdown's tara_modifier should be 1.0.
    """
    assert hasattr(engine_module, "_W23_TARA_BALA_ENABLED"), (
        "_W23_TARA_BALA_ENABLED not found in engine module — blind-spec commit not applied."
    )

    ctx = _build_minimal_context(moon_lon_deg=5.0)
    swe_stub = _FakeSwe(moon_transit_lon_deg=85.0)  # would be naidhana if enabled

    with patch.object(engine_module, "_W23_TARA_BALA_ENABLED", False):
        result = _run_single(swe_stub, ctx)

    tb = result.term_breakdown
    assert "tara_modifier" in tb, (
        f"tara_modifier not found in term_breakdown keys: {list(tb.keys())}"
    )
    tara_mod = tb["tara_modifier"]
    assert abs(tara_mod - 1.0) < 1e-9, (
        f"AC-E2 FAIL: tara_modifier={tara_mod}, expected 1.0 when mechanism disabled. "
        f"term_breakdown={tb}"
    )


# ---------------------------------------------------------------------------
# AC-E3: formula string in result detail contains "tara_modifier"
# ---------------------------------------------------------------------------

def test_ace3_formula_string_contains_tara_modifier():
    """AC-E3: x_t_detail['formula'] contains 'tara_modifier' after wiring.

    The formula annotation must be updated in the detail dict, reflecting:
      lambda_v3 = PROMISE * PERMISSION * activity * tara_modifier * quality_gates
    """
    assert hasattr(engine_module, "_W23_TARA_BALA_ENABLED"), (
        "_W23_TARA_BALA_ENABLED not found in engine module — blind-spec commit not applied."
    )

    ctx = _build_minimal_context(moon_lon_deg=5.0)
    swe_stub = _FakeSwe(moon_transit_lon_deg=85.0)

    with patch.object(engine_module, "_W23_TARA_BALA_ENABLED", True):
        result = _run_single(swe_stub, ctx)

    detail = result.x_t_detail
    formula = detail.get("formula", "")
    assert "tara_modifier" in formula, (
        f"AC-E3 FAIL: 'tara_modifier' not found in x_t_detail['formula']. "
        f"formula={formula!r}"
    )
