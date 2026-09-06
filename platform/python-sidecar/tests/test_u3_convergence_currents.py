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


# ── C8 eclipse_proximity ─────────────────────────────────────────────────────

class TestEclipseProximity:
    """
    L3-W3 (F-SANGAM-7). _c8_eclipse_score used to pass node_planet='TrueNode' —
    not a real planet name anywhere in this codebase (transit_search.PLANET_IDS
    only has 'Rahu'/'Ketu') — so every call raised ValueError inside
    _get_planet_pos, silently swallowed by a blanket except-Exception, scoring
    0.0 on all 14,868 of 14,868 kala_convergence rows for the canonical chart.
    Fixed to check both real lunar nodes, matching the established
    gochara_grammar.primitives.eclipse_degree four-pair pattern.
    """

    @staticmethod
    def _fake_event(orb_at_event_deg, applying_separating='applying'):
        from types import SimpleNamespace
        return SimpleNamespace(
            orb_at_event_deg=orb_at_event_deg,
            applying_separating=applying_separating,
        )

    def test_never_queries_the_fictional_true_node(self):
        from services.ka_sangam.engine import _c8_eclipse_score
        service = MagicMock()
        service.find_eclipse_proximity.return_value = []
        _c8_eclipse_score('Jupiter', 2451545.0, 2451546.0, service, target_lon=100.0)
        queried_nodes = {
            c.kwargs['node_planet'] for c in service.find_eclipse_proximity.call_args_list
        }
        assert 'TrueNode' not in queried_nodes
        assert queried_nodes == {'Rahu', 'Ketu'}

    def test_rahu_only_event_is_scored(self):
        from services.ka_sangam.engine import _c8_eclipse_score
        service = MagicMock()
        service.find_eclipse_proximity.side_effect = (
            lambda node_planet, **kw: [self._fake_event(1.0)] if node_planet == 'Rahu' else []
        )
        score = _c8_eclipse_score('Jupiter', 2451545.0, 2451546.0, service, target_lon=100.0, orb=5.0)
        assert score > 0.0

    def test_ketu_only_event_is_scored(self):
        """Regression: an eclipse near Ketu must not be silently missed —
        the bug this fix closes would have scored this 0.0 even after the
        planet-name fix alone, since only Rahu was ever queried."""
        from services.ka_sangam.engine import _c8_eclipse_score
        service = MagicMock()
        service.find_eclipse_proximity.side_effect = (
            lambda node_planet, **kw: [self._fake_event(1.0)] if node_planet == 'Ketu' else []
        )
        score = _c8_eclipse_score('Jupiter', 2451545.0, 2451546.0, service, target_lon=100.0, orb=5.0)
        assert score > 0.0

    def test_no_events_scores_zero(self):
        from services.ka_sangam.engine import _c8_eclipse_score
        service = MagicMock()
        service.find_eclipse_proximity.return_value = []
        score = _c8_eclipse_score('Jupiter', 2451545.0, 2451546.0, service, target_lon=100.0)
        assert score == pytest.approx(0.0)

    def test_none_service_returns_zero(self):
        from services.ka_sangam.engine import _c8_eclipse_score
        score = _c8_eclipse_score('Jupiter', 2451545.0, 2451546.0, None, target_lon=100.0)
        assert score == pytest.approx(0.0)

    def test_exception_from_one_node_does_not_suppress_the_other(self):
        """A real failure on one node's lookup must not silently zero out a
        genuine event found via the other node."""
        from services.ka_sangam.engine import _c8_eclipse_score
        service = MagicMock()
        def side_effect(node_planet, **kw):
            if node_planet == 'Rahu':
                raise ValueError("simulated ephemeris failure")
            return [self._fake_event(1.0)]
        service.find_eclipse_proximity.side_effect = side_effect
        score = _c8_eclipse_score('Jupiter', 2451545.0, 2451546.0, service, target_lon=100.0, orb=5.0)
        assert score > 0.0


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
    """
    L3-W3 (F-SANGAM-5). _c11_vedha_factor used to match an abstract house
    number against rules fetched from bg_transit_rules WHERE rule_type='vedha'
    — a filter value that doesn't exist on that table (0 rows ever matched),
    so this NECESSARY-side veto was permanently neutral (1.0) on every
    window. Fixed to match peak_date against real [window_start, window_end)
    date ranges from kala_vedha_gochara, the populated per-chart source.
    """

    def test_vedha_rule_suppresses_score(self, dignity, orb_s, base_supporting):
        from services.ka_sangam.engine import convergence_score, _c11_vedha_factor, EnrichmentContext
        ctx = EnrichmentContext(
            vedha_rules=[{'graha': 'Jupiter', 'window_start': date(2026, 3, 1), 'window_end': date(2026, 5, 1)}]
        )
        vedha_f = _c11_vedha_factor('Jupiter', date(2026, 4, 1), ctx)
        assert vedha_f < 1.0, "Vedha rule should produce factor < 1.0"
        nec_no_vedha  = [dignity, orb_s, 1.0]
        nec_with_vedha = [dignity, orb_s, vedha_f]
        score_no = convergence_score(nec_no_vedha, base_supporting)
        score_w  = convergence_score(nec_with_vedha, base_supporting)
        assert score_w < score_no, "Vedha factor must reduce score (necessary-side veto)"

    def test_no_vedha_rule_returns_one(self, empty_ctx):
        from services.ka_sangam.engine import _c11_vedha_factor
        f = _c11_vedha_factor('Jupiter', date(2026, 4, 1), empty_ctx)
        assert f == pytest.approx(1.0), "No vedha rules → factor 1.0 (neutral)"

    def test_mismatched_planet_returns_one(self):
        from services.ka_sangam.engine import _c11_vedha_factor, EnrichmentContext
        ctx = EnrichmentContext(
            vedha_rules=[{'graha': 'Saturn', 'window_start': date(2026, 3, 1), 'window_end': date(2026, 5, 1)}]
        )
        f = _c11_vedha_factor('Jupiter', date(2026, 4, 1), ctx)  # Jupiter != Saturn
        assert f == pytest.approx(1.0)

    def test_peak_date_outside_window_returns_one(self):
        from services.ka_sangam.engine import _c11_vedha_factor, EnrichmentContext
        ctx = EnrichmentContext(
            vedha_rules=[{'graha': 'Jupiter', 'window_start': date(2020, 1, 1), 'window_end': date(2020, 2, 1)}]
        )
        f = _c11_vedha_factor('Jupiter', date(2026, 4, 1), ctx)  # real window, wrong date
        assert f == pytest.approx(1.0)

    def test_peak_date_none_returns_one(self):
        from services.ka_sangam.engine import _c11_vedha_factor, EnrichmentContext
        ctx = EnrichmentContext(
            vedha_rules=[{'graha': 'Jupiter', 'window_start': date(2026, 3, 1), 'window_end': date(2026, 5, 1)}]
        )
        f = _c11_vedha_factor('Jupiter', None, ctx)
        assert f == pytest.approx(1.0)


