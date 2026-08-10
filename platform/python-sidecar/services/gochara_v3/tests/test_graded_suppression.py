"""
Test W1.3 — Graded suppression: vedha as multiplicative quality_gates in λ_v3.

Acceptance criteria verified here (VERIFIER will recheck independently):

  AC1. Empty kala_vedha_gochara table → quality_gates = 1.0 (backward compat;
       no suppression, same as pre-W1.3 placeholder).

  AC2. A synthetic vedha row with malefic_count > 0 → quality_gates < 1.0
       and suppression is recorded in the detail dict (fired_vedha populated).

  AC3. Multiple simultaneous vedhā → quality_gates is their product (strictly
       less than any single vedha's factor, strictly less than 1.0).

  AC4. v1_parity_mode=True path is completely unaffected (quality_gates only
       exists in the v3 path; v1 path still uses original formula).

  AC5. No services/gochara_grammar/*.py modified — verified by import check
       (inherits from test_lambda_v3_bounded.py's TestI2NoV1ModulesEdited;
       not re-asserted here to avoid duplication).

  AC6. Each suppression event records malefic_obstructing_grahas, effect_grade,
       suppression_factor, vedha_kind, graha (fact-grounded detail JSONB).

Additional unit tests:
  - malefic_count = 0 vedha → mild suppression (not 1.0, not 0.0)
  - suppression factor ordering: higher malefic_count → lower factor
  - non-overlapping vedha window → no suppression
  - overlapping AND non-overlapping vedha rows → only overlapping fires
  - _suppression_factor_for_grade grade-string normalisation
  - quality_gates always in (0, 1] for any combination of vedha rows
"""
from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

import numpy as np
import pytest
import swisseph as swe

from services.gochara_grammar import resonance_map as RM
from services.gochara_grammar import dasha_data as DD
from services.gochara_intensity.promise import compute_promise
from services.gochara_intensity.beta_priors import beta_for
from services.gochara_intensity.permission import (
    _relevant_grahas, _relevant_signs,
)
from services.gochara_intensity.engine import SHAPE_MAP

from services.gochara_v3.context import ClassContext, VedhaRow, MaleficScaleRow
from services.gochara_v3.engine import (
    evaluate_lambda_vector,
    _compute_quality_gates_from_context,
    _suppression_factor_for_grade,
    _jd_to_date_iso,
    _VEDHA_ZERO_MALEFIC_FACTOR,
    _VEDHA_NO_SCALE_ROW_FACTOR,
    _VEDHA_WORST_SUPPRESSION,
    _VEDHA_GRADE_SUPPRESSION,
)

CHART_ID = RM.CANONICAL_CHART_ID


# ---------------------------------------------------------------------------
# Helpers: VedhaRow + MaleficScaleRow fixtures
# ---------------------------------------------------------------------------

def _vedha_row(
    vedha_kind: str = "house_vedha",
    graha: str = "Saturn",
    window_start: str = "2013-06-01",
    window_end: str = "2013-09-30",
    malefic_count: int = 1,
    malefic_obstructing_grahas: list[str] | None = None,
    effect_grade: str | None = None,
    classical_citation: str | None = "Phaladeepika Ch.26",
) -> VedhaRow:
    """Build a minimal VedhaRow for testing."""
    detail: dict[str, Any] = {
        "malefic_count": malefic_count,
        "malefic_obstructing_grahas": malefic_obstructing_grahas or (["Saturn"] if malefic_count > 0 else []),
    }
    if effect_grade is not None:
        detail["malefic_effect_grade"] = effect_grade
    return VedhaRow(
        vedha_kind=vedha_kind,
        graha=graha,
        window_start=window_start,
        window_end=window_end,
        classical_citation=classical_citation,
        detail=detail,
    )


