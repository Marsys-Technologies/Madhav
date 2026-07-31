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
    isolation: answers the reconciliation SELECT over build_run_assets AND the
    F-01 asset_throughput cross-check SELECT, and swallows the
    run.rollup_reconciled emit_event call's implicit dependency (patched by the
    caller).

    `throughput` is the {asset_id: asset_throughput.state} view — the state the
    writer path actually COMPUTED, as opposed to `db_rows`, which is
    build_run_assets' unconditional 'complete' literal."""

    def __init__(self, db_rows, throughput=None):
        self._db_rows = db_rows
        self._throughput = throughput if throughput is not None else {}
        self._result = []

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "SELECT asset_id, state FROM build_run_assets WHERE run_id" in s:
            self._result = [{"asset_id": a, "state": st} for a, st in self._db_rows.items()]
        elif "FROM asset_throughput" in s:
            self._result = [{"asset_id": a, "state": st, "chart_id": "chart-C"}
                            for a, st in self._throughput.items()]
        else:
            raise AssertionError(f"unexpected query: {s}")

    def fetchall(self):
        return list(self._result)


def test_reconcile_adds_db_error_missed_by_in_process_tracker(monkeypatch):
    """In-process cache believes nothing failed, but build_run_assets shows one
    asset in 'error' — the reconciled set must include it."""
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    cur = _MiniCursor({"A": "complete", "B": "error", "C": "complete"},
                      {"A": "lit", "B": "error", "C": "lit"})
    reconciled = runner._reconcile_failed_assets_from_db(
        cur, "run-1", ["A", "B", "C"], set(), "chart-C")
    assert reconciled == {"B"}


def test_reconcile_drops_stale_in_process_failure_when_db_shows_complete(monkeypatch):
    """In-process cache believes 'B' failed, but build_run_assets shows 'complete'
    AND asset_throughput corroborates it with a computed success state (e.g. a
    retry landed after the worker's first result was read) — DB wins, 'B' must be
    removed from the reconciled failed set."""
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    cur = _MiniCursor({"A": "complete", "B": "complete", "C": "complete"},
                      {"A": "lit", "B": "lit", "C": "lit"})
    reconciled = runner._reconcile_failed_assets_from_db(
        cur, "run-1", ["A", "B", "C"], {"B"}, "chart-C")
    assert reconciled == set()


def test_reconcile_treats_non_terminal_or_missing_row_as_failed(monkeypatch):
    """An asset whose build_run_assets row never reached a terminal state (still
    'building'/'queued', or missing entirely) must not be silently counted as a
    success just because the in-process cache never saw a failure for it."""
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    cur = _MiniCursor({"A": "complete", "B": "building"},  # "C" row missing entirely
                      {"A": "lit", "B": "building"})
    reconciled = runner._reconcile_failed_assets_from_db(
        cur, "run-1", ["A", "B", "C"], set(), "chart-C")
    assert reconciled == {"B", "C"}


# ── F-01 (SAMĀPTI B-N8-SWEEPFIX): 'incomplete' must reach the run verdict ──────
#
# `asset_runner.py` writes `build_run_assets.state = 'complete'` unconditionally —
# for `final_state` values of 'lit', 'dormant' AND 'incomplete' alike. 'incomplete'
# is SATYA-DĪPA's own no-op-completion rejection state (migration 474), meaning
# "this build did NOT finish". These tests pin the three places in runner.py where
# that state used to be lost, so the run could report a clean green over a build
# the system itself had classified unfinished (CLAUDE.md §N.8).

def test_reconcile_flags_incomplete_throughput_despite_complete_literal(monkeypatch):
    """The headline F-01 case. build_run_assets says 'complete' for every asset;
    asset_throughput says 'incomplete' for B. The run must NOT be clean."""
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    cur = _MiniCursor({"A": "complete", "B": "complete", "C": "complete"},
                      {"A": "lit", "B": "incomplete", "C": "lit"})
    reconciled = runner._reconcile_failed_assets_from_db(
        cur, "run-1", ["A", "B", "C"], set(), "chart-C")
    assert reconciled == {"B"}, (
        "asset_throughput.state='incomplete' means the writer's own substep plan did "
        "not finish; build_run_assets' unconditional 'complete' literal must not "
        "override it — that is the green over-report this fix exists to prevent"
    )


