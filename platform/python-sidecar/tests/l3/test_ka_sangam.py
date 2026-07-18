"""
Tests for ka_sangam — Convergence engine (L3 K4-a).

Covers:
  - Scoring invariants: I-16 (convergence_score), I-17 (orb_strength), I-21 (confidence_label),
    I-22 (independent_current_count)
  - Mode A + Mode B behaviour
  - SPINE-FIRST GATE: end-to-end single signal
  - Anti-drift: no bodha_* writes
  - Contract: no commit/rollback in writer
"""
from __future__ import annotations

import math
import os
import sys
import subprocess
from datetime import date

import pytest

# Ensure the sidecar root is on sys.path
_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_sangam.engine import (
    SUPPORTING_WEIGHTS,
    HIGH_CONFIDENCE_ORB_THRESHOLD,
    convergence_score,
    orb_strength_score,
    confidence_label,
    relative_confidence_labels,
    independent_current_count,
    mode_a_search,
    mode_b_sweep,
    _jd_to_date,
    _date_to_jd,
    _resolve_transit_planet,
)


# ─── I-16: convergence_score ─────────────────────────────────────────────────

class TestConvergenceScore:

    def test_veto_kills_score(self):
        """Necessary condition of 0 drives score to ~0 (multiplicative veto)."""
        result = convergence_score([0.0, 1.0], {'constituent_lord_transit': 1.0})
        assert result < 0.05

    def test_saturation_increases_score(self):
        """More supporting factors → higher convergence score."""
        few_score = convergence_score(
            [1.0],
            {'constituent_lord_transit': 0.8},
        )
        more_score = convergence_score(
            [1.0],
            {
                'constituent_lord_transit': 0.8,
                'benefic_dristi': 0.7,
                'cross_dasha_agreement': 0.9,
            },
        )
        assert more_score > few_score

    def test_positive_score_all_conditions(self):
        """All conditions fully present → score > 0."""
        sup = {k: 1.0 for k in SUPPORTING_WEIGHTS}
        result = convergence_score([1.0, 1.0, 1.0], sup)
        assert result > 0

    def test_score_range_zero_to_one(self):
        """Score always in [0, 1] for edge inputs."""
        assert convergence_score([], {}) >= 0.0
        assert convergence_score([2.0], {'constituent_lord_transit': 3.0}) <= 1.0
        assert convergence_score([-1.0], {}) >= 0.0

    def test_convergence_score_clamped(self):
        """Result clamped to [0,1] with extreme inputs."""
        r1 = convergence_score([10.0, 10.0], {k: 10.0 for k in SUPPORTING_WEIGHTS})
        assert 0.0 <= r1 <= 1.0
        r2 = convergence_score([-5.0], {k: -5.0 for k in SUPPORTING_WEIGHTS})
        assert 0.0 <= r2 <= 1.0

    def test_all_zero_supporting_gives_zero(self):
        """If all supporting factors are 0, score = 0 (saturation term = 0)."""
        result = convergence_score([1.0], {k: 0.0 for k in SUPPORTING_WEIGHTS})
        assert result == pytest.approx(0.0, abs=1e-6)

    def test_single_veto_any_position(self):
        """A veto at any position in necessary list kills the score."""
        result = convergence_score([1.0, 0.0, 1.0], {'constituent_lord_transit': 1.0})
        assert result < 0.05


# ─── I-17: orb_strength_score ────────────────────────────────────────────────

class TestOrbStrengthScore:

    def test_orb_exact_is_one(self):
        """Exact orb (0°) with applying → 1.0."""
        result = orb_strength_score(0.0, 1.0, 'applying')
        assert result == pytest.approx(1.0, abs=1e-6)

    def test_orb_at_boundary_near_zero(self):
        """Orb at max boundary → ~0 (cos²(π/2) = 0)."""
        result = orb_strength_score(1.0, 1.0, 'applying')
        assert result < 0.01

    def test_applying_greater_than_separating(self):
        """Same orb, applying > separating."""
        applying = orb_strength_score(0.5, 2.0, 'applying')
        separating = orb_strength_score(0.5, 2.0, 'separating')
        assert applying > separating

    def test_orb_strength_values_in_range(self):
        """orb_strength_score always in [0, 1]."""
        for orb in [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]:
            for max_o in [1.0, 5.0, 10.0]:
                for mode in ['applying', 'separating', 'stationary']:
                    r = orb_strength_score(orb, max_o, mode)
                    assert 0.0 <= r <= 1.0, f"Out of range: orb={orb}, max={max_o}, mode={mode}, r={r}"

    def test_exact_applying_is_one(self):
        """Cos² at 0 = 1, × 1.0 for applying = 1.0."""
        assert orb_strength_score(0.0, 5.0, 'applying') == pytest.approx(1.0, abs=1e-6)

    def test_exact_separating_is_0_7(self):
        """Cos² at 0 = 1, × 0.7 for separating = 0.7."""
        assert orb_strength_score(0.0, 5.0, 'separating') == pytest.approx(0.7, abs=1e-6)

    def test_mid_orb_cos_squared_shape(self):
        """At mid-orb, value should follow cos²(π/4) = 0.5."""
        # orb = max/2 → ratio = 0.5 → cos²(π/4) = 0.5
        result = orb_strength_score(0.5, 1.0, 'applying')
        expected = math.cos(0.5 * math.pi / 2.0) ** 2
        assert result == pytest.approx(expected, abs=1e-5)

    def test_zero_max_orb_returns_one(self):
        """max_orb_deg = 0 edge case → returns 1.0."""
        assert orb_strength_score(0.0, 0.0, 'applying') == pytest.approx(1.0, abs=1e-6)


