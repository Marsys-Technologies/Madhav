"""
tests/test_ka_gochara_sweep.py — D-5 Lane G-4 "Forward sweep + serving" tests.

No DATABASE_URL required for the bulk of this suite — `shape_output.py` is a
pure module (constructed `IntensityResult` fixtures, real `swisseph` JD<->date
conversion, no DB/network), mirroring `tests/test_gochara_grammar.py` and
`tests/test_gochara_intensity.py`'s own documented pattern. The writer
resumption tests exercise `KaGocharaSweepWriter`'s pure helper methods
(`_compute_build_fingerprint`, `_load_completed_substeps`) against fake
connection objects, same technique as `tests/test_ka_sangam_resumption.py`.
`@pytest.mark.integration` tests at the bottom hit the LIVE Cloud SQL proxy
(127.0.0.1:5433) when reachable and are excluded by the mandated
`-m "not integration"` pytest invocation.
"""
from __future__ import annotations

from datetime import date, timedelta

import swisseph as swe
import pytest

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
    rows, carry = SO.build_interval_rows(swe, "major_gain", series, duration_prior)
    assert carry is None, "a one-shot (force_close default True) call must never leave a dangling carry"
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
    rows, carry = SO.build_interval_rows(swe, "major_gain", series, duration_prior)
    assert carry is None
    assert len(rows) == 1
    row = rows[0]
    assert row["window_start"].isoformat() <= "2010-07-06"
    assert row["window_end"].isoformat() >= "2011-02-24"
    assert (row["window_end"] - row["window_start"]).days > 200


def test_interval_shape_no_duration_prior_falls_back_honestly():
    series = [_result("career_setback", _jd(2015, 1, 1), 0.2, is_adverse=True, valence="loss", shape="interval")]
    rows, carry = SO.build_interval_rows(swe, "career_setback", series, duration_prior=None)
    assert carry is None
    assert len(rows) == 1
    span_days = (rows[0]["window_end"] - rows[0]["window_start"]).days
    assert span_days >= SO.FALLBACK_INTERVAL_DAYS - 1  # padding rounding tolerance
    assert rows[0]["is_adverse"] is True
    assert rows[0]["signed_intensity"] < 0


# ── shape_output: interval continuity across chunk boundaries (D-5 RED-C) ──
#
# RED-C finding: `build_interval_rows` was called once per year-substep chunk
# (writer.py) and closed EVERY still-active run at the chunk's last grid day
# unconditionally -- an activation genuinely still firing across a Dec-31/
# Jan-1 boundary got served as TWO separate ~365-day windows, each EXACTLY
# bounded by the chunk edge, not by any real signal-cessation point or the
# ontology's own `duration_prior.max_days`. These tests exercise the
# continuity-carry fix (`open_run`/`force_close`/tuple return) directly,
# mirroring writer.py's per-year `run_substep` loop closely enough to prove
# the fix, without touching the DB.

def _daily_series(event_class, start_jd, n_days, raw_lambda, shape="interval"):
    return [_result(event_class, start_jd + i, raw_lambda, valence="gain", shape=shape) for i in range(n_days)]


def _year_chunk_series(event_class, year, active_day_offsets, shape="interval"):
    """One calendar year's worth of daily series (365 days, IST midnight
    grid) -- `active_day_offsets` is the set of 0-indexed day offsets from
    that year's Jan 1 that are active; every other day is inactive. Mirrors
    writer.py's `run_substep` chunking exactly: one grid day per
    (event_class, year) substep."""
    start_jd = _jd(year, 1, 1)
    return [
        _result(event_class, start_jd + i, 0.3 if i in active_day_offsets else 0.0, valence="gain", shape=shape)
        for i in range(365)
    ]


