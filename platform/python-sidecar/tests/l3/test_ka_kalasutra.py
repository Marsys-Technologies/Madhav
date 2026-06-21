"""Tests for ka_kalasutra bounded activation artifact builder."""
import re
import pytest
from datetime import date, timedelta
from pathlib import Path

# Import the helper functions directly (not the writer class which needs DB)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.orchestrator.writers.ka_kalasutra import (
    _derive_dasha_periods,
    _derive_activation_dates,
    _derive_proximity_score,
    _compute_activation_start,
    _compute_activation_end,
)

WRITER_PATH = Path(__file__).parent.parent.parent / "pipeline/orchestrator/writers/ka_kalasutra.py"


class TestDeriveDashaPeriods:
    def test_derive_dasha_periods_with_lords(self):
        """rule has constituent_lords -> output list has graha entries"""
        rule = {'constituent_lords': ['Sun', 'Moon', 'Mars']}
        result = _derive_dasha_periods(rule)
        assert len(result) == 3
        assert all('graha' in entry for entry in result)
        assert result[0]['graha'] == 'Sun'
        assert result[0]['level'] == 'mahadasha'
        assert result[0]['source'] == 'dasha_eligibility_rule'

    def test_derive_dasha_periods_empty(self):
        """empty rule -> []"""
        assert _derive_dasha_periods({}) == []
        assert _derive_dasha_periods(None) == []

    def test_derive_dasha_periods_with_explicit_periods(self):
        """rule with explicit periods -> combined output"""
        rule = {
            'constituent_lords': ['Jupiter'],
            'periods': [{'graha': 'Venus', 'level': 'antardasha', 'source': 'explicit'}]
        }
        result = _derive_dasha_periods(rule)
        assert len(result) == 2
        assert result[0]['graha'] == 'Jupiter'
        assert result[1]['graha'] == 'Venus'


class TestDeriveActivationDates:
    def test_derive_activation_dates_with_peak(self):
        """peak_date given -> 7-element list (+-3 days)"""
        peak = date(2026, 6, 15)
        transit_rule = {'type': 'transit_conjunction'}
        result = _derive_activation_dates(transit_rule, peak)
        assert len(result) == 7

    def test_derive_activation_dates_no_peak(self):
        """peak=None -> []"""
        result = _derive_activation_dates({'type': 'transit'}, None)
        assert result == []

    def test_derive_activation_dates_strength_decay(self):
        """strength 1.0 at peak, decreasing outward"""
        peak = date(2026, 6, 15)
        transit_rule = {'type': 'transit'}
        result = _derive_activation_dates(transit_rule, peak)
        # Sort by date to find peak (middle element)
        strengths = [entry['strength'] for entry in result]
        # Peak should be index 3 (delta=0)
        assert strengths[3] == 1.0
        # Outward entries should have lower strength
        assert strengths[2] < strengths[3]
        assert strengths[4] < strengths[3]
        assert strengths[0] < strengths[1]

    def test_activation_dates_are_sorted(self):
        """dates in output are in ascending order"""
        peak = date(2026, 6, 15)
        result = _derive_activation_dates({'type': 'transit'}, peak)
        dates = [entry['date'] for entry in result]
        assert dates == sorted(dates)

    def test_derive_activation_dates_no_transit_rule(self):
        """No transit rule -> []"""
        result = _derive_activation_dates(None, date(2026, 6, 15))
        assert result == []


class TestDeriveProximityScore:
    def test_proximity_score_range(self):
        """result always in [0,1]"""
        for dignity in [0.0, 0.5, 1.0, 1.5]:
            for non_aff in [0.0, 0.5, 1.0]:
                score = _derive_proximity_score({'dignity_score': dignity}, {'non_affliction': non_aff}, date(2026, 1, 1))
                assert 0.0 <= score <= 1.0

    def test_proximity_score_high_dignity(self):
        """dignity=1.0, non_affliction=1.0 -> score ~1.0"""
        score = _derive_proximity_score(
            {'dignity_score': 1.0},
            {'non_affliction': 1.0},
            date(2026, 6, 15)
        )
        assert abs(score - 1.0) < 0.001

    def test_proximity_score_no_peak(self):
        """peak=None -> 0.5"""
        score = _derive_proximity_score({}, {}, None)
        assert score == 0.5


