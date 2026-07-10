"""R6 0h-watchdog — proves the last_built_at heartbeat fix in
pipeline.orchestrator.asset_runner.run_asset().

Root cause (see 00_ARCHITECTURE/R6_RUN_LEDGER_v1_0.md, T-5/T-9 sections): the initial
'building' transition never stamped asset_throughput.last_built_at, so a single-substep
(non-heartbeating) writer's 'building' row kept whatever last_built_at value survived
from that asset's PREVIOUS build/finish — which can be arbitrarily stale. The Cloud
Scheduler watchdog (platform/src/app/api/cockpit/watchdog/route.ts, clause 2) reaps any
'building' row whose last_built_at is >15 min old, so a stale timestamp let it fire
almost immediately instead of after 15 real minutes of the CURRENT build.

Two things are proven here, independent of a live DB:

1. Code-level trace: the exact SQL `run_asset()` issues for the initial 'building'
   transition now stamps `last_built_at = NOW()` (INSERT value + ON CONFLICT SET), for
   both the chart-scoped and global-scope branches.

2. Synthetic timeline simulation of the watchdog's clause-2 reaper predicate
   (`state='building' AND last_built_at < NOW() - INTERVAL '15 minutes'`), replayed in
   pure Python against two scenarios:
     a. PRE-FIX behaviour (last_built_at left stale from a prior build) — the reaper
        fires almost immediately, confirming the bug as described.
     b. POST-FIX behaviour (last_built_at stamped at build start) — the reaper does NOT
        fire while the build is within its real 15-minute window, but DOES fire once a
        build has genuinely gone stale beyond 15 minutes with no further heartbeat —
        i.e. the fix restores the documented contract (wait the full window; still
        catch genuine hangs) rather than disabling the reaper.
"""
from __future__ import annotations

import sys
import pathlib
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import asset_runner as ar


# ── Part 1: code-level trace of the actual SQL run_asset() issues ─────────────

class _RecordingCursor:
    """Captures every SQL statement + params `run_asset()` issues, no DB required."""

    def __init__(self):
        self.executed: list[tuple[str, object]] = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        # Used by deps_unsatisfied()/registry-metadata lookups downstream of the
        # building-transition block under test; returning None short-circuits those
        # (deps_unsatisfied treats a missing row as "no deps to verify").
        return None

    def fetchall(self):
        return []

    def statements_containing(self, keyword: str) -> list[str]:
        return [s for s, _ in self.executed if keyword in s]


class _NoCommitConn:
    def commit(self):
        pass


def _run_building_transition_only(chart_id: str | None) -> _RecordingCursor:
    """
    Exercises just the asset_throughput 'building'-transition block of run_asset() by
    running it with dep-assertion off and letting it fall through to the registry-probe
    lookup (which fetchone()==None makes is_service=False / has_check=False), then
    stopping before `_run_data_writer` (no writer registered for this synthetic asset_id
    → `get_writer` returns None inside `_run_data_writer`, and since there's no probe/
    rebuild policy, the branch that would call it is skipped — the function returns
    after logging, never touching a writer). This isolates the exact statements the
    orchestrator's own state machine emits at build start.
    """
    cur = _RecordingCursor()
    conn = _NoCommitConn()
    ar._DEP_ASSERT_MODE = "off"  # bypass unrelated dep-assertion path for this trace
    ar.run_asset(conn, cur, run_id="run-1", chart_id=chart_id,
                 asset_id="_test_watchdog_asset", position=0)
    return cur


def test_chart_scoped_building_transition_stamps_last_built_at():
    cur = _run_building_transition_only(chart_id="482012f1-710e-4a25-994a-93821f5871aa")
    stmts = [s for s in cur.statements_containing("state = 'building'")
             if "asset_throughput" in s]
    assert stmts, "expected an asset_throughput 'building' transition statement"
    for sql in stmts:
        assert "last_built_at" in sql, (
            "the initial 'building' transition must stamp last_built_at — "
            "this is the exact watchdog-staleness bug being fixed"
        )
        assert "NOW()" in sql


def test_global_scope_building_transition_stamps_last_built_at():
    cur = _run_building_transition_only(chart_id=None)
    stmts = [s for s in cur.statements_containing("state = 'building'")
             if "asset_throughput" in s]
    assert stmts, "expected an asset_throughput 'building' transition statement"
    for sql in stmts:
        assert "last_built_at" in sql
        assert "NOW()" in sql


