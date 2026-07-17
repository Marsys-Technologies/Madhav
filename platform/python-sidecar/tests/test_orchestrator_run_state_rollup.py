"""Orchestrator run-level state rollup (BA-P3 FIX 3).

Regression for the "green over-report" (NF-1): a run whose plan included any
failed/blocked asset must terminate with state='failed', never 'completed' —
an operator reading 'completed' must be able to trust the build actually
succeeded. Reuses the FakeConn/FakeCursor harness from test_orchestrator_gate.py.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import runner  # noqa: E402
from tests.test_orchestrator_gate import REGISTRY, PLAN, FakeConn, FakeCursor  # noqa: E402


class _ReconcilingFakeCursor(FakeCursor):
    """FakeCursor extended to also answer the RR-fix final-rollup reconciliation
    query (`SELECT asset_id, state FROM build_run_assets WHERE run_id = %s`),
    which the base FakeCursor (test_orchestrator_gate.py) predates and does not
    handle — it would otherwise fall through to the generic "ignore" branch and
    return no rows, making every plan asset look non-terminal. Answers from the
    same shared `state` dict the base cursor already uses for per-asset state."""

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if s.startswith("SELECT asset_id, state FROM build_run_assets WHERE run_id"):
            self._result = [{"asset_id": a, "state": st} for a, st in self._state.items()]
        else:
            super().execute(sql, params)


class _ReconcilingFakeConn(FakeConn):
    def cursor(self):
        return _ReconcilingFakeCursor(self._state)


def _install(monkeypatch, state, fail_assets, mark_calls):
    monkeypatch.setattr(runner, "connect", lambda: _ReconcilingFakeConn(state))
    monkeypatch.setattr(runner, "acquire_chart_lock", lambda *a, **k: True)
    monkeypatch.setattr(runner, "release_chart_lock", lambda *a, **k: None)
    monkeypatch.setattr(runner, "check_signals", lambda *a, **k: None)
    monkeypatch.setattr(runner, "is_asset_complete", lambda *a, **k: False)

    def fake_mark_run_state(conn, cur, run_id, new_state, **kwargs):
        mark_calls.append(new_state)

    monkeypatch.setattr(runner, "mark_run_state", fake_mark_run_state)
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    import pipeline.orchestrator.writers as writers_mod
    monkeypatch.setattr(writers_mod, "discover_all", lambda: None, raising=False)
    monkeypatch.setattr(runner, "_check_writer_registry_gaps", lambda cur: [], raising=False)

    def fake_run_asset(conn, cur, run_id, chart_id, asset_id, position):
        cur.execute(
            "UPDATE build_run_assets SET state=%s WHERE run_id=%s AND asset_id=%s",
            ("error" if asset_id in fail_assets else "complete", run_id, asset_id),
        )
        state[asset_id] = "error" if asset_id in fail_assets else "complete"

    import pipeline.orchestrator.asset_runner as ar
    monkeypatch.setattr(ar, "run_asset", fake_run_asset)


def test_run_with_failed_asset_is_marked_failed_not_completed(monkeypatch):
    state: dict[str, str] = {}
    mark_calls: list[str] = []
    _install(monkeypatch, state, fail_assets={"A"}, mark_calls=mark_calls)

    runner.execute_run("run-1")

    assert "running" in mark_calls
    assert "completed" not in mark_calls
    assert mark_calls[-1] == "failed", (
        f"run had failed/blocked assets — must terminate 'failed', got {mark_calls!r}"
    )


def test_clean_run_is_still_marked_completed(monkeypatch):
    state: dict[str, str] = {}
    mark_calls: list[str] = []
    _install(monkeypatch, state, fail_assets=set(), mark_calls=mark_calls)

    runner.execute_run("run-1")

    assert mark_calls[-1] == "completed", (
        f"a run with zero failed assets must still report 'completed', got {mark_calls!r}"
    )


# ── RR-fix (D-3): run-rollup race reconciliation ──────────────────────────────
#
# _schedule_parallel tracks `failed_assets` IN-PROCESS as worker futures resolve.
# That in-process set is a cache of build_run_assets, not the source of truth —
# a race between a worker's own state write and the scheduler's read of that
# write (or a crash-cleanup path writing after the future already resolved) can
# leave the cache out of sync with what actually landed in the DB. The tests
# below prove execute_run's final rollup trusts a FRESH build_run_assets read
# over the in-process cache, in both directions.
#
# `_reconcile_failed_assets_from_db` is exercised two ways:
#   1. Directly (unit-level) against a minimal fake cursor — isolates the pure
#      reconciliation logic from the scheduler/threading machinery.
#   2. End-to-end through execute_run, using a DB double that gives the
#      in-process worker() read (`state`) and the final reconciliation read
#      (`db_truth`) INDEPENDENT views — reproducing the exact race window: the
#      in-process tracker saw one thing, a (simulated) concurrent write left a
#      different thing in build_run_assets, and only the final fresh read sees it.

class _MiniCursor:
    """Bare-minimum cursor for unit-testing _reconcile_failed_assets_from_db in
    isolation: answers only the reconciliation SELECT and swallows the
    run.rollup_reconciled emit_event call's implicit dependency (patched by the
    caller)."""

    def __init__(self, db_rows):
        self._db_rows = db_rows

    def execute(self, sql, params=None):
        assert "SELECT asset_id, state FROM build_run_assets WHERE run_id" in " ".join(sql.split())

    def fetchall(self):
        return [{"asset_id": a, "state": s} for a, s in self._db_rows.items()]


def test_reconcile_adds_db_error_missed_by_in_process_tracker(monkeypatch):
    """In-process cache believes nothing failed, but build_run_assets shows one
    asset in 'error' — the reconciled set must include it."""
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    cur = _MiniCursor({"A": "complete", "B": "error", "C": "complete"})
    reconciled = runner._reconcile_failed_assets_from_db(cur, "run-1", ["A", "B", "C"], set())
    assert reconciled == {"B"}


def test_reconcile_drops_stale_in_process_failure_when_db_shows_complete(monkeypatch):
    """In-process cache believes 'B' failed, but build_run_assets shows 'complete'
    (e.g. a retry landed after the worker's first result was read) — DB wins,
    'B' must be removed from the reconciled failed set."""
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    cur = _MiniCursor({"A": "complete", "B": "complete", "C": "complete"})
    reconciled = runner._reconcile_failed_assets_from_db(cur, "run-1", ["A", "B", "C"], {"B"})
    assert reconciled == set()


def test_reconcile_treats_non_terminal_or_missing_row_as_failed(monkeypatch):
    """An asset whose build_run_assets row never reached a terminal state (still
    'building'/'queued', or missing entirely) must not be silently counted as a
    success just because the in-process cache never saw a failure for it."""
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    cur = _MiniCursor({"A": "complete", "B": "building"})  # "C" row missing entirely
    reconciled = runner._reconcile_failed_assets_from_db(cur, "run-1", ["A", "B", "C"], set())
    assert reconciled == {"B", "C"}


class _RaceFakeCursor(FakeCursor):
    """FakeCursor variant that also serves the RR-fix reconciliation query, with
    an INDEPENDENT `db_truth` dict standing in for build_run_assets rows as a
    concurrent writer/connection would actually leave them — separate from
    `self._state`, which is what worker()'s own read (`SELECT state FROM
    build_run_assets WHERE run_id = %s AND asset_id = %s`) sees. This reproduces
    the exact race the fix closes: the in-process tracker's view (`state`) and
    DB reality at final rollup (`db_truth`) can diverge.
    """

    def __init__(self, state, db_truth):
        super().__init__(state)
        self._db_truth = db_truth

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if s.startswith("SELECT asset_id, state FROM build_run_assets WHERE run_id"):
            self._result = [{"asset_id": a, "state": st} for a, st in self._db_truth.items()]
        else:
            super().execute(sql, params)


class _RaceFakeConn(FakeConn):
    def __init__(self, state, db_truth):
        super().__init__(state)
        self._db_truth = db_truth

    def cursor(self):
        return _RaceFakeCursor(self._state, self._db_truth)


def _install_race(monkeypatch, state, db_truth, mark_calls, run_asset_fn):
    monkeypatch.setattr(runner, "connect", lambda: _RaceFakeConn(state, db_truth))
    monkeypatch.setattr(runner, "acquire_chart_lock", lambda *a, **k: True)
    monkeypatch.setattr(runner, "release_chart_lock", lambda *a, **k: None)
    monkeypatch.setattr(runner, "check_signals", lambda *a, **k: None)
    monkeypatch.setattr(runner, "is_asset_complete", lambda *a, **k: False)

    def fake_mark_run_state(conn, cur, run_id, new_state, **kwargs):
        mark_calls.append(new_state)

    monkeypatch.setattr(runner, "mark_run_state", fake_mark_run_state)
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    import pipeline.orchestrator.writers as writers_mod
    monkeypatch.setattr(writers_mod, "discover_all", lambda: None, raising=False)
    monkeypatch.setattr(runner, "_check_writer_registry_gaps", lambda cur: [], raising=False)

    import pipeline.orchestrator.asset_runner as ar
    monkeypatch.setattr(ar, "run_asset", run_asset_fn)


def test_run_reported_failed_when_db_shows_error_the_in_process_tracker_missed(monkeypatch):
    """Every worker's in-process read says 'complete' (so `failed_assets` stays
    empty in _schedule_parallel), but the DB truth queried at final rollup shows
    the independent asset 'D' actually landed 'error' — the run must terminate
    'failed', not the green-over-report the in-process cache alone would have
    produced. (Only 'D' carries the race: it has no dependents in the A→B→C→D
    fixture's DAG, which keeps this test isolated from the separately-covered
    upstream-blocking behaviour in test_orchestrator_gate.py.)"""
    state: dict[str, str] = {}
    db_truth: dict[str, str] = {}
    mark_calls: list[str] = []

    def fake_run_asset(conn, cur, run_id, chart_id, asset_id, position):
        cur.execute(
            "UPDATE build_run_assets SET state=%s WHERE run_id=%s AND asset_id=%s",
            ("complete", run_id, asset_id),
        )
        state[asset_id] = "complete"                                   # in-process worker() view
        db_truth[asset_id] = "error" if asset_id == "D" else "complete"  # DB reality (the race)

    _install_race(monkeypatch, state, db_truth, mark_calls, fake_run_asset)

    runner.execute_run("run-1")

    assert "completed" not in mark_calls
    assert mark_calls[-1] == "failed", (
        f"DB shows build_run_assets='error' for asset D, which the in-process "
        f"tracker believed succeeded — final rollup must trust the DB, got {mark_calls!r}"
    )


def test_run_reported_completed_when_db_shows_success_the_in_process_tracker_lost(monkeypatch):
    """The independent asset 'D' reads 'error' in-process (so `failed_assets`
    picks it up in _schedule_parallel), but DB truth at final rollup shows
    'complete' for every asset — the run must terminate 'completed', not a
    false failure caused by trusting the stale in-process cache."""
    state: dict[str, str] = {}
    db_truth: dict[str, str] = {}
    mark_calls: list[str] = []

    def fake_run_asset(conn, cur, run_id, chart_id, asset_id, position):
        in_process_state = "error" if asset_id == "D" else "complete"
        cur.execute(
            "UPDATE build_run_assets SET state=%s WHERE run_id=%s AND asset_id=%s",
            (in_process_state, run_id, asset_id),
        )
        state[asset_id] = in_process_state    # in-process worker() view
        db_truth[asset_id] = "complete"       # DB reality (the race) — every asset actually landed clean

    _install_race(monkeypatch, state, db_truth, mark_calls, fake_run_asset)

    runner.execute_run("run-1")

    assert mark_calls[-1] == "completed", (
        f"DB shows build_run_assets='complete' for every asset — a stale "
        f"in-process failure for D must not falsely report the run 'failed', got {mark_calls!r}"
    )