# ── C7 ashtakavarga_transit_potency ─────────────────────────────────────────

class TestAshtakavarga:
    """
    NIRMĀṆA L3-W3 N4b: c7 is HELD at an honest `None` — dropped from the
    saturating product, not scored zero — pending the L1 frame ruling on
    #1810 (is ashtakavarga_bindu's HOUSE_<N> a house or a rāśi?). Conductor
    ENDORSED this as D-CND-21: a partial fix that silences the visible
    failure while leaving the frame question open would be worse than the
    untouched defect. These tests lock in the held-null behaviour so it
    cannot regress into a plausible-looking fabricated number before #1810
    resolves; they must be revisited (not just loosened) once L1 answers.
    """
    def test_high_bindus_still_returns_none_pending_frame_ruling(self, empty_ctx):
        from services.ka_sangam.engine import _c7_ashtakavarga_potency, EnrichmentContext
        ctx_high = EnrichmentContext(ashtakavarga_bindu={'Jupiter': {1: 7}})
        assert _c7_ashtakavarga_potency('Jupiter', 1, ctx_high) is None

    def test_dropped_term_matches_omitted_key(self, dignity, orb_s, base_supporting):
        """A None c7 must be DROPPED from the saturating product (§N.7 item 6),
        identical to omitting the key entirely — never coalesced to a real 0.0."""
        from services.ka_sangam.engine import (
            convergence_score, _c7_ashtakavarga_potency, EnrichmentContext,
        )
        nec = [dignity, orb_s, 1.0]
        ctx = EnrichmentContext(ashtakavarga_bindu={'Jupiter': {1: 7}})
        c7 = _c7_ashtakavarga_potency('Jupiter', 1, ctx)
        assert c7 is None
        rest = {k: v for k, v in base_supporting.items() if k != 'ashtakavarga_transit_potency'}
        supporting_with_key_dropped = dict(rest)
        assert 'ashtakavarga_transit_potency' not in supporting_with_key_dropped
        # The writer's own pattern (engine.py:1092/1278): only include the key when
        # c7 is not None. With c7 always None today, that means never including it.
        supporting_as_writer_would_build_it = {
            **rest,
            **({'ashtakavarga_transit_potency': c7} if c7 is not None else {}),
        }
        assert convergence_score(nec, supporting_as_writer_would_build_it) == pytest.approx(
            convergence_score(nec, supporting_with_key_dropped)
        )

    def test_zero_bindus_returns_none(self, empty_ctx):
        from services.ka_sangam.engine import _c7_ashtakavarga_potency
        assert _c7_ashtakavarga_potency('Jupiter', 1, empty_ctx) is None

    @pytest.mark.parametrize("bindus", [0, 4, 8])
    def test_no_bindu_count_produces_a_score(self, bindus):
        """Formerly asserted a linear bindus/8.0 formula; that formula is unreachable
        code today (see the function's docstring) — it must stay unreachable until
        #1810 rules, not silently start firing again."""
        from services.ka_sangam.engine import _c7_ashtakavarga_potency, EnrichmentContext
        ctx = EnrichmentContext(ashtakavarga_bindu={'Jupiter': {1: bindus}})
        assert _c7_ashtakavarga_potency('Jupiter', 1, ctx) is None

    def test_no_transit_sign_returns_none(self, empty_ctx):
        from services.ka_sangam.engine import _c7_ashtakavarga_potency
        assert _c7_ashtakavarga_potency('Jupiter', None, empty_ctx) is None


