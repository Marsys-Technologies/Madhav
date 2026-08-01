"""
tests/test_w2g_validations.py — W2G (GOCHARA-2.0) bind-time validations V1–V6.

No DATABASE_URL required for the bulk of this suite: every validation is a
pure function of a `QueryFn` seam, so the unit tests drive them against
`_FakeDB`, a small canned-rows fake keyed on SQL fragments. That is the same
technique `tests/test_ka_gochara_sweep.py` and `tests/test_ka_sangam_resumption.py`
already use for writer helpers.

MUTATION DISCIPLINE. Each validation is asserted BOTH ways — a fixture that
should PASS and a fixture that should FAIL — so no test can be satisfied by a
detector that always returns the same answer. That is the §N.8 Earned-Signal
Principle applied to the tests themselves: a status must have a code path
that would make it read the other way.

`@pytest.mark.integration` tests at the bottom hit the LIVE database when
DATABASE_URL is set and are excluded by the mandated `-m "not integration"`
pytest invocation.
"""
from __future__ import annotations

import os
from datetime import date

import pytest

from services.w2g_validations import (
    FAIL,
    INDETERMINATE,
    PASS,
    WAVE_ID,
    ValidationResult,
    bind_gate,
    classify_divergence,
    run_all,
    run_divergence_report,
    validate_v1_profile_split,
    validate_v2_ephemeris_coverage,
    validate_v3_spline_accuracy,
    validate_v4_transition_sizing,
    validate_v5_corpus_readiness,
    validate_v6_divergence_pilot,
)
from services.w2g_validations.v6_divergence_pilot import (
    CLASS_A_V1_GRID_ARTIFACT,
    CLASS_AGREEMENT,
    CLASS_B_V1_MOON_UNDERSAMPLING,
    CLASS_C_CANDIDATE_2_0_BUG,
    UNCLASSIFIED,
)

CHART_A = "482012f1-710e-4a25-994a-93821f5871aa"
CHART_B = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"

NINE_BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


class _FakeDB:
    """Canned-rows QueryFn. Routes on distinctive SQL fragments, in order."""

    def __init__(self, routes: list[tuple[str, list[dict]]]):
        self.routes = routes
        self.calls: list[tuple[str, list]] = []

    def __call__(self, sql: str, params=()) -> list[dict]:
        self.calls.append((sql, list(params)))
        for fragment, rows in self.routes:
            if fragment in sql:
                return rows if not callable(rows) else rows(sql, list(params))
        return []


def _tables(*names: str):
    return ("information_schema.tables", [{"table_name": n} for n in names])


# ─────────────────────────────────────────────────────────────────────────────
# types — the DATA-HONESTY RAIL is enforced by the type, not by convention
# ─────────────────────────────────────────────────────────────────────────────


def test_indeterminate_without_reason_is_rejected():
    with pytest.raises(ValueError, match="reason"):
        ValidationResult(
            validation_id="V9", title="t", status=INDETERMINATE, summary="s"
        )


def test_unknown_status_is_rejected():
    with pytest.raises(ValueError, match="status"):
        ValidationResult(validation_id="V9", title="t", status="GREEN", summary="s")


def test_result_dict_carries_the_wave_id():
    r = ValidationResult(validation_id="V1", title="t", status=PASS, summary="s")
    assert r.to_dict()["wave"] == WAVE_ID == "W2G"


# ─────────────────────────────────────────────────────────────────────────────
# V2 — ephemeris coverage (ADJUDICATION-5 amended: 1900–2084 x 9 bodies)
# ─────────────────────────────────────────────────────────────────────────────


def _coverage_rows(first="1900-01-01", last="2150-12-31", n_dates=91676, bodies=None):
    return [
        {
            "body": b,
            "first_date": first,
            "last_date": last,
            "n_rows": n_dates,
            "n_dates": n_dates,
        }
        for b in (bodies or NINE_BODIES)
    ]