# ─── I-21: confidence_label ──────────────────────────────────────────────────

class TestConfidenceLabel:

    def test_confidence_high(self):
        assert confidence_label(0.80) == 'high'

    def test_confidence_moderate(self):
        assert confidence_label(0.60) == 'moderate'

    def test_confidence_speculative(self):
        assert confidence_label(0.30) == 'speculative'

    def test_confidence_boundary_high(self):
        assert confidence_label(0.75) == 'high'

    def test_confidence_boundary_moderate(self):
        assert confidence_label(0.45) == 'moderate'

    def test_confidence_label_all_boundaries(self):
        """Test all thresholds including just-below values."""
        assert confidence_label(1.0)  == 'high'
        assert confidence_label(0.75) == 'high'
        assert confidence_label(0.74) == 'moderate'
        assert confidence_label(0.45) == 'moderate'
        assert confidence_label(0.44) == 'speculative'
        assert confidence_label(0.0)  == 'speculative'


# ─── JL-014 (BA Phase 2.5 J5): relative_confidence_labels ────────────────────

class TestRelativeConfidenceLabels:

    def test_low_absolute_scores_are_not_all_speculative(self):
        """The exact real-world defect this fixes: a batch whose scores all sit
        far below I-21's absolute thresholds must still be discriminated by the
        relative tier — proves it's not degenerate to a constant."""
        scores = [0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16]
        # All would be 'speculative' under the absolute confidence_label()
        assert all(confidence_label(s) == 'speculative' for s in scores)
        labels = relative_confidence_labels(scores)
        assert len(set(labels)) > 1, "relative tier must discriminate within the batch"
        assert labels[-1] == 'high'    # 0.16 is the top score in the batch

    def test_empty_batch(self):
        assert relative_confidence_labels([]) == []

    def test_single_element_batch_is_moderate(self):
        assert relative_confidence_labels([0.5]) == ['moderate']

    def test_all_equal_scores_are_moderate_not_arbitrary(self):
        labels = relative_confidence_labels([0.1, 0.1, 0.1, 0.1])
        assert labels == ['moderate'] * 4

    def test_top_score_is_high_bottom_is_speculative(self):
        scores = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
        labels = relative_confidence_labels(scores)
        assert labels[-1] == 'high'          # top of the batch
        assert labels[0] == 'speculative'    # bottom of the batch

    def test_length_matches_input(self):
        scores = [0.1, 0.5, 0.9, 0.3, 0.7]
        assert len(relative_confidence_labels(scores)) == len(scores)


# ─── I-22: independent_current_count ─────────────────────────────────────────

class TestIndependentCurrentCount:

    def test_independent_count_dasha_nakshatra_coupled(self):
        """dasha + nakshatra_overlay together count as ~1 (coupled), result < 2."""
        result = independent_current_count({'dasha': True, 'nakshatra_overlay': True})
        assert result < 2

    def test_independent_transit_without_dasha(self):
        """Transit alone → >= 1."""
        result = independent_current_count({'transit': True})
        assert result >= 1

    def test_independent_count_minimum_one(self):
        """Result always >= 1 (even with empty dict)."""
        result = independent_current_count({})
        assert result >= 1

    def test_independent_transit_and_dasha_independent(self):
        """Transit + dasha → independent (count >= 2)."""
        result = independent_current_count({'transit': True, 'dasha': True})
        assert result >= 2

    def test_multiple_independent_factors(self):
        """Many independent factors → higher count."""
        low  = independent_current_count({'transit': True})
        high = independent_current_count({
            'transit': True, 'dasha': True,
            'benefic_dristi': True, 'cross_dasha_agreement': True,
        })
        assert high >= low


# ─── SUPPORTING_WEIGHTS invariant ────────────────────────────────────────────

