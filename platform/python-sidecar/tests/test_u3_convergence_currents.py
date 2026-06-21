"""
test_u3_convergence_currents.py — U3 acceptance tests: 7 new convergence currents (C7-C13).

Covers (U3 pass-1: C7-C12, pass-2: C13):
  - SUPPORTING_WEIGHTS: 12 keys, sum == 1.0, C13 school_consensus live
  - convergence_score stays ∈ [0,1] with new currents
  - C8 eclipse + C10 station raise score (intra-new-system direction test)
  - C11 vedha_cancellation suppresses score (necessary-side veto)
  - C7 ashtakavarga_potency raises score with high bindus
  - C12 tajika raises score when varṣeśa matches domain lord
  - C13 school_consensus: domain prefix mapping, empty/None safety, raises score
  - EnrichmentContext: default-empty context leaves new currents at 0.0 (no crash)
  - independent_current_count: C7–C13 coupling rules
  - No writes to L1/L3 tables (anti-drift)
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def dignity():
    return 0.85


@pytest.fixture
def orb_s():
    from services.ka_sangam.engine import orb_strength_score
    return orb_strength_score(2.3, 5.0, 'applying')


@pytest.fixture
def base_supporting():
    return {
        'constituent_lord_transit':    0.75,
        'ashtakavarga_transit_potency': 0.0,
        'cross_dasha_agreement':       0.60,
        'benefic_dristi':              0.40,
        'transit_to_transit':          0.0,
        'panchanga_quality':           0.50,
        'tara_bala':                   0.55,
        'eclipse_proximity':           0.0,
        'nakshatra_subsystem':         0.35,
        'station_retrograde':          0.0,
        'tajika_annual_reinforcement': 0.0,
    }


@pytest.fixture
def empty_ctx():
    from services.ka_sangam.engine import EnrichmentContext
    return EnrichmentContext.empty()


# ── SUPPORTING_WEIGHTS integrity ─────────────────────────────────────────────

class TestWeights:
    def test_12_keys(self):
        from services.ka_sangam.engine import SUPPORTING_WEIGHTS
        assert len(SUPPORTING_WEIGHTS) == 12, "U3-pass2 should have 12 keys (C13 now live)"

    def test_sum_equals_one(self):
        from services.ka_sangam.engine import SUPPORTING_WEIGHTS
        assert abs(sum(SUPPORTING_WEIGHTS.values()) - 1.0) < 1e-4

    def test_c13_present(self):
        from services.ka_sangam.engine import SUPPORTING_WEIGHTS
        assert 'school_consensus' in SUPPORTING_WEIGHTS, \
            "C13 school_consensus must be present (U3 pass-2 activated)"
        assert SUPPORTING_WEIGHTS['school_consensus'] == pytest.approx(0.10, rel=0.01)

    def test_vedha_absent(self):
        from services.ka_sangam.engine import SUPPORTING_WEIGHTS
        assert 'vedha_cancellation' not in SUPPORTING_WEIGHTS, \
            "C11 vedha enters the NECESSARY side, not supporting"

    def test_c7_through_c12_present(self):
        from services.ka_sangam.engine import SUPPORTING_WEIGHTS
        for key in (
            'ashtakavarga_transit_potency',  # C7
            'eclipse_proximity',             # C8
            'transit_to_transit',            # C9
            'station_retrograde',            # C10
            'tajika_annual_reinforcement',   # C12
        ):
            assert key in SUPPORTING_WEIGHTS, f"{key} missing from SUPPORTING_WEIGHTS"

    @pytest.mark.parametrize("key", [
        'constituent_lord_transit',
        'ashtakavarga_transit_potency',
        'cross_dasha_agreement',
        'benefic_dristi',
        'transit_to_transit',
        'panchanga_quality',
        'tara_bala',
        'eclipse_proximity',
        'nakshatra_subsystem',
        'station_retrograde',
        'tajika_annual_reinforcement',
    ])
    def test_weight_positive(self, key):
        from services.ka_sangam.engine import SUPPORTING_WEIGHTS
        assert SUPPORTING_WEIGHTS[key] > 0.0


# ── convergence_score bounds ─────────────────────────────────────────────────

class TestScoreBounds:
    def test_score_in_unit_interval(self, dignity, orb_s, base_supporting):
        from services.ka_sangam.engine import convergence_score
        score = convergence_score([dignity, orb_s, 1.0], base_supporting)
        assert 0.0 <= score <= 1.0

    def test_score_with_all_zero_supporting(self, dignity, orb_s):
        from services.ka_sangam.engine import convergence_score, SUPPORTING_WEIGHTS
        zero_sup = {k: 0.0 for k in SUPPORTING_WEIGHTS}
        score = convergence_score([dignity, orb_s, 1.0], zero_sup)
        assert score == pytest.approx(0.0, abs=1e-6)

    def test_score_with_all_one_supporting(self, dignity, orb_s):
        from services.ka_sangam.engine import convergence_score, SUPPORTING_WEIGHTS
        full_sup = {k: 1.0 for k in SUPPORTING_WEIGHTS}
        score = convergence_score([dignity, orb_s, 1.0], full_sup)
        assert 0.0 < score <= 1.0

    def test_clamped_above_one_input(self, dignity):
        from services.ka_sangam.engine import convergence_score, SUPPORTING_WEIGHTS
        # Even if inputs exceed 1.0, output stays ≤ 1.0
        over_sup = {k: 2.0 for k in SUPPORTING_WEIGHTS}
        score = convergence_score([dignity, 1.5], over_sup)
        assert score <= 1.0


# ── C8 eclipse + C10 station direction test (HARD GATE) ─────────────────────

class TestDirectionC8C10:
    def test_eclipse_and_station_raise_score(self, dignity, orb_s, base_supporting):
        from services.ka_sangam.engine import convergence_score
        nec = [dignity, orb_s, 1.0]
        score_base = convergence_score(nec, base_supporting)
        enriched = dict(base_supporting, eclipse_proximity=0.80, station_retrograde=0.60)
        score_enriched = convergence_score(nec, enriched)
        assert score_enriched > score_base, \
            "Eclipse+station should raise score (compound intensification)"

    def test_score_monotone_in_eclipse(self, dignity, orb_s, base_supporting):
        from services.ka_sangam.engine import convergence_score
        nec = [dignity, orb_s, 1.0]
        scores = []
        for v in (0.0, 0.3, 0.6, 0.9):
            s = convergence_score(nec, dict(base_supporting, eclipse_proximity=v))
            scores.append(s)
        assert scores == sorted(scores), "Score must be monotone in eclipse_proximity"

    def test_score_monotone_in_station(self, dignity, orb_s, base_supporting):
        from services.ka_sangam.engine import convergence_score
        nec = [dignity, orb_s, 1.0]
        scores = []
        for v in (0.0, 0.25, 0.50, 1.0):
            s = convergence_score(nec, dict(base_supporting, station_retrograde=v))
            scores.append(s)
        assert scores == sorted(scores), "Score must be monotone in station_retrograde"


# ── C11 vedha_cancellation NECESSARY-side veto ───────────────────────────────

class TestVedhaVeto:
    def test_vedha_rule_suppresses_score(self, dignity, orb_s, base_supporting):
        from services.ka_sangam.engine import convergence_score, _c11_vedha_factor, EnrichmentContext
        ctx = EnrichmentContext(
            vedha_rules=[{'graha': 'Jupiter', 'transit_to_house': 1, 'vedha_house': 7}]
        )
        vedha_f = _c11_vedha_factor('Jupiter', 1, ctx)
        assert vedha_f < 1.0, "Vedha rule should produce factor < 1.0"
        nec_no_vedha  = [dignity, orb_s, 1.0]
        nec_with_vedha = [dignity, orb_s, vedha_f]
        score_no = convergence_score(nec_no_vedha, base_supporting)
        score_w  = convergence_score(nec_with_vedha, base_supporting)
        assert score_w < score_no, "Vedha factor must reduce score (necessary-side veto)"

    def test_no_vedha_rule_returns_one(self, empty_ctx):
        from services.ka_sangam.engine import _c11_vedha_factor
        f = _c11_vedha_factor('Jupiter', 1, empty_ctx)
        assert f == pytest.approx(1.0), "No vedha rules → factor 1.0 (neutral)"

    def test_mismatched_planet_returns_one(self):
        from services.ka_sangam.engine import _c11_vedha_factor, EnrichmentContext
        ctx = EnrichmentContext(
            vedha_rules=[{'graha': 'Saturn', 'transit_to_house': 1, 'vedha_house': 7}]
        )
        f = _c11_vedha_factor('Jupiter', 1, ctx)  # Jupiter != Saturn
        assert f == pytest.approx(1.0)

    def test_mismatched_house_returns_one(self):
        from services.ka_sangam.engine import _c11_vedha_factor, EnrichmentContext
        ctx = EnrichmentContext(
            vedha_rules=[{'graha': 'Jupiter', 'transit_to_house': 2, 'vedha_house': 8}]
        )
        f = _c11_vedha_factor('Jupiter', 1, ctx)  # house 1 != 2
        assert f == pytest.approx(1.0)


# ── C7 ashtakavarga_transit_potency ─────────────────────────────────────────

class TestAshtakavarga:
    def test_high_bindus_raise_score(self, dignity, orb_s, base_supporting):
        from services.ka_sangam.engine import (
            convergence_score, _c7_ashtakavarga_potency, EnrichmentContext
        )
        nec = [dignity, orb_s, 1.0]
        ctx_low  = EnrichmentContext(ashtakavarga_bindu={'Jupiter': {1: 2}})
        ctx_high = EnrichmentContext(ashtakavarga_bindu={'Jupiter': {1: 7}})
        c7_low  = _c7_ashtakavarga_potency('Jupiter', 1, ctx_low)
        c7_high = _c7_ashtakavarga_potency('Jupiter', 1, ctx_high)
        score_low  = convergence_score(nec, dict(base_supporting, ashtakavarga_transit_potency=c7_low))
        score_high = convergence_score(nec, dict(base_supporting, ashtakavarga_transit_potency=c7_high))
        assert score_high > score_low

    def test_zero_bindus_returns_zero(self, empty_ctx):
        from services.ka_sangam.engine import _c7_ashtakavarga_potency
        assert _c7_ashtakavarga_potency('Jupiter', 1, empty_ctx) == pytest.approx(0.0)

    @pytest.mark.parametrize("bindus,expected", [
        (0, 0.0), (4, 0.5), (8, 1.0),
    ])
    def test_bindu_to_score_formula(self, bindus, expected):
        from services.ka_sangam.engine import _c7_ashtakavarga_potency, EnrichmentContext
        ctx = EnrichmentContext(ashtakavarga_bindu={'Jupiter': {1: bindus}})
        result = _c7_ashtakavarga_potency('Jupiter', 1, ctx)
        assert result == pytest.approx(expected, rel=0.01)

    def test_no_transit_sign_returns_zero(self, empty_ctx):
        from services.ka_sangam.engine import _c7_ashtakavarga_potency
        assert _c7_ashtakavarga_potency('Jupiter', None, empty_ctx) == pytest.approx(0.0)


# ── C12 tajika_annual_reinforcement ─────────────────────────────────────────

class TestTajika:
    def test_varshesha_match_returns_one(self):
        from services.ka_sangam.engine import _c12_tajika_score, EnrichmentContext
        ctx = EnrichmentContext(
            tajika_year_lords=[{'varsha_year': 2026, 'varshesha': 'Jupiter', 'muntha': 'Mars'}]
        )
        score = _c12_tajika_score(date(2026, 4, 1), 'Jupiter', ctx)
        assert score == pytest.approx(1.0)

    def test_muntha_match_returns_half(self):
        from services.ka_sangam.engine import _c12_tajika_score, EnrichmentContext
        ctx = EnrichmentContext(
            tajika_year_lords=[{'varsha_year': 2026, 'varshesha': 'Saturn', 'muntha': 'Jupiter'}]
        )
        score = _c12_tajika_score(date(2026, 4, 1), 'Jupiter', ctx)
        assert score == pytest.approx(0.5)

    def test_no_match_returns_zero(self):
        from services.ka_sangam.engine import _c12_tajika_score, EnrichmentContext
        ctx = EnrichmentContext(
            tajika_year_lords=[{'varsha_year': 2026, 'varshesha': 'Saturn', 'muntha': 'Mars'}]
        )
        score = _c12_tajika_score(date(2026, 4, 1), 'Jupiter', ctx)
        assert score == pytest.approx(0.0)

    def test_empty_context_returns_zero(self):
        from services.ka_sangam.engine import _c12_tajika_score
        from services.ka_sangam.engine import EnrichmentContext
        score = _c12_tajika_score(date(2026, 4, 1), 'Jupiter', EnrichmentContext.empty())
        assert score == pytest.approx(0.0)

    def test_wrong_year_returns_zero(self):
        from services.ka_sangam.engine import _c12_tajika_score, EnrichmentContext
        ctx = EnrichmentContext(
            tajika_year_lords=[{'varsha_year': 2025, 'varshesha': 'Jupiter', 'muntha': 'Jupiter'}]
        )
        score = _c12_tajika_score(date(2026, 4, 1), 'Jupiter', ctx)
        assert score == pytest.approx(0.0)


# ── EnrichmentContext empty-safe ─────────────────────────────────────────────

class TestEnrichmentContextEmptySafe:
    def test_empty_ctx_no_crash(self, dignity, orb_s, base_supporting):
        """EnrichmentContext.empty() must not raise in any C7-C12 helper."""
        from services.ka_sangam.engine import (
            EnrichmentContext, _c7_ashtakavarga_potency,
            _c11_vedha_factor, _c12_tajika_score,
        )
        ctx = EnrichmentContext.empty()
        assert _c7_ashtakavarga_potency('Jupiter', 1, ctx) == pytest.approx(0.0)
        assert _c11_vedha_factor('Jupiter', 1, ctx) == pytest.approx(1.0)
        assert _c12_tajika_score(date(2026, 1, 1), 'Jupiter', ctx) == pytest.approx(0.0)


# ── independent_current_count coupling rules (U3 extensions) ─────────────────

class TestICCCouplingU3:
    def test_ashtak_coupled_with_transit(self):
        from services.ka_sangam.engine import independent_current_count
        icc = independent_current_count({
            'transit': True,
            'ashtakavarga_transit_potency': True,
        })
        # Coupled: should count as ~1.5 → round to 2
        assert icc <= 2

    def test_eclipse_independent(self):
        from services.ka_sangam.engine import independent_current_count
        icc_base = independent_current_count({'transit': True})
        icc_with_eclipse = independent_current_count({'transit': True, 'eclipse_proximity': True})
        assert icc_with_eclipse > icc_base

    def test_t2t_independent(self):
        from services.ka_sangam.engine import independent_current_count
        icc_base = independent_current_count({'transit': True})
        icc_with_t2t = independent_current_count({'transit': True, 'transit_to_transit': True})
        assert icc_with_t2t > icc_base

    def test_station_independent(self):
        from services.ka_sangam.engine import independent_current_count
        icc_base = independent_current_count({'transit': True})
        icc_with_station = independent_current_count({'transit': True, 'station_retrograde': True})
        assert icc_with_station > icc_base

    def test_tajika_independent(self):
        from services.ka_sangam.engine import independent_current_count
        icc_base = independent_current_count({'transit': True})
        icc_with_tajika = independent_current_count({'transit': True, 'tajika_annual_reinforcement': True})
        assert icc_with_tajika > icc_base

    def test_all_12_currents_active(self):
        from services.ka_sangam.engine import independent_current_count
        all_currents = {
            'dasha': True, 'nakshatra_overlay': True, 'transit': True,
            'panchanga': True, 'benefic_dristi': True, 'cross_dasha_agreement': True,
            'ashtakavarga_transit_potency': True, 'eclipse_proximity': True,
            'transit_to_transit': True, 'station_retrograde': True,
            'tajika_annual_reinforcement': True, 'school_consensus': True,
        }
        icc = independent_current_count(all_currents)
        # With coupling, should be substantially below 12
        assert 4 <= icc <= 11

    def test_no_currents_returns_one(self):
        from services.ka_sangam.engine import independent_current_count
        assert independent_current_count({}) == 1
        assert independent_current_count({'dasha': False, 'transit': False}) == 1


# ── Anti-drift: no writes to L1/L3 tables ────────────────────────────────────

class TestAntiDrift:
    def test_engine_does_not_write_l1_tables(self):
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'services', 'ka_sangam', 'engine.py'
        )
        with open(path) as f:
            src = f.read()
        for bad in ('INSERT INTO chart_facts', 'INSERT INTO chart_dashas',
                    'INSERT INTO kala_activation_predicates', 'INSERT INTO kala_convergence'):
            assert bad not in src, f"engine.py must not write to {bad}"

    def test_supporting_weights_c13_weight_in_range(self):
        from services.ka_sangam.engine import SUPPORTING_WEIGHTS
        w = SUPPORTING_WEIGHTS.get('school_consensus', 0.0)
        assert 0.07 <= w <= 0.13, "C13 school_consensus weight must be in spec bound [0.07, 0.13]"


# ── C13 school_consensus current (U3 pass-2) ────────────────────────────────

class TestC13SchoolConsensus:
    def test_six_of_seven_returns_correct_score(self):
        from services.ka_sangam.engine import _c13_school_consensus_score, EnrichmentContext
        ctx = EnrichmentContext(school_consensus_by_domain={'CAREER': 6})
        score = _c13_school_consensus_score('CAREER_PEAK', ctx)
        assert score == pytest.approx(6 / 7.0, rel=0.01)

    def test_seven_of_seven_capped_at_one(self):
        from services.ka_sangam.engine import _c13_school_consensus_score, EnrichmentContext
        ctx = EnrichmentContext(school_consensus_by_domain={'HEALTH': 7})
        score = _c13_school_consensus_score('HEALTH_RISK', ctx)
        assert score == pytest.approx(1.0)

    def test_unknown_signature_class_returns_zero(self):
        from services.ka_sangam.engine import _c13_school_consensus_score, EnrichmentContext
        ctx = EnrichmentContext(school_consensus_by_domain={'CAREER': 5})
        score = _c13_school_consensus_score('COSMIC_UNKNOWN', ctx)
        assert score == pytest.approx(0.0), "Unmappable signature class → 0.0"

    def test_empty_context_returns_zero(self):
        from services.ka_sangam.engine import _c13_school_consensus_score, EnrichmentContext
        score = _c13_school_consensus_score('CAREER_PEAK', EnrichmentContext.empty())
        assert score == pytest.approx(0.0)

    def test_none_school_consensus_by_domain_returns_zero(self):
        from services.ka_sangam.engine import _c13_school_consensus_score, EnrichmentContext
        ctx = EnrichmentContext(school_consensus_by_domain=None)
        score = _c13_school_consensus_score('SPIRITUAL_PEAK', ctx)
        assert score == pytest.approx(0.0)

    def test_domain_prefix_mapping_all_five(self):
        from services.ka_sangam.engine import _c13_school_consensus_score, EnrichmentContext
        ctx = EnrichmentContext(school_consensus_by_domain={
            'CAREER': 4, 'HEALTH': 5, 'RELATIONSHIP': 3, 'SPIRITUAL': 6, 'PSYCHOLOGICAL': 7,
        })
        for sig_prefix, domain, n in [
            ('CAREER_PEAK', 'CAREER', 4),
            ('HEALTH_RISK', 'HEALTH', 5),
            ('RELATIONSHIP_PEAK', 'RELATIONSHIP', 3),
            ('SPIRITUAL_PEAK', 'SPIRITUAL', 6),
            ('PSYCHOLOGICAL_CRISIS', 'PSYCHOLOGICAL', 7),
        ]:
            expected = min(1.0, n / 7.0)
            got = _c13_school_consensus_score(sig_prefix, ctx)
            assert got == pytest.approx(expected, rel=0.01), \
                f"{sig_prefix} → expected {expected:.4f}, got {got:.4f}"

    def test_c13_raises_convergence_score(self, dignity, orb_s, base_supporting):
        from services.ka_sangam.engine import (
            convergence_score, _c13_school_consensus_score, EnrichmentContext
        )
        ctx = EnrichmentContext(school_consensus_by_domain={'CAREER': 6})
        c13 = _c13_school_consensus_score('CAREER_PEAK', ctx)
        nec = [dignity, orb_s, 1.0]
        score_without = convergence_score(nec, dict(base_supporting, school_consensus=0.0))
        score_with = convergence_score(nec, dict(base_supporting, school_consensus=c13))
        assert score_with > score_without, \
            "C13 school_consensus should raise convergence_score when schools agree"
