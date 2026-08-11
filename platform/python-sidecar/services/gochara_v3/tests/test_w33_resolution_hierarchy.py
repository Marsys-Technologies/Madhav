"""
Test W3.3/PK-R-8 — Multi-resolution window hierarchy, peak-anchored (not tiled).

ADJUDICATOR ruling PK-R-8 replaced the original W3.3 fixed-step tiling design
(build_month_windows/build_day_windows, midpoint-sampled "peaks") with
PEAK-ANCHORING. This file is the R8-compliant test suite; the pre-PK-R-8
tiling tests (era/month duration classification, MONTH_STEP_DAYS/DAY_STEP_DAYS
subdivision) are REMOVED per R8.1 ("remove build_month_windows/build_day_
windows/MONTH_STEP_DAYS/DAY_STEP_DAYS + their tests").

Covers:
  R8.1  No tiling symbols remain; no midpoint-peak source pattern anywhere
        under services/gochara_v3/.
  R8.2  Peak scan reuses the coarse series find_threshold_crossings already
        computes (return_series=True) — no re-sweep; local-maxima detection
        on a synthetic multi-bump curve.
  R8.3  Admission = P90 of the era window's OWN coarse series, never
        lambda_thresh; flat curve admits nothing.
  R8.4  Retention: rank + greedy separation + cap; deterministic on ties.
  R8.5  Day refinement finds the TRUE argmax, not the coarse candidate.
  R8.6  Exactly one month + one day row per retained peak; zero peaks ->
        zero month/day rows (era-only).
  R8.7  Anti-explosion: a realistic-shaped multi-year era window does not
        explode into more than the closed-form row bound.

All tests mock find_threshold_crossings/_eval_single from interval_solver to
avoid DB/ephemeris calls. DB-free.
"""
from __future__ import annotations

import inspect
import uuid
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from services.gochara_v3 import resolution_hierarchy as rh
from services.gochara_v3.resolution_hierarchy import (
    RESOLUTION_TIERS,
    PEAK_SCAN_STRIDE_DAYS,
    ADMISSION_PERCENTILE,
    MIN_PEAK_SEPARATION_DAYS,
    MAX_PEAKS_PER_ERA_WINDOW,
    ZERO_PEAKS_ERA_WINDOW_TOO_SHORT,
    ZERO_PEAKS_FLAT_LAMBDA_CURVE,
    ZERO_PEAKS_NO_CANDIDATE_ABOVE_P90,
    ZERO_PEAKS_LOST_TO_POOLED_RETENTION,
    WindowResolutionRecord,
    PeakCandidate,
    HierarchyResult,
    assign_parent_window_ids,
    find_local_maxima,
    admit_candidates,
    retain_candidates,
    retain_candidates_pooled,
    refine_peak_to_day,
    build_peak_anchored_windows,
    build_era_windows,
    build_resolution_hierarchy,
)
from services.gochara_v3.interval_solver import IntervalBoundary, ERA_SLICE_KEY_V3
from services.gochara_v3.threshold import ThresholdConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# _jd_to_pydate assumes a JD near the modern calendar (epoch JD 2440588.0 =
# 1970-01-01); a raw 0.0-based JD underflows Python's date range. Tests that
# feed synthetic JDs through the month/day-row construction path (anything
# that reaches _calendar_month_bounds_jd) must anchor their series at a
# REALISTIC JD, not 0.0. Matches the writer's own BIRTH_JD convention.
_BASE_JD = 2445736.5  # 1984-02-05 (native birth date, same anchor the writer uses)


def _honest_eval_bound(span_days: float, era_window_count: int, peaks_retained: int) -> float:
    """PARĪKṢAKA F-1 (2026-08-11): the honest _eval_single call-count bound
    for one build_resolution_hierarchy call, replacing the old vacuous
    `span/7 + 15000` (see test_peak_scan_reuses_coarse_series' own
    docstring for the full rationale). Three named, documented components —
    none of them re-implement interval_solver's own bisection/dense-scan
    logic, they just budget generously for it:
      1. ONE full-range coarse sweep (ceil(span/PEAK_SCAN_STRIDE_DAYS) + 5
         slack for arange-edge rounding) — the single pass find_threshold_
         crossings itself makes, which R8.2 requires downstream peak-
         anchoring to REUSE rather than re-sweep.
      2. `_BISECT_AND_DENSE_SCAN_BUDGET` (100) per era window — covers each
         interval's own enter/exit bisection (~15 iterations x 2 crossings,
         generous given interval_solver's 0.1-day tolerance over a 7-day
         coarse step) plus its 50-sample dense peak scan plus slack.
      3. `_REFINEMENT_BUDGET` (20) per retained peak — refine_peak_to_day's
         own exact cost is 16 calls (int(round(2*7/1))+2); budgeted with
         slack.
    """
    import math
    _BISECT_AND_DENSE_SCAN_BUDGET = 100
    _REFINEMENT_BUDGET = 20
    _COARSE_SWEEP_SLACK = 5
    return (
        math.ceil(span_days / PEAK_SCAN_STRIDE_DAYS) + _COARSE_SWEEP_SLACK
        + era_window_count * _BISECT_AND_DENSE_SCAN_BUDGET
        + peaks_retained * _REFINEMENT_BUDGET
    )


def _make_threshold_config(lambda_thresh: float = 0.5) -> ThresholdConfig:
    return ThresholdConfig(
        percentile_used=0.90,
        lambda_thresh=lambda_thresh,
        implied_density=1.0,
        base_rate_cited=0.10,
        age_band_used="band_41_60",
        density_flag="ok",
        fallback_used=False,
        sample_count=100,
    )


def _make_window(
    tier: str, enter_jd: float, exit_jd: float,
    peak_jd: float = None, peak_lambda: float = 0.7,
    window_id: str = None, parent_window_id: str = None,
) -> WindowResolutionRecord:
    if peak_jd is None:
        peak_jd = 0.5 * (enter_jd + exit_jd)
    if window_id is None:
        window_id = str(uuid.uuid4())
    return WindowResolutionRecord(
        window_id=window_id, parent_window_id=parent_window_id,
        resolution_tier=tier, enter_jd=enter_jd, exit_jd=exit_jd,
        peak_jd=peak_jd, peak_lambda=peak_lambda,
    )


def _make_interval(
    enter_jd: float, exit_jd: float, peak_jd: float = None, peak_lambda: float = 0.8,
    term_breakdown: dict = None, lambda_v3_ci_low: float = None,
    lambda_v3_ci_high: float = None, ci_source: str = None,
) -> IntervalBoundary:
    if peak_jd is None:
        peak_jd = 0.5 * (enter_jd + exit_jd)
    return IntervalBoundary(
        enter_jd=enter_jd, exit_jd=exit_jd, peak_jd=peak_jd, peak_lambda=peak_lambda,
        era_slice_key=ERA_SLICE_KEY_V3, term_breakdown=term_breakdown,
        lambda_v3_ci_low=lambda_v3_ci_low, lambda_v3_ci_high=lambda_v3_ci_high,
        ci_source=ci_source,
    )


# ---------------------------------------------------------------------------
# R8.1 — no tiling symbols remain, no midpoint-peak source pattern
# ---------------------------------------------------------------------------

class TestR81NoTiling:
    def test_no_tiling_symbols_remain(self):
        """R8.1: build_month_windows/build_day_windows/MONTH_STEP_DAYS/
        DAY_STEP_DAYS must not exist on the module at all."""
        assert not hasattr(rh, "build_month_windows")
        assert not hasattr(rh, "build_day_windows")
        assert not hasattr(rh, "MONTH_STEP_DAYS")
        assert not hasattr(rh, "DAY_STEP_DAYS")

    def test_no_midpoint_peak_source_pattern_under_gochara_v3(self):
        """R8.1 source guard: the exact tiler midpoint-peak-assignment
        expression must not appear anywhere under services/gochara_v3/
        (NOT a ban on all '0.5 * (' — interval_solver.py's bisection
        convergence midpoint is a different, legitimate pattern and must
        NOT be flagged)."""
        import pathlib
        gochara_v3_dir = pathlib.Path(rh.__file__).parent
        offenders = []
        for py_file in gochara_v3_dir.rglob("*.py"):
            if "tests" in py_file.parts:
                continue
            text = py_file.read_text(encoding="utf-8")
            if "0.5 * (step_enter + step_exit)" in text:
                offenders.append(str(py_file))
        assert offenders == [], (
            f"R8.1 VIOLATION: midpoint-peak tiling pattern found in: {offenders}"
        )


# ---------------------------------------------------------------------------
# R8.2 — peak scan reuses the coarse series; local-maxima detection
# ---------------------------------------------------------------------------