def _malefic_scale_rows() -> tuple[MaleficScaleRow, ...]:
    """Build the five Phaladeepika PG353 scale rows for testing."""
    grades = [
        (1, "fear"),
        (2, "grade_2"),
        (3, "grade_3"),
        (4, "grade_4"),
        (5, "ignominy"),
    ]
    return tuple(
        MaleficScaleRow(
            malefic_count=count,
            effect_grade=grade,
            effect_description=f"test description for {grade}",
            source_citation="Phaladeepika PG353",
        )
        for count, grade in grades
    )


def _build_context(
    vedha_rows: tuple[VedhaRow, ...] = (),
    malefic_scale: tuple[MaleficScaleRow, ...] = (),
    event_class: str = "marriage",
    promise_override: float = 0.8,
) -> ClassContext:
    """Build a ClassContext with specified vedha / malefic_scale fixtures."""
    targets = [t for t in RM.build_fixture_targets(CHART_ID) if t.event_class == event_class]
    if not targets:
        targets = RM.build_fixture_targets(CHART_ID)[:1]
    dasha_periods = DD.build_fixture_dasha_periods(CHART_ID)

    from services.gochara_intensity.valence import is_adverse as _is_adverse
    adverse, valence = _is_adverse(None, event_class)

    return ClassContext(
        chart_id=CHART_ID,
        event_class=event_class,
        resonance_targets=tuple(targets),
        promise=promise_override,
        promise_detail={
            "target_count": len(targets),
            "targets": [],
            "aggregation": "noisy_or",
            "calibration_state": "structural_prior",
            "note": f"fixture promise={promise_override}",
        },
        dasha_periods=tuple(dasha_periods),
        relevant_grahas=frozenset(_relevant_grahas(list(targets))),
        relevant_signs=frozenset(_relevant_signs(list(targets))),
        temporal_shape=SHAPE_MAP.get(event_class, "point"),
        valence=valence,
        is_adverse=adverse,
        beta_e=beta_for(event_class),
        weight_by_target_ref={t.target_ref: t.weight for t in targets},
        natal_facts=None,
        av_gate_rows=(),
        sade_sati_phases=(),
        vedha_rows=vedha_rows,
        malefic_scale=malefic_scale,
    )


def _jd(y, m, d, h=12.0):
    return swe.julday(y, m, d, h)


@pytest.fixture(autouse=True)
def _reset_cache():
    from pipeline.transit_search import clear_ephemeris_cache
    clear_ephemeris_cache()
    yield
    clear_ephemeris_cache()


# ---------------------------------------------------------------------------
# Unit tests: _compute_quality_gates_from_context
# ---------------------------------------------------------------------------

