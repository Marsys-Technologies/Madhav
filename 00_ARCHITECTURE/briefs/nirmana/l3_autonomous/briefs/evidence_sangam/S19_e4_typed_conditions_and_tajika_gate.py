"""E4 typed natal/clock conditioning + annual Tājika gate detector.
Proposition: every ka_sangam mode stamps per-window typed_conditions
(natal_dignity_strong, retrograde_at_peak, day_birth, kendra_from_lagna);
availability['tajika'] and typed_conditions['tajika_covering'] report
'computed'/True only when a covering varṣa exists, 'unavailable'/False
otherwise; typed_conditions are lineage data and never veto the score."""
from _common import *
from datetime import date
from unittest.mock import MagicMock

from services.ka_sangam.engine import (
    EnrichmentContext,
    _e4_natal_dignity_strong_flag,
    _e4_retrograde_flag,
    _e4_day_birth_flag,
    _e4_kendra_flag,
    mode_a_search,
    mode_b_sweep,
    mode_c_subsystem_period,
    mode_d_av_bindhu,
    _date_to_jd,
    convergence_score,
)
from pipeline import transit_search

head("S19 — E4 typed natal/clock conditioning + annual Tājika gate")

_TAURUS_LON = 35.0
_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'


class _FakeTransitEvent:
    def __init__(self, exact_longitude_deg, event_jd, speed_at_event_dps=1.0):
        self.exact_longitude_deg = exact_longitude_deg
        self.event_jd = event_jd
        self.orb_at_event_deg = 0.0
        self.applying_separating = 'applying'
        self.speed_at_event_dps = speed_at_event_dps
        self.extra = {'aspect_deg': 0}
        self.sign = 'Taurus'
        self.nakshatra = 'Rohini'
        self.event_datetime_ist = '2024-06-01T00:00:00+05:30'


class _FakeIngressEvent:
    def __init__(self, event_jd):
        self.event_jd = event_jd


class _FakeGocharaService:
    def __init__(self, ingress_jd):
        self._ingress_jd = ingress_jd

    def find_ingresses(self, planet, target_sign, start_jd, end_jd):
        return [_FakeIngressEvent(self._ingress_jd)]


