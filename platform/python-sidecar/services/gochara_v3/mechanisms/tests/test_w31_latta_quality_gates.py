"""
test_w31_latta_quality_gates.py — TDD red-phase: all tests fail before B3 effect.

Acceptance criteria for B3 (Lattā → quality_gates):
  AC-E1: latta vedha row gets suppression stronger than _VEDHA_ZERO_MALEFIC_FACTOR (0.85)
          i.e., NOT treated as malefic_count=0
  AC-E2: non-latta vedha row (house_vedha) is unaffected by B3 change (regression guard)
  AC-E3: _LATTA_EFFECTIVE_MALEFIC_COUNT constant exists and is an int >= 1
  AC-E4: latta row with empty malefic_scale still degrades gracefully (no crash)
"""
from __future__ import annotations

import sys
import os

# Ensure the python-sidecar root is on the path so services.* imports work.
_SIDECAR_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
if _SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, os.path.abspath(_SIDECAR_ROOT))

import pytest
from dataclasses import dataclass, field
from typing import Optional

from services.gochara_v3.context import VedhaRow, MaleficScaleRow
from services.gochara_v3.engine import (
    _compute_quality_gates_from_context,
    _LATTA_EFFECTIVE_MALEFIC_COUNT,
    _VEDHA_ZERO_MALEFIC_FACTOR,
    _VEDHA_NO_SCALE_ROW_FACTOR,
)


# ---------------------------------------------------------------------------
# Minimal ClassContext stand-in (no DB access required)
# ---------------------------------------------------------------------------

@dataclass
class _MinimalNatalFacts:
    graha_longitudes: dict = field(default_factory=dict)
    graha_signs: dict = field(default_factory=dict)
    lagna_sign: Optional[str] = None
    lagna_longitude: Optional[float] = None


@dataclass
class _MinimalClassContext:
    """Minimal stand-in for ClassContext — only fields used by _compute_quality_gates_from_context."""
    vedha_rows: list
    malefic_scale: list
    # The following fields satisfy ClassContext structural needs but are unused by W1.3
    chart_id: str = "test-chart"
    event_class: str = "test_class"
    natal_facts: Optional[_MinimalNatalFacts] = None
    resonance_targets: tuple = ()
    promise: float = 0.5
    promise_detail: dict = field(default_factory=dict)
    dasha_periods: tuple = ()
    relevant_grahas: frozenset = field(default_factory=frozenset)
    relevant_signs: frozenset = field(default_factory=frozenset)
    temporal_shape: str = "point"
    valence: str = "neutral"
    is_adverse: bool = False


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_malefic_scale() -> list[MaleficScaleRow]:
    """Build a representative bg_vedha_malefic_scale (counts 1–5).

    Grade → factor schedule (mirrors engine.py _VEDHA_GRADE_SUPPRESSION):
      fear=0.75, grade_2=0.65, grade_3=0.55, grade_4=0.45, ignominy=0.35
    """
    return [
        MaleficScaleRow(malefic_count=1, effect_grade="fear",      effect_description="Fear.",      source_citation="PG353"),
        MaleficScaleRow(malefic_count=2, effect_grade="grade_2",   effect_description="Anxiety.",   source_citation="PG353"),
        MaleficScaleRow(malefic_count=3, effect_grade="grade_3",   effect_description="Loss.",      source_citation="PG353"),
        MaleficScaleRow(malefic_count=4, effect_grade="grade_4",   effect_description="Ruin.",      source_citation="PG353"),
        MaleficScaleRow(malefic_count=5, effect_grade="ignominy",  effect_description="Ignominy.",  source_citation="PG353"),
    ]


def _latta_vedha_row(graha: str = "Sun") -> VedhaRow:
    """Construct a latta VedhaRow as the writer produces it.

    latta rows have NO malefic_count in their detail JSONB — the writer only
    stores direction / count_from_graha / effect_description / janma/latta
    nakshatra indices and affliction_condition.
    """
    return VedhaRow(
        vedha_kind="latta",
        graha=graha,
        window_start="2026-01-01",
        window_end="2026-03-31",
        classical_citation="Phaladeepika PG338-339 Slokas 42-44",
        detail={
            "direction": "forward",
            "count_from_graha": 11,
            "effect_description": "Ruin of every business.",
            "janma_nakshatra_idx": 25,
            "latta_nakshatra_idx": 25,
            "affliction_condition": "latta_nak_eq_janma_nak",
        },
    )


def _house_vedha_row() -> VedhaRow:
    """Construct a regular house-vedha row (non-latta, with malefic_count)."""
    return VedhaRow(
        vedha_kind="house_vedha",
        graha="Saturn",
        window_start="2026-01-01",
        window_end="2026-03-31",
        classical_citation="PG353",
        detail={
            "malefic_count": 2,
            "malefic_obstructing_grahas": ["Saturn", "Mars"],
            "effect_grade": "grade_2",
        },
    )


# ---------------------------------------------------------------------------
# Evaluation window — overlaps all test rows above
# ---------------------------------------------------------------------------
WIN_START = "2026-01-15"
WIN_END   = "2026-02-15"


# ---------------------------------------------------------------------------
# AC-E3: constant exists, is int, is >= 1  (tested first — it's the import guard)
# ---------------------------------------------------------------------------

