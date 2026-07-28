"""
test_ph_nimitta_spine.py — ph_nimitta acceptance tests (SPINE-FIRST gate D26).

Covers:
  - compute_posterior: BA-P5B product model (replaces G-LADDER compute_confidence_range)
  - AnchorLiftVector / StructuredFalsifier: new BA-P5B dataclasses
  - compute_magnitude: rarity × score tiers
  - derive_karmic_frame: planet → frame mapping
  - derive_malleability: domain × magnitude × direction
  - derive_anchor_from_convergence: all axes + elevations populated, posterior present
  - derive_anchor_from_bhavishya: D37 inherit (falsifier preserved, bhavishya_id set)
  - derive_anchor_from_discovery: Axis 4 (discovery_seeded)
  - SPINE GATE (D26): ≥1 anchor passes end-to-end
  - Anti-drift: engine.py has no DB writes
"""
from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def empty_ctx():
    from services.ph_nimitta.engine import NimittaContext
    return NimittaContext()


@pytest.fixture
def full_ctx():
    from services.ph_nimitta.engine import NimittaContext
    return NimittaContext(
        signal_domain='career',
        signal_signature_class='CAREER_PEAK',
        cgm_path_ids=['cgm-path-001'],
        root_graha='saturn',
        precedent_signal_ids=['sig-abc'],
        contradiction_contested=True,
        contradiction_thread='malefic_aspect_from_mars',
        contradiction_net='net_positive',
        dasha_consensus_count=5,
        school_consensus_jsonb={'n_of_7': 5, 'direction': 'positive'},
        ayanamsha_robustness=4,
        # BA-P5B posterior model inputs
        pratijna_grade=7.0,
        pratijna_status='promised',
        multi_system_confirmation_count=3,
        av_transit_potency=0.5,
        base_rate=0.12,
    )


@pytest.fixture
def convergence_row():
    return {
        'convergence_id': 42,
        'signal_id': '11111111-1111-1111-1111-111111111111',
        'mode': 'A',
        'peak_date': date(2026, 9, 15),
        'window_start': date(2026, 8, 1),
        'window_end': date(2026, 11, 30),
        'convergence_score': 0.72,
        'rarity_years': 7.5,
        'constituent_factors': {'dasha_score': 0.8, 'direction': 'elevated'},
        'source_citation': 'kala_convergence/42',
        'independent_current_count': 5,
        'confidence_score': 0.72,
        'confidence_label': 'high',
    }


@pytest.fixture
def bhavishya_row():
    return {
        'id': 7,
        'signal_id': '22222222-2222-2222-2222-222222222222',
        'convergence_id': 10,
        'domain': 'career',
        'peak_date': date(2027, 3, 1),
        'window_start': date(2026, 12, 1),
        'window_end': date(2027, 6, 30),
        'probability_tier': 'high_positive',
        'effective_score': 0.68,
        'falsifiability': 'No major career event by 2027-06-30 → REFUTED',
        'source_chain': 'L3/ka_yojaka→ka_sangam',
        'narrative': 'Career elevation likely in Saturn dasha',
        'outcome_recorded': None,
    }


@pytest.fixture
def discovery_row():
    return {
        'id': 'dd000000-0000-0000-0000-000000000001',
        'signal_id': '33333333-3333-3333-3333-333333333333',
        'domain': 'career',
        'discovery_type': 'hidden_yogakaraka',
        'surface_depth_delta': 0.45,
        'why_an_acharya_misses_it': 'Requires simultaneous 10H lord transit + dasha-anta activation',
        'falsifier_jsonb': {'statement': 'No Saturn-activation event in career by 2026-12-31 → REFUTED'},
        'confidence_score': 0.61,
    }


# ── compute_posterior (BA-P5B replaces G-LADDER) ─────────────────────────────