class TestComputeActivationWindow:
    def test_compute_activation_window_yoga(self):
        """YOGA -> 7-day window each side"""
        peak = date(2026, 6, 15)
        start = _compute_activation_start(peak, 'YOGA')
        end = _compute_activation_end(peak, 'YOGA')
        assert start == peak - timedelta(days=7)
        assert end == peak + timedelta(days=7)

    def test_compute_activation_window_dosha(self):
        """DOSHA -> 14-day window"""
        peak = date(2026, 6, 15)
        start = _compute_activation_start(peak, 'DOSHA')
        end = _compute_activation_end(peak, 'DOSHA')
        assert start == peak - timedelta(days=14)
        assert end == peak + timedelta(days=14)

    def test_compute_activation_window_no_peak(self):
        """no peak -> None/None"""
        assert _compute_activation_start(None, 'YOGA') is None
        assert _compute_activation_end(None, 'YOGA') is None

    def test_compute_start_before_end(self):
        """start < end for any non-None peak"""
        peak = date(2026, 6, 15)
        for sig_class in ['YOGA', 'DOSHA', 'DIGNITY', 'SENSITIVE_POINT', 'SUBSYSTEM']:
            start = _compute_activation_start(peak, sig_class)
            end = _compute_activation_end(peak, sig_class)
            assert start < end

    def test_signature_class_window_default(self):
        """unknown sig_class -> 5-day default window"""
        peak = date(2026, 6, 15)
        start = _compute_activation_start(peak, 'UNKNOWN_CLASS')
        end = _compute_activation_end(peak, 'UNKNOWN_CLASS')
        assert start == peak - timedelta(days=5)
        assert end == peak + timedelta(days=5)


class TestWriterContractGrep:
    def test_writer_contract_no_commit(self):
        """grep writers/ka_kalasutra.py for .commit() -> 0 matches"""
        source = WRITER_PATH.read_text()
        matches = re.findall(r'\.commit\(\)', source)
        assert len(matches) == 0, f"Found .commit() calls: {matches}"

    def test_writer_contract_no_rollback(self):
        """grep for .rollback() -> 0 matches"""
        source = WRITER_PATH.read_text()
        matches = re.findall(r'\.rollback\(\)', source)
        assert len(matches) == 0, f"Found .rollback() calls: {matches}"

    def test_writer_contract_no_l2_writes(self):
        """grep for INSERT INTO bodha_ -> 0 matches"""
        source = WRITER_PATH.read_text()
        matches = re.findall(r'INSERT INTO bodha_|UPDATE bodha_', source)
        assert len(matches) == 0, f"Found L2 write attempts: {matches}"

    def test_writer_contract_no_kala_timeline_writes(self):
        """grep for INSERT INTO kala_timeline -> 0 matches"""
        source = WRITER_PATH.read_text()
        matches = re.findall(r'INSERT INTO kala_timeline', source)
        assert len(matches) == 0, f"Found kala_timeline write attempts: {matches}"

    def test_source_citation_format(self):
        """source_citation starts with 'ka_kalasutra:v1.0:'"""
        source = WRITER_PATH.read_text()
        # Find the source_citation format string in the writer
        assert 'ka_kalasutra:v1.0:' in source

    def test_l2_hooks_are_l3_only(self):
        """assert that L2 table (bodha_msr_signals) is NEVER written"""
        source = WRITER_PATH.read_text()
        l2_writes = re.findall(r'(INSERT INTO|UPDATE)\s+bodha_msr_signals', source)
        assert len(l2_writes) == 0, f"Found writes to bodha_msr_signals: {l2_writes}"
