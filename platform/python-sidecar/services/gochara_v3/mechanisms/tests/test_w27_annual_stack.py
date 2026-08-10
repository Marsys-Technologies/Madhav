"""
Tests for W2.7 — annual context stack mechanism.

All tests are fixture-based (no DB connection required), per lane constraint.

Test inventory
--------------
1. test_disabled_returns_unit
   Master enabled=False → combined modifier==1.0, empty sentences, enabled==False.

2. test_honest_when_no_annual_data
   All three sub-mechanism context attrs absent → all sub-modifiers==1.0,
   combined modifier==1.0, detail.reason=="no_annual_data" on each sub.

3. test_tajaka_year_lord_fires
   Synthetic context with matching year-lord in resonance targets → modifier > 1.0.

4. test_combined_modifiers_in_range
   Combined modifier is always in [0.0, 2.0] across edge-case inputs.

5. test_each_submechanism_independently_disableable
   enabled_a=False, enabled_b=True, enabled_c=True → sub_a disabled (modifier==1.0),
   sub_b and sub_c compute normally.

6. test_tithi_pravesha_favourable_fires
   Pravesha tone "favourable" → sub_b modifier > 1.0.

7. test_tithi_pravesha_adverse_fires
   Pravesha tone "adverse" → sub_b modifier < 1.0.

8. test_sudarshana_kendra_amplifies
   Sudarshana house 1 (kendra) → sub_c modifier > 1.0.

9. test_sudarshana_dusthana_damps
   Sudarshana house 8 (dusthana) → sub_c modifier < 1.0.

10. test_modifier_bounds_enforced_always
    Sub-mechanism modifiers and combined modifier always in [0.0, 2.0].

11. test_year_lord_no_match_neutral
    Year-lord is NOT in resonance targets → modifier == 1.0.

12. test_all_three_disabled_independently
    All three sub-toggles False → combined modifier == 1.0.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any

import pytest

from services.gochara_v3.mechanisms.w27_annual_stack import (
    MECHANISM_ID,
    MECHANISM_ID_A,
    MECHANISM_ID_B,
    MECHANISM_ID_C,
    MODIFIER_MIN,
    MODIFIER_MAX,
    MODIFIER_NEUTRAL,
    MechanismResult,
    compute,
    compute_tajaka_year_lord,
    compute_tithi_pravesha,
    compute_sudarshana,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────

_SAMPLE_JD = 2460450.5  # ~2024-06-01, within varsha starting 2024


@dataclass
class _MockTarget:
    """Minimal resonance target stand-in."""
    graha: str
    target_ref: str = "7"
    weight: float = 0.5
    event_class: str = "marriage"


@dataclass
class _MockContext:
    """Minimal ClassContext-like object for W2.7 tests.

    All annual data attrs default to None/empty so each test populates
    only the fields it needs.
    """
    chart_id: str = "test-chart-id"
    event_class: str = "marriage"
    resonance_targets: tuple = field(default_factory=tuple)
    relevant_grahas: frozenset = field(default_factory=frozenset)
    # W2.7 specific optional attrs
    tajaka_year_lords: Optional[list] = None
    annual_data: Optional[list] = None
    tithi_pravesha_rows: Optional[list] = None
    sudarshana_rows: Optional[list] = None


def _make_year_lord_row(year_lord: str, varsha_year: int = 40) -> dict:
    """Build a synthetic l1_tajik_varsha_year_lords-like row."""
    return {
        "varsha_year": varsha_year,
        "year_lord": year_lord,
        "varsha_start_iso": "2024-02-05",
        "varsha_end_iso": "2025-02-04",
        "year_lord_method": "pancha_varsheshvara",
    }


def _make_pravesha_row(tone: str, event_class: str = "marriage") -> dict:
    """Build a synthetic kala_tithi_pravesha-like row."""
    return {
        "event_class": event_class,
        "tone": tone,
        "varsha_start_iso": "2024-02-05",
        "varsha_end_iso": "2025-02-04",
    }


def _make_sudarshana_row(graha: str, house: int) -> dict:
    """Build a synthetic sudarshana-like row."""
    return {
        "graha": graha,
        "house_number": house,
        "window_start_iso": "2024-02-05",
        "window_end_iso": "2025-02-04",
    }


# ── Tests ────────────────────────────────────────────────────────────────────


def test_disabled_returns_unit():
    """Master enabled=False → combined modifier==1.0, enabled==False, sentences empty."""
    ctx = _MockContext(
        tajaka_year_lords=[_make_year_lord_row("Venus")],
        resonance_targets=(_MockTarget(graha="Venus"),),
    )
    result = compute(ctx, _SAMPLE_JD, enabled=False)

    assert isinstance(result, MechanismResult)
    assert result.modifier == MODIFIER_NEUTRAL, f"expected 1.0, got {result.modifier}"
    assert result.enabled is False
    assert result.sentences == []
    assert result.mechanism_id == MECHANISM_ID
    assert result.detail.get("reason") == "disabled"


def test_honest_when_no_annual_data():
    """All three sub-mechanisms without data → all modifiers == 1.0, honest detail."""
    ctx = _MockContext()  # no annual data at all
    result = compute(ctx, _SAMPLE_JD, enabled=True)

    assert result.modifier == MODIFIER_NEUTRAL, f"expected 1.0, got {result.modifier}"
    assert result.enabled is True
    assert result.mechanism_id == MECHANISM_ID

    # Each sub-mechanism should report no_annual_data
    sub = result.detail.get("sub_mechanisms", {})
    assert sub[MECHANISM_ID_A].get("reason") == "no_annual_data", (
        f"sub_a detail: {sub.get(MECHANISM_ID_A)}"
    )
    assert sub[MECHANISM_ID_B].get("reason") == "no_annual_data", (
        f"sub_b detail: {sub.get(MECHANISM_ID_B)}"
    )
    assert sub[MECHANISM_ID_C].get("reason") == "no_annual_data", (
        f"sub_c detail: {sub.get(MECHANISM_ID_C)}"
    )


def test_tajaka_year_lord_fires():
    """Matching year-lord in resonance targets → sub_a modifier > 1.0."""
    ctx = _MockContext(
        tajaka_year_lords=[_make_year_lord_row("Venus")],
        resonance_targets=(_MockTarget(graha="Venus"),),
        relevant_grahas=frozenset({"Venus"}),
    )
    result_a = compute_tajaka_year_lord(ctx, _SAMPLE_JD, enabled=True)

    assert result_a.modifier > MODIFIER_NEUTRAL, (
        f"Expected modifier > 1.0 for year-lord match, got {result_a.modifier}"
    )
    assert result_a.enabled is True
    assert result_a.mechanism_id == MECHANISM_ID_A
    assert len(result_a.sentences) == 1
    assert result_a.sentences[0]["classification"] == "year_lord_match"


def test_combined_modifiers_in_range():
    """Combined modifier must always be in [MODIFIER_MIN, MODIFIER_MAX]."""
    test_cases = [
        # empty context
        _MockContext(),
        # favourable everything
        _MockContext(
            tajaka_year_lords=[_make_year_lord_row("Venus")],
            tithi_pravesha_rows=[_make_pravesha_row("favourable")],
            sudarshana_rows=[_make_sudarshana_row("Venus", 1)],
            resonance_targets=(_MockTarget(graha="Venus"),),
            relevant_grahas=frozenset({"Venus"}),
        ),
        # adverse everything
        _MockContext(
            tajaka_year_lords=[_make_year_lord_row("Saturn")],
            tithi_pravesha_rows=[_make_pravesha_row("adverse")],
            sudarshana_rows=[_make_sudarshana_row("Venus", 8)],
            resonance_targets=(_MockTarget(graha="Venus"),),
            relevant_grahas=frozenset({"Venus"}),
        ),
        # mixed
        _MockContext(
            tajaka_year_lords=[_make_year_lord_row("Venus")],
            tithi_pravesha_rows=[_make_pravesha_row("mixed")],
            sudarshana_rows=[_make_sudarshana_row("Venus", 6)],
            resonance_targets=(_MockTarget(graha="Venus"),),
            relevant_grahas=frozenset({"Venus"}),
        ),
    ]

    for ctx in test_cases:
        result = compute(ctx, _SAMPLE_JD, enabled=True)
        assert MODIFIER_MIN <= result.modifier <= MODIFIER_MAX, (
            f"modifier={result.modifier} out of [{MODIFIER_MIN}, {MODIFIER_MAX}]"
        )
        # Each sub also in range
        for mech_id in (MECHANISM_ID_A, MECHANISM_ID_B, MECHANISM_ID_C):
            sub_mod = result.detail.get("sub_modifiers", {}).get(mech_id, 1.0)
            assert MODIFIER_MIN <= sub_mod <= MODIFIER_MAX, (
                f"{mech_id} sub_modifier={sub_mod} out of range"
            )


def test_each_submechanism_independently_disableable():
    """enabled_a=False leaves sub_a disabled while sub_b/sub_c compute normally."""
    ctx = _MockContext(
        tajaka_year_lords=[_make_year_lord_row("Venus")],
        tithi_pravesha_rows=[_make_pravesha_row("favourable")],
        sudarshana_rows=[_make_sudarshana_row("Venus", 10)],
        resonance_targets=(_MockTarget(graha="Venus"),),
        relevant_grahas=frozenset({"Venus"}),
    )

    result = compute(ctx, _SAMPLE_JD, enabled=True, enabled_a=False, enabled_b=True, enabled_c=True)

    # sub_a disabled → modifier == 1.0
    sub_a_mod = result.detail["sub_modifiers"][MECHANISM_ID_A]
    assert sub_a_mod == MODIFIER_NEUTRAL, f"sub_a should be 1.0 (disabled), got {sub_a_mod}"

    # sub_b favourable → modifier > 1.0
    sub_b_mod = result.detail["sub_modifiers"][MECHANISM_ID_B]
    assert sub_b_mod > MODIFIER_NEUTRAL, f"sub_b (favourable) should be > 1.0, got {sub_b_mod}"

    # sub_c house 10 (kendra) → modifier > 1.0
    sub_c_mod = result.detail["sub_modifiers"][MECHANISM_ID_C]
    assert sub_c_mod > MODIFIER_NEUTRAL, f"sub_c (house 10) should be > 1.0, got {sub_c_mod}"

    # enabled flags are recorded
    flags = result.detail["enabled_flags"]
    assert flags[MECHANISM_ID_A] is False
    assert flags[MECHANISM_ID_B] is True
    assert flags[MECHANISM_ID_C] is True


def test_tithi_pravesha_favourable_fires():
    """Pravesha tone 'favourable' → sub_b modifier > 1.0."""
    ctx = _MockContext(
        tithi_pravesha_rows=[_make_pravesha_row("favourable", "marriage")],
        event_class="marriage",
    )
    result_b = compute_tithi_pravesha(ctx, _SAMPLE_JD, enabled=True)

    assert result_b.modifier > MODIFIER_NEUTRAL, (
        f"Expected modifier > 1.0 for favourable tone, got {result_b.modifier}"
    )
    assert result_b.enabled is True
    assert result_b.mechanism_id == MECHANISM_ID_B
    assert result_b.sentences[0]["tone"] == "favourable"


def test_tithi_pravesha_adverse_fires():
    """Pravesha tone 'adverse' → sub_b modifier < 1.0."""
    ctx = _MockContext(
        tithi_pravesha_rows=[_make_pravesha_row("adverse", "marriage")],
        event_class="marriage",
    )
    result_b = compute_tithi_pravesha(ctx, _SAMPLE_JD, enabled=True)

    assert result_b.modifier < MODIFIER_NEUTRAL, (
        f"Expected modifier < 1.0 for adverse tone, got {result_b.modifier}"
    )
    assert result_b.sentences[0]["tone"] == "adverse"


def test_sudarshana_kendra_amplifies():
    """Sudarshana house 1 (kendra) → sub_c modifier > 1.0."""
    ctx = _MockContext(
        sudarshana_rows=[_make_sudarshana_row("Venus", 1)],
        resonance_targets=(_MockTarget(graha="Venus"),),
        relevant_grahas=frozenset({"Venus"}),
    )
    result_c = compute_sudarshana(ctx, _SAMPLE_JD, enabled=True)

    assert result_c.modifier > MODIFIER_NEUTRAL, (
        f"Expected modifier > 1.0 for house 1 (kendra), got {result_c.modifier}"
    )
    assert result_c.sentences[0]["house_number"] == 1


def test_sudarshana_dusthana_damps():
    """Sudarshana house 8 (dusthana) → sub_c modifier < 1.0."""
    ctx = _MockContext(
        sudarshana_rows=[_make_sudarshana_row("Venus", 8)],
        resonance_targets=(_MockTarget(graha="Venus"),),
        relevant_grahas=frozenset({"Venus"}),
    )
    result_c = compute_sudarshana(ctx, _SAMPLE_JD, enabled=True)

    assert result_c.modifier < MODIFIER_NEUTRAL, (
        f"Expected modifier < 1.0 for house 8 (dusthana), got {result_c.modifier}"
    )
    assert result_c.sentences[0]["house_number"] == 8


def test_modifier_bounds_enforced_always():
    """Every compute call (sub and combined) returns modifier in [0.0, 2.0]."""
    extremes = [
        _MockContext(),
        _MockContext(
            tajaka_year_lords=[_make_year_lord_row("Venus")],
            tithi_pravesha_rows=[_make_pravesha_row("favourable")],
            sudarshana_rows=[_make_sudarshana_row("Venus", 1)],
            resonance_targets=(_MockTarget(graha="Venus"),),
            relevant_grahas=frozenset({"Venus"}),
        ),
        _MockContext(
            tajaka_year_lords=[_make_year_lord_row("Saturn")],
            tithi_pravesha_rows=[_make_pravesha_row("adverse")],
            sudarshana_rows=[_make_sudarshana_row("Venus", 8)],
            resonance_targets=(_MockTarget(graha="Venus"),),
            relevant_grahas=frozenset({"Venus"}),
        ),
    ]

    for ctx in extremes:
        for enabled in (True, False):
            r = compute(ctx, _SAMPLE_JD, enabled=enabled)
            assert MODIFIER_MIN <= r.modifier <= MODIFIER_MAX, (
                f"compute() modifier={r.modifier} out of bounds"
            )
        for fn in (compute_tajaka_year_lord, compute_tithi_pravesha, compute_sudarshana):
            for enabled in (True, False):
                r = fn(ctx, _SAMPLE_JD, enabled=enabled)
                assert MODIFIER_MIN <= r.modifier <= MODIFIER_MAX, (
                    f"{fn.__name__} modifier={r.modifier} out of bounds"
                )


def test_year_lord_no_match_neutral():
    """Year-lord NOT in resonance targets → sub_a modifier == 1.0."""
    ctx = _MockContext(
        tajaka_year_lords=[_make_year_lord_row("Saturn")],  # Saturn is year-lord
        resonance_targets=(_MockTarget(graha="Venus"),),     # Venus is target, not Saturn
        relevant_grahas=frozenset({"Venus"}),
    )
    result_a = compute_tajaka_year_lord(ctx, _SAMPLE_JD, enabled=True)

    assert result_a.modifier == MODIFIER_NEUTRAL, (
        f"Expected 1.0 (no year-lord match), got {result_a.modifier}"
    )
    assert result_a.sentences[0]["classification"] == "year_lord_no_match"


def test_all_three_disabled_independently():
    """All three sub-toggles False → combined modifier == 1.0."""
    ctx = _MockContext(
        tajaka_year_lords=[_make_year_lord_row("Venus")],
        tithi_pravesha_rows=[_make_pravesha_row("favourable")],
        sudarshana_rows=[_make_sudarshana_row("Venus", 1)],
        resonance_targets=(_MockTarget(graha="Venus"),),
        relevant_grahas=frozenset({"Venus"}),
    )
    result = compute(
        ctx, _SAMPLE_JD,
        enabled=True,
        enabled_a=False,
        enabled_b=False,
        enabled_c=False,
    )

    # All sub-modifiers are 1.0 (disabled)
    for mech_id in (MECHANISM_ID_A, MECHANISM_ID_B, MECHANISM_ID_C):
        sub_mod = result.detail["sub_modifiers"][mech_id]
        assert sub_mod == MODIFIER_NEUTRAL, (
            f"{mech_id} should be 1.0 (disabled), got {sub_mod}"
        )

    # Combined = 1.0 * 1.0 * 1.0 = 1.0
    assert result.modifier == MODIFIER_NEUTRAL, (
        f"Combined modifier with all subs disabled should be 1.0, got {result.modifier}"
    )
    assert result.enabled is True  # master switch still on


def test_result_has_correct_mechanism_ids():
    """mechanism_id on all result variants matches the expected constant."""
    ctx = _MockContext()

    assert compute(ctx, _SAMPLE_JD, enabled=False).mechanism_id == MECHANISM_ID
    assert compute(ctx, _SAMPLE_JD, enabled=True).mechanism_id == MECHANISM_ID
    assert compute_tajaka_year_lord(ctx, _SAMPLE_JD).mechanism_id == MECHANISM_ID_A
    assert compute_tithi_pravesha(ctx, _SAMPLE_JD).mechanism_id == MECHANISM_ID_B
    assert compute_sudarshana(ctx, _SAMPLE_JD).mechanism_id == MECHANISM_ID_C