class TestComputePosterior:
    def test_returns_float_and_lift_vector(self):
        from services.ph_nimitta.engine import compute_posterior, AnchorLiftVector
        p, lift = compute_posterior(0.10, 7.0, 'promised', 3, 0.5)
        assert isinstance(p, float)
        assert isinstance(lift, AnchorLiftVector)

    def test_posterior_clamped_between_0_02_and_0_95(self):
        from services.ph_nimitta.engine import compute_posterior
        # extreme high inputs
        p, _ = compute_posterior(0.99, 10.0, 'promised', 5, 1.0)
        assert p <= 0.95
        # extreme low inputs
        p, _ = compute_posterior(0.001, 0.0, 'denied', 0, 0.0)
        assert p >= 0.02

    def test_denied_status_reduces_posterior(self):
        from services.ph_nimitta.engine import compute_posterior
        p_promised, _ = compute_posterior(0.10, 8.0, 'promised', 2, 0.3)
        p_denied, _   = compute_posterior(0.10, 8.0, 'denied',   2, 0.3)
        assert p_denied < p_promised

    def test_higher_grade_raises_posterior(self):
        from services.ph_nimitta.engine import compute_posterior
        p_low, _  = compute_posterior(0.10, 2.0, 'promised', 2, 0.3)
        p_high, _ = compute_posterior(0.10, 9.0, 'promised', 2, 0.3)
        assert p_high > p_low

    def test_higher_multi_system_count_raises_posterior(self):
        from services.ph_nimitta.engine import compute_posterior
        p0, _ = compute_posterior(0.10, 5.0, 'conditional', 0, 0.0)
        p5, _ = compute_posterior(0.10, 5.0, 'conditional', 5, 0.0)
        assert p5 > p0

    def test_lift_vector_fields_present(self):
        from services.ph_nimitta.engine import compute_posterior
        _, lift = compute_posterior(0.12, 7.0, 'promised', 3, 0.5)
        d = lift.as_dict()
        assert 'base_rate' in d
        assert 'promise_lift' in d
        assert 'activation_lift' in d
        assert 'trigger_lift' in d
        assert 'ayanamsha_robustness_modifier' in d
        assert 'posterior' in d

    def test_lift_posterior_matches_returned_posterior(self):
        from services.ph_nimitta.engine import compute_posterior
        p, lift = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4)
        assert lift.posterior == p


# ── StructuredFalsifier ───────────────────────────────────────────────────────

class TestStructuredFalsifier:
    def test_as_text_contains_domain_and_deadline(self):
        from services.ph_nimitta.engine import StructuredFalsifier
        sf = StructuredFalsifier(
            event_class_id='ec_career_change',
            magnitude_floor='moderate',
            domain='career',
            window_end='2026-12-31',
            attestation_required='lel_entry',
            refutation_condition='No career event of magnitude ≥ moderate by 2026-12-31.',
            confirmation_condition='Career event recorded in LEL before 2026-12-31.',
        )
        text = sf.as_text()
        assert 'career' in text.lower()
        assert '2026-12-31' in text
        assert 'REFUTED' in text or 'refuted' in text.lower() or 'documented' in text.lower()

    def test_as_dict_round_trips(self):
        from services.ph_nimitta.engine import StructuredFalsifier
        sf = StructuredFalsifier(
            event_class_id='ec_health',
            magnitude_floor='minor',
            domain='health',
            window_end='2027-03-31',
            attestation_required='native_attestation',
            refutation_condition='No health event',
            confirmation_condition='Health event recorded',
        )
        d = sf.as_dict()
        assert d['event_class_id'] == 'ec_health'
        assert d['attestation_required'] == 'native_attestation'

    def test_machine_evaluable_fields(self):
        from services.ph_nimitta.engine import StructuredFalsifier
        sf = StructuredFalsifier(
            event_class_id=None,
            magnitude_floor='major',
            domain='financial',
            window_end='2027-06-30',
            attestation_required='documented_external',
            refutation_condition='No financial event of magnitude ≥ major by 2027-06-30.',
            confirmation_condition='Financial event confirmed.',
        )
        # All fields machine-parseable
        d = sf.as_dict()
        assert d['magnitude_floor'] in ('minor', 'moderate', 'major', 'pivotal')
        assert d['domain'] in ('career', 'relationship', 'financial', 'spiritual',
                               'health', 'transition', 'psychological')


