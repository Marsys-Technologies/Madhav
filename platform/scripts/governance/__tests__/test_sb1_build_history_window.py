"""test_sb1_build_history_window.py -- Build.history judged inside its window (SS definition), asset_census.py side.

The window DATING (git, scratch repos) is test_sb1_build_window_reader.py. This file proves the GRADING on hand-built attempt logs:
older errors are reported not judged; no attempt since reads NO_DETECTOR not PASS; a forced rebuild counts and a skip_no_delta does not;
an undeterminable window reads NO_DETECTOR naming why; the writer source set the window dates equals the engine's own digest set for every
registered writer; and measure() wires it (offline harness as test_r99_*). No database, no network.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

OPEN = 1_000_000.0           # the window opens here
OK_WINDOW = dict(ok=True, epoch=OPEN, basis="BASIS", opens="2026-10-01T00:00:00Z")


def _a(epoch, state="complete", disp="build", started=True, err="", scope="chart"):
    return dict(scope=scope, state=state, disposition=disp, when=f"d{int(epoch)}", error=err, started=started, epoch=float(epoch))


def _h(attempts, aid="x"):
    per: dict = {}
    for a in attempts:
        ac._tally_attempt(per, aid, a["scope"], a["state"], a["disposition"], a["when"], a["error"], "t" if a["started"] else "f")
    return per[aid]


def _grade(attempts, window=OK_WINDOW, log="same", err=None):
    h = _h(attempts)
    return ac._grade_build_history_windowed("x", attempts if log == "same" else log, err, window, h)


# ───────────────────────────── the window decides what is judged ─────────────────────────────

def test_old_errors_are_reported_not_judged_and_a_clean_attempt_since_reads_pass():
    r = _grade([_a(10, "error", err="old boom"), _a(20, "aborted", started=False), _a(OPEN + 5)])
    assert r["v"] == ac.PASS, r
    assert "pre-window history" in r["measured"] and "1 error(s), 1 abort(s)" in r["measured"], r
    assert "old boom" not in r["measured"]                      # reported as a count, not quoted as the asset's current failure


def test_the_same_errors_inside_the_window_are_judged_fail():
    r = _grade([_a(OPEN + 1), _a(OPEN + 2, "error", err="new boom")])
    assert r["v"] == ac.FAIL and "new boom" in r["measured"], r


def test_an_earlier_complete_does_not_earn_a_pass_when_nothing_ran_since():
    """The defect this guards: PASS read off a history that predates the code under judgment."""
    r = _grade([_a(10), _a(20), _a(30)])
    assert r["v"] == ac.NO_DET and "nothing has exercised the current code" in r["measured"], r
    assert "3 attempt(s)" in r["measured"] and "BASIS" in r["measured"], r


def test_no_attempt_since_and_old_errors_still_reads_no_detector_with_the_old_count_reported():
    r = _grade([_a(10, "error", err="e1"), _a(11, "error", err="e2")])
    assert r["v"] == ac.NO_DET and "2 error(s)" in r["measured"], r


def test_skip_no_delta_since_is_not_an_attempt_of_the_current_code():
    r = _grade([_a(10), _a(OPEN + 1, "complete", "skip_no_delta")])
    assert r["v"] == ac.NO_DET and "none of which executed the current code" in r["measured"], r


def test_a_forced_unchanged_rebuild_counts_as_an_attempt_of_the_current_code():
    """Forced rebuild = the writer ran (disposition 'build') even though nothing changed: it exercises the current code."""
    r = _grade([_a(10), _a(OPEN + 1, "complete", "skip_no_delta"), _a(OPEN + 2, "complete", "build")])
    assert r["v"] == ac.PASS, r


def test_cascade_blocked_since_is_not_an_attempt():
    r = _grade([_a(OPEN + 1, "error", "blocked_dependency", started=False, err="BLOCKED: upstream")])
    assert r["v"] == ac.NO_DET, r


def test_queued_or_unstarted_rows_since_are_not_an_attempt():
    r = _grade([_a(OPEN + 1, "queued", "", started=False), _a(OPEN + 2, "aborted", "", started=False)])
    assert r["v"] == ac.NO_DET, r


def test_an_attempt_exactly_at_the_window_start_is_not_inside_it():
    """Strictly after: an attempt created in the same second as the commit cannot be shown to have run the new code."""
    assert _grade([_a(OPEN)])["v"] == ac.NO_DET
    assert _grade([_a(OPEN + 0.001)])["v"] == ac.PASS


def test_in_window_attempt_that_is_the_last_error_fails_even_after_complete():
    r = _grade([_a(OPEN + 1), _a(OPEN + 2, "error", err="late")])
    assert r["v"] == ac.FAIL


def test_review_skip_then_an_in_flight_started_attempt_is_not_a_pass():
    """Reproduced by the review: a skip_no_delta row (counted complete) followed by a started `building` row used to read PASS '1 complete'."""
    r = _grade([_a(OPEN + 1, "complete", "skip_no_delta"), _a(OPEN + 2, "building", "", started=True)])
    assert r["v"] == ac.NO_DET and "no exercising attempt completed since the window opened" in r["measured"], r


def test_review_a_started_building_attempt_alone_is_not_a_pass():
    assert _grade([_a(OPEN + 1, "building", "")])["v"] == ac.NO_DET


def test_review_a_real_complete_followed_by_an_in_flight_attempt_is_no_detector_n233():
    """N-233 R1 review: the LATEST exercising attempt must be complete; a complete followed by a later in-flight attempt used to read PASS."""
    assert _grade([_a(OPEN + 1, "complete", "build"), _a(OPEN + 2, "building", "")])["v"] == ac.NO_DET
    assert _grade([_a(OPEN + 1, "building", ""), _a(OPEN + 2, "complete", "build")])["v"] == ac.PASS


def test_review_a_real_error_in_the_window_is_still_judged_not_hidden_by_the_new_guard():
    assert _grade([_a(OPEN + 1, "building", ""), _a(OPEN + 2, "error", err="late")])["v"] == ac.FAIL


# ───────────────────────────── fail closed ─────────────────────────────

def test_undeterminable_window_is_no_detector_naming_why_and_the_whole_history_verdict():
    r = _grade([_a(10), _a(20)], window=dict(ok=False, reason="the repository is a shallow clone"))
    assert r["v"] == ac.NO_DET and "shallow clone" in r["measured"] and "whole-history reading would be PASS" in r["measured"], r


def test_unreadable_attempt_log_is_no_detector():
    h = _h([_a(10)])
    r = ac._grade_build_history_windowed("x", None, "psql down", OK_WINDOW, h)
    assert r["v"] == ac.NO_DET and "psql down" in r["measured"], r


def test_log_and_history_tally_disagreeing_is_no_detector():
    h = _h([_a(OPEN + 1), _a(OPEN + 2)])
    r = ac._grade_build_history_windowed("x", [_a(OPEN + 1)], None, OK_WINDOW, h)
    assert r["v"] == ac.NO_DET and "disagree" in r["measured"], r


def test_attempt_log_rejects_a_ragged_line_and_an_untimed_attempt(monkeypatch):
    monkeypatch.setattr(ac, "psql", lambda *a, **k: [["x", "chart", "complete", "", "d", "", "t", "1"]])
    with pytest.raises(ac.Unknown, match="10 selected fields"):
        ac.build_attempt_log("bg_", ["x"])
    monkeypatch.setattr(ac, "psql", lambda *a, **k: [["x", "chart", "complete", "", "d", "", "t", "", "f", "r0"]])
    with pytest.raises(ac.Unknown, match="no readable run creation time"):
        ac.build_attempt_log("bg_", ["x"])


def test_attempt_log_parses_the_timed_rows_in_order(monkeypatch):
    monkeypatch.setattr(ac, "psql", lambda *a, **k: [["x", "chart", "error", "", "2026-10-01", "boom", "t", "100.5", "f", "r1"],
                                                      ["x", "chart", "complete", "", "2026-10-02", "", "t", "200.25", "t", "r2"]])
    log = ac.build_attempt_log("bg_", ["x"])
    assert [a["epoch"] for a in log["x"]] == [100.5, 200.25] and log["x"][0]["error"] == "boom" and log["x"][1]["started"] is True
    assert [a["receipt"] for a in log["x"]] == [False, True]                      # the probe-green evidence rides with each attempt


def test_refactored_tally_equals_the_whole_history_read(monkeypatch):
    """build_history() now delegates to _tally_attempt: its per-asset dict equals the one built attempt by attempt."""
    rows = [["x", "chart", "error", "", "d1", "e", "t"], ["x", "chart", "error", "blocked_dependency", "d2", "b", "f"],
            ["x", "chart", "complete", "skip_no_delta", "d3", "", "t"], ["x", "global", "complete", "build", "d4", "", "t"]]
    calls = iter([rows, [["3"]], [["3"]]])
    monkeypatch.setattr(ac, "psql", lambda *a, **k: next(calls))
    monkeypatch.setattr(ac, "scalar", lambda sql: "0")
    got = ac.build_history("bg_", ["x"])["per"]["x"]
    want: dict = {}
    for r in rows:
        ac._tally_attempt(want, *r)
    assert got == want["x"]
    assert got["blocked"] == 1 and got["skipped"] == 1 and got["complete"] == 2 and got["executed"] == 3


# ───────────────────────────── the writer source set the window dates = the engine's digest set ─────────────────────────────

def test_writer_code_paths_equal_the_engines_digest_set_for_every_registered_writer():
    pytest.importorskip("psycopg")
    sys.path.insert(0, str(ac.SIDECAR))
    try:
        from pipeline.orchestrator import asset_runner as ar
        from pipeline.orchestrator.writers import discover_all
        discover_all()
    except Exception as exc:                                   # an environment that cannot import the engine cannot run the parity
        pytest.skip(f"engine not importable here: {type(exc).__name__}")
    n = 0
    for prefix in ("bg_", "ga_", "bo_", "ka_", "ph_", "mi_"):
        for aid, files in ac.registered_ids(prefix).items():
            eng = [p for p, _ in ar._writer_source_files(ar._writer_source_paths(aid))]
            assert ac._writer_code_paths(aid, files, True) == eng, aid
            n += 1
    assert n > 100


def test_writer_code_paths_follow_a_declared_source_paths_adapter():
    paths = ac._writer_code_paths("ga_dashas", ["ga_dashas.py"], True)
    assert "platform/python-sidecar/ga_writers/ga_dashas_writer.py" in paths


def test_no_writer_asset_dates_the_generic_probe_sources():
    assert ac._writer_code_paths("bo_x", [], False) == list(ac._PROBE_SOURCE_PATHS)


def test_writer_backed_asset_with_no_registered_file_has_no_path_set():
    assert ac._writer_code_paths("ga_x", [], True) == []


# ───────────────────────────── measure() wiring (offline harness as test_r99_*) ─────────────────────────────

def _reg_row(aid):
    return dict(asset_id=aid, has_writer=True, target_table="ga_t", count_sql="SELECT count(*) FROM ga_t", has_integrity=False,
                integrity_sql=None, depends_on=[], target_floor="5", catalog_status="CURRENT", asset_kind="data")


def _stub(monkeypatch, tmp_path, attempts, window):
    reg = {"ga_x": _reg_row("ga_x")}
    h = _h(attempts, "ga_x")
    rec = dict(state="lit", rows_written="5", rps="", last_built="2026-09-01", n_rows=1, ambiguous=False,
               _key=(0.0, 0.0), built_epoch="0", duration=None)
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=1, active=1, excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists={"ga_t"}, cols={"ga_t": ["id"]}, keys={"ga_t": []}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: 5 for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {aid: {"": dict(rec)} for aid in reg})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={"ga_x": h}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "build_attempt_log", lambda prefix, ids=None: {"ga_x": attempts})
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: [] for a in reg}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=0, full=[], never=list(c), note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)
    bw = ac._lint_module("build_window")
    monkeypatch.setattr(bw, "compute_window", lambda reader, aid, paths: window)
    monkeypatch.setattr(ac._WindowedHistory, "cert_floor", lambda self: (0.0, None))      # N-233 R1: the pass instant (a DB read) is out of these tests' scope; 0.0 = earlier than every test window
    monkeypatch.setattr(ac, "_writer_code_paths", lambda aid, files, has_writer: ["platform/x.py"])
    monkeypatch.setattr(bw.WindowReader, "__init__", lambda self, *a, **k: None)


def _cell(census, crit="Build.history"):
    return next(a for a in census["assets"] if a["asset_id"] == "ga_x")["measurements"][crit]


def test_measure_reads_the_windowed_cell(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, [_a(10, "error", err="old"), _a(OPEN + 1)], OK_WINDOW)
    c = _cell(ac.measure("L1"))
    assert c["v"] == ac.PASS and "pre-window history" in c["measured"], c


def test_measure_reads_no_detector_when_nothing_ran_since(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, [_a(10), _a(20)], OK_WINDOW)
    assert _cell(ac.measure("L1"))["v"] == ac.NO_DET


def test_measure_reads_no_detector_when_the_window_is_unknown(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, [_a(10)], dict(ok=False, reason="no main ref"))
    c = _cell(ac.measure("L1"))
    assert c["v"] == ac.NO_DET and "no main ref" in c["measured"], c


def test_measure_degrades_a_raising_window_to_errored_not_an_aborted_layer(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, [_a(10)], OK_WINDOW)

    def boom(aid, files, has_writer):
        raise RuntimeError("surprise")
    monkeypatch.setattr(ac, "_writer_code_paths", boom)
    c = _cell(ac.measure("L1"))
    assert c["v"] == ac.ERRORED and "surprise" in c["measured"], c


def test_the_criterion_is_revision_3():
    assert ac.CRITERION_REGISTRY["Build.history"]["revision"] == 3


# ───────────── review fix: an asset whose rows were never started is windowed too ─────────────

def test_measure_windows_an_asset_whose_rows_never_started(monkeypatch, tmp_path):
    """Old aborts (before the window) must not read FAIL against the 'judge only since the window' rule: pre-window rows are reported, and with nothing
    started since the cell reads NO_DETECTOR."""
    atts = [_a(10, "aborted", "", started=False), _a(20, "aborted", "", started=False)]
    _stub(monkeypatch, tmp_path, atts, OK_WINDOW)
    c = _cell(ac.measure("L1"))
    assert c["v"] == ac.NO_DET and "pre-window history" in c["measured"] and "2 abort(s)" in c["measured"], c


def test_measure_never_started_rows_inside_the_window_are_not_an_exercise_either(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, [_a(OPEN + 1, "aborted", "", started=False)], OK_WINDOW)
    c = _cell(ac.measure("L1"))
    assert c["v"] == ac.NO_DET and "none of which executed the current code" in c["measured"], c


def test_measure_never_started_rows_with_an_unknown_window_read_no_detector_naming_why(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, [_a(10, "aborted", "", started=False)], dict(ok=False, reason="no main ref"))
    c = _cell(ac.measure("L1"))
    assert c["v"] == ac.NO_DET and "no main ref" in c["measured"], c
