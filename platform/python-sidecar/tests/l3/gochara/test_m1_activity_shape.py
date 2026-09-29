"""M-1 (L3 §4.5) exit-gate fixture — `activity_shape` projection flag.

Reproduces WP4's pinned numbers at +4 d past exact contact, transit speed
0.017454°/d, promise 0.8, weight 1.0:

  legacy_box                 → λ = 0.80000  (full event-time contribution
                               across the whole ±5-day box)
  linear_no_box × 5.0°       → λ = 0.7888   (1 − 0.069816/5.0 = 0.9860368)
  linear_no_box × 1.0°       → λ = 0.74415  (1 − 0.069816/1.0 = 0.930184)

Synthetic chart data only (WP4-SYNTH-shaped; no real chart, no person).
"""
from __future__ import annotations

import pytest

from services.gochara_grammar.models import ConfigurationSentence
from services.gochara_v3 import engine


CHART_ID = "00000000-0000-4000-8000-0000000004a5"  # synthetic, non-person
TARGET_DEG = 280.0
T_EXACT = 2460000.0
SPEED = 0.017454  # °/d (WP4's pinned slow-body speed)
PROMISE = 0.8
T_OFF = T_EXACT + 4.0


def _sentence() -> ConfigurationSentence:
    return ConfigurationSentence(
        primitive="degree_contact",
        chart_id=CHART_ID,
        event_class="synthetic_m1",
        target_type="synthetic",
        target_ref="syn:target",
        transit_planet="Saturn",
        secondary_planet=None,
        event_jd=T_EXACT,
        event_datetime_ist=None,
        uncited_extension=True,
        temporal_shape="point",
        detail={"target_longitude_deg": TARGET_DEG, "orb_strength": 1.0},
    )


def _fake_planet_pos(_swe, planet: str, jd: float) -> tuple[float, float]:
    assert planet == "Saturn"
    return ((TARGET_DEG + SPEED * (jd - T_EXACT)) % 360.0, SPEED)


@pytest.fixture
def patched_engine(monkeypatch):
    monkeypatch.setattr(engine, "_get_planet_pos", _fake_planet_pos)
    return engine


def test_legacy_box_at_plus_4d(patched_engine):
    """Inside the ±5-day box the event-time contribution is undecayed."""
    s = _sentence()
    activity, detail, _ = patched_engine._compute_activity_v3(
        [s], {"syn:target": 1.0},
    )
    lam = PROMISE * activity
    assert activity == 1.0
    assert abs(lam - 0.8) < 1e-9  # WP4: box 0.80000
    # flag-off provenance keys absent (byte-identical legacy detail)
    assert "activity_shape" not in detail
    assert "orb_max_deg" not in detail
    assert "orb_source" not in detail


def test_linear_no_box_orb_5deg(patched_engine):
    s = _sentence()
    orbs = patched_engine._instantaneous_orbs_at(None, [s], T_OFF)
    assert abs(orbs[0] - 4.0 * SPEED) < 1e-9  # 0.069816°
    activity, detail, _ = patched_engine._compute_activity_v3(
        [s], {"syn:target": 1.0},
        activity_shape="linear_no_box",
        orb_max_deg=5.0,
        instantaneous_orbs=orbs,
    )
    assert abs(activity - (1.0 - 4.0 * SPEED / 5.0)) < 1e-9
    lam = PROMISE * activity
    assert round(lam, 4) == 0.7888  # WP4: no-box×5.0° 0.7888
    assert detail["activity_shape"] == "linear_no_box"
    assert detail["orb_max_deg"] == 5.0
    assert detail["orb_source"] == "wp1_contracts_s7_orb_source"


def test_linear_no_box_orb_1deg(patched_engine):
    s = _sentence()
    orbs = patched_engine._instantaneous_orbs_at(None, [s], T_OFF)
    activity, _, _ = patched_engine._compute_activity_v3(
        [s], {"syn:target": 1.0},
        activity_shape="linear_no_box",
        orb_max_deg=1.0,
        instantaneous_orbs=orbs,
    )
    lam = PROMISE * activity
    assert abs(lam - 0.74415) < 1e-5  # WP4: no-box×1.0° 0.74415


def test_linear_no_box_varies_with_instant(patched_engine):
    """No time box: the contribution decays as |t − t_exact| grows."""
    s = _sentence()
    orbs_in = patched_engine._instantaneous_orbs_at(None, [s], T_EXACT + 1.0)
    orbs_out = patched_engine._instantaneous_orbs_at(None, [s], T_EXACT + 4.0)
    a_in, _, _ = patched_engine._compute_activity_v3(
        [s], {"syn:target": 1.0},
        activity_shape="linear_no_box", orb_max_deg=5.0,
        instantaneous_orbs=orbs_in,
    )
    a_out, _, _ = patched_engine._compute_activity_v3(
        [s], {"syn:target": 1.0},
        activity_shape="linear_no_box", orb_max_deg=5.0,
        instantaneous_orbs=orbs_out,
    )
    assert a_in > a_out > 0.0


def test_flag_off_byte_identical(patched_engine):
    """Default call (no projection args) matches an explicit legacy_box call."""
    s = _sentence()
    a_default, d_default, tb_default = patched_engine._compute_activity_v3(
        [s], {"syn:target": 1.0},
    )
    a_legacy, d_legacy, tb_legacy = patched_engine._compute_activity_v3(
        [s], {"syn:target": 1.0}, activity_shape="legacy_box",
    )
    assert a_default == a_legacy
    assert d_default == d_legacy
    assert tb_default == tb_legacy


def test_unorbed_sentence_keeps_neutral_fallback(patched_engine):
    """No resolvable body/target longitude -> honest 0.5, no fabrication."""
    s = ConfigurationSentence(
        primitive="sign_ingress",
        chart_id=CHART_ID,
        event_class="synthetic_m1",
        target_type="synthetic",
        target_ref="syn:target",
        transit_planet="Saturn",
        secondary_planet=None,
        event_jd=T_EXACT,
        event_datetime_ist=None,
        uncited_extension=True,
        temporal_shape="interval",
        detail={},
    )
    orbs = patched_engine._instantaneous_orbs_at(None, [s], T_OFF)
    assert orbs == {}  # nothing to resolve against
    activity, _, _ = patched_engine._compute_activity_v3(
        [s], {"syn:target": 1.0},
        activity_shape="linear_no_box", orb_max_deg=5.0,
        instantaneous_orbs=orbs,
    )
    assert activity == 0.5


def test_invalid_shape_rejected():
    with pytest.raises(ValueError, match="activity_shape"):
        engine._evaluate_single_from_context(
            None, None, 0.0, [], activity_shape="not_a_shape",
        )