def test_v2_passes_on_full_contiguous_coverage():
    db = _FakeDB([_tables("ephemeris_daily"), ("MIN(date) AS first_date", _coverage_rows())])
    r = validate_v2_ephemeris_coverage(db)
    assert r.status == PASS
    assert r.data["calendar_epoch_start"] == "1900-01-01"
    assert r.data["calendar_epoch_start_basis"] == "max_over_bodies_first_covered_date"
    assert r.data["bodies_measured"] == 9


def test_v2_epoch_start_is_max_over_bodies_and_fails_when_later_than_nominal():
    """ADJUDICATION-5: 'If any body proves to have a later start than 1900,
    calendar_epoch_start becomes the max over bodies of first-covered date.'"""
    rows = _coverage_rows()
    rows[3] = {
        "body": "Mercury",
        "first_date": "1962-03-01",
        "last_date": "2150-12-31",
        "n_rows": 68_776,
        "n_dates": 68_776,
    }
    db = _FakeDB([_tables("ephemeris_daily"), ("MIN(date) AS first_date", rows)])
    r = validate_v2_ephemeris_coverage(db)
    assert r.status == FAIL
    assert r.data["calendar_epoch_start"] == "1962-03-01"  # the LATEST start, not 1900
    assert r.data["epoch_start_later_than_nominal"] is True
    assert any("ADJUDICATION-5" in f for f in r.findings)


def test_v2_epoch_end_is_min_over_bodies():
    rows = _coverage_rows()
    rows[1] = {
        "body": "Moon",
        "first_date": "1900-01-01",
        "last_date": "2060-12-31",
        "n_rows": 58_804,
        "n_dates": 58_804,
    }
    db = _FakeDB([_tables("ephemeris_daily"), ("MIN(date) AS first_date", rows)])
    r = validate_v2_ephemeris_coverage(db)
    assert r.data["calendar_epoch_end"] == "2060-12-31"
    assert r.status == FAIL  # 2060 < the required 2084 chart-anchored horizon


def test_v2_detects_a_cadence_gap_and_samples_it():
    rows = _coverage_rows()
    rows[0] = {
        "body": "Sun",
        "first_date": "1900-01-01",
        "last_date": "2150-12-31",
        "n_rows": 91_670,
        "n_dates": 91_670,  # 6 dates short of the span => a gap
    }
    db = _FakeDB(
        [
            _tables("ephemeris_daily"),
            ("MIN(date) AS first_date", rows),
            (
                "LAG(date)",
                [{"prev_date": "1975-01-01", "next_date": "1975-01-08", "gap_days": 7}],
            ),
        ]
    )
    r = validate_v2_ephemeris_coverage(db)
    assert r.status == FAIL
    assert r.data["gap_bodies"] == ["Sun"]
    assert r.data["gap_samples"]["Sun"][0]["missing_from"] == "1975-01-02"


def test_v2_missing_body_fails():
    db = _FakeDB(
        [
            _tables("ephemeris_daily"),
            ("MIN(date) AS first_date", _coverage_rows(bodies=NINE_BODIES[:-1])),
        ]
    )
    r = validate_v2_ephemeris_coverage(db)
    assert r.status == FAIL
    assert r.data["missing_bodies"] == ["Ketu"]


def test_v2_indeterminate_when_table_absent():
    r = validate_v2_ephemeris_coverage(_FakeDB([]))
    assert r.status == INDETERMINATE
    assert r.reason


# ─────────────────────────────────────────────────────────────────────────────
# V1 — profile split
# ─────────────────────────────────────────────────────────────────────────────


def _progress_rows(n=5, step_seconds=200, fp="fp1"):
    rows = []
    for i in range(n):
        rows.append(
            {
                "substep_key": f"career_advancement:year:{i}",
                "build_fingerprint": fp,
                "rows_written": 40,
                "completed_at": f"2026-07-24T15:{(i * step_seconds) // 60:02d}:"
                f"{(i * step_seconds) % 60:02d}+00:00",
            }
        )
    return rows


