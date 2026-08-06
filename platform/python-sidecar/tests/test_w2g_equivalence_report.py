"""Tests for services.w2g.equivalence_report (native ruling point 3, design §3).

TDD-first, written before `services/w2g/equivalence_report.py`. Everything
here is offline and deterministic — synthetic `GenerationRow`s, no DB, no
swisseph. The tool this module backs reads v1's `kala_gochara_windows`
(read-only, the frozen validation benchmark) and the reworked writer's own
`kala_gochara_windows_v2`, and produces the report design §3 requires:

  §3.1 equivalence corpus check — 2.0 reproduces v1's windows (same
        event-class, overlapping bounds within 1 day) wherever v1 was right.
  §3.2 documented-divergence protocol — every divergence classified as (a) v1
        grid artifact, (b) v1 Moon-undersampling miss, or (c) genuine 2.0 bug.
        NO divergence ships unclassified.
  §3.3–3.4 specimen continuity / determinism / adversarial probes — honestly
        NOT built in this lane (see `EquivalenceReport.deferred`), scoped
        down per the ruling's "build what's reasonably scoped" instruction.
"""
from __future__ import annotations

from datetime import date

import pytest

from services.w2g.equivalence_report import (
    ALL_CLASSIFICATIONS,
    CLASS_GENUINE_2_0_BUG_VALENCE_MISMATCH,
    CLASS_UNCLASSIFIED_V1_ONLY_NEEDS_REVIEW,
    CLASS_UNCLASSIFIED_V2_ONLY_NEEDS_REVIEW,
    CLASS_V1_GRID_ARTIFACT,
    CLASS_V1_MOON_UNDERSAMPLING_MISS,
    GenerationRow,
    build_equivalence_report,
    classify_v1_only,
    classify_v2_only,
    match_rows,
    scope_v1_rows,
)


def _row(
    event_class="marriage",
    peak_date=date(2013, 1, 6),
    temporal_shape="point",
    is_adverse=False,
    valence="gain",
    signed_intensity=1.5,
    generation="v1",
    transit_planets=frozenset(),
) -> GenerationRow:
    return GenerationRow(
        event_class=event_class,
        temporal_shape=temporal_shape,
        peak_date=peak_date,
        window_start=peak_date,
        window_end=peak_date,
        is_adverse=is_adverse,
        valence=valence,
        signed_intensity=signed_intensity,
        generation=generation,
        transit_planets=transit_planets,
    )


# ── GenerationRow.from_db_row ─────────────────────────────────────────────────


def test_from_db_row_extracts_transit_planets_from_active_sentences():
    db_row = {
        "event_class": "marriage",
        "temporal_shape": "point",
        "peak_date": date(2013, 1, 6),
        "window_start": date(2013, 1, 6),
        "window_end": date(2013, 1, 6),
        "is_adverse": False,
        "valence": "gain",
        "signed_intensity": 1.2,
        "generation": "v1",
        "active_sentences": [
            {"transit_planet": "Moon", "primitive": "sign_ingress"},
            {"transit_planet": "Venus", "primitive": "drishti_contact"},
        ],
    }
    row = GenerationRow.from_db_row(db_row)
    assert row.transit_planets == frozenset({"Moon", "Venus"})


def test_from_db_row_honest_empty_when_no_active_sentences():
    db_row = {
        "event_class": "marriage", "temporal_shape": "point",
        "peak_date": date(2013, 1, 6), "window_start": date(2013, 1, 6),
        "window_end": date(2013, 1, 6), "is_adverse": False, "valence": "gain",
        "signed_intensity": 1.0, "generation": "2.0", "active_sentences": [],
    }
    row = GenerationRow.from_db_row(db_row)
    assert row.transit_planets == frozenset()


# ── scope_v1_rows: §3.1's comparable-scope definition ─────────────────────────


def test_scope_excludes_non_point_shapes():
    v1 = [_row(event_class="major_gain", temporal_shape="interval")]
    in_scope, out_of_scope = scope_v1_rows(
        v1, classes_attempted_by_v2=["major_gain"],
        horizon_start=date(2020, 1, 1), horizon_end=date(2030, 1, 1),
    )
    assert in_scope == []
    assert "major_gain" in out_of_scope
    assert "point" in out_of_scope["major_gain"].lower() or "interval" in out_of_scope["major_gain"].lower()


