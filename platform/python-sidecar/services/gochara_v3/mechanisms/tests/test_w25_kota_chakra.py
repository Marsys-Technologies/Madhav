"""
Tests for W2.5 — Kota Chakra ring modifier mechanism.

All tests are fixture-based (no DB access). The mechanism is DORMANT (not
wired into engine.py) and must behave as a pure function of context + t_jd.

Coverage
--------
  test_disabled_returns_unit_modifier
      enabled=False always returns modifier==1.0 regardless of context or class.

  test_non_siege_class_returns_unit
      A gain/neutral event class (e.g. "career_gain") returns modifier==1.0
      because Kota Chakra siege amplification is only for adverse classes.

  test_stambha_amplifies_adverse
      An adverse event class (illness_acute) with Saturn in the stambha ring
      returns modifier==1.30 and enabled==True.

  test_honest_when_no_kota_data
      A context with NO kota field returns modifier==1.0 with an honest detail
      note indicating that kota_data is not yet in ClassContext (W0.2 dependency).

  test_all_ring_modifiers_correct
      Each valid ring name produces the documented modifier value.

  test_non_malefic_in_ring_returns_none_modifier
      If only a non-malefic graha (e.g. Jupiter) is in a ring, no siege
      amplification fires — modifier==1.0.

  test_bahya_ring_adverse_class
      bahya ring (outermost) with Mars → modifier==1.04.

  test_madhya_ring_adverse_class
      madhya ring with Saturn → modifier==1.15.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import MagicMock

import pytest

from services.gochara_v3.mechanisms import MechanismResult
from services.gochara_v3.mechanisms.w25_kota_chakra import (
    MECHANISM_ID,
    RING_MODIFIERS,
    SIEGE_CLASSES,
    compute,
)

# ---------------------------------------------------------------------------
# Fixtures: minimal ClassContext stand-ins (no DB, no imports of gochara_v3.context)
# ---------------------------------------------------------------------------

@dataclass
class _FakeContext:
    """Minimal stand-in for ClassContext; only carries fields the mechanism reads."""
    event_class: str
    # kota_chakra_data: dict or absent (None = field not present in ClassContext yet)
    kota_chakra_data: Optional[dict] = None


def _ctx(event_class: str, kota_chakra_data=None) -> _FakeContext:
    """Build a fake context for testing."""
    return _FakeContext(event_class=event_class, kota_chakra_data=kota_chakra_data)


def _ctx_no_kota(event_class: str) -> object:
    """Context with NO kota attribute at all — simulates current ClassContext state."""
    ctx = MagicMock(spec=[])  # spec=[] means no attributes will be found
    ctx.event_class = event_class
    return ctx


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDisabled:
    def test_disabled_returns_unit_modifier(self):
        """enabled=False must return modifier==1.0 regardless of context."""
        ctx = _ctx("illness_acute", kota_chakra_data={"Saturn": "stambha"})
        result = compute(ctx, t_jd=2461042.0, enabled=False)

        assert isinstance(result, MechanismResult)
        assert result.mechanism_id == MECHANISM_ID
        assert result.modifier == 1.0, (
            f"disabled mechanism must return unit modifier, got {result.modifier}"
        )
        assert result.enabled is False
        assert "disabled" in result.detail.lower()


class TestNonSiegeClass:
    def test_non_siege_class_returns_unit(self):
        """A gain-class event returns modifier==1.0 — Kota is adverse-only."""
        assert "career_gain" not in SIEGE_CLASSES, (
            "test precondition: career_gain must NOT be in SIEGE_CLASSES"
        )
        ctx = _ctx("career_gain", kota_chakra_data={"Saturn": "stambha"})
        result = compute(ctx, t_jd=2461042.0, enabled=True)

        assert result.modifier == 1.0, (
            f"non-siege event class must return unit modifier, got {result.modifier}"
        )
        assert result.enabled is False
        assert "not in SIEGE_CLASSES" in result.detail or "not applicable" in result.detail.lower()

    def test_marriage_class_returns_unit(self):
        """Marriage is not a siege class — unit modifier expected."""
        ctx = _ctx("marriage", kota_chakra_data={"Mars": "madhya"})
        result = compute(ctx, t_jd=2461042.0, enabled=True)
        assert result.modifier == 1.0
        assert result.enabled is False

    def test_wealth_gain_returns_unit(self):
        """wealth_gain is not in SIEGE_CLASSES — unit modifier."""
        ctx = _ctx("wealth_gain", kota_chakra_data={"Saturn": "pragara"})
        result = compute(ctx, t_jd=2461042.0, enabled=True)
        assert result.modifier == 1.0
        assert result.enabled is False


class TestStambhaAmplifies:
    def test_stambha_amplifies_adverse(self):
        """illness_acute + Saturn in stambha → modifier==1.30."""
        assert "illness_acute" in SIEGE_CLASSES
        ctx = _ctx("illness_acute", kota_chakra_data={"Saturn": "stambha"})
        result = compute(ctx, t_jd=2461042.0, enabled=True)

        assert result.enabled is True
        assert result.modifier == pytest.approx(1.30), (
            f"stambha ring must return modifier 1.30, got {result.modifier}"
        )
        assert result.mechanism_id == MECHANISM_ID
        assert "stambha" in result.detail

    def test_stambha_with_mars_amplifies_adverse(self):
        """chronic_onset + Mars in stambha → modifier==1.30."""
        ctx = _ctx("chronic_onset", kota_chakra_data={"Mars": "stambha"})
        result = compute(ctx, t_jd=2461042.0, enabled=True)

        assert result.enabled is True
        assert result.modifier == pytest.approx(1.30)


class TestHonestWhenNoKotaData:
    def test_honest_when_no_kota_data_missing_attribute(self):
        """Context with no kota attribute → modifier==1.0 with honest detail."""
        ctx = _ctx_no_kota("illness_acute")
        result = compute(ctx, t_jd=2461042.0, enabled=True)

        assert result.modifier == 1.0, (
            f"no kota data must return unit modifier, got {result.modifier}"
        )
        assert result.enabled is False
        assert "kota_data not in ClassContext" in result.detail or "W0.2" in result.detail, (
            f"detail must reference the missing data path; got: {result.detail!r}"
        )

    def test_honest_when_no_kota_data_none_value(self):
        """Context with kota_chakra_data=None → modifier==1.0 (no siege data)."""
        ctx = _ctx("illness_acute", kota_chakra_data=None)
        result = compute(ctx, t_jd=2461042.0, enabled=True)

        assert result.modifier == 1.0
        assert result.enabled is False
        assert "kota_data not in ClassContext" in result.detail or "W0.2" in result.detail

    def test_honest_when_kota_data_empty_dict(self):
        """Empty kota_chakra_data dict → no malefic in any ring → modifier==1.0."""
        ctx = _ctx("illness_acute", kota_chakra_data={})
        # Empty dict IS present, so it doesn't trigger "no kota data" path.
        # It should instead find no malefic in any ring → ring="none" → modifier=1.0.
        result = compute(ctx, t_jd=2461042.0, enabled=True)

        assert result.modifier == 1.0


class TestAllRingModifiers:
    def test_all_ring_modifiers_correct(self):
        """Each ring name produces the documented modifier for an adverse class."""
        expected = {
            "stambha": 1.30,
            "madhya": 1.15,
            "pragara": 1.08,
            "bahya": 1.04,
        }
        for ring, expected_mod in expected.items():
            ctx = _ctx("illness_acute", kota_chakra_data={"Saturn": ring})
            result = compute(ctx, t_jd=2461042.0, enabled=True)
            assert result.modifier == pytest.approx(expected_mod), (
                f"ring={ring!r}: expected modifier {expected_mod}, got {result.modifier}"
            )
            assert result.enabled is True

    def test_none_ring_returns_unit(self):
        """'none' ring key → modifier==1.0."""
        ctx = _ctx("illness_acute", kota_chakra_data={"Saturn": "none"})
        result = compute(ctx, t_jd=2461042.0, enabled=True)
        # "none" is not a VALID_RING, so no malefic is treated as in a siege ring.
        # Should fall back to ring="none" → modifier=1.0.
        assert result.modifier == 1.0


class TestBahyaRing:
    def test_bahya_ring_adverse_class(self):
        """bahya + Mars + accident → modifier==1.04."""
        assert "accident" in SIEGE_CLASSES
        ctx = _ctx("accident", kota_chakra_data={"Mars": "bahya"})
        result = compute(ctx, t_jd=2461042.0, enabled=True)

        assert result.enabled is True
        assert result.modifier == pytest.approx(1.04)
        assert "bahya" in result.detail


class TestMadhyaRing:
    def test_madhya_ring_adverse_class(self):
        """madhya + Saturn + loss → modifier==1.15."""
        assert "loss" in SIEGE_CLASSES
        ctx = _ctx("loss", kota_chakra_data={"Saturn": "madhya"})
        result = compute(ctx, t_jd=2461042.0, enabled=True)

        assert result.enabled is True
        assert result.modifier == pytest.approx(1.15)
        assert "madhya" in result.detail


class TestNonMaleficInRing:
    def test_non_malefic_in_ring_returns_unit_modifier(self):
        """Jupiter in stambha — not a KOTA_MALEFIC — no siege amplification."""
        ctx = _ctx("illness_acute", kota_chakra_data={"Jupiter": "stambha"})
        result = compute(ctx, t_jd=2461042.0, enabled=True)
        # Jupiter is not in KOTA_MALEFICS; no ring siege fires.
        assert result.modifier == 1.0

    def test_venus_in_ring_returns_unit_modifier(self):
        """Venus in madhya — not a KOTA_MALEFIC — no siege amplification."""
        ctx = _ctx("chronic_onset", kota_chakra_data={"Venus": "madhya"})
        result = compute(ctx, t_jd=2461042.0, enabled=True)
        assert result.modifier == 1.0


class TestInnermostRingPriority:
    def test_innermost_ring_wins_when_multiple_malefics(self):
        """When both Saturn (stambha) and Mars (bahya) are in rings,
        the innermost (stambha) modifier wins."""
        ctx = _ctx("illness_acute", kota_chakra_data={
            "Saturn": "stambha",
            "Mars": "bahya",
        })
        result = compute(ctx, t_jd=2461042.0, enabled=True)
        # stambha is innermost, so modifier=1.30 takes priority over bahya=1.04.
        assert result.modifier == pytest.approx(1.30)
        assert "stambha" in result.detail

    def test_innermost_ring_wins_madhya_over_pragara(self):
        """madhya (Saturn) vs pragara (Mars) → madhya wins."""
        ctx = _ctx("accident", kota_chakra_data={
            "Saturn": "madhya",
            "Mars": "pragara",
        })
        result = compute(ctx, t_jd=2461042.0, enabled=True)
        assert result.modifier == pytest.approx(1.15)
        assert "madhya" in result.detail


class TestMechanismResultContract:
    def test_mechanism_result_id_is_correct(self):
        """Every result must carry the canonical mechanism_id."""
        ctx = _ctx("illness_acute", kota_chakra_data={"Saturn": "stambha"})
        result = compute(ctx, t_jd=2461042.0, enabled=True)
        assert result.mechanism_id == "w25_kota_chakra"

    def test_result_detail_always_non_empty(self):
        """detail must always be a non-empty string."""
        for enabled in (True, False):
            for ec in ("illness_acute", "career_gain"):
                ctx = _ctx(ec, kota_chakra_data=None)
                result = compute(ctx, t_jd=2461042.0, enabled=enabled)
                assert isinstance(result.detail, str) and len(result.detail) > 0, (
                    f"detail must be non-empty; enabled={enabled}, event_class={ec!r}"
                )

    def test_modifier_is_always_non_negative(self):
        """modifier must always be >= 0 (MechanismResult contract)."""
        for ring in ("stambha", "madhya", "pragara", "bahya", "none"):
            ctx = _ctx("illness_acute", kota_chakra_data={"Saturn": ring})
            result = compute(ctx, t_jd=2461042.0, enabled=True)
            assert result.modifier >= 0.0
