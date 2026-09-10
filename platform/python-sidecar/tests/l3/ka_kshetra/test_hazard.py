"""
tests/l3/ka_kshetra/test_hazard.py — ṢAḌ-DARŚANA W2 Lane C, §5.1 THE HAZARD FORMULA.

Every test here checks a property the design document states in prose, and each
one has a real failure mode. The properties are not incidental: the hazard's
strict positivity, the structural Adṛṣṭa floor, the multiplicative (never
subtractive) suppression, and the exact additivity of log-contributions are what
make the field integrable in closed form, null-calibratable, and provenance-
reconcilable. Break any one and a downstream guarantee silently stops holding.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ka_kshetra.contracts import ClockApplicability, PromisePrior, Route  # noqa: E402
from services.ka_kshetra import hazard  # noqa: E402


# ── C-1 baseline ──────────────────────────────────────────────────────────────

class TestBaseline:
    def test_baseline_rate_is_lifetime_count_over_a_century_of_days(self):
        # N_e events per 100 years -> events per day. 36525 = 100 Julian years.
        # P3-a: baseline_rate() now returns (rate, is_synthetic). Unpack for assertion.
        rate1, synth1 = hazard.baseline_rate(1.0)
        assert rate1 == pytest.approx(1.0 / 36525.0, rel=1e-15)
        assert synth1 is False
        rate3, synth3 = hazard.baseline_rate(3.0)
        assert rate3 == pytest.approx(3.0 / 36525.0, rel=1e-15)
        assert synth3 is False

    def test_zero_or_negative_lifetime_count_is_rejected_not_floored(self):
        # B.10 / LAW ZERO: a class with no usable prior is SKIPPED entirely
        # (§5.1 C-1), never handed a made-up or floored baseline. Silently
        # clamping to a tiny positive number would manufacture a hazard for a
        # class nobody has a prior for.
        with pytest.raises(ValueError):
            hazard.baseline_rate(0.0)
        with pytest.raises(ValueError):
            hazard.baseline_rate(-1.0)


# ── C-2 promise + the structural Adṛṣṭa floor ────────────────────────────────

class TestPromiseFloor:
    def test_zero_promise_still_yields_the_floor_not_zero(self):
        # THE Adṛṣṭa CHANNEL MADE STRUCTURAL. A class with zero natal promise
        # still receives 5% of baseline hazard, so windows over absent promise
        # are SERVED AND LABELLED, never suppressed — and λ can never be
        # identically zero, which the hazard interpretation requires.
        assert hazard.promise_tilde(0.0) == pytest.approx(hazard.P_FLOOR)

    def test_full_promise_yields_one(self):
        assert hazard.promise_tilde(1.0) == pytest.approx(1.0)

    def test_promise_tilde_is_affine_and_monotone_into_the_floor_one_band(self):
        prev = -1.0
        for p in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]:
            v = hazard.promise_tilde(p)
            assert hazard.P_FLOOR <= v <= 1.0
            assert v > prev
            prev = v
        assert hazard.promise_tilde(0.5) == pytest.approx(
            hazard.P_FLOOR + (1 - hazard.P_FLOOR) * 0.5
        )

    def test_out_of_range_promise_is_a_bug_not_a_clamp(self):
        with pytest.raises(ValueError):
            hazard.promise_tilde(1.5)
        with pytest.raises(ValueError):
            hazard.promise_tilde(-0.01)

    @pytest.mark.parametrize(
        "p,expected",
        [(0.0, 'absent'), (0.2, 'weak'), (0.45, 'moderate'), (0.8, 'strong')],
    )
    def test_promise_state_bands(self, p, expected):
        assert hazard.promise_state(p) == expected


# ── C-3 clocks: proportional hazards ─────────────────────────────────────────

def _clock(system_id: str, quality: float, predictive: bool = True,
           competence: str = 'fruition') -> ClockApplicability:
    return ClockApplicability(
        system_id=system_id,
        applicability_state='applicable',
        competence_class=competence,
        seniority_rank=1,
        is_predictive=predictive,
        quality=quality,
    )


class TestClockTerm:
    def test_weight_zero_collapses_the_factor_to_exactly_one(self):
        # §5.1: "w_s = 0 collapses the factor to exactly 1 — a calibration run
        # can switch a clock off smoothly without changing the model's
        # structure." Exactly 1.0, not approximately.
        assert hazard.clock_log_factor(quality=1.0, relevance=0.9, w_s=0.0) == 0.0

    def test_clock_factor_is_strictly_positive_for_any_finite_relevance(self):
        for r in (-1.0, -0.5, 0.0, 0.5, 1.0):
            v = math.exp(hazard.clock_log_factor(quality=1.0, relevance=r, w_s=1.0))
            assert v > 0.0

    def test_log_factor_is_w_times_quality_times_relevance(self):
        assert hazard.clock_log_factor(quality=0.8, relevance=0.5, w_s=0.6) == pytest.approx(
            0.6 * 0.8 * 0.5
        )

    def test_negative_relevance_suppresses_below_one_positive_lifts_above(self):
        assert math.exp(hazard.clock_log_factor(1.0, -0.7, 1.0)) < 1.0
        assert math.exp(hazard.clock_log_factor(1.0, +0.7, 1.0)) > 1.0

    def test_non_predictive_systems_are_excluded_from_S_pred(self):
        # Rule C-4: competence_class='life_stage' (naisargika) is a CONTEXT band,
        # never a predictor. Excluded BY CONSTRUCTION, not by a fitted weight
        # that happens to be near zero.
        clocks = [
            _clock('vimshottari', 1.0),
            _clock('naisargika', 1.0, predictive=False, competence='life_stage'),
        ]
        assert [c.system_id for c in hazard.predictive_systems(clocks)] == ['vimshottari']

    def test_non_applicable_systems_are_excluded_from_S_pred(self):
        c = ClockApplicability(
            system_id='kalachakra', applicability_state='not_computed',
            competence_class='arena', seniority_rank=3, is_predictive=True, quality=None,
        )
        assert hazard.predictive_systems([c]) == []

    # ── W3K G-4: the KP voice reaches S_pred(e) through the EXISTING clauses ──
    #
    # KALA_W2_FIELD_DESIGN_v1_0.md §11.4: "S_pred(e) is open by construction —
    # W3K's KP clock joins by adding a bg_dasha_systems row and a q_s rule (§4.1
    # step 4), WITH NO CHANGE TO §5.1." These two tests are that promise's proof:
    # `predictive_systems` is untouched by W3K, and both KP outcomes route
    # through clauses it already had.

    def test_redundant_kp_clock_is_excluded_from_S_pred_by_its_stage3_verdict(self):
        """When stage3's window-redundancy detector rules `vimshottari_kp`
        `excluded_by_condition`, S_pred drops it via its pre-existing
        applicability clause — so Vimśottarī's exponent is w_vim, never
        w_vim + w_kp on the identical lord stack."""
        clocks = [
            _clock('vimshottari', 0.9),
            ClockApplicability(
                system_id='vimshottari_kp', applicability_state='excluded_by_condition',
                competence_class='fruition', seniority_rank=8, is_predictive=True,
                quality=None,
                exclusion_reason="vimshottari_kp's period ladder is boundary-identical...",
            ),
        ]
        assert [c.system_id for c in hazard.predictive_systems(clocks)] == ['vimshottari']

    def test_a_genuinely_distinct_kp_clock_does_enter_S_pred(self):
        """The exclusion is a MEASUREMENT, not a permanent rule (§N.8): a chart
        whose KP ladder genuinely diverges yields `applicable` + a real q_s, and
        S_pred admits it with no code change here either."""
        clocks = [
            _clock('vimshottari', 0.9),
            _clock('vimshottari_kp', 0.42),
        ]
        assert [c.system_id for c in hazard.predictive_systems(clocks)] == [
            'vimshottari', 'vimshottari_kp',
        ]


class TestRelevance:
    def _routes(self):
        return (
            Route(event_class='career_change', route_rank=1,
                  path_node_ids=('graha:Ju', 'bhava:10', 'event_class:career_change'),
                  path_edge_ids=(), route_gain=0.60, is_primary=True),
            Route(event_class='career_change', route_rank=2,
                  path_node_ids=('graha:Sa', 'bhava:10', 'event_class:career_change'),
                  path_edge_ids=(), route_gain=0.30, is_primary=False, suppressed_by=('vedha:Sa->10',)),
        )

    def test_relevance_is_bounded_by_tanh(self):
        stack = [('MD', 'Ju'), ('AD', 'Ju'), ('PD', 'Ju'), ('SD', 'Ju'), ('PrD', 'Ju')]
        r = hazard.relevance(stack, self._routes(), hazard.DEFAULT_DEPTH_WEIGHTS)
        assert -1.0 <= r <= 1.0

    def test_a_lord_with_no_route_contributes_nothing(self):
        # g_ℓ = 0 when no route contains 'graha:<ℓ>' — an honest zero, not an
        # imputed default.
        r = hazard.relevance([('MD', 'Ve')], self._routes(), hazard.DEFAULT_DEPTH_WEIGHTS)
        assert r == 0.0

    def test_supportive_lord_is_positive_suppressed_lord_is_negative(self):
        pos = hazard.relevance([('MD', 'Ju')], self._routes(), hazard.DEFAULT_DEPTH_WEIGHTS)
        neg = hazard.relevance([('MD', 'Sa')], self._routes(), hazard.DEFAULT_DEPTH_WEIGHTS)
        assert pos > 0
        assert neg < 0
        assert pos == pytest.approx(math.tanh(1.0 * 0.60))
        assert neg == pytest.approx(math.tanh(-1.0 * 0.30))

    def test_deeper_levels_weigh_less_than_shallower_ones(self):
        md = hazard.relevance([('MD', 'Ju')], self._routes(), hazard.DEFAULT_DEPTH_WEIGHTS)
        prd = hazard.relevance([('PrD', 'Ju')], self._routes(), hazard.DEFAULT_DEPTH_WEIGHTS)
        assert md > prd > 0

    def test_precision_unsupported_levels_are_simply_absent(self):
        # Rule C-5: a level whose precision_state is 'precision_unsupported'
        # does not appear in lord_stack at all. Its term is ABSENT, not zeroed —
        # the caller (Lane B's boundary machinery) drops it before we see it, so
        # this test pins the arithmetic consequence: dropping a level changes r.
        full = hazard.relevance([('MD', 'Ju'), ('AD', 'Ju')], self._routes(),
                                hazard.DEFAULT_DEPTH_WEIGHTS)
        dropped = hazard.relevance([('MD', 'Ju')], self._routes(),
                                   hazard.DEFAULT_DEPTH_WEIGHTS)
        assert full != dropped


# ── C-5 modifiers ─────────────────────────────────────────────────────────────

class TestModifiers:
    def test_covariate_vector_is_frozen_at_twelve(self):
        # §5.1 C-5 / §11.2: "Adding a thirteenth covariate is a
        # weights-version-breaking change." The count is an invariant of
        # x_schema_version 'x12_v0', so it is asserted, not assumed.
        assert len(hazard.COVARIATE_KEYS) == 12
        assert hazard.X_SCHEMA_VERSION == 'x12_v0'
        assert hazard.COVARIATE_KEYS[0] == 'contact_moon_ref'
        assert hazard.COVARIATE_KEYS[11] == 'panchanga_affinity'

    def test_dual_reference_agreement_is_the_min_of_the_two_legs(self):
        x = hazard.derive_dual_reference_agreement({'contact_moon_ref': 0.8,
                                                    'contact_lagna_ref': 0.3})
        assert x == pytest.approx(0.3)

    def test_modifier_log_term_is_the_beta_dot_x(self):
        betas = {'beta:x1': 0.4, 'beta:x4': 0.35}
        x = {'contact_moon_ref': 0.5, 'av_kaksha_gate': 1.0}
        assert hazard.modifier_log_term(x, betas) == pytest.approx(0.4 * 0.5 + 0.35 * 1.0)

    def test_absent_beta_is_zero_not_a_default(self):
        assert hazard.modifier_log_term({'contact_moon_ref': 1.0}, {}) == 0.0


# ── C-6 suppression: MULTIPLICATIVE THINNING ─────────────────────────────────

class TestSuppression:
    def test_suppression_is_bounded_below_by_rho_max_complement(self):
        # ρ_max = 0.95 ⇒ S ≥ 0.05^|vighna|, STRICTLY POSITIVE however many
        # obstructors fire. This is the whole point of the Elevation §3 stage-4
        # amendment: λ stays positive by construction.
        u = {f'v{i}': 1.0 for i in range(5)}
        rho = {f'rho:v{i}': 0.95 for i in range(5)}
        S = math.exp(hazard.suppression_log_term(u, rho, default_rho=0.25))
        assert S > 0.0
        assert S == pytest.approx(0.05 ** 5)

    def test_full_suppression_at_rho_one_is_rejected_not_silently_clamped_wrong(self):
        # ρ is model-bounded to 0.95. A ρ above that would drive S to 0 and
        # ln λ to −inf, destroying the hazard interpretation.
        with pytest.raises(ValueError):
            hazard.suppression_log_term({'v': 1.0}, {'rho:v': 1.0}, default_rho=0.25)

    def test_no_active_obstructor_is_exactly_one(self):
        assert hazard.suppression_log_term({}, {}, default_rho=0.25) == 0.0
        assert hazard.suppression_log_term({'v': 0.0}, {'rho:v': 0.9}, default_rho=0.25) == 0.0

    def test_suppression_never_subtracts(self):
        # A subtractive form (λ − k·u) can cross zero; the multiplicative form
        # cannot. This test is the regression guard for anyone "simplifying"
        # thinning back into subtraction.
        for u_val in [0.0, 0.25, 0.5, 0.75, 1.0]:
            S = math.exp(hazard.suppression_log_term({'v': u_val}, {'rho:v': 0.95},
                                                     default_rho=0.25))
            assert 0.0 < S <= 1.0

    def test_signed_obstruction_is_a_rendering_in_minus_one_zero(self):
        assert hazard.signed_obstruction(1.0) == pytest.approx(0.0)
        assert hazard.signed_obstruction(0.05) == pytest.approx(-0.95)
        assert -1.0 < hazard.signed_obstruction(0.05) <= 0.0


# ── The whole formula + provenance additivity ────────────────────────────────

def _std_inputs(**over):
    base = dict(
        lifetime_count=1.0,
        promise=PromisePrior(p=0.5, routes=(
            Route(event_class='e', route_rank=1, path_node_ids=('graha:Ju', 'event_class:e'),
                  path_edge_ids=(), route_gain=0.6, is_primary=True),
        ), n_routes=1, fact_ids=('fact:promise:e',)),
        clocks=[_clock('vimshottari', 0.9)],
        lord_stacks={'vimshottari': [('MD', 'Ju')]},
        covariates={'contact_moon_ref': 0.5, 'av_kaksha_gate': 0.2},
        obstructions={'vedha:Sa->10': 0.4},
        weights={
            'w_s:vimshottari': 1.0,
            'beta:x1': 0.4, 'beta:x4': 0.35,
            'rho:vedha': 0.4,
            'd:MD': 1.0, 'd:AD': 0.7, 'd:PD': 0.5, 'd:SD': 0.3, 'd:PrD': 0.15,
        },
    )
    base.update(over)
    return base


class TestHazardEvaluation:
    def test_ln_lambda_equals_sum_of_provenance_log_contributions(self):
        # THE RECONCILIATION INVARIANT (§5.4) at its source. If this ever fails,
        # every provenance edge downstream is decorative rather than earned.
        terms = hazard.evaluate(**_std_inputs())
        assert terms.ln_lambda == pytest.approx(
            sum(e.log_contribution for e in terms.edges), abs=1e-12
        )

    def test_lambda_is_strictly_positive_under_maximal_suppression(self):
        terms = hazard.evaluate(**_std_inputs(
            promise=PromisePrior(p=0.0),
            obstructions={f'v{i}': 1.0 for i in range(8)},
            weights={**_std_inputs()['weights'], **{f'rho:v{i}': 0.95 for i in range(8)}},
        ))
        assert math.exp(terms.ln_lambda) > 0.0
        assert math.isfinite(terms.ln_lambda)

    def test_the_five_factors_multiply_back_to_lambda(self):
        t = hazard.evaluate(**_std_inputs())
        product = (t.baseline * t.promise_term * t.clock_term
                   * t.modifier_term * t.suppression_term)
        assert product == pytest.approx(math.exp(t.ln_lambda), rel=1e-12)

    def test_every_provenance_edge_has_a_positive_term_value(self):
        # The migration's CHECK (term_value > 0) must never be able to fire from
        # a legitimate build; if it can, the hazard model is broken upstream.
        t = hazard.evaluate(**_std_inputs())
        for e in t.edges:
            assert e.term_value > 0.0
            assert e.log_contribution == pytest.approx(math.log(e.term_value), abs=1e-12)

    def test_all_twelve_modifier_edges_are_emitted_even_when_zero(self):
        # Completeness beats brevity: a reader must be able to see the WHOLE
        # covariate vector at the peak, including the entries that were zero.
        t = hazard.evaluate(**_std_inputs(covariates={}))
        mod = [e for e in t.edges if e.term_role == 'modifier']
        assert len(mod) == 12
        assert all(e.term_value == 1.0 for e in mod)

    def test_identity_role_edges_carry_exactly_one_so_reconciliation_is_unchanged(self):
        # `route` and `gate` edges are REFERENCE edges: they cite the row that
        # holds the value (§N.5 — inherit, never restate) and are multiplicative
        # identities, so §5.4's sum "over that window's provenance rows" holds
        # verbatim with them present.
        t = hazard.evaluate(**_std_inputs())
        extra = hazard.identity_edge('route', 'route:rank1', 'l3_row',
                                     source_table='kala_field_routes', source_pk='17')
        assert extra.term_value == 1.0
        assert extra.log_contribution == 0.0
        assert t.ln_lambda == pytest.approx(
            sum(e.log_contribution for e in list(t.edges) + [extra]), abs=1e-12
        )

    def test_identity_edge_rejects_a_multiplicative_role(self):
        with pytest.raises(ValueError):
            hazard.identity_edge('clock', 'clock:vimshottari', 'l3_row')

    def test_one_clock_edge_per_predictive_system(self):
        t = hazard.evaluate(**_std_inputs(
            clocks=[_clock('vimshottari', 0.9), _clock('yogini', 0.5),
                    _clock('naisargika', 1.0, predictive=False, competence='life_stage')],
            lord_stacks={'vimshottari': [('MD', 'Ju')], 'yogini': [('MD', 'Ju')],
                         'naisargika': [('MD', 'Ju')]},
            weights={**_std_inputs()['weights'], 'w_s:yogini': 0.6, 'w_s:naisargika': 0.0},
        ))
        clock_keys = sorted(e.term_key for e in t.edges if e.term_role == 'clock')
        assert clock_keys == ['clock:vimshottari:MD:Ju', 'clock:yogini:MD:Ju']

    def test_a_missing_w_s_is_zero_so_an_unweighted_clock_cannot_smuggle_effect(self):
        # An unfitted, unseeded system must be INERT, not implicitly weight-1.
        t = hazard.evaluate(**_std_inputs(
            clocks=[_clock('unknown_system', 1.0)],
            lord_stacks={'unknown_system': [('MD', 'Ju')]},
        ))
        assert t.clock_term == pytest.approx(1.0)

    def test_determinism_same_inputs_same_bits(self):
        a = hazard.evaluate(**_std_inputs())
        b = hazard.evaluate(**_std_inputs())
        assert a.ln_lambda == b.ln_lambda
        assert [(e.term_key, e.term_value) for e in a.edges] == \
               [(e.term_key, e.term_value) for e in b.edges]
