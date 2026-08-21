"""
test_ph_wave4.py — Wave 4 parallel assets: ph_muhurta, ph_pratikara, ph_sankrama.

Covers:
  ph_muhurta:
    - compute_composite_quality: formula + clamping
    - classify_verdict: strong/adequate/mediocre/none_genuine thresholds (M4)
    - ACTION_GRAHA_MAP: domain coverage
    - derive_muhurta_record: all M1-M4 fields populated
    - Anti-drift: no panchanga math inside ph_muhurta engine

  ph_pratikara:
    - topo_sort_prescriptions: prerequisite ordering
    - exclude_incompatibles: conflict-exclusion
    - tier_prescriptions: P1 cost-tiering
    - cross_tradition_count: P5
    - derive_intensity_tier: severity × magnitude mapping
    - derive_mitigation_record: program ordered, outcome_hook present
    - Anti-drift: remedies consumed not authored

  ph_sankrama:
    - derive_projected_window: SK1 from activation windows (NOT a formula)
    - classify_relationship: SK3 conflict vs contagion
    - compute_spillover_confidence: source × linkage, cap 0.80
    - generate_spillover_falsifier: REFUTED/CONFIRMED present
    - derive_spillover: SK1-SK4 populated, cascade bounded
    - Anti-drift: no hardcoded lag arithmetic
"""
from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# PH_MUHURTA
# ══════════════════════════════════════════════════════════════════════════════

class TestMuhurtaComposite:
    def test_formula(self):
        from services.ph_muhurta.engine import compute_composite_quality
        # BA-P5B added tarabala/chandrabala; pass 1.0 to isolate panchanga formula
        q = compute_composite_quality(0.8, 0.9, 0.1, tarabala_score=1.0, chandrabala_score=1.0)
        assert abs(q - 0.8 * 0.9 * 0.9) < 1e-4

    def test_clamps_to_unit(self):
        from services.ph_muhurta.engine import compute_composite_quality
        assert compute_composite_quality(2.0, 1.0, 0.0) == pytest.approx(1.0)
        assert compute_composite_quality(0.5, 0.0, 0.0) == pytest.approx(0.0)

    def test_adversity_penalty_reduces_quality(self):
        from services.ph_muhurta.engine import compute_composite_quality
        high = compute_composite_quality(0.8, 0.9, 0.0)
        penalized = compute_composite_quality(0.8, 0.9, 0.3)
        assert penalized < high


class TestMuhurtaVerdict:
    @pytest.mark.parametrize("q,expected", [
        (0.80, 'strong'),
        (0.65, 'adequate'),
        (0.30, 'mediocre'),
        (0.00, 'none_genuine'),
    ])
    def test_verdict_thresholds(self, q, expected):
        from services.ph_muhurta.engine import classify_verdict
        verdict, _ = classify_verdict(q)
        assert verdict == expected

    def test_mediocre_has_reason(self):
        from services.ph_muhurta.engine import classify_verdict
        _, reason = classify_verdict(0.30)
        assert reason is not None and len(reason) > 10

    def test_none_genuine_has_reason(self):
        from services.ph_muhurta.engine import classify_verdict
        _, reason = classify_verdict(0.0)
        assert reason is not None

    def test_strong_reason_is_none(self):
        from services.ph_muhurta.engine import classify_verdict
        _, reason = classify_verdict(0.80)
        assert reason is None


class TestActionGrahaMap:
    def test_career_maps_to_saturn(self):
        from services.ph_muhurta.engine import ACTION_GRAHA_MAP
        assert ACTION_GRAHA_MAP['start_business'] == 'saturn'

    def test_marriage_maps_to_venus(self):
        from services.ph_muhurta.engine import ACTION_GRAHA_MAP
        assert ACTION_GRAHA_MAP['marriage'] == 'venus'

    def test_medical_maps_to_moon(self):
        from services.ph_muhurta.engine import ACTION_GRAHA_MAP
        assert ACTION_GRAHA_MAP['medical'] == 'moon'

    def test_all_values_are_valid_grahas(self):
        from services.ph_muhurta.engine import ACTION_GRAHA_MAP
        valid = {'sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu'}
        for ac, graha in ACTION_GRAHA_MAP.items():
            assert graha in valid, f"{ac} → {graha} not a valid graha"


