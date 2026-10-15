"""test_n233_build_history_cert_window.py: Build.history, SS ruling N-233 R1 (the certification window).

The window opens no earlier than the bottom-up pass (build run ca17639b-..., the pass's own attempts inside). Inside it the asset's LATEST attempt must be complete AND there must be no UNEXPLAINED error or abort;
an error is explained only when it is attributable to a pinned entry of build_window.EXPLAINED_RUNS (run 981a51ec: its abort, or an error whose text matches a pinned cause). No blanket ignore.

Pure grading on hand-built attempt logs (the real build_window.apply_certification_floor builds the window), plus a disposable PostgreSQL for the two reads that touch the database (the pass instant from build_runs,
the run id of the timed attempt log). Every mutation here turns the cell from the clean reading to a non-clean one.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

bw = ac._lint_module("build_window")
PASS_RUN = bw.CERT_WINDOW_RUN_ID
CANCELLED = "981a51ec-f1d1-4d82-b8c6-a8dccc81b1cb"
OTHER = "11111111-2222-3333-4444-555555555555"
FLOOR = 2_000_000.0            # the pass instant
PER_ASSET = 1_000_000.0        # the per-asset (writer / registry) date, earlier than the pass
PERM = "InsufficientPrivilege: permission denied for table brahma_activity_ontology Traceback (most recent call last)"
TIMEOUT = "QueryCanceled: canceling statement due to statement timeout"


def _a(epoch, state="complete", disp="build", started=True, err="", run=OTHER, scope="chart"):
    return dict(scope=scope, state=state, disposition=disp, when=f"d{int(epoch)}", error=err, started=started, epoch=float(epoch), run_id=run)


def _window(floor=FLOOR, per_asset=PER_ASSET):
    base = dict(ok=True, epoch=per_asset, basis="BASIS", opens="2026-10-01T00:00:00Z")
    return bw.apply_certification_floor(base, floor)


def _grade(attempts, window=None):
    per: dict = {}
    for a in attempts:
        ac._tally_attempt(per, "x", a["scope"], a["state"], a["disposition"], a["when"], a["error"], "t" if a["started"] else "f")
    return ac._grade_build_history_windowed("x", attempts, None, window or _window(), per["x"])


# ───────────────────────── the window opens at the pass ─────────────────────────

def test_floor_later_than_the_per_asset_date_opens_the_window_at_the_pass_inclusive():
    w = _window()
    assert w["ok"] and w["epoch"] == FLOOR and w["inclusive"] is True and "bottom-up pass" in w["basis"] and PASS_RUN[:8] in w["basis"]


def test_floor_earlier_than_the_per_asset_date_leaves_the_per_asset_date_strictly_after():
    w = _window(floor=500_000.0)
    assert w["epoch"] == PER_ASSET and w["inclusive"] is False and "per-asset date stands" in w["basis"]


def test_an_unreadable_pass_instant_makes_the_window_unknown_fail_closed():
    w = bw.apply_certification_floor(dict(ok=True, epoch=PER_ASSET, basis="B", opens="x"), None, "no row")
    assert w["ok"] is False and "no row" in w["reason"] and PASS_RUN in w["reason"]
    r = _grade([_a(FLOOR + 5)], w)
    assert r["v"] == ac.NO_DET and "could not be established" in r["measured"], r


def test_a_complete_attempt_of_the_pass_itself_is_inside_the_window():
    r = _grade([_a(FLOOR, run=PASS_RUN)])
    assert r["v"] == ac.PASS, r


def test_a_complete_attempt_before_the_pass_earns_nothing_and_reads_no_detector():
    r = _grade([_a(FLOOR - 1)])
    assert r["v"] == ac.NO_DET and "nothing has exercised the current code" in r["measured"], r


def test_errors_before_the_pass_are_reported_not_judged():
    r = _grade([_a(FLOOR - 50, "error", err="KeyError: old"), _a(FLOOR - 40, "aborted", started=False), _a(FLOOR + 1)])
    assert r["v"] == ac.PASS and "pre-window history" in r["measured"] and "1 error(s), 1 abort(s)" in r["measured"], r


# ───────────────────────── explained errors: only the pinned cause list ─────────────────────────

def test_the_cancelled_runs_permission_error_is_explained_and_a_later_complete_reads_pass():
    r = _grade([_a(FLOOR + 1, "error", err=PERM, run=CANCELLED), _a(FLOOR + 2)])
    assert r["v"] == ac.PASS, r
    assert "EXPLAINED" in r["measured"] and "981a51ec" in r["measured"] and "1 error/abort attempt(s)" in r["measured"], r


def test_the_cancelled_runs_abort_and_statement_timeout_are_explained():
    r = _grade([_a(FLOOR + 1, "aborted", "", started=False, run=CANCELLED), _a(FLOOR + 2, "error", err=TIMEOUT, run=CANCELLED), _a(FLOOR + 3)])
    assert r["v"] == ac.PASS and "2 error/abort attempt(s)" in r["measured"], r


def test_MUTATION_the_same_permission_error_of_another_run_is_judged_partial():
    r = _grade([_a(FLOOR + 1, "error", err=PERM, run=OTHER), _a(FLOOR + 2)])
    assert r["v"] == ac.PARTIAL and "1 error(s)" in r["measured"], r


def test_MUTATION_the_same_permission_error_of_another_run_as_the_latest_attempt_is_fail():
    r = _grade([_a(FLOOR + 1), _a(FLOOR + 2, "error", err=PERM, run=OTHER)])
    assert r["v"] == ac.FAIL, r


def test_MUTATION_another_cause_in_the_cancelled_run_is_not_explained():
    r = _grade([_a(FLOOR + 1, "error", err="KeyError: 'x' Traceback", run=CANCELLED), _a(FLOOR + 2)])
    assert r["v"] == ac.PARTIAL and "EXPLAINED" not in r["measured"], r


def test_MUTATION_an_empty_error_text_of_the_cancelled_run_is_not_explained():
    r = _grade([_a(FLOOR + 1, "error", err="", run=CANCELLED), _a(FLOOR + 2)])
    assert r["v"] == ac.PARTIAL, r


def test_MUTATION_an_abort_of_another_run_is_judged_partial():
    r = _grade([_a(FLOOR + 1, "aborted", "", started=False, run=OTHER), _a(FLOOR + 2)])
    assert r["v"] == ac.PARTIAL and "1 abort(s)" in r["measured"], r


def test_MUTATION_a_run_id_that_only_shares_the_prefix_is_not_the_pinned_run():
    r = _grade([_a(FLOOR + 1, "error", err=PERM, run="981a51ec-0000-0000-0000-000000000000"), _a(FLOOR + 2)])
    assert r["v"] == ac.PARTIAL, r


def test_an_unexplained_error_beside_an_explained_one_still_judges_the_unexplained_one():
    r = _grade([_a(FLOOR + 1, "error", err=PERM, run=CANCELLED), _a(FLOOR + 2, "error", err="boom", run=OTHER), _a(FLOOR + 3)])
    assert r["v"] == ac.PARTIAL and "1 error(s)" in r["measured"] and "EXPLAINED" in r["measured"], r


def test_only_explained_attempts_in_the_window_read_no_detector_not_pass():
    r = _grade([_a(FLOOR + 1, "error", err=PERM, run=CANCELLED), _a(FLOOR + 2, "aborted", "", run=CANCELLED)])
    assert r["v"] == ac.NO_DET, r


def test_a_latest_failed_attempt_in_the_window_is_fail_even_after_a_complete():
    r = _grade([_a(FLOOR + 1), _a(FLOOR + 2, "error", err="late boom")])
    assert r["v"] == ac.FAIL and "late boom" in r["measured"], r


def test_the_explained_attempt_is_removed_from_the_tally_so_it_does_not_become_the_latest():
    """A cancelled-run abort AFTER the asset's last complete is not held against it and does not make the latest attempt 'aborted'."""
    r = _grade([_a(FLOOR + 1), _a(FLOOR + 2, "aborted", "", started=False, run=CANCELLED)])
    assert r["v"] == ac.PASS, r


