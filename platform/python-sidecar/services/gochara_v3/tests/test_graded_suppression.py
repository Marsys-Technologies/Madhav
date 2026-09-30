"""
Test W1.3 — vedha as the §5 interval qualifier on λ_v3 (reconciled).

RECONCILED with the sealed contract (ASTRA_REVIEW_A5_4 v1.2 P2-a;
GOCHARA_DESIGN_SPECS_v1_4 §5; FABLE #16/#17/#25; D-PG353). The original W1.3
criteria AC2/AC3/AC6 pinned a whole-row DATE-grain multiplier graded from a
legacy `malefic_count` (0.85 for a clean row, PG353 grade factors, 0.70 with
no scale row, products across overlapping rows). That evaluator is retired
on the shared v3 path and is NOT restored here. The contract these tests pin:

  AC1. No overlay rows → the gate is honestly `unavailable` (no computed
       horizon) and the λ PRODUCT receives 1.0 (null_state omit).
  AC2'. A pre-T0-8 row carrying only malefic_count / malefic_obstructing_grahas
       is not an interval row: ignored (counted), never a factor.
  AC3'. Attenuation is per obstructing ROOT, once, and multiplies across
       DISTINCT roots only under an explicitly CITED scale (the production
       engine cites none — D-PG353): an active obstruction is `obstructed`
       with factor None; λ is unchanged and the state rides the row.
  AC4. v1_parity_mode=True path is completely unaffected (unchanged test).
  AC6'. A fired entry records the primary contact (graha / house / residence),
       its §6.1 identity, the rule (citation, vedha house, provenance), the
       obstructing interval(s) with obstructor_body / t_in / t_out, the
       operator role and the nullable factor.

Retained legacy helpers (`_suppression_factor_for_grade`, the `_VEDHA_*`
constants, `_LATTA_EFFECTIVE_MALEFIC_COUNT`) still exist in engine.py but
are unwired on the production path; TestSuppressionFactorForGrade pins the
helper's own arithmetic only.
"""
from __future__ import annotations

import json
import math
from dataclasses import replace
from datetime import date
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
from services.ka_vedha_gochara import gate as VG
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


def _interval(body, t_in, t_out, *, state="active", group=None):
    """One §5 interval relation as the ka_vedha_gochara writer stores it."""
    return {"obstructor_body": body, "t_in": t_in, "t_out": t_out, "half_open": True,
            "state": state, "exception": "none",
            "independence_group": group or f"ig:{body}:{t_in}",
            "segments": [{"start": t_in, "end": t_out, "state": state}],
            "operator_role": "scored", "provenance": "verse_cited"}