def test_reconcile_will_not_release_a_failure_on_the_literal_alone(monkeypatch):
    """'complete' must not pull an asset out of the failed set unless the COMPUTED
    state corroborates it. Without this the worker()/execute_dag fixes are undone
    at rollup: an asset correctly failed for being 'incomplete' would be put back
    in the clean column by the very next step."""
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    cur = _MiniCursor({"A": "complete", "B": "complete"},
                      {"A": "lit", "B": "incomplete"})
    reconciled = runner._reconcile_failed_assets_from_db(
        cur, "run-1", ["A", "B"], {"B"}, "chart-C")
    assert reconciled == {"B"}


def test_reconcile_keeps_failure_when_no_computed_state_corroborates_complete(monkeypatch):
    """'complete' with NO asset_throughput row at all. A successfully built asset
    always leaves a computed state behind, so a missing row means nothing
    corroborates the literal — the in-process failure must stand. This is the
    branch that decides whether `build_run_assets.state = 'complete'` is allowed
    to speak for a build on its own. It is not."""
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    cur = _MiniCursor({"A": "complete", "B": "complete"}, {"A": "lit"})  # no row for B
    reconciled = runner._reconcile_failed_assets_from_db(
        cur, "run-1", ["A", "B"], {"B"}, "chart-C")
    assert reconciled == {"B"}, (
        "an uncorroborated 'complete' literal must not release an asset from the "
        "failed set — that is the F-01 defect in its purest form"
    )


def test_reconcile_accepts_dormant_and_service_ok_as_success(monkeypatch):
    """'dormant' (ran, legitimately produced 0 rows) and 'service_ok' (health probe
    GREEN) are DECLARED successful outcomes — they must not be swept up as failures
    by the allowlist. Guards against over-correcting F-01 into a false-red."""
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    cur = _MiniCursor({"A": "complete", "B": "complete", "C": "complete", "D": "complete"},
                      {"A": "dormant", "B": "service_ok", "C": "mature", "D": "lit"})
    reconciled = runner._reconcile_failed_assets_from_db(
        cur, "run-1", ["A", "B", "C", "D"], set(), "chart-C")
    assert reconciled == set()


def test_execute_dag_success_rule_is_an_allowlist_not_a_denylist():
    """execute_dag's own docstring has always said `run_fn -> 'lit' | <anything
    else = failure>`; the code said `if result == 'error'`. Any non-success string
    — 'incomplete' above all — used to score as a success and let its downstream
    dispatch onto unfinished data."""
    deps = {"A": [], "B": ["A"]}

    failed, _ = runner.execute_dag(["A", "B"], deps, lambda a: "incomplete", worker_limit=2)
    assert "A" in failed, "'incomplete' must be a FAILURE outcome, not a success"
    assert "B" in failed, "B depends on a failed A — it must be blocked transitively"

    failed_ok, _ = runner.execute_dag(["A", "B"], deps, lambda a: "lit", worker_limit=2)
    assert failed_ok == set(), "'lit' must still be a success outcome"

    failed_dormant, _ = runner.execute_dag(["A", "B"], deps, lambda a: "dormant", worker_limit=2)
    assert failed_dormant == set(), "'dormant' is a declared success outcome"

    failed_unknown, _ = runner.execute_dag(["A"], {"A": []}, lambda a: "wat", worker_limit=1)
    assert failed_unknown == {"A"}, "an unrecognised outcome string must fail closed"


