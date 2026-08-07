"""
Tests for services.ka_kshetra.stage65_insights — KALA_W2_FIELD_DESIGN_v1_0.md
§6.4 (E2: the 8-type insight catalog, 7 non-LEL types).

Pure-Python module, no DB -- all tests here are pure unit tests.
"""
from __future__ import annotations

import os
import sys

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_kshetra.stage65_insights import (
    NON_LEL_INSIGHT_TYPES,
    ClockAgreement,
    CohortSurpriseInput,
    InsightWindow,
    ReversalSample,
    assemble_insight_row,
    compute_cohort_surprise,
    detect_absence_of_expected,
    detect_compression,
    detect_concurrence,
    detect_contrast,
    detect_rarity_firing,
    detect_reversal,
    detect_scarcity,
    select_leading_insight,
    synthesize_insights,
)


def _window(window_id="w1", event_class="career_change", t_peak=1000.0, salience=0.7,
            confidence_tier="concurrent", t_start=None, t_end=None,
            lord_stack=("Saturn",), clock_agreements=(), fact_ids=("fact1",), robustness=None):
    return InsightWindow(
        window_id=window_id, event_class=event_class,
        t_start=t_start if t_start is not None else t_peak - 30,
        t_end=t_end if t_end is not None else t_peak + 30,
        t_peak=t_peak, lambda_peak=0.05, salience=salience,
        confidence_tier=confidence_tier, lord_stack_at_peak=lord_stack,
        clock_agreements=clock_agreements, fact_ids=fact_ids, robustness=robustness,
    )


class TestCircularityGuard:
    """The one non-negotiable invariant of this module."""

    def test_biographical_echo_not_in_non_lel_types(self):
        assert "biographical_echo" not in NON_LEL_INSIGHT_TYPES

    def test_seven_types_exactly(self):
        assert len(NON_LEL_INSIGHT_TYPES) == 7

    def test_assembled_row_always_lel_derived_false(self):
        cand = detect_concurrence(_window(clock_agreements=(
            ClockAgreement("vimshottari", "dasha_md", 0.5),
            ClockAgreement("yogini", "dasha_yogini", 0.6),
            ClockAgreement("kalachakra", "dasha_kalachakra", 0.4),
        )))
        row = assemble_insight_row("chart1", cand, "wv1", "snap1")
        assert row["lel_derived"] is False
        assert row["field_snapshot_id"] == "snap1"

    def test_no_lel_reference_anywhere_in_module_source(self):
        """Static half of the Circularity Guard (§8.3): grep the module's own
        source for any LEL reference."""
        import services.ka_kshetra.stage65_insights as mod
        src = open(mod.__file__).read().lower()
        for banned in ("life_event_log", "lel_query", "mimamsa_lel", "from lel"):
            assert banned not in src


class TestCohortSurprise:
    def test_none_cohort_is_not_surprise_credited(self):
        surprise, basis = compute_cohort_surprise(None)
        assert surprise == 0.5
        assert basis == "not_surprise_credited"

    def test_p_none_is_not_surprise_credited(self):
        surprise, basis = compute_cohort_surprise(CohortSurpriseInput(p_cohort=None, n_cohort=10_000))
        assert surprise == 0.5
        assert basis == "not_surprise_credited"

    def test_p_zero_is_maximal_surprise(self):
        surprise, basis = compute_cohort_surprise(CohortSurpriseInput(p_cohort=0.0, n_cohort=10_000))
        assert surprise == 1.0
        assert basis == "cohort_base_rate"

    def test_real_rate_in_bounds(self):
        surprise, basis = compute_cohort_surprise(CohortSurpriseInput(p_cohort=0.01, n_cohort=10_000))
        assert 0.0 < surprise < 1.0
        assert basis == "cohort_base_rate"