def test_scope_excludes_classes_v2_never_attempted():
    v1 = [_row(event_class="chronic_onset")]
    in_scope, out_of_scope = scope_v1_rows(
        v1, classes_attempted_by_v2=["marriage"],  # chronic_onset not attempted
        horizon_start=date(2020, 1, 1), horizon_end=date(2030, 1, 1),
    )
    assert in_scope == []
    assert "chronic_onset" in out_of_scope


def test_scope_excludes_rows_outside_the_progressive_horizon():
    v1 = [_row(peak_date=date(1999, 1, 1))]  # long before any ±3y horizon
    in_scope, out_of_scope = scope_v1_rows(
        v1, classes_attempted_by_v2=["marriage"],
        horizon_start=date(2023, 8, 6), horizon_end=date(2029, 8, 6),
    )
    assert in_scope == []
    assert "marriage" in out_of_scope
    assert "horizon" in out_of_scope["marriage"].lower()


def test_scope_includes_point_shaped_in_horizon_attempted_class():
    v1 = [_row(peak_date=date(2025, 1, 1))]
    in_scope, out_of_scope = scope_v1_rows(
        v1, classes_attempted_by_v2=["marriage"],
        horizon_start=date(2023, 8, 6), horizon_end=date(2029, 8, 6),
    )
    assert len(in_scope) == 1
    assert out_of_scope == {}


# ── match_rows: §3.1's "overlapping bounds within 1 day" matching ────────────


def test_match_rows_exact_same_date():
    v1 = [_row(peak_date=date(2013, 1, 6), generation="v1")]
    v2 = [_row(peak_date=date(2013, 1, 6), generation="2.0")]
    matched, v1_only, v2_only = match_rows(v1, v2)
    assert len(matched) == 1
    assert matched[0].date_diff_days == 0
    assert v1_only == [] and v2_only == []


def test_match_rows_within_one_day_tolerance():
    v1 = [_row(peak_date=date(2013, 1, 6))]
    v2 = [_row(peak_date=date(2013, 1, 7), generation="2.0")]
    matched, v1_only, v2_only = match_rows(v1, v2)
    assert len(matched) == 1
    assert matched[0].date_diff_days == 1


def test_match_rows_beyond_tolerance_is_unmatched():
    v1 = [_row(peak_date=date(2013, 1, 6))]
    v2 = [_row(peak_date=date(2013, 1, 10), generation="2.0")]
    matched, v1_only, v2_only = match_rows(v1, v2)
    assert matched == []
    assert len(v1_only) == 1
    assert len(v2_only) == 1


def test_match_rows_never_crosses_event_class():
    v1 = [_row(event_class="marriage", peak_date=date(2013, 1, 6))]
    v2 = [_row(event_class="surgery", peak_date=date(2013, 1, 6), generation="2.0")]
    matched, v1_only, v2_only = match_rows(v1, v2)
    assert matched == []
    assert len(v1_only) == 1 and len(v2_only) == 1


def test_match_rows_greedy_prefers_closest_date_one_to_one():
    v1 = [_row(peak_date=date(2013, 1, 5)), _row(peak_date=date(2013, 1, 7))]
    v2 = [_row(peak_date=date(2013, 1, 6), generation="2.0")]  # equidistant from both
    matched, v1_only, v2_only = match_rows(v1, v2)
    assert len(matched) == 1  # only one v2 row -- can match at most one v1 row
    assert len(v1_only) == 1
    assert v2_only == []


def test_match_rows_valence_agreement_flag():
    v1 = [_row(peak_date=date(2013, 1, 6), valence="gain", is_adverse=False)]
    v2 = [_row(peak_date=date(2013, 1, 6), valence="loss", is_adverse=True, generation="2.0")]
    matched, _, _ = match_rows(v1, v2)
    assert matched[0].valence_agrees is False


# ── classify_v1_only / classify_v2_only: §3.2's three named categories ───────