class _RaceFakeCursor(FakeCursor):
    """FakeCursor variant that also serves the RR-fix reconciliation query, with
    an INDEPENDENT `db_truth` dict standing in for build_run_assets rows as a
    concurrent writer/connection would actually leave them — separate from
    `self._state`, which is what worker()'s own read (`SELECT state FROM
    build_run_assets WHERE run_id = %s AND asset_id = %s`) sees. This reproduces
    the exact race the fix closes: the in-process tracker's view (`state`) and
    DB reality at final rollup (`db_truth`) can diverge.

    `throughput` is the third, independent view: asset_throughput.state — the state
    the writer path actually COMPUTED. F-01: build_run_assets' 'complete' is an
    unconditional literal, so worker() and the final reconciliation both cross-check
    against this dict.
    """

    def __init__(self, state, db_truth, throughput=None):
        super().__init__(state)
        self._db_truth = db_truth
        self._throughput = throughput if throughput is not None else {}

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if s.startswith("SELECT asset_id, state FROM build_run_assets WHERE run_id"):
            self._result = [{"asset_id": a, "state": st} for a, st in self._db_truth.items()]
        elif s.startswith("SELECT asset_id, state, chart_id FROM asset_throughput"):
            self._result = [{"asset_id": a, "state": st, "chart_id": "chart-C"}
                            for a, st in self._throughput.items()]
        elif s.startswith("SELECT state FROM asset_throughput"):
            st = self._throughput.get(params[0])
            self._result = [{"state": st}] if st is not None else []
        else:
            super().execute(sql, params)


class _RaceFakeConn(FakeConn):
    def __init__(self, state, db_truth, throughput=None):
        super().__init__(state)
        self._db_truth = db_truth
        self._throughput = throughput if throughput is not None else {}

    def cursor(self):
        return _RaceFakeCursor(self._state, self._db_truth, self._throughput)


def _install_race(monkeypatch, state, db_truth, mark_calls, run_asset_fn, throughput=None):
    monkeypatch.setattr(runner, "connect", lambda: _RaceFakeConn(state, db_truth, throughput))
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
    throughput: dict[str, str] = {}
    mark_calls: list[str] = []

    def fake_run_asset(conn, cur, run_id, chart_id, asset_id, position):
        cur.execute(
            "UPDATE build_run_assets SET state=%s WHERE run_id=%s AND asset_id=%s",
            ("complete", run_id, asset_id),
        )
        state[asset_id] = "complete"                                   # in-process worker() view
        db_truth[asset_id] = "error" if asset_id == "D" else "complete"  # DB reality (the race)
        throughput[asset_id] = "lit"   # every asset's COMPUTED state looks clean

    _install_race(monkeypatch, state, db_truth, mark_calls, fake_run_asset, throughput)

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
    throughput: dict[str, str] = {}
    mark_calls: list[str] = []

    def fake_run_asset(conn, cur, run_id, chart_id, asset_id, position):
        in_process_state = "error" if asset_id == "D" else "complete"
        cur.execute(
            "UPDATE build_run_assets SET state=%s WHERE run_id=%s AND asset_id=%s",
            (in_process_state, run_id, asset_id),
        )
        state[asset_id] = in_process_state    # in-process worker() view
        db_truth[asset_id] = "complete"       # DB reality (the race) — every asset actually landed clean
        throughput[asset_id] = "lit"          # ...and the COMPUTED state corroborates it

    _install_race(monkeypatch, state, db_truth, mark_calls, fake_run_asset, throughput)

    runner.execute_run("run-1")

    assert mark_calls[-1] == "completed", (
        f"DB shows build_run_assets='complete' for every asset — a stale "
        f"in-process failure for D must not falsely report the run 'failed', got {mark_calls!r}"
    )


# ── F-01 end-to-end: an 'incomplete' asset must turn the whole run red ─────────