def test_interval_still_open_at_chunk_end_is_not_closed_on_the_spot():
    """The core RED-C fix: force_close=False (writer.py's non-final-year
    call) must NOT close a run that is still active at the chunk's last
    grid day -- it must carry forward instead."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 1000}
    chunk1 = _daily_series("major_gain", _jd(2010, 1, 1), 365, 0.3)  # active straight through
    rows1, carry1 = SO.build_interval_rows(swe, "major_gain", chunk1, duration_prior, force_close=False)
    assert rows1 == [], "a run still active at the chunk boundary must not be served as a closed window yet"
    assert carry1 is not None
    assert carry1["true_start_date"].isoformat() == "2010-01-01"
    assert carry1["last_active_date"].isoformat() == "2010-12-31"


def test_interval_continuity_merges_across_boundary_then_closes_on_confirmed_cessation():
    """A carried-forward open run, once the NEXT chunk shows real inactivity,
    closes as ONE window spanning both chunks -- window_start is the TRUE
    origin (chunk 1), window_end is the TRUE end (well into chunk 2), never
    truncated to the old chunk-boundary artifact (2010-12-31/2011-01-01)."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 1000}
    chunk1 = _daily_series("major_gain", _jd(2010, 1, 1), 365, 0.3)
    _rows1, carry1 = SO.build_interval_rows(swe, "major_gain", chunk1, duration_prior, force_close=False)

    # Year 2: active for another 42 days, then genuinely stops (a long
    # inactive cooldown follows WITHIN this same chunk, positively
    # confirming the cessation rather than assuming one).
    active_tail = _daily_series("major_gain", _jd(2011, 1, 1), 42, 0.3)
    cooldown = _daily_series("major_gain", _jd(2011, 1, 1) + 42, 100, 0.0)
    chunk2 = active_tail + cooldown
    rows2, carry2 = SO.build_interval_rows(swe, "major_gain", chunk2, duration_prior,
                                            open_run=carry1, force_close=False)

    assert carry2 is None, "confirmed cessation must close the window for real, not re-carry it"
    assert len(rows2) == 1
    row = rows2[0]
    assert row["window_start"].isoformat() == "2010-01-01"
    assert row["window_end"] != date(2010, 12, 31), \
        "window_end must reflect the TRUE cessation date, not the old chunk-boundary artifact"
    total_span = (row["window_end"] - row["window_start"]).days
    assert total_span > 365, "the merged window must reflect the full multi-chunk span"


def test_interval_continuity_closes_at_max_days_cap_not_indefinitely():
    """A signal that never shows confirmed cessation must still close --
    exactly at the ontology's duration_prior.max_days cap, not carried
    forward forever."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 200}
    # 201 active days -> the run's true span (day 0 to day 200) is exactly
    # 200 days, meeting the cap (a 200-DAY series of daily points spans 199
    # days between its first and last date; this is deliberately one day
    # over so the span genuinely reaches max_days).
    chunk = _daily_series("major_gain", _jd(2010, 1, 1), 201, 0.3)
    rows, carry = SO.build_interval_rows(swe, "major_gain", chunk, duration_prior, force_close=False)
    assert carry is None, "hitting max_days must close for real, not carry past the ontology's own cap"
    assert len(rows) == 1
    assert (rows[0]["window_end"] - rows[0]["window_start"]).days <= 200


def test_interval_continuity_force_close_on_final_horizon_year_never_drops_a_window():
    """writer.py passes force_close=True on the sweep horizon's LAST year so
    a still-open activation is served, not silently lost because there's no
    further substep to confirm cessation."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 1000}
    chunk = _daily_series("major_gain", _jd(2099, 1, 1), 365, 0.3)  # active straight through the final year
    rows, carry = SO.build_interval_rows(swe, "major_gain", chunk, duration_prior, force_close=True)
    assert carry is None
    assert len(rows) == 1


# ── gate assertion (native-mandated, D-5 RED-C): no served window boundary
# may coincide with a chunk boundary absent duration_prior.max_days support ─

def _chunk_boundary_dates(year: int) -> set:
    return {date(year - 1, 12, 31), date(year, 1, 1), date(year, 12, 31), date(year + 1, 1, 1)}