class TestDetectConcurrence:
    def test_three_independent_systems_fires(self):
        w = _window(clock_agreements=(
            ClockAgreement("vimshottari", "dasha_md", 0.5),
            ClockAgreement("yogini", "dasha_yogini", 0.6),
            ClockAgreement("kalachakra", "dasha_kalachakra", 0.4),
        ))
        cand = detect_concurrence(w)
        assert cand is not None
        assert cand.insight_type == "concurrence"
        assert cand.statement_params["n_independent_systems"] == 3

    def test_two_systems_does_not_fire(self):
        w = _window(clock_agreements=(
            ClockAgreement("vimshottari", "dasha_md", 0.5),
            ClockAgreement("yogini", "dasha_yogini", 0.6),
        ))
        assert detect_concurrence(w) is None

    def test_same_competence_class_counts_once(self):
        """Independence = distinct competence_class -- two systems sharing
        one competence_class must not double-count as two voices."""
        w = _window(clock_agreements=(
            ClockAgreement("vimshottari", "dasha_md", 0.5),
            ClockAgreement("ashtottari", "dasha_md", 0.6),   # same class as vimshottari
            ClockAgreement("kalachakra", "dasha_kalachakra", 0.4),
        ))
        assert detect_concurrence(w) is None  # only 2 distinct classes

    def test_negative_r_value_does_not_count(self):
        w = _window(clock_agreements=(
            ClockAgreement("vimshottari", "dasha_md", 0.5),
            ClockAgreement("yogini", "dasha_yogini", -0.2),  # negative -- not agreeing
            ClockAgreement("kalachakra", "dasha_kalachakra", 0.4),
        ))
        assert detect_concurrence(w) is None


class TestDetectRarityFiring:
    def test_fires_below_threshold(self):
        w = _window()
        cand = detect_rarity_firing(w, CohortSurpriseInput(p_cohort=0.01, n_cohort=10_000))
        assert cand is not None
        assert cand.insight_type == "rarity_firing"

    def test_does_not_fire_above_threshold(self):
        w = _window()
        assert detect_rarity_firing(w, CohortSurpriseInput(p_cohort=0.5, n_cohort=10_000)) is None

    def test_does_not_fire_when_p_none(self):
        w = _window()
        assert detect_rarity_firing(w, CohortSurpriseInput(p_cohort=None, n_cohort=10_000)) is None

    def test_custom_p_rare_threshold(self):
        w = _window()
        assert detect_rarity_firing(w, CohortSurpriseInput(0.08, 10_000), p_rare=0.10) is not None
        assert detect_rarity_firing(w, CohortSurpriseInput(0.08, 10_000), p_rare=0.05) is None


class TestDetectAbsenceOfExpected:
    def test_fires_when_strong_promise_and_no_windows(self):
        # ABSENCE_MIN_PROMISE = 6.0 (grade on [0, 10] scale); 7.5 is above threshold
        cand = detect_absence_of_expected("career_entry", 7.5, [], 0.0, 36525.0)
        assert cand is not None
        assert cand.window_id is None
        assert cand.event_class == "career_entry"

    def test_does_not_fire_below_promise_threshold(self):
        # 4.0 is below the [0,10] threshold of 6.0
        assert detect_absence_of_expected("career_entry", 4.0, [], 0.0, 36525.0) is None

    def test_does_not_fire_when_windows_exist(self):
        w = _window(event_class="career_entry")
        # 9.0 is above threshold but windows exist, so should not fire
        assert detect_absence_of_expected("career_entry", 9.0, [w], 0.0, 36525.0) is None


class TestDetectCompression:
    def test_three_distinct_families_within_span_fires(self):
        windows = [
            _window("w1", t_peak=1000, lord_stack=("Saturn",)),
            _window("w2", t_peak=1010, lord_stack=("Jupiter",)),
            _window("w3", t_peak=1020, lord_stack=("Mars",)),
        ]
        results = detect_compression(windows)
        assert len(results) == 1
        assert results[0].insight_type == "compression"
        assert results[0].statement_params["n_families"] == 3

    def test_same_family_repeated_does_not_count_as_distinct(self):
        windows = [
            _window("w1", t_peak=1000, lord_stack=("Saturn",)),
            _window("w2", t_peak=1010, lord_stack=("Saturn",)),  # same family
            _window("w3", t_peak=1020, lord_stack=("Saturn",)),  # same family
        ]
        assert detect_compression(windows) == []

    def test_windows_too_far_apart_do_not_fire(self):
        windows = [
            _window("w1", t_peak=1000, lord_stack=("Saturn",)),
            _window("w2", t_peak=1100, lord_stack=("Jupiter",)),  # 100 days later > 45
            _window("w3", t_peak=1200, lord_stack=("Mars",)),
        ]
        assert detect_compression(windows) == []

    def test_cluster_does_not_double_emit(self):
        # 4 windows, all within a tight span, 4 distinct families -- must
        # emit exactly ONE compression insight, not multiple overlapping ones.
        windows = [
            _window("w1", t_peak=1000, lord_stack=("Saturn",)),
            _window("w2", t_peak=1005, lord_stack=("Jupiter",)),
            _window("w3", t_peak=1010, lord_stack=("Mars",)),
            _window("w4", t_peak=1015, lord_stack=("Venus",)),
        ]
        results = detect_compression(windows)
        assert len(results) == 1


