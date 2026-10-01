"""
test_w31_latta_quality_gates.py — Lattā on the v3 quality gate (reconciled).

RECONCILED with the sealed contract (ASTRA_REVIEW_A5_4 v1.2 P2-a; GOCHARA_
DESIGN_SPECS_v1_4 §5; D-PG353). The original B3 criteria made a lattā row a
suppression MULTIPLIER (`_LATTA_EFFECTIVE_MALEFIC_COUNT` → grade → 0.55; 0.70
with no scale row). That path is retired on the shared v3 gate and is NOT
restored. The contract pinned here:

  AC-E1'. A lattā row carries no interval relation and no cited suppression
          scale: it is an ANNOTATION on the gate output (kind, graha, window,
          citation, note) — never a factor; the λ product receives 1.0.
  AC-E2'. A LEGACY house_vedha row (malefic_count, no vedha_intervals/coverage)
          is ignored, never a 0.65 grade_2 multiplier; a T0-8 house_vedha row
          with an active interval is `obstructed` with factor None (no cited
          scale), and a lattā row beside it stays an annotation.
  AC-E3.  `_LATTA_EFFECTIVE_MALEFIC_COUNT` still exists (retained, UNWIRED on
          the production path) — the import guard is kept as-is.
  AC-E4'. A lattā row with an empty scale table is the same annotation — no
          crash, no `_VEDHA_NO_SCALE_ROW_FACTOR` fallback number.
"""
from __future__ import annotations

import sys
import os

# Ensure the python-sidecar root is on the path so services.* imports work.
_SIDECAR_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
if _SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, os.path.abspath(_SIDECAR_ROOT))

import json

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


