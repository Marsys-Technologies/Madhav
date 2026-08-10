"""
Tests for W2.6 — w26_real_eclipses mechanism.

All tests are fixture-based (no DB, no swisseph calls).

Acceptance criteria verified:
  test_disabled_returns_unit_modifier:
      When enabled=False, modifier==1.0 and data_source=='disabled'.

  test_no_eclipse_data_returns_unit:
      Context with no sky_calendar_rows → modifier==1.0, data_source=='no_data'.

  test_total_solar_eclipse_amplifies:
      Synthetic context with a total solar eclipse within ECLIPSE_ORBS_DEG of a
      natal point → modifier==ECLIPSE_MODIFIERS['total_solar'] == 1.35
      (single contact → noisy-OR of one element == the element itself).

  test_far_eclipse_no_effect:
      Eclipse longitude more than ECLIPSE_ORBS_DEG away from all natal points
      → modifier==1.0.

  test_modifier_in_range:
      For any combination of synthetic eclipse contacts, modifier always in
      [0.0, 2.0].

Additional tests:
  test_total_lunar_eclipse_amplifies:
      total_lunar eclipse near natal point → modifier==1.25.

  test_penumbral_lunar_mildest:
      penumbral_lunar → modifier==1.05.

  test_multiple_contacts_noisy_or:
      Two simultaneous eclipse contacts → combined modifier > either individual
      but <= 2.0 (noisy-OR invariant).

  test_temporal_window_gate:
      Eclipse outside ±ECLIPSE_TEMPORAL_WINDOW_DAYS → modifier==1.0.

  test_eclipse_count_field:
      eclipse_count reflects number of individual target-contact pairs found.

  test_no_natal_points_returns_unit:
      Context with sky_calendar_rows but no resonance targets with longitudes
      → modifier==1.0.

  test_unknown_eclipse_type_fallback:
      eclipse_type='unknown' in detail → modifier==ECLIPSE_MODIFIERS['unknown'].
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import pytest

from services.gochara_v3.mechanisms.w26_real_eclipses import (
    ECLIPSE_MODIFIERS,
    ECLIPSE_ORBS_DEG,
    ECLIPSE_TEMPORAL_WINDOW_DAYS,
    MECHANISM_ID,
    MechanismResult,
    compute,
    _noisy_or,
    _shortest_arc_deg,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

@dataclass
class _FakeTarget:
    """Minimal stand-in for ResonanceTarget."""
    target_ref: str
    target_longitude_deg: Optional[float]
    event_class: str = "career"
    weight: float = 1.0


@dataclass
class _FakeContext:
    """Minimal stand-in for ClassContext — injects sky_calendar_rows."""
    resonance_targets: tuple = ()
    sky_calendar_rows: list = field(default_factory=list)


def _eclipse_row(
    event_type: str = "eclipse_solar",
    eclipse_type: str = "total",
    longitude_deg: float = 15.0,
    event_jd: float = 2460000.0,
) -> dict:
    """Build a synthetic sky_calendar eclipse row (dict form)."""
    return {
        "event_type": event_type,
        "primary_body": "Sun" if "solar" in event_type else "Moon",
        "secondary_body": "Moon" if "solar" in event_type else "Sun",
        "event_jd": event_jd,
        "longitude_deg": longitude_deg,
        "detail": {"eclipse_type": eclipse_type},
    }


def _context_with_eclipse(
    eclipse_lon: float,
    natal_lon: float,
    eclipse_type: str = "total",
    event_type: str = "eclipse_solar",
    eclipse_jd: float = 2460000.0,
    eval_jd: float = 2460000.0,
) -> tuple[_FakeContext, float]:
    """Return (context, eval_jd) with one eclipse row and one natal target."""
    row = _eclipse_row(
        event_type=event_type,
        eclipse_type=eclipse_type,
        longitude_deg=eclipse_lon,
        event_jd=eclipse_jd,
    )
    target = _FakeTarget(target_ref="bhava_7", target_longitude_deg=natal_lon)
    ctx = _FakeContext(
        resonance_targets=(target,),
        sky_calendar_rows=[row],
    )
    return ctx, eval_jd


# ---------------------------------------------------------------------------
# Core acceptance-criteria tests
# ---------------------------------------------------------------------------

class TestDisabledReturnsUnit:
    def test_disabled_returns_unit_modifier(self):
        """AC1: enabled=False → modifier==1.0, data_source=='disabled'."""
        ctx = _FakeContext(
            resonance_targets=(_FakeTarget("x", 10.0),),
            sky_calendar_rows=[_eclipse_row(longitude_deg=10.0)],
        )
        result = compute(ctx, t_jd=2460000.0, enabled=False)
        assert result.modifier == 1.0
        assert result.enabled is False
        assert result.data_source == "disabled"
        assert result.mechanism_id == MECHANISM_ID


class TestNoEclipseDataReturnsUnit:
    def test_no_eclipse_data_returns_unit(self):
        """AC2: no sky_calendar_rows in context → modifier==1.0, data_source=='no_data'."""
        ctx = _FakeContext(
            resonance_targets=(_FakeTarget("x", 15.0),),
            sky_calendar_rows=[],  # empty
        )
        result = compute(ctx, t_jd=2460000.0, enabled=True)
        assert result.modifier == 1.0
        assert result.data_source == "no_data"
        assert result.eclipse_count == 0

    def test_no_sky_calendar_attr_returns_unit(self):
        """Context without sky_calendar_rows attr → modifier==1.0 (honest degrade)."""
        class _BareBoneContext:
            resonance_targets = (_FakeTarget("x", 15.0),)
            # NOTE: no sky_calendar_rows attribute

        result = compute(_BareBoneContext(), t_jd=2460000.0, enabled=True)
        assert result.modifier == 1.0
        assert result.data_source == "no_data"


class TestTotalSolarEclipseAmplifies:
    def test_total_solar_eclipse_amplifies(self):
        """AC3: total solar eclipse within ECLIPSE_ORBS_DEG → modifier==1.35."""
        natal_lon = 45.0
        eclipse_lon = natal_lon + 5.0  # 5° arc, within 10° orb
        ctx, jd = _context_with_eclipse(
            eclipse_lon=eclipse_lon,
            natal_lon=natal_lon,
            eclipse_type="total",
            event_type="eclipse_solar",
            eclipse_jd=2460000.0,
            eval_jd=2460000.0,
        )
        result = compute(ctx, t_jd=jd, enabled=True)

        expected = ECLIPSE_MODIFIERS["total_solar"]  # 1.35
        assert result.modifier == pytest.approx(expected, abs=1e-9)
        assert result.eclipse_count == 1
        assert result.data_source == "sky_calendar_context"
        assert result.contacted_eclipses[0]["eclipse_key"] == "total_solar"

    def test_total_solar_eclipse_exact_overlap(self):
        """Eclipse exactly on natal point → same modifier (arc==0.0 ≤ orb)."""
        lon = 120.0
        ctx, jd = _context_with_eclipse(
            eclipse_lon=lon, natal_lon=lon,
            eclipse_type="total", event_type="eclipse_solar",
        )
        result = compute(ctx, t_jd=jd)
        assert result.modifier == pytest.approx(ECLIPSE_MODIFIERS["total_solar"], abs=1e-9)


class TestFarEclipseNoEffect:
    def test_far_eclipse_no_effect(self):
        """AC4: eclipse more than ECLIPSE_ORBS_DEG away → modifier==1.0."""
        natal_lon = 45.0
        eclipse_lon = natal_lon + ECLIPSE_ORBS_DEG + 1.0  # 11°, outside orb
        ctx, jd = _context_with_eclipse(
            eclipse_lon=eclipse_lon,
            natal_lon=natal_lon,
            eclipse_type="total",
            event_type="eclipse_solar",
        )
        result = compute(ctx, t_jd=jd, enabled=True)
        assert result.modifier == 1.0
        assert result.eclipse_count == 0

    def test_eclipse_at_boundary_is_included(self):
        """Eclipse exactly at ECLIPSE_ORBS_DEG → modifier > 1.0 (boundary inclusive)."""
        natal_lon = 100.0
        eclipse_lon = natal_lon + ECLIPSE_ORBS_DEG  # exactly 10°
        ctx, jd = _context_with_eclipse(
            eclipse_lon=eclipse_lon,
            natal_lon=natal_lon,
            eclipse_type="total",
            event_type="eclipse_solar",
        )
        result = compute(ctx, t_jd=jd, enabled=True)
        assert result.modifier > 1.0


class TestModifierInRange:
    def test_modifier_always_in_range_single(self):
        """AC5: modifier always in [0.0, 2.0] for any single eclipse type."""
        for eclipse_key, mod_val in ECLIPSE_MODIFIERS.items():
            parts = eclipse_key.rsplit("_", 1)
            if len(parts) != 2:
                continue
            eclipse_type, family = parts
            event_type = f"eclipse_{family}"
            ctx, jd = _context_with_eclipse(
                eclipse_lon=50.0,
                natal_lon=50.0,
                eclipse_type=eclipse_type,
                event_type=event_type,
            )
            result = compute(ctx, t_jd=jd, enabled=True)
            assert 0.0 <= result.modifier <= 2.0, (
                f"modifier out of range for eclipse_key={eclipse_key}: {result.modifier}"
            )

    def test_modifier_in_range_multiple_contacts(self):
        """Multiple simultaneous contacts — combined modifier still in [0.0, 2.0]."""
        # Three natal targets, same eclipse longitude → three contacts.
        targets = tuple(
            _FakeTarget(f"bhava_{i}", 30.0)
            for i in range(3)
        )
        row = _eclipse_row(event_type="eclipse_solar", eclipse_type="total", longitude_deg=30.0)
        ctx = _FakeContext(resonance_targets=targets, sky_calendar_rows=[row])
        result = compute(ctx, t_jd=2460000.0, enabled=True)
        assert 0.0 <= result.modifier <= 2.0
        assert result.eclipse_count == 3


# ---------------------------------------------------------------------------
# Additional unit tests
# ---------------------------------------------------------------------------

class TestLunarEclipseTypes:
    def test_total_lunar_eclipse_amplifies(self):
        """total_lunar → modifier==1.25."""
        ctx, jd = _context_with_eclipse(
            eclipse_lon=200.0, natal_lon=200.0,
            eclipse_type="total", event_type="eclipse_lunar",
        )
        result = compute(ctx, t_jd=jd, enabled=True)
        assert result.modifier == pytest.approx(ECLIPSE_MODIFIERS["total_lunar"], abs=1e-9)

    def test_penumbral_lunar_mildest(self):
        """penumbral_lunar → modifier==1.05 (mildest amplifier)."""
        ctx, jd = _context_with_eclipse(
            eclipse_lon=90.0, natal_lon=90.0,
            eclipse_type="penumbral", event_type="eclipse_lunar",
        )
        result = compute(ctx, t_jd=jd, enabled=True)
        assert result.modifier == pytest.approx(ECLIPSE_MODIFIERS["penumbral_lunar"], abs=1e-9)

    def test_partial_solar_amplifies(self):
        """partial_solar → modifier==1.10."""
        ctx, jd = _context_with_eclipse(
            eclipse_lon=270.0, natal_lon=272.0,  # 2° arc, within orb
            eclipse_type="partial", event_type="eclipse_solar",
        )
        result = compute(ctx, t_jd=jd, enabled=True)
        assert result.modifier == pytest.approx(ECLIPSE_MODIFIERS["partial_solar"], abs=1e-9)


class TestNoisyOrBehavior:
    def test_multiple_contacts_noisy_or_gt_single(self):
        """Two contacts → combined modifier > single-contact modifier."""
        # Two natal targets at the same eclipse longitude.
        targets = (
            _FakeTarget("x", 50.0),
            _FakeTarget("y", 52.0),  # both within 10° of eclipse at 50°
        )
        row = _eclipse_row(event_type="eclipse_solar", eclipse_type="total", longitude_deg=50.0)
        ctx = _FakeContext(resonance_targets=targets, sky_calendar_rows=[row])
        result = compute(ctx, t_jd=2460000.0, enabled=True)
        single_mod = ECLIPSE_MODIFIERS["total_solar"]
        assert result.modifier > single_mod
        assert result.modifier <= 2.0

    def test_noisy_or_helper_single(self):
        """_noisy_or([m]) == m for a single modifier."""
        for m in [1.05, 1.10, 1.25, 1.35]:
            assert _noisy_or([m]) == pytest.approx(m, abs=1e-9)

    def test_noisy_or_helper_empty(self):
        """_noisy_or([]) == 1.0."""
        assert _noisy_or([]) == 1.0

    def test_noisy_or_helper_two_modifiers(self):
        """Two modifiers: combined > max(individual), ≤ 2.0."""
        a, b = 1.25, 1.35
        combined = _noisy_or([a, b])
        assert combined > max(a, b)
        assert combined <= 2.0


class TestTemporalWindowGate:
    def test_temporal_window_gate_too_old(self):
        """Eclipse more than ECLIPSE_TEMPORAL_WINDOW_DAYS in the past → no contact."""
        eclipse_jd = 2460000.0
        eval_jd = eclipse_jd + ECLIPSE_TEMPORAL_WINDOW_DAYS + 1.0
        ctx, _ = _context_with_eclipse(
            eclipse_lon=100.0, natal_lon=100.0,
            eclipse_type="total", event_type="eclipse_solar",
            eclipse_jd=eclipse_jd,
            eval_jd=eval_jd,
        )
        result = compute(ctx, t_jd=eval_jd, enabled=True)
        assert result.modifier == 1.0
        assert result.eclipse_count == 0

    def test_temporal_window_gate_too_future(self):
        """Eclipse more than ECLIPSE_TEMPORAL_WINDOW_DAYS in the future → no contact."""
        eclipse_jd = 2460000.0
        eval_jd = eclipse_jd - ECLIPSE_TEMPORAL_WINDOW_DAYS - 1.0
        ctx, _ = _context_with_eclipse(
            eclipse_lon=100.0, natal_lon=100.0,
            eclipse_type="total", event_type="eclipse_solar",
            eclipse_jd=eclipse_jd,
            eval_jd=eval_jd,
        )
        result = compute(ctx, t_jd=eval_jd, enabled=True)
        assert result.modifier == 1.0

    def test_temporal_window_gate_within(self):
        """Eclipse within ECLIPSE_TEMPORAL_WINDOW_DAYS → contact fires."""
        eclipse_jd = 2460000.0
        eval_jd = eclipse_jd + ECLIPSE_TEMPORAL_WINDOW_DAYS - 1.0
        ctx, _ = _context_with_eclipse(
            eclipse_lon=50.0, natal_lon=50.0,
            eclipse_type="total", event_type="eclipse_solar",
            eclipse_jd=eclipse_jd,
            eval_jd=eval_jd,
        )
        result = compute(ctx, t_jd=eval_jd, enabled=True)
        assert result.modifier > 1.0


class TestEclipseCountField:
    def test_eclipse_count_field(self):
        """eclipse_count == number of (eclipse × target) contact pairs found."""
        # One eclipse, two targets both within orb → count == 2.
        targets = (
            _FakeTarget("a", 45.0),
            _FakeTarget("b", 47.0),
        )
        row = _eclipse_row(event_type="eclipse_solar", eclipse_type="total", longitude_deg=45.0)
        ctx = _FakeContext(resonance_targets=targets, sky_calendar_rows=[row])
        result = compute(ctx, t_jd=2460000.0, enabled=True)
        assert result.eclipse_count == 2

    def test_eclipse_count_zero_no_contact(self):
        """No contact → eclipse_count == 0."""
        ctx, jd = _context_with_eclipse(
            eclipse_lon=200.0, natal_lon=10.0,  # 190° apart — no contact
        )
        result = compute(ctx, t_jd=jd, enabled=True)
        assert result.eclipse_count == 0


class TestNoNatalPoints:
    def test_no_natal_points_returns_unit(self):
        """sky_calendar_rows present but no resonance targets → modifier==1.0."""
        row = _eclipse_row(event_type="eclipse_solar", eclipse_type="total", longitude_deg=50.0)
        ctx = _FakeContext(
            resonance_targets=(),  # empty
            sky_calendar_rows=[row],
        )
        result = compute(ctx, t_jd=2460000.0, enabled=True)
        assert result.modifier == 1.0
        assert result.eclipse_count == 0

    def test_targets_without_longitude_returns_unit(self):
        """Targets with target_longitude_deg=None → no natal points → modifier==1.0."""
        row = _eclipse_row(event_type="eclipse_solar", eclipse_type="total", longitude_deg=50.0)
        ctx = _FakeContext(
            resonance_targets=(_FakeTarget("x", None),),  # no longitude
            sky_calendar_rows=[row],
        )
        result = compute(ctx, t_jd=2460000.0, enabled=True)
        assert result.modifier == 1.0


class TestUnknownEclipseType:
    def test_unknown_eclipse_type_fallback(self):
        """eclipse_type='unknown' → modifier == ECLIPSE_MODIFIERS['unknown'] == 1.02."""
        ctx, jd = _context_with_eclipse(
            eclipse_lon=80.0, natal_lon=80.0,
            eclipse_type="unknown", event_type="eclipse_solar",
        )
        result = compute(ctx, t_jd=jd, enabled=True)
        # 'unknown_solar' not in ECLIPSE_MODIFIERS, falls to 'unknown'
        assert result.modifier == pytest.approx(ECLIPSE_MODIFIERS["unknown"], abs=1e-9)

    def test_missing_eclipse_type_falls_to_unknown(self):
        """detail with no eclipse_type key → treated as 'unknown'."""
        row = {
            "event_type": "eclipse_lunar",
            "event_jd": 2460000.0,
            "longitude_deg": 60.0,
            "detail": {},  # no eclipse_type key
        }
        target = _FakeTarget("x", 60.0)
        ctx = _FakeContext(resonance_targets=(target,), sky_calendar_rows=[row])
        result = compute(ctx, t_jd=2460000.0, enabled=True)
        # eclipse_type resolves to 'unknown'; event is 'eclipse_lunar'
        # key tried: 'unknown_lunar' (not in map) → fallback to 'unknown'
        assert result.modifier == pytest.approx(ECLIPSE_MODIFIERS["unknown"], abs=1e-9)


class TestNonEclipseRowsIgnored:
    def test_non_eclipse_rows_ignored(self):
        """Ingress/station rows in sky_calendar_rows are silently ignored."""
        non_eclipse_rows = [
            {"event_type": "ingress", "event_jd": 2460000.0, "longitude_deg": 50.0, "detail": {}},
            {"event_type": "station", "event_jd": 2460000.0, "longitude_deg": 50.0, "detail": {}},
        ]
        target = _FakeTarget("x", 50.0)
        ctx = _FakeContext(resonance_targets=(target,), sky_calendar_rows=non_eclipse_rows)
        result = compute(ctx, t_jd=2460000.0, enabled=True)
        assert result.modifier == 1.0
        assert result.eclipse_count == 0


class TestShortestArcHelper:
    def test_shortest_arc_same_point(self):
        assert _shortest_arc_deg(45.0, 45.0) == pytest.approx(0.0, abs=1e-9)

    def test_shortest_arc_opposite(self):
        assert _shortest_arc_deg(0.0, 180.0) == pytest.approx(180.0, abs=1e-9)

    def test_shortest_arc_wraps(self):
        # 350° and 10° are 20° apart (not 340°)
        assert _shortest_arc_deg(350.0, 10.0) == pytest.approx(20.0, abs=1e-9)


class TestMechanismResultFields:
    def test_result_has_mechanism_id(self):
        """MechanismResult always carries mechanism_id == MECHANISM_ID."""
        ctx = _FakeContext()
        result = compute(ctx, t_jd=2460000.0, enabled=False)
        assert result.mechanism_id == MECHANISM_ID

    def test_result_data_source_sky_calendar_when_data_present_no_contact(self):
        """When sky_calendar_rows present but no contact: data_source=='sky_calendar_context'."""
        row = _eclipse_row(event_type="eclipse_solar", eclipse_type="total", longitude_deg=1.0)
        target = _FakeTarget("x", 180.0)  # far away
        ctx = _FakeContext(resonance_targets=(target,), sky_calendar_rows=[row])
        result = compute(ctx, t_jd=2460000.0, enabled=True)
        assert result.data_source == "sky_calendar_context"