class TestR82PeakScanReusesSeries:
    def test_local_maxima_on_synthetic_curve(self):
        """A 3-bump synthetic curve produces exactly 3 candidates, at the
        known JDs of each bump's true peak."""
        jds = np.arange(0.0, 300.0, 7.0)

        def curve(jd: float) -> float:
            # Three triangular bumps centered at 50, 150, 250.
            val = 0.1
            for center in (50.0, 150.0, 250.0):
                val = max(val, 0.9 - abs(jd - center) * 0.02)
            return val

        lambdas = np.array([curve(jd) for jd in jds])
        candidates = find_local_maxima(jds, lambdas)

        # Each bump's coarse-grid-nearest point should be a candidate.
        assert len(candidates) == 3, (
            f"expected exactly 3 local-maxima candidates, got {len(candidates)}: "
            f"{[(c.jd, c.lam) for c in candidates]}"
        )
        found_jds = sorted(c.jd for c in candidates)
        for expected_center, found_jd in zip((50.0, 150.0, 250.0), found_jds):
            assert abs(found_jd - expected_center) <= PEAK_SCAN_STRIDE_DAYS, (
                f"candidate at {found_jd} not within one stride of bump center {expected_center}"
            )

    def test_local_maxima_empty_on_flat_series(self):
        jds = np.arange(0.0, 100.0, 7.0)
        lambdas = np.full(len(jds), 0.5)
        assert find_local_maxima(jds, lambdas) == []

    def test_local_maxima_endpoint_only_if_strictly_exceeds_neighbour(self):
        jds = np.array([0.0, 7.0, 14.0])
        # Monotonically increasing: index 2 (endpoint) strictly exceeds its
        # single neighbour -> admitted. Index 0 does NOT exceed its neighbour
        # (it's lower) -> not admitted.
        lambdas = np.array([0.1, 0.5, 0.9])
        candidates = find_local_maxima(jds, lambdas)
        assert len(candidates) == 1
        assert candidates[0].jd == 14.0

    def test_peak_scan_reuses_coarse_series(self, monkeypatch):
        """R8.2: total _eval_single calls across one build_resolution_
        hierarchy call stay within the reused-series bound — proof that
        peak-anchoring does not re-sweep the era window.

        PARĪKṢAKA F-1 (2026-08-11): the original bound was `span/7 + 15000`
        — at this test's span (3,650d) that's ~15,521, roughly 20x the real
        observed cost (~762 calls), so loose it would pass unchanged even
        under a per-era-window full re-sweep. Tightened to HONEST arithmetic
        built from this module's own named constants (no re-derivation of
        interval_solver's exact bisection/dense-scan cost — that would just
        be a second implementation of the thing under test — instead a
        documented, generous-but-far-tighter-than-15000 per-unit budget):
          coarse sweep   ceil(span / PEAK_SCAN_STRIDE_DAYS) + slack — the
                         one full-range coarse pass find_threshold_crossings
                         itself makes (R8.2's own "reuse this, don't re-sweep
                         it" series).
          per era window _BISECT_AND_DENSE_SCAN_BUDGET — covers each
                         interval's enter/exit bisection (interval_solver's
                         own _BISECT_TOL_DAYS=0.1 tolerance over a 7-day
                         coarse step converges in ~7 iterations; budgeted at
                         15 x2 crossings = 30) plus its 50-sample dense peak
                         scan (interval_solver's own _PEAK_SAMPLE_COUNT) plus
                         slack for _eval_single_full's own peak read — a
                         documented 100, comfortably above the ~80 actually
                         observed per era window in this fixture.
          per retained
          peak           _REFINEMENT_BUDGET — refine_peak_to_day's own EXACT
                         cost is int(round(2*DAY_REFINEMENT_HALF_WINDOW_DAYS/
                         DAY_REFINEMENT_STEP_DAYS)) + 2 == 16 calls; budgeted
                         at 20 for slack.
        At this test's span (3,650d, 3 era windows, 3 retained peaks) this
        formula evaluates to ~887 — the real observed count (762) clears it
        with a ~16% margin, not a ~20x one, so a per-era-window re-sweep
        (which would add roughly one more full-span coarse pass PER era
        window, ~521 calls each — see test_peak_scan_detects_resweep_
        mutation below) blows straight through it."""
        from services.gochara_v3 import interval_solver as isolver

        call_count = {"n": 0}
        span_days = 3650.0  # ~10 years, matches a real decade slice
        start_jd = _BASE_JD

        def curve(jd: float) -> float:
            val = 0.3
            for center in (start_jd + 500.0, start_jd + 1800.0, start_jd + 3000.0):
                val = max(val, 0.95 - abs(jd - center) * 0.01)
            return val

        def counting_eval(swe, context, jd):
            call_count["n"] += 1
            return curve(float(jd))

        monkeypatch.setattr(isolver, "_eval_single", counting_eval)
        monkeypatch.setattr(rh, "_eval_single", counting_eval)

        config = _make_threshold_config(lambda_thresh=0.5)
        result = build_resolution_hierarchy(MagicMock(), MagicMock(), start_jd, start_jd + span_days, config)

        bound = _honest_eval_bound(span_days, result.era_window_count, result.peaks_retained)
        assert call_count["n"] <= bound, (
            f"R8.2 VIOLATION: {call_count['n']} eval calls exceeds the reused-series "
            f"bound {bound} — peak-anchoring appears to be re-sweeping instead of "
            f"reusing the coarse series."
        )
        # Sanity: this scenario is non-trivial (real windows were produced),
        # and the bound is genuinely tight (not another 15000-style no-op) —
        # observed count must clear >=50% of the bound's slack margin, or
        # the fixture itself has drifted loose again.
        assert result.era_window_count >= 1
        assert call_count["n"] >= bound * 0.5, (
            f"fixture regression: observed count {call_count['n']} is suspiciously "
            f"far below bound {bound} — the bound may have drifted loose again"
        )

    def test_peak_scan_detects_resweep_mutation(self, monkeypatch):
        """Companion RED case: a hypothetical implementation that re-sweeps
        the FULL requested range once per era window (instead of reusing the
        already-computed series) blows the SAME tightened bound this file's
        primary detector checks — proving that formula is a real detector,
        not a vacuous always-true bound.

        PARĪKṢAKA F-1 (2026-08-11): the original companion test used an
        artificial 200,000-day span specifically chosen so that span/7 alone
        (~28,571) already dwarfed the old loose bound's fixed +15000 slack —
        i.e. it proved the OLD bound's arithmetic could be exceeded at an
        unrealistic scale, not that it discriminates at a REAL production
        span. Fixed: this test now uses the SAME realistic span (3,650d) and
        SAME curve as the primary detector above, so it exercises the exact
        bound formula and scenario the primary test uses — proving the
        TIGHTENED bound (not some other, looser one) is what catches the
        mutation."""
        from services.gochara_v3 import interval_solver as isolver

        call_count = {"n": 0}
        span_days = 3650.0  # SAME span as the primary detector, on purpose
        start_jd = _BASE_JD

        def curve(jd: float) -> float:
            val = 0.3
            for center in (start_jd + 500.0, start_jd + 1800.0, start_jd + 3000.0):
                val = max(val, 0.95 - abs(jd - center) * 0.01)
            return val

        def counting_eval(swe, context, jd):
            call_count["n"] += 1
            return curve(float(jd))

        monkeypatch.setattr(isolver, "_eval_single", counting_eval)
        monkeypatch.setattr(rh, "_eval_single", counting_eval)

        config = _make_threshold_config(lambda_thresh=0.5)

        # First, the REAL (reuse-based) call — establishes the honest count
        # AND the era_window_count a per-era-window re-sweep bug would loop
        # over.
        call_count["n"] = 0
        honest_result = build_resolution_hierarchy(
            MagicMock(), MagicMock(), start_jd, start_jd + span_days, config,
        )
        honest_count = call_count["n"]

        # Now simulate the mutation literally: what a "re-sweep instead of
        # reuse" bug would do is call find_threshold_crossings AGAIN, once
        # per era window, over the FULL requested range (the exact defect
        # R8.2 exists to prevent).
        call_count["n"] = 0
        for _ in range(honest_result.era_window_count):
            isolver.find_threshold_crossings(
                MagicMock(), MagicMock(), start_jd, start_jd + span_days, config,
                coarse_step_days=PEAK_SCAN_STRIDE_DAYS,
            )
        redundant_resweep_cost = call_count["n"]
        mutated_total = honest_count + redundant_resweep_cost

        bound = _honest_eval_bound(
            span_days, honest_result.era_window_count, honest_result.peaks_retained,
        )
        assert mutated_total > bound, (
            "R8.2 detector is not tight enough to catch a per-era-window re-sweep at "
            f"this span: honest={honest_count} + resweep={redundant_resweep_cost} = "
            f"{mutated_total} did not exceed bound={bound}"
        )


# ---------------------------------------------------------------------------
# R8.3 — admission: P90 of the era window's own series, never lambda_thresh
# ---------------------------------------------------------------------------

class TestR83Admission:
    def test_admission_no_lambda_thresh_reference_in_source(self):
        """R8.3: admit_candidates' CODE must never actually CONSULT
        lambda_thresh/ThresholdConfig (dot-access or constructor-call
        patterns) -- checked on executable lines only (comments/docstring
        prose that merely NAMES the invariant, e.g. "no reference to
        lambda_thresh", is not itself a reference and must not false-positive
        this guard). Signature must not accept either as a parameter."""
        src = inspect.getsource(admit_candidates)
        code_lines = [
            line for line in src.splitlines()
            if not line.strip().startswith("#") and '"""' not in line
        ]
        # Exclude the triple-quoted docstring body itself (lines between the
        # opening/closing """ markers), leaving only real code lines.
        executable_lines: list[str] = []
        in_docstring = False
        for line in src.splitlines():
            if '"""' in line:
                # Toggle on any line containing a triple-quote marker (the
                # docstring open and close lines both get excluded too).
                in_docstring = not in_docstring
                continue
            if in_docstring:
                continue
            executable_lines.append(line)
        code_only = "\n".join(executable_lines)

        assert ".lambda_thresh" not in code_only, (
            f"R8.3 VIOLATION: admit_candidates' CODE dot-accesses lambda_thresh:\n{code_only}"
        )
        assert "ThresholdConfig(" not in code_only
        assert "threshold_config." not in code_only

        sig = inspect.signature(admit_candidates)
        assert "threshold_config" not in sig.parameters
        assert "lambda_thresh" not in sig.parameters

    def test_admission_is_threshold_independent(self):
        """Identical retained sets across lambda_thresh in {0.0, 0.3, 0.9}
        proves admission never consults the external threshold.

        Verifier note (2026-08-11, cheap fix): the original curve had a
        baseline of 0.85 with peaks to 0.98 — EVERY point in the series
        (not just the two local-maxima candidates) already cleared all
        three tested lambda_thresh values, so a hypothetical mutant that
        wired `lam >= lambda_thresh` into admission could never have
        produced a different retained set at any of the three thresholds —
        the assertion was structurally incapable of discriminating. Fixed:
        the curve now has a LOW baseline (0.05) and two peaks of differing
        height — one at 0.95 (clears all three thresholds) and one at 0.25
        (clears lambda_thresh=0.0, but falls BELOW both 0.3 and 0.9) — so a
        threshold-gated mutant would retain the 0.25 peak only at
        lambda_thresh=0.0 and drop it at 0.3/0.9, producing three DIFFERENT
        result sets instead of one identical set."""
        start_jd = _BASE_JD

        def curve(jd: float) -> float:
            val = 0.05
            val = max(val, 0.95 - abs(jd - (start_jd + 200.0)) * 0.05)
            val = max(val, 0.25 - abs(jd - (start_jd + 600.0)) * 0.02)
            return val

        results = {}
        for lambda_thresh in (0.0, 0.3, 0.9):
            with patch(
                "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
                wraps=None,
            ) as mock_ftc:
                # Provide a single era interval covering the whole synthetic
                # range, plus its own reused series (mirrors what a real
                # find_threshold_crossings(return_series=True) call returns).
                jds = np.arange(start_jd, start_jd + 800.0, PEAK_SCAN_STRIDE_DAYS)
                lambdas = np.array([curve(jd) for jd in jds])
                interval = _make_interval(enter_jd=start_jd, exit_jd=start_jd + 800.0, peak_lambda=curve(start_jd + 400.0))
                mock_ftc.return_value = ([interval], jds, lambdas)

                with patch(
                    "services.gochara_v3.resolution_hierarchy._eval_single",
                    side_effect=lambda swe, context, jd: curve(float(jd)),
                ):
                    config = _make_threshold_config(lambda_thresh=lambda_thresh)
                    result = build_resolution_hierarchy(MagicMock(), MagicMock(), start_jd, start_jd + 800.0, config)
                    results[lambda_thresh] = sorted(
                        round(w.peak_jd, 1) for w in result.month_windows
                    )

        assert results[0.0] == results[0.3] == results[0.9], (
            f"R8.3 VIOLATION: admission depends on lambda_thresh — "
            f"got different retained peak sets: {results}"
        )
        assert len(results[0.0]) > 0, "test scenario must retain at least one peak"

    def test_flat_curve_admits_nothing(self):
        candidates = [PeakCandidate(jd=10.0, lam=0.5), PeakCandidate(jd=20.0, lam=0.5)]
        flat_series = np.full(20, 0.5)
        assert admit_candidates(candidates, flat_series) == []

    def test_admits_only_candidates_at_or_above_p90(self):
        series = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        p90 = float(np.percentile(series, 90.0))
        candidates = [
            PeakCandidate(jd=1.0, lam=0.95),  # above p90
            PeakCandidate(jd=2.0, lam=0.2),   # below p90
        ]
        admitted = admit_candidates(candidates, series)
        assert len(admitted) == 1
        assert admitted[0].jd == 1.0
        assert admitted[0].lam >= p90