class TestDeriveMuhurtaRecord:
    def _ctx(self, **kwargs):
        from services.ph_muhurta.engine import MuhurtaContext
        defaults = dict(
            action_class='start_business',
            window_start=datetime(2026, 9, 1, 6, 0),
            window_end=datetime(2026, 9, 30, 18, 0),
            hora_lord='saturn',
            panchanga_score=0.72,
            condition_score=0.8,
            transit_score=0.6,
            overlapping_obstruction_id=None,
            obstruction_penalty=0.0,
            linked_anchor_id='anchor-001',
        )
        defaults.update(kwargs)
        return MuhurtaContext(**defaults)

    def test_all_fields_populated(self):
        from services.ph_muhurta.engine import derive_muhurta_record
        rec = derive_muhurta_record(self._ctx())
        assert rec.composite_quality is not None
        assert rec.window_quality_verdict is not None
        assert rec.chart_personalization_score is not None
        assert rec.personalization_graha == 'saturn'
        assert rec.derivation_ledger_jsonb

    def test_m3_linked_anchor_id_preserved(self):
        from services.ph_muhurta.engine import derive_muhurta_record
        rec = derive_muhurta_record(self._ctx(linked_anchor_id='anchor-xyz'))
        assert rec.linked_anchor_id == 'anchor-xyz'

    def test_m2_obstruction_penalty_applied(self):
        from services.ph_muhurta.engine import derive_muhurta_record
        rec_clean = derive_muhurta_record(self._ctx(obstruction_penalty=0.0))
        rec_penalized = derive_muhurta_record(self._ctx(obstruction_penalty=0.4, overlapping_obstruction_id=99))
        assert rec_penalized.composite_quality < rec_clean.composite_quality


class TestMuhurtaAntiDrift:
    def test_engine_has_no_panchanga_math(self):
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'services', 'ph_muhurta', 'engine.py'
        )
        with open(path) as f:
            src = f.read()
        # Engine must not reimplement tithi/nakshatra/vara calculations
        for bad in ('tithi', 'nakshatra_lord', 'vara_score', 'karana_score', 'panchaka'):
            assert bad not in src, f"ph_muhurta engine must not contain '{bad}' (belongs in ka_muhurta_seva)"


# ══════════════════════════════════════════════════════════════════════════════
# PH_PRATIKARA
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def prescriptions():
    from services.ph_pratikara.engine import RemedyPrescription
    return [
        RemedyPrescription(
            prescription_id='P1', tradition='vedic', remedy_category='mantra',
            classical_strength_rating=0.8, resonance_match_score=0.9, feasibility_score=0.85,
            estimated_cost_inr_range={'min_inr': 0, 'max_inr': 0},
            estimated_time_minutes=10, requires_acharya_review=False,
            prerequisite_ids=[], incompatible_ids=['P3'],
            classical_citation='BPHS Upaya ch. 85',
        ),
        RemedyPrescription(
            prescription_id='P2', tradition='ayurvedic', remedy_category='dravya',
            classical_strength_rating=0.7, resonance_match_score=0.75, feasibility_score=0.70,
            estimated_cost_inr_range={'min_inr': 500, 'max_inr': 2000},
            estimated_time_minutes=30, requires_acharya_review=False,
            prerequisite_ids=['P1'], incompatible_ids=[],
            classical_citation='Ashtanga Hridayam §22',
        ),
        RemedyPrescription(
            prescription_id='P3', tradition='tantra', remedy_category='gemstone',
            classical_strength_rating=0.9, resonance_match_score=0.6, feasibility_score=0.4,
            estimated_cost_inr_range={'min_inr': 20000, 'max_inr': 80000},
            estimated_time_minutes=None, requires_acharya_review=True,
            prerequisite_ids=[], incompatible_ids=['P1'],
            classical_citation='Ratna Pariksha §3',
        ),
    ]


class TestTopoSort:
    def test_prerequisite_comes_first(self, prescriptions):
        from services.ph_pratikara.engine import topo_sort_prescriptions
        order = topo_sort_prescriptions(prescriptions)
        # P1 must come before P2 (P2 requires P1)
        assert order.index('P1') < order.index('P2')

    def test_all_prescriptions_included(self, prescriptions):
        from services.ph_pratikara.engine import topo_sort_prescriptions
        order = topo_sort_prescriptions(prescriptions)
        assert set(order) == {'P1', 'P2', 'P3'}


class TestExcludeIncompatibles:
    def test_incompatible_pair_excluded(self, prescriptions):
        from services.ph_pratikara.engine import topo_sort_prescriptions, exclude_incompatibles
        sorted_ids = topo_sort_prescriptions(prescriptions)
        scheduled  = exclude_incompatibles(prescriptions, sorted_ids)
        # P1 and P3 are incompatible; both should NOT appear
        assert not ('P1' in scheduled and 'P3' in scheduled)

    def test_no_incompatible_pairs_in_output(self, prescriptions):
        from services.ph_pratikara.engine import topo_sort_prescriptions, exclude_incompatibles
        sorted_ids = topo_sort_prescriptions(prescriptions)
        scheduled  = exclude_incompatibles(prescriptions, sorted_ids)
        p_map = {p.prescription_id: p for p in prescriptions}
        scheduled_set = set(scheduled)
        for pid in scheduled:
            p = p_map[pid]
            for bad in p.incompatible_ids:
                assert bad not in scheduled_set, \
                    f"{pid} and {bad} are incompatible but both scheduled"