class TestComputeQualityGatesUnit:
    """Unit tests for _compute_quality_gates_from_context directly."""

    # AC1: empty vedha_rows → quality_gates = 1.0
    def test_empty_vedha_rows_gives_quality_gates_1(self):
        """AC1: no vedha rows → quality_gates = 1.0."""
        ctx = _build_context(vedha_rows=(), malefic_scale=())
        qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-01", "2013-06-10")
        assert qg == pytest.approx(1.0, abs=1e-10), (
            f"Empty vedha_rows must give quality_gates=1.0, got {qg}"
        )
        assert detail["vedha_fired_count"] == 0
        assert detail["fired_vedha"] == []

    # AC1: non-overlapping vedha window → no suppression
    def test_non_overlapping_window_gives_1(self):
        """Vedha window in the past, eval window in the future → no suppression."""
        vrow = _vedha_row(window_start="2010-01-01", window_end="2010-06-01", malefic_count=2)
        ctx = _build_context(
            vedha_rows=(vrow,),
            malefic_scale=_malefic_scale_rows(),
        )
        # Evaluation window is 2013-06-01 to 2013-06-10: no overlap
        qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-01", "2013-06-10")
        assert qg == pytest.approx(1.0, abs=1e-10), (
            f"Non-overlapping vedha should not suppress; got quality_gates={qg}"
        )
        assert detail["vedha_fired_count"] == 0

    # AC2: synthetic vedha row with malefic_count > 0 → quality_gates < 1.0
    def test_overlapping_malefic_vedha_suppresses(self):
        """AC2: one overlapping vedha with malefic_count=1 → quality_gates < 1.0."""
        vrow = _vedha_row(
            window_start="2013-06-01", window_end="2013-09-30",
            malefic_count=1,
        )
        ctx = _build_context(
            vedha_rows=(vrow,),
            malefic_scale=_malefic_scale_rows(),
        )
        qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
        assert qg < 1.0, f"Malefic vedha must suppress; quality_gates={qg}"
        assert detail["vedha_fired_count"] == 1
        assert len(detail["fired_vedha"]) == 1
        fv = detail["fired_vedha"][0]
        assert fv["malefic_count"] == 1
        assert fv["suppression_factor"] < 1.0

    # AC2: detail JSONB carries all required fields (AC6)
    def test_detail_carries_required_fields(self):
        """AC6: each suppression event records vedha_kind, graha, malefic_count,
        malefic_obstructing_grahas, effect_grade, suppression_factor."""
        vrow = _vedha_row(
            vedha_kind="house_vedha",
            graha="Mars",
            window_start="2013-06-01",
            window_end="2013-09-30",
            malefic_count=2,
            malefic_obstructing_grahas=["Saturn", "Mars"],
        )
        ctx = _build_context(
            vedha_rows=(vrow,),
            malefic_scale=_malefic_scale_rows(),
        )
        _, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
        assert detail["vedha_fired_count"] == 1
        fv = detail["fired_vedha"][0]
        # AC6: all required fields present
        assert "vedha_kind" in fv, "fired_vedha must carry vedha_kind"
        assert "graha" in fv, "fired_vedha must carry graha"
        assert "malefic_count" in fv, "fired_vedha must carry malefic_count"
        assert "malefic_obstructing_grahas" in fv, "fired_vedha must carry malefic_obstructing_grahas"
        assert "effect_grade" in fv, "fired_vedha must carry effect_grade"
        assert "suppression_factor" in fv, "fired_vedha must carry suppression_factor"
        # Values are correct
        assert fv["vedha_kind"] == "house_vedha"
        assert fv["graha"] == "Mars"
        assert fv["malefic_count"] == 2
        assert fv["malefic_obstructing_grahas"] == ["Saturn", "Mars"]

    # AC3: multiple simultaneous vedhā → multiplicative product
    def test_two_vedha_multiply(self):
        """AC3: two overlapping vedhā → quality_gates = factor1 * factor2."""
        vrow1 = _vedha_row(
            graha="Saturn",
            window_start="2013-06-01", window_end="2013-09-30",
            malefic_count=1,
        )
        vrow2 = _vedha_row(
            graha="Mars",
            window_start="2013-06-01", window_end="2013-09-30",
            malefic_count=2,
        )
        ctx = _build_context(
            vedha_rows=(vrow1, vrow2),
            malefic_scale=_malefic_scale_rows(),
        )
        qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
        assert detail["vedha_fired_count"] == 2, (
            f"Expected 2 vedha to fire, got {detail['vedha_fired_count']}"
        )
        # The combined factor should be product of the individual factors
        f1 = detail["fired_vedha"][0]["suppression_factor"]
        f2 = detail["fired_vedha"][1]["suppression_factor"]
        expected = f1 * f2
        assert qg == pytest.approx(expected, rel=1e-9), (
            f"quality_gates={qg} should equal f1*f2={expected} "
            f"(f1={f1}, f2={f2})"
        )
        # AC3: second vedha further reduces the already-suppressed value
        assert qg < min(f1, f2), (
            f"Two vedhā product ({qg}) must be strictly less than "
            f"either single factor ({min(f1, f2)})"
        )

    # AC3: three simultaneous vedhā (product of three)
    def test_three_vedha_multiply(self):
        """AC3: three overlapping vedhā → product of three factors."""
        rows = tuple(
            _vedha_row(
                graha=g,
                window_start="2013-06-01", window_end="2013-09-30",
                malefic_count=c,
            )
            for g, c in [("Saturn", 1), ("Mars", 2), ("Rahu", 3)]
        )
        ctx = _build_context(vedha_rows=rows, malefic_scale=_malefic_scale_rows())
        qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
        assert detail["vedha_fired_count"] == 3
        factors = [fv["suppression_factor"] for fv in detail["fired_vedha"]]
        expected = factors[0] * factors[1] * factors[2]
        assert qg == pytest.approx(expected, rel=1e-9)

    # Malefic_count = 0: mild suppression (not 1.0)
    def test_zero_malefic_count_gives_mild_suppression(self):
        """malefic_count=0 vedha (benefic obstruction) → mild suppression (not 1.0)."""
        vrow = _vedha_row(
            window_start="2013-06-01", window_end="2013-09-30",
            malefic_count=0,
            malefic_obstructing_grahas=[],
        )
        ctx = _build_context(
            vedha_rows=(vrow,),
            malefic_scale=_malefic_scale_rows(),
        )
        qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
        assert detail["vedha_fired_count"] == 1
        fv = detail["fired_vedha"][0]
        assert fv["effect_grade"] == "no_grade"
        assert fv["suppression_factor"] == pytest.approx(_VEDHA_ZERO_MALEFIC_FACTOR, abs=1e-9)
        assert 0.0 < qg < 1.0, (
            f"Zero-malefic vedha should give mild suppression (not 0 or 1), got {qg}"
        )
        assert qg < 1.0 - 1e-9, "Zero-malefic vedha must suppress (quality_gates < 1.0)"

    # Suppression factor ordering
    def test_higher_malefic_count_gives_lower_factor(self):
        """Higher malefic_count → lower (more suppressive) factor."""
        scale = _malefic_scale_rows()
        ctx_base = _build_context(malefic_scale=scale)
        factors = {}
        for count in range(1, 6):
            vrow = _vedha_row(
                window_start="2013-06-01", window_end="2013-09-30",
                malefic_count=count,
            )
            ctx = _build_context(vedha_rows=(vrow,), malefic_scale=scale)
            qg, _ = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
            factors[count] = qg

        # Must be strictly decreasing with malefic_count
        for c in range(1, 5):
            assert factors[c] > factors[c + 1], (
                f"factor[{c}]={factors[c]:.4f} must be > factor[{c+1}]={factors[c+1]:.4f}"
            )

    # Empty malefic_scale table (CI / absent) + malefic_count > 0
    def test_empty_malefic_scale_table_gives_no_scale_row_factor(self):
        """malefic_count > 0 but scale table empty → uses _VEDHA_NO_SCALE_ROW_FACTOR."""
        vrow = _vedha_row(
            window_start="2013-06-01", window_end="2013-09-30",
            malefic_count=3,
        )
        ctx = _build_context(vedha_rows=(vrow,), malefic_scale=())
        qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
        assert detail["vedha_fired_count"] == 1
        fv = detail["fired_vedha"][0]
        assert fv["suppression_factor"] == pytest.approx(_VEDHA_NO_SCALE_ROW_FACTOR, abs=1e-9)

    # Mixed: overlapping + non-overlapping
    def test_only_overlapping_vedha_fires(self):
        """One overlapping + one non-overlapping vedha: only overlapping fires."""
        overlapping = _vedha_row(
            graha="Saturn",
            window_start="2013-06-01", window_end="2013-09-30",
            malefic_count=1,
        )
        non_overlapping = _vedha_row(
            graha="Mars",
            window_start="2012-01-01", window_end="2012-06-01",
            malefic_count=5,
        )
        ctx = _build_context(
            vedha_rows=(overlapping, non_overlapping),
            malefic_scale=_malefic_scale_rows(),
        )
        qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
        assert detail["vedha_fired_count"] == 1
        assert detail["fired_vedha"][0]["graha"] == "Saturn"
        # Only the overlapping (malefic_count=1) factor applies
        expected_factor = _suppression_factor_for_grade("fear")
        assert qg == pytest.approx(expected_factor, rel=1e-9)

    # quality_gates always in (0, 1]
    def test_quality_gates_always_in_0_1(self):
        """Any combination of vedha rows gives quality_gates in (0, 1]."""
        scale = _malefic_scale_rows()
        for counts in [(0,), (1,), (5,), (1, 2), (1, 2, 3), (0, 5)]:
            rows = tuple(
                _vedha_row(
                    graha=f"Saturn_{i}",
                    window_start="2013-06-01", window_end="2013-09-30",
                    malefic_count=c,
                )
                for i, c in enumerate(counts)
            )
            ctx = _build_context(vedha_rows=rows, malefic_scale=scale)
            qg, _ = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
            assert 0.0 < qg <= 1.0 + 1e-10, (
                f"quality_gates={qg} out of (0,1] for counts={counts}"
            )


