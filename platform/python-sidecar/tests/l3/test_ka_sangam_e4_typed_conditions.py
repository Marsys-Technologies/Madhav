"""
Tests for ka_sangam E4 — typed natal/clock conditioning and annual-Tājika gate.

Scope (Phase 4 narrowed by working handoff, recorded as a ruling):
  - per-window typed_conditions inside constituent_factors:
      * natal_dignity_strong (D1 dignity in {Exalted, Moolatrikona, Own})
      * retrograde_at_peak   (transit speed < 0 at exact contact)
      * day_birth            (birth instant between local sunrise/sunset)
      * kendra_from_lagna    (transit sign in 1/4/7/10 from natal lagna)
  - availability['tajika'] = 'computed' when a covering varṣa exists,
    'unavailable' otherwise.

Engine-only; no DB, no writer, no orchestrator.
"""
from __future__ import annotations

import os
import sys
from datetime import date
from unittest.mock import MagicMock

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_sangam.engine import (
    EnrichmentContext,
    mode_a_search,
    mode_c_subsystem_period,
    mode_d_av_bindhu,
    _date_to_jd,
)

_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
_TAURUS_LON = 35.0


class _FakeTransitEvent:
    """Minimal stand-in for pipeline.transit_search.TransitEvent."""

    def __init__(self, exact_longitude_deg, event_jd, orb_at_event_deg=0.0,
                 applying_separating='applying', aspect_deg=0, speed_at_event_dps=1.0):
        self.exact_longitude_deg = exact_longitude_deg
        self.event_jd = event_jd
        self.orb_at_event_deg = orb_at_event_deg
        self.applying_separating = applying_separating
        self.speed_at_event_dps = speed_at_event_dps
        self.extra = {'aspect_deg': aspect_deg}
        self.sign = 'Taurus'
        self.nakshatra = 'Rohini'
        self.event_datetime_ist = '2024-06-01T00:00:00+05:30'


class _FakeIngressEvent:
    def __init__(self, event_jd):
        self.event_jd = event_jd


class _FakeGocharaService:
    """find_ingresses returns one ingress per requested sign at a fixed JD."""

    def __init__(self, ingress_jd):
        self._ingress_jd = ingress_jd

    def find_ingresses(self, planet, target_sign, start_jd, end_jd):
        return [_FakeIngressEvent(self._ingress_jd)]


class _FakeDashaService:
    """query() returns fixed eligible windows regardless of args."""

    def __init__(self, windows):
        self._windows = windows

    def query(self, **kwargs):
        return MagicMock(windows=self._windows)


class _FakeEligibleWindow:
    def __init__(self, start_date, end_date, eligibility_score):
        self.start_date = start_date
        self.end_date = end_date
        self.eligibility_score = eligibility_score


def _predicate(dignity_score=0.9, eligibility_score=0.8, domain_lord=None):
    p = {
        'signal_id': 'dddddddd-0000-0000-0000-000000000000',
        'signature_class': 'DIGNITY',
        'graha_name': 'Jupiter',
        'dignity_score': dignity_score,
        'dasha_eligibility_rule_jsonb': {
            'eligibility_score': eligibility_score,
            'constituent_lords': ['Jupiter'],
        },
        'transit_trigger_jsonb': {
            'target_longitude_deg': _TAURUS_LON,
            'aspect_degrees': [0],
            'orb_deg': 5.0,
        },
        'strength_affliction_hook_jsonb': {},
        'derivation_ledger_jsonb': {},
    }
    if domain_lord:
        p['domain_lord'] = domain_lord
    return p


def _patched_mode_a(monkeypatch, predicate, ctx=None, dasha_service=None, event_speed=1.0):
    event = _FakeTransitEvent(_TAURUS_LON, _date_to_jd(date(2024, 6, 1)),
                              speed_at_event_dps=event_speed)
    monkeypatch.setattr(
        'pipeline.transit_search.find_aspect_events', lambda **kwargs: [event]
    )
    s, e = _date_to_jd(date(2024, 1, 1)), _date_to_jd(date(2025, 1, 1))
    windows = mode_a_search(
        janma_nakshatra_idx=3,
        predicate=predicate,
        horizon_start_jd=s, horizon_end_jd=e,
        dasha_kala_service=dasha_service, gochara_service=None,
        muhurta_service=None,
        chart_id=_CHART_ID,
        enrichment_context=ctx or EnrichmentContext.empty(),
    )
    assert len(windows) == 1
    return windows[0]