class TestTierPrescriptions:
    def test_free_tier_has_zero_cost(self, prescriptions):
        from services.ph_pratikara.engine import topo_sort_prescriptions, exclude_incompatibles, tier_prescriptions
        sorted_ids = topo_sort_prescriptions(prescriptions)
        scheduled  = exclude_incompatibles(prescriptions, sorted_ids)
        tiers = tier_prescriptions(prescriptions, scheduled)
        for entry in tiers['free']:
            cost = entry.get('cost_range_inr', {})
            assert cost.get('max_inr', 0) == 0

    def test_all_tiers_present_as_keys(self, prescriptions):
        from services.ph_pratikara.engine import topo_sort_prescriptions, exclude_incompatibles, tier_prescriptions
        sorted_ids = topo_sort_prescriptions(prescriptions)
        scheduled  = exclude_incompatibles(prescriptions, sorted_ids)
        tiers = tier_prescriptions(prescriptions, scheduled)
        assert set(tiers.keys()) == {'free', 'low_cost', 'high_investment'}


class TestCrossTraditional:
    def test_counts_distinct_traditions(self, prescriptions):
        from services.ph_pratikara.engine import cross_tradition_count
        all_ids = [p.prescription_id for p in prescriptions]
        ctc = cross_tradition_count(prescriptions, all_ids)
        assert ctc >= 2   # vedic, ayurvedic, tantra — all in the known-traditions list


class TestIntensityTier:
    @pytest.mark.parametrize("sev,mag,expected", [
        ('low',  'minor',   'light'),
        ('high', 'pivotal', 'intensive'),
        ('medium','moderate','moderate'),
    ])
    def test_severity_magnitude_mapping(self, sev, mag, expected):
        from services.ph_pratikara.engine import derive_intensity_tier
        tier, basis = derive_intensity_tier(sev, mag)
        assert tier == expected
        assert sev in basis and mag in basis


class TestDeriveMitigationRecord:
    def test_outcome_hook_present(self, prescriptions):
        from services.ph_pratikara.engine import MitigationContext, derive_mitigation_record
        ctx = MitigationContext(
            obstruction_id=42,
            obstruction_severity='medium',
            obstruction_window_start=date(2026, 9, 1),
            obstruction_window_end=date(2026, 12, 31),
            afflicting_graha='saturn',
            linked_anchor_id='anchor-001',
            anchor_magnitude='major',
            prescriptions=prescriptions,
        )
        rec = derive_mitigation_record(ctx)
        assert 'question' in rec.outcome_hook_jsonb
        assert rec.re_evaluation_date == date(2026, 12, 31)

    def test_program_ordered(self, prescriptions):
        from services.ph_pratikara.engine import MitigationContext, derive_mitigation_record
        ctx = MitigationContext(
            obstruction_id=1, obstruction_severity='high',
            obstruction_window_start=None, obstruction_window_end=None,
            afflicting_graha='rahu', linked_anchor_id=None,
            anchor_magnitude='pivotal', prescriptions=prescriptions,
        )
        rec = derive_mitigation_record(ctx)
        assert 'scheduled_ids' in rec.program_jsonb
        assert 'sequence_basis' in rec.program_jsonb

    def test_anti_drift_no_authored_remedy_text(self, prescriptions):
        """P-discipline: engine builds program structure, never authors remedy narratives."""
        from services.ph_pratikara.engine import MitigationContext, derive_mitigation_record
        ctx = MitigationContext(
            obstruction_id=1, obstruction_severity='low',
            obstruction_window_start=None, obstruction_window_end=None,
            afflicting_graha='mars', linked_anchor_id=None,
            anchor_magnitude='minor', prescriptions=prescriptions,
        )
        rec = derive_mitigation_record(ctx)
        # program_jsonb should reference prescription_ids, not invent text
        scheduled = rec.program_jsonb.get('scheduled_ids', [])
        for pid in scheduled:
            assert isinstance(pid, str)


# ══════════════════════════════════════════════════════════════════════════════
# PH_SANKRAMA
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def cdlm_cell():
    from services.ph_sankrama.engine import CdlmCell
    return CdlmCell(
        cell_id='cell-001',
        domain_row='career',
        domain_col='health',
        net_linkage_strength=0.55,
        asymmetry_score=0.1,
        contradicting_pairs_count=0,
        cgm_bridge_edge_seeds=[{'mediating_planet': 'saturn', 'house': 10}],
        predicted_activation_windows=[{
            'window_start': '2026-08-01',
            'window_end':   '2026-11-30',
            'peak_date':    '2026-09-15',
        }],
        evolution_gradient_score=0.2,   # strengthening
    )