# ---------------------------------------------------------------------------
# R8.4 — retention: rank + greedy separation + cap
# ---------------------------------------------------------------------------

class TestR84Retention:
    def test_retention_cap_and_separation(self):
        """8 admitted candidates, two 40 days apart (must collapse to the
        higher one) -> exactly 3 retained, none within 90 days of another."""
        admitted = [
            PeakCandidate(jd=0.0, lam=0.99),
            PeakCandidate(jd=40.0, lam=0.80),   # within 90d of jd=0 -> dropped
            PeakCandidate(jd=200.0, lam=0.95),
            PeakCandidate(jd=210.0, lam=0.70),  # within 90d of jd=200 -> dropped
            PeakCandidate(jd=500.0, lam=0.90),
            PeakCandidate(jd=800.0, lam=0.60),  # far enough from all -> would be 4th, capped out
            PeakCandidate(jd=1000.0, lam=0.55),
            PeakCandidate(jd=1200.0, lam=0.50),
        ]
        retained = retain_candidates(admitted)
        assert len(retained) == 3
        jds = sorted(r.jd for r in retained)
        assert jds == [0.0, 200.0, 500.0]
        for i in range(len(jds)):
            for j in range(i + 1, len(jds)):
                assert abs(jds[i] - jds[j]) >= MIN_PEAK_SEPARATION_DAYS

    def test_retention_cap_removed_or_widened_changes_result(self):
        """Mutation check: changing max_peaks changes the retained count —
        proves the cap parameter is load-bearing."""
        admitted = [
            PeakCandidate(jd=jd, lam=0.9 - i * 0.01)
            for i, jd in enumerate([0.0, 200.0, 500.0, 800.0, 1200.0])
        ]
        retained_cap3 = retain_candidates(admitted, max_peaks=3)
        retained_cap4 = retain_candidates(admitted, max_peaks=4)
        assert len(retained_cap3) == 3
        assert len(retained_cap4) == 4

    def test_retention_separation_removed_changes_result(self):
        """Mutation check: reducing min_separation_days changes which
        candidates survive — proves separation is load-bearing."""
        admitted = [
            PeakCandidate(jd=0.0, lam=0.99),
            PeakCandidate(jd=40.0, lam=0.80),
        ]
        retained_default_sep = retain_candidates(admitted, min_separation_days=90.0)
        retained_no_sep = retain_candidates(admitted, min_separation_days=0.0)
        assert len(retained_default_sep) == 1
        assert len(retained_no_sep) == 2

    def test_retention_is_deterministic_on_ties(self):
        """Equal λ, different jd -- tiebreak is jd ASC, deterministic across
        repeated calls."""
        admitted = [
            PeakCandidate(jd=500.0, lam=0.9),
            PeakCandidate(jd=0.0, lam=0.9),
            PeakCandidate(jd=1000.0, lam=0.9),
        ]
        r1 = retain_candidates(admitted)
        r2 = retain_candidates(admitted)
        assert [c.jd for c in r1] == [c.jd for c in r2]
        # With all λ tied, rank order is jd ASC -> first-ranked is jd=0.0.
        ranked_first = sorted(admitted, key=lambda c: (-c.lam, c.jd))[0]
        assert ranked_first.jd == 0.0


# ---------------------------------------------------------------------------
# R8.5 — day refinement finds the TRUE argmax, not the coarse candidate
# ---------------------------------------------------------------------------

class TestR85DayRefinement:
    def test_day_refinement_beats_coarse_grid(self):
        """The true max is deliberately OFF the 7-day coarse grid; day
        refinement must find a HIGHER lambda than the coarse candidate's own
        value -- proving refinement is genuinely improving the estimate, not
        a no-op."""
        candidate_jd = 100.0  # a coarse-grid point

        def curve(jd: float) -> float:
            # True peak at jd=103.4 (off-grid), coarse candidate at jd=100
            # sits on the curve's shoulder, well below the true peak.
            true_peak = 103.4
            return max(0.1, 0.95 - abs(jd - true_peak) * 0.05)

        coarse_lambda = curve(candidate_jd)

        with patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            side_effect=lambda swe, context, jd: curve(float(jd)),
        ):
            refined_jd, refined_lambda = refine_peak_to_day(MagicMock(), MagicMock(), candidate_jd)

        assert refined_lambda > coarse_lambda, (
            f"R8.5 VIOLATION: refined lambda ({refined_lambda}) did not exceed the "
            f"coarse candidate's own lambda ({coarse_lambda}) -- refinement is not "
            f"finding the true off-grid peak."
        )
        assert abs(refined_jd - 103.4) <= 1.0, (
            f"refined_jd={refined_jd} is not close to the true peak at 103.4"
        )

    def test_month_and_day_rows_carry_refined_peak_not_coarse_candidate(self):
        """End-to-end: build_peak_anchored_windows' month AND day rows carry
        peak_jd_true (refined), never the coarse candidate.jd.

        PARĪKṢAKA F-2 (2026-08-11): the original version of this test placed
        the true peak only 0.7d off the nearest 7-day coarse-grid point,
        with an assertion tolerance of 1.0d -- so the UNREFINED coarse
        candidate.jd (203.0) would ALSO satisfy `abs(peak_jd - true_peak) <=
        1.0`, making the test pass whether or not refine_peak_to_day ever
        ran. Fixed two ways:
          1. true_peak is now 2.0d off the 7-day grid (grid points 203.0 and
             210.0 straddle it; the nearer one, 203.0, is 2.0d away) AND
             landed exactly on an integer day, so refine_peak_to_day's
             1-day-step re-sample hits it EXACTLY -- the assertion below is
             an exact equality, not a tolerance a coarse hit could sneak
             under.
          2. A second phase monkeypatches refine_peak_to_day itself with a
             call-recording spy returning a SENTINEL (peak_jd, peak_lambda)
             pair that cannot arise from the real curve -- proving the
             month/day rows' peak_jd is LITERALLY the refine_peak_to_day
             return value, not independently derived from the coarse
             candidate elsewhere in build_peak_anchored_windows.
        """
        start_jd = _BASE_JD
        era = _make_window("era", enter_jd=start_jd, exit_jd=start_jd + 800.0)
        true_peak = start_jd + 205.0  # exactly 2.0d off the 203.0 grid point

        def curve(jd: float) -> float:
            return max(0.1, 0.95 - abs(jd - true_peak) * 0.03)

        jds = np.arange(start_jd, start_jd + 800.0, PEAK_SCAN_STRIDE_DAYS)
        lambdas = np.array([curve(jd) for jd in jds])

        # Sanity-check the fixture's own premise: the coarse grid point
        # nearest true_peak is >=2.0d away (i.e. genuinely off-grid), so a
        # test that only checked "close to true_peak" without exactness
        # could not be satisfied by the coarse candidate alone.
        nearest_grid_jd = min(jds, key=lambda jd: abs(jd - true_peak))
        assert abs(nearest_grid_jd - true_peak) >= 2.0, (
            "fixture regression: coarse grid point drifted within 2.0d of "
            "true_peak, which would make this test vacuous again"
        )

        with patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            side_effect=lambda swe, context, jd: curve(float(jd)),
        ):
            month_rows, day_rows, acc = build_peak_anchored_windows(
                MagicMock(), MagicMock(), era, (jds, lambdas),
            )

        assert len(month_rows) == 1 and len(day_rows) == 1
        # Exact equality (not a >=2.0d-slack tolerance a coarse hit could
        # satisfy): refine_peak_to_day's 1-day-step re-sample lands exactly
        # on the integer-day true_peak.
        assert month_rows[0].peak_jd == true_peak, (
            f"R8.5 VIOLATION: month row peak_jd={month_rows[0].peak_jd} != "
            f"true_peak={true_peak} -- refinement did not find the true "
            f"off-grid maximum (or the coarse candidate.jd leaked through)."
        )
        assert day_rows[0].peak_jd == true_peak
        assert month_rows[0].peak_jd == day_rows[0].peak_jd

        # --- wiring assertion: peak_jd is LITERALLY refine_peak_to_day's
        # return value, proven via a call-recording spy + sentinel that the
        # real curve could never produce. ---
        calls = []
        # Far outside [start_jd, start_jd + 800] (the era span) and nowhere
        # near true_peak or any coarse-grid point, but still a valid
        # calendar date (near-epoch JDs like true_peak's own OverflowError
        # under _jd_to_pydate for wildly out-of-range values).
        sentinel_jd, sentinel_lambda = start_jd + 12345.6789, 0.123456

        def _spy(swe, context, candidate_jd, **kwargs):
            calls.append(candidate_jd)
            return sentinel_jd, sentinel_lambda

        with patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            side_effect=lambda swe, context, jd: curve(float(jd)),
        ), patch(
            "services.gochara_v3.resolution_hierarchy.refine_peak_to_day",
            side_effect=_spy,
        ):
            month_rows2, day_rows2, _acc2 = build_peak_anchored_windows(
                MagicMock(), MagicMock(), era, (jds, lambdas),
            )

        assert len(calls) >= 1, (
            "R8.5 WIRING VIOLATION: build_peak_anchored_windows retained a "
            "peak but never called refine_peak_to_day at all."
        )
        assert len(month_rows2) == 1 and len(day_rows2) == 1
        assert month_rows2[0].peak_jd == sentinel_jd, (
            f"R8.5 WIRING VIOLATION: month row peak_jd={month_rows2[0].peak_jd} "
            f"did not come through refine_peak_to_day (expected sentinel "
            f"{sentinel_jd}) -- build_peak_anchored_windows is not calling "
            f"the refinement function it claims to."
        )
        assert day_rows2[0].peak_jd == sentinel_jd
        assert month_rows2[0].peak_lambda == sentinel_lambda
        assert day_rows2[0].peak_lambda == sentinel_lambda