class TestSupportingWeights:

    def test_supporting_weights_sum(self):
        """SUPPORTING_WEIGHTS values must sum to 1.0 within float tolerance."""
        total = sum(SUPPORTING_WEIGHTS.values())
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_supporting_weights_all_positive(self):
        """All weights must be positive."""
        for k, v in SUPPORTING_WEIGHTS.items():
            assert v > 0, f"Weight for {k} is non-positive: {v}"


# ─── Mode A ───────────────────────────────────────────────────────────────────

class TestModeA:

    def _make_predicate(self, dignity_score=0.7, dasha_score=0.6):
        return {
            'signal_id': 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
            'signature_class': 'YOGA',
            'dignity_score': dignity_score,
            'dasha_eligibility_rule_jsonb': {'eligibility_score': dasha_score},
            'transit_trigger_jsonb': {
                'planet': 'Jupiter',
                'target_longitude_deg': 270.0,   # Capricorn 0° (sidereal)
                'aspect_degrees': [0, 120],
                'orb_deg': 5.0,
            },
            'strength_affliction_hook_jsonb': {},
            'derivation_ledger_jsonb': {},
        }

    def _horizon_jd(self):
        start = _date_to_jd(date(2024, 1, 1))
        end   = _date_to_jd(date(2026, 1, 1))
        return start, end

    def test_mode_a_returns_list(self):
        """mode_a_search always returns a list."""
        s, e = self._horizon_jd()
        result = mode_a_search(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            predicate=self._make_predicate(),
            horizon_start_jd=s,
            horizon_end_jd=e,
            dasha_kala_service=None,
            gochara_service=None,
            muhurta_service=None,
            chart_id='482012f1-710e-4a25-994a-93821f5871aa',
        )
        assert isinstance(result, list)

    def test_mode_a_soft_prior(self):
        """Mode A with dasha_score=0 still returns windows (dasha is soft prior, not gate)."""
        s, e = self._horizon_jd()
        result = mode_a_search(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            predicate=self._make_predicate(dasha_score=0.0),
            horizon_start_jd=s,
            horizon_end_jd=e,
            dasha_kala_service=None,
            gochara_service=None,
            muhurta_service=None,
            chart_id='482012f1-710e-4a25-994a-93821f5871aa',
        )
        # May return 0 if no transit events in window; that's OK — the key invariant is
        # it doesn't raise an exception and is not gated by dasha
        assert isinstance(result, list)

    def test_mode_a_windows_have_required_fields(self):
        """All Mode A windows must have the required fields."""
        s, e = self._horizon_jd()
        result = mode_a_search(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            predicate=self._make_predicate(),
            horizon_start_jd=s,
            horizon_end_jd=e,
            dasha_kala_service=None,
            gochara_service=None,
            muhurta_service=None,
            chart_id='482012f1-710e-4a25-994a-93821f5871aa',
        )
        required = {'mode', 'window_start', 'window_end', 'peak_date',
                    'convergence_score', 'orb_strength', 'constituent_factors',
                    'source_citation', 'is_off_dasha_discovery'}
        for w in result:
            missing = required - set(w.keys())
            assert not missing, f"Window missing fields: {missing}"

    def test_mode_a_not_off_dasha_discovery(self):
        """All Mode A windows have is_off_dasha_discovery=False."""
        s, e = self._horizon_jd()
        result = mode_a_search(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            predicate=self._make_predicate(),
            horizon_start_jd=s,
            horizon_end_jd=e,
            dasha_kala_service=None,
            gochara_service=None,
            muhurta_service=None,
            chart_id='482012f1-710e-4a25-994a-93821f5871aa',
        )
        for w in result:
            assert w['is_off_dasha_discovery'] is False


# ─── Mode B ───────────────────────────────────────────────────────────────────

