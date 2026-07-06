"""
Tests for the wave-parallel DAG scheduler core (runner.execute_dag).

execute_dag is the DB-free scheduling algorithm behind _schedule_parallel. These
tests verify the correctness invariants the build's completeness/consistency
guarantee rests on:
  * an asset never starts before ALL its deps complete (the gate),
  * independent assets actually run concurrently (the speedup),
  * a failed asset blocks its downstream transitively (no build-on-bad-data),
  * stop/pause halts dispatch,
  * worker_limit=1 degrades to dependency-ordered serial (safe fallback).
  * stale-mark lock (_stale_mark_lock) serialises downstream closure across workers.
"""
from __future__ import annotations

import threading
import time

from pipeline.orchestrator.runner import execute_dag


class _Recorder:
    """Thread-safe run_fn that records start/finish order and peak concurrency."""
    def __init__(self, fail: set[str] | None = None, dwell: float = 0.0):
        self.fail = fail or set()
        self.dwell = dwell
        self.lock = threading.Lock()
        self.active = 0
        self.peak = 0
        self.started: list[str] = []
        self.finished: list[str] = []
        self.start_t: dict[str, float] = {}
        self.end_t: dict[str, float] = {}

    def __call__(self, asset: str) -> str:
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
            self.started.append(asset)
            self.start_t[asset] = time.monotonic()
        if self.dwell:
            time.sleep(self.dwell)
        with self.lock:
            self.active -= 1
            self.finished.append(asset)
            self.end_t[asset] = time.monotonic()
        return "error" if asset in self.fail else "lit"


# Diamond: A -> {B, C} -> D   (B and C independent; both need A; D needs B and C)
DIAMOND = {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]}


def test_respects_dependency_order():
    rec = _Recorder(dwell=0.02)
    failed, terminal = execute_dag(["A", "B", "C", "D"], DIAMOND, rec, worker_limit=4)
    assert terminal is None and failed == set()
    # A finishes before B/C start; B and C finish before D starts.
    assert rec.end_t["A"] <= rec.start_t["B"] + 1e-6
    assert rec.end_t["A"] <= rec.start_t["C"] + 1e-6
    assert rec.end_t["B"] <= rec.start_t["D"] + 1e-6
    assert rec.end_t["C"] <= rec.start_t["D"] + 1e-6


def test_independent_assets_run_concurrently():
    rec = _Recorder(dwell=0.05)
    execute_dag(["A", "B", "C", "D"], DIAMOND, rec, worker_limit=4)
    # B and C have no edge between them -> they must overlap.
    assert rec.peak >= 2, f"expected concurrency >= 2, got {rec.peak}"


def test_worker_limit_one_is_serial():
    rec = _Recorder(dwell=0.01)
    execute_dag(["A", "B", "C", "D"], DIAMOND, rec, worker_limit=1)
    assert rec.peak == 1, f"worker_limit=1 must never overlap, got {rec.peak}"
    # still a valid topological order
    assert rec.started.index("A") < rec.started.index("B")
    assert rec.started.index("B") < rec.started.index("D")


def test_failure_blocks_downstream_transitively():
    # B fails -> D (needs B,C) must be blocked and never run; C still runs.
    rec = _Recorder(fail={"B"}, dwell=0.0)
    blocked: list[str] = []
    failed, terminal = execute_dag(
        ["A", "B", "C", "D"], DIAMOND, rec, worker_limit=4,
        on_block=lambda a, deps: blocked.append(a),
    )
    assert "B" in failed and "D" in failed
    assert "D" not in rec.started, "D ran despite a failed upstream"
    assert "D" in blocked
    assert "C" in rec.finished  # independent of B, still completes


def test_seed_completed_satisfies_out_of_plan_dep():
    # E depends on X which is NOT in the plan; seeding X as completed makes E ready.
    deps = {"E": ["X"]}
    rec = _Recorder()
    failed, terminal = execute_dag(["E"], deps, rec, worker_limit=2, seed_completed={"X"})
    assert failed == set() and "E" in rec.finished


def test_missing_upstream_deadlock_is_blocked_not_hung():
    # F needs Y; Y neither in plan nor seeded -> F can never be ready. Must block, not hang.
    deps = {"F": ["Y"]}
    rec = _Recorder()
    blocked: list[str] = []
    failed, terminal = execute_dag(
        ["F"], deps, rec, worker_limit=2, on_block=lambda a, d: blocked.append(a),
    )
    assert "F" in failed and "F" in blocked and "F" not in rec.started


def test_stop_halts_dispatch():
    # should_stop returns 'stop' immediately -> nothing dispatched, terminal='stopped'.
    rec = _Recorder()
    failed, terminal = execute_dag(
        ["A", "B", "C", "D"], DIAMOND, rec, worker_limit=4,
        should_stop=lambda: "stop",
    )
    assert terminal == "stopped"
    assert rec.started == []


def test_per_asset_timeout_evicts_and_fails_slow_writer(monkeypatch):
    """JL-023: a writer that exceeds ITS asset_registry budget is killed+failed by
    the watchdog (never hangs), and a fast writer under its budget still completes.
    The budget comes per-asset from timeouts_of, not the global default."""
    import pipeline.orchestrator.runner as R
    monkeypatch.setattr(R, "_POLL_INTERVAL", 0.02)  # tight poll so the deadline check runs quickly
    rec = _Recorder(dwell=3.0)  # every worker dwells 3s; only budgets decide the outcome
    # SLOW gets a 1s budget (evicted ~1s in, well before its 3s dwell finishes);
    # FAST is independent and gets a generous 100s budget (completes at ~3s dwell).
    failed, terminal = R.execute_dag(
        ["SLOW", "FAST"], {"SLOW": [], "FAST": []}, rec, worker_limit=2,
        timeouts_of={"SLOW": 1, "FAST": 100},
    )
    assert "SLOW" in failed          # exceeded its per-asset budget -> killed+failed
    assert "FAST" not in failed      # under its budget -> completed
    assert terminal is None          # run finished cleanly, did not hang


def test_stale_mark_lock_exists_and_is_a_lock():
    """_stale_mark_lock must be a threading.Lock so the parallel race is guarded."""
    from pipeline.orchestrator.asset_runner import _stale_mark_lock
    assert isinstance(_stale_mark_lock, type(threading.Lock())), (
        "_stale_mark_lock must be a threading.Lock — it serialises downstream "
        "stale-mark UPDATEs across concurrent workers"
    )
    # Verify the lock is re-entrant-safe for tests: acquire + release works.
    assert _stale_mark_lock.acquire(blocking=False), "lock should be free at test time"
    _stale_mark_lock.release()


def test_stale_mark_lock_serialises_concurrent_callers():
    """Two threads cannot hold _stale_mark_lock simultaneously."""
    from pipeline.orchestrator.asset_runner import _stale_mark_lock

    held_simultaneously = threading.Event()
    inside = threading.Event()

    def holder():
        with _stale_mark_lock:
            inside.set()             # signal: lock acquired
            time.sleep(0.05)         # hold for 50ms

    def tester():
        inside.wait()                # wait until holder has the lock
        # try_acquire should fail (lock is held)
        got = _stale_mark_lock.acquire(blocking=False)
        if got:
            _stale_mark_lock.release()
            held_simultaneously.set()

    import time
    t1 = threading.Thread(target=holder)
    t2 = threading.Thread(target=tester)
    t1.start(); t2.start()
    t1.join(); t2.join()
    assert not held_simultaneously.is_set(), (
        "two threads acquired _stale_mark_lock simultaneously — race not guarded"
    )


