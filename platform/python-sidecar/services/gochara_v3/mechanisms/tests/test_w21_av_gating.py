"""
Tests for W2.1 — Ashtakavarga bindu gating mechanism.

All tests are fixture-based (no DB connection required), per lane constraint.

Test inventory
--------------
1. test_disabled_returns_unit_modifier
   enabled=False → modifier==1.0, sentences==[], enabled==False

2. test_modifier_in_range
   modifier is always in [0.0, 2.0] regardless of input (fuzz over edge cases)

3. test_fires_with_high_bindus
   av_gate_rows with high min_sav_score (above 28 threshold) → modifier > 1.0

4. test_honest_empty_when_no_av_data
   empty av_gate_rows → modifier==1.0, detail carries honest reason

5. test_fires_with_low_bindus (bonus — low bindu → damp → modifier < 1.0)

6. test_fires_neutral_at_boundary (bonus — bindu == 28 → modifier == 1.0)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pytest

from services.gochara_v3.mechanisms.w21_av_gating import (
    MECHANISM_ID,
    MechanismResult,
    compute,
)

# ── Fixtures ────────────────────────────────────────────────────────────────


@dataclass
class _MockAVGateRow:
    """Minimal stand-in for context.AVGateRow — only the fields w21 reads."""
    graha: str
    min_sav_score: Optional[float]
    effect: Optional[str] = None
    target_ref: str = "1"
    classical_citation: Optional[str] = None


@dataclass
class _MockContext:
    """Minimal ClassContext-like object sufficient for w21_av_gating.compute()."""
    av_gate_rows: tuple = field(default_factory=tuple)
    chart_id: str = "test-chart-id"
    event_class: str = "career"


_SAMPLE_JD = 2460000.5  # arbitrary valid JD for all tests


# ── Tests ───────────────────────────────────────────────────────────────────


def test_disabled_returns_unit_modifier():
    """enabled=False must return modifier==1.0, empty sentences, enabled==False."""
    ctx = _MockContext(av_gate_rows=(_MockAVGateRow(graha="Jupiter", min_sav_score=35.0),))
    result = compute(ctx, _SAMPLE_JD, enabled=False)

    assert isinstance(result, MechanismResult)
    assert result.modifier == 1.0, f"Expected 1.0, got {result.modifier}"
    assert result.sentences == [], f"Expected empty sentences, got {result.sentences}"
    assert result.enabled is False
    assert result.mechanism_id == MECHANISM_ID


def test_modifier_in_range():
    """modifier must always be in [0.0, 2.0] for any av_gate_rows input."""
    test_cases = [
        (),  # empty
        (_MockAVGateRow(graha="Sun", min_sav_score=0.0),),         # extreme low
        (_MockAVGateRow(graha="Moon", min_sav_score=100.0),),      # extreme high
        (_MockAVGateRow(graha="Mars", min_sav_score=None),),       # None score
        (
            _MockAVGateRow(graha="Jupiter", min_sav_score=28.0),
            _MockAVGateRow(graha="Saturn", min_sav_score=14.0),
            _MockAVGateRow(graha="Venus", min_sav_score=42.0),
        ),  # mixed
        (_MockAVGateRow(graha="Mercury", min_sav_score=28.08),),   # right at mean
    ]

    for rows in test_cases:
        ctx = _MockContext(av_gate_rows=rows)
        result = compute(ctx, _SAMPLE_JD, enabled=True)
        assert 0.0 <= result.modifier <= 2.0, (
            f"modifier={result.modifier} out of [0.0, 2.0] for av_gate_rows={rows}"
        )


def test_fires_with_high_bindus():
    """High min_sav_score (> 28) → amplify → modifier > 1.0."""
    high_bindu_rows = (
        _MockAVGateRow(graha="Jupiter", min_sav_score=36.0, effect="auspicious"),
        _MockAVGateRow(graha="Venus", min_sav_score=40.0, effect="auspicious"),
    )
    ctx = _MockContext(av_gate_rows=high_bindu_rows)
    result = compute(ctx, _SAMPLE_JD, enabled=True)

    assert result.enabled is True
    assert result.modifier > 1.0, (
        f"Expected modifier > 1.0 for high bindus, got {result.modifier}"
    )
    assert len(result.sentences) == 2
    for sentence in result.sentences:
        assert sentence["classification"] == "amplify"
        assert sentence["row_modifier"] > 1.0
    assert result.mechanism_id == MECHANISM_ID


def test_honest_empty_when_no_av_data():
    """Empty av_gate_rows → modifier==1.0 with honest detail (no silent false positive)."""
    ctx = _MockContext(av_gate_rows=())
    result = compute(ctx, _SAMPLE_JD, enabled=True)

    assert result.modifier == 1.0, f"Expected 1.0 for empty data, got {result.modifier}"
    assert result.sentences == []
    assert result.enabled is True
    assert "reason" in result.detail, "detail must carry 'reason' key for honest reporting"
    assert result.detail["reason"] == "no_av_data", (
        f"Expected reason='no_av_data', got {result.detail.get('reason')}"
    )


def test_fires_with_low_bindus():
    """Low min_sav_score (< 28) → damp → modifier < 1.0."""
    low_bindu_rows = (
        _MockAVGateRow(graha="Saturn", min_sav_score=14.0, effect="inauspicious"),
        _MockAVGateRow(graha="Mars", min_sav_score=20.0, effect="inauspicious"),
    )
    ctx = _MockContext(av_gate_rows=low_bindu_rows)
    result = compute(ctx, _SAMPLE_JD, enabled=True)

    assert result.enabled is True
    assert result.modifier < 1.0, (
        f"Expected modifier < 1.0 for low bindus, got {result.modifier}"
    )
    for sentence in result.sentences:
        assert sentence["classification"] == "damp"
        assert sentence["row_modifier"] < 1.0


def test_fires_neutral_at_boundary():
    """min_sav_score == 28 (exactly at threshold) → neutral → modifier == 1.0."""
    boundary_rows = (
        _MockAVGateRow(graha="Sun", min_sav_score=28.0),
    )
    ctx = _MockContext(av_gate_rows=boundary_rows)
    result = compute(ctx, _SAMPLE_JD, enabled=True)

    assert result.modifier == 1.0, (
        f"Expected 1.0 at boundary bindu count, got {result.modifier}"
    )
    assert result.sentences[0]["classification"] == "neutral"


def test_none_min_sav_score_is_neutral():
    """A row with min_sav_score=None carries no threshold data — must be neutral."""
    rows = (
        _MockAVGateRow(graha="Rahu", min_sav_score=None),
    )
    ctx = _MockContext(av_gate_rows=rows)
    result = compute(ctx, _SAMPLE_JD, enabled=True)

    assert result.modifier == 1.0
    assert result.sentences[0]["classification"] == "neutral"
    assert "absent" in result.sentences[0]["note"].lower()


def test_result_has_correct_mechanism_id():
    """mechanism_id on all result variants must equal MECHANISM_ID."""
    ctx_empty = _MockContext(av_gate_rows=())
    ctx_data = _MockContext(av_gate_rows=(_MockAVGateRow(graha="Sun", min_sav_score=30.0),))

    for ctx in (ctx_empty, ctx_data):
        for enabled in (True, False):
            result = compute(ctx, _SAMPLE_JD, enabled=enabled)
            assert result.mechanism_id == MECHANISM_ID, (
                f"mechanism_id mismatch: {result.mechanism_id!r}"
            )