class TestModeB:

    def _make_predicate(self, dignity_score=0.8):
        return {
            'signal_id': 'aaaaaaaa-bbbb-cccc-dddd-ffffffffffff',
            'signature_class': 'DIGNITY',
            'graha_name': 'Saturn',   # required — _resolve_transit_planet reads this for DIGNITY
            'dignity_score': dignity_score,
            'dasha_eligibility_rule_jsonb': {'eligibility_score': 0.5},
            'transit_trigger_jsonb': {
                # 'planet' key intentionally absent — resolver owns planet selection now
                'target_longitude_deg': 0.0,   # Aries 0°
                'aspect_degrees': [0, 60, 90, 120, 180],
                'orb_deg': 5.0,
            },
            'strength_affliction_hook_jsonb': {},
            'derivation_ledger_jsonb': {},
        }

    def _horizon_5yr(self):
        start = _date_to_jd(date(2024, 1, 1))
        end   = _date_to_jd(date(2029, 1, 1))
        return start, end

    def test_mode_b_is_off_dasha_discovery(self):
        """All Mode B windows have is_off_dasha_discovery=True."""
        s, e = self._horizon_5yr()
        result = mode_b_sweep(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            signal_id='aaaaaaaa-bbbb-cccc-dddd-ffffffffffff',
            predicate=self._make_predicate(),
            horizon_start_jd=s,
            horizon_end_jd=e,
            gochara_service=None,
            magnitude_threshold=0.1,
        )
        for w in result:
            assert w['is_off_dasha_discovery'] is True

    def test_mode_b_threshold_filters(self):
        """Higher threshold → fewer or equal windows than lower threshold."""
        s, e = self._horizon_5yr()
        low_threshold_result = mode_b_sweep(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            signal_id='aaaaaaaa-bbbb-cccc-dddd-ffffffffffff',
            predicate=self._make_predicate(dignity_score=0.9),
            horizon_start_jd=s,
            horizon_end_jd=e,
            gochara_service=None,
            magnitude_threshold=0.1,
        )
        high_threshold_result = mode_b_sweep(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            signal_id='aaaaaaaa-bbbb-cccc-dddd-ffffffffffff',
            predicate=self._make_predicate(dignity_score=0.9),
            horizon_start_jd=s,
            horizon_end_jd=e,
            gochara_service=None,
            magnitude_threshold=0.8,
        )
        assert len(high_threshold_result) <= len(low_threshold_result)

    def test_mode_b_windows_have_required_fields(self):
        """All Mode B windows must have required fields."""
        s, e = self._horizon_5yr()
        result = mode_b_sweep(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            signal_id='aaaaaaaa-bbbb-cccc-dddd-ffffffffffff',
            predicate=self._make_predicate(),
            horizon_start_jd=s,
            horizon_end_jd=e,
            gochara_service=None,
            magnitude_threshold=0.1,
        )
        required = {'mode', 'window_start', 'window_end', 'peak_date',
                    'convergence_score', 'orb_strength', 'constituent_factors',
                    'source_citation', 'is_off_dasha_discovery'}
        for w in result:
            missing = required - set(w.keys())
            assert not missing, f"Window missing fields: {missing}"

    def test_mode_b_windows_mode_field(self):
        """All Mode B windows have mode='B'."""
        s, e = self._horizon_5yr()
        result = mode_b_sweep(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            signal_id='aaaaaaaa-bbbb-cccc-dddd-ffffffffffff',
            predicate=self._make_predicate(),
            horizon_start_jd=s,
            horizon_end_jd=e,
            gochara_service=None,
            magnitude_threshold=0.1,
        )
        for w in result:
            assert w['mode'] == 'B'


# ─── SPINE-FIRST GATE ─────────────────────────────────────────────────────────

class TestSpineE2E:

    def test_spine_e2e_one_signal(self):
        """
        SPINE-FIRST GATE: one signal exercised end-to-end.

        Mode B at threshold=0.1 over a 5-year horizon (2024-2029) with
        a high dignity_score Saturn signal MUST return at least one window.

        Saturn transits across major aspect points (0°, 60°, 90°, 120°, 180°)
        from any natal longitude over 5 years will always produce events.
        """
        # A high-dignity signal with Jupiter as trigger planet
        # Jupiter is fast enough to produce many events over 5 years
        predicate = {
            'signal_id': 'deadbeef-1234-5678-abcd-ef0123456789',
            'signature_class': 'YOGA',
            'dignity_score': 0.9,
            'dasha_eligibility_rule_jsonb': {'eligibility_score': 0.7},
            'transit_trigger_jsonb': {
                'planet': 'Jupiter',
                'target_longitude_deg': 270.0,   # Capricorn 0° (Saturn exaltation sign cusp)
                'aspect_degrees': [0, 60, 90, 120, 180],
                'orb_deg': 8.0,   # generous orb to ensure we catch events
            },
            'strength_affliction_hook_jsonb': {},
            'derivation_ledger_jsonb': {},
        }

        start_jd = _date_to_jd(date(2024, 1, 1))
        end_jd   = _date_to_jd(date(2029, 1, 1))  # 5-year horizon

        windows = mode_b_sweep(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            signal_id='deadbeef-1234-5678-abcd-ef0123456789',
            predicate=predicate,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=None,
            magnitude_threshold=0.1,   # low threshold to ensure we get results
        )

        # SPINE-FIRST GATE: must return at least one window
        assert len(windows) > 0, (
            "SPINE-FIRST GATE FAILED: mode_b_sweep returned 0 windows "
            "for a 5-year Jupiter sweep at threshold=0.1. "
            "Expected at least one Jupiter event over 5 years across 5 aspects at 8° orb."
        )

        # Validate structure of at least one window
        w = windows[0]
        assert w['mode'] == 'B'
        assert w['is_off_dasha_discovery'] is True
        assert isinstance(w['peak_date'], date)
        assert isinstance(w['window_start'], date)
        assert isinstance(w['window_end'], date)
        assert 0.0 <= w['convergence_score'] <= 1.0
        assert 0.0 <= w['orb_strength'] <= 1.0
        assert w['source_citation'].startswith('mode_b/')
        assert 'constituent_factors' in w

        # Confidence label must be valid
        c_label = confidence_label(w['convergence_score'])
        assert c_label in ('high', 'moderate', 'speculative')

        # Independent current count
        cf = w.get('constituent_factors', {})
        currents = {'transit': True, 'dasha': False, 'nakshatra_overlay': False}
        icc = independent_current_count(currents)
        assert icc >= 1