def test_run_reported_failed_when_a_writer_landed_incomplete(monkeypatch):
    """The full F-01 cascade, end-to-end through execute_run.

    Reproduces the real reachable scenario: a heavy writer with a substep plan
    that does not finish. `asset_runner` writes `asset_throughput.state =
    'incomplete'` (SATYA-DĪPA's no-op-completion rejection) but writes
    `build_run_assets.state = 'complete'` unconditionally. Pre-fix, every
    downstream step read the literal — worker() returned 'complete', execute_dag's
    denylist scored it a success, and the reconciler actively removed it from the
    failed set — so `build_runs.state` came out 'completed'. An operator read a
    clean green over a build the system itself had classified unfinished.

    'D' is used because it has no dependents in the A→B→C + D fixture, isolating
    this from the separately-covered upstream-blocking behaviour.
    """
    state: dict[str, str] = {}
    db_truth: dict[str, str] = {}
    throughput: dict[str, str] = {}
    mark_calls: list[str] = []

    def fake_run_asset(conn, cur, run_id, chart_id, asset_id, position):
        # build_run_assets: the unconditional literal, for EVERY asset
        cur.execute(
            "UPDATE build_run_assets SET state=%s WHERE run_id=%s AND asset_id=%s",
            ("complete", run_id, asset_id),
        )
        state[asset_id] = "complete"
        db_truth[asset_id] = "complete"
        # asset_throughput: the state actually computed
        throughput[asset_id] = "incomplete" if asset_id == "D" else "lit"

    _install_race(monkeypatch, state, db_truth, mark_calls, fake_run_asset, throughput)

    runner.execute_run("run-1")

    assert "completed" not in mark_calls, (
        f"asset D landed asset_throughput.state='incomplete' — the run must NOT "
        f"report 'completed'; got {mark_calls!r}"
    )
    assert mark_calls[-1] == "failed", (
        f"a run containing an asset the build itself classified 'incomplete' must "
        f"terminate 'failed', got {mark_calls!r}"
    )


def test_incomplete_upstream_blocks_its_downstream_from_running(monkeypatch):
    """The half of F-01 that the run-level verdict alone does not cover.

    A red run verdict at rollup is too late for the DOWNSTREAM assets: pre-fix,
    worker() returned the 'complete' literal, so execute_dag put the incomplete
    asset in `completed` and fired `on_complete` — its dependents were then
    dispatched and BUILT ON UNFINISHED DATA. The register named this explicitly:
    the downstream never takes the honest `BLOCKED:` path because `execute_dag`
    never put the incomplete asset in `failed`.

    Here B (mid-chain, A→B→C) lands 'incomplete'. C must never run.
    """
    state: dict[str, str] = {}
    db_truth: dict[str, str] = {}
    throughput: dict[str, str] = {}
    mark_calls: list[str] = []
    ran: list[str] = []

    def fake_run_asset(conn, cur, run_id, chart_id, asset_id, position):
        ran.append(asset_id)
        cur.execute(
            "UPDATE build_run_assets SET state=%s WHERE run_id=%s AND asset_id=%s",
            ("complete", run_id, asset_id),
        )
        state[asset_id] = "complete"
        db_truth[asset_id] = "complete"
        throughput[asset_id] = "incomplete" if asset_id == "B" else "lit"

    _install_race(monkeypatch, state, db_truth, mark_calls, fake_run_asset, throughput)

    runner.execute_run("run-1")

    assert "A" in ran and "B" in ran
    assert "C" not in ran, (
        "C depends on B, which landed 'incomplete' — C must be BLOCKED, not built "
        "on an unfinished upstream slice"
    )
    assert mark_calls[-1] == "failed"


def test_run_still_completed_when_every_asset_is_dormant(monkeypatch):
    """Counter-case: 'dormant' is a DECLARED successful outcome (the writer ran and
    legitimately produced zero rows). The F-01 allowlist must not turn it red —
    a fix that fails everything is as useless as one that passes everything."""
    state: dict[str, str] = {}
    db_truth: dict[str, str] = {}
    throughput: dict[str, str] = {}
    mark_calls: list[str] = []

    def fake_run_asset(conn, cur, run_id, chart_id, asset_id, position):
        cur.execute(
            "UPDATE build_run_assets SET state=%s WHERE run_id=%s AND asset_id=%s",
            ("complete", run_id, asset_id),
        )
        state[asset_id] = "complete"
        db_truth[asset_id] = "complete"
        throughput[asset_id] = "dormant"

    _install_race(monkeypatch, state, db_truth, mark_calls, fake_run_asset, throughput)

    runner.execute_run("run-1")

    assert mark_calls[-1] == "completed", (
        f"every asset landed 'dormant' — a declared success — run must be "
        f"'completed', got {mark_calls!r}"
    )
