"""
tests/test_ka_gochara_sweep.py — D-5 Lane G-4 "Forward sweep + serving" tests.

No DATABASE_URL required for the bulk of this suite — `shape_output.py` is a
pure module (constructed `IntensityResult` fixtures, real `swisseph` JD<->date
conversion, no DB/network), mirroring `tests/test_gochara_grammar.py` and
`tests/test_gochara_intensity.py`'s own documented pattern. The writer
resumption tests exercise `KaGocharaSweepWriter`'s pure helper methods
(`_compute_build_fingerprint`, `_load_completed_substeps`) against fake
connection objects, same technique as `tests/test_ka_sangam_resumption.py`.
The "sweep.py: order-independent continuity" section drives the REAL
`sweep.sweep_event_class_chunk` (the production continuity mechanism, D-5
RED-C fix v2) with its DB-touching dependencies replaced via `monkeypatch`
(a deterministic synthetic activation calendar standing in for
`compute_lambda_e`/`compute_lambda_e_series`) — still no live DB, but
exercises the actual dispatch-order-independence property end to end,
including OUT-OF-ORDER dispatch (a later year running before an earlier
one), not just the pure `shape_output` layer.
`@pytest.mark.integration` tests at the bottom hit the LIVE Cloud SQL proxy
(127.0.0.1:5433) when reachable and are excluded by the mandated
`-m "not integration"` pytest invocation.
"""
from __future__ import annotations

from datetime import date, timedelta

import swisseph as swe
import pytest

from pipeline.orchestrator.writers import SubStep
from services.gochara_intensity.models import IntensityResult
from services.ka_gochara_sweep import shape_output as SO
from services.ka_gochara_sweep.writer import KaGocharaSweepWriter

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _jd(y, m, d, h=12.0):
    return swe.julday(y, m, d, h)


def _result(event_class, t_jd, raw_lambda, is_adverse=False, valence="gain", shape="point"):
    signed = raw_lambda * (-1.0 if is_adverse else 1.0)
    return IntensityResult(
        chart_id=CHART_ID,
        event_class=event_class,
        temporal_shape=shape,
        t_jd=t_jd,
        t_datetime_ist=None,
        promise=0.5,
        promise_detail={},
        permission=0.5,
        permission_detail={"systems": [{"system_id": "vimshottari", "active": True, "weight": 0.16}],
                            "calibration_state": "structural_prior"},
        x_t=1.0,
        x_t_detail={},
        beta_e=1.0,
        beta_e_calibration_state="structural_prior",
        exp_term=1.0,
        suppression=0.0,
        suppression_detail={"note": "test fixture"},
        raw_lambda=raw_lambda,
        valence=valence,
        is_adverse=is_adverse,
        signed_lambda=signed,
        source="fixture",
    )


# ── shape_output: point ──────────────────────────────────────────────────

def test_point_shape_emits_single_dated_peak_never_a_span():
    # Three days of activity around a peak on 2013-12-11 (the wave's named
    # marriage double-transit specimen date).
    series = [
        _result("marriage", _jd(2013, 12, 9), 0.3),
        _result("marriage", _jd(2013, 12, 10), 0.6),
        _result("marriage", _jd(2013, 12, 11), 0.9),  # peak
        _result("marriage", _jd(2013, 12, 12), 0.4),
        _result("marriage", _jd(2013, 12, 13), 0.0),  # inactive -- ends the run
    ]
    rows = SO.build_point_rows(swe, "marriage", series)
    assert len(rows) == 1
    row = rows[0]
    assert row["temporal_shape"] == "point"
    assert row["window_start"] == row["window_end"] == row["peak_date"]
    assert row["peak_date"].isoformat() == "2013-12-11"
    assert row["milestone_id"] is None
    assert row["raw_intensity"] == pytest.approx(0.9)
    assert row["peak_basis"] == "gochara_lambda_e_v1"


def test_point_shape_multiple_disjoint_runs_emit_multiple_rows():
    series = [
        _result("marriage", _jd(2013, 12, 11), 0.9),
        _result("marriage", _jd(2013, 12, 12), 0.0),
        _result("marriage", _jd(2014, 1, 5), 0.5),
    ]
    rows = SO.build_point_rows(swe, "marriage", series)
    assert len(rows) == 2


