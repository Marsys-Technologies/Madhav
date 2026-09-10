"""MR-14 — term_breakdown production wiring (interval_solver level).

PARIṢKĀRA remediation register, PG-6/PG-7, recon W1.5.

GAP (before this fix): `services.gochara_v3.engine._evaluate_single_from_context`
already computes the full W1.5 λ_v3 decomposition on every non-v1-parity
`IntensityResult` (`term_breakdown`, `lambda_v3_ci_low`, `lambda_v3_ci_high`,
`ci_source` — see `test_lambda_decomposition.py` AC1-AC6). But
`interval_solver.find_threshold_crossings` — the function that actually
produces the `IntervalBoundary` objects the century-materialize writer turns
into rows — discarded that decomposition entirely: every call site in the
coarse sweep, the bisection root-solver, and the dense peak search used
`_eval_single`, which returns a bare `float` (`raw_lambda`) and nothing else.
`IntervalBoundary` itself never had a field to carry a decomposition in even
if one had been computed. This is why every gen-3.0 row in `kala_gochara_windows`
was disclosed with `term_breakdown` NULL on 120/120 rows (PARISHKARA_LEDGER,
2026-08-11 ~05:2x IST baseline) despite the engine underneath being correct —
the wiring between engine and interval-boundary output was the actual gap,
not the engine's own W1.5 computation (confirmed via `_eval_single_full`,
which already existed and already returns the full `IntensityResult`, but was
only ever called from `score_chain_milestones`, never from
`find_threshold_crossings`).

FIX: `find_threshold_crossings` now calls `_eval_single_full` once more at
each detected interval's `peak_jd` (one extra call per DETECTED interval, not
per coarse/bisection/dense-sampling point) and carries the resulting
`term_breakdown`/`lambda_v3_ci_low`/`lambda_v3_ci_high`/`ci_source` onto the
new `IntervalBoundary` fields. Honest None on an I4 evaluation failure at
peak_jd — never a fabricated breakdown.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.gochara_v3.interval_solver import (
    ERA_SLICE_KEY_V3,
    IntervalBoundary,
    find_threshold_crossings,
)
from services.gochara_v3.threshold import ThresholdConfig

_BASE_JD = 2461042.0


def _make_threshold_config(lambda_thresh: float = 0.30) -> ThresholdConfig:
    return ThresholdConfig(
        percentile_used=0.80,
        lambda_thresh=lambda_thresh,
        implied_density=10.0,
        base_rate_cited=0.20,
        age_band_used="band_41_60",
        density_flag="ok",
        fallback_used=False,
        sample_count=5200,
    )


def _make_mock_context():
    ctx = MagicMock()
    ctx.event_class = "marriage"
    ctx.chart_id = "test-chart-id"
    return ctx


_SAMPLE_TERM_BREAKDOWN = {
    "promise": 0.6,
    "permission": 0.5,
    "activity": 0.7,
    "quality_gates": 1.0,
    "lambda_v3": 0.21,
    "activity_terms": [
        {"primitive": "degree_contact", "target_ref": "graha:venus",
         "orb_decay": 0.9, "target_weight": 0.8, "p_i": 0.72},
    ],
    "formula": "PROMISE × PERMISSION × activity × quality_gates",
}


def _make_mock_intensity_result(
    raw_lambda: float,
    jd: float,
    *,
    term_breakdown=None,
    ci_low=None,
    ci_high=None,
    ci_source=None,
):
    """Build a mock IntensityResult carrying the full W1.5 decomposition,
    mirroring what services.gochara_v3.engine._evaluate_single_from_context
    actually produces on a v3 (non-parity) evaluation."""
    result = MagicMock()
    result.raw_lambda = raw_lambda
    result.t_jd = jd
    result.term_breakdown = term_breakdown
    result.lambda_v3_ci_low = ci_low
    result.lambda_v3_ci_high = ci_high
    result.ci_source = ci_source
    return result


def _make_evaluate_lambda_vector_side_effect(lambda_fn, *, decompose_fn=None):
    """side_effect for mocking evaluate_lambda_vector.

    lambda_fn(jd) -> float: the raw_lambda value at a given JD.
    decompose_fn(jd) -> dict | None: if given, the term_breakdown to attach
    at that JD (mirrors the real engine attaching a decomposition to EVERY
    result, not just the ones a caller happens to read closely).
    """
    def side_effect(swe, context, jd_array, v1_parity_mode=False, **kwargs):
        results = []
        for jd in jd_array:
            jd_f = float(jd)
            lam = lambda_fn(jd_f)
            tb = decompose_fn(jd_f) if decompose_fn is not None else None
            results.append(_make_mock_intensity_result(
                lam, jd_f,
                term_breakdown=tb,
                ci_low=max(0.0, lam * 0.8) if tb is not None else None,
                ci_high=min(1.0, lam * 1.2) if tb is not None else None,
                ci_source="structural_prior" if tb is not None else None,
            ))
        return results
    return side_effect


class TestTermBreakdownWiring:
    """IntervalBoundary must carry the peak's full W1.5 decomposition."""

    def test_interval_boundary_carries_term_breakdown_at_peak(self):
        """A detected interval's IntervalBoundary.term_breakdown must be the
        REAL decomposition dict the engine produced at peak_jd — not None,
        and not the coarse-sweep/bisection float-only value."""
        base_jd = _BASE_JD
        threshold_config = _make_threshold_config(lambda_thresh=0.30)
        context = _make_mock_context()
        swe = MagicMock()

        def lambda_fn(jd: float) -> float:
            day_offset = jd - base_jd
            if 5.0 <= day_offset <= 15.0:
                return 0.80
            return 0.05

        def decompose_fn(jd: float) -> dict:
            # Every live evaluation carries a decomposition (mirrors the real
            # engine, which always populates term_breakdown on a v3 result).
            return dict(_SAMPLE_TERM_BREAKDOWN)

        with patch(
            "services.gochara_v3.interval_solver.evaluate_lambda_vector",
            side_effect=_make_evaluate_lambda_vector_side_effect(
                lambda_fn, decompose_fn=decompose_fn,
            ),
        ):
            intervals = find_threshold_crossings(
                swe, context,
                start_jd=base_jd,
                end_jd=base_jd + 30.0,
                threshold_config=threshold_config,
                coarse_step_days=1.0,
                bisect_tol_days=0.1,
            )

        assert len(intervals) == 1
        iv = intervals[0]

        assert iv.term_breakdown is not None, (
            "IntervalBoundary.term_breakdown must be populated when the "
            "engine's peak-JD evaluation succeeds and carries a decomposition "
            "— this is the exact PG-6/PG-7 defect (term_breakdown never "
            "produced) this fix closes."
        )
        assert iv.term_breakdown == _SAMPLE_TERM_BREAKDOWN
        assert set(iv.term_breakdown.keys()) == {
            "promise", "permission", "activity", "quality_gates",
            "lambda_v3", "activity_terms", "formula",
        }, "term_breakdown must carry the migration-564-documented shape"

    def test_interval_boundary_carries_ci_fields_at_peak(self):
        """lambda_v3_ci_low/high and ci_source must also survive onto the
        IntervalBoundary (the same W1.5 output model, migration 559/564)."""
        base_jd = _BASE_JD
        threshold_config = _make_threshold_config(lambda_thresh=0.30)
        context = _make_mock_context()
        swe = MagicMock()

        def lambda_fn(jd: float) -> float:
            day_offset = jd - base_jd
            if 5.0 <= day_offset <= 15.0:
                return 0.80
            return 0.05

        def decompose_fn(jd: float) -> dict:
            return dict(_SAMPLE_TERM_BREAKDOWN)

        with patch(
            "services.gochara_v3.interval_solver.evaluate_lambda_vector",
            side_effect=_make_evaluate_lambda_vector_side_effect(
                lambda_fn, decompose_fn=decompose_fn,
            ),
        ):
            intervals = find_threshold_crossings(
                swe, context,
                start_jd=base_jd,
                end_jd=base_jd + 30.0,
                threshold_config=threshold_config,
                coarse_step_days=1.0,
                bisect_tol_days=0.1,
            )

        assert len(intervals) == 1
        iv = intervals[0]
        assert iv.ci_source == "structural_prior"
        assert iv.lambda_v3_ci_low is not None
        assert iv.lambda_v3_ci_high is not None
        assert iv.lambda_v3_ci_low <= iv.peak_lambda <= iv.lambda_v3_ci_high or (
            # peak_lambda comes from the dense-sample float path and
            # lambda_v3_ci_* comes from the separate peak-JD full
            # evaluation; both are honest reads of the same mocked
            # function at (approximately) the same jd, so they should
            # agree closely, not necessarily bit-for-bit.
            abs(iv.lambda_v3_ci_low - max(0.0, iv.peak_lambda * 0.8)) < 1e-6
        )

    def test_interval_boundary_term_breakdown_honestly_none_on_eval_failure(self):
        """I4: if the peak-JD full evaluation fails (engine raises / returns
        nothing), term_breakdown must be None — never a fabricated dict, and
        the interval itself must still be reported (peak_lambda came from a
        separate, successful bare-float evaluation)."""
        base_jd = _BASE_JD
        threshold_config = _make_threshold_config(lambda_thresh=0.30)
        context = _make_mock_context()
        swe = MagicMock()

        def lambda_fn(jd: float) -> float:
            day_offset = jd - base_jd
            if 5.0 <= day_offset <= 15.0:
                return 0.80
            return 0.05

        # The coarse sweep / bisection / dense peak search all go through
        # `_eval_single` (bare float, via evaluate_lambda_vector) and must
        # keep succeeding normally so the interval is still found. Only the
        # SEPARATE full-decomposition evaluation this fix adds
        # (`_eval_single_full`, called once per detected interval at
        # peak_jd) is made to fail here, simulating a transient engine
        # exception at that specific call.
        with patch(
            "services.gochara_v3.interval_solver.evaluate_lambda_vector",
            side_effect=_make_evaluate_lambda_vector_side_effect(lambda_fn),
        ), patch(
            "services.gochara_v3.interval_solver._eval_single_full",
            return_value=None,
        ):
            intervals = find_threshold_crossings(
                swe, context,
                start_jd=base_jd,
                end_jd=base_jd + 30.0,
                threshold_config=threshold_config,
                coarse_step_days=1.0,
                bisect_tol_days=0.1,
            )

        assert len(intervals) == 1, "the interval must still be detected/reported"
        iv = intervals[0]
        assert iv.term_breakdown is None
        assert iv.lambda_v3_ci_low is None
        assert iv.lambda_v3_ci_high is None
        assert iv.ci_source is None
        # peak_lambda itself must still be honest (from the successful
        # bare-float sweep), not silently zeroed by the failed full-eval.
        assert iv.peak_lambda == pytest.approx(0.80, abs=0.05)


__all__ = ["TestTermBreakdownWiring"]
