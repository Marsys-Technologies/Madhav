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
        cand = detect_absence_of_expected("career_entry", 0.75, [], 0.0, 36525.0)
        assert cand is not None
        assert cand.window_id is None
        assert cand.event_class == "career_entry"

    def test_does_not_fire_below_promise_threshold(self):
        assert detect_absence_of_expected("career_entry", 0.4, [], 0.0, 36525.0) is None

    def test_does_not_fire_when_windows_exist(self):
        w = _window(event_class="career_entry")
        assert detect_absence_of_expected("career_entry", 0.9, [w], 0.0, 36525.0) is None


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
        cand = detect_absence_of_expected("career_entry", 0.8, [], 0.0, 36525.0)
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
        rows = synthesize_insights(
            "chart-1", [], "wv1", "snap1",
            absence_candidates=[("career_entry", 0.9, 0.0, 36525.0)],
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