def _t08_row(graha="Saturn", *, start="2013-01-01", end="2014-12-31", intervals=(),
             operator_role="scored", extra_detail=None) -> VedhaRow:
    """A T0-8-shaped kala_vedha_gochara row — the §5 payload the shared gate
    reads: the primary residence [start, end) with its interval relations and
    a computed coverage horizon."""
    detail: dict[str, Any] = {
        "vedha_intervals": list(intervals),
        "coverage": {"state": "computed", "grain": "date",
                     "horizon_start": start, "horizon_end": end},
        "operator_role": operator_role, "provenance": "verse_cited",
        "primary_house": 3, "vedha_house": 9, "phala": "gain",
        "primary_sign_idx": 9, "primary_sign_name": "Capricorn",
    }
    if extra_detail:
        detail.update(extra_detail)
    return VedhaRow(vedha_kind="house_vedha", graha=graha, window_start=start,
                    window_end=end, classical_citation="Phaladipika Adh. XXVI (fixture)",
                    detail=detail)


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

    # AC2': a legacy malefic_count row is not an interval row
    def test_legacy_malefic_count_rows_are_ignored_never_scored(self):
        """A pre-T0-8 row whose detail carries only malefic_count /
        malefic_obstructing_grahas has no interval relations and no
        coverage horizon: the gate ignores it (counted in
        legacy_shape_rows_ignored), covers nothing (`unavailable`), fires
        nothing, and the λ product receives 1.0. The retired multiplier
        scored this row 0.75 ('fear'); no such number is produced."""
        vrow = _vedha_row(window_start="2013-06-01", window_end="2013-09-30", malefic_count=1)
        ctx = _build_context(vedha_rows=(vrow,), malefic_scale=_malefic_scale_rows())
        qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
        assert qg == 1.0
        assert detail["state"] == "unavailable" and detail["factor"] is None
        assert detail["legacy_shape_rows_ignored"] == 1 and detail["vedha_rows_total"] == 1
        assert detail["vedha_fired_count"] == 0 and detail["fired_vedha"] == []
        assert detail["coverage"]["covers_instant"] is False
        assert "suppression_factor" not in json.dumps(detail)
        assert _suppression_factor_for_grade("fear") == 0.75  # exists only in the unwired helper

    # AC6': the fired entry is identity, not a grade
    def test_obstructed_detail_carries_identity_fields(self):
        """A fired entry records the primary contact (graha, house,
        residence), its §6.1 identity, the rule (citation, vedha house,
        provenance), the obstructing interval(s) with obstructor_body /
        t_in / t_out, the operator role and the nullable factor — never a
        malefic_count / effect_grade / suppression_factor."""
        row = _t08_row("Mars", start="2013-06-01", end="2013-09-30",
                       intervals=[_interval("Saturn", "2013-06-10", "2013-07-10")])
        ctx = _build_context(vedha_rows=(row,), malefic_scale=_malefic_scale_rows())
        qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
        assert qg == 1.0 and detail["state"] == "obstructed" and detail["factor"] is None
        assert detail["null_state"] == "omit" and detail["vedha_fired_count"] == 1
        fv = detail["fired_vedha"][0]
        assert fv["primary_graha"] == "Mars" and fv["vedha_kind"] == "house_vedha"
        assert fv["primary_contact"]["primary_house"] == 3
        assert fv["primary_contact"]["residence"] == ["2013-06-01", "2013-09-30"]
        assert fv["primary_contact_identity"]["overlay_residence_key"] == (
            "Mars|residence|span:Capricorn|kala_vedha_gochara:unversioned|2013-06-01")
        # date-grain overlay: the ledger identity is explicitly unresolved (v1.3 am. 2)
        assert fv["primary_contact_identity"]["identity_resolution"] == "unresolved"
        assert fv["primary_contact_identity"]["independence_group"] is None
        assert fv["rule"]["classical_citation"].startswith("Phaladipika")
        assert fv["rule"]["vedha_house"] == 9 and fv["rule"]["provenance"] == "verse_cited"
        assert fv["operator_role"] == "scored"
        assert fv["fired"][0]["obstructor_body"] == "Saturn"
        assert (fv["fired"][0]["t_in"], fv["fired"][0]["t_out"]) == ("2013-06-10", "2013-07-10")
        assert fv["factor"] is None
        for legacy_key in ("malefic_count", "effect_grade", "suppression_factor",
                           "malefic_obstructing_grahas"):
            assert legacy_key not in fv

    # AC3': roots multiply only under a CITED scale; the engine cites none
    def test_distinct_roots_multiply_only_under_a_cited_scale(self):
        """Two obstructing roots on the engine path: `obstructed`, factor
        None, λ product 1.0 (D-PG353 — no cited scale). The multiplicative
        reduction exists in the gate under an explicitly CITED scale only:
        each DISTINCT root once, product across roots (0.7 × 0.7 = 0.49);
        the same root cited twice counts once (0.7, never 0.49)."""
        two = [_interval("Saturn", "2013-06-01", "2013-09-30", group="root-1"),
               _interval("Mars", "2013-06-01", "2013-09-30", group="root-2")]
        row = _t08_row("Venus", start="2013-01-01", end="2013-12-31", intervals=two)
        ctx = _build_context(vedha_rows=(row,), malefic_scale=_malefic_scale_rows())
        qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
        assert qg == 1.0 and detail["state"] == "obstructed" and detail["factor"] is None
        assert len(detail["fired_vedha"][0]["fired"]) == 2 and detail["factor_by_body"] == {}
        at = date(2013, 6, 15)
        g = VG.make_gate([row], cited_scale=lambda iv: 0.7)(at)
        assert g["factor_by_body"]["Venus"] == pytest.approx(0.49)
        dup = [_interval("Saturn", "2013-06-01", "2013-09-30", group="root-1"),
               _interval("Saturn", "2013-06-01", "2013-09-30", group="root-1")]
        g2 = VG.make_gate([_t08_row("Venus", start="2013-01-01", end="2013-12-31",
                                    intervals=dup)], cited_scale=lambda iv: 0.7)(at)
        assert g2["factor_by_body"]["Venus"] == pytest.approx(0.7)

    def test_three_roots_under_a_cited_scale_take_the_strongest_per_root_once(self):
        """Three roots, one cited twice at different strengths: per root the
        strongest evidence once (0.5 for Saturn, not 0.5 × 0.7), then the
        product across the three roots — 0.5 × 0.7 × 0.7 = 0.245."""
        ivs = [_interval("Saturn", "2013-06-01", "2013-09-30", group="r1"),
               _interval("Saturn", "2013-06-05", "2013-09-30", group="r1"),
               _interval("Mars", "2013-06-01", "2013-09-30", group="r2"),
               _interval("Rahu", "2013-06-01", "2013-09-30", group="r3")]
        row = _t08_row("Venus", start="2013-01-01", end="2013-12-31", intervals=ivs)

        def scale(iv):
            return 0.5 if (iv["obstructor_body"] == "Saturn" and iv["t_in"] == date(2013, 6, 5)) else 0.7

        g = VG.make_gate([row], cited_scale=scale)(date(2013, 6, 15))
        assert len(g["fired"][0]["fired"]) == 4
        assert g["factor_by_body"]["Venus"] == pytest.approx(0.5 * 0.7 * 0.7)
        assert g["factor"] == pytest.approx(0.245) and g["factor"] != pytest.approx(0.5 * 0.7 ** 3)

    # a clean covered row is clear (1.0), never the legacy 'mild' 0.85
    def test_clean_covered_row_is_clear_one_never_a_mild_0_85(self):
        """The retired multiplier scored a malefic_count=0 row at 0.85. A
        covered row with no active interval is `clear`: factor 1.0, nothing
        fired, λ product 1.0."""
        row = _t08_row("Saturn", start="2013-06-01", end="2013-09-30", intervals=[])
        ctx = _build_context(vedha_rows=(row,), malefic_scale=_malefic_scale_rows())
        qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
        assert qg == 1.0 and detail["state"] == "clear" and detail["factor"] == 1.0
        assert detail["vedha_fired_count"] == 0 and detail["coverage"]["covers_instant"] is True
        assert _VEDHA_ZERO_MALEFIC_FACTOR == 0.85 and qg != _VEDHA_ZERO_MALEFIC_FACTOR

    # malefic_count never grades the gate (D-PG353)
    def test_malefic_count_never_grades_the_gate(self):
        """Legacy grading keys riding alongside the §5 payload (malefic_count
        0..5, an effect grade) change NOTHING: the same obstructed / None
        result for every count — no ordering by count exists."""
        outs = []
        for count in range(0, 6):
            row = _t08_row("Saturn", start="2013-06-01", end="2013-09-30",
                           intervals=[_interval("Mars", "2013-06-01", "2013-09-30")],
                           extra_detail={"malefic_count": count, "malefic_effect_grade": "ignominy",
                                         "malefic_obstructing_grahas": ["Mars"] * count})
            ctx = _build_context(vedha_rows=(row,), malefic_scale=_malefic_scale_rows())
            qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
            outs.append((qg, detail["state"], detail["factor"], detail["vedha_fired_count"]))
        assert outs == [(1.0, "obstructed", None, 1)] * 6

    # no cited scale → factor None, never the legacy 0.70 fallback
    def test_no_cited_scale_is_factor_none_not_0_70(self):
        """The retired multiplier fell back to 0.70 with an empty scale
        table. An obstruction without a cited scale is structure — factor
        None, scale 'none_cited', λ product 1.0 — with or without rows in
        malefic_scale (the engine never cites it)."""
        row = _t08_row("Saturn", start="2013-06-01", end="2013-09-30",
                       intervals=[_interval("Mars", "2013-06-01", "2013-09-30")])
        for scale in ((), _malefic_scale_rows()):
            ctx = _build_context(vedha_rows=(row,), malefic_scale=scale)
            qg, detail = _compute_quality_gates_from_context(ctx, "2013-06-15", "2013-06-25")
            assert detail["state"] == "obstructed" and detail["factor"] is None and qg == 1.0
            assert detail["scale"].startswith("none_cited")
            assert "suppression_factor" not in json.dumps(detail)
        assert _VEDHA_NO_SCALE_ROW_FACTOR == 0.70

    # only the interval covering the INSTANT fires (half-open; the reviewer's April-1 probe)
    def test_only_the_interval_covering_the_instant_fires(self):
        """One row, two intervals: Saturn active from March 1; Mars ended
        March 1 (half-open). On April 1 only Saturn fires — the Mars
        interval is not a lingering 0.70; on February 1 only Mars."""
        ivs = [_interval("Saturn", "2013-03-01", "2013-09-30"),
               _interval("Mars", "2013-01-01", "2013-03-01")]
        row = _t08_row("Venus", start="2013-01-01", end="2013-12-31", intervals=ivs)
        ctx = _build_context(vedha_rows=(row,), malefic_scale=_malefic_scale_rows())
        _, d_apr = _compute_quality_gates_from_context(ctx, "2013-04-01", "2013-04-10")
        assert [f["obstructor_body"] for f in d_apr["fired_vedha"][0]["fired"]] == ["Saturn"]
        _, d_feb = _compute_quality_gates_from_context(ctx, "2013-02-01", "2013-02-10")
        assert [f["obstructor_body"] for f in d_feb["fired_vedha"][0]["fired"]] == ["Mars"]
        _, d_mar1 = _compute_quality_gates_from_context(ctx, "2013-03-01", "2013-03-02")
        assert [f["obstructor_body"] for f in d_mar1["fired_vedha"][0]["fired"]] == ["Saturn"]

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

    def test_lambda_identical_with_and_without_an_uncited_obstruction(self):
        """Reconciled: an active obstruction with no cited scale (the
        production engine cites none — D-PG353) is structure on the row,
        not a number in λ. λ_v3 is IDENTICAL with and without the overlay
        row at every JD; the state `obstructed` (factor None) is visible in
        x_t_detail.quality_gates_detail; the legacy 'suppressed <
        unsuppressed' ordering is gone. Without any overlay the gate reads
        `unavailable`, never a clean number."""
        row = _t08_row("Saturn", start="2013-01-01", end="2014-12-31",
                       intervals=[_interval("Mars", "2013-01-01", "2014-12-31")])
        ctx_no_vedha = _build_context(vedha_rows=(), malefic_scale=_malefic_scale_rows())
        ctx_with_vedha = _build_context(vedha_rows=(row,), malefic_scale=_malefic_scale_rows())

        jd_vector = np.linspace(_jd(2013, 6, 1), _jd(2014, 6, 1), 100)
        results_no = evaluate_lambda_vector(swe, ctx_no_vedha, jd_vector, v1_parity_mode=False)
        results_with = evaluate_lambda_vector(swe, ctx_with_vedha, jd_vector, v1_parity_mode=False)

        assert any(r.raw_lambda > 1e-8 for r in results_no), "no primitive fired — vacuous"
        for i, (r_no, r_with) in enumerate(zip(results_no, results_with)):
            assert r_with.raw_lambda == pytest.approx(r_no.raw_lambda, abs=1e-12), i
            qgd = r_with.x_t_detail["quality_gates_detail"]
            assert qgd["state"] == "obstructed" and qgd["factor"] is None
            assert qgd["quality_gates"] == 1.0 and qgd["scoped_application"] == []
            assert r_no.x_t_detail["quality_gates_detail"]["state"] == "unavailable"

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