def test_ac_e3_latta_effective_malefic_count_constant():
    """AC-E3: _LATTA_EFFECTIVE_MALEFIC_COUNT exists, is an int, and is >= 1."""
    assert isinstance(_LATTA_EFFECTIVE_MALEFIC_COUNT, int), (
        f"_LATTA_EFFECTIVE_MALEFIC_COUNT must be an int, got {type(_LATTA_EFFECTIVE_MALEFIC_COUNT)}"
    )
    assert _LATTA_EFFECTIVE_MALEFIC_COUNT >= 1, (
        f"_LATTA_EFFECTIVE_MALEFIC_COUNT must be >= 1, got {_LATTA_EFFECTIVE_MALEFIC_COUNT}"
    )


# ---------------------------------------------------------------------------
# AC-E1: latta row gets suppression STRONGER than _VEDHA_ZERO_MALEFIC_FACTOR
# ---------------------------------------------------------------------------

def test_ac_e1_latta_vedha_suppression_stronger_than_zero_malefic():
    """AC-E1: a latta row (no malefic_count in detail) must NOT be treated as
    malefic_count=0 — it must receive a suppression factor < 0.85."""
    ctx = _MinimalClassContext(
        vedha_rows=[_latta_vedha_row("Sun")],
        malefic_scale=_make_malefic_scale(),
    )
    quality_gates, detail = _compute_quality_gates_from_context(ctx, WIN_START, WIN_END)

    assert len(detail["fired_vedha"]) == 1, "Expected exactly one fired vedha"
    fired = detail["fired_vedha"][0]

    assert fired["vedha_kind"] == "latta", f"Expected vedha_kind='latta', got {fired['vedha_kind']}"

    suppression_factor = fired["suppression_factor"]
    assert suppression_factor < _VEDHA_ZERO_MALEFIC_FACTOR, (
        f"Lattā suppression_factor {suppression_factor} must be < "
        f"_VEDHA_ZERO_MALEFIC_FACTOR ({_VEDHA_ZERO_MALEFIC_FACTOR}). "
        f"Lattā is a serious affliction (Phaladeepika 'Ruin / Great Loss'), "
        f"not a mild benefic obstruction."
    )

    # Also verify quality_gates itself is < 0.85 (end-to-end)
    assert quality_gates < _VEDHA_ZERO_MALEFIC_FACTOR, (
        f"quality_gates {quality_gates} must be < {_VEDHA_ZERO_MALEFIC_FACTOR} for a latta row"
    )


# ---------------------------------------------------------------------------
# AC-E2: non-latta row (house_vedha) is UNAFFECTED by the B3 change
# ---------------------------------------------------------------------------

def test_ac_e2_non_latta_vedha_regression_guard():
    """AC-E2: a house_vedha row with malefic_count=2 still follows the regular
    malefic_scale lookup path — B3 must not break existing vedha types."""
    ctx = _MinimalClassContext(
        vedha_rows=[_house_vedha_row()],
        malefic_scale=_make_malefic_scale(),
    )
    quality_gates, detail = _compute_quality_gates_from_context(ctx, WIN_START, WIN_END)

    assert len(detail["fired_vedha"]) == 1
    fired = detail["fired_vedha"][0]

    assert fired["vedha_kind"] == "house_vedha"
    # malefic_count=2 → grade_2 → suppression_factor=0.65
    assert fired["malefic_count"] == 2, f"Expected malefic_count=2, got {fired['malefic_count']}"
    assert fired["effect_grade"] == "grade_2", (
        f"Expected effect_grade='grade_2', got {fired['effect_grade']}"
    )
    assert abs(fired["suppression_factor"] - 0.65) < 1e-6, (
        f"Expected suppression_factor=0.65 for grade_2, got {fired['suppression_factor']}"
    )


# ---------------------------------------------------------------------------
# AC-E4: latta row with empty malefic_scale degrades gracefully (no crash)
# ---------------------------------------------------------------------------

def test_ac_e4_latta_graceful_fallback_empty_scale():
    """AC-E4: when malefic_scale is empty (CI / absent table), a latta row must
    NOT crash — it falls back to _VEDHA_NO_SCALE_ROW_FACTOR."""
    ctx = _MinimalClassContext(
        vedha_rows=[_latta_vedha_row("Moon")],
        malefic_scale=[],  # empty scale table — simulates CI / absent table
    )
    # Must not raise
    quality_gates, detail = _compute_quality_gates_from_context(ctx, WIN_START, WIN_END)

    assert len(detail["fired_vedha"]) == 1
    fired = detail["fired_vedha"][0]

    assert fired["vedha_kind"] == "latta"
    # With no scale table, should fall back to _VEDHA_NO_SCALE_ROW_FACTOR (0.70)
    assert abs(fired["suppression_factor"] - _VEDHA_NO_SCALE_ROW_FACTOR) < 1e-6, (
        f"Expected fallback suppression_factor={_VEDHA_NO_SCALE_ROW_FACTOR} "
        f"(empty scale table), got {fired['suppression_factor']}"
    )
    assert quality_gates < 1.0, "quality_gates must be < 1.0 when a latta row fires"
