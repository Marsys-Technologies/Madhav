"""
Tests for W2.3 — Tara bala: 9-cycle nakshatra quality modifier.

Acceptance criteria:
  AC1. disabled (enabled=False) → modifier == 1.0, skipped=True
  AC2. 9-tara cycle positions produce correct tara names
  AC3. naidhana (position 7) → modifier < 1.0
  AC4. paramamitra (position 9) → modifier > 1.0
  AC5. no natal Moon in context → modifier == 1.0, skipped=True (honest empty)
  AC6. no transit longitude supplied → modifier == 1.0, skipped=True
  AC7. compute_tara is pure and handles all 27 nakshatra input combinations
  AC8. all modifiers are positive (never zero or negative)
  AC9. MechanismResult.mechanism_id == MECHANISM_ID
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import MagicMock

import pytest

from services.gochara_v3.mechanisms.w23_tara_bala import (
    MECHANISM_ID,
    TARA_QUALITY,
    TARA_MODIFIERS,
    MechanismResult,
    compute_tara,
    compute,
)


# ---------------------------------------------------------------------------
# Fixtures: minimal ClassContext stand-ins (no DB)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _NatalFacts:
    graha_longitudes: dict
    graha_signs: dict
    lagna_sign: Optional[str] = None
    lagna_longitude: Optional[float] = None


@dataclass(frozen=True)
class _ClassContext:
    chart_id: str
    event_class: str
    natal_facts: Optional[_NatalFacts] = None
    # All other ClassContext fields unused by this mechanism
    resonance_targets: tuple = ()
    promise: float = 0.0
    promise_detail: dict = field(default_factory=dict)
    dasha_periods: tuple = ()
    relevant_grahas: frozenset = field(default_factory=frozenset)
    relevant_signs: frozenset = field(default_factory=frozenset)
    temporal_shape: str = "point"
    valence: str = "neutral"
    is_adverse: bool = False
    beta_e: float = 0.45
    weight_by_target_ref: dict = field(default_factory=dict)
    av_gate_rows: tuple = ()
    sade_sati_phases: tuple = ()
    vedha_rows: tuple = ()
    malefic_scale: tuple = ()


def _ctx_with_moon(moon_lon_deg: float) -> _ClassContext:
    """Build a fixture context with Moon at the given longitude."""
    nf = _NatalFacts(
        graha_longitudes={"Moon": moon_lon_deg},
        graha_signs={"Moon": "Aquarius"},
    )
    return _ClassContext(chart_id="test-chart", event_class="career", natal_facts=nf)


def _ctx_no_moon() -> _ClassContext:
    """Build a fixture context with natal_facts present but no Moon longitude."""
    nf = _NatalFacts(
        graha_longitudes={"Sun": 45.0},
        graha_signs={},
    )
    return _ClassContext(chart_id="test-chart", event_class="career", natal_facts=nf)


def _ctx_no_natal_facts() -> _ClassContext:
    """Build a fixture context with natal_facts=None."""
    return _ClassContext(chart_id="test-chart", event_class="career", natal_facts=None)


# ---------------------------------------------------------------------------
# AC1: disabled returns unit modifier
# ---------------------------------------------------------------------------

def test_disabled_returns_unit_modifier():
    """When enabled=False the mechanism is a no-op: modifier==1.0, skipped=True."""
    ctx = _ctx_with_moon(moon_lon_deg=306.67)  # ~Purva Bhadrapada nak 25
    result = compute(ctx, t_jd=2451545.0, enabled=False, transit_body_longitude_deg=80.0)
    assert isinstance(result, MechanismResult)
    assert result.modifier == 1.0
    assert result.skipped is True
    assert result.tara_name is None
    assert result.tara_position is None
    assert "disabled" in (result.skip_reason or "")


# ---------------------------------------------------------------------------
# AC2: tara cycle correct — nakshatra positions produce correct tara names
# ---------------------------------------------------------------------------

def test_tara_cycle_correct_sampat():
    """Natal Moon nak 1, transit nak 2 → position=2 → sampat."""
    tara, modifier = compute_tara(transit_nak_index=2, natal_moon_nak_index=1)
    assert tara == "sampat"
    assert modifier == TARA_MODIFIERS["sampat"]


def test_tara_cycle_correct_vipat():
    """Natal Moon nak 1, transit nak 3 → position=3 → vipat."""
    tara, modifier = compute_tara(transit_nak_index=3, natal_moon_nak_index=1)
    assert tara == "vipat"
    assert modifier == TARA_MODIFIERS["vipat"]


def test_tara_cycle_correct_janma_self():
    """Transit == natal Moon → position=1 (offset=0: 0%27=0, 0%9=0, +1=1) → janma."""
    tara, modifier = compute_tara(transit_nak_index=5, natal_moon_nak_index=5)
    assert tara == "janma"
    assert modifier == 1.00


def test_tara_cycle_correct_paramamitra():
    """Natal Moon nak 1, transit nak 9 → position=9 → paramamitra."""
    tara, modifier = compute_tara(transit_nak_index=9, natal_moon_nak_index=1)
    assert tara == "paramamitra"
    assert modifier == TARA_MODIFIERS["paramamitra"]


def test_tara_cycle_wraps_at_27():
    """Cycle wraps at 27: transit nak 27, natal nak 1 → offset=26 → 26%9=8 → pos=9 → paramamitra."""
    # offset = (27 - 1) % 27 = 26; 26 % 9 = 8; 8 + 1 = 9
    tara, modifier = compute_tara(transit_nak_index=27, natal_moon_nak_index=1)
    assert tara == "paramamitra"
    assert modifier == 1.20


def test_tara_cycle_position_10_wraps_to_1():
    """Position 10 wraps to Janma again (cycle repeats every 9): transit=10, natal=1 → pos=1."""
    # offset = (10 - 1) % 27 = 9; 9 % 9 = 0; 0 + 1 = 1
    tara, modifier = compute_tara(transit_nak_index=10, natal_moon_nak_index=1)
    assert tara == "janma"


def test_tara_cycle_all_positions_covered():
    """Confirm all 9 tara names are reachable from natal=1, transits 1-27."""
    seen = set()
    for transit in range(1, 28):
        tara, _ = compute_tara(transit_nak_index=transit, natal_moon_nak_index=1)
        seen.add(tara)
    assert seen == set(TARA_QUALITY.values()), f"Missing tara names: {set(TARA_QUALITY.values()) - seen}"


# ---------------------------------------------------------------------------
# AC3: naidhana damps
# ---------------------------------------------------------------------------

def test_naidhana_damps():
    """tara=naidhana → modifier < 1.0."""
    # position 7 = naidhana: transit_nak - natal_nak ≡ 6 (mod 27), 6 % 9 = 6, + 1 = 7
    tara, modifier = compute_tara(transit_nak_index=7, natal_moon_nak_index=1)
    assert tara == "naidhana"
    assert modifier < 1.0
    assert modifier == 0.70


def test_naidhana_via_compute_full():
    """Full compute() path produces naidhana modifier < 1.0 when transit aligns."""
    # Natal Moon longitude in nak 1 (Ashwini: 0–13.33°): use 5°
    # Transit body in nak 7 (Punarvasu: 80–93.33°): use 85°
    ctx = _ctx_with_moon(moon_lon_deg=5.0)
    result = compute(ctx, t_jd=2451545.0, enabled=True, transit_body_longitude_deg=85.0)
    assert not result.skipped
    assert result.tara_name == "naidhana"
    assert result.modifier < 1.0
    assert result.modifier == 0.70


# ---------------------------------------------------------------------------
# AC4: paramamitra amplifies
# ---------------------------------------------------------------------------

def test_paramamitra_amplifies():
    """tara=paramamitra → modifier > 1.0."""
    # position 9 = paramamitra: transit_nak - natal_nak ≡ 8 (mod 27), 8 % 9 = 8, + 1 = 9
    tara, modifier = compute_tara(transit_nak_index=9, natal_moon_nak_index=1)
    assert tara == "paramamitra"
    assert modifier > 1.0
    assert modifier == 1.20


def test_paramamitra_via_compute_full():
    """Full compute() path produces paramamitra modifier > 1.0 when transit aligns."""
    # Natal Moon in nak 1 (0–13.33°): use 6°
    # Transit body in nak 9 (Ashlesha: 106.67–120°): use 110°
    ctx = _ctx_with_moon(moon_lon_deg=6.0)
    result = compute(ctx, t_jd=2451545.0, enabled=True, transit_body_longitude_deg=110.0)
    assert not result.skipped
    assert result.tara_name == "paramamitra"
    assert result.modifier > 1.0
    assert result.modifier == 1.20


# ---------------------------------------------------------------------------
# AC5: honest empty when no natal Moon
# ---------------------------------------------------------------------------

def test_honest_empty_when_no_natal_moon_longitude():
    """natal_facts present but no Moon longitude → modifier==1.0, skipped=True."""
    ctx = _ctx_no_moon()
    result = compute(ctx, t_jd=2451545.0, enabled=True, transit_body_longitude_deg=100.0)
    assert result.modifier == 1.0
    assert result.skipped is True
    assert result.tara_name is None
    assert result.tara_position is None
    assert "Moon" in (result.skip_reason or "")


def test_honest_empty_when_natal_facts_none():
    """natal_facts=None → modifier==1.0, skipped=True."""
    ctx = _ctx_no_natal_facts()
    result = compute(ctx, t_jd=2451545.0, enabled=True, transit_body_longitude_deg=100.0)
    assert result.modifier == 1.0
    assert result.skipped is True
    assert result.tara_name is None
    assert "natal_facts" in (result.skip_reason or "")


# ---------------------------------------------------------------------------
# AC6: no transit longitude supplied
# ---------------------------------------------------------------------------

def test_honest_skip_when_no_transit_longitude():
    """transit_body_longitude_deg=None → modifier==1.0, skipped=True."""
    ctx = _ctx_with_moon(moon_lon_deg=100.0)
    result = compute(ctx, t_jd=2451545.0, enabled=True, transit_body_longitude_deg=None)
    assert result.modifier == 1.0
    assert result.skipped is True
    assert "transit_body_longitude_deg" in (result.skip_reason or "")


# ---------------------------------------------------------------------------
# AC7: compute_tara pure function — all 27×27 combos produce valid output
# ---------------------------------------------------------------------------

def test_compute_tara_pure_all_combinations():
    """compute_tara(i, j) for all i,j in 1..27 produces valid (tara_name, modifier)."""
    valid_tara_names = set(TARA_QUALITY.values())
    for transit in range(1, 28):
        for natal in range(1, 28):
            tara, modifier = compute_tara(transit, natal)
            assert tara in valid_tara_names, f"Invalid tara {tara!r} for transit={transit}, natal={natal}"
            assert modifier > 0.0, f"Non-positive modifier {modifier} for transit={transit}, natal={natal}"


# ---------------------------------------------------------------------------
# AC8: all modifiers positive
# ---------------------------------------------------------------------------

def test_all_modifiers_positive():
    """TARA_MODIFIERS: every value > 0.0 (no zero suppression, no negative)."""
    for tara_name, mod in TARA_MODIFIERS.items():
        assert mod > 0.0, f"Modifier for {tara_name!r} is non-positive: {mod}"


# ---------------------------------------------------------------------------
# AC9: mechanism_id constant
# ---------------------------------------------------------------------------

def test_mechanism_id_in_result():
    """MechanismResult.mechanism_id == MECHANISM_ID for all paths."""
    ctx = _ctx_with_moon(moon_lon_deg=100.0)

    # enabled path
    result_enabled = compute(ctx, t_jd=2451545.0, enabled=True, transit_body_longitude_deg=150.0)
    assert result_enabled.mechanism_id == MECHANISM_ID

    # disabled path
    result_disabled = compute(ctx, t_jd=2451545.0, enabled=False, transit_body_longitude_deg=150.0)
    assert result_disabled.mechanism_id == MECHANISM_ID

    # skip path (no Moon)
    ctx_no_moon = _ctx_no_natal_facts()
    result_skip = compute(ctx_no_moon, t_jd=2451545.0, enabled=True, transit_body_longitude_deg=150.0)
    assert result_skip.mechanism_id == MECHANISM_ID