# ---------------------------------------------------------------------------
# R8.6 — exactly one month + one day row per retained peak; zero -> era-only
# ---------------------------------------------------------------------------

class TestR86RowCardinality:
    def test_row_cardinality_identity(self):
        """month row count == day row count == retained peak count, and
        both are <= 3 * era_window_count."""
        start_jd = _BASE_JD

        def curve(jd: float) -> float:
            val = 0.3
            for center in (start_jd + 200.0, start_jd + 600.0, start_jd + 1000.0):
                val = max(val, 0.95 - abs(jd - center) * 0.01)
            return val

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
        ) as mock_ftc, patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            side_effect=lambda swe, context, jd: curve(float(jd)),
        ):
            jds = np.arange(start_jd, start_jd + 1200.0, PEAK_SCAN_STRIDE_DAYS)
            lambdas = np.array([curve(jd) for jd in jds])
            interval = _make_interval(enter_jd=start_jd, exit_jd=start_jd + 1200.0)
            mock_ftc.return_value = ([interval], jds, lambdas)

            config = _make_threshold_config(lambda_thresh=0.5)
            result = build_resolution_hierarchy(MagicMock(), MagicMock(), start_jd, start_jd + 1200.0, config)

        assert len(result.month_windows) == len(result.day_windows) == result.peaks_retained
        assert result.peaks_retained <= 3 * result.era_window_count

    def test_flat_curve_emits_era_only(self):
        """A flat era window (no genuine peak) produces the era row but
        zero month/day rows -- no fallback fabrication."""
        start_jd = _BASE_JD
        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
        ) as mock_ftc:
            jds = np.arange(start_jd, start_jd + 500.0, PEAK_SCAN_STRIDE_DAYS)
            lambdas = np.full(len(jds), 0.7)
            interval = _make_interval(enter_jd=start_jd, exit_jd=start_jd + 500.0, peak_lambda=0.7)
            mock_ftc.return_value = ([interval], jds, lambdas)

            config = _make_threshold_config(lambda_thresh=0.5)
            result = build_resolution_hierarchy(MagicMock(), MagicMock(), start_jd, start_jd + 500.0, config)

        assert len(result.era_windows) == 1
        assert result.month_windows == []
        assert result.day_windows == []
        assert result.zero_peaks_reason == ZERO_PEAKS_FLAT_LAMBDA_CURVE


# ---------------------------------------------------------------------------
# R8.7 — anti-explosion invariant (F3/F3b + PK-R-8)
# ---------------------------------------------------------------------------
#
# BACKGROUND (F3/F3b): the pre-PK-R-8 tiling design, applied naively to a
# multi-year era window, could subdivide into dozens of month rows and
# hundreds of day rows per era window per event class -- a corpus-scale
# explosion (F3/F3b, the finding this ruling and R8.4's MAX_PEAKS_PER_ERA_
# WINDOW=3 cap directly close). This test is PINNED to that finding and to
# PK-R-8 explicitly so it cannot be deleted later as "just an arbitrary
# assertion" -- it is the corpus-shape regression guard for a real,
# previously-observed defect class.

class TestR87AntiExplosion:
    def test_real_corpus_shape_does_not_explode(self):
        """Run the producer against a 3,647-day era window (a realistic
        decade-scale span) with lambda_thresh=0.0 (the writer's own
        structural-prior gate) -- total rows must stay <= 7 (1 era + <=3
        month + <=3 day), day rows must stay <= 3 (F3/F3b + PK-R-8).

        SCOPE NOTE (MR-45 correction, register
        MASTER_REMEDIATION_REGISTER_v2_0.md): this bound of 7 is PER ERA
        WINDOW (this test constructs exactly one). It is NOT a per-substep
        bound -- a single substep's build_resolution_hierarchy call can
        return MULTIPLE era windows (production-confirmed: chart
        482012f1, career_setback::g3_2014_2024), so the honest per-substep
        bound is `N_era + 2*min(3*N_era, ceil(decade_days/90))`, not a flat
        7. See ka_gochara_v3_century_materialize.py's R8.13 docstring
        section for the corrected disclosure."""
        span_days = 3647.0
        start_jd = _BASE_JD

        def curve(jd: float) -> float:
            # A "realistic" multi-bump signal across the decade: several
            # elevated windows of varying width, never fully flat.
            val = 0.35
            for offset, width in ((300.0, 40.0), (1200.0, 60.0), (2100.0, 30.0),
                                   (2900.0, 50.0), (3400.0, 20.0)):
                center = start_jd + offset
                val = max(val, 0.9 - abs(jd - center) / width * 0.4)
            return max(0.0, min(1.0, val))

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
        ) as mock_ftc, patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            side_effect=lambda swe, context, jd: curve(float(jd)),
        ):
            jds = np.arange(start_jd, start_jd + span_days, PEAK_SCAN_STRIDE_DAYS)
            lambdas = np.array([curve(jd) for jd in jds])
            interval = _make_interval(enter_jd=start_jd, exit_jd=start_jd + span_days, peak_lambda=float(np.max(lambdas)))
            mock_ftc.return_value = ([interval], jds, lambdas)

            config = _make_threshold_config(lambda_thresh=0.0)
            result = build_resolution_hierarchy(MagicMock(), MagicMock(), start_jd, start_jd + span_days, config)

        total_rows = len(result.era_windows) + len(result.month_windows) + len(result.day_windows)
        assert total_rows <= 7, (
            f"R8.7 ANTI-EXPLOSION VIOLATION (F3/F3b + PK-R-8): total_rows={total_rows} "
            f"exceeds the closed-form bound of 7 (1 era + <=3 month + <=3 day) for a "
            f"single {span_days}-day era window."
        )
        assert len(result.day_windows) <= 3, (
            f"R8.7 VIOLATION: day_windows={len(result.day_windows)} exceeds "
            f"MAX_PEAKS_PER_ERA_WINDOW=3."
        )


# ---------------------------------------------------------------------------
# MR-44 — retention POOLED across intervals (fixes cross-interval
# natural-key collision). Register: MASTER_REMEDIATION_REGISTER_v2_0.md
# MR-44; PK-R-8 R8.4 amendment.
#
# THE BUG: retain_candidates enforces MIN_PEAK_SEPARATION_DAYS only within
# ONE interval's own candidate set. When find_threshold_crossings genuinely
# returns >=2 intervals for one decade slice (a real, observed production
# condition -- confirmed live: chart 482012f1, event_class=career_setback,
# decade g3_2014_2024, both peaks refined to 2017-03-01), two peaks from
# two DIFFERENT intervals can each trivially clear their own interval's
# within-interval separation check (nothing else in their own interval to
# collide with) yet independently day-refine (R8.5) to the IDENTICAL
# calendar day -- a duplicate row on
# uq_kala_gochara_windows_v2_natural_key (chart_id, event_class,
# window_start, peak_date, milestone_id, generation).
# ---------------------------------------------------------------------------