def test_v1_is_indeterminate_when_no_phase_instrumentation_exists():
    db = _FakeDB(
        [
            _tables("build_substep_progress"),
            ("information_schema.columns", []),  # no phase-timing columns anywhere
            ("build_substep_progress WHERE asset_id", _progress_rows()),
        ]
    )
    r = validate_v1_profile_split(db, [CHART_A])
    assert r.status == INDETERMINATE
    assert "split" in r.reason.lower() or "aggregate" in r.reason.lower()
    # The aggregate IS still measured and reported — the claim is unmet, the
    # data is not withheld.
    assert r.data["per_chart"][CHART_A]["substep_wall_clock"]["n"] == 4
    assert r.data["per_chart"][CHART_A]["substep_wall_clock"]["median_seconds"] == 200.0


def test_v1_passes_when_phase_instrumentation_is_present():
    db = _FakeDB(
        [
            _tables("build_substep_progress"),
            (
                "information_schema.columns",
                [{"table_name": "writer_profile", "column_name": "phase_seconds"}],
            ),
            ("build_substep_progress WHERE asset_id", _progress_rows()),
        ]
    )
    r = validate_v1_profile_split(db, [CHART_A])
    assert r.status == PASS
    assert r.data["phase_profile_source"]["matches"]


def test_v1_excludes_dispatch_gaps_and_reports_the_exclusion():
    rows = _progress_rows(n=3, step_seconds=100)
    rows.append(
        {
            "substep_key": "career_advancement:year:99",
            "build_fingerprint": "fp1",
            "rows_written": 1,
            "completed_at": "2026-07-25T15:00:00+00:00",  # ~24h later
        }
    )
    db = _FakeDB(
        [
            _tables("build_substep_progress"),
            ("information_schema.columns", []),
            ("build_substep_progress WHERE asset_id", rows),
        ]
    )
    r = validate_v1_profile_split(db, [CHART_A])
    excluded = r.data["per_chart"][CHART_A]["excluded_deltas"]
    assert excluded["n"] == 1
    assert excluded["total_seconds"] > 3600
    # The gap is NOT averaged into the substep cost.
    assert r.data["per_chart"][CHART_A]["substep_wall_clock"]["max_seconds"] == 100.0


# ─────────────────────────────────────────────────────────────────────────────
# V3 — spline numerics (pure helpers; no DB, no swisseph needed)
# ─────────────────────────────────────────────────────────────────────────────


def test_angular_delta_takes_the_short_way_round_the_wrap():
    from services.w2g_validations.v3_spline_accuracy import angular_delta_deg

    assert angular_delta_deg(1.0, 359.0) == pytest.approx(2.0)
    assert angular_delta_deg(359.0, 1.0) == pytest.approx(-2.0)
    assert angular_delta_deg(10.0, 10.0) == pytest.approx(0.0)


def test_spline_fit_survives_the_360_wrap():
    """A naive spline across 359 -> 1 swings ~360 deg. The unwrapped fit must
    recover the true, small motion instead."""
    pytest.importorskip("scipy")
    from services.w2g_validations.v3_spline_accuracy import fit_longitude_spline

    jds = [2451545.0 + i for i in range(8)]
    lons = [(356.0 + 1.0 * i) % 360.0 for i in range(8)]  # crosses the wrap
    evaluate = fit_longitude_spline(jds, lons)
    # Half-way between the knots straddling 360 -> 0.
    mid = evaluate(2451545.0 + 4.5)
    assert mid == pytest.approx(0.5, abs=1e-6)


def test_spline_reproduces_its_own_knots_exactly():
    pytest.importorskip("scipy")
    from services.w2g_validations.v3_spline_accuracy import fit_longitude_spline

    jds = [2451545.0 + i for i in range(10)]
    lons = [(100.0 + 13.2 * i) % 360.0 for i in range(10)]
    evaluate = fit_longitude_spline(jds, lons)
    for jd, lon in zip(jds, lons):
        assert evaluate(jd) == pytest.approx(lon, abs=1e-8)