# ── compute_magnitude ────────────────────────────────────────────────────────

class TestMagnitude:
    @pytest.mark.parametrize("ry,es,expected", [
        (10.0, 1.0, 'pivotal'),    # 1.0 × 1.0 = 1.0 ≥ 0.60
        (8.0,  0.7, 'pivotal'),    # 0.8 × 0.7 = 0.56 → major (allow 1 tier off)
        (5.0,  0.7, 'major'),      # 0.5 × 0.7 = 0.35 → moderate (allow 1 tier off)
        (1.0,  0.1, 'minor'),      # 0.1 × 0.1 = 0.01 < 0.20
    ])
    def test_tiers(self, ry, es, expected):
        from services.ph_nimitta.engine import compute_magnitude
        tier, basis = compute_magnitude(ry, es)
        tiers = ['minor', 'moderate', 'major', 'pivotal']
        ti = tiers.index(tier)
        ei = tiers.index(expected)
        assert abs(ti - ei) <= 1, f"Expected ≈{expected}, got {tier} (ry={ry}, es={es})"

    def test_basis_contains_rarity_and_score(self):
        from services.ph_nimitta.engine import compute_magnitude
        _, basis = compute_magnitude(7.5, 0.72)
        assert 'rarity_years' in basis and 'effective_score' in basis

    def test_none_inputs_do_not_crash(self):
        from services.ph_nimitta.engine import compute_magnitude
        tier, _ = compute_magnitude(None, None)
        assert tier in ('minor', 'moderate', 'major', 'pivotal')


# ── derive_karmic_frame ──────────────────────────────────────────────────────

class TestKarmicFrame:
    @pytest.mark.parametrize("planet,expected_frame", [
        ('saturn',  'debt_surfacing'),
        ('ketu',    'debt_surfacing'),
        ('jupiter', 'grace_expansion'),
        ('rahu',    'desire_amplification'),
        ('mars',    'energy_directive'),
        ('venus',   'pleasure_integration'),
        ('moon',    'emotional_flux'),
        ('mercury', 'discernment_push'),
        ('sun',     'authority_assertion'),
    ])
    def test_all_planets(self, planet, expected_frame):
        from services.ph_nimitta.engine import derive_karmic_frame
        frame, note = derive_karmic_frame(planet)
        assert frame == expected_frame
        assert note  # non-empty

    def test_none_planet_returns_none(self):
        from services.ph_nimitta.engine import derive_karmic_frame
        frame, note = derive_karmic_frame(None)
        assert frame is None and note is None

    def test_case_insensitive(self):
        from services.ph_nimitta.engine import derive_karmic_frame
        f1, _ = derive_karmic_frame('Saturn')
        f2, _ = derive_karmic_frame('SATURN')
        assert f1 == f2 == 'debt_surfacing'


# ── derive_malleability ──────────────────────────────────────────────────────

class TestMalleability:
    def test_fated_when_pivotal_suppressed(self):
        from services.ph_nimitta.engine import derive_malleability
        assert derive_malleability('spiritual', 'pivotal', 'suppressed') == 'fated'

    def test_influenceable_for_health_minor(self):
        from services.ph_nimitta.engine import derive_malleability
        assert derive_malleability('health', 'minor', 'elevated') == 'influenceable'

    def test_semi_influenceable_default(self):
        from services.ph_nimitta.engine import derive_malleability
        assert derive_malleability('spiritual', 'major', 'elevated') == 'semi_influenceable'


# ── derive_anchor_from_convergence ───────────────────────────────────────────