@pytest.fixture
def conflict_cell():
    from services.ph_sankrama.engine import CdlmCell
    return CdlmCell(
        cell_id='cell-002',
        domain_row='career',
        domain_col='relationship',
        net_linkage_strength=0.40,
        asymmetry_score=0.3,
        contradicting_pairs_count=3,    # SK3: conflict
        cgm_bridge_edge_seeds=[],
        predicted_activation_windows=[],
        evolution_gradient_score=-0.15,  # weakening
    )


class TestProjectedWindow:
    def test_derived_from_activation_windows_not_formula(self):
        from services.ph_sankrama.engine import derive_projected_window
        source_start = date(2026, 7, 1)
        source_end   = date(2026, 12, 31)
        act_windows  = [{'window_start': '2026-09-01', 'window_end': '2026-10-31', 'peak_date': '2026-09-20'}]
        ws, we, wp = derive_projected_window(source_start, source_end, act_windows)
        # derived window must be intersection (not 90-day formula)
        assert ws == date(2026, 9, 1)
        assert we == date(2026, 10, 31)

    def test_empty_activation_windows_fallback_to_source(self):
        from services.ph_sankrama.engine import derive_projected_window
        s = date(2026, 6, 1)
        e = date(2026, 9, 30)
        ws, we, wp = derive_projected_window(s, e, [])
        assert ws == s and we == e

    def test_activation_window_outside_source_excluded(self):
        """SK1: activation window outside source anchor window → use source window."""
        from services.ph_sankrama.engine import derive_projected_window
        source_start = date(2026, 1, 1)
        source_end   = date(2026, 3, 31)
        act_windows  = [{'window_start': '2027-01-01', 'window_end': '2027-06-30', 'peak_date': '2027-03-01'}]
        ws, we, wp = derive_projected_window(source_start, source_end, act_windows)
        # intersection is empty (activation is after source) → fallback
        assert ws == source_start


class TestClassifyRelationship:
    def test_conflict_when_contradicting_pairs(self):
        from services.ph_sankrama.engine import classify_relationship
        assert classify_relationship(3) == 'conflict'

    def test_contagion_when_no_contradiction(self):
        from services.ph_sankrama.engine import classify_relationship
        assert classify_relationship(0) == 'contagion'


class TestSpilloverConfidence:
    def test_product_formula(self):
        from services.ph_sankrama.engine import compute_spillover_confidence
        result = compute_spillover_confidence(0.70, 0.55)
        assert result == pytest.approx(0.70 * 0.55, rel=0.01)

    def test_capped_at_0_80(self):
        from services.ph_sankrama.engine import compute_spillover_confidence
        assert compute_spillover_confidence(1.0, 1.0) <= 0.80

    def test_zero_linkage_zero_confidence(self):
        from services.ph_sankrama.engine import compute_spillover_confidence
        assert compute_spillover_confidence(0.9, 0.0) == pytest.approx(0.0)


class TestSpilloverFalsifier:
    def test_refuted_confirmed_present(self):
        from services.ph_sankrama.engine import generate_spillover_falsifier
        f = generate_spillover_falsifier('career', 'health', 'contagion', date(2027, 3, 31))
        assert 'REFUTED' in f and 'CONFIRMED' in f

    def test_source_and_target_domains_in_text(self):
        from services.ph_sankrama.engine import generate_spillover_falsifier
        f = generate_spillover_falsifier('career', 'health', 'conflict', None)
        assert 'career' in f.lower() and 'health' in f.lower()