def test_point_shape_no_activity_emits_no_rows():
    series = [_result("marriage", _jd(2020, 1, d), 0.0) for d in range(1, 5)]
    rows = SO.build_point_rows(swe, "marriage", series)
    assert rows == []


# ── shape_output: interval ───────────────────────────────────────────────

def test_interval_shape_never_degenerates_to_a_single_day():
    # A short 3-day detected run for major_gain (duration_prior min_days=14,
    # typical_days=90, per live brahma_event_ontology, migration 456).
    series = [
        _result("major_gain", _jd(2010, 7, 1), 0.2, valence="gain", shape="interval"),
        _result("major_gain", _jd(2010, 7, 2), 0.5, valence="gain", shape="interval"),
        _result("major_gain", _jd(2010, 7, 3), 0.3, valence="gain", shape="interval"),
    ]
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    rows = SO.build_interval_rows(swe, "major_gain", series, duration_prior)
    assert len(rows) == 1
    row = rows[0]
    assert row["temporal_shape"] == "interval"
    assert row["window_start"] < row["window_end"]
    span_days = (row["window_end"] - row["window_start"]).days
    assert span_days >= 14, "interval-shaped row must never be narrower than duration_prior.min_days"
    # peak_date should be inside the (possibly widened) span
    assert row["window_start"] <= row["peak_date"] <= row["window_end"]


def test_interval_shape_named_windfall_specimen_spans_not_points():
    """BRIEF_D5 §2 named specimen: the 2010-07 -> 2011-03 windfall interval
    (chart 482012f1, event_id bd7f5711..., shape='interval') -- the engine's
    interval-shaped output must show elevated intensity SPANNING the window,
    not a single point. This constructs a fixture series covering that
    range with one clear elevated run and asserts the served row is a real
    multi-day span overlapping the named window, per BRIEF_D5 §2's
    specimen-reproduction acceptance bar (fixture form; live reproduction is
    covered separately in this lane's close-report verification pass)."""
    days = []
    d = _jd(2010, 7, 1)
    while d <= _jd(2011, 3, 1):
        days.append(d)
        d += 5.0  # coarse fixture grid, not the real daily sweep
    series = [_result("major_gain", jd, 0.4, valence="gain", shape="interval") for jd in days]
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    rows = SO.build_interval_rows(swe, "major_gain", series, duration_prior)
    assert len(rows) == 1
    row = rows[0]
    assert row["window_start"].isoformat() <= "2010-07-06"
    assert row["window_end"].isoformat() >= "2011-02-24"
    assert (row["window_end"] - row["window_start"]).days > 200


def test_interval_shape_no_duration_prior_falls_back_honestly():
    series = [_result("career_setback", _jd(2015, 1, 1), 0.2, is_adverse=True, valence="loss", shape="interval")]
    rows = SO.build_interval_rows(swe, "career_setback", series, duration_prior=None)
    assert len(rows) == 1
    span_days = (rows[0]["window_end"] - rows[0]["window_start"]).days
    assert span_days >= SO.FALLBACK_INTERVAL_DAYS - 1  # padding rounding tolerance
    assert rows[0]["is_adverse"] is True
    assert rows[0]["signed_intensity"] < 0


def test_interval_shape_never_wider_than_max_days_cap():
    """D-5 RED-C fix: the original bug enforced NO ceiling at all on an
    interval row's width. A single very-long detected run must be clipped
    down to duration_prior.max_days, not served at its full raw length."""
    series = [_result("major_gain", _jd(2010, 1, 1) + i, 0.3, valence="gain", shape="interval")
              for i in range(500)]  # a 500-day-wide raw run
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 200}
    rows = SO.build_interval_rows(swe, "major_gain", series, duration_prior)
    assert len(rows) == 1
    assert (rows[0]["window_end"] - rows[0]["window_start"]).days <= 200


# ── shape_output: chain ──────────────────────────────────────────────────

