"""
Tests for ka_sangam R-1 (target provenance / availability) and R-4
(withdrawal of benefic_dristi / transit_to_transit from the scored product).

Anti-drift: engine-only fixtures for Mode B; writer target-resolution helpers
are exercised with in-memory fake chart_facts.
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
    mode_b_sweep,
    _has_target_provenance,
    _target_provenance_dict,
    _date_to_jd,
)
from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter

_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
_TAURUS_LON = 35.0


class _FakeTransitEvent:
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


def _horizon():
    return _date_to_jd(date(2024, 1, 1)), _date_to_jd(date(2029, 1, 1))


def _base_predicate(target_lon=None, provenance=None):
    trig = {
        'aspect_degrees': [0],
        'orb_deg': 5.0,
    }
    if target_lon is not None:
        trig['target_longitude_deg'] = target_lon
    if provenance:
        trig.update(provenance)
    return {
        'signal_id': 'eeeeeeee-0000-0000-0000-000000000000',
        'signature_class': 'DIGNITY',
        'graha_name': 'Jupiter',
        'dignity_score': 0.9,
        'dasha_eligibility_rule_jsonb': {'eligibility_score': 0.5},
        'transit_trigger_jsonb': trig,
        'strength_affliction_hook_jsonb': {},
        'derivation_ledger_jsonb': {},
    }


class TestModeBR1R4:
    """Mode B R-1/R-4 wiring."""

    def test_mode_b_refuses_unresolvable_target(self, monkeypatch):
        """A trigger with neither target_longitude_deg nor provenance returns []."""
        pred = _base_predicate()
        result = mode_b_sweep(
            janma_nakshatra_idx=3,
            signal_id='eeeeeeee-0000-0000-0000-000000000000',
            predicate=pred,
            horizon_start_jd=_horizon()[0],
            horizon_end_jd=_horizon()[1],
            gochara_service=None,
            magnitude_threshold=0.1,
        )
        assert result == []

    def test_mode_b_includes_target_provenance_and_availability(self, monkeypatch):
        event = _FakeTransitEvent(_TAURUS_LON, _date_to_jd(date(2024, 6, 1)))
        monkeypatch.setattr(
            'pipeline.transit_search.search_long_horizon', lambda **kwargs: [event]
        )
        provenance = {
            'target_fact_id': 'f_001',
            'target_type': 'graha_position',
            'frame': 'longitude_sidereal',
            'ayanamsha_id': 'lahiri_chitrapaksha',
            'derivation': 'test',
        }
        pred = _base_predicate(target_lon=_TAURUS_LON, provenance=provenance)
        windows = mode_b_sweep(
            janma_nakshatra_idx=3,
            signal_id='eeeeeeee-0000-0000-0000-000000000000',
            predicate=pred,
            horizon_start_jd=_horizon()[0],
            horizon_end_jd=_horizon()[1],
            gochara_service=None,
            magnitude_threshold=0.1,
        )
        assert len(windows) == 1
        w = windows[0]
        assert w['availability']['target'] == 'computed'
        cf = w['constituent_factors']
        assert 'target_provenance' in cf
        assert cf['target_provenance']['target_fact_id'] == 'f_001'

    def test_mode_b_supporting_excludes_withdrawn_keys(self, monkeypatch):
        event = _FakeTransitEvent(_TAURUS_LON, _date_to_jd(date(2024, 6, 1)))
        monkeypatch.setattr(
            'pipeline.transit_search.search_long_horizon', lambda **kwargs: [event]
        )
        pred = _base_predicate(target_lon=_TAURUS_LON)
        windows = mode_b_sweep(
            janma_nakshatra_idx=3,
            signal_id='eeeeeeee-0000-0000-0000-000000000000',
            predicate=pred,
            horizon_start_jd=_horizon()[0],
            horizon_end_jd=_horizon()[1],
            gochara_service=None,
            magnitude_threshold=0.1,
        )
        assert len(windows) == 1
        # The scored supporting product is internal; R-6 applicability is the public
        # contract that these terms were not admitted to the kernel.
        assert windows[0]['applicability']['benefic_dristi'] is False
        assert windows[0]['applicability']['transit_to_transit'] is False
        # Lineage values and withdrawal reasons are still carried as data.
        cf = windows[0]['constituent_factors']
        assert 'c_benefic_dristi' in cf
        assert 'c_benefic_dristi_withdrawn' in cf
        assert 'c9_transit_to_transit' in cf
        assert 'c9_transit_to_transit_withdrawn' in cf

    def test_mode_b_constituent_factors_include_withdrawn_reason_keys(self, monkeypatch):
        event = _FakeTransitEvent(_TAURUS_LON, _date_to_jd(date(2024, 6, 1)))
        monkeypatch.setattr(
            'pipeline.transit_search.search_long_horizon', lambda **kwargs: [event]
        )
        pred = _base_predicate(target_lon=_TAURUS_LON)
        windows = mode_b_sweep(
            janma_nakshatra_idx=3,
            signal_id='eeeeeeee-0000-0000-0000-000000000000',
            predicate=pred,
            horizon_start_jd=_horizon()[0],
            horizon_end_jd=_horizon()[1],
            gochara_service=None,
            magnitude_threshold=0.1,
        )
        assert len(windows) == 1
        cf = windows[0]['constituent_factors']
        assert 'c_benefic_dristi_withdrawn' in cf
        assert 'c9_transit_to_transit_withdrawn' in cf
        assert 'c_benefic_dristi' in cf
        assert 'c9_transit_to_transit' in cf


class TestWriterTargetResolution:
    """Writer-side R-1 target provenance enrichment."""

    def _writer(self, facts):
        writer = KaSangamWriter()
        writer._target_facts = facts
        return writer

    def test_resolve_dignity_target(self):
        facts = [{
            'fact_id': 'f_jup',
            'fact_category': 'graha_position',
            'fact_subject': 'JUP',  # norm_graha('Jupiter')
            'fact_key': 'longitude_sidereal',
            'fact_value_num': 35.0,
            'ayanamsha_id': 'lahiri_chitrapaksha',
        }]
        writer = self._writer(facts)
        result = writer._resolve_target_for_predicate({
            'signature_class': 'DIGNITY',
            'graha_name': 'Jupiter',
            'ayanamsha_id': 'lahiri_chitrapaksha',
        })
        assert result is not None
        assert result['target_longitude_deg'] == 35.0
        assert result['target_fact_id'] == 'f_jup'
        assert result['target_type'] == 'graha_position'
        assert result['frame'] == 'longitude_sidereal'

    def test_resolve_dispositor_target(self):
        facts = [{
            'fact_id': 'f_h5',
            'fact_category': 'bhava_cusps',
            'fact_subject': 'BHAVA_05',
            'fact_key': 'sripati_madhya',
            'fact_value_num': 123.0,
            'ayanamsha_id': 'lahiri_chitrapaksha',
        }]
        writer = self._writer(facts)
        result = writer._resolve_target_for_predicate({
            'signature_class': 'DISPOSITOR_RELATIONAL',
            'house_num': 5,
            'ayanamsha_id': 'lahiri_chitrapaksha',
        })
        assert result is not None
        assert result['target_longitude_deg'] == 123.0
        assert result['target_type'] == 'bhava_cusps'
        assert result['frame'] == 'sripati_madhya'

    def test_resolve_yoga_first_lord_target(self):
        facts = [{
            'fact_id': 'f_mar',
            'fact_category': 'graha_position',
            'fact_subject': 'MAR',  # norm_graha('Mars')
            'fact_key': 'longitude_sidereal',
            'fact_value_num': 15.0,
            'ayanamsha_id': 'lahiri_chitrapaksha',
        }]
        writer = self._writer(facts)
        result = writer._resolve_target_for_predicate({
            'signature_class': 'YOGA',
            'dasha_eligibility_rule_jsonb': {'constituent_lords': ['Mars', 'Saturn']},
            'ayanamsha_id': 'lahiri_chitrapaksha',
        })
        assert result is not None
        assert result['target_longitude_deg'] == 15.0

    def test_unresolvable_predicate_returns_none(self):
        writer = self._writer([])
        result = writer._resolve_target_for_predicate({
            'signature_class': 'DOSHA',
            'ayanamsha_id': 'lahiri_chitrapaksha',
        })
        assert result is None

    def test_enrich_predicate_target_stamps_provenance(self):
        facts = [{
            'fact_id': 'f_jup',
            'fact_category': 'graha_position',
            'fact_subject': 'JUP',  # norm_graha('Jupiter')
            'fact_key': 'longitude_sidereal',
            'fact_value_num': 35.0,
            'ayanamsha_id': 'lahiri_chitrapaksha',
        }]
        writer = self._writer(facts)
        pd = {
            'signature_class': 'DIGNITY',
            'graha_name': 'Jupiter',
            'ayanamsha_id': 'lahiri_chitrapaksha',
            'transit_trigger_jsonb': {'aspect_degrees': [0], 'orb_deg': 5.0},
        }
        writer._enrich_predicate_target(pd)
        trig = pd['transit_trigger_jsonb']
        assert trig['target_longitude_deg'] == 35.0
        assert trig['target_fact_id'] == 'f_jup'
        assert _has_target_provenance(trig)


class TestWriterR3bFailLoudLagna:
    """R-3(b): lagna lookup raises when chart_facts has no lagna sign row."""

    def test_build_house_lord_map_raises_when_lagna_missing(self):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        conn.cursor.return_value.__enter__.return_value = cursor
        writer = KaSangamWriter()
        with pytest.raises(RuntimeError, match="could not resolve lagna sign"):
            writer._build_house_lord_map(conn, _CHART_ID)

    def test_build_house_lord_map_raises_when_lagna_sign_invalid(self):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = {'fact_value_text': 'NotASign'}
        conn.cursor.return_value.__enter__.return_value = cursor
        writer = KaSangamWriter()
        with pytest.raises(RuntimeError, match="not a recognised sign name"):
            writer._build_house_lord_map(conn, _CHART_ID)