def test_v3_indeterminate_without_the_position_table():
    pytest.importorskip("swisseph")
    pytest.importorskip("scipy")
    r = validate_v3_spline_accuracy(_FakeDB([]))
    assert r.status == INDETERMINATE
    assert "ephemeris_daily" in r.reason


# ─────────────────────────────────────────────────────────────────────────────
# V4 — transition sizing
# ─────────────────────────────────────────────────────────────────────────────


def _v4_db(total_variation_per_body=13_000.0, n_targets=80):
    return _FakeDB(
        [
            _tables("ephemeris_daily", "gochara_resonance_map"),
            (
                "total_variation_deg",
                [
                    {
                        "body": b,
                        "total_variation_deg": total_variation_per_body,
                        "n_steps": 67_000,
                        "variation_first_date": "1900-01-01",
                        "variation_last_date": "2084-12-31",
                    }
                    for b in NINE_BODIES
                ],
            ),
            (
                "sign_ingresses",
                [
                    {
                        "body": b,
                        "sign_ingresses": 150,
                        "nakshatra_ingresses": 340,
                        "stations": 20,
                    }
                    for b in NINE_BODIES
                ],
            ),
            (
                "FROM gochara_resonance_map WHERE chart_id",
                [{"chart_id": CHART_A, "event_class": "marriage", "n": n_targets}],
            ),
        ]
    )


def test_v4_crossings_come_from_measured_angular_variation():
    db = _v4_db(total_variation_per_body=3600.0, n_targets=10)
    r = validate_v4_transition_sizing(db, [CHART_A], date(1900, 1, 1), date(2084, 12, 31))
    # 3600 deg of travel per body = 10 crossings of any fixed degree, x 9 bodies = 90.
    assert r.data["sum_crossings_per_fixed_degree_all_bodies"] == pytest.approx(90.0)
    # 10 targets x 90 crossings x 3 events per crossing = 2700 -> below the band.
    assert r.data["per_chart"][CHART_A]["estimated_contact_events"] == 2700
    assert r.status == FAIL
    assert any("BELOW" in f for f in r.findings)


def test_v4_passes_inside_the_design_tens_of_thousands_band():
    db = _v4_db(total_variation_per_body=3600.0, n_targets=80)
    r = validate_v4_transition_sizing(db, [CHART_A], date(1900, 1, 1), date(2084, 12, 31))
    assert r.data["per_chart"][CHART_A]["estimated_contact_events"] == 21_600
    assert r.status == PASS


def test_v4_splits_eager_from_lazy_moon_layer():
    """Design §2.5 defers the Moon to a lazy layer, so one undifferentiated
    total would misattribute the architecture's own savings."""
    db = _v4_db(total_variation_per_body=3600.0, n_targets=80)
    r = validate_v4_transition_sizing(db, [CHART_A], date(1900, 1, 1), date(2084, 12, 31))
    chart = r.data["per_chart"][CHART_A]
    # 8 non-Moon bodies x 10 crossings x 80 targets x 3 = 19,200.
    assert chart["estimated_contact_events_eager_layer"] == 19_200
    assert chart["estimated_contact_events_lazy_layer"] == 2_400
    assert (
        chart["estimated_contact_events_eager_layer"]
        + chart["estimated_contact_events_lazy_layer"]
        == chart["estimated_contact_events"]
    )
    assert r.data["lazy_layer_bodies"] == ["Moon"]


def test_v4_sql_uses_mod_not_percent():
    """Regression guard, found LIVE not in review: a bare `%` in a
    parameterised statement makes psycopg raise `incomplete placeholder`, so
    the whole validation dies before it measures anything."""
    from services.w2g_validations.v4_transition_sizing import (
        _global_transition_sql,
        _shortest_arc_sum_sql,
    )

    for sql in (_shortest_arc_sum_sql(), _global_transition_sql()):
        # Every remaining `%` must be a `%s` placeholder.
        assert sql.count("%") == sql.count("%s"), sql