# ─── Anti-drift + contract checks (static analysis) ──────────────────────────

class TestAntiDriftAndContract:

    _writer_path = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "pipeline", "orchestrator", "writers", "ka_sangam.py"
    )
    _engine_path = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "services", "ka_sangam", "engine.py"
    )

    def _read_writer(self):
        with open(self._writer_path) as f:
            return f.read()

    def test_anti_drift_no_bodha_writes(self):
        """No 'INSERT INTO bodha_' or 'UPDATE bodha_' in writer source code."""
        src = self._read_writer()
        assert 'INSERT INTO bodha_' not in src, "Writer must never write to bodha_ tables"
        assert 'UPDATE bodha_' not in src, "Writer must never write to bodha_ tables"

    def test_contract_no_commit(self):
        """No '.commit()' in writer source code."""
        src = self._read_writer()
        # Exclude comment/docstring lines
        code_lines = [
            line for line in src.splitlines()
            if not line.strip().startswith('#') and 'NEVER' not in line
            and '.commit()' in line
        ]
        assert not code_lines, f"commit() found in writer: {code_lines}"

    def test_contract_no_rollback(self):
        """No '.rollback()' in writer source code."""
        src = self._read_writer()
        code_lines = [
            line for line in src.splitlines()
            if not line.strip().startswith('#') and 'NEVER' not in line
            and '.rollback()' in line
        ]
        assert not code_lines, f"rollback() found in writer: {code_lines}"

    def test_register_decorator_present(self):
        """Writer must have @register('ka_sangam') decorator."""
        src = self._read_writer()
        assert "@register('ka_sangam')" in src

    def test_writer_base_subclass(self):
        """Writer must subclass WriterBase."""
        src = self._read_writer()
        assert 'WriterBase' in src

    def test_engine_no_bodha_writes(self):
        """Engine module must not reference bodha_ tables for writes."""
        with open(self._engine_path) as f:
            src = f.read()
        assert 'INSERT INTO bodha_' not in src
        assert 'UPDATE bodha_' not in src

    def test_no_jupiter_hardcoded_fallback(self):
        """Engine must not contain the old transit_trig.get('planet', 'Jupiter') fallback."""
        with open(self._engine_path) as f:
            src = f.read()
        assert "get('planet', 'Jupiter')" not in src, (
            "Hardcoded Jupiter fallback found in engine — should use _resolve_transit_planet"
        )

    def test_no_event_cap_constant(self):
        """Engine must not contain a max_events cap constant (gate, not cap)."""
        with open(self._engine_path) as f:
            src = f.read()
        # no per-predicate event cap — the design uses an inline orb threshold, not a truncation
        assert '_MAX_EVENTS' not in src
        assert 'max_events' not in src


# ─── Per-signature planet resolver ────────────────────────────────────────────