def test_classify_v1_only_as_grid_artifact_when_v2_has_a_wider_drift_match():
    v1_row = _row(event_class="marriage", peak_date=date(2013, 1, 6))
    v2_same_class = [_row(event_class="marriage", peak_date=date(2013, 1, 9), generation="2.0")]  # 3 days off
    d = classify_v1_only(v1_row, v2_same_class)
    assert d.classification == CLASS_V1_GRID_ARTIFACT
    assert d.kind == "v1_only"


def test_classify_v1_only_falls_to_unclassified_needs_review_with_no_nearby_v2():
    v1_row = _row(event_class="marriage", peak_date=date(2013, 1, 6))
    d = classify_v1_only(v1_row, [])
    assert d.classification == CLASS_UNCLASSIFIED_V1_ONLY_NEEDS_REVIEW


def test_classify_v2_only_as_moon_undersampling_when_moon_drives_the_candidate():
    v2_row = _row(event_class="marriage", peak_date=date(2013, 1, 6), generation="2.0",
                   transit_planets=frozenset({"Moon"}))
    d = classify_v2_only(v2_row, [])
    assert d.classification == CLASS_V1_MOON_UNDERSAMPLING_MISS
    assert d.kind == "v2_only"


def test_classify_v2_only_as_grid_artifact_when_v1_has_a_wider_drift_match():
    v2_row = _row(event_class="marriage", peak_date=date(2013, 1, 6), generation="2.0")
    v1_same_class = [_row(event_class="marriage", peak_date=date(2013, 1, 9))]  # 3 days off, non-Moon
    d = classify_v2_only(v2_row, v1_same_class)
    assert d.classification == CLASS_V1_GRID_ARTIFACT


def test_classify_v2_only_falls_to_unclassified_needs_review_otherwise():
    v2_row = _row(event_class="marriage", peak_date=date(2013, 1, 6), generation="2.0")
    d = classify_v2_only(v2_row, [])
    assert d.classification == CLASS_UNCLASSIFIED_V2_ONLY_NEEDS_REVIEW


def test_every_named_classification_is_in_the_closed_vocabulary():
    for c in (CLASS_V1_GRID_ARTIFACT, CLASS_V1_MOON_UNDERSAMPLING_MISS,
              CLASS_GENUINE_2_0_BUG_VALENCE_MISMATCH,
              CLASS_UNCLASSIFIED_V1_ONLY_NEEDS_REVIEW,
              CLASS_UNCLASSIFIED_V2_ONLY_NEEDS_REVIEW):
        assert c in ALL_CLASSIFICATIONS


# ── build_equivalence_report: the end-to-end tool ─────────────────────────────