def test_v4_indeterminate_without_targets():
    db = _v4_db(n_targets=0)
    db.routes[3] = ("FROM gochara_resonance_map WHERE chart_id", [])
    r = validate_v4_transition_sizing(db, [CHART_A], date(1900, 1, 1), date(2084, 12, 31))
    assert r.status == INDETERMINATE
    # The global calendar is still reported — an unmeasurable chart claim does
    # not suppress the measurable global one.
    assert r.data["global_calendar_totals"]["all_families"] > 0


# ─────────────────────────────────────────────────────────────────────────────
# V5 — corpus completeness + generation stamp
# ─────────────────────────────────────────────────────────────────────────────


def _v5_db(
    substeps_a=303,
    substeps_b=303,
    generation_column=False,
    n_event_classes=3,
    sources=("live",),
):
    cols = [{"column_name": c} for c in ("id", "chart_id", "event_class", "source")]
    if generation_column:
        cols.append({"column_name": "generation"})
    return _FakeDB(
        [
            _tables("kala_gochara_windows", "build_substep_progress", "gochara_resonance_map"),
            ("information_schema.columns", cols),
            ("table_name LIKE", [{"table_name": "kala_gochara_windows__ssv_20260728c"}]),
            (
                "MIN(window_start)",
                [
                    {
                        "chart_id": CHART_A,
                        "n_rows": 8345,
                        "first_window": "1984-01-01",
                        "last_window": "2084-12-31",
                        "n_event_classes": 3,
                        "n_sources": 1,
                    },
                    {
                        "chart_id": CHART_B,
                        "n_rows": 5680,
                        "first_window": "1985-01-01",
                        "last_window": "2084-03-01",
                        "n_event_classes": 3,
                        "n_sources": 1,
                    },
                ],
            ),
            (
                "GROUP BY chart_id, source",
                [
                    {"chart_id": c, "source": s, "n": 100}
                    for c in (CHART_A, CHART_B)
                    for s in sources
                ],
            ),
            (
                "FROM gochara_resonance_map",
                [
                    {"chart_id": CHART_A, "n_event_classes": n_event_classes},
                    {"chart_id": CHART_B, "n_event_classes": n_event_classes},
                ],
            ),
            (
                "FROM build_substep_progress WHERE asset_id",
                [
                    {"chart_id": CHART_A, "n_substeps": substeps_a, "n_fingerprints": 1},
                    {"chart_id": CHART_B, "n_substeps": substeps_b, "n_fingerprints": 1},
                ],
            ),
        ]
    )


def test_v5_fails_when_a_tier1_corpus_is_incomplete_despite_having_rows():
    """Row count is a PROXY; the substep plan is the claim (§N.8)."""
    r = validate_v5_corpus_readiness(_v5_db(substeps_b=211, generation_column=True), [CHART_A, CHART_B])
    assert r.status == FAIL
    assert r.data["incomplete_tier1_charts"] == [CHART_B]
    entry = r.data["per_chart"][CHART_B]
    assert entry["rows"] == 5680 and entry["complete"] is False
    assert entry["substeps_missing"] == 92
    assert any("INCOMPLETE" in f for f in r.findings)


def test_v5_fails_when_no_generation_discriminator_exists():
    r = validate_v5_corpus_readiness(_v5_db(generation_column=False), [CHART_A, CHART_B])
    assert r.status == FAIL
    assert r.data["provenance"]["per_row_discriminator_exists"] is False
    assert any("ADJUDICATION-6" in f for f in r.findings)


def test_v5_passes_when_complete_and_stamped():
    r = validate_v5_corpus_readiness(
        _v5_db(generation_column=True, sources=("v1", "v2")), [CHART_A, CHART_B]
    )
    assert r.status == PASS
    assert r.data["provenance"]["generation_columns_found"] == ["generation"]


def test_v5_flags_a_single_valued_source_column_as_no_discriminator():
    r = validate_v5_corpus_readiness(_v5_db(generation_column=True), [CHART_A, CHART_B])
    assert any("`source`" in f and "untouchable" in f for f in r.findings)