# ── C12 tajika_annual_reinforcement ─────────────────────────────────────────

class TestTajika:
    """
    L3-W3 (F-SANGAM-7). _c12_tajika_score now matches on the varṣa's own
    [varsha_start, varsha_end) date range rather than an unreachable
    varsha_year == calendar_year comparison, and returns honest Optional[float]
    (None when no covering varṣa row exists, or no domain_lord to compare).
    """

    def test_varshesha_match_returns_one(self):
        from services.ka_sangam.engine import _c12_tajika_score, EnrichmentContext
        ctx = EnrichmentContext(
            tajika_year_lords=[{
                'varsha_year': 43, 'varshesha': 'Jupiter', 'muntha': 'Mars',
                'varsha_start': date(2026, 2, 5), 'varsha_end': date(2027, 2, 4),
            }]
        )
        score = _c12_tajika_score(date(2026, 4, 1), 'Jupiter', ctx)
        assert score == pytest.approx(1.0)

    def test_muntha_match_returns_half(self):
        from services.ka_sangam.engine import _c12_tajika_score, EnrichmentContext
        ctx = EnrichmentContext(
            tajika_year_lords=[{
                'varsha_year': 43, 'varshesha': 'Saturn', 'muntha': 'Jupiter',
                'varsha_start': date(2026, 2, 5), 'varsha_end': date(2027, 2, 4),
            }]
        )
        score = _c12_tajika_score(date(2026, 4, 1), 'Jupiter', ctx)
        assert score == pytest.approx(0.5)

    def test_no_match_returns_zero(self):
        from services.ka_sangam.engine import _c12_tajika_score, EnrichmentContext
        ctx = EnrichmentContext(
            tajika_year_lords=[{
                'varsha_year': 43, 'varshesha': 'Saturn', 'muntha': 'Mars',
                'varsha_start': date(2026, 2, 5), 'varsha_end': date(2027, 2, 4),
            }]
        )
        score = _c12_tajika_score(date(2026, 4, 1), 'Jupiter', ctx)
        assert score == pytest.approx(0.0)

    def test_empty_context_returns_none(self):
        from services.ka_sangam.engine import _c12_tajika_score
        from services.ka_sangam.engine import EnrichmentContext
        score = _c12_tajika_score(date(2026, 4, 1), 'Jupiter', EnrichmentContext.empty())
        assert score is None

    def test_no_domain_lord_returns_none(self):
        from services.ka_sangam.engine import _c12_tajika_score, EnrichmentContext
        ctx = EnrichmentContext(
            tajika_year_lords=[{
                'varsha_year': 43, 'varshesha': 'Jupiter', 'muntha': 'Mars',
                'varsha_start': date(2026, 2, 5), 'varsha_end': date(2027, 2, 4),
            }]
        )
        score = _c12_tajika_score(date(2026, 4, 1), None, ctx)
        assert score is None

    def test_window_outside_any_covering_varsha_returns_none(self):
        from services.ka_sangam.engine import _c12_tajika_score, EnrichmentContext
        ctx = EnrichmentContext(
            tajika_year_lords=[{
                'varsha_year': 42, 'varshesha': 'Jupiter', 'muntha': 'Jupiter',
                'varsha_start': date(2025, 2, 5), 'varsha_end': date(2026, 2, 4),
            }]
        )
        score = _c12_tajika_score(date(2026, 4, 1), 'Jupiter', ctx)
        assert score is None

    def test_datetime_with_date_method_is_handled(self):
        """varsha_start/varsha_end arrive as tz-aware datetimes in production
        (l1_tajik_varsha_year_lords.varsha_start_iso/varsha_end_iso are
        timestamptz columns) — must compare on the .date() component."""
        from datetime import datetime, timezone
        from services.ka_sangam.engine import _c12_tajika_score, EnrichmentContext
        ctx = EnrichmentContext(
            tajika_year_lords=[{
                'varsha_year': 43, 'varshesha': 'Jupiter', 'muntha': 'Mars',
                'varsha_start': datetime(2026, 2, 5, 5, 12, 38, tzinfo=timezone.utc),
                'varsha_end': datetime(2027, 2, 4, 11, 27, 24, tzinfo=timezone.utc),
            }]
        )
        score = _c12_tajika_score(date(2026, 4, 1), 'Jupiter', ctx)
        assert score == pytest.approx(1.0)


