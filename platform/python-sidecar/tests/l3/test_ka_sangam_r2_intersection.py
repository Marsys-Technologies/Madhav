"""
Tests for ka_sangam R-2 clock-intersection oracle
(plan §3 R-2 / §3b SPEC R-2; F-13 repair).

Oracle cases from the SPEC falsifier: unequal endpoints, disjoint, nested
levels, zero score, valid empty, service failure, sub-day boundary.
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime
from types import SimpleNamespace

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_dasha_kala.intersection import (
    BOUNDARY_CONVENTION,
    intersect_segments,
    agreement_for,
)
from services.ka_dasha_kala.tree_walk import DashaInterval
from services.ka_dasha_kala import service as DS
from services.ka_sangam.engine import (
    _c_cross_dasha_agreement,
    _date_to_jd,
)

_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'


def _iv(start, end, *, system='vimshottari', level=2, lord='Jupiter',
        row='r1', parent=None):
    """Synthetic interval bearing the identity fields the oracle reads."""
    return SimpleNamespace(
        start_date=start, end_date=end,
        system_id=system, level_n=level, lord_graha=lord,
        dasha_row_id=row, parent_row_id=parent,
    )


class _FakeTransitEvent:
    def __init__(self, exact_longitude_deg, event_jd, orb_at_event_deg=0.0,
                 applying_separating='applying', aspect_deg=0):
        self.exact_longitude_deg = exact_longitude_deg
        self.event_jd = event_jd
        self.orb_at_event_deg = orb_at_event_deg
        self.applying_separating = applying_separating
        self.extra = {'aspect_deg': aspect_deg}
        self.sign = 'Capricorn'
        self.nakshatra = 'Uttara Ashadha'
        self.event_datetime_ist = '2026-06-01 00:00:00'


# ── Oracle: SPEC R-2 falsifier cases ─────────────────────────────────────────

class TestIntersectionOracle:
    def test_unequal_endpoints_agree(self):
        """The S6 case: two clocks overlapping ~305 d with different endpoints
        must register agreement (exact-key grouping gave them different keys)."""
        a = _iv(date(2027, 1, 1), date(2027, 12, 31), system='vim', row='ra')
        b = _iv(date(2027, 3, 1), date(2028, 2, 28), system='yog', row='rb')
        segs = intersect_segments([a, b])
        sa = agreement_for(a.start_date, a.end_date, segs)
        sb = agreement_for(b.start_date, b.end_date, segs)
        assert sa.count == 2 and sa.systems_agreeing == ('vim', 'yog')
        assert sb.count == 2
        shared = [s for s in segs
                  if {r.system_id for r in s.supporters} == {'vim', 'yog'}]
        assert len(shared) == 1
        assert shared[0].start == date(2027, 3, 1)
        assert shared[0].end == date(2027, 12, 31)

    def test_disjoint_intervals_do_not_agree(self):
        a = _iv(date(2027, 1, 1), date(2027, 6, 30), system='vim', row='ra')
        b = _iv(date(2027, 7, 1), date(2027, 12, 31), system='yog', row='rb')
        segs = intersect_segments([a, b])
        assert agreement_for(a.start_date, a.end_date, segs).count == 1
        assert agreement_for(b.start_date, b.end_date, segs).count == 1
        assert all(len(s.supporters) == 1 for s in segs)

    def test_transitive_chain_is_not_merged(self):
        """A overlaps B, B overlaps C, A disjoint C: C must NOT inherit A.
        Direct co-support only — never transitive merging of overlappers."""
        a = _iv(date(2027, 1, 1), date(2027, 4, 10), system='vim', row='ra')
        b = _iv(date(2027, 3, 1), date(2027, 7, 10), system='yog', row='rb')
        c = _iv(date(2027, 6, 1), date(2027, 10, 10), system='chara', row='rc')
        segs = intersect_segments([a, b, c])
        assert agreement_for(c.start_date, c.end_date, segs).count == 2
        assert agreement_for(c.start_date, c.end_date, segs).systems_agreeing == ('chara', 'yog')
        assert agreement_for(a.start_date, a.end_date, segs).count == 2
        assert agreement_for(a.start_date, a.end_date, segs).systems_agreeing == ('vim', 'yog')
        # A and C never share a segment
        assert not any({'vim', 'chara'} <= {r.system_id for r in s.supporters}
                       for s in segs)

    def test_nested_levels_same_system_not_inflated(self):
        """A level-1 span containing a level-3 span of the SAME system, plus a
        level-2 span of another system: agreement counts DISTINCT systems (2),
        not intervals (3). Parent identity is carried on the supporter refs."""
        l1 = _iv(date(2020, 1, 1), date(2030, 1, 1), system='vim', level=1,
                 row='r_l1', parent=None)
        l3 = _iv(date(2024, 1, 1), date(2025, 1, 1), system='vim', level=3,
                 row='r_l3', parent='r_l1')
        other = _iv(date(2024, 1, 1), date(2025, 1, 1), system='yog', level=2,
                    row='r_o', parent=None)
        segs = intersect_segments([l1, l3, other])
        summary = agreement_for(l3.start_date, l3.end_date, segs)
        assert summary.count == 2
        shared = [s for s in segs
                  if {r.system_id for r in s.supporters} == {'vim', 'yog'}]
        assert len(shared) == 1
        seg = shared[0]
        assert {r.level_n for r in seg.supporters} == {1, 2, 3}
        parents = {r.dasha_row_id: r.parent_row_id for r in seg.supporters}
        assert parents['r_l3'] == 'r_l1'

    def test_degenerate_interval_is_evaluated_zero(self):
        """A zero-length [d, d) interval supports nothing: a REAL, evaluated
        zero — distinct from unavailable (R-2)."""
        a = _iv(date(2027, 5, 1), date(2027, 5, 1), system='vim', row='ra')
        segs = intersect_segments([a])
        assert segs == []
        assert agreement_for(a.start_date, a.end_date, segs).count == 0

    def test_valid_empty_is_not_failure(self):
        """A successful query over zero intervals yields zero segments —
        evaluated, empty; never an error state."""
        assert intersect_segments([]) == []

    def test_contiguous_intervals_do_not_agree(self):
        """S-H: [0,10) and [10,20) share nothing — a boundary instant belongs
        to exactly one interval."""
        a = _iv(date(2027, 1, 1), date(2027, 4, 10), system='vim', row='ra')
        b = _iv(date(2027, 4, 10), date(2027, 7, 10), system='yog', row='rb')
        segs = intersect_segments([a, b])
        assert all(len(s.supporters) == 1 for s in segs)
        assert agreement_for(a.start_date, a.end_date, segs).count == 1
        assert agreement_for(b.start_date, b.end_date, segs).count == 1

    def test_sub_day_datetime_boundaries(self):
        """The oracle is grain-agnostic: datetime intervals split at sub-day
        boundaries under the same S-H convention."""
        a = _iv(datetime(2024, 1, 1, 6, 0), datetime(2024, 1, 3, 6, 0),
                system='vim', row='ra')
        b = _iv(datetime(2024, 1, 3, 0, 0), datetime(2024, 1, 5, 0, 0),
                system='yog', row='rb')
        segs = intersect_segments([a, b])
        starts = [s.start for s in segs]
        assert datetime(2024, 1, 3, 0, 0) in starts   # sub-day boundary
        assert datetime(2024, 1, 3, 6, 0) in starts
        shared = [s for s in segs
                  if {r.system_id for r in s.supporters} == {'vim', 'yog'}]
        assert len(shared) == 1
        assert shared[0].start == datetime(2024, 1, 3, 0, 0)
        assert shared[0].end == datetime(2024, 1, 3, 6, 0)
        # S-H: b's end instant is not covered by b
        assert agreement_for(datetime(2024, 1, 5, 0, 0),
                             datetime(2024, 1, 6, 0, 0), segs).count == 0

    def test_boundary_convention_declared(self):
        assert BOUNDARY_CONVENTION == '[start, end)'


# ── Service wiring ────────────────────────────────────────────────────────────

def _dasha_interval(system, start, end, row):
    return DashaInterval(
        dasha_row_id=row, chart_id=_CHART_ID, ayanamsha_id='lahiri',
        system_id=system, level_n=2, lord_graha='Jupiter',
        start_date=start, end_date=end, parent_row_id=None,
        ancestor_lords=[], eligibility_score=0.8,
    )


class TestServiceR2Wiring:
    def test_query_agreement_via_intersection(self, monkeypatch):
        """Windows with unequal endpoints across two systems agree under the
        oracle; under the withdrawn exact-key grouping each counted 1."""
        def fake_walk(*, system_id, **kwargs):
            if system_id == 'vimshottari':
                return [_dasha_interval('vimshottari', date(2027, 1, 1), date(2027, 12, 31), 'ra')]
            if system_id == 'yogini':
                return [_dasha_interval('yogini', date(2027, 3, 1), date(2028, 2, 28), 'rb')]
            return []
        monkeypatch.setattr(DS, 'walk_eligible_intervals', fake_walk)

        svc = DS.KaDashaKalaService(db_conn=None)
        result = svc.query(
            chart_id=_CHART_ID, ayanamsha_id='lahiri',
            target_lords={'Jupiter'}, related_lords=set(),
            date_start=date(2026, 1, 1), date_end=date(2029, 1, 1),
            max_level=3,
            systems={'vimshottari', 'yogini'},
        )
        counts = sorted(w.cross_dasha_agreement.count for w in result.windows)
        systems = sorted(w.cross_dasha_agreement.systems_agreeing for w in result.windows)
        assert counts == [2, 2]
        assert systems == [['vimshottari', 'yogini'], ['vimshottari', 'yogini']]
        assert result.high_agreement_count == 2

    def test_query_zero_intervals_is_evaluated_empty(self, monkeypatch):
        monkeypatch.setattr(DS, 'walk_eligible_intervals', lambda **kwargs: [])
        svc = DS.KaDashaKalaService(db_conn=None)
        result = svc.query(
            chart_id=_CHART_ID, ayanamsha_id='lahiri',
            target_lords={'Jupiter'}, related_lords=set(),
            date_start=date(2026, 1, 1), date_end=date(2029, 1, 1),
            max_level=3, systems={'vimshottari'},
        )
        assert result.windows == []
        assert result.total_windows == 0
        assert result.high_agreement_count == 0


# ── Engine: boundary convention + query-state distinction ────────────────────

def _window(start, end, count=None, eligibility=0.8):
    agreement = (SimpleNamespace(count=count, systems_agreeing=['vimshottari'] * (count or 0))
                 if count is not None else None)
    return SimpleNamespace(start_date=start, end_date=end,
                           eligibility_score=eligibility,
                           cross_dasha_agreement=agreement)


class TestEngineR2:
    def test_c_cross_boundary_is_start_inclusive_end_exclusive(self):
        windows = [_window(date(2026, 3, 1), date(2026, 5, 1), count=3)]
        # interior: covered
        assert _c_cross_dasha_agreement(date(2026, 4, 1), windows) == pytest.approx(3.0 / 7.0)
        # exactly at end: NOT covered (S-H)
        assert _c_cross_dasha_agreement(date(2026, 5, 1), windows) is None
        # exactly at start: covered
        assert _c_cross_dasha_agreement(date(2026, 3, 1), windows) == pytest.approx(3.0 / 7.0)

    def _mode_a(self, monkeypatch, dasha_service, peak=date(2026, 6, 1)):
        from services.ka_sangam.engine import mode_a_search
        monkeypatch.setattr(
            'pipeline.transit_search.find_aspect_events',
            lambda **kwargs: [_FakeTransitEvent(270.0, _date_to_jd(peak))],
        )
        predicate = {
            'signal_id': 'eeeeeeee-0000-0000-0000-000000000001',
            'signature_class': 'YOGA',
            'dignity_score': 0.7,
            'dasha_eligibility_rule_jsonb': {
                'eligibility_score': 0.6,
                'constituent_lords': ['Jupiter'],
            },
            'transit_trigger_jsonb': {
                'planet': 'Jupiter',
                'target_longitude_deg': 270.0,
                'aspect_degrees': [0],
                'orb_deg': 5.0,
            },
            'strength_affliction_hook_jsonb': {},
            'derivation_ledger_jsonb': {},
        }
        return mode_a_search(
            janma_nakshatra_idx=24,
            predicate=predicate,
            horizon_start_jd=_date_to_jd(date(2026, 1, 1)),
            horizon_end_jd=_date_to_jd(date(2027, 1, 1)),
            dasha_kala_service=dasha_service,
            gochara_service=None,
            muhurta_service=None,
            chart_id=_CHART_ID,
        )

    def test_service_failure_records_unavailable_not_evaluated_empty(self, monkeypatch):
        class _Boom:
            def query(self, **kwargs):
                raise RuntimeError('dasha store unreachable')
        windows = self._mode_a(monkeypatch, _Boom())
        assert len(windows) == 1
        cf = windows[0]['constituent_factors']
        assert 'c_cross_dasha_agreement_unavailable' in cf
        assert 'FAILED' in cf['c_cross_dasha_agreement_unavailable']
        assert 'c_cross_dasha_agreement_evaluated_empty' not in cf
        assert windows[0]['availability']['dasha'] == 'unavailable'

    def test_query_ok_no_covering_window_records_evaluated_empty(self, monkeypatch):
        """Query succeeded; windows exist but none covers the peak — the R-2
        'evaluated, empty' state, never merged with failure."""
        result = SimpleNamespace(windows=[_window(date(2027, 3, 1), date(2027, 5, 1), count=2)])
        windows = self._mode_a(monkeypatch, SimpleNamespace(query=lambda **k: result))
        cf = windows[0]['constituent_factors']
        assert 'c_cross_dasha_agreement_evaluated_empty' in cf
        assert 'c_cross_dasha_agreement_unavailable' not in cf

    def test_query_ok_valid_empty_records_evaluated_empty(self, monkeypatch):
        """Query succeeded with ZERO windows — valid empty, still evaluated."""
        result = SimpleNamespace(windows=[])
        windows = self._mode_a(monkeypatch, SimpleNamespace(query=lambda **k: result))
        cf = windows[0]['constituent_factors']
        assert 'c_cross_dasha_agreement_evaluated_empty' in cf
        assert 'c_cross_dasha_agreement_unavailable' not in cf

    def test_covering_window_scores_cross_value(self, monkeypatch):
        result = SimpleNamespace(windows=[
            _window(date(2026, 5, 1), date(2026, 7, 1), count=2, eligibility=0.9),
        ])
        windows = self._mode_a(monkeypatch, SimpleNamespace(query=lambda **k: result))
        cf = windows[0]['constituent_factors']
        assert cf['c_cross_dasha_agreement'] == pytest.approx(0.2857)
        assert windows[0]['availability']['dasha'] == 'computed'
