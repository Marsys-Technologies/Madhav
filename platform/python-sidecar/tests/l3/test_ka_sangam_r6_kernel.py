"""
Tests for ka_sangam R-6 score-kernel separation (RR-05, decision M-7;
ASTRA amendments RRV-03/RRV-08 dispositioned 2026-09-23).

Covers the SPEC R-6 acceptance fixtures:
  - dignity-0 intensely active → activity > 0 AND valence < 0, while the
    legacy convergence_score is still 0.0 (S11 defect fixed on the NEW
    kernel, preserved as legacy_i16 reading for backward compat)
  - eligibility failure → availability['dasha'] == 'unavailable', zero
    manufactured supporting contribution (RRV-08)
  - equal-activity opposite-valence windows BOTH survive a page cut
    (RRV-03: valence carried as data, never pooled into the ordering key)
  - deterministic ordering tiebreak (activity DESC, contact instant ASC)
  - C11 vedha unavailable recorded as unavailable — never folded into a
    silent neutral 1.0 on the new path
  - sign-level routes (mode C / mode D) carry the kernel fields with
    severity / SAV fraction as activity

Anti-drift: engine-only; no DB, no writer, no orchestrator.
"""
from __future__ import annotations

import os
import sys
from datetime import date

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_sangam.engine import (
    EnrichmentContext,
    KERNEL_VERSION_SEPARATED,
    convergence_score,
    mode_a_search,
    mode_c_subsystem_period,
    mode_d_av_bindhu,
    ordering_key,
    separate_kernel,
    separate_kernel_sign_level,
    _date_to_jd,
)

_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
_TAURUS_LON = 35.0  # sign idx = int(35//30)+1 = 2 (Taurus)


class _FakeTransitEvent:
    """Minimal stand-in for pipeline.transit_search.TransitEvent — only the
    attributes mode_a_search actually reads (same shape as the fixture in
    test_ka_sangam.py's TestFSangam5VedhaWired)."""

    def __init__(self, exact_longitude_deg, event_jd, orb_at_event_deg=0.0,
                 applying_separating='applying', aspect_deg=0):
        self.exact_longitude_deg = exact_longitude_deg
        self.event_jd = event_jd
        self.orb_at_event_deg = orb_at_event_deg
        self.applying_separating = applying_separating
        self.extra = {'aspect_deg': aspect_deg}
        self.sign = 'Taurus'
        self.nakshatra = 'Rohini'
        self.event_datetime_ist = '2024-06-01T00:00:00+05:30'


class _FakeEligibleWindow:
    def __init__(self, start_date, end_date, eligibility_score):
        self.start_date = start_date
        self.end_date = end_date
        self.eligibility_score = eligibility_score


class _FakeDashaResult:
    def __init__(self, windows):
        self.windows = windows


class _FakeDashaService:
    """query() returns fixed eligible windows regardless of args."""

    def __init__(self, windows):
        self._windows = windows

    def query(self, **kwargs):
        return _FakeDashaResult(self._windows)


class _FakeIngressEvent:
    def __init__(self, event_jd):
        self.event_jd = event_jd


class _FakeGocharaService:
    """find_ingresses returns one ingress per requested sign at a fixed JD."""

    def __init__(self, ingress_jd):
        self._ingress_jd = ingress_jd

    def find_ingresses(self, planet, target_sign, start_jd, end_jd):
        return [_FakeIngressEvent(self._ingress_jd)]


def _horizon():
    return _date_to_jd(date(2024, 1, 1)), _date_to_jd(date(2025, 1, 1))