def test_the_pinned_list_is_closed_and_names_only_the_cancelled_run():
    assert set(bw.EXPLAINED_RUNS) == {CANCELLED}
    spec = bw.EXPLAINED_RUNS[CANCELLED]
    assert spec["abort_explained"] and len(spec["error_causes"]) == 2
    assert ac.explained_attempt(_a(1, "complete", run=CANCELLED), bw.EXPLAINED_RUNS) is None
    assert ac.explained_attempt(_a(1, "error", "blocked_dependency", err=PERM, run=CANCELLED), bw.EXPLAINED_RUNS) is None
    assert ac.explained_attempt(_a(1, "error", err=PERM), {}) is None


def test_the_nominal_instant_cross_check_rejects_the_wrong_run():
    import datetime as dt
    nominal = dt.datetime(2026, 10, 7, 20, 18, tzinfo=dt.timezone.utc).timestamp()
    assert bw.check_floor_against_nominal(nominal + 60) is None
    assert "another run" in bw.check_floor_against_nominal(nominal + 86400)


def test_the_registry_text_and_revision():
    e = ac.CRITERION_REGISTRY["Build.history"]
    assert e["revision"] == 3 and "N-233 R1" in e["applicability"] and "ca17639b-f3cf-42c7-9866-0a61f3855802" in e["applicability"] and "NO blanket ignore" in e["applicability"]