def _t08_house_vedha_row() -> VedhaRow:
    """A T0-8-shaped house_vedha row (the §5 payload): Saturn's residence over
    Jan–Mar 2026 with one active Mars obstruction covering the window."""
    return VedhaRow(
        vedha_kind="house_vedha", graha="Saturn",
        window_start="2026-01-01", window_end="2026-03-31",
        classical_citation="Phaladipika Adh. XXVI (fixture)",
        detail={
            "vedha_intervals": [{
                "obstructor_body": "Mars", "t_in": "2026-01-10", "t_out": "2026-02-20",
                "half_open": True, "state": "active", "exception": "none",
                "independence_group": "ig:Mars:2026-01-10",
                "segments": [{"start": "2026-01-10", "end": "2026-02-20", "state": "active"}],
                "operator_role": "scored", "provenance": "verse_cited"}],
            "coverage": {"state": "computed", "grain": "date",
                         "horizon_start": "2026-01-01", "horizon_end": "2026-03-31"},
            "operator_role": "scored", "provenance": "verse_cited",
            "primary_house": 3, "vedha_house": 9, "phala": "gain",
            "primary_sign_idx": 9, "primary_sign_name": "Capricorn",
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

def test_ac_e1_latta_is_annotation_only_never_a_multiplier():
    """AC-E1': a lattā row is an ANNOTATION (kind, graha, window, citation,
    note) on the gate output — never a suppression factor; the λ product
    receives 1.0. A lattā-only overlay computes no house-vedha horizon, so
    the gate is honestly `unavailable` (not a clean number)."""
    ctx = _MinimalClassContext(
        vedha_rows=[_latta_vedha_row("Sun")],
        malefic_scale=_make_malefic_scale(),
    )
    quality_gates, detail = _compute_quality_gates_from_context(ctx, WIN_START, WIN_END)

    assert quality_gates == 1.0
    assert detail["fired_vedha"] == [] and detail["vedha_fired_count"] == 0
    assert len(detail["annotations"]) == 1
    ann = detail["annotations"][0]
    assert ann["vedha_kind"] == "latta" and ann["graha"] == "Sun"
    assert ann["window_start"] == "2026-01-01" and ann["window_end"] == "2026-03-31"
    assert ann["classical_citation"] == "Phaladeepika PG338-339 Slokas 42-44"
    assert "annotation only" in ann["note"]
    assert "suppression_factor" not in json.dumps(detail)
    assert detail["state"] == "unavailable" and detail["factor"] is None
    assert detail["legacy_shape_rows_ignored"] == 0
    # the retired grade number exists only in the unwired constant
    assert _VEDHA_ZERO_MALEFIC_FACTOR == 0.85 and quality_gates != _VEDHA_ZERO_MALEFIC_FACTOR


# ---------------------------------------------------------------------------
# AC-E2: non-latta row (house_vedha) is UNAFFECTED by the B3 change
# ---------------------------------------------------------------------------

def test_ac_e2_house_vedha_rows_follow_the_interval_contract():
    """AC-E2': a LEGACY house_vedha row (malefic_count=2 in detail, no
    vedha_intervals / coverage) is not a T0-8 overlay row — ignored, never
    the 0.65 grade_2 multiplier. A T0-8 house_vedha row with an active
    interval over the window is `obstructed` with factor None (no cited
    scale), and the lattā row beside it stays an annotation."""
    ctx = _MinimalClassContext(
        vedha_rows=[_house_vedha_row()],
        malefic_scale=_make_malefic_scale(),
    )
    quality_gates, detail = _compute_quality_gates_from_context(ctx, WIN_START, WIN_END)
    assert quality_gates == 1.0
    assert detail["legacy_shape_rows_ignored"] == 1 and detail["fired_vedha"] == []
    assert detail["state"] == "unavailable" and detail["factor"] is None
    assert "suppression_factor" not in json.dumps(detail)

    ctx2 = _MinimalClassContext(
        vedha_rows=[_t08_house_vedha_row(), _latta_vedha_row("Sun")],
        malefic_scale=_make_malefic_scale(),
    )
    qg2, d2 = _compute_quality_gates_from_context(ctx2, WIN_START, WIN_END)
    assert qg2 == 1.0 and d2["state"] == "obstructed" and d2["factor"] is None
    assert d2["null_state"] == "omit"
    fired = d2["fired_vedha"]
    assert len(fired) == 1 and fired[0]["vedha_kind"] == "house_vedha"
    assert fired[0]["primary_graha"] == "Saturn"
    assert fired[0]["fired"][0]["obstructor_body"] == "Mars"
    assert fired[0]["factor"] is None
    assert [a["vedha_kind"] for a in d2["annotations"]] == ["latta"]
    assert "suppression_factor" not in json.dumps(d2)


# ---------------------------------------------------------------------------
# AC-E4: latta row with empty malefic_scale degrades gracefully (no crash)
# ---------------------------------------------------------------------------

def test_ac_e4_latta_with_empty_scale_is_the_same_annotation_no_fallback_number():
    """AC-E4': with an empty malefic_scale (CI / absent table) a lattā row
    must not crash and is the SAME annotation as with a populated scale —
    the scale is irrelevant to an annotation; no `_VEDHA_NO_SCALE_ROW_FACTOR`
    fallback number is produced."""
    ctx = _MinimalClassContext(
        vedha_rows=[_latta_vedha_row("Moon")],
        malefic_scale=[],  # empty scale table — simulates CI / absent table
    )
    quality_gates, detail = _compute_quality_gates_from_context(ctx, WIN_START, WIN_END)

    assert quality_gates == 1.0 and detail["fired_vedha"] == []
    assert detail["annotations"][0]["vedha_kind"] == "latta"
    assert detail["annotations"][0]["graha"] == "Moon"
    assert "suppression_factor" not in json.dumps(detail)
    assert _VEDHA_NO_SCALE_ROW_FACTOR == 0.70 and quality_gates != _VEDHA_NO_SCALE_ROW_FACTOR

    ctx2 = _MinimalClassContext(
        vedha_rows=[_latta_vedha_row("Moon")],
        malefic_scale=_make_malefic_scale(),
    )
    _, d2 = _compute_quality_gates_from_context(ctx2, WIN_START, WIN_END)
    assert d2["annotations"] == detail["annotations"]
    assert d2["state"] == detail["state"] == "unavailable"