def _predicate(dignity_score=0.9, domain_lord=None):
    p = {
        'signal_id': 'dddddddd-0000-0000-0000-000000000000',
        'signature_class': 'DIGNITY',
        'graha_name': 'Jupiter',
        'dignity_score': dignity_score,
        'dasha_eligibility_rule_jsonb': {
            'eligibility_score': 0.8,
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


def _patch_mode_a(ctx, event_speed=1.0, domain_lord=None):
    event = _FakeTransitEvent(_TAURUS_LON, _date_to_jd(date(2024, 6, 1)),
                              speed_at_event_dps=event_speed)
    original = transit_search.find_aspect_events
    transit_search.find_aspect_events = lambda *args, **kwargs: [event]
    try:
        s, e = _date_to_jd(date(2024, 1, 1)), _date_to_jd(date(2025, 1, 1))
        windows = mode_a_search(
            janma_nakshatra_idx=3,
            predicate=_predicate(domain_lord=domain_lord),
            horizon_start_jd=s, horizon_end_jd=e,
            dasha_kala_service=None, gochara_service=None,
            muhurta_service=None,
            chart_id=_CHART_ID,
            enrichment_context=ctx,
        )
        return windows[0] if windows else None
    finally:
        transit_search.find_aspect_events = original


def _patch_mode_b(ctx, event_speed=1.0, domain_lord=None):
    event = _FakeTransitEvent(_TAURUS_LON, _date_to_jd(date(2024, 6, 1)),
                              speed_at_event_dps=event_speed)
    original = transit_search.find_aspect_events
    transit_search.find_aspect_events = lambda *args, **kwargs: [event]
    try:
        s, e = _date_to_jd(date(2024, 1, 1)), _date_to_jd(date(2025, 1, 1))
        windows = mode_b_sweep(
            signal_id='sig-s19-b',
            predicate=_predicate(domain_lord=domain_lord),
            horizon_start_jd=s, horizon_end_jd=e,
            gochara_service=None, muhurta_service=None,
            janma_nakshatra_idx=3,
            enrichment_context=ctx,
        )
        return windows[0] if windows else None
    finally:
        transit_search.find_aspect_events = original


def _mode_c(ctx):
    s, e = _date_to_jd(date(2024, 1, 1)), _date_to_jd(date(2025, 1, 1))
    svc = _FakeGocharaService(_date_to_jd(date(2024, 3, 1)))
    windows = mode_c_subsystem_period(
        predicate=_predicate(dignity_score=0.0),
        horizon_start_jd=s, horizon_end_jd=e,
        gochara_service=svc, moon_sign='Aquarius',
        enrichment_context=ctx,
    )
    return windows[0] if windows else None


def _mode_d(ctx):
    s, e = _date_to_jd(date(2024, 1, 1)), _date_to_jd(date(2025, 1, 1))
    svc = _FakeGocharaService(_date_to_jd(date(2024, 3, 1)))
    windows = mode_d_av_bindhu(
        predicate=_predicate(dignity_score=1.0),
        horizon_start_jd=s, horizon_end_jd=e,
        gochara_service=svc, enrichment_context=ctx,
    )
    return windows[0] if windows else None


ctx_all_true = EnrichmentContext(
    ashtakavarga_bindu={'SARVA': {2: 32}},
    d1_dignity_by_graha={'Jupiter': 'Exalted'},
    lagna_sign='Taurus',
    is_day_birth=True,
    tajika_year_lords=[{
        'varsha_year': 1,
        'varshesha': 'Jupiter',
        'muntha': 'Mars',
        'varsha_start': date(2024, 1, 1),
        'varsha_end': date(2024, 12, 31),
    }],
)
ctx_all_false = EnrichmentContext(
    d1_dignity_by_graha={'Jupiter': 'Debilitated'},
    lagna_sign='Cancer',
    is_day_birth=False,
    tajika_year_lords=[],
)

w_a_true = _patch_mode_a(ctx_all_true, event_speed=-1.2, domain_lord='Jupiter')
w_a_false = _patch_mode_a(ctx_all_false, event_speed=1.0)
w_b_true = _patch_mode_b(ctx_all_true, event_speed=-1.2, domain_lord='Jupiter')
w_c = _mode_c(ctx_all_true)
w_d = _mode_d(ctx_all_true)

# Veto-falsifier: identical inputs except typed_conditions should not change score.
ctx_neutral = EnrichmentContext(
    d1_dignity_by_graha={'Jupiter': 'neutral'},
    lagna_sign=None,
    is_day_birth=None,
)
w_a_neutral = _patch_mode_a(ctx_neutral, event_speed=1.0)
w_a_strong = _patch_mode_a(
    EnrichmentContext(
        d1_dignity_by_graha={'Jupiter': 'Own'},
        lagna_sign='Taurus',
        is_day_birth=True,
    ),
    event_speed=-1.0,
)

if NEG:
    # Inverted expectations: the detector must fail on correct code.
    prop("Exalted counts as strong dignity", not _e4_natal_dignity_strong_flag('Exalted'))
    prop("Moolatrikona counts as strong dignity", not _e4_natal_dignity_strong_flag('Moolatrikona'))
    prop("Own counts as strong dignity", not _e4_natal_dignity_strong_flag('Own'))
    prop("Debilitated does NOT count as strong dignity", _e4_natal_dignity_strong_flag('Debilitated'))
    prop("negative speed is retrograde", not _e4_retrograde_flag(-0.5))
    prop("positive speed is direct", _e4_retrograde_flag(0.5))
    prop("day birth flag True", not _e4_day_birth_flag(True))
    prop("day birth flag False", _e4_day_birth_flag(False))
    prop("kendra from Aries lagna at Aries", not _e4_kendra_flag(1, 1))
    prop("non-kendra from Aries lagna at Taurus", _e4_kendra_flag(1, 2))
    prop("mode A stamps typed_conditions", w_a_true is None or 'typed_conditions' not in w_a_true.get('constituent_factors', {}))
    prop("mode A tajika computed when covering varsha exists", w_a_true is None or w_a_true.get('availability', {}).get('tajika') != 'computed')
    prop("mode A tajika unavailable when no covering varsha", w_a_false is None or w_a_false.get('availability', {}).get('tajika') != 'unavailable')
    prop("mode B stamps typed_conditions", w_b_true is None or 'typed_conditions' not in w_b_true.get('constituent_factors', {}))
    prop("mode C stamps typed_conditions", w_c is None or 'typed_conditions' not in w_c.get('constituent_factors', {}))
    prop("mode D stamps typed_conditions", w_d is None or 'typed_conditions' not in w_d.get('constituent_factors', {}))
    prop("typed_conditions do not veto score", w_a_neutral is None or w_a_strong is None or w_a_neutral.get('convergence_score') != w_a_strong.get('convergence_score'))
    prop("mode A tajika_covering matches availability", w_a_true is None or w_a_true.get('constituent_factors', {}).get('typed_conditions', {}).get('tajika_covering') is False)
    prop("mode D kendra_from_lagna correct", w_d is None or w_d.get('constituent_factors', {}).get('typed_conditions', {}).get('kendra_from_lagna') is False)
else:
    prop("Exalted counts as strong dignity", _e4_natal_dignity_strong_flag('Exalted'))
    prop("Moolatrikona counts as strong dignity", _e4_natal_dignity_strong_flag('Moolatrikona'))
    prop("Own counts as strong dignity", _e4_natal_dignity_strong_flag('Own'))
    prop("Debilitated does NOT count as strong dignity", not _e4_natal_dignity_strong_flag('Debilitated'))
    prop("negative speed is retrograde", _e4_retrograde_flag(-0.5))
    prop("positive speed is direct", not _e4_retrograde_flag(0.5))
    prop("day birth flag True", _e4_day_birth_flag(True))
    prop("day birth flag False", not _e4_day_birth_flag(False))
    prop("kendra from Aries lagna at Aries", _e4_kendra_flag(1, 1))
    prop("non-kendra from Aries lagna at Taurus", not _e4_kendra_flag(1, 2))
    prop("mode A stamps typed_conditions", w_a_true is not None and 'typed_conditions' in w_a_true.get('constituent_factors', {}))
    prop("mode A tajika computed when covering varsha exists", w_a_true is not None and w_a_true.get('availability', {}).get('tajika') == 'computed')
    prop("mode A tajika unavailable when no covering varsha", w_a_false is not None and w_a_false.get('availability', {}).get('tajika') == 'unavailable')
    prop("mode B stamps typed_conditions", w_b_true is not None and 'typed_conditions' in w_b_true.get('constituent_factors', {}))
    prop("mode C stamps typed_conditions", w_c is not None and 'typed_conditions' in w_c.get('constituent_factors', {}))
    prop("mode D stamps typed_conditions", w_d is not None and 'typed_conditions' in w_d.get('constituent_factors', {}))
    prop("typed_conditions do not veto score", w_a_neutral is not None and w_a_strong is not None and w_a_neutral.get('convergence_score') == w_a_strong.get('convergence_score'))
    prop("mode A tajika_covering matches availability", w_a_true is not None and w_a_true.get('constituent_factors', {}).get('typed_conditions', {}).get('tajika_covering') is True)
    prop("mode D kendra_from_lagna correct", w_d is not None and w_d.get('constituent_factors', {}).get('typed_conditions', {}).get('kendra_from_lagna') is True)

done("POST-FIX BEHAVIOUR")