class TestDeriveSpillover:
    def test_contagion_record_from_clean_cell(self, cdlm_cell):
        from services.ph_sankrama.engine import SankramaContext, derive_spillover
        ctx = SankramaContext(
            source_anchor_id='anchor-001',
            source_domain='career',
            source_window_start=date(2026, 7, 1),
            source_window_end=date(2026, 12, 31),
            source_confidence=0.70,
            cdlm_cells=[cdlm_cell],
            all_cells_by_domain_pair={},
        )
        records = derive_spillover(ctx)
        assert len(records) == 1
        r = records[0]
        assert r.relationship_type == 'contagion'
        assert r.trajectory == 'strengthening'
        assert r.target_domain == 'health'
        assert r.spillover_confidence <= 0.80
        assert 'REFUTED' in r.falsifier

    def test_conflict_record_from_conflict_cell(self, conflict_cell):
        from services.ph_sankrama.engine import SankramaContext, derive_spillover
        ctx = SankramaContext(
            source_anchor_id='anchor-002',
            source_domain='career',
            source_window_start=date(2026, 8, 1),
            source_window_end=date(2027, 1, 31),
            source_confidence=0.60,
            cdlm_cells=[conflict_cell],
            all_cells_by_domain_pair={},
        )
        records = derive_spillover(ctx)
        assert len(records) == 1
        assert records[0].relationship_type == 'conflict'
        assert records[0].trajectory == 'weakening'

    def test_cascade_depth_bounded(self, cdlm_cell):
        from services.ph_sankrama.engine import SankramaContext, CdlmCell, derive_spillover
        # Create a long chain: career→health→relationship→financial
        extra = CdlmCell(
            cell_id='cell-003', domain_row='health', domain_col='relationship',
            net_linkage_strength=0.40, asymmetry_score=0.0,
            contradicting_pairs_count=0, cgm_bridge_edge_seeds=[],
            predicted_activation_windows=[], evolution_gradient_score=0.0,
        )
        ctx = SankramaContext(
            source_anchor_id='anchor-003',
            source_domain='career',
            source_window_start=date(2026, 6, 1),
            source_window_end=date(2027, 6, 30),
            source_confidence=0.65,
            cdlm_cells=[cdlm_cell],
            all_cells_by_domain_pair={('health', 'relationship'): [extra]},
        )
        records = derive_spillover(ctx)
        for r in records:
            if r.cascade_chain_jsonb:
                assert r.cascade_depth <= 3

    def test_below_threshold_cell_excluded(self):
        from services.ph_sankrama.engine import SankramaContext, CdlmCell, derive_spillover
        weak_cell = CdlmCell(
            cell_id='cell-weak', domain_row='career', domain_col='health',
            net_linkage_strength=0.10,  # below 0.25 threshold
            asymmetry_score=0.0, contradicting_pairs_count=0,
            cgm_bridge_edge_seeds=[], predicted_activation_windows=[],
            evolution_gradient_score=0.0,
        )
        ctx = SankramaContext(
            source_anchor_id='a', source_domain='career',
            source_window_start=None, source_window_end=None,
            source_confidence=0.6, cdlm_cells=[weak_cell],
        )
        records = derive_spillover(ctx)
        assert records == []

    def test_sk1_no_lag_formula(self):
        """SK1 guard: engine must not contain hardcoded lag_days arithmetic."""
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'services', 'ph_sankrama', 'engine.py'
        )
        with open(path) as f:
            src = f.read()
        assert 'lag_days' not in src, "SK1: lag must be derived from activation windows, not a formula"
        assert '90' not in src or 'MAX_CASCADE' in src, \
            "SK1: no hardcoded 90-day lag (D44 RETIRES the D23 formula)"


# ══════════════════════════════════════════════════════════════════════════════
# PH_PRATIKARA WRITER — schema contract guard (regression for the ka_vighnakara bug)
# ══════════════════════════════════════════════════════════════════════════════