class TestDetectScarcity:
    def test_fires_when_no_further_window_at_all(self):
        current = _window("w1", t_peak=1000)
        cand = detect_scarcity(current, [])
        assert cand is not None
        assert cand.statement_params["next_window_id"] is None

    def test_fires_when_gap_exceeds_five_years(self):
        current = _window("w1", t_peak=1000, t_end=1030)
        far_future = _window("w2", t_peak=1030 + 6 * 365.2425 + 100,
                              t_start=1030 + 6 * 365.2425 + 100 - 30)
        cand = detect_scarcity(current, [far_future])
        assert cand is not None
        assert cand.statement_params["next_window_id"] == "w2"

    def test_does_not_fire_when_next_window_is_soon(self):
        current = _window("w1", t_peak=1000, t_end=1030)
        soon = _window("w2", t_peak=1060, t_start=1040)
        assert detect_scarcity(current, [soon]) is None

    def test_ignores_earlier_windows(self):
        current = _window("w1", t_peak=1000, t_end=1030)
        earlier = _window("w0", t_peak=500, t_start=470, t_end=530)
        cand = detect_scarcity(current, [earlier])
        assert cand is not None  # earlier window must not count as "next"
        assert cand.statement_params["next_window_id"] is None


class TestDetectReversal:
    def test_obstruction_sign_crossing_fires(self):
        carrier = _window("w1")
        # signed_obstruction stays constant (-0.1) so only the lambda-vs-q_e
        # crossing fires: lambda drops from above q_e (0.05 >= 0.03) to
        # below it (0.02 < 0.03).
        samples = [
            ReversalSample(t=100, signed_obstruction=-0.1, lambda_value=0.05, q_e=0.03),
            ReversalSample(t=200, signed_obstruction=-0.1, lambda_value=0.02, q_e=0.03),
        ]
        results = detect_reversal("career_change", carrier, samples)
        assert len(results) == 1  # lambda crossed q_e downward
        assert results[0].statement_params["lambda_crossed"] is True

    def test_no_crossing_no_fire(self):
        carrier = _window("w1")
        samples = [
            ReversalSample(t=100, signed_obstruction=-0.1, lambda_value=0.05, q_e=0.03),
            ReversalSample(t=200, signed_obstruction=-0.2, lambda_value=0.06, q_e=0.03),
        ]
        assert detect_reversal("career_change", carrier, samples) == []

    def test_multiple_crossings_detected(self):
        carrier = _window("w1")
        # Two genuine sign flips: -0.1 -> +0.1 (pair 1), +0.1 -> -0.1 (pair 2).
        # (signed_obstruction is documented as living in (-1, 0] in the real
        # design, but this detector is a pure sign-crossing check that must
        # not special-case the domain -- it works over whatever samples it
        # is given, so a synthetic +/- fixture is a valid probe of the logic.)
        samples = [
            ReversalSample(t=100, signed_obstruction=-0.1, lambda_value=0.05, q_e=0.03),
            ReversalSample(t=200, signed_obstruction=0.1, lambda_value=0.05, q_e=0.03),
            ReversalSample(t=300, signed_obstruction=-0.1, lambda_value=0.05, q_e=0.03),
        ]
        results = detect_reversal("career_change", carrier, samples)
        assert len(results) == 2