def _assert_no_uncapped_chunk_boundary_windows(rows: list[dict], duration_prior: dict, years: "list[int]"):
    """The gate assertion itself: a served interval row's window_start/
    window_end must never exactly equal a processed year's chunk edge
    (Dec-31/Jan-1) UNLESS the window's own width is at the ontology's
    duration_prior.max_days cap (a legitimate coincidence, not a chunking
    artifact -- BRIEF_D5's own binding shape-precision discipline cuts both
    ways: never MORE precision than the shape supports, and never LESS
    discrimination than a bounded prior demands)."""
    max_days = duration_prior.get("max_days")
    boundary_dates = set()
    for year in years:
        boundary_dates |= _chunk_boundary_dates(year)
    for row in rows:
        width_days = (row["window_end"] - row["window_start"]).days
        is_capped = max_days is not None and width_days >= max_days
        for edge in (row["window_start"], row["window_end"]):
            if edge in boundary_dates:
                assert is_capped, (
                    f"served window edge {edge.isoformat()} (width={width_days}d) coincides with a "
                    f"year-chunk boundary but is NOT duration_prior.max_days-capped ({max_days}d) -- "
                    "this is the RED-C chunking-artifact bug: a served boundary must never silently "
                    "coincide with an internal chunking boundary when it isn't actually where the "
                    "signal ended."
                )


def test_gate_no_served_window_boundary_coincides_with_chunk_edge_absent_signal_support():
    """The RED-C gate assertion, driven through a multi-year synthetic sweep
    (one `build_interval_rows` call per calendar year, carry threaded
    through exactly like `run_substep` does) reproducing the shape of the
    live finding: a signal firing continuously across ONE year boundary
    (2010-07-01 -> 2011-03-01) then genuinely stopping."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    signal_start, signal_end = date(2010, 7, 1), date(2011, 3, 1)
    years = [2010, 2011, 2012]

    all_rows: list[dict] = []
    carry = None
    for idx, year in enumerate(years):
        active = {i for i in range(365) if signal_start <= (date(year, 1, 1) + timedelta(days=i)) <= signal_end}
        chunk = _year_chunk_series("major_gain", year, active)
        rows, carry = SO.build_interval_rows(
            swe, "major_gain", chunk, duration_prior, open_run=carry, force_close=(idx == len(years) - 1),
        )
        all_rows.extend(rows)

    assert carry is None
    assert len(all_rows) == 1, "one continuous episode must serve as ONE window, not one per chunk"
    _assert_no_uncapped_chunk_boundary_windows(all_rows, duration_prior, years)


def test_gate_assertion_is_not_vacuous_it_catches_the_old_broken_behavior():
    """Sanity-check that the gate assertion above is a real regression check,
    not trivially satisfied -- replay the SAME synthetic signal through the
    OLD (pre-fix) per-chunk behavior (force_close=True on every chunk, no
    carry threaded through -- exactly what `run_substep` did before this
    fix) and confirm the assertion helper DOES flag it."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    signal_start, signal_end = date(2010, 7, 1), date(2011, 3, 1)
    years = [2010, 2011, 2012]

    old_behavior_rows: list[dict] = []
    for year in years:
        active = {i for i in range(365) if signal_start <= (date(year, 1, 1) + timedelta(days=i)) <= signal_end}
        chunk = _year_chunk_series("major_gain", year, active)
        # OLD behavior: force_close=True on EVERY chunk, no carry passed in
        # or out -- each year's still-open run is closed on the spot.
        rows, _carry = SO.build_interval_rows(swe, "major_gain", chunk, duration_prior, force_close=True)
        old_behavior_rows.extend(rows)

    with pytest.raises(AssertionError):
        _assert_no_uncapped_chunk_boundary_windows(old_behavior_rows, duration_prior, years)


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
        rows, carry = sweep_event_class_chunk(swe, conn, CHART_ID, "marriage", start_jd, end_jd, step_days=1.0)
        assert carry is None  # marriage is point-shaped -- never carries
        assert isinstance(rows, list)
        for r in rows:
            assert r["temporal_shape"] == "point"
            assert r["window_start"] == r["window_end"]
    finally:
        conn.close()