class TestMR44PooledRetention:
    """Covers both the isolated aggregation-function unit test and the
    end-to-end build_resolution_hierarchy reproduction, plus a mutation-
    provable regression test that a revert to per-interval-only retention
    goes RED under these same assertions."""

    # -- Isolated unit test of the aggregation function itself -------------

    def test_pooled_retention_drops_cross_interval_collision_isolated(self):
        """Two era windows, each with exactly ONE admitted candidate (so
        each interval's own within-interval separation check is trivially
        satisfied -- there is nothing else in either interval to collide
        with), but the two candidates' jds are only 7 days apart (well
        inside MIN_PEAK_SEPARATION_DAYS=90). Naive per-group retention
        (the pre-MR-44 behaviour: retain_candidates called separately per
        group) would keep BOTH. retain_candidates_pooled must keep only the
        higher-lambda one, GLOBALLY."""
        era0_admitted = [PeakCandidate(jd=42.0, lam=0.90)]
        era1_admitted = [PeakCandidate(jd=49.0, lam=0.95)]

        # Sanity: prove the OLD per-group behaviour really would keep both
        # (i.e. this scenario is a genuine collision, not a vacuous setup).
        old_behaviour = [
            retain_candidates(era0_admitted),
            retain_candidates(era1_admitted),
        ]
        assert len(old_behaviour[0]) == 1 and len(old_behaviour[1]) == 1, (
            "fixture regression: per-group retention should trivially keep "
            "both single-candidate groups"
        )

        pooled = retain_candidates_pooled([era0_admitted, era1_admitted])

        assert len(pooled) == 2, "result must be index-aligned with input (2 era groups)"
        total_retained = sum(len(bucket) for bucket in pooled)
        assert total_retained == 1, (
            f"MR-44 VIOLATION: pooled retention kept {total_retained} candidates "
            f"across the two era windows; expected exactly 1 (the higher-lambda "
            f"one, era1's jd=49.0/lam=0.95) since the two candidates are only "
            f"7 days apart -- well inside MIN_PEAK_SEPARATION_DAYS=90. "
            f"pooled={[[(c.jd, c.lam) for c in b] for b in pooled]}"
        )
        # The SURVIVING candidate must be the higher-lambda one (era1's),
        # per the ranked lambda-DESC/jd-ASC tie-break retain_candidates
        # itself uses -- preserved, not silently changed, by pooling.
        assert pooled[0] == []
        assert len(pooled[1]) == 1 and pooled[1][0].jd == 49.0 and pooled[1][0].lam == 0.95

    def test_pooled_retention_preserves_tie_break_rule(self):
        """Same lambda across two era-window groups -- pooled tie-break
        must be jd ASC, identical to retain_candidates' own rule (register
        MR-44: 'preserve the actual existing tie-break rule')."""
        era0_admitted = [PeakCandidate(jd=500.0, lam=0.9)]
        era1_admitted = [PeakCandidate(jd=0.0, lam=0.9)]
        pooled = retain_candidates_pooled([era0_admitted, era1_admitted])
        # jd=0.0 (era1) ranks first on the tie-break and is retained; jd=500
        # is >=90 days away so it also survives separation -- but the RANK
        # order (which one is considered "first") must still be jd ASC.
        ranked_all = sorted(
            [(0, c) for c in era0_admitted] + [(1, c) for c in era1_admitted],
            key=lambda t: (-t[1].lam, t[1].jd),
        )
        assert ranked_all[0][1].jd == 0.0, (
            "fixture regression: tie-break comparison must rank jd=0.0 first"
        )
        assert len(pooled[0]) == 1 and len(pooled[1]) == 1, (
            "both should survive: 500 days apart clears MIN_PEAK_SEPARATION_DAYS=90"
        )

    def test_pooled_retention_caps_per_era_window_not_globally(self):
        """Register MR-44's ruled interpretation of PK-R-8 R8.4: the cap
        stays PER-ERA-WINDOW (MAX_PEAKS_PER_ERA_WINDOW=3 for EACH era
        window), not a shared decade-wide total. Two era windows, each
        with 3 well-separated admitted candidates (6 total, all >=90 days
        from every other candidate including cross-group) -- pooled
        retention must keep all 6 (3 per era window), not cap at 3 total."""
        era0_admitted = [
            PeakCandidate(jd=0.0, lam=0.9),
            PeakCandidate(jd=200.0, lam=0.8),
            PeakCandidate(jd=400.0, lam=0.7),
        ]
        era1_admitted = [
            PeakCandidate(jd=1000.0, lam=0.9),
            PeakCandidate(jd=1200.0, lam=0.8),
            PeakCandidate(jd=1400.0, lam=0.7),
        ]
        pooled = retain_candidates_pooled([era0_admitted, era1_admitted])
        assert len(pooled[0]) == 3, (
            f"MR-44 VIOLATION: era window 0 retained {len(pooled[0])}, expected 3 "
            f"-- the per-era-window cap must not be reduced by pooling."
        )
        assert len(pooled[1]) == 3, (
            f"MR-44 VIOLATION: era window 1 retained {len(pooled[1])}, expected 3."
        )

    def test_pooled_retention_cap_exhaustion_across_eras(self):
        """A single era window whose OWN 4th-best candidate is beaten by a
        SIBLING era window's higher-lambda candidate for a *global*
        separation slot is a different case from the cap test above --
        here we confirm cap enforcement is genuinely PER era-window-index
        (using per_era_count), not e.g. accidentally shared. 4 candidates
        in era0 (well separated) must retain only its own top 3 by lambda,
        regardless of era1 being empty."""
        era0_admitted = [
            PeakCandidate(jd=0.0, lam=0.9),
            PeakCandidate(jd=200.0, lam=0.8),
            PeakCandidate(jd=400.0, lam=0.7),
            PeakCandidate(jd=600.0, lam=0.6),
        ]
        era1_admitted: list[PeakCandidate] = []
        pooled = retain_candidates_pooled([era0_admitted, era1_admitted])
        assert len(pooled[0]) == 3
        assert sorted(c.lam for c in pooled[0]) == [0.7, 0.8, 0.9]
        assert pooled[1] == []

    # -- End-to-end reproduction against build_resolution_hierarchy --------

    @staticmethod
    def _two_interval_collision_fixture():
        """Builds the exact synthetic scenario from the MR-44 register
        finding, at unit-test scale: TWO era windows (interval A =
        [start, start+45], interval B = [start+46, start+90]) each with
        exactly ONE clean, independently-admitted local-maximum peak
        (interval A's candidate at offset 42, lambda 0.9; interval B's at
        offset 49, lambda 0.95) -- trivially separated from any OTHER
        candidate within their OWN interval (there is only one each), but
        only 7 days apart from EACH OTHER. A narrow, deliberately
        off-coarse-grid spike at offset 45 (invisible to the 7-day coarse
        admission scan, but discoverable by refine_peak_to_day's 1-day-step
        +-7-day resample) sits inside BOTH candidates' day-refinement
        windows -- so under the pre-MR-44 per-interval-only retention, BOTH
        peaks independently day-refine to the IDENTICAL calendar day
        (offset 45.0), reproducing the real production collision
        (2017-03-01, chart 482012f1, career_setback g3_2014_2024).

        Verified against the real find_local_maxima/admit_candidates/
        retain_candidates/refine_peak_to_day pipeline (not hand-asserted)
        before being pinned here.
        """
        start_jd = _BASE_JD

        def curve(jd: float) -> float:
            val = 0.1
            val = max(val, 0.9 - abs(jd - (start_jd + 42.0)) * 0.05)
            val = max(val, 0.95 - abs(jd - (start_jd + 49.0)) * 0.05)
            if abs(jd - (start_jd + 45.0)) < 0.5:
                val = max(val, 0.99)  # narrow, off-coarse-grid spike
            return val

        offsets = list(range(0, 91, 7))
        series_jds = np.array([start_jd + o for o in offsets])
        series_lambdas = np.array([curve(j) for j in series_jds])

        interval_a = _make_interval(
            enter_jd=start_jd, exit_jd=start_jd + 45.0,
            peak_jd=start_jd + 42.0, peak_lambda=0.9,
        )
        interval_b = _make_interval(
            enter_jd=start_jd + 46.0, exit_jd=start_jd + 90.0,
            peak_jd=start_jd + 49.0, peak_lambda=0.95,
        )
        return start_jd, curve, series_jds, series_lambdas, interval_a, interval_b

    def test_build_resolution_hierarchy_no_cross_interval_duplicate_peak_dates(self):
        """The PRIMARY MR-44 gate: on the two-interval collision fixture,
        build_resolution_hierarchy must produce ZERO duplicate peak_jd
        values across day_windows. Exactly one peak is retained overall
        (the higher-lambda one, interval B's) -- interval A's candidate is
        honestly dropped for losing the pooled cross-interval separation
        check, not silently duplicated."""
        start_jd, curve, series_jds, series_lambdas, interval_a, interval_b = (
            self._two_interval_collision_fixture()
        )
        config = _make_threshold_config(lambda_thresh=0.5)

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=([interval_a, interval_b], series_jds, series_lambdas),
        ), patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            side_effect=lambda swe, context, jd: curve(float(jd)),
        ):
            result = build_resolution_hierarchy(
                MagicMock(), MagicMock(), start_jd, start_jd + 91.0, config,
            )

        assert len(result.era_windows) == 2, "both context/era rows still emitted"

        peak_dates = [round(w.peak_jd, 6) for w in result.day_windows]
        assert len(peak_dates) == len(set(peak_dates)), (
            f"MR-44 VIOLATION: duplicate peak_jd values across day_windows: "
            f"{peak_dates} -- cross-interval retention is not pooled."
        )
        month_peak_dates = [round(w.peak_jd, 6) for w in result.month_windows]
        assert len(month_peak_dates) == len(set(month_peak_dates)), (
            f"MR-44 VIOLATION: duplicate peak_jd values across month_windows: "
            f"{month_peak_dates}"
        )

        # Exactly one peak retained globally (interval B's higher-lambda
        # candidate); interval A's candidate lost the pooled competition.
        assert result.peaks_admitted == 2
        assert result.peaks_retained == 1
        assert len(result.month_windows) == 1
        assert len(result.day_windows) == 1
        # The surviving peak is the higher-lambda one, refined to the
        # shared spike at offset 45.0 -- proving refinement genuinely ran
        # (not a coarse-candidate passthrough at offset 49.0).
        assert round(result.day_windows[0].peak_jd - start_jd, 4) == 45.0
        assert result.day_windows[0].peak_lambda == pytest.approx(0.99)

    def test_build_resolution_hierarchy_fails_on_unmodified_pre_fix_behaviour(self):
        """GATE PROOF (TDD step 1): re-running the exact same fixture
        through the OLD per-interval-only retention strategy (each era
        window's build_peak_anchored_windows call retains independently,
        exactly what build_resolution_hierarchy did before MR-44) DOES
        reproduce the duplicate -- proving the primary test above is a
        real detector, not a vacuous always-true assertion. This is the
        literal reproduction that FAILED on unmodified code before the fix
        (verified during development; pinned here as a permanent
        regression proof)."""
        start_jd, curve, series_jds, series_lambdas, interval_a, interval_b = (
            self._two_interval_collision_fixture()
        )

        # Reconstruct the PRE-MR-44 code path directly: build each era
        # window's own peak-anchored windows via build_peak_anchored_windows
        # (single-interval retention, exactly as the old
        # build_resolution_hierarchy loop called it), independently.
        era_a = _make_window("era", enter_jd=interval_a.enter_jd, exit_jd=interval_a.exit_jd)
        era_b = _make_window("era", enter_jd=interval_b.enter_jd, exit_jd=interval_b.exit_jd)

        mask_a = (series_jds >= interval_a.enter_jd) & (series_jds <= interval_a.exit_jd)
        mask_b = (series_jds >= interval_b.enter_jd) & (series_jds <= interval_b.exit_jd)

        with patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            side_effect=lambda swe, context, jd: curve(float(jd)),
        ):
            month_a, day_a, _acc_a = build_peak_anchored_windows(
                MagicMock(), MagicMock(), era_a, (series_jds[mask_a], series_lambdas[mask_a]),
            )
            month_b, day_b, _acc_b = build_peak_anchored_windows(
                MagicMock(), MagicMock(), era_b, (series_jds[mask_b], series_lambdas[mask_b]),
            )

        all_day = day_a + day_b
        peak_dates = [round(w.peak_jd, 6) for w in all_day]

        assert len(all_day) == 2, (
            "fixture regression: each interval should independently retain "
            "exactly its own one candidate under per-interval-only retention"
        )
        assert len(peak_dates) != len(set(peak_dates)), (
            "GATE PROOF FAILURE: the per-interval-only retention path (what "
            "build_resolution_hierarchy did before MR-44) did NOT reproduce a "
            "duplicate peak_jd on this fixture -- the fixture no longer proves "
            "the bug it is pinned to, so the primary MR-44 test above is not "
            "actually discriminating."
        )

    # -- Mutation-provable regression test ----------------------------------

    def test_mutation_revert_to_per_interval_retention_reproduces_duplicate(self, monkeypatch):
        """MUTATION test (register requirement): monkeypatch
        retain_candidates_pooled with a function that emulates the exact
        PRE-FIX defect -- retention scoped to each era window
        independently, zero cross-interval separation awareness -- and
        confirm build_resolution_hierarchy, run through THAT mutant, DOES
        reproduce the duplicate peak_jd this file's primary test proves is
        absent from the real (fixed) implementation. This is the literal
        'revert to per-interval retention -> test goes RED' proof: if
        build_resolution_hierarchy's call to retain_candidates_pooled were
        ever reverted/replaced by this same per-interval-only mutant, the
        primary no-duplicates assertion above would fail exactly as
        demonstrated here."""
        start_jd, curve, series_jds, series_lambdas, interval_a, interval_b = (
            self._two_interval_collision_fixture()
        )
        config = _make_threshold_config(lambda_thresh=0.5)

        def _buggy_per_interval_only_retention(admitted_by_era, **kwargs):
            # Exactly the pre-MR-44 defect: no cross-group awareness at all.
            return [
                retain_candidates(group) for group in admitted_by_era
            ]

        monkeypatch.setattr(rh, "retain_candidates_pooled", _buggy_per_interval_only_retention)

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=([interval_a, interval_b], series_jds, series_lambdas),
        ), patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            side_effect=lambda swe, context, jd: curve(float(jd)),
        ):
            mutant_result = build_resolution_hierarchy(
                MagicMock(), MagicMock(), start_jd, start_jd + 91.0, config,
            )

        mutant_peak_dates = [round(w.peak_jd, 6) for w in mutant_result.day_windows]
        assert mutant_result.peaks_retained == 2, (
            "mutant should retain BOTH candidates (no cross-interval awareness)"
        )
        assert len(mutant_peak_dates) != len(set(mutant_peak_dates)), (
            "MUTATION TEST FAILURE: reverting to per-interval-only retention "
            "did NOT reproduce a duplicate peak_jd -- this mutation test is not "
            "a real detector of the MR-44 regression class."
        )