# ───────────────────────── review R1: the LATEST exercising attempt must be complete ─────────────────────────

def test_a_complete_followed_by_a_later_in_flight_attempt_reads_no_detector():
    r = _grade([_a(FLOOR + 1), _a(FLOOR + 2, "building", "")])
    assert r["v"] == ac.NO_DET and "latest exercising attempt" in r["measured"] and "building" in r["measured"], r


def test_a_complete_followed_by_a_complete_reads_pass():
    assert _grade([_a(FLOOR + 1), _a(FLOOR + 2)])["v"] == ac.PASS


def test_an_in_window_failed_latest_still_reads_fail_and_an_earlier_failure_still_reads_partial():
    assert _grade([_a(FLOOR + 1), _a(FLOOR + 2, "error", err="late boom")])["v"] == ac.FAIL
    assert _grade([_a(FLOOR + 1, "error", err="early boom"), _a(FLOOR + 2)])["v"] == ac.PARTIAL


def test_the_abort_of_the_cancelled_run_is_worded_as_a_cancellation_not_as_a_cause():
    r = _grade([_a(FLOOR + 1, "aborted", "", started=False, run=CANCELLED), _a(FLOOR + 2)])
    assert r["v"] == ac.PASS and "cancellation of run 981a51ec" in r["measured"], r


# ───────────────────────── real SQL: the pass instant and the run id ─────────────────────────

def _mk_tables(pg, monkeypatch):
    point_psql_at(pg, monkeypatch)
    for t in ("asset_provenance_receipts", "build_run_assets", "build_runs"):
        ac.psql(f"DROP TABLE IF EXISTS {t}")
    ac.psql("CREATE TABLE build_runs (id uuid PRIMARY KEY, scope text, created_at timestamptz)")
    ac.psql("CREATE TABLE build_run_assets (run_id uuid, asset_id text, state text, disposition text, error text, started_at timestamptz)")
    ac.psql("CREATE TABLE asset_provenance_receipts (build_id uuid, asset_id text)")


def _hist():
    h = ac._WindowedHistory("bg_", ["bg_x"], reader=object())
    h._bw = bw
    return h