class TestDetectContrast:
    def test_fires_above_threshold(self):
        w = _window()
        cand = detect_contrast(w, current_ln_lambda=-2.0, baseline_ln_lambda=-2.6, baseline_label="last_month")
        assert cand is not None
        assert abs(cand.statement_params["delta_ln_lambda"] - 0.6) < 1e-9

    def test_does_not_fire_below_threshold(self):
        w = _window()
        assert detect_contrast(w, -2.0, -2.3, "last_month") is None

    def test_negative_delta_also_fires(self):
        w = _window()
        cand = detect_contrast(w, -3.0, -2.0, "last_year")
        assert cand is not None
        assert cand.statement_params["delta_ln_lambda"] < 0


class TestAssembleInsightRow:
    def test_row_shape_matches_migration_487(self):
        w = _window(clock_agreements=(
            ClockAgreement("vimshottari", "dasha_md", 0.5),
            ClockAgreement("yogini", "dasha_yogini", 0.6),
            ClockAgreement("kalachakra", "dasha_kalachakra", 0.4),
        ))
        cand = detect_concurrence(w)
        row = assemble_insight_row("chart-123", cand, "wv_2026", "snap_abc")
        required_keys = {
            "chart_id", "insight_id", "insight_type", "event_class", "window_id",
            "t_start", "t_end", "statement_key", "statement_params", "fact_ids",
            "cohort_surprise", "cohort_version", "surprise_basis", "robustness",
            "insight_score", "lel_derived", "weights_version", "field_snapshot_id",
        }
        assert required_keys == set(row.keys())
        assert row["insight_id"].startswith("kin_")
        assert row["chart_id"] == "chart-123"

    def test_insight_id_deterministic(self):
        w = _window(clock_agreements=(
            ClockAgreement("vimshottari", "dasha_md", 0.5),
            ClockAgreement("yogini", "dasha_yogini", 0.6),
            ClockAgreement("kalachakra", "dasha_kalachakra", 0.4),
        ))
        cand = detect_concurrence(w)
        row1 = assemble_insight_row("chart-1", cand, "wv1", "snap1")
        row2 = assemble_insight_row("chart-1", cand, "wv1", "snap1")
        assert row1["insight_id"] == row2["insight_id"]

    def test_insight_id_differs_by_chart(self):
        w = _window(clock_agreements=(
            ClockAgreement("vimshottari", "dasha_md", 0.5),
            ClockAgreement("yogini", "dasha_yogini", 0.6),
            ClockAgreement("kalachakra", "dasha_kalachakra", 0.4),
        ))
        cand = detect_concurrence(w)
        row1 = assemble_insight_row("chart-1", cand, "wv1", "snap1")
        row2 = assemble_insight_row("chart-2", cand, "wv1", "snap1")
        assert row1["insight_id"] != row2["insight_id"]

    def test_insight_score_formula(self):
        w = _window(salience=0.8, confidence_tier="calibrated")
        cand = detect_rarity_firing(w, CohortSurpriseInput(p_cohort=0.01, n_cohort=10_000))
        row = assemble_insight_row("chart-1", cand, "wv1", "snap1")
        surprise, _ = compute_cohort_surprise(CohortSurpriseInput(0.01, 10_000))
        expected = surprise * 0.8 * 1.0  # reliability(calibrated) = 1.0
        assert abs(row["insight_score"] - expected) < 1e-12

    def test_absence_of_expected_has_null_window_and_zero_score_components(self):
        # ABSENCE_MIN_PROMISE = 6.0 (grade on [0, 10] scale); 8.0 is above threshold
        cand = detect_absence_of_expected("career_entry", 8.0, [], 0.0, 36525.0)
        row = assemble_insight_row("chart-1", cand, "wv1", "snap1")
        assert row["window_id"] is None
        assert row["event_class"] == "career_entry"


