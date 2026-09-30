"""Packet B1 — "Cascade reads as one cause, N blocked".

Proof, against a mocked DB (same _Conn/_Cursor pattern as
test_a3_registry_divergence_narrowing.py::test_shared_error_terminal_helper_writes_...),
that:

  1. A seeded root failure with three dependents produces a build_run_assets write
     shape of ONE cause + THREE blocked_dependency rows, not four undifferentiated
     failures (the packet's stated proof, Decision 1).
  2. A writer TIMEOUT is recorded as its own root cause — never funneled through
     _mark_asset_blocked, never tagged disposition='blocked_dependency', and never
     given a fabricated 'timeout:Ns' dependency name (Decision 2, the packet's most
     valuable single change: this exact defect was found sitting in the engine's
     own code at execute_dag:673, per B1_before_20260926T173931Z.json §2).
  3. execute_dag routes a timeout to `on_timeout`, not `on_block` — proven by a
     fake callback pair that records which one fired.

Mutation-checked framing: every test below fails against the PRE-B1 code, because
(a) _mark_asset_blocked never set `disposition` or `blocked_by_asset_id` at all
(both params did not exist), and (b) execute_dag's timeout branch called
`_block(a, [f"timeout:{_budget}s"])` directly — there was no `on_timeout` callback
to route to.

Run:
  python -m pytest platform/python-sidecar/tests/test_b1_blocked_dependency_classification.py -v
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import runner  # noqa: E402
from pipeline.orchestrator.runner import execute_dag  # noqa: E402


class _Cursor:
    """Records every executed UPDATE/INSERT with its bound params, keyed by which
    table the SQL touches, so a test can inspect exactly what was written without a
    real database."""
    def __init__(self):
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, sql, params=None):
        self.calls.append((" ".join(sql.split()), params))

    def build_run_assets_updates(self):
        return [(sql, params) for sql, params in self.calls if sql.startswith("UPDATE build_run_assets")]


class _Conn:
    def commit(self):
        pass


# ── Decision 1: the packet's stated proof — 1 cause, 3 blocked, not 4 failures ──

def test_root_failure_with_three_dependents_is_one_cause_three_blocked():
    """Simulates a DAG ROOT -> {D1, D2, D3} where ROOT's writer fails (a genuine
    crash, recorded elsewhere by asset_runner.mark_asset_error — out of scope for
    this test) and D1/D2/D3 are blocked by execute_dag's ordinary on_block cascade,
    wired to the REAL _mark_asset_blocked(). Asserts the DB write shape is
    differentiated: exactly 3 build_run_assets rows carry
    disposition='blocked_dependency' (the blocked dependents) and ROOT gets none of
    them (nothing in this test's scope writes disposition for ROOT at all — its
    failure is recorded by a different, pre-existing code path that already leaves
    disposition NULL for a plain writer crash)."""
    cur = _Cursor()
    conn = _Conn()

    def run_fn(asset):
        return "error" if asset == "ROOT" else "lit"

    def on_block(a, blocking):
        runner._mark_asset_blocked(conn, cur, "run-1", "chart-1", a, blocking)

    deps = {"ROOT": [], "D1": ["ROOT"], "D2": ["ROOT"], "D3": ["ROOT"]}
    failed, terminal = execute_dag(
        ["ROOT", "D1", "D2", "D3"], deps, run_fn, worker_limit=4, on_block=on_block,
    )

    assert failed == {"ROOT", "D1", "D2", "D3"}, "the DAG scheduler still must mark all four as not-completed"

    updates = cur.build_run_assets_updates()
    blocked_writes = [(sql, p) for sql, p in updates if p is not None and p[1] == "blocked_dependency"]
    assert len(blocked_writes) == 3, (
        f"expected exactly 3 build_run_assets rows tagged disposition='blocked_dependency' "
        f"(D1, D2, D3), got {len(blocked_writes)}: {blocked_writes}"
    )
    blocked_asset_ids = {p[-1] for _, p in blocked_writes}  # (message, disposition, blocked_by, run_id, asset_id)
    assert blocked_asset_ids == {"D1", "D2", "D3"}
    # ROOT's own failure is NOT written via this mechanism at all — on_block is never
    # called for ROOT (it has no failed upstream; it fails on its own writer result).
    assert not any(p[-1] == "ROOT" for _, p in updates), (
        "ROOT must never be tagged blocked_dependency — it is the cause, not a dependent"
    )
    # Every blocked write also carries the immediate blocker in blocked_by_asset_id.
    for _, p in blocked_writes:
        assert p[2] == "ROOT", f"blocked_by_asset_id must name ROOT as the immediate blocker, got {p[2]!r}"


# ── Decision 2: a timeout is a root cause, never a fabricated dependency block ──

def test_mark_asset_timeout_is_not_a_blocked_dependency():
    """_mark_asset_timeout must record the asset as its OWN failure: disposition
    stays NULL (same as any plain writer crash), blocked_by_asset_id stays NULL, and
    the message says TIMEOUT — never 'BLOCKED: upstream dependency(ies)
    timeout:600s'."""
    cur = _Cursor()
    conn = _Conn()

    runner._mark_asset_timeout(conn, cur, "run-1", "chart-1", "slow_writer", 600)

    updates = cur.build_run_assets_updates()
    assert len(updates) == 1
    sql, params = updates[0]
    message, disposition, blocked_by, run_id, asset_id = params
    assert asset_id == "slow_writer"
    assert disposition is None, f"a timeout must never be classified blocked_dependency, got {disposition!r}"
    assert blocked_by is None, f"a timeout blocks nothing but itself, got blocked_by_asset_id={blocked_by!r}"
    assert message.startswith("TIMEOUT:"), f"expected an honest TIMEOUT message, got {message!r}"
    assert "timeout:600s" not in message, "must not fabricate a fake dependency name in the message"
    assert "upstream dependency" not in message, "must not use the BLOCKED cascade template at all"