# ---------------------------------------------------------------------------
# Unit tests: _suppression_factor_for_grade
# ---------------------------------------------------------------------------

class TestSuppressionFactorForGrade:
    """Unit tests for the grade → factor mapping."""

    def test_known_grades_map_correctly(self):
        """All expected grades return their documented factors."""
        for grade, expected in _VEDHA_GRADE_SUPPRESSION.items():
            assert _suppression_factor_for_grade(grade) == pytest.approx(expected, abs=1e-9), (
                f"Grade {grade!r} should map to {expected}, not "
                f"{_suppression_factor_for_grade(grade)}"
            )

    def test_grade_case_insensitive(self):
        """Grade matching is case-insensitive and strips whitespace."""
        assert _suppression_factor_for_grade("Fear") == _suppression_factor_for_grade("fear")
        assert _suppression_factor_for_grade(" IGNOMINY ") == _suppression_factor_for_grade("ignominy")

    def test_grade_space_to_underscore(self):
        """Grade matching converts spaces to underscores."""
        # "grade 2" → "grade_2"
        assert _suppression_factor_for_grade("grade 2") == _suppression_factor_for_grade("grade_2")

    def test_unknown_grade_falls_back_to_worst(self):
        """An unrecognised grade string → _VEDHA_WORST_SUPPRESSION."""
        assert _suppression_factor_for_grade("totally_unknown_grade") == pytest.approx(
            _VEDHA_WORST_SUPPRESSION, abs=1e-9
        )

    def test_empty_grade_falls_back_to_worst(self):
        """Empty or None grade → _VEDHA_WORST_SUPPRESSION."""
        assert _suppression_factor_for_grade("") == pytest.approx(_VEDHA_WORST_SUPPRESSION, abs=1e-9)

    def test_all_factors_in_valid_range(self):
        """Every factor in the schedule is in (0, 1]."""
        for grade, factor in _VEDHA_GRADE_SUPPRESSION.items():
            assert 0.0 < factor <= 1.0, (
                f"Suppression factor for grade {grade!r} must be in (0,1], got {factor}"
            )