class TestSelectLeadingInsight:
    def test_highest_score_wins(self):
        rows = [
            {"insight_id": "kin_a", "insight_score": 0.3},
            {"insight_id": "kin_b", "insight_score": 0.9},
            {"insight_id": "kin_c", "insight_score": 0.5},
        ]
        leading = select_leading_insight(rows)
        assert leading["insight_id"] == "kin_b"

    def test_tie_break_lower_insight_id_wins(self):
        rows = [
            {"insight_id": "kin_zzz", "insight_score": 0.5},
            {"insight_id": "kin_aaa", "insight_score": 0.5},
        ]
        leading = select_leading_insight(rows)
        assert leading["insight_id"] == "kin_aaa"

    def test_empty_list_returns_none(self):
        assert select_leading_insight([]) is None


class TestSynthesizeInsights:
    """The top-level orchestrator: every optional input is honest-empty by
    default, and every assembled row is lel_derived=False."""

    def test_windows_only_runs_concurrence_and_compression(self):
        windows = [
            _window("w1", t_peak=1000, lord_stack=("Saturn",),
                    clock_agreements=(
                        ClockAgreement("vimshottari", "dasha_md", 0.5),
                        ClockAgreement("yogini", "dasha_yogini", 0.6),
                        ClockAgreement("kalachakra", "dasha_kalachakra", 0.4),
                    )),
            _window("w2", t_peak=1010, lord_stack=("Jupiter",)),
            _window("w3", t_peak=1020, lord_stack=("Mars",)),
        ]
        rows = synthesize_insights("chart-1", windows, "wv1", "snap1")
        types_fired = {r["insight_type"] for r in rows}
        assert "concurrence" in types_fired
        assert "compression" in types_fired
        assert all(r["lel_derived"] is False for r in rows)
        assert all(r["chart_id"] == "chart-1" for r in rows)

    def test_no_inputs_no_windows_returns_empty(self):
        assert synthesize_insights("chart-1", [], "wv1", "snap1") == []

    def test_rarity_firing_wired_via_cohort_by_window(self):
        w = _window("w1")
        rows = synthesize_insights(
            "chart-1", [w], "wv1", "snap1",
            cohort_by_window={"w1": CohortSurpriseInput(p_cohort=0.01, n_cohort=10_000)},
        )
        assert any(r["insight_type"] == "rarity_firing" for r in rows)

    def test_absence_of_expected_wired(self):
        # ABSENCE_MIN_PROMISE = 6.0 (grade on [0, 10] scale); 9.0 is above threshold
        rows = synthesize_insights(
            "chart-1", [], "wv1", "snap1",
            absence_candidates=[("career_entry", 9.0, 0.0, 36525.0)],
        )
        assert len(rows) == 1
        assert rows[0]["insight_type"] == "absence_of_expected"
        assert rows[0]["window_id"] is None

    def test_scarcity_wired(self):
        current = _window("w1", t_peak=1000, t_end=1030)
        rows = synthesize_insights(
            "chart-1", [current], "wv1", "snap1",
            scarcity_pairs=[(current, [])],
        )
        assert any(r["insight_type"] == "scarcity" for r in rows)

    def test_reversal_wired(self):
        carrier = _window("w1")
        samples = [
            ReversalSample(t=100, signed_obstruction=-0.1, lambda_value=0.05, q_e=0.03),
            ReversalSample(t=200, signed_obstruction=-0.1, lambda_value=0.02, q_e=0.03),
        ]
        rows = synthesize_insights(
            "chart-1", [carrier], "wv1", "snap1",
            reversal_inputs=[("career_change", carrier, samples)],
        )
        assert any(r["insight_type"] == "reversal" for r in rows)

    def test_contrast_wired(self):
        carrier = _window("w1")
        rows = synthesize_insights(
            "chart-1", [carrier], "wv1", "snap1",
            contrast_inputs=[(carrier, -2.0, -2.6, "last_month")],
        )
        assert any(r["insight_type"] == "contrast" for r in rows)


# ── Item 33: Absence-of-expected with bodha_pratijna rows (W3 TDD additions) ─


from services.ka_kshetra.stage65_insights import (
    PratijnaRow,
    detect_absence_from_pratijna,
)