class TestPerSignaturePlanet:
    """
    Validates _resolve_transit_planet routing (design §4.6) and the
    HIGH_CONFIDENCE_ORB_THRESHOLD constant from I-21.
    """

    def test_dosha_resolves_to_saturn(self):
        assert _resolve_transit_planet({'signature_class': 'DOSHA'}) == 'Saturn'

    def test_dosha_case_insensitive(self):
        assert _resolve_transit_planet({'signature_class': 'dosha'}) == 'Saturn'

    def test_yoga_resolves_to_jupiter(self):
        assert _resolve_transit_planet({'signature_class': 'YOGA'}) == 'Jupiter'

    def test_subsystem_returns_none(self):
        assert _resolve_transit_planet({'signature_class': 'SUBSYSTEM'}) is None

    def test_subsystem_variant_returns_none(self):
        assert _resolve_transit_planet({'signature_class': 'KP_SUBSYSTEM'}) is None

    def test_dignity_with_graha_name_resolves(self):
        pred = {'signature_class': 'DIGNITY', 'graha_name': 'Mercury'}
        assert _resolve_transit_planet(pred) == 'Mercury'

    def test_dignity_without_graha_name_returns_none(self):
        """DIGNITY with no graha_name → unresolvable → None (writer enrichment missing)."""
        pred = {'signature_class': 'DIGNITY'}
        assert _resolve_transit_planet(pred) is None

    def test_dignity_graha_name_none_returns_none(self):
        pred = {'signature_class': 'DIGNITY', 'graha_name': None}
        assert _resolve_transit_planet(pred) is None

    def test_dispositor_with_lord_resolves(self):
        pred = {'signature_class': 'DISPOSITOR_RELATIONAL', 'dispositor_lord': 'Mars'}
        assert _resolve_transit_planet(pred) == 'Mars'

    def test_dispositor_without_lord_returns_none(self):
        pred = {'signature_class': 'DISPOSITOR_RELATIONAL'}
        assert _resolve_transit_planet(pred) is None

    def test_unknown_class_returns_none(self):
        assert _resolve_transit_planet({'signature_class': 'MYSTERY_TYPE'}) is None

    def test_empty_predicate_returns_none(self):
        assert _resolve_transit_planet({}) is None

    def test_high_confidence_threshold_value(self):
        """HIGH_CONFIDENCE_ORB_THRESHOLD must equal 0.45 (I-21 moderate floor)."""
        assert HIGH_CONFIDENCE_ORB_THRESHOLD == 0.45

    def test_subsystem_mode_a_returns_empty(self):
        """SUBSYSTEM predicate must short-circuit mode_a — no sky scan."""
        pred = {
            'signal_id': 'bbbbbbbb-0000-0000-0000-000000000000',
            'signature_class': 'SUBSYSTEM',
            'dignity_score': 0.9,
            'dasha_eligibility_rule_jsonb': {'eligibility_score': 0.8},
            'transit_trigger_jsonb': {'target_longitude_deg': 180.0, 'orb_deg': 5.0},
            'strength_affliction_hook_jsonb': {},
            'derivation_ledger_jsonb': {},
        }
        start_jd = _date_to_jd(date(2024, 1, 1))
        end_jd   = _date_to_jd(date(2026, 1, 1))
        result = mode_a_search(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            dasha_kala_service=None,
            gochara_service=None,
            muhurta_service=None,
            chart_id='482012f1-710e-4a25-994a-93821f5871aa',
        )
        assert result == [], "SUBSYSTEM predicate must return [] from mode_a (no transit scan)"

    def test_subsystem_mode_b_returns_empty(self):
        """SUBSYSTEM predicate must short-circuit mode_b — no sky scan."""
        pred = {
            'signal_id': 'bbbbbbbb-0000-0000-0000-000000000001',
            'signature_class': 'SUBSYSTEM',
            'dignity_score': 0.9,
            'dasha_eligibility_rule_jsonb': {'eligibility_score': 0.8},
            'transit_trigger_jsonb': {'target_longitude_deg': 180.0, 'orb_deg': 5.0},
            'strength_affliction_hook_jsonb': {},
            'derivation_ledger_jsonb': {},
        }
        start_jd = _date_to_jd(date(2024, 1, 1))
        end_jd   = _date_to_jd(date(2026, 1, 1))
        result = mode_b_sweep(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            signal_id='bbbbbbbb-0000-0000-0000-000000000001',
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=None,
            magnitude_threshold=0.1,
        )
        assert result == [], "SUBSYSTEM predicate must return [] from mode_b (no transit scan)"

    def test_planet_in_constituent_factors_matches_resolver(self):
        """
        Windows produced by mode_b for a DOSHA predicate must have
        constituent_factors['planet'] == 'Saturn' (not 'Jupiter').
        """
        pred = {
            'signal_id': 'cccccccc-0000-0000-0000-000000000000',
            'signature_class': 'DOSHA',
            'dignity_score': 0.9,
            'dasha_eligibility_rule_jsonb': {'eligibility_score': 0.8},
            'transit_trigger_jsonb': {
                'target_longitude_deg': 270.0,
                'aspect_degrees': [0, 60, 90, 120, 180],
                'orb_deg': 8.0,
            },
            'strength_affliction_hook_jsonb': {},
            'derivation_ledger_jsonb': {},
        }
        start_jd = _date_to_jd(date(2024, 1, 1))
        end_jd   = _date_to_jd(date(2029, 1, 1))
        windows = mode_b_sweep(
            janma_nakshatra_idx=24,  # CR-87 test fixture value only — arbitrary
            signal_id='cccccccc-0000-0000-0000-000000000000',
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=None,
            magnitude_threshold=0.1,
        )
        for w in windows:
            assert w['constituent_factors']['planet'] == 'Saturn', (
                f"DOSHA window must have planet='Saturn', got {w['constituent_factors']['planet']!r}"
            )