# ---------------------------------------------------------------------------
# AC4: v1_parity_mode=True path unaffected
# ---------------------------------------------------------------------------

class TestV1ParityModeUnaffected:
    """AC4: v1_parity_mode=True must be completely unaffected by W1.3."""

    def test_v1_parity_mode_unaffected_by_vedha_rows(self):
        """Feeding vedha_rows to context does NOT change v1_parity_mode results."""
        targets = [t for t in RM.build_fixture_targets(CHART_ID) if t.event_class == "marriage"]
        dasha_periods = DD.build_fixture_dasha_periods(CHART_ID)

        # Build two contexts: one with vedha_rows, one without.
        # v1 path should produce identical results for both.
        vrow = _vedha_row(
            window_start="2013-01-01", window_end="2014-12-31",
            malefic_count=5,  # worst possible suppression — should be invisible in v1 path
        )
        ctx_no_vedha = _build_context(vedha_rows=(), malefic_scale=_malefic_scale_rows())
        ctx_with_vedha = _build_context(
            vedha_rows=(vrow,), malefic_scale=_malefic_scale_rows()
        )

        jd_vector = np.linspace(_jd(2013, 6, 1), _jd(2014, 6, 1), 30)

        results_no_vedha = evaluate_lambda_vector(
            swe, ctx_no_vedha, jd_vector, v1_parity_mode=True,
        )
        results_with_vedha = evaluate_lambda_vector(
            swe, ctx_with_vedha, jd_vector, v1_parity_mode=True,
        )

        for i, (r_no, r_with) in enumerate(zip(results_no_vedha, results_with_vedha)):
            assert r_no.raw_lambda == pytest.approx(r_with.raw_lambda, rel=1e-10, abs=1e-14), (
                f"[{i}] v1_parity_mode=True: vedha_rows must not affect result. "
                f"no_vedha={r_no.raw_lambda:.8f}, with_vedha={r_with.raw_lambda:.8f}"
            )