# ---------------------------------------------------------------------------
# MR-45 — month-row/day-row SELF-collision on month-boundary peaks (the
# REAL live-rebuild blocker). Register: MASTER_REMEDIATION_REGISTER_v2_0.md
# MR-45; found by PARĪKṢAKA re-verdict on PR #1231/MR-44, recovering the
# actual halt log from the R2 authorized corpus rebuild -- native chart
# 482012f1, substep 74/270, career_setback::g3_2014_2024, peak refined to
# 2017-03-01.
#
# THE BUG: uq_kala_gochara_windows_v2_natural_key (and its production-table
# counterpart) is (chart_id, event_class, window_start, peak_date,
# COALESCE(milestone_id,''), generation) -- resolution is NOT a key column
# (migration 567 added the column but never folded it into either unique
# index; fixed by migration 568, this same lane). _emit_retained_peaks sets
# a MONTH row's window_start to the calendar-month start containing the
# day-refined true peak, and a DAY row's window_start to that SAME
# day-refined peak date; peak_date is identical on both rows (R8.5/R8.6).
# Whenever a retained peak's day-refined date IS the 1st of a calendar
# month, window_start == peak_date for BOTH rows -- every other pre-568 key
# column is also identical between them (same era_window/call, milestone_id
# always None here, same generation) -- so the two rows collide on an
# identical pre-568 natural key. THIS is a DIFFERENT collision from MR-44's
# (two peaks from two SIBLING era windows landing on the same date): this
# is ONE peak's own month row vs. its own day row colliding with EACH
# OTHER. MR-44's pooled-retention fix does not touch this at all.
#
# THE FIX (migration 568, this lane, execute-to-verified against a
# throwaway Postgres mirroring live schema -- see this lane's PR
# description for the full transcript): add resolution to both unique
# indexes. This Python-level suite cannot close that fix itself (it is
# schema-level) -- its job is to PROVE the writer's row shapes genuinely
# collide on their pre-568 natural-key tuple whenever this condition holds,
# i.e. that migration 568 is fixing a REAL defect, not a hypothetical one.
# ---------------------------------------------------------------------------

class TestMR45MonthDaySelfCollision:
    """Covers (a) an isolated natural-key-tuple-equality proof that a
    month row and day row for the SAME peak collide on the pre-568 key
    whenever the day-refined date is a calendar-month-1st, and (b) an
    end-to-end trace through the REAL build_resolution_hierarchy ->
    _emit_retained_peaks code path confirming the writer genuinely
    produces this exact shape for a real peak landing on a month
    boundary -- not merely a hand-constructed WindowResolutionRecord
    pair."""

    # 2017-03-01, the exact live halt date (chart 482012f1, career_setback,
    # g3_2014_2024) -- JD computed under the SAME epoch convention both
    # resolution_hierarchy.py's _jd_to_pydate/_pydate_to_jd AND the writer's
    # own _jd_to_date use (EPOCH_JD = 2440588.0 == 1970-01-01).
    _MONTH_BOUNDARY_PEAK_JD = 2457814.0  # 2017-03-01

    def test_month_and_day_row_natural_key_tuples_collide_isolated(self):
        """(a) Isolated detector: hand-construct the month row and day row
        WindowResolutionRecord pair _emit_retained_peaks produces for ONE
        retained peak whose day-refined date is a calendar-month-1st, then
        derive (window_start, peak_date) for each using the SAME
        JD-to-date conversion the writer uses (_jd_to_date /
        _jd_to_pydate -- both EPOCH_JD=2440588.0). Assert the two rows'
        (window_start, peak_date) tuples are IDENTICAL -- proving that,
        independent of any index/schema, the writer's own row shapes
        collide on the pre-568 natural key whenever this condition holds
        (chart_id, event_class, COALESCE(milestone_id,''), generation are
        trivially identical too -- both rows come from the same writer
        call for the same event_class/chart/milestone_id=None/generation)."""
        peak_jd = self._MONTH_BOUNDARY_PEAK_JD
        era_window = _make_window(
            "era", enter_jd=peak_jd - 60.0, exit_jd=peak_jd + 60.0,
        )

        month_windows, day_windows = rh._emit_retained_peaks(
            MagicMock(), MagicMock(), era_window,
            [PeakCandidate(jd=peak_jd, lam=0.9)],
        )
        assert len(month_windows) == 1 and len(day_windows) == 1
        month_row, day_row = month_windows[0], day_windows[0]

        # Confirm this fixture genuinely landed on a month-1st (fixture
        # sanity, not the defect assertion itself).
        assert rh._jd_to_pydate(month_row.peak_jd).day == 1, (
            "fixture regression: _MONTH_BOUNDARY_PEAK_JD must refine to a "
            "calendar-month-1st for this test to exercise the real defect"
        )

        month_window_start = rh._jd_to_pydate(month_row.enter_jd)
        month_peak_date = rh._jd_to_pydate(month_row.peak_jd)
        day_window_start = rh._jd_to_pydate(day_row.enter_jd)
        day_peak_date = rh._jd_to_pydate(day_row.peak_jd)

        month_key_tuple = (month_window_start, month_peak_date)
        day_key_tuple = (day_window_start, day_peak_date)

        assert month_key_tuple == day_key_tuple, (
            f"expected the month row and day row to collide on their "
            f"pre-568 (window_start, peak_date) key tuple for a "
            f"month-boundary peak -- month={month_key_tuple} "
            f"day={day_key_tuple}"
        )
        # Both rows land on the exact live halt date.
        assert month_window_start.isoformat() == "2017-03-01"
        assert day_window_start.isoformat() == "2017-03-01"

        # The ONE column migration 568 adds to the key DOES differ between
        # the two rows -- this is what disambiguates them post-fix.
        assert month_row.resolution_tier == "month"
        assert day_row.resolution_tier == "day"
        assert month_row.resolution_tier != day_row.resolution_tier

    def test_real_writer_pipeline_produces_month_boundary_self_collision(self):
        """(b) End-to-end trace through the REAL build_resolution_hierarchy
        -> _scan_and_admit -> retain_candidates_pooled -> _emit_retained_
        peaks pipeline (the actual production code path, not a
        hand-constructed record) confirms a genuine peak whose coarse
        candidate day-refines to a calendar-month-1st produces exactly
        this colliding month/day row pair -- proving the writer really
        does emit this shape under realistic conditions, not merely that
        the shape is theoretically constructible."""
        target_jd = self._MONTH_BOUNDARY_PEAK_JD
        start_jd = target_jd - 60.0
        end_jd = target_jd + 60.0

        def curve(jd: float) -> float:
            # Single clean peak exactly at target_jd, decreasing outward --
            # the coarse (7-day-stride) scan admits the grid point nearest
            # target_jd, and the ±7-day/1-day-step refinement (R8.5) then
            # finds the TRUE argmax at target_jd itself.
            return max(0.1, 0.9 - abs(jd - target_jd) * 0.05)

        series_jds = np.arange(start_jd, end_jd, PEAK_SCAN_STRIDE_DAYS)
        series_lambdas = np.array([curve(j) for j in series_jds])
        interval = _make_interval(
            enter_jd=start_jd, exit_jd=end_jd,
            peak_jd=target_jd, peak_lambda=float(np.max(series_lambdas)),
        )
        config = _make_threshold_config(lambda_thresh=0.5)

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=([interval], series_jds, series_lambdas),
        ), patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            side_effect=lambda swe, context, jd: curve(float(jd)),
        ):
            result = build_resolution_hierarchy(
                MagicMock(), MagicMock(), start_jd, end_jd, config,
            )

        assert result.peaks_retained == 1, (
            "fixture regression: exactly one clean peak should be admitted "
            "and retained"
        )
        assert len(result.month_windows) == 1 and len(result.day_windows) == 1

        month_row = result.month_windows[0]
        day_row = result.day_windows[0]

        # The REAL pipeline's day-refinement genuinely converged on
        # target_jd (not the coarse candidate) -- confirms the true argmax
        # (R8.5) is what got stamped, matching the isolated fixture above.
        assert round(month_row.peak_jd, 6) == round(target_jd, 6)
        assert round(day_row.peak_jd, 6) == round(target_jd, 6)

        month_window_start = rh._jd_to_pydate(month_row.enter_jd)
        day_window_start = rh._jd_to_pydate(day_row.enter_jd)
        peak_date = rh._jd_to_pydate(day_row.peak_jd)

        assert month_window_start == peak_date == day_window_start, (
            f"REAL production pipeline did not reproduce the month-boundary "
            f"self-collision shape: month_window_start={month_window_start} "
            f"peak_date={peak_date} day_window_start={day_window_start}"
        )
        assert month_window_start.isoformat() == "2017-03-01", (
            "fixture regression: expected the exact live halt date"
        )