def test_chain_shape_one_row_per_milestone_with_irreversibility_flag():
    anchor = _result("business_launch", _jd(2020, 1, 1), 0.5, valence="gain", shape="chain")
    milestone_template = [
        {"milestone_id": "decision", "name_en": "Decision to found/launch", "typical_offset_days_from_first": 0},
        {"milestone_id": "registration", "name_en": "Legal/business registration", "typical_offset_days_from_first": 45},
        {"milestone_id": "first_revenue", "name_en": "First revenue booked", "typical_offset_days_from_first": 120},
    ]
    milestone_results = [
        (m, _result("business_launch", anchor.t_jd + m["typical_offset_days_from_first"], 0.4 + i * 0.1,
                     valence="gain", shape="chain"))
        for i, m in enumerate(milestone_template)
    ]
    rows = SO.build_chain_rows(swe, "business_launch", anchor, milestone_results, "first_revenue")
    assert len(rows) == 3
    assert {r["temporal_shape"] for r in rows} == {"chain"}
    assert {r["milestone_id"] for r in rows} == {"decision", "registration", "first_revenue"}
    # Each row is its OWN dated sub-window, not a shared span.
    for r in rows:
        assert r["window_start"] == r["window_end"] == r["peak_date"]
    irr_rows = [r for r in rows if r["is_irreversibility_milestone"]]
    assert len(irr_rows) == 1
    assert irr_rows[0]["milestone_id"] == "first_revenue"
    # Milestone dates are offset from the anchor, not identical.
    dates = sorted(r["peak_date"] for r in rows)
    assert dates[0] < dates[-1]


def test_chain_shape_no_irreversibility_milestone_flags_none():
    anchor = _result("career_change", _jd(2018, 6, 1), 0.5, shape="chain")
    milestone_template = [{"milestone_id": "resignation_or_decision", "typical_offset_days_from_first": 0}]
    milestone_results = [(milestone_template[0], anchor)]
    rows = SO.build_chain_rows(swe, "career_change", anchor, milestone_results, irreversibility_milestone=None)
    assert rows[0]["is_irreversibility_milestone"] is False


# ── dispatcher ────────────────────────────────────────────────────────────

def test_dispatcher_reads_shape_never_hardcodes_it():
    series = [_result("marriage", _jd(2013, 12, 11), 0.9)]
    rows = SO.build_rows_for_event_class(swe, "marriage", "point", series=series)
    assert rows[0]["temporal_shape"] == "point"


def test_dispatcher_unknown_shape_raises_not_silently_defaults():
    with pytest.raises(ValueError):
        SO.build_rows_for_event_class(swe, "x", "not_a_real_shape", series=[])


# ── idempotent re-run (shape_output level: same fixture -> same rows) ────

def test_idempotent_rebuild_same_series_same_rows():
    series = [
        _result("marriage", _jd(2013, 12, 10), 0.6),
        _result("marriage", _jd(2013, 12, 11), 0.9),
    ]
    rows_a = SO.build_point_rows(swe, "marriage", series)
    rows_b = SO.build_point_rows(swe, "marriage", series)
    assert rows_a == rows_b


# ── writer resumption (mirrors tests/test_ka_sangam_resumption.py pattern) ─

class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
    def execute(self, *a, **kw):
        pass
    def fetchall(self):
        return self._rows
    def fetchone(self):
        return self._rows[0] if self._rows else None


class _FakeConn:
    def __init__(self, rows):
        self._rows = rows
    def cursor(self, *a, **kw):
        return _FakeCursor(self._rows)


def _writer(event_classes=("marriage", "major_gain"), birth_year=1950):
    w = KaGocharaSweepWriter()
    w._event_classes = list(event_classes)
    w._birth_year = birth_year
    return w


def test_fingerprint_stable_across_instances_with_same_inputs():
    a = _writer()._compute_build_fingerprint("chartX")
    b = _writer()._compute_build_fingerprint("chartX")
    assert a == b


def test_fingerprint_changes_with_event_classes():
    a = _writer(event_classes=("marriage",))._compute_build_fingerprint("chartX")
    b = _writer(event_classes=("marriage", "career_advancement"))._compute_build_fingerprint("chartX")
    assert a != b


def test_fingerprint_changes_with_birth_year():
    a = _writer(birth_year=1950)._compute_build_fingerprint("chartX")
    b = _writer(birth_year=1984)._compute_build_fingerprint("chartX")
    assert a != b


def test_empty_ledger_returns_none_first_run():
    w = _writer()
    assert w._load_completed_substeps(_FakeConn([]), "cid", "fp") is None


def test_matching_fingerprint_returns_completed_keys_for_resume():
    rows = [
        {"substep_key": "marriage:year:0", "build_fingerprint": "fp"},
        {"substep_key": "marriage:year:1", "build_fingerprint": "fp"},
    ]
    w = _writer()
    completed = w._load_completed_substeps(_FakeConn(rows), "cid", "fp")
    assert completed == {"marriage:year:0", "marriage:year:1"}