class TestPratijnaRow:
    """PratijnaRow is a typed container for a bodha_pratijna DB row slice
    carrying `pratijna_id`, `event_class`, `grade`, and `fact_ids`."""

    def test_pratijna_row_carries_fact_ids(self):
        row = PratijnaRow(
            pratijna_id="p1",
            event_class="marriage",
            grade=0.8,
            fact_ids=("fact_a", "fact_b"),
        )
        assert row.fact_ids == ("fact_a", "fact_b")

    def test_pratijna_row_defaults_fact_ids_empty(self):
        row = PratijnaRow(pratijna_id="p1", event_class="marriage", grade=0.7)
        assert row.fact_ids == ()


class TestDetectAbsenceFromPratijna:
    """
    Item 33 TDD: detect_absence_from_pratijna(
        event_class, pratijna_rows, windows_in_horizon, horizon_start, horizon_end
    ) -> InsightCandidate | None

    Semantics:
    - Fires when the MAXIMUM grade across the pratijna_rows for `event_class`
      exceeds ABSENCE_MIN_PROMISE (6.0 on [0, 10] scale) AND zero windows exist
      for that class in the horizon.
    - The resulting InsightCandidate.fact_ids are the union of all pratijna
      row fact_ids (so the bodha_pratijna provenance rides the row).
    - Does NOT fire when no pratijna rows exist (not expected => absence is not
      "absence of expected").
    - Does NOT fire when promise is below threshold.
    - Does NOT fire when windows exist.
    - Monotonicity property: ceteris paribus, a higher grade (still above
      threshold) never produces a lower `carrier_salience` than a lower grade.

    NOTE: grades are on the bodha_pratijna [0, 10] scale.
    ABSENCE_MIN_PROMISE = 6.0 (the 'promised' floor from bo_pratijna v2.0).
    """

    def _pratijna(self, grade: float, fact_ids=("f1",)):
        return PratijnaRow(
            pratijna_id="p1",
            event_class="marriage",
            grade=grade,
            fact_ids=fact_ids,
        )

    def test_fires_when_strong_promise_no_windows(self):
        # 8.0 is above ABSENCE_MIN_PROMISE (6.0) on [0, 10] scale
        rows = [self._pratijna(8.0)]
        cand = detect_absence_from_pratijna("marriage", rows, [], 0.0, 36525.0)
        assert cand is not None
        assert cand.insight_type == "absence_of_expected"
        assert cand.event_class == "marriage"
        assert cand.window_id is None

    def test_fact_ids_carried_from_pratijna_rows(self):
        # Both rows above 6.0 threshold
        rows = [
            PratijnaRow("p1", "marriage", 8.0, fact_ids=("fact_a",)),
            PratijnaRow("p2", "marriage", 7.5, fact_ids=("fact_b", "fact_c")),
        ]
        cand = detect_absence_from_pratijna("marriage", rows, [], 0.0, 36525.0)
        assert cand is not None
        # All fact_ids from all rows must be present
        assert "fact_a" in cand.fact_ids
        assert "fact_b" in cand.fact_ids
        assert "fact_c" in cand.fact_ids

    def test_does_not_fire_when_no_pratijna_rows(self):
        """No promise at all — absence of irrelevant thing, must not fire."""
        cand = detect_absence_from_pratijna("marriage", [], [], 0.0, 36525.0)
        assert cand is None

    def test_does_not_fire_below_promise_threshold(self):
        # 4.0 is below ABSENCE_MIN_PROMISE (6.0)
        rows = [self._pratijna(4.0)]
        assert detect_absence_from_pratijna("marriage", rows, [], 0.0, 36525.0) is None

    def test_does_not_fire_when_windows_exist(self):
        # 9.0 is above threshold but windows exist, so should not fire
        rows = [self._pratijna(9.0)]
        w = _window(event_class="marriage")
        assert detect_absence_from_pratijna("marriage", rows, [w], 0.0, 36525.0) is None

    def test_uses_max_grade_across_multiple_rows(self):
        """Even if one row is below threshold, if another is above, it fires."""
        rows = [
            self._pratijna(3.0),   # below threshold (6.0)
            self._pratijna(8.5),   # above threshold
        ]
        cand = detect_absence_from_pratijna("marriage", rows, [], 0.0, 36525.0)
        assert cand is not None

    def test_grade_exactly_at_threshold_fires(self):
        """p_e == ABSENCE_MIN_PROMISE (6.0): just at boundary, must fire."""
        rows = [self._pratijna(6.0)]
        cand = detect_absence_from_pratijna("marriage", rows, [], 0.0, 36525.0)
        assert cand is not None

    def test_grade_just_below_threshold_does_not_fire(self):
        # 5.999 is just below ABSENCE_MIN_PROMISE (6.0)
        rows = [self._pratijna(5.999)]
        assert detect_absence_from_pratijna("marriage", rows, [], 0.0, 36525.0) is None

    def test_monotonicity_higher_grade_never_lower_salience(self):
        """Property: for two above-threshold grades g1 < g2, salience(g1) <= salience(g2)."""
        # Both grades above 6.0; g1 < g2
        g1, g2 = 6.5, 9.5
        cand1 = detect_absence_from_pratijna("marriage", [self._pratijna(g1)], [], 0.0, 36525.0)
        cand2 = detect_absence_from_pratijna("marriage", [self._pratijna(g2)], [], 0.0, 36525.0)
        assert cand1 is not None and cand2 is not None
        assert cand1.carrier_salience <= cand2.carrier_salience

    def test_statement_params_carry_max_grade(self):
        # 8.0 is above ABSENCE_MIN_PROMISE (6.0)
        rows = [self._pratijna(8.0)]
        cand = detect_absence_from_pratijna("marriage", rows, [], 0.0, 36525.0)
        assert cand is not None
        assert abs(cand.statement_params["p_e"] - 8.0) < 1e-9