def test_mark_asset_blocked_still_sets_disposition_and_blocked_by():
    """Companion regression guard for _mark_asset_blocked itself (Decision 1): a
    genuine dependency block DOES get disposition='blocked_dependency' plus the
    blocking asset id(s), joined the same way the existing message text is."""
    cur = _Cursor()
    conn = _Conn()

    runner._mark_asset_blocked(conn, cur, "run-1", "chart-1", "dependent_a", ["upstream_x", "upstream_y"])

    updates = cur.build_run_assets_updates()
    assert len(updates) == 1
    message, disposition, blocked_by, run_id, asset_id = updates[0][1]
    assert disposition == "blocked_dependency"
    assert blocked_by == "upstream_x, upstream_y"
    assert asset_id == "dependent_a"
    assert message.startswith("BLOCKED: upstream dependency(ies)")


# ── execute_dag routes a timeout to on_timeout, never on_block ──────────────────

def test_execute_dag_routes_timeout_to_on_timeout_not_on_block(monkeypatch):
    """The §N.8 requirement: name the code path that makes an asset read as a cause
    rather than a block. Proves execute_dag's timeout branch calls on_timeout(asset,
    budget) — never on_block — by wiring both callbacks to distinct recorders and
    forcing a fast, deterministic timeout via a monkeypatched poll interval and a
    slow run_fn."""
    monkeypatch.setattr(runner, "_POLL_INTERVAL", 0.02)

    blocked_calls: list[tuple] = []
    timeout_calls: list[tuple] = []

    def rec(asset):
        import time
        time.sleep(3.0)
        return "lit"

    failed, terminal = execute_dag(
        ["SLOW"], {"SLOW": []}, rec, worker_limit=1,
        on_block=lambda a, deps: blocked_calls.append((a, deps)),
        on_timeout=lambda a, budget: timeout_calls.append((a, budget)),
        timeouts_of={"SLOW": 1},
    )

    assert "SLOW" in failed
    assert timeout_calls == [("SLOW", 1)], f"expected exactly one on_timeout call for SLOW, got {timeout_calls}"
    assert blocked_calls == [], (
        "on_block must NEVER be called for a writer's own timeout — that is exactly "
        "the pre-B1 defect (a root cause funneled through the dependency-block path "
        "with a fabricated 'timeout:Ns' dependency name)"
    )


def test_execute_dag_still_blocks_transitive_dependents_of_a_timed_out_asset():
    """A timeout still fails `a` into the `failed` set, so `a`'s OWN dependents are
    correctly cascade-blocked via the ordinary on_block path on a later round —
    only `a` itself is exempted from on_block, not its downstream."""
    import time as _time

    def rec(asset):
        if asset == "SLOW":
            _time.sleep(3.0)
        return "lit"

    blocked_calls: list[str] = []
    timeout_calls: list[str] = []
    import pipeline.orchestrator.runner as R
    orig_poll = R._POLL_INTERVAL
    R._POLL_INTERVAL = 0.02
    try:
        failed, terminal = execute_dag(
            ["SLOW", "DEP"], {"SLOW": [], "DEP": ["SLOW"]}, rec, worker_limit=2,
            on_block=lambda a, deps: blocked_calls.append(a),
            on_timeout=lambda a, budget: timeout_calls.append(a),
            timeouts_of={"SLOW": 1, "DEP": 100},
        )
    finally:
        R._POLL_INTERVAL = orig_poll

    assert failed == {"SLOW", "DEP"}
    assert timeout_calls == ["SLOW"]
    assert blocked_calls == ["DEP"], "DEP must be blocked via on_block (its upstream SLOW failed), not exempted"