def test_mismatched_fingerprint_forces_replan_all():
    rows = [{"substep_key": "marriage:year:0", "build_fingerprint": "OLD"}]
    w = _writer()
    assert w._load_completed_substeps(_FakeConn(rows), "cid", "fp_new") is None


def test_substep_key_encodes_event_class_and_year():
    """plan_substeps' key format `<event_class>:year:<idx>` must round-trip
    through run_substep's own rpartition parse. (D-5 REBUILD chunking fix,
    2026-07-20: re-chunked from decade-sized to year-sized substeps -- a
    real Cloud Run dispatch hit the 1800s writer_timeout_seconds watchdog on
    a single decade substep with zero rows committed.)"""
    key = "career_advancement:year:37"
    event_class, _, year_str = key.rpartition(":year:")
    assert event_class == "career_advancement"
    assert int(year_str) == 37


def test_plan_substeps_produces_year_granularity_not_decade():
    """Regression guard for the D-5 REBUILD chunking fix: plan_substeps must
    emit one substep per (event_class x year) -- 100 per event_class over
    the 100-year horizon -- not the old one-per-decade (10 per event_class)
    grain that timed out against real data."""
    from services.ka_gochara_sweep.writer import _N_YEARS, _HORIZON_YEARS
    assert _N_YEARS == _HORIZON_YEARS == 100


def test_substep_sort_key_orders_years_numerically_not_lexically():
    """D-5 RED-C independent-verification finding: the stable sort in
    `plan_substeps` used to key on the raw `step.key` STRING, so
    "…:year:10" sorted lexically BEFORE "…:year:9" -- a real, independent
    dispatch-order bug (on top of specimen-priority reordering) that a
    carry-based continuity fix would have silently broken under. Drives the
    real `_substep_sort_key` (not a reimplementation) directly."""
    from services.ka_gochara_sweep.writer import _substep_sort_key

    steps = [SubStep(key="major_gain:year:9", label="y9"), SubStep(key="major_gain:year:10", label="y10"),
             SubStep(key="major_gain:year:2", label="y2"), SubStep(key="major_gain:year:100", label="y100")]
    ordered = sorted(steps, key=lambda s: _substep_sort_key(s, priority_years=set()))
    assert [s.key for s in ordered] == [
        "major_gain:year:2", "major_gain:year:9", "major_gain:year:10", "major_gain:year:100",
    ], "years must sort numerically (2, 9, 10, 100), not lexically (10, 100, 2, 9)"


def test_substep_sort_key_still_promotes_priority_years_first():
    """Regression guard: fixing the numeric tiebreak must not weaken
    specimen-priority promotion (D-5 GATE fix) -- a priority year must still
    sort ahead of ALL non-priority years, reachable within a handful of
    dispatches, not require materializing a full numeric year-prefix."""
    from services.ka_gochara_sweep.writer import _substep_sort_key

    steps = [SubStep(key="major_gain:year:0", label="y0"), SubStep(key="major_gain:year:1", label="y1"),
             SubStep(key="major_gain:year:60", label="y60"), SubStep(key="major_gain:year:61", label="y61")]
    priority_years = {("major_gain", 60), ("major_gain", 61)}
    ordered = sorted(steps, key=lambda s: _substep_sort_key(s, priority_years))
    assert [s.key for s in ordered] == [
        "major_gain:year:60", "major_gain:year:61", "major_gain:year:0", "major_gain:year:1",
    ]


# ── sweep.py: order-independent continuity (D-5 RED-C fix v2) ─────────────
#
# Independent verification REJECTED the first RED-C fix attempt (cross-
# substep carry state): `plan_substeps` does not dispatch year substeps in
# ascending order (specimen-priority reordering, plus the lexical-sort bug
# above) -- year 10 can run before year 9, silently truncating a carried
# window's tail. These tests drive the REAL `sweep.sweep_event_class_chunk`
# (the actual production mechanism, not a reimplementation) with the DB
# layer mocked out via monkeypatch, and explicitly exercise OUT-OF-ORDER
# dispatch -- a later year running before an earlier one -- asserting the
# served result is IDENTICAL regardless of order (no double-serving, no
# dropped tail).

def _build_activation_calendar(start: date, end: date, raw_lambda: float = 0.3) -> dict:
    cal = {}
    d = start
    while d <= end:
        cal[d.isoformat()] = raw_lambda
        d += timedelta(days=1)
    return cal