# ─────────────────────────────────────────────────────────────────────────────
# V6 — divergence classifier (design §3.2)
# ─────────────────────────────────────────────────────────────────────────────


def _w(start, end, **extra):
    return {"window_start": start, "window_end": end, **extra}


def test_agreement_within_v1s_own_one_day_resolution():
    out = classify_divergence(
        _w(date(2013, 12, 1), date(2013, 12, 20)),
        _w(date(2013, 12, 1), date(2013, 12, 21)),
    )
    assert out["class"] == CLASS_AGREEMENT


def test_chunk_boundary_edges_classify_as_v1_grid_artifact():
    out = classify_divergence(
        _w(date(2013, 1, 1), date(2013, 12, 31)),
        _w(date(2013, 6, 4), date(2013, 8, 2)),
    )
    assert out["class"] == CLASS_A_V1_GRID_ARTIFACT
    assert any("chunk boundary" in e for e in out["evidence"])


def test_subday_moon_only_row_classifies_as_undersampling_miss():
    out = classify_divergence(
        None,
        _w(date(2013, 6, 4), date(2013, 6, 4), sub_day=True, transiting_bodies=["Moon", "Venus"]),
    )
    assert out["class"] == CLASS_B_V1_MOON_UNDERSAMPLING


def test_subday_row_without_the_moon_is_not_silently_called_undersampling():
    out = classify_divergence(
        None,
        _w(date(2013, 6, 4), date(2013, 6, 4), sub_day=True, transiting_bodies=["Saturn"]),
    )
    assert out["class"] == UNCLASSIFIED


def test_full_day_2_0_only_row_is_a_candidate_2_0_bug():
    out = classify_divergence(
        None, _w(date(2013, 3, 2), date(2013, 5, 9), sub_day=False, transiting_bodies=["Jupiter"])
    )
    assert out["class"] == CLASS_C_CANDIDATE_2_0_BUG


def test_mid_month_disagreement_is_unclassified_not_defaulted():
    out = classify_divergence(
        _w(date(2013, 3, 14), date(2013, 4, 2)),
        _w(date(2013, 2, 1), date(2013, 4, 2)),
    )
    assert out["class"] == UNCLASSIFIED
    assert out["delta_days"]["start_days"] == 41


def test_divergence_report_counts_every_row_exactly_once():
    v1 = [
        {"event_class": "marriage", "peak_date": date(2013, 12, 11),
         "window_start": date(2013, 12, 1), "window_end": date(2013, 12, 20)},
        {"event_class": "marriage", "peak_date": date(2013, 7, 4),
         "window_start": date(2013, 1, 1), "window_end": date(2013, 12, 31)},
    ]
    cand = [
        {"event_class": "marriage", "peak_date": date(2013, 12, 11),
         "window_start": date(2013, 12, 1), "window_end": date(2013, 12, 21)},
        {"event_class": "marriage", "peak_date": date(2013, 7, 4),
         "window_start": date(2013, 7, 1), "window_end": date(2013, 7, 8)},
        {"event_class": "marriage", "peak_date": date(2013, 2, 2),
         "window_start": date(2013, 2, 2), "window_end": date(2013, 2, 2),
         "sub_day": True, "transiting_bodies": ["Moon"]},
    ]
    report = run_divergence_report(v1, cand)
    assert report["total_pairings"] == 3
    assert sum(report["counts"].values()) == 3
    assert report["counts"][CLASS_AGREEMENT] == 1
    assert report["counts"][CLASS_A_V1_GRID_ARTIFACT] == 1
    assert report["counts"][CLASS_B_V1_MOON_UNDERSAMPLING] == 1
    assert report["zero_unclassified"] is True
    assert report["divergence_rate"] == pytest.approx(2 / 3)