# ── EnrichmentContext empty-safe ─────────────────────────────────────────────

class TestEnrichmentContextEmptySafe:
    def test_empty_ctx_no_crash(self, dignity, orb_s, base_supporting):
        """EnrichmentContext.empty() must not raise in any C7-C12 helper."""
        from services.ka_sangam.engine import (
            EnrichmentContext, _c7_ashtakavarga_potency,
            _c11_vedha_factor, _c12_tajika_score,
        )
        ctx = EnrichmentContext.empty()
        assert _c7_ashtakavarga_potency('Jupiter', 1, ctx) is None  # held-null (N4b), not a crash
        assert _c11_vedha_factor('Jupiter', 1, ctx) == pytest.approx(1.0)
        assert _c12_tajika_score(date(2026, 1, 1), 'Jupiter', ctx) is None  # held-null (F-SANGAM-7), not a crash


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

    def test_unknown_signature_class_returns_none(self):
        from services.ka_sangam.engine import _c13_school_consensus_score, EnrichmentContext
        ctx = EnrichmentContext(school_consensus_by_domain={'CAREER': 5})
        score = _c13_school_consensus_score('COSMIC_UNKNOWN', ctx)
        assert score is None, "Unmappable signature class → honest None, not a fabricated 0.0"

    def test_empty_context_returns_none(self):
        from services.ka_sangam.engine import _c13_school_consensus_score, EnrichmentContext
        score = _c13_school_consensus_score('CAREER_PEAK', EnrichmentContext.empty())
        assert score is None

    def test_none_school_consensus_by_domain_returns_none(self):
        from services.ka_sangam.engine import _c13_school_consensus_score, EnrichmentContext
        ctx = EnrichmentContext(school_consensus_by_domain=None)
        score = _c13_school_consensus_score('SPIRITUAL_PEAK', ctx)
        assert score is None

    def test_real_signature_class_vocabulary_never_matches_a_domain(self):
        """NIRMĀṆA L3-W3 F-SANGAM-6, defect 2. The five hardcoded prefixes
        (CAREER/HEALTH/RELATIONSHIP/SPIRITUAL/PSYCHOLOGICAL) never match the
        REAL kala_activation_predicates_signature_class_check vocabulary
        (measured live) — so even with school_consensus_by_domain populated,
        every genuine signature_class value returns None, never a score."""
        from services.ka_sangam.engine import _c13_school_consensus_score, EnrichmentContext
        ctx = EnrichmentContext(school_consensus_by_domain={
            'CAREER': 4, 'HEALTH': 5, 'RELATIONSHIP': 3, 'SPIRITUAL': 6, 'PSYCHOLOGICAL': 7,
        })
        real_signature_classes = (
            'YOGA', 'DOSHA', 'DIGNITY', 'DISPOSITOR_RELATIONAL',
            'SENSITIVE_POINT', 'CONJUNCTION_ASPECT', 'SUBSYSTEM', 'CLASSIFY_RESIDUAL',
        )
        for sig_class in real_signature_classes:
            assert _c13_school_consensus_score(sig_class, ctx) is None, (
                f"{sig_class} is a real signature_class value and must not silently score"
            )

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

    def test_dropped_term_matches_omitted_key(self, dignity, orb_s, base_supporting):
        """A None c13 must be DROPPED from the saturating product (§N.7 item 6),
        identical to omitting the key entirely — never coalesced to a real 0.0."""
        from services.ka_sangam.engine import (
            convergence_score, _c13_school_consensus_score, EnrichmentContext,
        )
        nec = [dignity, orb_s, 1.0]
        c13 = _c13_school_consensus_score('YOGA', EnrichmentContext.empty())
        assert c13 is None
        rest = {k: v for k, v in base_supporting.items() if k != 'school_consensus'}
        supporting_with_key_dropped = dict(rest)
        assert 'school_consensus' not in supporting_with_key_dropped
        supporting_as_writer_would_build_it = {
            **rest,
            **({'school_consensus': c13} if c13 is not None else {}),
        }
        assert convergence_score(nec, supporting_as_writer_would_build_it) == pytest.approx(
            convergence_score(nec, supporting_with_key_dropped)
        )

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