def test_REAL_SQL_the_pass_instant_is_read_from_build_runs(monkeypatch, disposable_pg):
    _mk_tables(disposable_pg, monkeypatch)
    try:
        ac.psql(f"INSERT INTO build_runs VALUES ('{PASS_RUN}', 'global', '2026-10-07 20:18:30+00')")
        ep, why = _hist().cert_floor()
        assert why is None and abs(ep - 1791404310.0) < 1.0, (ep, why)
    finally:
        ac.psql("DROP TABLE IF EXISTS build_runs")


def test_REAL_SQL_a_missing_pass_run_is_fail_closed(monkeypatch, disposable_pg):
    _mk_tables(disposable_pg, monkeypatch)
    try:
        ep, why = _hist().cert_floor()
        assert ep is None and PASS_RUN in why
    finally:
        ac.psql("DROP TABLE IF EXISTS build_runs")


def test_REAL_SQL_a_pass_run_created_at_the_wrong_time_is_fail_closed(monkeypatch, disposable_pg):
    _mk_tables(disposable_pg, monkeypatch)
    try:
        ac.psql(f"INSERT INTO build_runs VALUES ('{PASS_RUN}', 'global', '2026-09-01 08:00:00+00')")
        ep, why = _hist().cert_floor()
        assert ep is None and "another run" in why
    finally:
        ac.psql("DROP TABLE IF EXISTS build_runs")


def test_REAL_SQL_the_attempt_log_carries_the_run_id_and_the_whole_cell_attributes_the_cancelled_runs_errors(monkeypatch, disposable_pg):
    """End to end on the database: the cancelled run's permission error and abort are explained; the same error text in another run is not."""
    _mk_tables(disposable_pg, monkeypatch)
    last = "99999999-9999-9999-9999-999999999999"
    try:
        ac.psql(f"INSERT INTO build_runs VALUES ('{PASS_RUN}', 'global', '2026-10-07 20:18:30+00'), ('{CANCELLED}', 'global', '2026-10-07 20:30:00+00'), ('{OTHER}', 'global', '2026-10-07 21:00:00+00'), "
                f"('{last}', 'global', '2026-10-07 22:00:00+00')")
        ac.psql(f"INSERT INTO build_run_assets VALUES ('{PASS_RUN}', 'bg_x', 'complete', 'build', NULL, '2026-10-07 20:19:00+00'), "
                f"('{CANCELLED}', 'bg_x', 'error', 'build', 'InsufficientPrivilege: permission denied for table t', '2026-10-07 20:31:00+00'), "
                f"('{CANCELLED}', 'bg_x', 'aborted', NULL, NULL, NULL), "
                f"('{last}', 'bg_x', 'complete', 'build', NULL, '2026-10-07 22:01:00+00')")
        log = ac.build_attempt_log("bg_", ["bg_x"])
        assert [a["run_id"] for a in log["bg_x"]] == [PASS_RUN, CANCELLED, CANCELLED, last]
        h = _hist()
        fl, why = h.cert_floor()
        window = bw.apply_certification_floor(dict(ok=True, epoch=fl - 86400, basis="B", opens="x"), fl, why)

        def tally(lg):
            per: dict = {}
            for a in lg:
                ac._tally_attempt(per, "bg_x", a["scope"], a["state"], a["disposition"], a["when"], a["error"], "t" if a["started"] else "f")
            return per["bg_x"]
        r = ac._grade_build_history_windowed("bg_x", log["bg_x"], None, window, tally(log["bg_x"]))
        assert r["v"] == ac.PASS and "EXPLAINED" in r["measured"], r
        # MUTATION: re-attribute the permission error to a run that is not pinned: the cell leaves PASS
        ac.psql(f"UPDATE build_run_assets SET run_id = '{OTHER}' WHERE state = 'error'")
        log = ac.build_attempt_log("bg_", ["bg_x"])
        r = ac._grade_build_history_windowed("bg_x", log["bg_x"], None, window, tally(log["bg_x"]))
        assert r["v"] == ac.PARTIAL, r
    finally:
        for t in ("build_run_assets", "build_runs", "asset_provenance_receipts"):
            ac.psql(f"DROP TABLE IF EXISTS {t}")