def _make_fake_engine(activation: dict):
    """Builds deterministic fake replacements for
    `compute_lambda_e`/`compute_lambda_e_series` driven by a plain
    date->raw_lambda dict -- a pure function of (event_class, jd) with NO
    memory of prior calls, mirroring the real engine's own determinism
    (same inputs, same output, regardless of call order/count)."""
    def _lookup(jd: float) -> float:
        y, m, d, _h = swe.revjul(jd + 5.5 / 24.0)
        return activation.get(date(int(y), int(m), int(d)).isoformat(), 0.0)

    def fake_compute_lambda_e(swe_mod, conn, chart_id, event_class, jd, **kwargs):
        return _result(event_class, jd, _lookup(jd), valence="gain", shape="interval")

    def fake_compute_lambda_e_series(swe_mod, conn, chart_id, event_class, t_start_jd, t_end_jd, step_days,
                                      **kwargs):
        results = []
        t = t_start_jd
        while t <= t_end_jd:  # matches engine.py's own `while t <= t_end_jd` inclusive loop
            results.append(_result(event_class, t, _lookup(t), valence="gain", shape="interval"))
            t += step_days
        return results

    return fake_compute_lambda_e, fake_compute_lambda_e_series


def _patch_sweep_deps(monkeypatch, duration_prior: dict, activation: dict):
    from services.ka_gochara_sweep import sweep as sweep_module

    fake_e, fake_series = _make_fake_engine(activation)
    monkeypatch.setattr(sweep_module, "fetch_ontology_meta", lambda conn, ec: {
        "temporal_shape": "interval", "duration_prior": duration_prior,
        "milestone_template": None, "irreversibility_milestone": None,
    })
    monkeypatch.setattr(sweep_module.RM, "fetch_resonance_targets", lambda conn, cid, ec: [object()])
    monkeypatch.setattr(sweep_module, "enrich_targets",
                         lambda conn, raw, ayanamsha_id="lahiri_chitrapaksha": raw)
    monkeypatch.setattr(sweep_module.DD, "fetch_dasha_periods",
                         lambda conn, cid, ayanamsha_id="lahiri_chitrapaksha": [])
    monkeypatch.setattr(sweep_module, "compute_lambda_e_series", fake_series)
    monkeypatch.setattr(sweep_module, "compute_lambda_e", fake_e)
    monkeypatch.setattr(sweep_module, "gather_configuration_sentences", lambda *a, **kw: [])
    return sweep_module


def _year_chunk(sweep_module, event_class: str, year: int):
    start_jd = _jd(year, 1, 1, h=0.0)
    end_jd = _jd(year + 1, 1, 1, h=0.0)
    return sweep_module.sweep_event_class_chunk(swe, None, CHART_ID, event_class, start_jd, end_jd, step_days=1.0)


_SPECIMEN_ACTIVE_START, _SPECIMEN_ACTIVE_END = date(2010, 7, 1), date(2011, 3, 1)