def _predicate(dignity_score=0.9, eligibility_score=0.8):
    return {
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


def _patched_mode_a(monkeypatch, predicate, ctx=None, dasha_service=None):
    event = _FakeTransitEvent(_TAURUS_LON, _date_to_jd(date(2024, 6, 1)))
    monkeypatch.setattr(
        'pipeline.transit_search.find_aspect_events', lambda **kwargs: [event]
    )
    s, e = _horizon()
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


class TestSeparateKernelUnit:
    """Unit-level contract of the two kernel constructors."""

    def test_dignity_maps_to_valence_signed(self):
        k = separate_kernel(0.0, [1.0], {})
        assert k['valence'] == -1.0
        k = separate_kernel(1.0, [1.0], {})
        assert k['valence'] == 1.0
        k = separate_kernel(0.5, [1.0], {})
        assert k['valence'] == 0.0

    def test_sign_level_kernel_clamps_intensity(self):
        k = separate_kernel_sign_level(0.7, 1.4)
        assert k['activity'] == 1.0
        k = separate_kernel_sign_level(0.7, -0.2)
        assert k['activity'] == 0.0

    def test_kernel_carries_applicability_and_availability(self):
        k = separate_kernel(
            0.5, [1.0], {},
            availability={'dasha': 'unavailable'},
            applicability={'orb_presence': True},
        )
        assert k['availability'] == {'dasha': 'unavailable'}
        assert k['applicability'] == {'orb_presence': True}


class TestR6AdverseActivityVisible:
    """SPEC R-6 headline fixture: dignity-0 intensely active configuration."""

    def test_dignity_zero_adverse_visible_on_new_kernel(self, monkeypatch):
        w = _patched_mode_a(monkeypatch, _predicate(dignity_score=0.0))
        # Legacy composite UNCHANGED (S11 behavior preserved as legacy_i16):
        assert w['convergence_score'] == 0.0
        # New kernel: activity survives (orb exact + evaluated support),
        # valence is adverse.
        assert w['activity'] > 0.0, "adverse activity must not be erased"
        assert w['valence'] == -1.0
        assert w['kernel_version'] == KERNEL_VERSION_SEPARATED
        assert w['comparability_class'] == 'ka_sangam/DIGNITY'

    def test_legacy_score_is_dignity_times_kernel_path(self, monkeypatch):
        """Cross-check of coexistence: the legacy composite is the SAME form
        with dignity left inside the necessary product and the (static here)
        daśā term inside support — i.e. legacy == dignity × convergence of
        the kernel necessary + the legacy supporting dict."""
        w = _patched_mode_a(monkeypatch, _predicate(dignity_score=0.5))
        cf = w['constituent_factors']
        sup_legacy = {
            'constituent_lord_transit': 0.8,  # static prior, legacy path only
            # R-4: benefic_dristi and transit_to_transit are withdrawn from the
            # scored product, so the legacy reconstruction must not include them.
            'tara_bala': cf['c_tara_bala'],
            'eclipse_proximity': cf['c8_eclipse_proximity'],
            'nakshatra_subsystem': cf['c_nakshatra_subsystem'],
            'station_retrograde': cf['c10_station_retrograde'],
        }
        legacy_reconstructed = convergence_score([0.5, w['orb_strength']], sup_legacy)
        assert w['convergence_score'] == pytest.approx(legacy_reconstructed, abs=1e-4)
        assert w['valence'] == 0.0


class TestR6DashaAvailability:
    """RRV-08: static daśā prior is an availability state, never support."""

    def test_no_service_dasha_unavailable_no_manufactured_support(self, monkeypatch):
        w = _patched_mode_a(monkeypatch, _predicate(), dasha_service=None)
        assert w['availability']['dasha'] == 'unavailable'
        assert w['applicability']['constituent_lord_transit'] is False
        # The static 0.5 prior must not appear as support anywhere on the new
        # path: reconstruct what activity WOULD be with the static term and
        # show the served activity is strictly below it (term omitted).
        orb_s = w['orb_strength']
        nec = [orb_s]  # vedha unavailable in this fixture
        cf = w['constituent_factors']
        sup_without = {
            # R-4: withdrawn terms are not part of the kernel supporting product.
            'tara_bala': cf['c_tara_bala'],
            'eclipse_proximity': cf['c8_eclipse_proximity'],
            'nakshatra_subsystem': cf['c_nakshatra_subsystem'],
            'station_retrograde': cf['c10_station_retrograde'],
        }
        activity_without = convergence_score(nec, sup_without)
        assert w['activity'] == pytest.approx(activity_without, abs=1e-4)
        sup_with_static = dict(sup_without, constituent_lord_transit=0.8)
        assert activity_without < convergence_score(nec, sup_with_static), (
            "if the static prior leaked into the kernel, activity would be higher"
        )

    def test_covering_window_dasha_computed(self, monkeypatch):
        service = _FakeDashaService([
            _FakeEligibleWindow(date(2024, 5, 1), date(2024, 7, 1), 0.9),
        ])
        w = _patched_mode_a(monkeypatch, _predicate(), dasha_service=service)
        assert w['availability']['dasha'] == 'computed'
        assert w['applicability']['constituent_lord_transit'] is True


class TestR6OrderingKey:
    """RRV-03: one declared within-class ordering key; valence never pooled."""

    def _window(self, activity, valence, peak, klass='ka_sangam/DIGNITY'):
        return {
            'activity': activity,
            'valence': valence,
            'peak_date': peak,
            'comparability_class': klass,
            'kernel_version': KERNEL_VERSION_SEPARATED,
        }

    def test_activity_desc_contact_asc(self):
        a = self._window(0.9, 0.5, date(2024, 3, 1))
        b = self._window(0.9, -0.5, date(2024, 1, 1))
        c = self._window(0.7, 0.5, date(2024, 1, 1))
        ordered = sorted([a, b, c], key=ordering_key)
        # activity DESC first: a,b (0.9) before c (0.7)
        assert ordered[0]['activity'] == 0.9
        assert ordered[1]['activity'] == 0.9
        assert ordered[2]['activity'] == 0.7
        # contact instant ASC tiebreak: b (Jan) before a (Mar)
        assert ordered[0]['peak_date'] == date(2024, 1, 1)
        assert ordered[1]['peak_date'] == date(2024, 3, 1)

    def test_opposite_valence_both_survive_page_cut(self):
        """SPEC R-6 / RRV-03 assertion: two identical-activity rows of
        opposite valence both survive to a served page."""
        pos = self._window(0.8, 1.0, date(2024, 1, 1))
        neg = self._window(0.8, -1.0, date(2024, 2, 1))
        filler = self._window(0.1, 1.0, date(2024, 3, 1))
        page = sorted([filler, neg, pos], key=ordering_key)[:2]  # LIMIT 2
        assert {w['valence'] for w in page} == {1.0, -1.0}

    def test_classes_never_interleave(self):
        x = self._window(0.1, 0.0, date(2024, 1, 1), klass='ka_sangam/A')
        y = self._window(0.9, 0.0, date(2024, 1, 1), klass='ka_sangam/B')
        ordered = sorted([y, x], key=ordering_key)
        assert ordered[0]['comparability_class'] == 'ka_sangam/A'

    def test_deterministic_under_shuffle(self):
        import random
        windows = [
            self._window(0.5, 0.0, date(2024, m, 1)) for m in range(1, 7)
        ]
        orders = set()
        for seed in range(5):
            random.Random(seed).shuffle(windows)
            orders.add(tuple(w['peak_date'].month for w in sorted(windows, key=ordering_key)))
        assert len(orders) == 1, "ordering must be fully deterministic"


class TestR6VedhaUnavailable:
    """C11 unavailability is recorded, not silently neutral."""

    def test_vedha_unavailable_recorded_not_neutral(self, monkeypatch):
        w = _patched_mode_a(monkeypatch, _predicate(), ctx=EnrichmentContext.empty())
        # Legacy factor is neutral 1.0 (recorded for the legacy reading)...
        assert w['constituent_factors']['c11_vedha_factor'] == 1.0
        # ...but the new kernel records the truth: vedha was not evaluated.
        assert w['availability']['vedha'] == 'unavailable'
        assert w['applicability']['vedha_cancellation'] is False

    def test_vedha_covering_window_computed(self, monkeypatch):
        ctx = EnrichmentContext(vedha_rules=[{
            'graha': 'jupiter',
            'window_start': date(2024, 5, 20),
            'window_end': date(2024, 6, 10),
        }])
        w = _patched_mode_a(monkeypatch, _predicate(), ctx=ctx)
        assert w['availability']['vedha'] == 'computed'
        assert w['applicability']['vedha_cancellation'] is True
        assert w['constituent_factors']['c11_vedha_factor'] == pytest.approx(0.3)
        # vedha is a genuine necessary-side modulator: it lowers activity.
        assert w['activity'] < 1.0


class TestR6SignLevelRoutes:
    """Modes C and D carry the kernel with severity/SAV as activity."""

    def test_mode_c_kernel_fields(self):
        s, e = _horizon()
        svc = _FakeGocharaService(_date_to_jd(date(2024, 3, 1)))
        windows = mode_c_subsystem_period(
            predicate=_predicate(dignity_score=0.0),
            horizon_start_jd=s, horizon_end_jd=e,
            gochara_service=svc, moon_sign='Aquarius',
        )
        assert windows, "fixture must produce at least one ingress window"
        for w in windows:
            assert w['kernel_version'] == KERNEL_VERSION_SEPARATED
            assert w['activity'] == pytest.approx(w['constituent_factors']['severity_score'])
            assert w['valence'] == -1.0  # dignity 0 → adverse
            assert w['convergence_score'] == 0.0  # legacy: dignity × severity
            assert w['availability']['dasha'] == 'unavailable'
        # sorted by the R-6 ordering key, not the legacy composite
        assert windows == sorted(windows, key=ordering_key)

    def test_mode_d_kernel_fields(self):
        s, e = _horizon()
        svc = _FakeGocharaService(_date_to_jd(date(2024, 3, 1)))
        ctx = EnrichmentContext(ashtakavarga_bindu={'SARVA': {2: 32}})
        windows = mode_d_av_bindhu(
            predicate=_predicate(dignity_score=1.0),
            horizon_start_jd=s, horizon_end_jd=e,
            gochara_service=svc, enrichment_context=ctx,
        )
        assert windows, "SAV 32 ≥ 28 must produce ingress windows"
        for w in windows:
            sav_score = min(1.0, 32 / 56.0)
            assert w['kernel_version'] == KERNEL_VERSION_SEPARATED
            assert w['activity'] == pytest.approx(round(sav_score, 4))
            assert w['valence'] == 1.0
            assert w['convergence_score'] == pytest.approx(round(1.0 * sav_score, 4))
            assert w['applicability']['av_bindhu_route'] is True
        assert windows == sorted(windows, key=ordering_key)
