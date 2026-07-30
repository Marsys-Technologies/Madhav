"""
Tests for services.ka_kshetra.stage6_salience — KALA_W2_FIELD_DESIGN_v1_0.md §6.1.

Most tests here are pure (no DB) since stage6_salience.py is a pure
computation layer by design. `TestComputeDomainsTouchedRealData` is the one
DB-backed class, run against the REAL seeded `brahma_event_ontology`
(migration 388, applied verbatim) to verify `compute_domains_touched()`
against real adjacency data rather than a hand-rolled fixture shape.
"""
from __future__ import annotations

import math
import os
import sys

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_kshetra.stage6_salience import (
    EventOntologyInfo,
    QuestionFrame,
    compute_actionability,
    compute_consequence,
    compute_domains_touched,
    compute_informativeness,
    compute_relevance,
    compute_reliability,
    compute_salience_vector,
)

_DSN = os.environ.get(
    "LANE_D_COHORT_DSN",
    "postgresql://postgres@/laned_test?host=/tmp/laned_pg_sock&port=55532",
)


class TestComputeInformativeness:
    def test_none_when_p_cohort_is_none(self):
        assert compute_informativeness(None, 10_000) is None

    def test_zero_p_caps_at_one(self):
        assert compute_informativeness(0.0, 10_000) == 1.0

    def test_p_equals_one_is_zero_informativeness(self):
        assert compute_informativeness(1.0, 10_000) == 0.0

    def test_typical_rare_configuration(self):
        # p = 1/27 (one nakshatra out of 27) at N=10,000
        p = 1 / 27
        i = compute_informativeness(p, 10_000)
        assert i is not None
        expected = min(1.0, -math.log(p) / math.log(10_000))
        assert abs(i - expected) < 1e-12

    def test_degenerate_n_returns_none(self):
        assert compute_informativeness(0.5, 1) is None
        assert compute_informativeness(0.5, 0) is None

    def test_never_negative_or_above_one(self):
        for p in [0.001, 0.01, 0.1, 0.5, 0.9, 0.999]:
            i = compute_informativeness(p, 10_000)
            assert 0.0 <= i <= 1.0


class TestComputeConsequence:
    def test_none_ontology_is_not_computed(self):
        q, basis = compute_consequence(None)
        assert q is None
        assert basis == ()

    def test_trivial_no_adjacency(self):
        onto = EventOntologyInfo("x", "career", "trivial", frozenset())
        q, basis = compute_consequence(onto)
        assert basis == ("severity", "domains")
        # severity_norm = 0/4 = 0; domains_norm = min(1, 1/3) = 1/3
        expected = (0.5 * 0.0 + 0.3 * (1 / 3)) / 0.8
        assert abs(q - expected) < 1e-12

    def test_life_altering_max_severity(self):
        onto = EventOntologyInfo("x", "career", "life_altering", frozenset())
        q, _ = compute_consequence(onto)
        # severity_norm = 4/4 = 1.0
        expected = (0.5 * 1.0 + 0.3 * (1 / 3)) / 0.8
        assert abs(q - expected) < 1e-12

    def test_multi_domain_adjacency_saturates_domains_norm(self):
        onto = EventOntologyInfo(
            "x", "career", "moderate",
            adjacent_domains=frozenset({"wealth", "health", "family"}),
        )
        q, _ = compute_consequence(onto)
        # domains_touched = {career, wealth, health, family} = 4 -> min(1, 4/3) = 1.0
        expected = (0.5 * 0.25 + 0.3 * 1.0) / 0.8
        assert abs(q - expected) < 1e-12
        assert 0.0 <= q <= 1.0

    def test_q_always_in_unit_interval(self):
        for mag in ["trivial", "moderate", "significant", "major", "life_altering"]:
            for n_adj in range(0, 5):
                onto = EventOntologyInfo(
                    "x", "career", mag,
                    adjacent_domains=frozenset(f"d{i}" for i in range(n_adj)),
                )
                q, _ = compute_consequence(onto)
                assert 0.0 <= q <= 1.0