class TestPratikaraWriterSchemaGuard:
    """
    Guard tests that would have caught the ka_vighnakara silent-fail bug.

    Root cause: writer queried non-existent ka_vighnakara; SAVEPOINT/ROLLBACK
    swallowed the UndefinedTable exception; returned []; inserted 0 rows silently.
    The fix: query kala_obstruction JOIN kala_convergence; fail loud on errors.

    These tests verify:
      1. The writer source does NOT reference ka_vighnakara (anti-drift source guard).
      2. The writer sources kala_obstruction with the real column names.
      3. The writer produces > 0 rows when given non-empty kala_obstruction data.
    """

    def _writer_source(self) -> str:
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator', 'writers', 'ph_pratikara.py'
        )
        with open(path) as f:
            return f.read()

    def test_no_ka_vighnakara_reference(self):
        """Writer must not reference the non-existent ka_vighnakara table."""
        src = self._writer_source()
        assert 'ka_vighnakara' not in src, (
            "ph_pratikara writer still references ka_vighnakara — this table does not exist; "
            "the correct table is kala_obstruction"
        )

    def test_queries_kala_obstruction(self):
        """Writer must query kala_obstruction (the real L3 table)."""
        src = self._writer_source()
        assert 'kala_obstruction' in src, (
            "ph_pratikara writer must query kala_obstruction"
        )

    def test_joins_kala_convergence_for_window(self):
        """Writer must join kala_convergence to bridge window_start/window_end."""
        src = self._writer_source()
        assert 'kala_convergence' in src, (
            "ph_pratikara writer must join kala_convergence to bridge window dates and graha"
        )

    def test_no_silent_savepoint_swallow(self):
        """Writer must not use SAVEPOINT to silently swallow table-not-found errors."""
        src = self._writer_source()
        assert 'sp_pratikara_obs' not in src, (
            "ph_pratikara writer must not silently swallow kala_obstruction query errors via SAVEPOINT"
        )

    def test_writer_produces_rows_from_obstruction_data(self):
        """
        With 3 mock kala_obstruction rows (bridged via convergence), the writer must
        produce > 0 phala_mitigation rows. This would have caught the 0-row silent bug.
        """
        import uuid
        from datetime import date
        from unittest.mock import MagicMock, patch, call
        import psycopg

        chart_id = '482012f1-710e-4a25-994a-93821f5871aa'

        # Mock obstruction rows as returned by the bridged JOIN query
        mock_obstruction_rows = [
            {
                'id': 1, 'convergence_id': 125, 'obstruction_type': 'panchanga_obstruction',
                'severity': 'mild', 'severity_score': 0.25, 'override_score': 0.0,
                'obstruction_detail': {'panchanga_element': 'rikta_tithi_proxy'},
                'window_start': date(2027, 1, 9), 'window_end': date(2027, 2, 8),
                'afflicting_graha': 'Jupiter',
            },
            {
                'id': 2, 'convergence_id': 124, 'obstruction_type': 'panchanga_obstruction',
                'severity': 'moderate', 'severity_score': 0.50, 'override_score': 0.1,
                'obstruction_detail': {'panchanga_element': 'rikta_tithi_proxy'},
                'window_start': date(2029, 8, 9), 'window_end': date(2029, 9, 8),
                'afflicting_graha': 'Jupiter',
            },
            {
                'id': 3, 'convergence_id': 123, 'obstruction_type': 'panchanga_obstruction',
                'severity': 'severe', 'severity_score': 0.75, 'override_score': 0.2,
                'obstruction_detail': {'panchanga_element': 'rikta_tithi_proxy'},
                'window_start': date(2029, 3, 14), 'window_end': date(2029, 4, 13),
                'afflicting_graha': None,  # null graha → must not drop the row
            },
        ]

        # Mock influenceable anchors
        mock_anchor_rows = [
            {'anchor_id': uuid.uuid4(), 'domain': 'career', 'magnitude': 'major', 'malleability': 'influenceable'},
        ]

        # Build the writer and mock its sub-methods
        from pipeline.orchestrator.writers.ph_pratikara import PhPratikaraWriter
        writer = PhPratikaraWriter()

        with (
            patch.object(writer, '_load_obstructions', return_value=mock_obstruction_rows),
            patch.object(writer, '_load_influenceable_anchors', return_value={'career': mock_anchor_rows}),
            patch.object(writer, '_load_prescriptions', return_value={}),
        ):
            conn = MagicMock()
            cur = MagicMock()
            cur.__enter__ = MagicMock(return_value=cur)
            cur.__exit__ = MagicMock(return_value=False)
            conn.cursor.return_value = cur

            ctx = MagicMock()
            ctx.db_conn = conn
            ctx.config = {'chart_id': chart_id}

            result = writer.run(ctx)

        # All 3 obstruction rows (including null-graha one) must produce a row
        assert result.rows_inserted == 3, (
            f"Expected 3 rows from 3 obstructions (including null-graha), got {result.rows_inserted}"
        )

    def test_null_graha_obstruction_does_not_drop_row(self):
        """
        When afflicting_graha is None (no planet in constituent_factors),
        the writer must still produce a row using obstruction_type as fallback key.
        """
        import uuid
        from datetime import date
        from unittest.mock import MagicMock, patch

        chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
        null_graha_row = [{
            'id': 99, 'convergence_id': None, 'obstruction_type': 'combustion',
            'severity': 'severe', 'severity_score': 0.9, 'override_score': 0.3,
            'obstruction_detail': {}, 'window_start': None, 'window_end': None,
            'afflicting_graha': None,
        }]

        from pipeline.orchestrator.writers.ph_pratikara import PhPratikaraWriter
        writer = PhPratikaraWriter()

        with (
            patch.object(writer, '_load_obstructions', return_value=null_graha_row),
            patch.object(writer, '_load_influenceable_anchors', return_value={}),
            patch.object(writer, '_load_prescriptions', return_value={}),
        ):
            conn = MagicMock()
            cur = MagicMock()
            cur.__enter__ = MagicMock(return_value=cur)
            cur.__exit__ = MagicMock(return_value=False)
            conn.cursor.return_value = cur

            ctx = MagicMock()
            ctx.db_conn = conn
            ctx.config = {'chart_id': chart_id}

            result = writer.run(ctx)

        assert result.rows_inserted == 1, (
            f"Null-graha obstruction must still produce a row; got {result.rows_inserted}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# PH_PRATIKARA WRITER — F-173 regression (bodha_rm_remedy_prescriptions schema)
# ══════════════════════════════════════════════════════════════════════════════

class _F173FakeCursor:
    """Minimal cursor stand-in: records the executed SQL, returns canned rows."""

    def __init__(self, rows, capture):
        self._rows = rows
        self._capture = capture

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._capture['sql'] = sql
        self._capture['params'] = params

    def fetchall(self):
        return self._rows


class _F173FakeConn:
    """Minimal conn stand-in for conn.cursor(row_factory=...) — ignores row_factory."""

    def __init__(self, rows):
        self._rows = rows
        self.captured = {}

    def cursor(self, row_factory=None):
        return _F173FakeCursor(self._rows, self.captured)


class TestPratikaraPrescriptionsSchemaGuard:
    """
    Guard tests for F-173: _load_prescriptions SELECTed six nonexistent columns
    on bodha_rm_remedy_prescriptions (graha, requires_acharya_review,
    recommended_hora, recommended_choghadiya, pranapratishtha,
    classical_citation_text), and the SAVEPOINT/except swallow turned the
    resulting UndefinedColumn into a silent empty dict — 536/536 charts got
    empty phala_mitigation remedy payloads. Fixing the names alone would then
    hit a live ValueError, because classical_strength_rating is TEXT and the
    old code did a bare float() on it.

    These tests verify (mirroring TestPratikaraWriterSchemaGuard's pattern for
    the sibling kala_obstruction bug):
      1. Source-level: real column names are used, no bare 'graha', no SAVEPOINT.
      2. Behavioural: _load_prescriptions actually executes against a fake
         cursor and correctly builds RemedyPrescription objects — including
         safely coercing TEXT classical_strength_rating values that are
         numeric-string, empty-string, and outright garbage, none of which
         may raise.
    """

    def _writer_source(self) -> str:
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator', 'writers', 'ph_pratikara.py'
        )
        with open(path) as f:
            return f.read()

    # ── source-level guards ──────────────────────────────────────────────

    def test_no_silent_savepoint_swallow_prescriptions(self):
        """Writer must not use SAVEPOINT to silently swallow prescriptions query errors."""
        src = self._writer_source()
        assert 'sp_pratikara_presc' not in src, (
            "ph_pratikara writer must not silently swallow bodha_rm_remedy_prescriptions "
            "query errors via SAVEPOINT"
        )

    def test_prescriptions_query_uses_real_columns(self):
        """SELECT must use the real bodha_rm_remedy_prescriptions column names."""
        src = self._writer_source()
        for real_col in (
            'target_graha',
            'requires_acharya_review_flag',
            'recommended_hora_lord_array',
            'recommended_choghadiya_window_array',
            'pranapratishtha_required_flag',
            'classical_sources_jsonb',
        ):
            assert real_col in src, f"ph_pratikara must select {real_col} from bodha_rm_remedy_prescriptions"
        assert 'classical_citation_text' not in src, (
            "classical_citation_text does not exist on bodha_rm_remedy_prescriptions"
        )

    def test_prescriptions_select_has_no_bare_graha_column(self):
        """The SELECT must name target_graha, never a bare 'graha' (that's on the sibling resonances table)."""
        import re
        src = self._writer_source()
        m = re.search(r'SELECT prescription_id.*?FROM bodha_rm_remedy_prescriptions', src, re.DOTALL)
        assert m, "could not locate the bodha_rm_remedy_prescriptions SELECT in ph_pratikara.py"
        select_clause = m.group(0)
        bare_graha = re.search(r'(?<!target_)\bgraha\b', select_clause)
        assert bare_graha is None, (
            f"prescriptions SELECT names a bare 'graha' column (in: {select_clause!r}); "
            "the real column on bodha_rm_remedy_prescriptions is target_graha — graha lives "
            "only on the sibling table bodha_rm_resonances"
        )

    # ── behavioural: real execution against a fake cursor ──────────────────

    def test_load_prescriptions_builds_rows_and_coerces_text_strength_rating(self):
        """
        Real _load_prescriptions() call (no method patching) against rows shaped
        exactly like bo_upaya's real inserts. Covers: normal numeric-string
        classical_strength_rating, an empty-string one (bo_upaya's own
        str(confidence) or '' convention), and outright garbage — none may raise,
        and the coerced value must fall back to the documented 0.5 default.
        Also covers target_graha grouping/lower-casing, None → 'generic', the
        array-typed hora/choghadiya columns, and the classical_sources_jsonb →
        classical_citation extraction (bo_upaya's real {"source_id","citation"} shape).
        """
        from pipeline.orchestrator.writers.ph_pratikara import PhPratikaraWriter

        rows = [
            {
                'prescription_id': 'p1', 'tradition': 'vedic', 'sub_tradition': None,
                'remedy_category': 'mantra',
                'classical_strength_rating': '0.85',  # normal numeric TEXT
                'resonance_match_score': 0.7, 'feasibility_score': 0.9,
                'estimated_cost_inr_range_jsonb': {'max_inr': 0},
                'requires_acharya_review_flag': False,
                'prerequisite_prescription_ids_array': [],
                'incompatible_with_prescription_ids_array': [],
                'recommended_hora_lord_array': ['jupiter', 'mercury'],
                'recommended_choghadiya_window_array': ['amrit'],
                'pranapratishtha_required_flag': True,
                'classical_sources_jsonb': {'source_id': 'BPHS', 'citation': 'BPHS 45.12'},
                'target_graha': 'Jupiter',
            },
            {
                'prescription_id': 'p2', 'tradition': 'vedic', 'sub_tradition': None,
                'remedy_category': 'dana',
                'classical_strength_rating': '',  # bo_upaya's str(confidence) or '' — blank TEXT
                'resonance_match_score': 0.5, 'feasibility_score': 0.5,
                'estimated_cost_inr_range_jsonb': None,
                'requires_acharya_review_flag': True,
                'prerequisite_prescription_ids_array': None,
                'incompatible_with_prescription_ids_array': None,
                'recommended_hora_lord_array': None,
                'recommended_choghadiya_window_array': None,
                'pranapratishtha_required_flag': None,
                'classical_sources_jsonb': None,
                'target_graha': None,  # → 'generic' bucket
            },
            {
                'prescription_id': 'p3', 'tradition': 'kp', 'sub_tradition': None,
                'remedy_category': 'gem',
                'classical_strength_rating': 'not-a-number',  # garbage TEXT — must not raise
                'resonance_match_score': None, 'feasibility_score': None,
                'estimated_cost_inr_range_jsonb': {},
                'requires_acharya_review_flag': False,
                'prerequisite_prescription_ids_array': [],
                'incompatible_with_prescription_ids_array': [],
                'recommended_hora_lord_array': [],
                'recommended_choghadiya_window_array': [],
                'pranapratishtha_required_flag': False,
                'classical_sources_jsonb': {},
                'target_graha': 'Saturn',
            },
        ]
        conn = _F173FakeConn(rows)
        writer = PhPratikaraWriter()

        result = writer._load_prescriptions(conn, '482012f1-710e-4a25-994a-93821f5871aa')

        # Executed SQL used the real columns (belt-and-braces on top of the source guards above).
        assert 'target_graha' in conn.captured['sql']
        assert 'classical_citation_text' not in conn.captured['sql']

        assert set(result.keys()) == {'jupiter', 'generic', 'saturn'}

        p1 = result['jupiter'][0]
        assert p1.classical_strength_rating == 0.85
        assert p1.classical_citation == 'BPHS 45.12'
        assert p1.recommended_hora == 'jupiter'
        assert p1.recommended_choghadiya == 'amrit'
        assert p1.pranapratishtha is True
        assert p1.requires_acharya_review is False

        p2 = result['generic'][0]
        assert p2.classical_strength_rating == 0.5, "blank TEXT rating must fall back to the 0.5 default"
        assert p2.classical_citation == ''
        assert p2.recommended_hora is None
        assert p2.recommended_choghadiya is None
        assert p2.requires_acharya_review is True

        p3 = result['saturn'][0]
        assert p3.classical_strength_rating == 0.5, "garbage TEXT rating must fall back, not raise"
        assert p3.resonance_match_score == 0.5
        assert p3.feasibility_score == 0.5

    def test_load_prescriptions_empty_result_is_empty_dict_not_error(self):
        """No rows → empty dict, same shape the caller (run()) already handles."""
        from pipeline.orchestrator.writers.ph_pratikara import PhPratikaraWriter

        conn = _F173FakeConn([])
        writer = PhPratikaraWriter()
        result = writer._load_prescriptions(conn, '482012f1-710e-4a25-994a-93821f5871aa')
        assert result == {}

    def test_safe_float_helper_never_raises(self):
        """Unit-level guard on the TEXT→float coercion helper itself."""
        from pipeline.orchestrator.writers.ph_pratikara import _safe_float

        assert _safe_float('0.85', 0.5, field='x', row_id='r1') == 0.85
        assert _safe_float('', 0.5, field='x', row_id='r1') == 0.5
        assert _safe_float(None, 0.5, field='x', row_id='r1') == 0.5
        assert _safe_float('not-a-number', 0.5, field='x', row_id='r1') == 0.5
        assert _safe_float('1', 0.5, field='x', row_id='r1') == 1.0
        # Decimal/numeric types (as NUMERIC columns come back) must pass through too.
        from decimal import Decimal
        assert _safe_float(Decimal('0.42'), 0.5, field='x', row_id='r1') == 0.42