# ── Item 34: Contrastive field-diff for kala_explain_get (W3 TDD additions) ──


from services.ka_kshetra.stage65_insights import (
    FieldSnapshot,
    compute_field_diff,
)


class TestFieldSnapshot:
    """FieldSnapshot is a lightweight container representing a set of field
    windows at a given point in time — used as the baseline for contrast."""

    def test_field_snapshot_stores_windows_by_id(self):
        w1 = _window("wA", event_class="career_change")
        snap = FieldSnapshot(snapshot_label="last_month", windows=[w1])
        assert "wA" in snap.windows_by_id

    def test_field_snapshot_empty_is_valid(self):
        snap = FieldSnapshot(snapshot_label="baseline", windows=[])
        assert snap.windows_by_id == {}


class TestComputeFieldDiff:
    """
    Item 34 TDD: compute_field_diff(
        current_windows, baseline_snapshot, lambda_threshold=0.5
    ) -> dict with keys:
      new_windows, closed_windows, intensified_windows, weakened_windows

    Each value is a list of dicts carrying at minimum:
      window_id, event_class, fact_ids, (and delta_ln_lambda where applicable)

    Properties:
    - new_windows: window_ids present in current but absent from baseline.
    - closed_windows: window_ids present in baseline but absent from current.
    - intensified_windows: window_ids present in both, with
        current.lambda_peak / baseline.lambda_peak > exp(lambda_threshold).
    - weakened_windows: window_ids present in both, with
        baseline.lambda_peak / current.lambda_peak > exp(lambda_threshold).
    - contrast(A, B).new_windows == contrast(B_as_snap_of(A), current=B).closed_windows
      (anti-symmetry of new/closed).
    """

    def _snap(self, label, windows):
        return FieldSnapshot(snapshot_label=label, windows=windows)

    def test_new_window_detected(self):
        current = [_window("w_new", event_class="career_change")]
        baseline = self._snap("last_month", [])
        diff = compute_field_diff(current, baseline)
        ids = {r["window_id"] for r in diff["new_windows"]}
        assert "w_new" in ids

    def test_closed_window_detected(self):
        w_old = _window("w_old", event_class="career_change")
        current = []
        baseline = self._snap("last_month", [w_old])
        diff = compute_field_diff(current, baseline)
        ids = {r["window_id"] for r in diff["closed_windows"]}
        assert "w_old" in ids

    def test_intensified_window_detected(self):
        # current lambda_peak significantly higher than baseline
        # We'll use a window with the same id but supply baseline separately.
        # lambda_peak in _window is 0.05; override via direct InsightWindow.
        from services.ka_kshetra.stage65_insights import InsightWindow
        w_current = InsightWindow(
            window_id="w1", event_class="career_change",
            t_start=970.0, t_end=1030.0, t_peak=1000.0, lambda_peak=0.20,
            salience=0.8, confidence_tier="concurrent",
        )
        w_baseline = InsightWindow(
            window_id="w1", event_class="career_change",
            t_start=970.0, t_end=1030.0, t_peak=1000.0, lambda_peak=0.05,
            salience=0.5, confidence_tier="concurrent",
        )
        baseline = self._snap("last_month", [w_baseline])
        diff = compute_field_diff([w_current], baseline)
        ids = {r["window_id"] for r in diff["intensified_windows"]}
        assert "w1" in ids
        assert diff["new_windows"] == []
        assert diff["closed_windows"] == []

    def test_weakened_window_detected(self):
        from services.ka_kshetra.stage65_insights import InsightWindow
        w_current = InsightWindow(
            window_id="w1", event_class="career_change",
            t_start=970.0, t_end=1030.0, t_peak=1000.0, lambda_peak=0.02,
            salience=0.3, confidence_tier="structural_prior",
        )
        w_baseline = InsightWindow(
            window_id="w1", event_class="career_change",
            t_start=970.0, t_end=1030.0, t_peak=1000.0, lambda_peak=0.15,
            salience=0.7, confidence_tier="concurrent",
        )
        baseline = self._snap("last_month", [w_baseline])
        diff = compute_field_diff([w_current], baseline)
        ids = {r["window_id"] for r in diff["weakened_windows"]}
        assert "w1" in ids

    def test_no_change_window_not_in_any_diff_list(self):
        """Window with same id and nearly identical lambda stays out of all lists."""
        from services.ka_kshetra.stage65_insights import InsightWindow
        w_same = InsightWindow(
            window_id="w1", event_class="career_change",
            t_start=970.0, t_end=1030.0, t_peak=1000.0, lambda_peak=0.05,
            salience=0.5, confidence_tier="concurrent",
        )
        baseline = self._snap("last_month", [
            InsightWindow(
                window_id="w1", event_class="career_change",
                t_start=970.0, t_end=1030.0, t_peak=1000.0, lambda_peak=0.05,
                salience=0.5, confidence_tier="concurrent",
            )
        ])
        diff = compute_field_diff([w_same], baseline)
        assert diff["new_windows"] == []
        assert diff["closed_windows"] == []
        assert diff["intensified_windows"] == []
        assert diff["weakened_windows"] == []

    def test_diff_row_carries_fact_ids(self):
        w_new = _window("w_new", event_class="marriage", fact_ids=("f1", "f2"))
        baseline = self._snap("last_month", [])
        diff = compute_field_diff([w_new], baseline)
        row = next(r for r in diff["new_windows"] if r["window_id"] == "w_new")
        assert "f1" in row["fact_ids"]
        assert "f2" in row["fact_ids"]

    def test_antisymmetry_new_closed(self):
        """Anti-symmetry: new in A→B === closed in B→A (for the same windows)."""
        from services.ka_kshetra.stage65_insights import InsightWindow
        wA = InsightWindow(
            window_id="wA", event_class="career_change",
            t_start=970.0, t_end=1030.0, t_peak=1000.0, lambda_peak=0.05,
            salience=0.5, confidence_tier="concurrent",
        )
        wB = InsightWindow(
            window_id="wB", event_class="career_change",
            t_start=970.0, t_end=1030.0, t_peak=1000.0, lambda_peak=0.05,
            salience=0.5, confidence_tier="concurrent",
        )
        diff_AtoB = compute_field_diff([wB], self._snap("snap_a", [wA]))
        diff_BtoA = compute_field_diff([wA], self._snap("snap_b", [wB]))
        new_ids_AtoB = {r["window_id"] for r in diff_AtoB["new_windows"]}
        closed_ids_BtoA = {r["window_id"] for r in diff_BtoA["closed_windows"]}
        assert new_ids_AtoB == closed_ids_BtoA

    def test_all_diff_keys_present_even_when_empty(self):
        diff = compute_field_diff([], self._snap("empty", []))
        assert set(diff.keys()) >= {"new_windows", "closed_windows", "intensified_windows", "weakened_windows"}
