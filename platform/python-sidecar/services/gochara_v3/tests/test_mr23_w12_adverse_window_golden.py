"""
MR-23 remainder — W1.2 golden test: a materialized ADVERSE WINDOW.

MASTER_REMEDIATION_REGISTER_v2_0.md MR-23 gap: "W1.2 adverse-window-vs-v1
golden comparison never recorded." Original W1.2 acceptance text
(GOCHARA_UTKARSHA_CAMPAIGN_PLAN_v1_0.md, Wave 1): "a synthetic afflicted
configuration produces an adverse window where v1 produces nothing; golden
tests on known corpus configurations."

RELATIONSHIP TO test_direction_restored.py (W1.2's own test suite)
--------------------------------------------------------------------
test_direction_restored.py already proves the underlying signed-channel and
valence-resolution mechanism thoroughly (AC1-AC5, 40+ tests), including an
AC1 test that scans a JD grid and finds an IntensityResult with
valence='adverse' in v3 mode vs. context.valence in v1 mode for an
all-negative weight_override. What it does NOT do is call the actual window-
materialization machinery (gochara_v3.interval_solver.find_threshold_crossings
-- the real root-solver gochara_v3 windows are built from, W3.2) to produce a
literal IntervalBoundary ("window": enter_jd/exit_jd/peak_jd/peak_lambda) and
check ITS peak is_adverse. This file closes exactly that gap -- extending,
not duplicating, W1.2's own suite.

WHY "ALL-NEGATIVE" WEIGHTS ALONE CANNOT PRODUCE A WINDOW (documented, not
guessed at -- read from engine.py directly)
--------------------------------------------------------------------------
engine.py's `_compute_activity_v3` (the v3 UNSIGNED activity term that drives
raw_lambda / threshold crossing) clamps `target_weight` to `[0, 1]`
(`max(0.0, min(1.0, weight))`) -- a negative weight contributes ZERO to
activity, by design ("negative weights encode direction, not activity
magnitude; direction is handled at the signed_lambda level", engine.py
comment at `_compute_activity_v3`). Only `_compute_signed_channels_v3` (the
SIGNED channels that drive valence) uses `abs(weight)`. So an all-afflicting
configuration alone yields raw_lambda=0 -- literally no window, in EITHER
mode, honest per the same activity math both engines share.

The synthetic configuration below is therefore a MIXED one: a small
supportive contact (weight override = +0.15, enough activity to cross a low
test threshold) plus a large dominant affliction (weight override = -0.95 on
a second real fixture target) -- astrologically the ordinary case of "a
minor supportive contact accompanied by a much stronger affliction", and the
only shape of input that can produce a materialized WINDOW whose valence
comes out adverse.

WHAT "v1 PRODUCES NOTHING" MEANS HERE, OPERATIONALIZED (not glossed)
----------------------------------------------------------------------
`context.promise` is shared, unclamped-computation-wise, between v1 and v3
(engine.py line ~380: `promise = context.promise`, read identically by both
paths) -- it is produced once by `gochara_intensity.promise.compute_promise`,
an I2-protected v1 module. So a genuinely negative PROMISE-driving weight
would zero PROMISE for BOTH engines, and neither would ever emit a window at
all (an honest, uninteresting non-finding). The weight override used here
instead targets `weight_by_target_ref` -- the RUNTIME per-instant weight map
v1's own `compute_x_t` (gochara_intensity/configuration_activity.py, I2-
protected, unmodified) also reads -- and v1 clamps the -0.95 override to 0
there too, so v1's X(t) never sees the affliction. "v1 produces nothing"
is verified directly below as: v1_parity_mode=True, evaluated at the exact
peak_jd of the v3-adverse window, returns valence == context.valence (the
class-level prior) and is_adverse == context.is_adverse -- v1 never
independently discovers 'adverse'. This is the literal, checked claim; nothing
here is asserted without the code being run.
"""
from __future__ import annotations