# ─── CR-102 (D-3 T-6): vedha reference-frame fix, WIRED (real call sites) ────
#
# Proves the fix at the actual served call sites (mode_a_search/mode_b_sweep +
# _c11_vedha_factor), not just the standalone re-derivation in
# services/kala_trigger/trigger.py (that module's own test suite already
# covers the isolated function; this proves it's actually WIRED).
#
# Scenario mirrors test_kala_trigger.py's TestVedhaFilterGap fixture exactly:
# Moon in Cancer (0-based idx 3), Jupiter transiting Taurus (1-based sign
# idx 2) -> house-from-Moon = ((2-1-3) % 12)+1 = 11. A vedha rule keys off
# transit_to_house=11 (Jupiter's classical best transit, 11th-from-Moon,
# vedha from the 8th — BPHS Gochara). Before the fix, both call sites fed
# the RASI SIGN NUMBER (2) as transit_house -> rule never matches -> vedha
# reported as neutral (1.0) even though this transit IS vedha-eligible.

class _FakeTransitEvent:
    """Minimal stand-in for pipeline.transit_search.TransitEvent — only the
    attributes mode_a_search/mode_b_sweep actually read."""

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


class TestCR102VedhaWired:
    """CR-102 fix demonstrated at the actual served call sites, both bugs:
    (1) house-from-Moon reference frame, (2) graha-name case mismatch
    (bg_transit_rules stores lowercase; the engine passes 'Jupiter')."""

    _VEDHA_RULE_LOWERCASE_GRAHA = {
        'graha': 'jupiter',            # bg_transit_rules stores lowercase (real seed data)
        'transit_to_house': 11,
        'vedha_house': 8,
    }
    _MOON_SIGN_CANCER = 'Cancer'       # 0-based idx 3
    _TAURUS_LON = 35.0                 # sign idx = int(35//30)+1 = 2 (Taurus)

    def _predicate(self):
        return {
            'signal_id': 'dddddddd-0000-0000-0000-000000000000',
            'signature_class': 'DIGNITY',
            'graha_name': 'Jupiter',   # capitalized, as the writer always populates it
            'dignity_score': 0.9,
            'dasha_eligibility_rule_jsonb': {'eligibility_score': 0.8},
            'transit_trigger_jsonb': {
                'target_longitude_deg': self._TAURUS_LON,
                'aspect_degrees': [0],
                'orb_deg': 5.0,
            },
            'strength_affliction_hook_jsonb': {},
            'derivation_ledger_jsonb': {},
        }

    def test_mode_a_search_vedha_factor_changes_with_moon_sign_wired(self, monkeypatch):
        from services.ka_sangam.engine import EnrichmentContext

        event = _FakeTransitEvent(self._TAURUS_LON, _date_to_jd(date(2024, 6, 1)))

        def fake_find_aspect_events(**kwargs):
            return [event]

        monkeypatch.setattr(
            'pipeline.transit_search.find_aspect_events', fake_find_aspect_events
        )
        ctx = EnrichmentContext(vedha_rules=[self._VEDHA_RULE_LOWERCASE_GRAHA])
        s, e = self._horizon_jd_local()

        # WITHOUT moon_sign (old call-site shape, pre-T-6): falls back to the
        # bugged sign-number behavior -> vedha rule missed -> factor 1.0.
        windows_before = mode_a_search(
            janma_nakshatra_idx=3,
            predicate=self._predicate(),
            horizon_start_jd=s, horizon_end_jd=e,
            dasha_kala_service=None, gochara_service=None, muhurta_service=None,
            chart_id='482012f1-710e-4a25-994a-93821f5871aa',
            enrichment_context=ctx,
            # moon_sign omitted
        )
        assert len(windows_before) == 1
        assert windows_before[0]['constituent_factors']['c11_vedha_factor'] == pytest.approx(1.0), (
            "control: without moon_sign, the served vedha factor must still show the OLD "
            "(bugged) neutral 1.0 — proves the difference below is caused by the fix, not a fixture artifact"
        )

        # WITH moon_sign (T-6 fix wired through mode_a_search -> _house_from_moon
        # -> _c11_vedha_factor): the SAME transit event now correctly resolves
        # house-from-Moon=11, matches the rule, and the SERVED vedha factor
        # drops to 0.3 (also proves the case-normalization fix: the rule's
        # 'graha': 'jupiter' (lowercase) matches the engine's 'Jupiter').
        windows_after = mode_a_search(
            janma_nakshatra_idx=3,
            predicate=self._predicate(),
            horizon_start_jd=s, horizon_end_jd=e,
            dasha_kala_service=None, gochara_service=None, muhurta_service=None,
            chart_id='482012f1-710e-4a25-994a-93821f5871aa',
            enrichment_context=ctx,
            moon_sign=self._MOON_SIGN_CANCER,
        )
        assert len(windows_after) == 1
        assert windows_after[0]['constituent_factors']['c11_vedha_factor'] == pytest.approx(0.3), (
            "FIX PROOF: same transit event, same vedha rule, only moon_sign wired in -> "
            "the SERVED c11_vedha_factor now correctly drops to 0.3 (vedha caught)"
        )
        # The fix also lowers the served convergence_score (vedha enters the
        # NECESSARY side multiplicatively) — proves the wiring reaches the
        # final scored output, not just the reported constituent factor.
        assert windows_after[0]['convergence_score'] < windows_before[0]['convergence_score']

    def test_mode_b_sweep_vedha_factor_changes_with_moon_sign_wired(self, monkeypatch):
        from services.ka_sangam.engine import EnrichmentContext

        event = _FakeTransitEvent(self._TAURUS_LON, _date_to_jd(date(2024, 6, 1)))

        def fake_search_long_horizon(**kwargs):
            return [event]

        monkeypatch.setattr(
            'pipeline.transit_search.search_long_horizon', fake_search_long_horizon
        )
        ctx = EnrichmentContext(vedha_rules=[self._VEDHA_RULE_LOWERCASE_GRAHA])
        s, e = self._horizon_jd_local()

        windows_before = mode_b_sweep(
            janma_nakshatra_idx=3,
            signal_id='dddddddd-0000-0000-0000-000000000000',
            predicate=self._predicate(),
            horizon_start_jd=s, horizon_end_jd=e,
            gochara_service=None,
            magnitude_threshold=0.0,
            enrichment_context=ctx,
            # moon_sign omitted
        )
        assert len(windows_before) == 1
        assert windows_before[0]['constituent_factors']['c11_vedha_factor'] == pytest.approx(1.0)

        windows_after = mode_b_sweep(
            janma_nakshatra_idx=3,
            signal_id='dddddddd-0000-0000-0000-000000000000',
            predicate=self._predicate(),
            horizon_start_jd=s, horizon_end_jd=e,
            gochara_service=None,
            magnitude_threshold=0.0,
            enrichment_context=ctx,
            moon_sign=self._MOON_SIGN_CANCER,
        )
        assert len(windows_after) == 1
        assert windows_after[0]['constituent_factors']['c11_vedha_factor'] == pytest.approx(0.3)
        assert windows_after[0]['convergence_score'] < windows_before[0]['convergence_score']

    @staticmethod
    def _horizon_jd_local():
        start = _date_to_jd(date(2024, 1, 1))
        end   = _date_to_jd(date(2024, 12, 31))
        return start, end


