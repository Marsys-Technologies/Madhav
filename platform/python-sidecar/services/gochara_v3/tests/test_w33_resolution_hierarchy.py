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
    WindowResolutionRecord,
    PeakCandidate,
    HierarchyResult,
    assign_parent_window_ids,
    find_local_maxima,
    admit_candidates,
    retain_candidates,
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
        month + <=3 day), day rows must stay <= 3 (F3/F3b + PK-R-8)."""
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
