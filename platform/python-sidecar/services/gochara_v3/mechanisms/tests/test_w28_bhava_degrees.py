"""
Tests for W2.8 — Bhava cusp degrees enrichment mechanism.

All tests are fixture-based (no DB connection required), per lane constraint.

Test inventory
--------------
1. test_disabled_returns_empty_sentences
   enabled=False -> modifier==1.0, sentences==[], enabled==False

2. test_modifier_always_unit
   modifier is always 1.0 regardless of input — this mechanism produces
   sentences (degree enrichment), not a multiplicative lambda modifier

3. test_resolves_bhava_targets
   synthetic context with bhava-typed targets + natal_facts.bhava_cusp_degrees
   -> one sentence per resolved bhava target, each carrying cusp_deg + fact_id

4. test_honest_empty_when_no_natal_facts
   natal_facts=None (or bhava_cusp_degrees absent) -> sentences==[], honest detail

5. test_no_bhava_targets_returns_empty_sentences
   context with only non-bhava targets -> sentences==[], reason='no_bhava_targets'

6. test_sentence_carries_fact_id_reference
   each resolved sentence must carry a non-empty fact_id (§N.5 L1 reference)

7. test_unresolvable_bhava_ref_does_not_crash
   target_ref that is not a valid 1-12 integer is reported as unresolved, not a crash

8. test_mechanism_id_is_constant_on_all_variants
   mechanism_id on all result variants equals MECHANISM_ID
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pytest

from services.gochara_v3.mechanisms.w28_bhava_degrees import (
    MECHANISM_ID,
    TOGGLE_KEY,
    MechanismResult,
    compute,
)

# ── Minimal fixture types ───────────────────────────────────────────────────


@dataclass
class _MockResonanceTarget:
    """Minimal stand-in for ResonanceTarget — only fields w28 reads."""
    target_type: str
    target_ref: str
    event_class: str = "marriage"
    weight: float = 0.9
    chart_id: str = "test-chart-id"
    classical_citation: Optional[str] = "test-citation"
    uncited_extension: bool = False


@dataclass
class _MockNatalFacts:
    """Minimal NatalFacts-like object with bhava_cusp_degrees extension."""
    graha_longitudes: dict = field(default_factory=dict)
    graha_signs: dict = field(default_factory=dict)
    lagna_sign: Optional[str] = None
    lagna_longitude: Optional[float] = None
    # W2.8 extension: {subject -> {"deg": float, "fact_id": str}}
    bhava_cusp_degrees: dict = field(default_factory=dict)


@dataclass
class _MockContext:
    """Minimal ClassContext-like object sufficient for w28_bhava_degrees.compute()."""
    resonance_targets: tuple = field(default_factory=tuple)
    natal_facts: Optional[_MockNatalFacts] = None
    chart_id: str = "test-chart-id"
    event_class: str = "marriage"


_SAMPLE_JD = 2460000.5  # arbitrary valid JD for all tests

# Synthetic cusp-degree data matching L1 fact schema
# fact_subject='BHAVA_07', fact_key='sripati_madhya', fact_value_num=195.0
_CUSP_MAP = {
    "BHAVA_07": {"deg": 195.0, "fact_id": "fact-bhava07-sripati-madhya"},
    "BHAVA_01": {"deg": 10.5,  "fact_id": "fact-bhava01-sripati-madhya"},
    "BHAVA_10": {"deg": 280.3, "fact_id": "fact-bhava10-sripati-madhya"},
}


# ── Tests ───────────────────────────────────────────────────────────────────


def test_disabled_returns_empty_sentences():
    """enabled=False must return modifier==1.0, empty sentences, enabled==False."""
    natal = _MockNatalFacts(bhava_cusp_degrees=_CUSP_MAP)
    ctx = _MockContext(
        resonance_targets=(
            _MockResonanceTarget(target_type="bhava", target_ref="7"),
        ),
        natal_facts=natal,
    )
    result = compute(ctx, _SAMPLE_JD, enabled=False)

    assert isinstance(result, MechanismResult)
    assert result.modifier == 1.0, f"Expected 1.0, got {result.modifier}"
    assert result.sentences == [], f"Expected empty sentences, got {result.sentences}"
    assert result.enabled is False
    assert result.mechanism_id == MECHANISM_ID


def test_modifier_always_unit():
    """modifier must always be 1.0 — this mechanism produces sentences, not a modifier.

    This invariant holds across: disabled, no targets, targets with data,
    targets without data, mixed resolved/unresolved targets.
    """
    natal = _MockNatalFacts(bhava_cusp_degrees=_CUSP_MAP)

    test_cases = [
        # (targets, natal_facts, enabled)
        ((), None, True),                # no targets, no facts
        ((), natal, True),               # no targets, with facts
        (
            (_MockResonanceTarget(target_type="bhava", target_ref="7"),),
            natal, True,
        ),                               # resolved target
        (
            (_MockResonanceTarget(target_type="bhava", target_ref="7"),),
            None, True,
        ),                               # target but no facts
        (
            (_MockResonanceTarget(target_type="karaka", target_ref="Venus"),),
            natal, True,
        ),                               # non-bhava target only
        (
            (_MockResonanceTarget(target_type="bhava", target_ref="7"),),
            natal, False,
        ),                               # disabled
    ]

    for targets, nf, ena in test_cases:
        ctx = _MockContext(resonance_targets=targets, natal_facts=nf)
        result = compute(ctx, _SAMPLE_JD, enabled=ena)
        assert result.modifier == 1.0, (
            f"modifier must always be 1.0, got {result.modifier} "
            f"for targets={[t.target_ref for t in targets]}, "
            f"natal_facts={'set' if nf else None}, enabled={ena}"
        )


def test_resolves_bhava_targets():
    """Bhava targets with matching cusp data -> one sentence per resolved target.

    Each sentence must carry:
      - target_ref matching the target's house number
      - cusp_deg matching the L1 fact value
      - bhava_subject in "BHAVA_NN" format
      - a non-empty note
    """
    natal = _MockNatalFacts(bhava_cusp_degrees=_CUSP_MAP)
    ctx = _MockContext(
        resonance_targets=(
            _MockResonanceTarget(target_type="bhava", target_ref="7",
                                 event_class="marriage", weight=0.9),
            _MockResonanceTarget(target_type="bhava", target_ref="1",
                                 event_class="career", weight=0.8),
        ),
        natal_facts=natal,
    )
    result = compute(ctx, _SAMPLE_JD, enabled=True)

    assert result.enabled is True
    assert result.modifier == 1.0
    assert len(result.sentences) == 2, (
        f"Expected 2 sentences for 2 resolved bhava targets, got {len(result.sentences)}"
    )

    # Check bhava 7 sentence
    s7 = next(s for s in result.sentences if s["target_ref"] == "7")
    assert s7["bhava_subject"] == "BHAVA_07"
    assert abs(s7["cusp_deg"] - 195.0) < 0.001, f"cusp_deg mismatch: {s7['cusp_deg']}"
    assert s7["mechanism_id"] == MECHANISM_ID
    assert s7["t_jd"] == _SAMPLE_JD
    assert s7["note"], "note must be non-empty"

    # Check bhava 1 sentence
    s1 = next(s for s in result.sentences if s["target_ref"] == "1")
    assert s1["bhava_subject"] == "BHAVA_01"
    assert abs(s1["cusp_deg"] - 10.5) < 0.001, f"cusp_deg mismatch: {s1['cusp_deg']}"

    # detail must report counts correctly
    assert result.detail["resolved_count"] == 2
    assert result.detail["bhava_targets_total"] == 2
    assert result.detail["unresolved_refs"] == []


def test_honest_empty_when_no_natal_facts():
    """natal_facts=None -> sentences==[], honest detail (no silent false positive).

    An empty result is correct and expected: the mechanism cannot enrich
    without L1 data. This must never be reported as a success or crash.
    """
    ctx = _MockContext(
        resonance_targets=(
            _MockResonanceTarget(target_type="bhava", target_ref="7"),
        ),
        natal_facts=None,
    )
    result = compute(ctx, _SAMPLE_JD, enabled=True)

    assert result.sentences == [], (
        f"Expected empty sentences with no natal_facts, got {result.sentences}"
    )
    assert result.modifier == 1.0
    assert result.enabled is True
    assert "reason" in result.detail, "detail must carry 'reason' key"
    assert result.detail["reason"] == "no_natal_facts_cusp_data", (
        f"Expected 'no_natal_facts_cusp_data', got {result.detail.get('reason')}"
    )


def test_no_bhava_targets_returns_empty_sentences():
    """Context with only non-bhava targets -> sentences==[], reason='no_bhava_targets'."""
    natal = _MockNatalFacts(bhava_cusp_degrees=_CUSP_MAP)
    ctx = _MockContext(
        resonance_targets=(
            _MockResonanceTarget(target_type="karaka", target_ref="Venus"),
            _MockResonanceTarget(target_type="lord", target_ref="10"),
        ),
        natal_facts=natal,
    )
    result = compute(ctx, _SAMPLE_JD, enabled=True)

    assert result.sentences == []
    assert result.modifier == 1.0
    assert result.detail["reason"] == "no_bhava_targets"


def test_sentence_carries_fact_id_reference():
    """Each resolved sentence must carry a non-empty fact_id (§N.5 L1 reference).

    fact_id links the cusp degree back to the specific chart_facts row it was
    read from. An empty or missing fact_id violates §N.5 (L1 authority).
    """
    natal = _MockNatalFacts(bhava_cusp_degrees=_CUSP_MAP)
    ctx = _MockContext(
        resonance_targets=(
            _MockResonanceTarget(target_type="bhava", target_ref="7"),
            _MockResonanceTarget(target_type="bhava", target_ref="10"),
        ),
        natal_facts=natal,
    )
    result = compute(ctx, _SAMPLE_JD, enabled=True)

    assert len(result.sentences) == 2
    for sentence in result.sentences:
        fact_id = sentence.get("fact_id", "")
        assert fact_id, (
            f"sentence for target_ref={sentence.get('target_ref')} "
            f"must carry a non-empty fact_id (§N.5), got {fact_id!r}"
        )


def test_unresolvable_bhava_ref_does_not_crash():
    """target_ref that is not a valid 1-12 integer is reported as unresolved, not a crash.

    Robust to: non-numeric refs ("7a", ""), out-of-range (0, 13, -1).
    """
    natal = _MockNatalFacts(bhava_cusp_degrees=_CUSP_MAP)
    bad_targets = (
        _MockResonanceTarget(target_type="bhava", target_ref="7a"),   # non-numeric
        _MockResonanceTarget(target_type="bhava", target_ref=""),     # empty
        _MockResonanceTarget(target_type="bhava", target_ref="13"),   # out of range
        _MockResonanceTarget(target_type="bhava", target_ref="0"),    # out of range
        _MockResonanceTarget(target_type="bhava", target_ref="7"),    # valid — one good one
    )
    ctx = _MockContext(resonance_targets=bad_targets, natal_facts=natal)
    result = compute(ctx, _SAMPLE_JD, enabled=True)

    # Must not raise; should resolve only the valid "7" target
    assert result.modifier == 1.0
    assert len(result.sentences) == 1, (
        f"Expected only 1 resolved sentence (bhava 7), got {len(result.sentences)}"
    )
    assert result.sentences[0]["target_ref"] == "7"

    # Unresolvable refs reported honestly in detail
    unresolved = result.detail.get("unresolved_refs", [])
    assert len(unresolved) == 4, (
        f"Expected 4 unresolved refs (7a, '', 13, 0), got {unresolved}"
    )


def test_mechanism_id_is_constant_on_all_variants():
    """mechanism_id on all result variants equals MECHANISM_ID."""
    natal = _MockNatalFacts(bhava_cusp_degrees=_CUSP_MAP)

    variants = [
        # (targets, natal_facts, enabled)
        ((), None, True),                             # no targets
        ((), natal, True),                            # no targets, with facts
        (
            (_MockResonanceTarget(target_type="bhava", target_ref="7"),),
            natal, True,
        ),                                            # resolved
        (
            (_MockResonanceTarget(target_type="bhava", target_ref="7"),),
            None, True,
        ),                                            # unresolvable
        (
            (_MockResonanceTarget(target_type="bhava", target_ref="7"),),
            natal, False,
        ),                                            # disabled
    ]

    for targets, nf, ena in variants:
        ctx = _MockContext(resonance_targets=targets, natal_facts=nf)
        result = compute(ctx, _SAMPLE_JD, enabled=ena)
        assert result.mechanism_id == MECHANISM_ID, (
            f"mechanism_id mismatch: expected {MECHANISM_ID!r}, "
            f"got {result.mechanism_id!r} "
            f"(targets={[t.target_ref for t in targets]}, enabled={ena})"
        )


def test_toggle_key_is_defined():
    """TOGGLE_KEY must be defined and non-empty — used for wave-4 wiring."""
    assert TOGGLE_KEY, "TOGGLE_KEY must be a non-empty string"
    assert isinstance(TOGGLE_KEY, str)


def test_partial_cusp_map_resolves_available_only():
    """Cusp map with only some bhavas -> resolves what it has, no crash for missing."""
    sparse_cusp_map = {
        "BHAVA_07": {"deg": 195.0, "fact_id": "fact-bhava07"},
        # BHAVA_01 absent
    }
    natal = _MockNatalFacts(bhava_cusp_degrees=sparse_cusp_map)
    ctx = _MockContext(
        resonance_targets=(
            _MockResonanceTarget(target_type="bhava", target_ref="7"),  # present
            _MockResonanceTarget(target_type="bhava", target_ref="1"),  # absent in map
        ),
        natal_facts=natal,
    )
    result = compute(ctx, _SAMPLE_JD, enabled=True)

    assert len(result.sentences) == 1
    assert result.sentences[0]["target_ref"] == "7"
    assert "1" in result.detail["unresolved_refs"]
    assert result.modifier == 1.0