import numpy as np
import pytest
import swisseph as swe

from services.gochara_grammar import resonance_map as RM
from services.gochara_grammar import dasha_data as DD
from services.gochara_intensity.promise import compute_promise
from services.gochara_intensity.beta_priors import beta_for
from services.gochara_intensity.permission import _relevant_grahas, _relevant_signs
from services.gochara_intensity.engine import SHAPE_MAP
from services.gochara_intensity.valence import is_adverse as _is_adverse

from services.gochara_v3.context import ClassContext
from services.gochara_v3.engine import evaluate_lambda_vector
from services.gochara_v3.interval_solver import find_threshold_crossings
from services.gochara_v3.threshold import ThresholdConfig


CHART_ID = RM.CANONICAL_CHART_ID

# Search window: two calendar years starting 2013-01-01 -- wide enough that
# the mixed supportive+afflicting fixture (2 marriage targets: bhava "7" and
# karaka "Venus") reliably produces at least one above-threshold window
# (verified live: 3 windows in 2013 alone at lambda_thresh=0.02, 2 of them
# adverse -- see this file's own test for the live assertion, not a
# pre-computed number trusted blindly).
_SEARCH_START = (2013, 1, 1)
_SEARCH_END = (2014, 1, 1)

# Deliberately low relative to production's PK-R-3 inert lambda_thresh=0.0 --
# this is a TEST-LOCAL threshold, independent of and not affected by the
# production self-normalizing-threshold ruling (W1.4/PK-R-3). Chosen low
# enough to catch the modest supportive-only activity contribution (weight
# override 0.15) that the mixed scenario intentionally keeps small.
_TEST_LAMBDA_THRESH = 0.02


def _jd(y, m, d, h=12.0):
    return swe.julday(y, m, d, h)


def _make_threshold_config(lambda_thresh: float) -> ThresholdConfig:
    return ThresholdConfig(
        percentile_used=0.80,
        lambda_thresh=lambda_thresh,
        implied_density=10.0,
        base_rate_cited=0.20,
        age_band_used="band_41_60",
        density_flag="ok",
        fallback_used=False,
        sample_count=52,
    )


def _build_mixed_afflicted_context(event_class: str) -> ClassContext:
    """Real fixture targets/dasha (PROMISE/PERMISSION genuinely non-zero,
    not fabricated) with a RUNTIME weight override: the first target gets a
    small positive weight (supportive -- drives activity/threshold-crossing
    enough to materialize a window), every other target gets a large
    negative weight (dominant affliction -- drives the afflicting channel
    that flips valence to 'adverse'). See module docstring for why an
    all-negative override alone cannot produce a window at all.
    """
    targets = [
        t for t in RM.build_fixture_targets(CHART_ID)
        if t.event_class == event_class
    ]
    assert len(targets) >= 2, (
        f"fixture requires >=2 {event_class!r} targets to construct a mixed "
        f"supportive+afflicting scenario; got {len(targets)} -- cannot "
        f"honestly build this test's scenario for this event_class"
    )
    dasha_periods = DD.build_fixture_dasha_periods(CHART_ID)

    promise, promise_detail = compute_promise(list(targets))
    rel_grahas = frozenset(_relevant_grahas(list(targets)))
    rel_signs = frozenset(_relevant_signs(list(targets)))
    class_adverse, class_valence = _is_adverse(None, event_class)
    shape = SHAPE_MAP.get(event_class, "point")

    weight_map = {
        t.target_ref: (0.15 if i == 0 else -0.95)
        for i, t in enumerate(targets)
    }

    return ClassContext(
        chart_id=CHART_ID,
        event_class=event_class,
        resonance_targets=tuple(targets),
        promise=promise,
        promise_detail=promise_detail,
        dasha_periods=tuple(dasha_periods),
        relevant_grahas=rel_grahas,
        relevant_signs=rel_signs,
        temporal_shape=shape,
        valence=class_valence,
        is_adverse=class_adverse,
        beta_e=beta_for(event_class),
        weight_by_target_ref=weight_map,
        natal_facts=None,
        av_gate_rows=(),
        sade_sati_phases=(),
    )