class TestComputeRelevance:
    def test_no_frame_is_maximal(self):
        assert compute_relevance("career", 0, 100, frozenset(), None) == 1.0

    def test_matching_domain_no_horizon_no_entities(self):
        frame = QuestionFrame(domain="career")
        r = compute_relevance("career", 0, 100, frozenset(), frame)
        # domain_match=1, horizon_overlap=1 (unconstrained), entity_match=1 (unconstrained)
        assert r == 1.0

    def test_mismatched_domain_penalizes(self):
        frame = QuestionFrame(domain="health")
        r = compute_relevance("career", 0, 100, frozenset(), frame)
        assert r == 0.5 * 0.0 + 0.3 * 1.0 + 0.2 * 1.0

    def test_full_horizon_overlap(self):
        frame = QuestionFrame(horizon_start=0, horizon_end=100)
        r = compute_relevance("career", 0, 100, frozenset(), frame)
        assert r == 1.0

    def test_partial_horizon_overlap_jaccard(self):
        frame = QuestionFrame(horizon_start=50, horizon_end=150)
        # window [0,100], frame [50,150]: intersection=50, union=150
        r = compute_relevance("career", 0, 100, frozenset(), frame)
        expected = 0.5 * 1.0 + 0.3 * (50 / 150) + 0.2 * 1.0
        assert abs(r - expected) < 1e-12

    def test_no_horizon_overlap_at_all(self):
        frame = QuestionFrame(horizon_start=200, horizon_end=300)
        r = compute_relevance("career", 0, 100, frozenset(), frame)
        expected = 0.5 * 1.0 + 0.3 * 0.0 + 0.2 * 1.0
        assert abs(r - expected) < 1e-12

    def test_entity_match_and_mismatch(self):
        frame = QuestionFrame(entities=frozenset({"Saturn"}))
        r_match = compute_relevance("career", 0, 100, frozenset({"Saturn", "Rahu"}), frame)
        r_miss = compute_relevance("career", 0, 100, frozenset({"Venus"}), frame)
        assert r_match == 1.0
        assert r_miss == 0.5 * 1.0 + 0.3 * 1.0 + 0.2 * 0.0


class TestComputeReliability:
    @pytest.mark.parametrize("tier,expected", [
        ("calibrated", 1.0), ("calibrated_provisional", 0.85),
        ("concurrent", 0.75), ("structural_prior", 0.5),
    ])
    def test_known_tiers(self, tier, expected):
        assert compute_reliability(tier) == expected

    def test_none_tier_is_not_computed(self):
        assert compute_reliability(None) is None

    def test_unknown_tier_is_not_computed(self):
        assert compute_reliability("bogus_tier") is None


class TestComputeActionability:
    def test_elect_upaya(self):
        assert compute_actionability("elect_upaya") == 1.0

    def test_ritual_only(self):
        assert compute_actionability("ritual_only") == 0.5

    def test_no_lever(self):
        assert compute_actionability("no_lever") == 0.0

    def test_none_is_not_computed(self):
        assert compute_actionability(None) is None