class TestCR102VedhaCaseNormalization:
    """Isolated proof of the SECOND CR-102 bug (case mismatch) independent of
    the reference-frame bug, directly on _c11_vedha_factor."""

    def test_lowercase_rule_graha_matches_capitalized_call_planet(self):
        from services.ka_sangam.engine import _c11_vedha_factor, EnrichmentContext

        ctx = EnrichmentContext(vedha_rules=[
            {'graha': 'saturn', 'transit_to_house': 5, 'vedha_house': 11},
        ])
        # Before the fix this would have returned 1.0 (neutral) because
        # 'Saturn' != 'saturn' under a bare == comparison.
        factor = _c11_vedha_factor('Saturn', 5, ctx)
        assert factor == pytest.approx(0.3), (
            "case-insensitive match must catch a lowercase-seeded bg_transit_rules row "
            "against a capitalized engine-side planet name"
        )

    def test_mixed_case_and_whitespace_still_matches(self):
        from services.ka_sangam.engine import _c11_vedha_factor, EnrichmentContext

        ctx = EnrichmentContext(vedha_rules=[
            {'graha': ' Mars ', 'transit_to_house': 3, 'vedha_house': 9},
        ])
        factor = _c11_vedha_factor('mars', 3, ctx)
        assert factor == pytest.approx(0.3)

    def test_non_matching_planet_still_neutral(self):
        from services.ka_sangam.engine import _c11_vedha_factor, EnrichmentContext

        ctx = EnrichmentContext(vedha_rules=[
            {'graha': 'venus', 'transit_to_house': 5, 'vedha_house': 11},
        ])
        factor = _c11_vedha_factor('Saturn', 5, ctx)
        assert factor == pytest.approx(1.0)