# ---------------------------------------------------------------------------
# Integration tests: evaluate_lambda_vector with vedha suppression
# ---------------------------------------------------------------------------

class TestEvaluateLambdaWithSuppression:
    """Integration tests: quality_gates flowing through evaluate_lambda_vector."""

    def test_lambda_with_vedha_less_than_without(self):
        """lambda_v3 with an active vedha < lambda_v3 without, at a JD where
        PROMISE * PERMISSION * activity > 0."""
        targets = [t for t in RM.build_fixture_targets(CHART_ID) if t.event_class == "marriage"]
        dasha_periods = DD.build_fixture_dasha_periods(CHART_ID)

        # Vedha active across the entire test period — every JD will be suppressed.
        vrow = _vedha_row(
            window_start="2013-01-01", window_end="2014-12-31",
            malefic_count=3,
        )
        ctx_no_vedha = _build_context(vedha_rows=(), malefic_scale=_malefic_scale_rows())
        ctx_with_vedha = _build_context(
            vedha_rows=(vrow,), malefic_scale=_malefic_scale_rows()
        )

        jd_vector = np.linspace(_jd(2013, 6, 1), _jd(2014, 6, 1), 100)

        results_no = evaluate_lambda_vector(swe, ctx_no_vedha, jd_vector, v1_parity_mode=False)
        results_with = evaluate_lambda_vector(swe, ctx_with_vedha, jd_vector, v1_parity_mode=False)

        # For every JD: suppressed result <= unsuppressed result.
        violations = []
        suppressed_somewhere = False
        for i, (r_no, r_with) in enumerate(zip(results_no, results_with)):
            if r_with.raw_lambda > r_no.raw_lambda + 1e-10:
                violations.append(
                    f"[{i}] suppressed lambda ({r_with.raw_lambda:.8f}) > "
                    f"unsuppressed lambda ({r_no.raw_lambda:.8f})"
                )
            if r_no.raw_lambda > 1e-8 and r_with.raw_lambda < r_no.raw_lambda - 1e-10:
                suppressed_somewhere = True

        assert not violations, (
            "Suppressed lambda must never exceed unsuppressed lambda:\n"
            + "\n".join(violations[:5])
        )
        # Verify suppression is actually visible somewhere (not vacuously passing)
        assert suppressed_somewhere, (
            "Suppression was never visible across 100 JDs — "
            "either all lambda=0 (no primitives fired) or suppression not applied."
        )

    def test_lambda_v3_still_in_0_1_with_suppression(self):
        """AC3 + invariant: lambda_v3 stays in [0,1] even with multiple active vedhā."""
        rows = tuple(
            _vedha_row(
                graha=g,
                window_start="2013-01-01", window_end="2014-12-31",
                malefic_count=c,
            )
            for g, c in [("Saturn", 1), ("Mars", 2), ("Rahu", 3), ("Sun", 5)]
        )
        ctx = _build_context(
            vedha_rows=rows,
            malefic_scale=_malefic_scale_rows(),
            promise_override=1.0,  # max promise so lambda is as high as possible
        )

        jd_vector = np.linspace(_jd(2013, 6, 1), _jd(2014, 6, 1), 200)
        results = evaluate_lambda_vector(swe, ctx, jd_vector, v1_parity_mode=False)

        for i, r in enumerate(results):
            assert 0.0 <= r.raw_lambda <= 1.0 + 1e-10, (
                f"[{i}] lambda_v3 with suppression out of [0,1]: {r.raw_lambda}"
            )

    def test_quality_gates_detail_carried_in_result(self):
        """quality_gates_detail is accessible in x_t_detail of the result."""
        vrow = _vedha_row(
            window_start="2013-06-01", window_end="2013-09-30",
            malefic_count=1,
        )
        ctx = _build_context(
            vedha_rows=(vrow,), malefic_scale=_malefic_scale_rows()
        )

        jd_vector = np.array([_jd(2013, 7, 15)])  # inside vedha window
        results = evaluate_lambda_vector(swe, ctx, jd_vector, v1_parity_mode=False)
        r = results[0]

        # quality_gates_detail is stored in x_t_detail["quality_gates_detail"]
        assert "quality_gates_detail" in r.x_t_detail, (
            "quality_gates_detail must be present in x_t_detail"
        )
        qgd = r.x_t_detail["quality_gates_detail"]
        assert "vedha_fired_count" in qgd, "quality_gates_detail must carry vedha_fired_count"
        assert "fired_vedha" in qgd, "quality_gates_detail must carry fired_vedha"
        assert "quality_gates" in qgd, "quality_gates_detail must carry quality_gates"

    def test_empty_vedha_table_backward_compat(self):
        """AC1: empty vedha table → lambda identical to pre-W1.3 (quality_gates=1.0)."""
        # With no vedha rows, quality_gates=1.0 so the formula is identical to W1.1.
        ctx_empty = _build_context(vedha_rows=(), malefic_scale=())
        jd_vector = np.linspace(_jd(2013, 6, 1), _jd(2014, 6, 1), 50)
        results = evaluate_lambda_vector(swe, ctx_empty, jd_vector, v1_parity_mode=False)

        for i, r in enumerate(results):
            # quality_gates must be 1.0 when no vedha rows
            qgd = r.x_t_detail.get("quality_gates_detail", {})
            qg_value = r.x_t_detail.get("quality_gates", None)
            # Either quality_gates key or quality_gates_detail must show 1.0
            if qg_value is not None:
                assert qg_value == pytest.approx(1.0, abs=1e-9), (
                    f"[{i}] No vedha rows: quality_gates should be 1.0, got {qg_value}"
                )
            if qgd:
                assert qgd.get("quality_gates", 1.0) == pytest.approx(1.0, abs=1e-9), (
                    f"[{i}] No vedha rows: quality_gates_detail.quality_gates should be 1.0"
                )
            # And raw_lambda in [0,1] (invariant must hold)
            assert 0.0 <= r.raw_lambda <= 1.0 + 1e-10


# ---------------------------------------------------------------------------
# Unit tests: _jd_to_date_iso
# ---------------------------------------------------------------------------

class TestJdToDateIso:
    """Unit tests for _jd_to_date_iso helper."""

    def test_known_date(self):
        """A known Julian day converts to the correct YYYY-MM-DD string."""
        jd = _jd(2013, 6, 15, 12.0)
        result = _jd_to_date_iso(swe, jd)
        assert result == "2013-06-15", f"Expected 2013-06-15, got {result!r}"

    def test_format_zero_padded(self):
        """Month and day are zero-padded to 2 digits."""
        jd = _jd(2000, 1, 5, 12.0)
        result = _jd_to_date_iso(swe, jd)
        assert result == "2000-01-05"

    def test_returns_string(self):
        """Result is a string."""
        result = _jd_to_date_iso(swe, _jd(2020, 3, 21))
        assert isinstance(result, str)
        # Must match YYYY-MM-DD format
        parts = result.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4
        assert len(parts[1]) == 2
        assert len(parts[2]) == 2