class TestE4TypedConditionHelpers:
    """Unit-level contract of the four typed-condition helper functions."""

    def test_natal_dignity_strong_for_exalted_moola_own(self):
        from services.ka_sangam.engine import _e4_natal_dignity_strong_flag
        assert _e4_natal_dignity_strong_flag('Exalted') is True
        assert _e4_natal_dignity_strong_flag('Moolatrikona') is True
        assert _e4_natal_dignity_strong_flag('Own') is True

    def test_natal_dignity_strong_false_for_debilitated_neutral(self):
        from services.ka_sangam.engine import _e4_natal_dignity_strong_flag
        assert _e4_natal_dignity_strong_flag('Debilitated') is False
        assert _e4_natal_dignity_strong_flag('neutral') is False
        assert _e4_natal_dignity_strong_flag(None) is False

    def test_retrograde_flag_true_when_speed_negative(self):
        from services.ka_sangam.engine import _e4_retrograde_flag
        assert _e4_retrograde_flag(-0.5) is True
        assert _e4_retrograde_flag(0.0) is False
        assert _e4_retrograde_flag(0.5) is False
        assert _e4_retrograde_flag(None) is False

    def test_day_birth_flag(self):
        from services.ka_sangam.engine import _e4_day_birth_flag
        assert _e4_day_birth_flag(True) is True
        assert _e4_day_birth_flag(False) is False
        assert _e4_day_birth_flag(None) is False

    def test_kendra_flag_for_lagna_relative_signs(self):
        from services.ka_sangam.engine import _e4_kendra_flag
        # Lagna = Aries (1). Kendra signs are 1, 4, 7, 10.
        assert _e4_kendra_flag(1, 1) is True   # Aries in Aries
        assert _e4_kendra_flag(1, 4) is True   # Cancer
        assert _e4_kendra_flag(1, 7) is True   # Libra
        assert _e4_kendra_flag(1, 10) is True  # Capricorn
        assert _e4_kendra_flag(1, 2) is False  # Taurus
        assert _e4_kendra_flag(4, 7) is True   # Libra from Cancer lagna
        assert _e4_kendra_flag(None, 1) is False
        assert _e4_kendra_flag(1, None) is False


class TestE4TypedConditionsStamped:
    """typed_conditions stamped into constituent_factors for modes A/C/D."""

    def test_mode_a_typed_conditions_stamped(self, monkeypatch):
        ctx = EnrichmentContext(
            d1_dignity_by_graha={'Jupiter': 'Exalted'},
            lagna_sign='Taurus',
            is_day_birth=True,
        )
        w = _patched_mode_a(monkeypatch, _predicate(), ctx=ctx, event_speed=-1.2)
        tc = w['constituent_factors']['typed_conditions']
        assert tc['natal_dignity_strong'] is True
        assert tc['retrograde_at_peak'] is True
        assert tc['day_birth'] is True
        assert tc['kendra_from_lagna'] is True

    def test_mode_a_typed_conditions_all_false(self, monkeypatch):
        ctx = EnrichmentContext(
            d1_dignity_by_graha={'Jupiter': 'Debilitated'},
            lagna_sign='Cancer',
            is_day_birth=False,
        )
        w = _patched_mode_a(monkeypatch, _predicate(), ctx=ctx, event_speed=1.0)
        tc = w['constituent_factors']['typed_conditions']
        assert tc['natal_dignity_strong'] is False
        assert tc['retrograde_at_peak'] is False
        assert tc['day_birth'] is False
        assert tc['kendra_from_lagna'] is False

    def test_mode_c_typed_conditions_stamped(self):
        s, e = _date_to_jd(date(2024, 1, 1)), _date_to_jd(date(2025, 1, 1))
        svc = _FakeGocharaService(_date_to_jd(date(2024, 3, 1)))
        ctx = EnrichmentContext(
            d1_dignity_by_graha={'Saturn': 'Own'},
            lagna_sign='Aquarius',
            is_day_birth=True,
        )
        windows = mode_c_subsystem_period(
            predicate=_predicate(dignity_score=0.0),
            horizon_start_jd=s, horizon_end_jd=e,
            gochara_service=svc, moon_sign='Aquarius',
            enrichment_context=ctx,
        )
        assert windows
        w = windows[0]
        tc = w['constituent_factors']['typed_conditions']
        assert 'natal_dignity_strong' in tc
        assert 'day_birth' in tc
        assert 'kendra_from_lagna' in tc

    def test_mode_d_typed_conditions_stamped(self):
        s, e = _date_to_jd(date(2024, 1, 1)), _date_to_jd(date(2025, 1, 1))
        svc = _FakeGocharaService(_date_to_jd(date(2024, 3, 1)))
        ctx = EnrichmentContext(
            ashtakavarga_bindu={'SARVA': {2: 32}},
            d1_dignity_by_graha={'Jupiter': 'Moolatrikona'},
            lagna_sign='Taurus',
            is_day_birth=False,
        )
        windows = mode_d_av_bindhu(
            predicate=_predicate(dignity_score=1.0),
            horizon_start_jd=s, horizon_end_jd=e,
            gochara_service=svc, enrichment_context=ctx,
        )
        assert windows
        w = windows[0]
        tc = w['constituent_factors']['typed_conditions']
        assert tc['natal_dignity_strong'] is True
        assert tc['day_birth'] is False
        assert tc['kendra_from_lagna'] is True  # Taurus in Taurus (1st)


class TestE4TajikaAvailabilityGate:
    """availability['tajika'] reflects whether a covering varṣa was evaluated."""

    def test_tajika_computed_when_varsha_covers_window(self, monkeypatch):
        ctx = EnrichmentContext(tajika_year_lords=[{
            'varsha_year': 1,
            'varshesha': 'Jupiter',
            'muntha': 'Mars',
            'varsha_start': date(2024, 1, 1),
            'varsha_end': date(2024, 12, 31),
        }])
        w = _patched_mode_a(monkeypatch, _predicate(domain_lord='Jupiter'), ctx=ctx)
        assert w['availability']['tajika'] == 'computed'
        assert w['constituent_factors']['typed_conditions']['tajika_covering'] is True

    def test_tajika_unavailable_when_no_covering_varsha(self, monkeypatch):
        ctx = EnrichmentContext(tajika_year_lords=[])
        w = _patched_mode_a(monkeypatch, _predicate(), ctx=ctx)
        assert w['availability']['tajika'] == 'unavailable'
        assert w['constituent_factors']['typed_conditions']['tajika_covering'] is False