def test_build_report_end_to_end_matched_plus_every_divergence_kind():
    v1_rows_raw = [
        # matched, agreeing
        dict(event_class="marriage", temporal_shape="point", peak_date=date(2013, 1, 6),
             window_start=date(2013, 1, 6), window_end=date(2013, 1, 6),
             is_adverse=False, valence="gain", signed_intensity=1.5, generation="v1",
             active_sentences=[]),
        # v1_only, no nearby v2 -> unclassified needs review
        dict(event_class="marriage", temporal_shape="point", peak_date=date(2015, 6, 1),
             window_start=date(2015, 6, 1), window_end=date(2015, 6, 1),
             is_adverse=False, valence="gain", signed_intensity=1.0, generation="v1",
             active_sentences=[]),
        # matched, valence disagrees -> genuine bug
        dict(event_class="surgery", temporal_shape="point", peak_date=date(2020, 3, 1),
             window_start=date(2020, 3, 1), window_end=date(2020, 3, 1),
             is_adverse=True, valence="loss", signed_intensity=-2.0, generation="v1",
             active_sentences=[]),
        # out of scope: interval shape
        dict(event_class="major_gain", temporal_shape="interval", peak_date=date(2020, 1, 1),
             window_start=date(2019, 12, 1), window_end=date(2020, 2, 1),
             is_adverse=False, valence="gain", signed_intensity=3.0, generation="v1",
             active_sentences=[]),
    ]
    v2_rows_raw = [
        # matches v1_rows_raw[0]
        dict(event_class="marriage", temporal_shape="point", peak_date=date(2013, 1, 6),
             window_start=date(2013, 1, 6), window_end=date(2013, 1, 6),
             is_adverse=False, valence="gain", signed_intensity=1.6, generation="2.0",
             active_sentences=[]),
        # matches v1_rows_raw[2]'s date but disagrees on valence
        dict(event_class="surgery", temporal_shape="point", peak_date=date(2020, 3, 1),
             window_start=date(2020, 3, 1), window_end=date(2020, 3, 1),
             is_adverse=False, valence="gain", signed_intensity=1.2, generation="2.0",
             active_sentences=[]),
        # v2_only, Moon-driven -> undersampling miss
        dict(event_class="career_advancement", temporal_shape="point", peak_date=date(2024, 4, 4),
             window_start=date(2024, 4, 4), window_end=date(2024, 4, 4),
             is_adverse=False, valence="gain", signed_intensity=0.8, generation="2.0",
             active_sentences=[{"transit_planet": "Moon"}]),
    ]

    report = build_equivalence_report(
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        v1_rows_raw=v1_rows_raw, v2_rows_raw=v2_rows_raw,
        horizon_start=date(2012, 1, 1), horizon_end=date(2030, 1, 1),
        classes_attempted_by_v2=["marriage", "surgery", "career_advancement", "illness_acute"],
    )

    assert report.chart_id == "482012f1-710e-4a25-994a-93821f5871aa"
    assert "major_gain" in report.classes_out_of_scope  # interval shape, honestly excluded

    # exactly one clean equivalent match
    assert len(report.matched) == 2  # marriage pair + surgery pair (matched by date, valence disagrees)
    assert sum(1 for m in report.matched if m.valence_agrees) == 1

    kinds = {d.kind for d in report.divergences}
    assert "v1_only" in kinds
    assert "v2_only" in kinds
    assert "valence_mismatch" in kinds

    classifications = {d.classification for d in report.divergences}
    assert CLASS_UNCLASSIFIED_V1_ONLY_NEEDS_REVIEW in classifications
    assert CLASS_V1_MOON_UNDERSAMPLING_MISS in classifications
    assert CLASS_GENUINE_2_0_BUG_VALENCE_MISMATCH in classifications

    # design §3.2: NO divergence ships unclassified
    assert report.unclassified() == []
    for d in report.divergences:
        assert d.classification in ALL_CLASSIFICATIONS

    # equivalence_rate: 1 clean-equivalent match out of 3 in-scope v1 rows
    # (marriage(2013) matched+agrees; marriage(2015) is v1_only; surgery(2020)
    # matched but disagrees on valence -- not counted as equivalent).
    # major_gain (interval-shaped) is correctly excluded from scope entirely.
    assert report.v1_in_scope_count == 3
    assert report.equivalent_count == 1
    assert report.equivalence_rate == pytest.approx(1 / 3)

    # honest disclosure of what this lane did NOT build (ruling point 3 / design §3.3-3.5)
    assert report.deferred, "the report must disclose what specimen-continuity/determinism/adversarial-probe work was NOT done"
    assert any("determinism" in d.lower() or "adversarial" in d.lower() for d in report.deferred)
    assert any("specimen" in d.lower() for d in report.deferred)


def test_build_report_honest_zero_when_both_sides_empty():
    report = build_equivalence_report(
        chart_id="c1", v1_rows_raw=[], v2_rows_raw=[],
        horizon_start=date(2020, 1, 1), horizon_end=date(2030, 1, 1),
        classes_attempted_by_v2=["marriage"],
    )
    assert report.matched == []
    assert report.divergences == []
    assert report.v1_in_scope_count == 0
    assert report.equivalence_rate is None  # honest null, not a fabricated 100% or 0%


def test_equivalence_report_summary_is_json_serializable():
    import json
    report = build_equivalence_report(
        chart_id="c1", v1_rows_raw=[], v2_rows_raw=[],
        horizon_start=date(2020, 1, 1), horizon_end=date(2030, 1, 1),
        classes_attempted_by_v2=["marriage"],
    )
    json.dumps(report.summary())  # must not raise