def test_divergence_report_surfaces_unclassified_rows_loudly():
    v1 = [{"event_class": "marriage", "peak_date": date(2013, 5, 5),
           "window_start": date(2013, 5, 1), "window_end": date(2013, 5, 9)}]
    cand = [{"event_class": "marriage", "peak_date": date(2013, 5, 5),
             "window_start": date(2013, 3, 1), "window_end": date(2013, 5, 9)}]
    report = run_divergence_report(v1, cand)
    assert report["counts"][UNCLASSIFIED] == 1
    assert report["zero_unclassified"] is False


def test_v6_reports_indeterminate_because_the_2_0_side_does_not_exist():
    db = _FakeDB(
        [
            _tables("kala_gochara_windows"),
            (
                "FROM kala_gochara_windows WHERE chart_id",
                [
                    {"event_class": "marriage", "temporal_shape": "point",
                     "window_start": "2013-01-01", "window_end": "2013-12-31",
                     "peak_date": "2013-06-01"},
                    {"event_class": "marriage", "temporal_shape": "point",
                     "window_start": "2013-03-04", "window_end": "2013-04-02",
                     "peak_date": "2013-03-20"},
                ],
            ),
        ]
    )
    r = validate_v6_divergence_pilot(db, [CHART_A], 2013)
    assert r.status == INDETERMINATE
    assert "2.0" in r.reason
    census = r.data["per_chart_census"][CHART_A]
    assert census["rows_in_year"] == 2
    assert census["chunk_boundary_coincident_rows"] == 1
    assert r.data["classifier_self_check"]["zero_unclassified"] is True


# ─────────────────────────────────────────────────────────────────────────────
# runner + bind gate
# ─────────────────────────────────────────────────────────────────────────────


def test_bind_gate_blocks_on_indeterminate_not_only_on_fail():
    report = {"summary": {"pass": ["V2"], "fail": [], "indeterminate": ["V1"]}}
    gate = bind_gate(report)
    assert gate["may_proceed"] is False
    assert gate["blocked_by_indeterminate"] == ["V1"]


def test_bind_gate_opens_only_when_everything_passes():
    report = {"summary": {"pass": ["V1", "V2"], "fail": [], "indeterminate": []}}
    assert bind_gate(report)["may_proceed"] is True


def test_run_all_produces_six_results_and_a_wave_stamp():
    report = run_all(_FakeDB([]))  # empty DB — every validation degrades honestly
    assert report["wave"] == "W2G"
    ids = [r["validation_id"] for r in report["results"]]
    assert ids == ["V1", "V2", "V3", "V4", "V5", "V6"]
    assert not report["summary"]["pass"]  # nothing may pass against nothing


def test_run_all_sizes_v4_over_the_epoch_v2_measured():
    """ADJUDICATION-5: the epoch is derived from live coverage, so V4 must be
    sized over the MEASURED epoch, not a constant."""
    rows = _coverage_rows()
    rows[3] = {"body": "Mercury", "first_date": "1930-01-01", "last_date": "2150-12-31",
               "n_rows": 80_674, "n_dates": 80_674}
    db = _FakeDB([_tables("ephemeris_daily"), ("MIN(date) AS first_date", rows)])
    report = run_all(db)
    assert report["epoch_used_for_sizing"][0] == "1930-01-01"


# ─────────────────────────────────────────────────────────────────────────────
# LIVE — excluded by `-m "not integration"`
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="no DATABASE_URL")
def test_live_bind_validations_run_end_to_end():
    import psycopg

    from services.w2g_validations import query_fn_from_conn

    with psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row) as conn:
        report = run_all(query_fn_from_conn(conn))

    assert len(report["results"]) == 6
    # Every result is well-formed: an INDETERMINATE must carry its reason.
    for r in report["results"]:
        assert r["status"] in (PASS, FAIL, INDETERMINATE)
        if r["status"] == INDETERMINATE:
            assert r["reason"]
    # Read-only posture: the live corpus is untouched by this run.
    with psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row) as conn:
        cur = conn.execute("SELECT COUNT(*) AS n FROM kala_gochara_windows")
        assert cur.fetchone()["n"] > 0