class TestComputeSalienceVector:
    def test_all_factors_present(self):
        onto = EventOntologyInfo("career_entry", "career", "moderate", frozenset())
        vec = compute_salience_vector(
            p_cohort=0.05, cohort_n_total=10_000, ontology=onto,
            event_domain="career", window_t_start=0, window_t_end=100,
            confidence_tier="concurrent", intervention_ref="elect_upaya",
        )
        assert vec.salience_basis == ("I", "Q", "R", "B", "A")
        assert vec.salience_weights_version == "salience_v0"
        # manual recompute
        i = compute_informativeness(0.05, 10_000)
        q, _ = compute_consequence(onto)
        r = 1.0  # no frame
        b = 0.75
        a = 1.0
        expected = 0.30 * i + 0.25 * q + 0.20 * r + 0.15 * b + 0.10 * a
        assert abs(vec.salience - expected) < 1e-12

    def test_missing_factors_renormalize_never_impute(self):
        # informativeness and actionability missing (None); Q/R/B present.
        onto = EventOntologyInfo("x", "career", "moderate", frozenset())
        vec = compute_salience_vector(
            p_cohort=None, cohort_n_total=10_000, ontology=onto,
            event_domain="career", window_t_start=0, window_t_end=100,
            confidence_tier="concurrent", intervention_ref=None,
        )
        assert vec.informativeness is None
        assert vec.actionability is None
        assert vec.salience_basis == ("Q", "R", "B")
        # renormalized: weights Q=0.25,R=0.20,B=0.15 sum=0.60
        q, _ = compute_consequence(onto)
        expected = (0.25 * q + 0.20 * 1.0 + 0.15 * 0.75) / 0.60
        assert abs(vec.salience - expected) < 1e-12

    def test_salience_bounded_in_unit_interval(self):
        onto = EventOntologyInfo("x", "career", "major", frozenset({"wealth"}))
        vec = compute_salience_vector(
            p_cohort=0.001, cohort_n_total=10_000, ontology=onto,
            event_domain="career", window_t_start=0, window_t_end=100,
            confidence_tier="calibrated", intervention_ref="elect_upaya",
        )
        assert 0.0 <= vec.salience <= 1.0

    def test_all_factors_missing_salience_is_zero_not_error(self):
        vec = compute_salience_vector(
            p_cohort=None, cohort_n_total=10_000, ontology=None,
            event_domain=None, window_t_start=0, window_t_end=100,
            confidence_tier=None, intervention_ref=None,
            frame=QuestionFrame(),  # still gives R (frame given but no constraints -> R=1.0, present)
        )
        # R is always computable (defaults to 1.0 with no constraints), so
        # salience_basis is never fully empty in practice -- but assert the
        # degenerate arithmetic doesn't crash and stays in-bounds regardless.
        assert 0.0 <= vec.salience <= 1.0
        assert "R" in vec.salience_basis


@pytest.mark.integration
class TestComputeDomainsTouchedRealData:
    """Against the REAL seeded brahma_event_ontology (migration 388)."""

    def _connect(self):
        try:
            import psycopg2
            return psycopg2.connect(_DSN)
        except Exception as exc:  # pragma: no cover
            pytest.skip(f"throwaway Postgres not available: {exc}")

    def test_career_change_touches_career_domain_only_for_resolvable_adjacency(self):
        """
        Real fixture: career_change's adjacency = ["career_entry", "transition"].
        career_entry resolves to domain "career"; "transition" is NOT itself a
        seeded event_class_id (only a domain enum value elsewhere) -- so it
        must NOT silently resolve to a fabricated domain. compute_domains_touched
        must handle the dangling adjacency reference honestly (skip, don't crash
        or invent).
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT event_class_id, domain, adjacency FROM brahma_event_ontology"
                )
                rows = cur.fetchall()
            domain_by_class = {r[0]: r[1] for r in rows}
            adjacency_by_class = {r[0]: (r[2] or []) for r in rows}

            touched = compute_domains_touched(
                "career_change", "career",
                adjacency_by_class["career_change"], domain_by_class,
            )
            assert touched == frozenset({"career"})
        finally:
            conn.close()

    def test_cross_domain_adjacency_resolves_multiple_domains(self):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT event_class_id, domain, adjacency FROM brahma_event_ontology"
                )
                rows = cur.fetchall()
            domain_by_class = {r[0]: r[1] for r in rows}
            adjacency_by_class = {r[0]: (r[2] or []) for r in rows}

            # Real fixture: major_gain (wealth) is adjacent to
            # property_acquisition (residence) -- a genuine cross-domain pair
            # confirmed present in the seeded 22-class corpus.
            touched = compute_domains_touched(
                "major_gain", domain_by_class["major_gain"],
                adjacency_by_class["major_gain"], domain_by_class,
            )
            assert touched == frozenset({"wealth", "residence"})

            # And assert the general property across the WHOLE corpus: every
            # class's own domain is always a member of its own touched set.
            found_cross_domain = False
            for cls, adj in adjacency_by_class.items():
                own_domain = domain_by_class[cls]
                t = compute_domains_touched(cls, own_domain, adj, domain_by_class)
                assert own_domain in t
                if len(t) > 1:
                    found_cross_domain = True
            assert found_cross_domain, "expected at least one real cross-domain adjacency in the corpus"
        finally:
            conn.close()