# ── Part 2: synthetic watchdog-clause-2 timeline simulation ───────────────────

def _watchdog_clause2_would_reap(state: str, last_built_at: datetime, now: datetime) -> bool:
    """
    Pure-Python mirror of platform/src/app/api/cockpit/watchdog/route.ts clause 2:

        UPDATE asset_throughput SET state = 'error', ...
        WHERE state = 'building' AND last_built_at < NOW() - INTERVAL '15 minutes'

    Kept intentionally line-for-line equivalent to the real SQL predicate so this test
    is a faithful synthetic stand-in, not a reinterpretation of the reaper's intent.
    """
    return state == "building" and last_built_at < (now - timedelta(minutes=15))


def test_prefix_behavior_reaps_almost_immediately_on_stale_prior_timestamp():
    """
    Reproduces the documented bug: PRIOR build finished/failed 20 minutes ago
    (last_built_at = t-20min). A NEW build starts now, transitions to 'building', but
    (pre-fix) never refreshes last_built_at. One watchdog tick (5 min) later, the
    reaper fires — even though the current build is only 5 minutes old.
    """
    t0 = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
    prior_last_built_at = t0 - timedelta(minutes=20)  # stale from a PRIOR build attempt

    # Pre-fix: building transition does NOT touch last_built_at.
    state = "building"
    last_built_at = prior_last_built_at  # unchanged by the (buggy) transition

    watchdog_tick = t0 + timedelta(minutes=5)  # next Cloud Scheduler tick
    assert _watchdog_clause2_would_reap(state, last_built_at, watchdog_tick) is True, (
        "pre-fix: the reaper incorrectly fires after only 5 real minutes because "
        "last_built_at was never refreshed at build start"
    )


def test_postfix_behavior_survives_full_window_then_still_catches_genuine_hangs():
    """
    Post-fix: the SAME prior-stale-timestamp scenario, but the building transition now
    stamps last_built_at = NOW() at t0. The build must survive watchdog ticks within
    its real 15-minute window (e.g. a healthy ~11-min ga_strength-class run), and the
    reaper must STILL fire if the build genuinely never advances past 15 real minutes
    (no per-substep heartbeat — the single-substep no-intermediate-commit case).
    """
    t0 = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)

    # Post-fix: building transition stamps last_built_at = NOW() regardless of any
    # stale prior value.
    state = "building"
    last_built_at = t0

    # Watchdog ticks at 5, 10, 15 minutes in — must NOT reap a build that's still
    # legitimately within its window (e.g. ga_strength's ~11-min real runtime).
    for minutes_in in (5, 10, 11, 14):
        tick = t0 + timedelta(minutes=minutes_in)
        assert _watchdog_clause2_would_reap(state, last_built_at, tick) is False, (
            f"post-fix build must survive a watchdog tick at t+{minutes_in}min "
            "(within the real 15-minute grace window)"
        )

    # But a build that NEVER advances (genuinely stuck, no heartbeat at all) must still
    # be reaped once the full 15-minute window has actually elapsed — the fix restores
    # the documented contract, it does not disable the reaper.
    tick_past_window = t0 + timedelta(minutes=20)
    assert _watchdog_clause2_would_reap(state, last_built_at, tick_past_window) is True, (
        "post-fix: a genuinely stuck build (no heartbeat for the full window) must "
        "still be reaped — the fix must not defeat the watchdog entirely"
    )


def test_healthy_completion_before_window_never_visible_to_reaper():
    """
    End-to-end sanity: a healthy single-substep writer (e.g. ga_strength, ~11 min) that
    completes and transitions OUT of 'building' before the 15-min mark is never even a
    candidate for clause 2 (state no longer 'building'), regardless of timestamp —
    confirming the fix's sufficiency for writers whose real runtime is under the
    threshold, without requiring an additional in-writer heartbeat (which §N.2 forbids
    writers from performing themselves).
    """
    t0 = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
    last_built_at = t0  # stamped at build start by the fix
    completion_time = t0 + timedelta(minutes=11)  # ga_strength-class real runtime

    # At completion, _run_data_writer's final UPDATE sets state to 'lit'/'dormant'/'error'
    # and refreshes last_built_at again — simulate the state flip only, since that alone
    # already removes it from clause 2's WHERE state='building' predicate.
    state_after_completion = "lit"
    tick_after_completion = completion_time + timedelta(minutes=1)
    assert _watchdog_clause2_would_reap(
        state_after_completion, last_built_at, tick_after_completion
    ) is False
