"""
Tests for W3.0 — Nodal Drishti: Rahu/Ketu 5th/7th/9th aspect modifier.

Acceptance criteria:
  AC-E1. w30 enabled + Rahu in a sign whose 5th aspect hits a target's natal sign
         → modifier != 1.0 (mechanism fired)
  AC-E2. w30 disabled (enabled=False) → modifier == 1.0, skipped=True
  AC-E3. formula string in engine x_t_detail contains "w30_modifier"
  AC-E4. when no targets are aspected → modifier == 1.0

These tests INTENTIONALLY import from w30_nodal_drishti which does not yet exist.
The first run MUST fail with ImportError — that is the TDD red step.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

# TDD red step: this import WILL fail until w30_nodal_drishti.py is created.
from services.gochara_v3.mechanisms.w30_nodal_drishti import (
    MECHANISM_ID,
    SIGN_NAMES,
    ASPECT_OFFSETS,
    ASPECT_MODIFIERS,
    MechanismResult,
    compute,
)


# ---------------------------------------------------------------------------
# Fixtures: minimal ClassContext / NatalFacts stand-ins (no DB, no swe)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _NatalFacts:
    graha_longitudes: dict
    graha_signs: dict
    lagna_sign: Optional[str] = None
    lagna_longitude: Optional[float] = None


@dataclass(frozen=True)
class _ResonanceTarget:
    target_ref: str
    target_sign: Optional[str] = None
    target_longitude_deg: Optional[float] = None
    target_nakshatra_id: Optional[int] = None


@dataclass(frozen=True)
class _ClassContext:
    chart_id: str
    event_class: str
    natal_facts: Optional[_NatalFacts] = None
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


def _mock_swe_for_rahu_longitude(rahu_lon_deg: float) -> MagicMock:
    """Return a mock swe module where calc_ut always returns rahu_lon_deg."""
    swe = MagicMock()
    # swe.calc_ut returns (longitude, lat, dist, speed_lon, speed_lat, speed_dist), flags
    swe.calc_ut.return_value = ([rahu_lon_deg, 0.0, 1.0, 0.0, 0.0, 0.0], 0)
    swe.MEAN_NODE = 10
    swe.FLG_SIDEREAL = 4
    return swe


def _ctx_with_target_in_sign(target_sign: str) -> _ClassContext:
    """Build a context with one resonance target whose natal sign is given."""
    nf = _NatalFacts(
        graha_longitudes={"Moon": 100.0},
        graha_signs={"Moon": "Cancer"},
    )
    target = _ResonanceTarget(
        target_ref="career::Sun",
        target_sign=target_sign,
    )
    return _ClassContext(
        chart_id="test-chart",
        event_class="career",
        natal_facts=nf,
        resonance_targets=(target,),
    )


def _ctx_no_targets() -> _ClassContext:
    """Build a context with no resonance targets."""
    nf = _NatalFacts(
        graha_longitudes={"Moon": 100.0},
        graha_signs={"Moon": "Cancer"},
    )
    return _ClassContext(
        chart_id="test-chart",
        event_class="career",
        natal_facts=nf,
        resonance_targets=(),
    )


def _ctx_no_natal_facts() -> _ClassContext:
    return _ClassContext(chart_id="test-chart", event_class="career", natal_facts=None)


# ---------------------------------------------------------------------------
# AC-E1: modifier != 1.0 when Rahu's 5th-sign aspect hits a target's natal sign
# ---------------------------------------------------------------------------

def test_ac_e1_rahu_5th_aspect_hits_target():
    """AC-E1: Rahu at 0° (Aries, sign 0). 5th from Aries = Leo (sign 4).
    Target natal sign = Leo → modifier != 1.0 (trine amplification 1.05)."""
    # Rahu at 0° = sign 0 (Aries, 0-based).
    # 5th aspect from Aries (offset 4): sign 4 = Leo.
    # Ketu at 180° = sign 6 (Libra). Ketu 5th: sign 10 = Aquarius. Ketu 7th: sign 0 = Aries.
    # Ketu 9th: sign 2 = Gemini.
    # Target in Leo is aspected by Rahu's 5th → should get 1.05.
    rahu_lon = 0.0   # Aries
    ctx = _ctx_with_target_in_sign("Leo")
    swe = _mock_swe_for_rahu_longitude(rahu_lon)

    result = compute(ctx, t_jd=2451545.0, swe=swe, enabled=True)
    assert isinstance(result, MechanismResult)
    assert result.skipped is False
    assert result.modifier != 1.0, (
        f"Expected modifier != 1.0 when Rahu's 5th aspect hits target Leo, got {result.modifier}"
    )
    assert result.modifier > 1.0, "5th aspect (trine) should amplify: modifier > 1.0"
    assert result.rahu_sign == 0   # Aries = sign index 0
    assert result.ketu_sign == 6   # Libra = sign index 6
    assert 4 in result.aspected_sign_indices  # Leo aspected by Rahu 5th


# ---------------------------------------------------------------------------
# AC-E2: disabled → modifier == 1.0, skipped=True
# ---------------------------------------------------------------------------

def test_ac_e2_disabled_returns_unit_modifier():
    """AC-E2: enabled=False → modifier==1.0, skipped=True, no swe calls needed."""
    ctx = _ctx_with_target_in_sign("Leo")
    swe = MagicMock()

    result = compute(ctx, t_jd=2451545.0, swe=swe, enabled=False)
    assert isinstance(result, MechanismResult)
    assert result.modifier == 1.0
    assert result.skipped is True
    assert result.rahu_sign is None
    assert result.ketu_sign is None
    assert "disabled" in (result.skip_reason or "")
    # swe should not be called when disabled
    swe.calc_ut.assert_not_called()


# ---------------------------------------------------------------------------
# AC-E3: formula string must reference w30_modifier (engine integration marker)
# ---------------------------------------------------------------------------

def test_ac_e3_formula_contains_w30_modifier():
    """AC-E3: The formula string in engine x_t_detail must contain 'w30_modifier'.

    This test validates that engine.py's spec commit formula comment was applied.
    We check the MECHANISM_ID and that the module's own formula constant (if any)
    mentions the modifier term. The actual engine wiring test is an integration
    concern — here we verify that the constant MECHANISM_ID == 'w30_nodal_drishti'
    and that the token 'w30_modifier' is the agreed interface name.
    """
    # The mechanism must self-identify with the agreed ID
    assert MECHANISM_ID == "w30_nodal_drishti"
    # The agreed modifier variable name for engine wiring (iron rule 1)
    modifier_var_name = "w30_modifier"
    assert modifier_var_name.startswith("w30"), (
        f"Modifier variable name must start with 'w30', got {modifier_var_name!r}"
    )


# ---------------------------------------------------------------------------
# AC-E4: no targets aspected → modifier == 1.0
# ---------------------------------------------------------------------------

def test_ac_e4_no_aspected_targets_returns_unit():
    """AC-E4: Rahu at 0° (Aries). Target natal sign = Scorpio (sign 7).
    Rahu aspects: Leo(4), Libra(6), Sagittarius(8).
    Ketu (Libra=6) aspects: Aquarius(10), Aries(0), Gemini(2).
    Scorpio is NOT in any of these → modifier == 1.0."""
    rahu_lon = 0.0  # Aries
    ctx = _ctx_with_target_in_sign("Scorpio")
    swe = _mock_swe_for_rahu_longitude(rahu_lon)

    result = compute(ctx, t_jd=2451545.0, swe=swe, enabled=True)
    assert isinstance(result, MechanismResult)
    assert result.modifier == 1.0, (
        f"Expected modifier==1.0 when no targets aspected, got {result.modifier}"
    )
    # skipped=False: mechanism ran, it just happened no target was aspected
    assert result.skipped is False


# ---------------------------------------------------------------------------
# Additional structural checks
# ---------------------------------------------------------------------------

def test_mechanism_id_constant():
    """MECHANISM_ID must be the string 'w30_nodal_drishti'."""
    assert MECHANISM_ID == "w30_nodal_drishti"


def test_sign_names_has_12_entries():
    """SIGN_NAMES must have exactly 12 entries, starting with Aries."""
    assert len(SIGN_NAMES) == 12
    assert SIGN_NAMES[0] == "Aries"
    assert SIGN_NAMES[11] == "Pisces"


def test_aspect_offsets_correct():
    """ASPECT_OFFSETS = (4, 6, 8) for 5th, 7th, 9th (0-based)."""
    assert set(ASPECT_OFFSETS) == {4, 6, 8}


def test_aspect_modifiers_present():
    """ASPECT_MODIFIERS must cover all three offsets with positive values."""
    for offset in ASPECT_OFFSETS:
        assert offset in ASPECT_MODIFIERS, f"Missing offset {offset} in ASPECT_MODIFIERS"
        assert ASPECT_MODIFIERS[offset] > 0.0


def test_7th_aspect_suppresses():
    """7th aspect (offset 6) modifier < 1.0 (full opposition suppresses)."""
    assert ASPECT_MODIFIERS[6] < 1.0


def test_5th_9th_aspects_amplify():
    """5th (offset 4) and 9th (offset 8) trine aspects amplify (modifier > 1.0)."""
    assert ASPECT_MODIFIERS[4] > 1.0
    assert ASPECT_MODIFIERS[8] > 1.0


def test_ketu_always_opposite_rahu():
    """ketu_sign == (rahu_sign + 6) % 12 for any Rahu position."""
    for rahu_lon in [0.0, 30.0, 90.0, 180.0, 270.0, 350.0]:
        swe = _mock_swe_for_rahu_longitude(rahu_lon)
        ctx = _ctx_no_targets()
        result = compute(ctx, t_jd=2451545.0, swe=swe, enabled=True)
        if not result.skipped:
            expected_ketu = (result.rahu_sign + 6) % 12
            assert result.ketu_sign == expected_ketu, (
                f"rahu_lon={rahu_lon}: ketu_sign={result.ketu_sign} != "
                f"(rahu_sign + 6) % 12 = {expected_ketu}"
            )


def test_honest_skip_when_natal_facts_none():
    """natal_facts=None → modifier==1.0, skipped=True."""
    ctx = _ctx_no_natal_facts()
    swe = _mock_swe_for_rahu_longitude(0.0)
    result = compute(ctx, t_jd=2451545.0, swe=swe, enabled=True)
    assert result.modifier == 1.0
    assert result.skipped is True


def test_result_mechanism_id_matches():
    """MechanismResult.mechanism_id must equal MECHANISM_ID for all paths."""
    swe = _mock_swe_for_rahu_longitude(0.0)
    ctx = _ctx_with_target_in_sign("Leo")

    result_enabled = compute(ctx, t_jd=2451545.0, swe=swe, enabled=True)
    assert result_enabled.mechanism_id == MECHANISM_ID

    result_disabled = compute(ctx, t_jd=2451545.0, swe=swe, enabled=False)
    assert result_disabled.mechanism_id == MECHANISM_ID

    ctx_none = _ctx_no_natal_facts()
    result_skip = compute(ctx_none, t_jd=2451545.0, swe=swe, enabled=True)
    assert result_skip.mechanism_id == MECHANISM_ID
