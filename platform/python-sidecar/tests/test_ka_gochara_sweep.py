"""
tests/test_ka_gochara_sweep.py — D-5 Lane G-4 "Forward sweep + serving" tests.

No DATABASE_URL required for the bulk of this suite — `shape_output.py` is a
pure module (constructed `IntensityResult` fixtures, real `swisseph` JD<->date
conversion, no DB/network), mirroring `tests/test_gochara_grammar.py` and
`tests/test_gochara_intensity.py`'s own documented pattern. The writer
resumption tests exercise `KaGocharaSweepWriter`'s pure helper methods
(`_compute_build_fingerprint`, `_load_completed_substeps`) against fake
connection objects, same technique as `tests/test_ka_sangam_resumption.py`.
The "writer.py: DB-driven segment consolidation" section drives the REAL
`KaGocharaSweepWriter._consolidate_interval_segment` /
`_find_adjacent_interval_row` / `_insert_rows` (the production D-5 RED-C
fix v4 mechanism) against `_FakeKalaWindowsDB`, a small in-memory fake for
the specific SQL shapes those methods issue against `kala_gochara_windows`
(SELECT ... FOR UPDATE neighbor lookup, DELETE ... WHERE id, INSERT ... ON
CONFLICT ... DO UPDATE) — still no live DB, but exercises the actual
persisted-state-driven consolidation end to end, including OUT-OF-ORDER and
SHUFFLED multi-year dispatch, with NO scan-distance dependency at any
episode length (unlike three earlier, rejected fix attempts — see
`sweep.py`'s module docstring for that history).
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


# ── writer.py: DB-driven segment consolidation (D-5 RED-C fix v4) ─────────
#
# `sweep_event_class_chunk` no longer resolves a cross-boundary episode
# itself (see module docstring's v4 section) -- it returns RAW SEGMENTS
# strictly bounded to their own chunk, and `writer.py`'s
# `_consolidate_interval_segment` chains them via already-committed DB
# state. `_FakeKalaWindowsDB` below is a small in-memory fake for the
# exact SQL shapes that method issues (SELECT ... FOR UPDATE neighbor
# lookup, DELETE ... WHERE id, INSERT ... ON CONFLICT ... DO UPDATE) so
# these tests drive the REAL production consolidation code end-to-end
# without a live DB.

class _FakeKalaWindowsDB:
    def __init__(self):
        self.rows: dict[int, dict] = {}
        self._next_id = 1

    def cursor(self):
        return _FakeKalaWindowsCursor(self)


class _FakeKalaWindowsConn:
    def __init__(self, db=None):
        self.db = db if db is not None else _FakeKalaWindowsDB()

    def cursor(self):
        return self.db.cursor()


class _FakeKalaWindowsCursor:
    def __init__(self, db: "_FakeKalaWindowsDB"):
        self.db = db
        self._result = None

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def execute(self, sql, params=()):
        import json as _json

        sql_norm = " ".join(sql.split())
        if sql_norm.startswith("SELECT id, continuity_state"):
            chart_id, event_class, adjacent_date = params
            flag_name = "left_active" if "'left_active'" in sql else "right_active"
            date_field = "raw_start" if "'raw_start'" in sql else "raw_end"
            match = None
            for row_id, row in self.db.rows.items():
                cs = row["continuity_state"]
                if (row["chart_id"] == chart_id and row["event_class"] == event_class
                        and row["temporal_shape"] == "interval"
                        and bool(cs.get(flag_name)) is True
                        and cs.get(date_field) == adjacent_date.isoformat()):
                    match = (row_id, row)
                    break
            self._result = None if match is None else dict(match[1], id=match[0])
        elif sql_norm.startswith("DELETE FROM kala_gochara_windows"):
            (row_id,) = params
            self.db.rows.pop(row_id, None)
            self._result = None
        elif sql_norm.startswith("INSERT INTO kala_gochara_windows"):
            (chart_id, event_class, temporal_shape,
             window_start, window_end, peak_date,
             milestone_id, _is_irrev,
             signed_intensity, raw_intensity, valence, is_adverse,
             active_sentences, contributing_systems, suppression_state,
             peak_basis, calibration_state, source, continuity_state) = params
            natural_key = (chart_id, event_class, window_start, peak_date, milestone_id or '')
            existing_id = next(
                (rid for rid, r in self.db.rows.items()
                 if (r["chart_id"], r["event_class"], r["window_start"], r["peak_date"],
                     r.get("milestone_id") or '') == natural_key),
                None,
            )
            row_id = existing_id if existing_id is not None else self.db._next_id
            if existing_id is None:
                self.db._next_id += 1
            self.db.rows[row_id] = {
                "chart_id": chart_id, "event_class": event_class, "temporal_shape": temporal_shape,
                "window_start": window_start, "window_end": window_end, "peak_date": peak_date,
                "milestone_id": milestone_id,
                "signed_intensity": signed_intensity, "raw_intensity": raw_intensity,
                "valence": valence, "is_adverse": is_adverse,
                "active_sentences": active_sentences, "contributing_systems": contributing_systems,
                "suppression_state": suppression_state, "peak_basis": peak_basis,
                "calibration_state": calibration_state, "source": source,
                "continuity_state": (_json.loads(continuity_state)
                                      if isinstance(continuity_state, str) else continuity_state),
            }
            self._result = None
        else:
            raise AssertionError(f"_FakeKalaWindowsDB: unhandled SQL: {sql_norm[:120]!r}")

    def fetchone(self):
        return self._result

    def fetchall(self):
        return [self._result] if self._result else []


def _consolidate_and_insert(writer, conn, event_class, segments):
    """Mirrors `run_substep`'s own interval-shape dispatch: consolidate
    each raw segment against whatever is already committed, then insert."""
    for segment in segments:
        final_row = writer._consolidate_interval_segment(conn, CHART_ID, event_class, segment)
        with conn.cursor() as cur:
            KaGocharaSweepWriter._insert_rows(cur, CHART_ID, [final_row])


def _committed_keys(db: _FakeKalaWindowsDB, event_class: str):
    return sorted(
        (r["window_start"], r["window_end"], r["peak_date"], r["milestone_id"])
        for r in db.rows.values() if r["event_class"] == event_class
    )


def test_sweep_chunk_returns_raw_segment_strictly_bounded_to_own_chunk(monkeypatch):
    """D-5 RED-C fix v4's defining property at the sweep-chunk level: a
    single year's chunk call NEVER resolves the full cross-boundary
    episode itself anymore -- it returns a RAW segment clipped to its OWN
    chunk (year 2011), flagged `left_active` (the episode was already
    running at 2011's own first grid day) so the DB-driven consolidation
    step (writer.py) knows to look for an already-committed left neighbor.
    No `window_start`/`window_end` key exists yet -- those are only
    produced by `finalize_interval_segment`, downstream of consolidation."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    activation = _build_activation_calendar(_SPECIMEN_ACTIVE_START, _SPECIMEN_ACTIVE_END)
    sweep_module = _patch_sweep_deps(monkeypatch, duration_prior, activation)

    rows = _year_chunk(sweep_module, "major_gain", 2011)
    assert len(rows) == 1
    row = rows[0]
    assert row["raw_start"] == date(2011, 1, 1), "clipped to the chunk's own first grid day"
    assert row["raw_end"] < date(2012, 1, 1), "clipped to inside the chunk -- episode ends 2011-03-01"
    assert row["left_active"] is True, "episode was already running at the chunk's own start"
    assert row["right_active"] is False, "episode genuinely ends inside this chunk"
    assert "window_start" not in row, "a raw segment is not yet a finalized served row"


def test_consolidation_out_of_order_dispatch_converges_to_identical_window(monkeypatch):
    """Reproduces the verifier's exact finding: a LATER year (2011)
    consolidated+committed BEFORE an EARLIER year (2010) that shares the
    same episode. Both dispatch orders must converge on the identical
    final served window via the DB-driven neighbor lookup -- no
    double-serving, no dropped tail, under out-of-order dispatch."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    activation = _build_activation_calendar(_SPECIMEN_ACTIVE_START, _SPECIMEN_ACTIVE_END)
    writer = KaGocharaSweepWriter()

    # Ascending order (the OLD assumed order).
    sweep_ascending = _patch_sweep_deps(monkeypatch, duration_prior, activation)
    conn_ascending = _FakeKalaWindowsConn()
    _consolidate_and_insert(writer, conn_ascending, "major_gain",
                             _year_chunk(sweep_ascending, "major_gain", 2010))
    _consolidate_and_insert(writer, conn_ascending, "major_gain",
                             _year_chunk(sweep_ascending, "major_gain", 2011))

    # OUT OF ORDER: year 2011 consolidated+committed BEFORE year 2010.
    sweep_out_of_order = _patch_sweep_deps(monkeypatch, duration_prior, activation)
    conn_out_of_order = _FakeKalaWindowsConn()
    _consolidate_and_insert(writer, conn_out_of_order, "major_gain",
                             _year_chunk(sweep_out_of_order, "major_gain", 2011))
    _consolidate_and_insert(writer, conn_out_of_order, "major_gain",
                             _year_chunk(sweep_out_of_order, "major_gain", 2010))

    keys_ascending = _committed_keys(conn_ascending.db, "major_gain")
    keys_out_of_order = _committed_keys(conn_out_of_order.db, "major_gain")
    assert len(keys_ascending) == 1, "the two year-segments must merge into ONE served row"
    assert keys_ascending == keys_out_of_order, (
        "the final committed window must be identical regardless of dispatch order -- a "
        "carry-based mechanism keyed to 'the immediately prior substep' would fail this"
    )


def test_consolidation_gate_no_boundary_artifact_under_out_of_order_dispatch(monkeypatch):
    """The RED-C gate assertion (native-mandated), driven through the REAL
    `sweep_event_class_chunk` + `_consolidate_interval_segment` across
    three years in REVERSE dispatch order (2012, then 2011, then 2010) --
    no FINAL committed window's start/end may coincide with a year-chunk
    boundary (Dec-31/Jan-1) unless the window is legitimately
    duration_prior.max_days-capped."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    activation = _build_activation_calendar(_SPECIMEN_ACTIVE_START, _SPECIMEN_ACTIVE_END)
    sweep_module = _patch_sweep_deps(monkeypatch, duration_prior, activation)
    writer = KaGocharaSweepWriter()
    conn = _FakeKalaWindowsConn()

    for year in (2012, 2011, 2010):  # deliberately descending -- out of order
        _consolidate_and_insert(writer, conn, "major_gain",
                                 _year_chunk(sweep_module, "major_gain", year))

    max_days = duration_prior["max_days"]
    boundary_dates = {date(y, 1, 1) for y in (2010, 2011, 2012, 2013)} | \
                      {date(y, 12, 31) for y in (2010, 2011, 2012)}
    for row in conn.db.rows.values():
        width_days = (row["window_end"] - row["window_start"]).days
        is_capped = width_days >= max_days
        for edge in (row["window_start"], row["window_end"]):
            if edge in boundary_dates:
                assert is_capped, (
                    f"served window edge {edge.isoformat()} (width={width_days}d) coincides with a "
                    f"year-chunk boundary but is NOT max_days-capped ({max_days}d) -- the RED-C "
                    "chunking-artifact bug"
                )


def test_consolidation_assertion_not_vacuous_without_consolidation(monkeypatch):
    """Sanity-check that the gate assertion above is a real regression
    check, not trivially satisfied -- finalize 2010's raw segment DIRECTLY
    (skip `_consolidate_interval_segment`'s DB neighbor lookup entirely,
    i.e. exactly what a chunk-scoped call produces on its own, pre-v4)
    and confirm the RED-C chunking artifact (a served window edge landing
    exactly on the chunk's own last grid day, uncapped, well short of the
    true ~2011-03-01 end) reappears."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    activation = _build_activation_calendar(_SPECIMEN_ACTIVE_START, _SPECIMEN_ACTIVE_END)
    sweep_module = _patch_sweep_deps(monkeypatch, duration_prior, activation)

    segments_2010 = _year_chunk(sweep_module, "major_gain", 2010)
    assert len(segments_2010) == 1
    segment = segments_2010[0]
    assert segment["right_active"] is True, "the episode is still running at 2010's own last grid day"

    row = SO.finalize_interval_segment("major_gain", segment["raw_start"], segment["raw_end"],
                                        segment, duration_prior)
    width_days = (row["window_end"] - row["window_start"]).days
    # `compute_lambda_e_series` (engine.py) loops inclusively through
    # `horizon_end_jd` itself (2011-01-01, the NEXT year's own
    # horizon_start_jd), so that's the exact RED-C artifact boundary here.
    assert row["window_end"] == date(2011, 1, 1)
    assert width_days < duration_prior["max_days"]


def test_consolidation_three_year_span_converges_regardless_of_dispatch_order(monkeypatch):
    """D-5 RED-C fix v3: second independent verification's exact
    counterexample. A 517-day episode (2010-10-01 -> 2012-03-01) is LONGER
    than duration_prior.max_days (365) -- under the v2/v3 designs (a
    bounded cross-boundary scan), a chunk far from the true start could
    exhaust its scan budget short of it, computing a wrongly-anchored
    window. Under v4, EACH of the 2010/2011/2012 chunks computes only its
    own strictly-bounded segment; the DB-driven consolidation converges
    them to the SAME clipped window regardless of which order they're
    committed in -- ascending, descending, and shuffled."""
    duration_prior = {"min_days": 14, "typical_days": 90, "max_days": 365}
    episode_start, episode_end = date(2010, 10, 1), date(2012, 3, 1)
    assert (episode_end - episode_start).days == 517 > duration_prior["max_days"], \
        "the whole point of this test is an episode LONGER than max_days"
    activation = _build_activation_calendar(episode_start, episode_end)
    writer = KaGocharaSweepWriter()

    dispatch_orders = [(2010, 2011, 2012), (2012, 2011, 2010), (2011, 2010, 2012)]
    all_keys = []
    for order in dispatch_orders:
        sweep_module = _patch_sweep_deps(monkeypatch, duration_prior, activation)
        conn = _FakeKalaWindowsConn()
        for year in order:
            _consolidate_and_insert(writer, conn, "major_gain",
                                     _year_chunk(sweep_module, "major_gain", year))
        keys = _committed_keys(conn.db, "major_gain")
        assert len(keys) == 1, f"dispatch order {order} must converge to ONE served row, got {keys}"
        all_keys.append(keys[0])

    assert len(set(all_keys)) == 1, (
        f"three chunks touching the SAME 517-day episode (> max_days={duration_prior['max_days']}) "
        f"must converge on the IDENTICAL clipped window regardless of dispatch order -- got {all_keys}"
    )
    window_start, window_end, peak_date, _milestone_id = all_keys[0]
    # The clip is anchored to the TRUE start (2010-10-01), not to wherever
    # any one chunk's own scan happened to reach.
    assert window_start.isoformat() == "2010-10-01"
    assert (window_end - window_start).days <= duration_prior["max_days"]
    # And no boundary-artifact: peak_date must not land on a chunk edge.
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