# ---------------------------------------------------------------------------
# MR-45 — ZERO_PEAKS_LOST_TO_POOLED_RETENTION reachability (MR-44's sibling
# finding, folded into the MR-45 lane per the register). GAP: the constant
# was unreachable dead code -- retain_candidates_pooled always retains >=1
# candidate globally whenever ANY era window admitted one, so the old
# aggregate `total_retained == 0` gate that guarded emitting this reason
# could never fire in the exact case the reason exists to name (one era
# window's own candidate globally rejected while the pool as a whole still
# retains something from a SIBLING era window). FIX: build_resolution_
# hierarchy now reports per-era-window accounting directly via
# HierarchyResult.era_window_accounting (index-aligned with era_windows),
# independent of the aggregate zero_peaks_reason gate.
# ---------------------------------------------------------------------------

class TestMR45ZeroPeaksLostToPooledRetentionReachability:
    def test_specific_era_reports_lost_to_pooled_retention_while_pool_nonzero(self):
        """Adapted from the PARĪKṢAKA verifier's adversarial 3-interval
        pattern: era0@low-lambda-peak, era1@high-lambda-peak-NEARBY (within
        MIN_PEAK_SEPARATION_DAYS=90 of era0's peak, so era0's admitted
        candidate loses the pooled retention competition to era1's), and
        era2@far-away (well outside 90 days of both, retains cleanly and
        independently). Overall total_retained > 0 (era1 + era2 survive),
        so the OLD aggregate-only zero_peaks_reason stays None/absent for
        the call as a whole -- but era0's OWN accounting entry must still
        report ZERO_PEAKS_LOST_TO_POOLED_RETENTION as ITS reason, not
        silently absent."""
        start_jd = _BASE_JD

        # era0: single admitted candidate, low lambda, at offset 0.
        era0_jd = start_jd
        era0_lam = 0.80
        # era1: single admitted candidate, HIGH lambda, 20 days from era0's
        # peak -- well inside MIN_PEAK_SEPARATION_DAYS=90, so whichever of
        # {era0, era1} ranks lower on (lambda DESC, jd ASC) loses the
        # pooled retention competition. era1's higher lambda wins; era0's
        # candidate is rejected. (20, not a multiple of PEAK_SCAN_STRIDE_
        # DAYS=7, deliberately breaks grid phase-alignment between era0's
        # and era1's own explicit sample points below -- see the NOTE.)
        era1_jd = start_jd + 20.0
        era1_lam = 0.95
        # era2: single admitted candidate, far away (600 days out) --
        # >=90 days from both era0 and era1's peaks, retains independently
        # and cleanly regardless of the era0/era1 competition.
        era2_jd = start_jd + 600.0
        era2_lam = 0.85

        # NOTE: each era window's coarse sample points are EXPLICIT and
        # DISJOINT from its siblings' (unlike a shared np.arange grid over
        # overlapping [-20,+20] windows, which would let build_resolution_
        # hierarchy's own interval-boundary MASKING pull era1's higher-
        # lambda points into era0's "own" sliced series -- an artifact of
        # this fixture's construction, not a real production condition;
        # find_threshold_crossings' actual detected intervals never
        # overlap in JD range). Each era's own 3-point sample sits entirely
        # within that era's own interval bounds, with a real gap to its
        # neighbour.
        def curve0(jd: float) -> float:
            return max(0.05, era0_lam - abs(jd - era0_jd) * 0.05)

        def curve1(jd: float) -> float:
            return max(0.05, era1_lam - abs(jd - era1_jd) * 0.05)

        def curve2(jd: float) -> float:
            return max(0.05, era2_lam - abs(jd - era2_jd) * 0.05)

        jds0 = np.array([era0_jd - 10.0, era0_jd - 3.0, era0_jd + 4.0])
        lambdas0 = np.array([curve0(j) for j in jds0])
        jds1 = np.array([era1_jd - 10.0, era1_jd - 3.0, era1_jd + 4.0])
        lambdas1 = np.array([curve1(j) for j in jds1])
        jds2 = np.arange(era2_jd - 20.0, era2_jd + 20.0, PEAK_SCAN_STRIDE_DAYS)
        lambdas2 = np.array([curve2(j) for j in jds2])

        interval0 = _make_interval(enter_jd=era0_jd - 10.0, exit_jd=era0_jd + 4.0, peak_jd=era0_jd, peak_lambda=era0_lam)
        interval1 = _make_interval(enter_jd=era1_jd - 10.0, exit_jd=era1_jd + 4.0, peak_jd=era1_jd, peak_lambda=era1_lam)
        interval2 = _make_interval(enter_jd=era2_jd - 20.0, exit_jd=era2_jd + 20.0, peak_jd=era2_jd, peak_lambda=era2_lam)

        # Fixture sanity: the three intervals' JD ranges must be genuinely
        # disjoint, or build_resolution_hierarchy's own per-interval series
        # masking would cross-contaminate them (defeating the fixture).
        assert interval0.exit_jd < interval1.enter_jd < interval1.exit_jd < interval2.enter_jd, (
            "fixture regression: era intervals must be disjoint JD ranges"
        )

        all_jds = np.concatenate([jds0, jds1, jds2])
        all_lambdas = np.concatenate([lambdas0, lambdas1, lambdas2])
        order = np.argsort(all_jds)
        all_jds = all_jds[order]
        all_lambdas = all_lambdas[order]

        def eval_single(swe, context, jd):
            jd = float(jd)
            if abs(jd - era0_jd) <= 10.0:
                return curve0(jd)
            if abs(jd - era1_jd) <= 10.0:
                return curve1(jd)
            return curve2(jd)

        config = _make_threshold_config(lambda_thresh=0.0)

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=([interval0, interval1, interval2], all_jds, all_lambdas),
        ), patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            side_effect=eval_single,
        ):
            result = build_resolution_hierarchy(
                MagicMock(), MagicMock(), era0_jd - 10.0, era2_jd + 20.0, config,
            )

        assert len(result.era_windows) == 3, "fixture regression: expected 3 era windows"
        assert len(result.era_window_accounting) == 3, (
            "MR-45 VIOLATION: era_window_accounting must be index-aligned "
            "with era_windows (one entry per era window)"
        )

        # The pool AS A WHOLE retained something (era1 + era2) -- the OLD
        # aggregate gate (total_retained == 0) never fires here.
        assert result.peaks_retained >= 2, (
            f"fixture regression: expected era1 and era2 to both retain "
            f"their own peaks; peaks_retained={result.peaks_retained}"
        )
        assert result.zero_peaks_reason is None, (
            "fixture regression/gate proof: the AGGREGATE zero_peaks_reason "
            "must stay None here (total_retained != 0) -- this is exactly "
            "the condition under which the pre-MR-45 code silently dropped "
            "era0's own rejection reason"
        )

        # era0 (index 0) is the one whose candidate lost the pooled
        # competition to era1's higher-lambda, nearby peak -- its OWN
        # accounting entry must name that loss explicitly.
        era0_accounting = result.era_window_accounting[0]
        assert era0_accounting.peaks_admitted >= 1, (
            "fixture regression: era0's candidate must have cleared its "
            "own P90 admission gate (the pooled-retention loss is the "
            "failure mode under test, not an admission failure)"
        )
        assert era0_accounting.peaks_retained == 0, (
            "fixture regression: era0's candidate must have been rejected "
            "by pooled retention (lost to era1's nearby higher-lambda peak)"
        )
        assert era0_accounting.zero_peaks_reason == ZERO_PEAKS_LOST_TO_POOLED_RETENTION, (
            f"MR-45 VIOLATION: era0 lost its admitted candidate to the pooled "
            f"retention competition (era1's nearby higher-lambda peak) while "
            f"the pool as a whole retained era1+era2's peaks, yet era0's own "
            f"accounting reason is {era0_accounting.zero_peaks_reason!r}, not "
            f"ZERO_PEAKS_LOST_TO_POOLED_RETENTION -- the dead-code defect is "
            f"not fixed."
        )

        # era1 and era2 (the survivors) must each report a real retention,
        # no zero_peaks_reason of their own.
        era1_accounting = result.era_window_accounting[1]
        era2_accounting = result.era_window_accounting[2]
        assert era1_accounting.peaks_retained == 1 and era1_accounting.zero_peaks_reason is None
        assert era2_accounting.peaks_retained == 1 and era2_accounting.zero_peaks_reason is None

    def test_mutation_reverting_per_era_accounting_to_aggregate_only_loses_era0_reason(self):
        """MUTATION test: proves era_window_accounting is a REAL, load-
        bearing detector, not vacuous. Simulates the PRE-MR-45 behaviour
        (only the aggregate zero_peaks_reason existed; no per-era-window
        field) by asserting that reading ONLY the aggregate field on the
        same fixture used above would have missed era0's rejection --
        i.e. confirms the aggregate alone is NOT sufficient and the new
        per-era field is what closes the gap."""
        start_jd = _BASE_JD
        era0_jd = start_jd
        era0_lam = 0.80
        era1_jd = start_jd + 14.0
        era1_lam = 0.95

        def curve(jd: float) -> float:
            jd = float(jd)
            v0 = max(0.05, era0_lam - abs(jd - era0_jd) * 0.05)
            v1 = max(0.05, era1_lam - abs(jd - era1_jd) * 0.05)
            return max(v0, v1)

        jds = np.arange(era0_jd - 20.0, era1_jd + 20.0, PEAK_SCAN_STRIDE_DAYS)
        lambdas = np.array([curve(j) for j in jds])
        interval0 = _make_interval(enter_jd=era0_jd - 20.0, exit_jd=era0_jd + 5.0, peak_jd=era0_jd, peak_lambda=era0_lam)
        interval1 = _make_interval(enter_jd=era1_jd - 5.0, exit_jd=era1_jd + 20.0, peak_jd=era1_jd, peak_lambda=era1_lam)
        config = _make_threshold_config(lambda_thresh=0.0)

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=([interval0, interval1], jds, lambdas),
        ), patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            side_effect=lambda swe, context, jd: curve(jd),
        ):
            result = build_resolution_hierarchy(
                MagicMock(), MagicMock(), era0_jd - 20.0, era1_jd + 20.0, config,
            )

        # Aggregate alone (the pre-MR-45 surface) is silent: total_retained
        # is nonzero (era1 survives), so zero_peaks_reason is None.
        assert result.peaks_retained >= 1
        assert result.zero_peaks_reason is None, (
            "fixture regression: aggregate must be None (pool nonzero)"
        )
        # But era0's own accounting entry is NOT silent -- this is the gap
        # MR-45 closes.
        assert result.era_window_accounting[0].zero_peaks_reason == (
            ZERO_PEAKS_LOST_TO_POOLED_RETENTION
        ), (
            "MUTATION TEST FAILURE: era_window_accounting failed to surface "
            "era0's pooled-retention loss even though the aggregate field "
            "(simulating the pre-MR-45 code) stayed silent -- the per-era "
            "field is not actually closing the reachability gap."
        )