def test_sweep_chunk_resolves_full_episode_independently_of_sibling_year_ever_running(monkeypatch):
    """The defining property of the order-independent fix: year 2011's OWN
    chunk call, made WITHOUT year 2010's chunk ever having run (no shared
    state exists for it to depend on), still resolves the FULL true episode
    (backward across the Dec-31/Jan-1 boundary into 2010) via its own
    bounded re-evaluation -- not a truncated tail."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    activation = _build_activation_calendar(_SPECIMEN_ACTIVE_START, _SPECIMEN_ACTIVE_END)
    sweep_module = _patch_sweep_deps(monkeypatch, duration_prior, activation)

    rows = _year_chunk(sweep_module, "major_gain", 2011)
    assert len(rows) == 1
    row = rows[0]
    assert row["window_start"].isoformat() <= "2010-07-06"
    assert row["window_end"].isoformat() >= "2011-02-24"
    assert row["window_start"] not in (date(2010, 12, 31), date(2011, 1, 1))
    assert row["window_end"] not in (date(2010, 12, 31), date(2011, 1, 1))


def test_sweep_chunk_out_of_order_dispatch_produces_identical_natural_key(monkeypatch):
    """Reproduces the verifier's exact finding: a LATER year (2011)
    dispatched BEFORE an EARLIER year (2010) that shares the same episode.
    Both dispatch orders must converge on the identical served window --
    the (window_start, window_end, peak_date, milestone_id) natural key the
    DB's ON CONFLICT dedups on (writer.py `_insert_rows`) -- proving no
    double-serving and no dropped tail under out-of-order dispatch."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    activation = _build_activation_calendar(_SPECIMEN_ACTIVE_START, _SPECIMEN_ACTIVE_END)
    sweep_module = _patch_sweep_deps(monkeypatch, duration_prior, activation)

    def _key(rows):
        assert len(rows) == 1
        r = rows[0]
        return (r["window_start"], r["window_end"], r["peak_date"], r["milestone_id"])

    # Ascending order (the OLD assumed order).
    key_2010_ascending = _key(_year_chunk(sweep_module, "major_gain", 2010))
    key_2011_ascending = _key(_year_chunk(sweep_module, "major_gain", 2011))

    # OUT OF ORDER: year 2011 dispatched BEFORE year 2010.
    key_2011_first = _key(_year_chunk(sweep_module, "major_gain", 2011))
    key_2010_second = _key(_year_chunk(sweep_module, "major_gain", 2010))

    assert key_2010_ascending == key_2011_ascending == key_2011_first == key_2010_second, (
        "the served window's natural key must be identical across EVERY call, in EVERY "
        "dispatch order -- a carry-based mechanism keyed to 'the immediately prior substep' "
        "would fail this under out-of-order dispatch (year 10 before year 9)"
    )