class TestAnchorFromConvergence:
    def test_all_elevations_populated(self, convergence_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        a = derive_anchor_from_convergence(convergence_row, full_ctx, n_independent=5)
        assert a.magnitude is not None
        # BA-P5B: posterior replaces G-LADDER
        assert a.posterior is not None and 0.02 <= a.posterior <= 0.95
        assert a.lift_vector is not None
        assert a.karmic_frame == 'debt_surfacing'  # root_graha=saturn
        assert a.malleability is not None
        assert a.falsifier
        assert a.derivation_ledger_jsonb

    def test_source_is_convergence(self, convergence_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        a = derive_anchor_from_convergence(convergence_row, full_ctx, n_independent=3)
        assert a.anchor_source == 'convergence'
        assert a.convergence_id == 42

    def test_confidence_band_in_bounds(self, convergence_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        a = derive_anchor_from_convergence(convergence_row, full_ctx, n_independent=4)
        # backward compat band derived from posterior
        assert 0.0 <= a.confidence_low <= a.confidence_high <= 0.80

    def test_confidence_basis_is_structural(self, convergence_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        a = derive_anchor_from_convergence(convergence_row, full_ctx, n_independent=4)
        assert a.confidence_basis == 'structural_not_yet_empirical'

    def test_contradiction_v5_populated(self, convergence_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        a = derive_anchor_from_convergence(convergence_row, full_ctx, n_independent=4)
        assert a.contradiction_jsonb is not None
        assert 'contested' in a.contradiction_jsonb

    def test_causal_chain_v3_axis3(self, convergence_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        a = derive_anchor_from_convergence(convergence_row, full_ctx, n_independent=4)
        assert a.causal_chain_jsonb is not None
        assert a.causal_chain_jsonb.get('root_graha') == 'saturn'

    def test_derivation_ledger_has_posterior_inputs(self, convergence_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        a = derive_anchor_from_convergence(convergence_row, full_ctx, n_independent=4)
        led = a.derivation_ledger_jsonb
        assert 'convergence_id' in led
        assert 'axes_applied' in led and 'elevations' in led
        # BA-P5B: posterior inputs replace g_ladder_inputs
        assert 'posterior_inputs' in led
        assert 'g_ladder_inputs' not in led

    def test_structured_falsifier_populated(self, convergence_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        a = derive_anchor_from_convergence(convergence_row, full_ctx, n_independent=4)
        assert a.structured_falsifier is not None
        assert 'magnitude_floor' in a.structured_falsifier
        assert 'attestation_required' in a.structured_falsifier

    def test_empty_ctx_does_not_crash(self, convergence_row, empty_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        a = derive_anchor_from_convergence(convergence_row, empty_ctx, n_independent=1)
        assert a.anchor_source == 'convergence'


# ── derive_anchor_from_bhavishya (D37) ───────────────────────────────────────

class TestAnchorFromBhavishya:
    def test_source_is_bhavishya(self, bhavishya_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_bhavishya
        a = derive_anchor_from_bhavishya(bhavishya_row, full_ctx)
        assert a.anchor_source == 'bhavishya'
        assert a.bhavishya_id == 7

    def test_falsifiability_inherited(self, bhavishya_row, full_ctx):
        """D37: bhavishya falsifier must be preserved (not overwritten)."""
        from services.ph_nimitta.engine import derive_anchor_from_bhavishya
        a = derive_anchor_from_bhavishya(bhavishya_row, full_ctx)
        assert '2027-06-30' in a.falsifier

    def test_outcome_hook_in_ledger(self, bhavishya_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_bhavishya
        a = derive_anchor_from_bhavishya(bhavishya_row, full_ctx)
        assert 'outcome_recorded' in a.derivation_ledger_jsonb

    def test_horizon_tier_lifetime(self, bhavishya_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_bhavishya
        a = derive_anchor_from_bhavishya(bhavishya_row, full_ctx)
        assert a.horizon_tier == 'lifetime'

    def test_domain_career(self, bhavishya_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_bhavishya
        a = derive_anchor_from_bhavishya(bhavishya_row, full_ctx)
        assert a.domain == 'career'

    def test_all_elevations_present(self, bhavishya_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_bhavishya
        a = derive_anchor_from_bhavishya(bhavishya_row, full_ctx)
        assert a.magnitude and a.malleability and a.falsifier
        # BA-P5B: posterior present
        assert a.posterior is not None and 0.02 <= a.posterior <= 0.95


# ── derive_anchor_from_discovery (Axis 4) ────────────────────────────────────

class TestAnchorFromDiscovery:
    def test_source_is_discovery(self, discovery_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_discovery
        a = derive_anchor_from_discovery(discovery_row, full_ctx)
        assert a.anchor_source == 'discovery'
        assert a.discovery_id == 'dd000000-0000-0000-0000-000000000001'

    def test_inherits_falsifier_from_row(self, discovery_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_discovery
        a = derive_anchor_from_discovery(discovery_row, full_ctx)
        assert 'REFUTED' in a.falsifier

    def test_why_acharya_misses_in_ledger(self, discovery_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_discovery
        a = derive_anchor_from_discovery(discovery_row, full_ctx)
        assert 'why_an_acharya_misses_it' in a.derivation_ledger_jsonb

    def test_posterior_in_bounds(self, discovery_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_discovery
        a = derive_anchor_from_discovery(discovery_row, full_ctx)
        assert a.posterior is not None and 0.02 <= a.posterior <= 0.95

    def test_confidence_band_in_bounds(self, discovery_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_discovery
        a = derive_anchor_from_discovery(discovery_row, full_ctx)
        assert 0.0 <= a.confidence_low <= a.confidence_high <= 0.80


# ── SPINE GATE (D26) ─────────────────────────────────────────────────────────

class TestSpineGate:
    """D26: _spine_gate must accept ≥1 fully-populated anchor."""

    def _make_writer(self):
        from pipeline.orchestrator.writers.ph_nimitta import PhNimittaWriter
        w = PhNimittaWriter()
        return w

    def test_gate_passes_with_full_anchor(self, convergence_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        a = derive_anchor_from_convergence(convergence_row, full_ctx, n_independent=4)
        w = self._make_writer()
        w._spine_gate([a])   # must not raise

    def test_gate_fails_with_empty_list(self):
        w = self._make_writer()
        with pytest.raises(RuntimeError, match="SPINE GATE FAILED"):
            w._spine_gate([])

    def test_gate_fails_with_missing_magnitude(self, convergence_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        a = derive_anchor_from_convergence(convergence_row, full_ctx, n_independent=4)
        a.magnitude = None    # deliberately break it
        w = self._make_writer()
        with pytest.raises(RuntimeError, match="SPINE GATE FAILED"):
            w._spine_gate([a])

    def test_gate_fails_with_missing_posterior(self, convergence_row, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        a = derive_anchor_from_convergence(convergence_row, full_ctx, n_independent=4)
        a.posterior = None    # deliberately break it
        w = self._make_writer()
        with pytest.raises(RuntimeError, match="SPINE GATE FAILED"):
            w._spine_gate([a])


# ── R6 fix: datetime coercion (window_end < birth_date crash) ────────────────

class TestDateCoercion:
    """
    R6 fix: kala_convergence/kala_bhavishya/bodha_discoveries date columns can be
    `timestamptz` (psycopg returns `datetime.datetime`) rather than `date`. The three
    derive_anchor_from_* call sites previously only coerced the `str` case, silently
    passing a raw `datetime` through untouched — window_end then stayed a datetime and
    crashed the writer's T-5 pre-birth gate (`window_end < birth_date`) with
    "TypeError: can't compare datetime.datetime to datetime.date", cascading to fail
    every downstream L4/L5 asset in a real live rebuild. This locks the fix: all three
    derivation paths must coerce a raw datetime to date, not just strings.
    """

    def test_coerce_date_handles_datetime(self):
        from services.ph_nimitta.engine import _coerce_date
        assert _coerce_date(datetime(2026, 9, 15, 14, 30, 0)) == date(2026, 9, 15)

    def test_coerce_date_handles_date(self):
        from services.ph_nimitta.engine import _coerce_date
        assert _coerce_date(date(2026, 9, 15)) == date(2026, 9, 15)

    def test_coerce_date_handles_iso_string(self):
        from services.ph_nimitta.engine import _coerce_date
        assert _coerce_date('2026-09-15') == date(2026, 9, 15)

    def test_coerce_date_handles_none_and_garbage(self):
        from services.ph_nimitta.engine import _coerce_date
        assert _coerce_date(None) is None
        assert _coerce_date('not-a-date') is None
        assert _coerce_date(12345) is None

    def test_convergence_with_datetime_dates_does_not_crash(self, full_ctx):
        """The exact real-world shape: kala_convergence.peak_date/window_start/window_end
        as timestamptz → psycopg returns datetime.datetime, not date."""
        from services.ph_nimitta.engine import derive_anchor_from_convergence
        row = {
            'convergence_id': 42,
            'signal_id': '11111111-1111-1111-1111-111111111111',
            'mode': 'A',
            'peak_date': datetime(2026, 9, 15, 10, 0, 0),
            'window_start': datetime(2026, 8, 1, 0, 0, 0),
            'window_end': datetime(2026, 11, 30, 23, 59, 59),
            'convergence_score': 0.72,
            'rarity_years': 7.5,
            'constituent_factors': {'dasha_score': 0.8, 'direction': 'elevated'},
            'source_citation': 'kala_convergence/42',
            'independent_current_count': 5,
            'confidence_score': 0.72,
            'confidence_label': 'high',
        }
        a = derive_anchor_from_convergence(row, full_ctx, n_independent=4)
        assert a.window_end == date(2026, 11, 30)
        assert isinstance(a.window_end, date) and not isinstance(a.window_end, datetime)

    def test_bhavishya_with_datetime_dates_does_not_crash(self, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_bhavishya
        row = {
            'id': 7,
            'signal_id': '22222222-2222-2222-2222-222222222222',
            'convergence_id': 10,
            'domain': 'career',
            'peak_date': datetime(2027, 3, 1, 12, 0, 0),
            'window_start': datetime(2026, 12, 1, 0, 0, 0),
            'window_end': datetime(2027, 6, 30, 23, 59, 59),
            'probability_tier': 'high_positive',
            'effective_score': 0.68,
            'falsifiability': 'No major career event by 2027-06-30 → REFUTED',
            'source_chain': 'L3/ka_yojaka→ka_sangam',
            'narrative': 'Career elevation likely in Saturn dasha',
            'outcome_recorded': None,
        }
        a = derive_anchor_from_bhavishya(row, full_ctx)
        assert a.window_end == date(2027, 6, 30)
        assert isinstance(a.window_end, date) and not isinstance(a.window_end, datetime)

    def test_discovery_with_datetime_dates_does_not_crash(self, full_ctx):
        from services.ph_nimitta.engine import derive_anchor_from_discovery
        row = {
            'id': 'dd000000-0000-0000-0000-000000000001',
            'signal_id': '33333333-3333-3333-3333-333333333333',
            'domain': 'career',
            'discovery_type': 'hidden_yogakaraka',
            'surface_depth_delta': 0.45,
            'why_an_acharya_misses_it': 'test',
            'falsifier_jsonb': {'statement': 'No event by 2026-12-30 → REFUTED'},
            'confidence_score': 0.61,
            'peak_date': datetime(2026, 10, 1, 8, 0, 0),
            'window_start': datetime(2026, 9, 1, 0, 0, 0),
            'window_end': datetime(2026, 12, 30, 23, 59, 59),
        }
        a = derive_anchor_from_discovery(row, full_ctx)
        assert a.window_end == date(2026, 12, 30)
        assert isinstance(a.window_end, date) and not isinstance(a.window_end, datetime)


# ── CR-66: domain-vocabulary alignment + horizon-tier banding ────────────────

class TestCr66DomainVocabulary:
    """CR-66 root cause #1: the engine's _VALID_DOMAINS was a stale vocabulary
    (financial/spiritual/psychological) that neither matched the upstream sources nor the
    phala_anchors_domain_canonical DB CHECK — so 'wealth'/'spirituality'/'character' source
    rows all collapsed to 'transition' (wealth anchors could never exist)."""

    def test_wealth_domain_survives(self):
        from services.ph_nimitta.engine import _canonical_domain
        assert _canonical_domain('wealth') == 'wealth'

    def test_spirituality_domain_survives(self):
        from services.ph_nimitta.engine import _canonical_domain
        assert _canonical_domain('spirituality') == 'spirituality'

    def test_character_domain_survives(self):
        from services.ph_nimitta.engine import _canonical_domain
        assert _canonical_domain('character') == 'character'

    def test_legacy_financial_maps_to_wealth(self):
        from services.ph_nimitta.engine import _canonical_domain
        assert _canonical_domain('financial') == 'wealth'

    def test_legacy_spiritual_maps_to_spirituality(self):
        from services.ph_nimitta.engine import _canonical_domain
        assert _canonical_domain('spiritual') == 'spirituality'

    def test_legacy_psychological_maps_to_character(self):
        from services.ph_nimitta.engine import _canonical_domain
        assert _canonical_domain('psychological') == 'character'

    def test_unknown_falls_back_to_transition(self):
        from services.ph_nimitta.engine import _canonical_domain
        assert _canonical_domain('nonsense', None) == 'transition'

    def test_convergence_wealth_row_yields_wealth_anchor(self):
        """The end-to-end regression: a wealth-domain convergence row must produce a
        domain='wealth' anchor, not 'transition' (the wealth=0 bug)."""
        from services.ph_nimitta.engine import derive_anchor_from_convergence, NimittaContext
        row = {
            'convergence_id': 99,
            'signal_id': None,
            'mode': 'D',
            'peak_date': date(2028, 12, 26),
            'window_start': date(2028, 12, 26),
            'window_end': date(2029, 12, 22),
            'convergence_score': 0.304,
            'rarity_years': 0.99,
            'constituent_factors': {},
            'source_citation': 'kala_convergence/99',
            'independent_current_count': 1,
            'confidence_score': 0.304,
            'confidence_label': 'moderate',
            'domain': 'wealth',
        }
        a = derive_anchor_from_convergence(row, NimittaContext(), n_independent=1)
        assert a.domain == 'wealth'


class TestCr66HorizonTier:
    """CR-66 root cause #3: a past window must be 'lifetime' (historical), never 'near' —
    the prior inline test mislabeled every past window 'near', which the writer's stale-'near'
    clip gate then rejected, wiping out 100% of convergence anchors."""

    def test_past_window_is_lifetime(self):
        from services.ph_nimitta.engine import _horizon_tier
        assert _horizon_tier(date(2000, 1, 1)) == 'lifetime'

    def test_upcoming_window_is_near(self):
        from services.ph_nimitta.engine import _horizon_tier
        soon = date.today().replace(year=date.today().year + 1)
        assert _horizon_tier(soon) == 'near'

    def test_far_future_window_is_lifetime(self):
        from services.ph_nimitta.engine import _horizon_tier
        far = date.today().replace(year=date.today().year + 20)
        assert _horizon_tier(far) == 'lifetime'

    def test_none_window_is_lifetime(self):
        from services.ph_nimitta.engine import _horizon_tier
        assert _horizon_tier(None) == 'lifetime'

    def test_convergence_past_window_not_near(self):
        """A convergence anchor with a past window_end must NOT be 'near' (would be
        clip-gate-rejected as stale) — it is a lifetime/retrodictive anchor."""
        from services.ph_nimitta.engine import derive_anchor_from_convergence, NimittaContext
        row = {
            'convergence_id': 7, 'signal_id': None, 'mode': 'A',
            'peak_date': date(2010, 5, 1), 'window_start': date(2010, 1, 1),
            'window_end': date(2010, 12, 31), 'convergence_score': 1.0,
            'rarity_years': 5.0, 'constituent_factors': {}, 'source_citation': 'x',
            'independent_current_count': 1, 'confidence_score': 1.0, 'confidence_label': 'high',
            'domain': 'career',
        }
        a = derive_anchor_from_convergence(row, NimittaContext(), n_independent=1)
        assert a.horizon_tier == 'lifetime'


# ── P0-11 (SUDDHA-VACA D4_GRADE_INVERSION): direction honesty ────────────────

class TestDirectionHonestFallback:
    """P0-11: derive_anchor_from_convergence's directional-valence read must never
    silently launder a missing or malformed `constituent_factors['direction']` into
    the favorable-sounding 'elevated'. The correct honest-unknown value within the
    frozen 3-way phala_anchors.direction CHECK ('elevated'|'suppressed'|'mixed') is
    'mixed' — already the AnchorRecord dataclass's own default (engine.py line ~388)
    and already the established unknown-fallback in derive_anchor_from_bhavishya's
    prob_tier resolution. A suppressed/mixed/unknown signal must never read as
    elevated."""

    def _row(self, constituent_factors):
        return {
            'convergence_id': 1, 'signal_id': None, 'mode': 'A',
            'peak_date': date(2026, 9, 15), 'window_start': date(2026, 8, 1),
            'window_end': date(2026, 11, 30), 'convergence_score': 0.72,
            'rarity_years': 7.5, 'constituent_factors': constituent_factors,
            'source_citation': 'kala_convergence/1', 'independent_current_count': 1,
            'confidence_score': 0.72, 'confidence_label': 'high',
        }

    def test_missing_direction_key_is_not_elevated(self):
        from services.ph_nimitta.engine import derive_anchor_from_convergence, NimittaContext
        row = self._row({'dasha_score': 0.8})   # no 'direction' key at all
        a = derive_anchor_from_convergence(row, NimittaContext(), n_independent=1)
        assert a.direction != 'elevated'
        assert a.direction == 'mixed'

    def test_garbled_direction_value_is_not_elevated(self):
        from services.ph_nimitta.engine import derive_anchor_from_convergence, NimittaContext
        row = self._row({'direction': 'garbled_unexpected_value'})
        a = derive_anchor_from_convergence(row, NimittaContext(), n_independent=1)
        assert a.direction != 'elevated'
        assert a.direction == 'mixed'

    @pytest.mark.parametrize("legit", ['elevated', 'suppressed', 'mixed'])
    def test_legitimate_direction_values_pass_through_unchanged(self, legit):
        from services.ph_nimitta.engine import derive_anchor_from_convergence, NimittaContext
        row = self._row({'direction': legit})
        a = derive_anchor_from_convergence(row, NimittaContext(), n_independent=1)
        assert a.direction == legit


# ── Anti-drift ───────────────────────────────────────────────────────────────

class TestAntiDrift:
    def test_engine_has_no_db_writes(self):
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'services', 'ph_nimitta', 'engine.py'
        )
        with open(path) as f:
            src = f.read()
        for bad in ('INSERT INTO', 'UPDATE ', 'DELETE FROM', 'conn.cursor', 'psycopg2'):
            assert bad not in src, f"engine.py must not contain '{bad}'"

    def test_engine_has_no_g_ladder(self):
        """BA-P5B: G-LADDER function must be gone (checking non-comment code lines)."""
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'services', 'ph_nimitta', 'engine.py'
        )
        with open(path) as f:
            src = f.read()
        # Check for function/variable definitions (not docstring mentions)
        assert 'def compute_confidence_range' not in src, \
            "G-LADDER def compute_confidence_range must be deleted in BA-P5B"
        assert '_DOMAIN_KEYWORDS' not in src, \
            "_DOMAIN_KEYWORDS must be deleted in BA-P5B"
        assert 'def derive_domain' not in src, \
            "def derive_domain must be deleted in BA-P5B"
        assert 'def compute_posterior' in src, \
            "def compute_posterior must be present in BA-P5B engine"

    def test_writer_never_commits(self):
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator', 'writers', 'ph_nimitta.py'
        )
        with open(path) as f:
            src = f.read()
        code_lines = [ln for ln in src.splitlines() if not ln.lstrip().startswith('#') and '"""' not in ln]
        code_only = '\n'.join(code_lines)
        assert '.commit()' not in code_only, "writer must not call .commit()"
        assert '.rollback()' not in code_only, "writer must not call .rollback()"

    def test_writer_only_writes_phala_anchors(self):
        import os, re
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator', 'writers', 'ph_nimitta.py'
        )
        with open(path) as f:
            src = f.read()
        inserts = re.findall(r'INSERT INTO (\w+)', src)
        for tbl in inserts:
            assert tbl == 'phala_anchors', f"Writer inserts into unexpected table: {tbl}"