# ---------------------------------------------------------------------------
# Backward-compat / structural tests (RESOLUTION_TIERS, assign_parent_window_ids,
# empty-input honesty) -- unaffected by PK-R-8, retained.
# ---------------------------------------------------------------------------

class TestResolutionTiersOrdered:
    def test_resolution_tiers_ordered(self):
        assert RESOLUTION_TIERS[0] == "era"
        assert RESOLUTION_TIERS[1] == "month"
        assert RESOLUTION_TIERS[2] == "day"
        assert RESOLUTION_TIERS[3] == "muhurta"

    def test_tier_count(self):
        assert len(RESOLUTION_TIERS) == 4

    def test_era_before_month_before_day(self):
        assert RESOLUTION_TIERS.index("era") < RESOLUTION_TIERS.index("month")
        assert RESOLUTION_TIERS.index("month") < RESOLUTION_TIERS.index("day")
        assert RESOLUTION_TIERS.index("day") < RESOLUTION_TIERS.index("muhurta")


class TestAssignParentWindowIds:
    """assign_parent_window_ids is retained as an independent pure utility
    (PK-R-8 no longer CALLS it from build_resolution_hierarchy — parent
    linkage is now set directly at construction — but the function itself
    is unmodified and still independently correct/tested)."""

    def test_assign_parent_window_ids_basic(self):
        era_id = str(uuid.uuid4())
        month_id = str(uuid.uuid4())
        era_win = _make_window("era", enter_jd=0.0, exit_jd=100.0, window_id=era_id)
        month_win = _make_window("month", enter_jd=10.0, exit_jd=40.0, window_id=month_id)
        result = assign_parent_window_ids([era_win, month_win])
        month_result = next(w for w in result if w.window_id == month_id)
        era_result = next(w for w in result if w.window_id == era_id)
        assert month_result.parent_window_id == era_id
        assert era_result.parent_window_id is None

    def test_assign_parent_window_ids_no_parent(self):
        month_id = str(uuid.uuid4())
        month_win = _make_window("month", enter_jd=10.0, exit_jd=40.0, window_id=month_id)
        result = assign_parent_window_ids([month_win])
        assert len(result) == 1
        assert result[0].parent_window_id is None

    def test_assign_parent_picks_widest_coarser_window(self):
        wide_era_id = str(uuid.uuid4())
        narrow_era_id = str(uuid.uuid4())
        month_id = str(uuid.uuid4())
        wide_era = _make_window("era", enter_jd=0.0, exit_jd=100.0, window_id=wide_era_id)
        narrow_era = _make_window("era", enter_jd=15.0, exit_jd=35.0, window_id=narrow_era_id)
        month_win = _make_window("month", enter_jd=20.0, exit_jd=30.0, window_id=month_id)
        result = assign_parent_window_ids([wide_era, narrow_era, month_win])
        month_result = next(w for w in result if w.window_id == month_id)
        assert month_result.parent_window_id == wide_era_id

    def test_assign_parent_does_not_assign_same_tier_as_parent(self):
        month_a_id = str(uuid.uuid4())
        month_b_id = str(uuid.uuid4())
        month_a = _make_window("month", enter_jd=0.0, exit_jd=60.0, window_id=month_a_id)
        month_b = _make_window("month", enter_jd=5.0, exit_jd=35.0, window_id=month_b_id)
        result = assign_parent_window_ids([month_a, month_b])
        for w in result:
            assert w.parent_window_id is None

    def test_assign_parent_preserves_all_window_ids(self):
        ids = [str(uuid.uuid4()) for _ in range(5)]
        windows = [
            _make_window("era", 0.0, 1000.0, window_id=ids[0]),
            _make_window("month", 10.0, 40.0, window_id=ids[1]),
            _make_window("month", 50.0, 80.0, window_id=ids[2]),
            _make_window("day", 12.0, 13.0, window_id=ids[3]),
            _make_window("day", 55.0, 56.0, window_id=ids[4]),
        ]
        result = assign_parent_window_ids(windows)
        result_ids = {w.window_id for w in result}
        assert result_ids == set(ids)


class TestBuildResolutionHierarchyEmpty:
    def test_build_resolution_hierarchy_empty(self):
        """When find_threshold_crossings returns no intervals, all tiers
        are empty and facet=0."""
        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=([], np.array([]), np.array([])),
        ):
            result = build_resolution_hierarchy(
                MagicMock(), MagicMock(), 0.0, 1000.0, _make_threshold_config(),
            )
        assert isinstance(result, HierarchyResult)
        assert result.era_windows == []
        assert result.month_windows == []
        assert result.day_windows == []
        assert result.resolution_facet == {"era": 0, "month": 0, "day": 0}

    def test_resolution_facet_keys_always_present(self):
        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=([], np.array([]), np.array([])),
        ):
            result = build_resolution_hierarchy(
                MagicMock(), MagicMock(), 0.0, 1000.0, _make_threshold_config(),
            )
        assert "era" in result.resolution_facet
        assert "month" in result.resolution_facet
        assert "day" in result.resolution_facet

    def test_build_era_windows_end_end_jd_le_start_jd(self):
        assert build_era_windows(MagicMock(), MagicMock(), 100.0, 100.0, _make_threshold_config()) == []


class TestResolutionFacetCounts:
    def test_resolution_facet_counts(self):
        era_wins = [_make_window("era", 0.0, 1000.0)]
        month_wins = [
            _make_window("month", 0.0, 30.0),
            _make_window("month", 30.0, 60.0),
            _make_window("month", 60.0, 90.0),
        ]
        day_wins = [_make_window("day", float(i), float(i + 1)) for i in range(7)]
        facet = {"era": len(era_wins), "month": len(month_wins), "day": len(day_wins)}
        result = HierarchyResult(
            era_windows=era_wins, month_windows=month_wins, day_windows=day_wins,
            resolution_facet=facet,
        )
        assert result.resolution_facet == {"era": 1, "month": 3, "day": 7}


# ---------------------------------------------------------------------------
# term_breakdown/CI propagation for era-tier windows (unaffected by PK-R-8)
# ---------------------------------------------------------------------------

class TestTermBreakdownPropagation:
    """era-tier windows must carry through the IntervalBoundary decomposition
    that find_threshold_crossings already computed; month/day-tier windows
    (day-refined via refine_peak_to_day's scalar-only _eval_single) carry an
    honest None, never a fabricated decomposition (§N.7 item 6)."""

    def test_build_era_windows_carries_term_breakdown(self):
        breakdown = {"promise": 0.5, "permission": 0.6, "lambda_v3": 0.72}
        long_interval = _make_interval(
            enter_jd=0.0, exit_jd=500.0, peak_lambda=0.72,
            term_breakdown=breakdown, lambda_v3_ci_low=0.58, lambda_v3_ci_high=0.86,
            ci_source="structural_prior",
        )
        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=[long_interval],
        ):
            windows = build_era_windows(MagicMock(), MagicMock(), 0.0, 1000.0, _make_threshold_config())
        assert len(windows) == 1
        assert windows[0].resolution_tier == "era"
        assert windows[0].term_breakdown == breakdown
        assert windows[0].lambda_v3_ci_low == 0.58
        assert windows[0].lambda_v3_ci_high == 0.86
        assert windows[0].ci_source == "structural_prior"

    def test_build_era_windows_honest_none_when_interval_has_none(self):
        long_interval = _make_interval(enter_jd=0.0, exit_jd=500.0)
        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=[long_interval],
        ):
            windows = build_era_windows(MagicMock(), MagicMock(), 0.0, 1000.0, _make_threshold_config())
        assert windows[0].term_breakdown is None
        assert windows[0].lambda_v3_ci_low is None

    def test_month_day_windows_carry_no_term_breakdown(self):
        start_jd = _BASE_JD
        era = _make_window("era", enter_jd=start_jd, exit_jd=start_jd + 800.0)

        def curve(jd: float) -> float:
            return max(0.1, 0.95 - abs(jd - (start_jd + 400.0)) * 0.02)

        jds = np.arange(start_jd, start_jd + 800.0, PEAK_SCAN_STRIDE_DAYS)
        lambdas = np.array([curve(jd) for jd in jds])

        with patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            side_effect=lambda swe, context, jd: curve(float(jd)),
        ):
            month_rows, day_rows, _acc = build_peak_anchored_windows(
                MagicMock(), MagicMock(), era, (jds, lambdas),
            )

        assert len(month_rows) >= 1
        for w in month_rows + day_rows:
            assert w.term_breakdown is None
            assert w.lambda_v3_ci_low is None