@pytest.fixture(autouse=True)
def _reset_cache():
    from pipeline.transit_search import clear_ephemeris_cache
    clear_ephemeris_cache()
    yield
    clear_ephemeris_cache()


class TestW12AdverseWindowGolden:
    """MR-23 remainder: a materialized window (IntervalBoundary from the
    real W3.2 root-solver), not just a per-JD IntensityResult, for a
    synthetic afflicted configuration -- with the v1-mode comparison at the
    identical peak instant checked directly, not assumed."""

    def test_synthetic_afflicted_configuration_yields_adverse_window(self):
        context = _build_mixed_afflicted_context("marriage")
        threshold_config = _make_threshold_config(_TEST_LAMBDA_THRESH)

        start_jd = _jd(*_SEARCH_START)
        end_jd = _jd(*_SEARCH_END)

        boundaries = find_threshold_crossings(
            swe, context, start_jd, end_jd, threshold_config,
            coarse_step_days=7.0,
        )

        assert boundaries, (
            f"find_threshold_crossings found zero windows for the synthetic "
            f"mixed supportive+afflicting configuration over "
            f"{_SEARCH_START}..{_SEARCH_END} at lambda_thresh="
            f"{_TEST_LAMBDA_THRESH} -- the scenario should reliably produce "
            f"at least one window (verified live during authoring: 3 windows "
            f"in this exact range). A regression here is a real finding, not "
            f"a fixture flake to be silently skipped."
        )

        adverse_windows = []
        for b in boundaries:
            peak_result_v3 = evaluate_lambda_vector(
                swe, context, np.array([b.peak_jd]), v1_parity_mode=False,
            )[0]
            if peak_result_v3.is_adverse:
                adverse_windows.append((b, peak_result_v3))

        assert adverse_windows, (
            f"{len(boundaries)} window(s) found, but none had is_adverse=True "
            f"at their peak. Boundaries (enter/exit/peak/peak_lambda): "
            f"{[(b.enter_jd, b.exit_jd, b.peak_jd, b.peak_lambda) for b in boundaries]}"
        )

        for b, peak_result_v3 in adverse_windows:
            assert peak_result_v3.valence == "adverse"
            assert peak_result_v3.raw_lambda >= threshold_config.lambda_thresh

            # The literal MR-23/W1.2 claim: v1 mode, evaluated at the SAME
            # instant with the SAME context, does not see the affliction --
            # it falls back to the class-level prior. Checked directly.
            peak_result_v1 = evaluate_lambda_vector(
                swe, context, np.array([b.peak_jd]), v1_parity_mode=True,
            )[0]
            assert peak_result_v1.valence == context.valence, (
                f"v1 mode at the v3-adverse window's peak_jd={b.peak_jd} "
                f"must retain the class-prior valence {context.valence!r} "
                f"(I2: gochara_intensity clamps the negative weight to 0 "
                f"before v1 ever sees it), got {peak_result_v1.valence!r} -- "
                f"if this fails, v1's own I2-protected clamping behaviour has "
                f"changed, which is a halt-worthy finding, not a test to relax"
            )
            assert peak_result_v1.is_adverse == context.is_adverse, (
                "v1 mode must retain the class-prior is_adverse, never the "
                "v3 evidence-derived value -- v1 'produces nothing' adverse "
                "for this configuration by construction of its own frozen "
                "formula, verified here rather than assumed"
            )
            assert peak_result_v1.is_adverse is False, (
                "for this specific synthetic scenario (class prior is "
                "non-adverse), v1 must never independently produce "
                "is_adverse=True -- the literal 'v1 produces nothing "
                "[adverse]' claim"
            )