def test_sweep_chunk_gate_no_boundary_artifact_under_out_of_order_dispatch(monkeypatch):
    """The RED-C gate assertion (native-mandated), driven through the REAL
    `sweep_event_class_chunk` across three years in REVERSE dispatch order
    (2012, then 2011, then 2010) -- no served window's start/end may
    coincide with a year-chunk boundary (Dec-31/Jan-1) unless the window is
    legitimately duration_prior.max_days-capped."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    activation = _build_activation_calendar(_SPECIMEN_ACTIVE_START, _SPECIMEN_ACTIVE_END)
    sweep_module = _patch_sweep_deps(monkeypatch, duration_prior, activation)

    years = [2012, 2011, 2010]  # deliberately descending -- out of order
    all_rows = []
    for year in years:
        all_rows.extend(_year_chunk(sweep_module, "major_gain", year))

    max_days = duration_prior["max_days"]
    boundary_dates = set()
    for year in (2010, 2011, 2012):
        boundary_dates |= {date(year, 1, 1), date(year, 12, 31)}
    for row in all_rows:
        width_days = (row["window_end"] - row["window_start"]).days
        is_capped = width_days >= max_days
        for edge in (row["window_start"], row["window_end"]):
            if edge in boundary_dates:
                assert is_capped, (
                    f"served window edge {edge.isoformat()} (width={width_days}d) coincides with a "
                    f"year-chunk boundary but is NOT max_days-capped ({max_days}d) -- the RED-C "
                    "chunking-artifact bug"
                )


def test_sweep_chunk_gate_assertion_not_vacuous_without_boundary_extension(monkeypatch):
    """Sanity-check that the gate assertion is a real regression check, not
    trivially satisfied -- disable the order-independent boundary extension
    (monkeypatch it to a no-op passthrough, i.e. exactly the ORIGINAL
    unconditional-per-chunk-close bug this fix removes) and confirm the
    RED-C chunking artifact (a served window edge landing exactly on Dec-31/
    Jan-1, uncapped) reappears."""
    from services.ka_gochara_sweep import sweep as sweep_module

    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    activation = _build_activation_calendar(_SPECIMEN_ACTIVE_START, _SPECIMEN_ACTIVE_END)
    sweep_module = _patch_sweep_deps(monkeypatch, duration_prior, activation)
    monkeypatch.setattr(sweep_module, "_extend_series_across_boundary",
                         lambda swe_mod, conn, chart_id, ec, series, **kwargs: series)

    rows_2010 = _year_chunk(sweep_module, "major_gain", 2010)
    assert len(rows_2010) == 1
    row = rows_2010[0]
    width_days = (row["window_end"] - row["window_start"]).days
    # Without the extension, 2010's chunk closes on the spot at its own
    # last grid day -- `compute_lambda_e_series` (engine.py) loops
    # inclusively through `horizon_end_jd` itself (2011-01-01, the NEXT
    # year's own horizon_start_jd), so that's the exact RED-C artifact
    # boundary here, not Dec-31 -- well short of the true ~2011-03-01 end,
    # and short of the max_days cap too.
    assert row["window_end"] == date(2011, 1, 1)
    assert width_days < duration_prior["max_days"]


def test_sweep_chunk_three_year_span_converges_regardless_of_which_chunk_runs_alone():
    """D-5 RED-C fix v3: second independent verification's exact
    counterexample. A 517-day episode (2010-10-01 -> 2012-03-01) is LONGER
    than duration_prior.max_days (365) -- under the v2 design (discovery
    scan bounded BY max_days), the 2012 chunk sits ~458 days from the true
    2010-10-01 start, farther than its own 365-day scan could reach, so it
    computed a SHORTER, differently-anchored window than the 2010 or 2011
    chunks -- three different (window_start, window_end, peak_date) triples
    for the same real episode, one with peak_date landing exactly on a
    chunk boundary (the artifact relocated, not eliminated).

    This drives EACH of the 2010/2011/2012 chunks completely ALONE (a fresh
    monkeypatch setup per call, exactly mirroring three independent
    Cloud Run dispatches that never share in-memory state) and asserts all
    three converge on the IDENTICAL clipped window."""
    from services.ka_gochara_sweep import sweep as sweep_module

    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    episode_start, episode_end = date(2010, 10, 1), date(2012, 3, 1)
    assert (episode_end - episode_start).days == 517 > duration_prior["max_days"], \
        "the whole point of this test is an episode LONGER than max_days"
    activation = _build_activation_calendar(episode_start, episode_end)

    def _run_alone(monkeypatch, year):
        sweep_module = _patch_sweep_deps(monkeypatch, duration_prior, activation)
        rows = _year_chunk(sweep_module, "major_gain", year)
        assert len(rows) == 1
        r = rows[0]
        return (r["window_start"], r["window_end"], r["peak_date"], r["milestone_id"])

    import _pytest.monkeypatch
    with _pytest.monkeypatch.MonkeyPatch.context() as mp_2010:
        key_2010 = _run_alone(mp_2010, 2010)
    with _pytest.monkeypatch.MonkeyPatch.context() as mp_2011:
        key_2011 = _run_alone(mp_2011, 2011)
    with _pytest.monkeypatch.MonkeyPatch.context() as mp_2012:
        key_2012 = _run_alone(mp_2012, 2012)

    assert key_2010 == key_2011 == key_2012, (
        f"three chunks touching the SAME 517-day episode (> max_days={duration_prior['max_days']}) "
        f"must converge on the IDENTICAL clipped window regardless of which chunk ran, or how far "
        f"from the true start it sits -- got 2010={key_2010}, 2011={key_2011}, 2012={key_2012}"
    )
    # The clip is anchored to the TRUE start (2010-10-01), not to wherever
    # any one chunk's own scan happened to reach.
    window_start, window_end, peak_date, _milestone_id = key_2010
    assert window_start.isoformat() == "2010-10-01"
    assert (window_end - window_start).days <= duration_prior["max_days"]
    # And no boundary-artifact: peak_date must not land on a chunk edge
    # (the verifier's "2012 alone" case put it exactly on one).
    for year in (2010, 2011, 2012):
        assert peak_date not in (date(year, 1, 1), date(year, 12, 31)), \
            f"peak_date {peak_date} lands exactly on a year-chunk boundary -- the RED-C artifact relocated"


# ── integration (live proxy, excluded by -m "not integration") ───────────

LIVE_DSN = "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis"


@pytest.mark.integration
def test_live_sweep_small_window_marriage_specimen():
    import psycopg
    from services.ka_gochara_sweep.sweep import sweep_event_class_chunk

    try:
        conn = psycopg.connect(LIVE_DSN, connect_timeout=10, row_factory=psycopg.rows.dict_row)
    except Exception:
        pytest.skip("live DB proxy not reachable")
    try:
        start_jd = _jd(2013, 11, 15)
        end_jd = _jd(2013, 12, 31)
        rows = sweep_event_class_chunk(swe, conn, CHART_ID, "marriage", start_jd, end_jd, step_days=1.0)
        assert isinstance(rows, list)
        for r in rows:
            assert r["temporal_shape"] == "point"
            assert r["window_start"] == r["window_end"]
    finally:
        conn.close()
