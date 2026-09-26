"""A3 — 'Stop one registry change killing a whole run'.

Integration-level proof (execute_run end-to-end, mocked DB) that a genuine
asset_registry divergence detected at preflight now fails ONLY the diverging
asset(s) plus their transitive dependents — not the entire run.

Mirrors the reconstructed worst case in
00_ARCHITECTURE/briefs/nirmana/engine/measurements/A3_before_20260926T120851Z.json
(run d4a6dae2-..., 10 planned L0 assets, 1 diverged, 10/10 aborted) but with one
of the ten assets given a synthetic dependent so the "dependents blocked, the
rest complete" half of the claim is exercised too, not just "the diverged asset
itself fails".

Honest framing of the "after" figure (post gate-review correction, C-2): the
before-figure (100% blast radius, every one of 8 production runs) is a real,
re-derivable production measurement — a different instrument and population
from anything below. What follows is a unit-level reconstruction against a
synthetic 10-asset plan with a mocked DB, not a production measurement, and is
reported as such. The production after-figure is unmeasured and stays that way
until a real divergence occurs post-deploy. The FakeCursor below DOES answer
the engine's own `_reconcile_failed_assets_from_db` query (build_run_assets +
asset_throughput) rather than falling through to an empty result — so the
"2 failed, 8 complete" this file demonstrates is confirmed by the same rollup
`execute_run` uses to decide the run's own final state, not read off a
test-side proxy dict alone (see `test_one_genuine_divergence_...`'s assertion
on `mark_run_state`'s final call and the absence of a `run.rollup_reconciled`
correction event).
"""
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import runner  # noqa: E402


CHART_ID = "33333333-3333-4333-8333-333333333333"

# 10 assets: bg_diverge_target's registry row will differ from the frozen manifest
# in some tests; bg_diverge_dependent depends on it (proves transitive blocking);
# the other 8 are independent (prove "the rest complete", not merely "the rest
# don't crash").
PLAN = [
    "bg_diverge_target", "bg_diverge_dependent",
    "bg_a", "bg_b", "bg_c", "bg_d", "bg_e", "bg_f", "bg_g", "bg_h",
]

# The frozen manifest's own copy of the registry (what dispatch-time accepted).
REGISTRY_FROZEN = {
    "bg_diverge_target": {"scope": "per_chart", "depends_on": [], "natural_key_partition": None, "has_cowriters": False},
    "bg_diverge_dependent": {"scope": "per_chart", "depends_on": ["bg_diverge_target"], "natural_key_partition": None, "has_cowriters": False},
    **{a: {"scope": "per_chart", "depends_on": [], "natural_key_partition": None, "has_cowriters": False}
       for a in ["bg_a", "bg_b", "bg_c", "bg_d", "bg_e", "bg_f", "bg_g", "bg_h"]},
}


def _frozen_run_fields():
    manifest = {
        "version": "nirmana-run-manifest/v1",
        "chart_id": CHART_ID,
        "scope": "global",
        "scope_target": None,
        "action": "rebuild",
        "waves": [PLAN],
        "assets": [
            {"asset_id": a, "expected_code_digest": "0" * 64, **REGISTRY_FROZEN[a]}
            for a in PLAN
        ],
    }
    return {
        "plan_manifest": manifest,
        "plan_manifest_digest": runner._canonical_manifest_digest(manifest),
    }


class FakeCursor:
    """Cursor answering the queries execute_run issues — including, after the
    C-2 gate-review correction, the reconcile-at-rollup queries
    (`_reconcile_failed_assets_from_db` / `_throughput_states`), so the run's
    own final accounting is genuinely exercised rather than falling through to
    an unanswered, always-empty result."""
    def __init__(self, state: dict, throughput: dict, registry_live: dict):
        self._state = state              # build_run_assets.state mirror
        self._throughput = throughput    # asset_throughput.state mirror
        self._registry_live = registry_live  # what the LIVE registry looks like at check-time
        self._result = None

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "count(*) AS active" in s:
            self._result = [{"active": 0}]
        elif "FROM build_runs WHERE id" in s:
            self._result = [{
                "id": "run-1", "chart_id": CHART_ID, "scope": "global",
                "scope_target": None, "action": "rebuild", "plan": PLAN, "state": "planned",
                **_frozen_run_fields(),
            }]
        elif "FROM asset_registry ar WHERE ar.asset_id = ANY" in s:
            # The REAL _verify_registry_still_matches_manifest query — answered from
            # the (possibly diverged) live-registry fixture, not the frozen copy.
            self._result = [
                {"asset_id": a, **row} for a, row in self._registry_live.items() if a in params[0]
            ]
        elif "SELECT asset_id, state FROM build_run_assets WHERE run_id" in s:
            # _reconcile_failed_assets_from_db's whole-run fetch (C-2 fix: this
            # used to fall through to the catch-all empty result below, which
            # made the reconcile step treat every asset as non-terminal).
            self._result = [{"asset_id": a, "state": v} for a, v in self._state.items()]
        elif "FROM asset_throughput WHERE asset_id = ANY" in s:
            # _throughput_states (also consumed by _reconcile_failed_assets_from_db).
            wanted = set(params[0])
            self._result = [
                {"asset_id": a, "state": v, "chart_id": CHART_ID}
                for a, v in self._throughput.items() if a in wanted
            ]
        elif s.startswith("SELECT state FROM build_run_assets"):
            self._result = [{"state": self._state.get(params[1])}]
        elif "INSERT INTO asset_throughput" in s:
            # _mark_asset_error_terminal's upsert — shared by _mark_asset_blocked
            # and _terminalize_diverged_assets. asset_id is always params[0] in
            # both the chart_id-present and chart_id-NULL variants.
            self._throughput[params[0]] = "error"
            self._result = []
        elif "UPDATE build_run_assets SET state='error'" in s:
            # Shared by _mark_asset_blocked and _terminalize_diverged_assets
            # (both go through _mark_asset_error_terminal). Packet B1 added two more
            # bound params (disposition, blocked_by_asset_id) ahead of run_id/asset_id
            # in the UPDATE's param tuple — asset_id is the LAST positional param
            # regardless of how many columns the SET clause grows to, so index from
            # the end rather than assuming a fixed absolute position.
            self._state[params[-1]] = "error"
            self._result = []
        else:
            self._result = []

    def fetchone(self):
        return self._result[0] if self._result else None

    def fetchall(self):
        return list(self._result or [])


class FakeConn:
    def __init__(self, state, throughput, registry_live):
        self._state = state
        self._throughput = throughput
        self._registry_live = registry_live
        self.autocommit = False

    def cursor(self):
        return FakeCursor(self._state, self._throughput, self._registry_live)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def _install(monkeypatch, state, registry_live, fail_assets=frozenset(), writer_gaps=None):
    """Patch execute_run's collaborators. _verify_registry_still_matches_manifest
    and _terminalize_diverged_assets are the REAL functions under test — everything
    else is faked exactly as test_orchestrator_gate.py's harness does.

    Returns (ran, throughput, mark_calls, emitted):
      ran         — asset_ids whose writer was actually invoked (dispatch proof)
      throughput  — the fake asset_throughput mirror (post-run)
      mark_calls  — every (state, ...) argument tuple passed to mark_run_state,
                    in call order — lets a test assert the ENGINE's own final
                    rollup state, not just the test's local state dict
      emitted     — every event passed to emit_event, in order
    """
    throughput: dict[str, str] = {}
    monkeypatch.setattr(runner, "connect", lambda: FakeConn(state, throughput, registry_live))
    monkeypatch.setattr(runner, "acquire_chart_lock", lambda *a, **k: True)
    monkeypatch.setattr(runner, "release_chart_lock", lambda *a, **k: None)
    monkeypatch.setattr(runner, "release_global_assets_lock", lambda *a, **k: None)
    monkeypatch.setattr(runner, "acquire_global_assets_lock", lambda *a, **k: True)
    monkeypatch.setattr(runner, "check_signals", lambda *a, **k: None)
    monkeypatch.setattr(runner, "is_asset_complete", lambda *a, **k: False)
    monkeypatch.setattr(runner, "claim_runnable_run", lambda *a, **k: True)

    mark_calls: list[tuple] = []
    monkeypatch.setattr(
        runner, "mark_run_state",
        lambda conn, cur, run_id, state, **kw: mark_calls.append((state, kw)),
    )
    emitted: list[dict] = []
    monkeypatch.setattr(runner, "emit_event", lambda evt: emitted.append(evt))
    monkeypatch.setattr(runner, "_verify_sidecar_code_matches_manifest", lambda *a, **k: None)
    import pipeline.orchestrator.writers as writers_mod
    monkeypatch.setattr(writers_mod, "discover_all", lambda: None, raising=False)
    monkeypatch.setattr(runner, "_check_writer_registry_gaps", lambda cur: list(writer_gaps or []), raising=False)

    ran: list[str] = []

    def fake_run_asset(
        conn, cur, run_id, chart_id, asset_id, position, *,
        declared_deps, natural_key_partition, has_cowriters, force=False,
    ):
        ran.append(asset_id)
        outcome = "error" if asset_id in fail_assets else "complete"
        cur.execute(
            "UPDATE build_run_assets SET state=%s WHERE run_id=%s AND asset_id=%s",
            (outcome, run_id, asset_id),
        )
        state[asset_id] = outcome
        # Mirror into asset_throughput too (C-2 fix): 'complete' is a valid
        # _SUCCESS_OUTCOMES member, so reusing the same literal is faithful to
        # what a real writer would report on success, and 'error' is correctly
        # NOT a success state either way.
        throughput[asset_id] = outcome

    import pipeline.orchestrator.asset_runner as ar
    monkeypatch.setattr(ar, "run_asset", fake_run_asset)
    return ran, throughput, mark_calls, emitted


def test_one_genuine_divergence_fails_only_that_asset_plus_dependents(monkeypatch):
    """The A3 headline proof: 10 planned assets, ONE registry divergence. Must
    produce 1 failed + its dependent blocked + the other 8 complete — NOT a
    10/10 wholesale abort (the pre-fix behaviour, confirmed in the before-state
    measurement for run d4a6dae2-...).

    C-2: this is a unit-level reconstruction (synthetic plan, mocked DB), not a
    production measurement — see the module docstring for the honest before/
    after framing. What this test asserts beyond the dispatch log (`ran`) is
    that the ENGINE'S OWN reconcile-at-rollup step agrees: no
    `run.rollup_reconciled` correction event fires (meaning the DB-truth check
    found nothing to correct — the in-process failed set already matched DB
    reality), and `mark_run_state`'s FINAL call reports the run itself as
    'failed' (correct — a narrowed run is still not a clean run), not silently
    'completed'.
    """
    state: dict[str, str] = {}
    registry_live = dict(REGISTRY_FROZEN)
    # Genuine, structurally load-bearing divergence: scope flipped after dispatch.
    registry_live["bg_diverge_target"] = {
        **REGISTRY_FROZEN["bg_diverge_target"], "scope": "global",
    }
    ran, throughput, mark_calls, emitted = _install(monkeypatch, state, registry_live)

    runner.execute_run("run-1")

    # The diverging asset itself never runs (writer not invoked) — it fails at
    # preflight, before any writer touches it.
    assert "bg_diverge_target" not in ran
    assert state["bg_diverge_target"] == "error"
    # Its dependent is blocked, also never runs.
    assert "bg_diverge_dependent" not in ran
    assert state["bg_diverge_dependent"] == "error"
    # Every OTHER asset in the plan — 8 of them — ran and completed normally.
    independent = ["bg_a", "bg_b", "bg_c", "bg_d", "bg_e", "bg_f", "bg_g", "bg_h"]
    assert set(ran) == set(independent)
    assert all(state[a] == "complete" for a in independent)
    # Blast radius in THIS reconstruction: 2/10 affected, not 10/10.
    affected = sum(1 for a in PLAN if state.get(a) == "error")
    assert affected == 2, f"expected narrowed blast radius of 2/10, got {affected}/10"

    # C-2: the engine's OWN rollup agrees with the 2/10 figure, not the fake
    # cursor silently reporting 10/10 (the exact gap the gate review found).
    assert not any(e.get("type") == "run.rollup_reconciled" for e in emitted), (
        "a rollup_reconciled correction event means the DB-truth check disagreed "
        "with the in-process failed set — it must NOT fire when both already "
        "agree on the narrowed 2/10 result"
    )
    assert mark_calls, "mark_run_state was never called — the run never reached rollup"
    assert mark_calls[-1][0] == "failed", (
        "a run with a genuine (narrowed) failure must still report 'failed' overall "
        f"— got {mark_calls[-1][0]!r}"
    )


def test_no_divergence_runs_every_asset_normally(monkeypatch):
    """Control: an UNCHANGED registry must not narrow anything — every asset runs,
    and the engine's own rollup reports the run 'completed'."""
    state: dict[str, str] = {}
    registry_live = dict(REGISTRY_FROZEN)  # identical to the frozen manifest
    ran, throughput, mark_calls, emitted = _install(monkeypatch, state, registry_live)

    runner.execute_run("run-1")

    assert set(ran) == set(PLAN)
    assert all(state[a] == "complete" for a in PLAN)
    assert mark_calls[-1][0] == "completed"


def test_two_simultaneous_divergences_are_both_named_and_both_fail(monkeypatch):
    """A3 Decision 4: TWO assets diverge in the same run. Both must be named (the
    old first-mismatch-only check could only ever report one), both fail, and
    their respective dependents/independents are handled correctly."""
    state: dict[str, str] = {}
    registry_live = dict(REGISTRY_FROZEN)
    registry_live["bg_diverge_target"] = {**REGISTRY_FROZEN["bg_diverge_target"], "scope": "global"}
    registry_live["bg_a"] = {**REGISTRY_FROZEN["bg_a"], "natural_key_partition": "some_other_partition"}
    ran, throughput, mark_calls, emitted = _install(monkeypatch, state, registry_live)

    runner.execute_run("run-1")

    # Both diverging assets fail; neither runs.
    assert "bg_diverge_target" not in ran and state["bg_diverge_target"] == "error"
    assert "bg_a" not in ran and state["bg_a"] == "error"
    # bg_diverge_target's dependent is blocked.
    assert "bg_diverge_dependent" not in ran and state["bg_diverge_dependent"] == "error"
    # Everything else (6 assets) still completes.
    still_ok = ["bg_b", "bg_c", "bg_d", "bg_e", "bg_f", "bg_g", "bg_h"]
    assert set(ran) == set(still_ok)
    assert all(state[a] == "complete" for a in still_ok)


def test_divergence_error_message_names_the_asset_and_keeps_the_monitoring_prefix(monkeypatch):
    """The per-asset error text must still start with 'frozen manifest validation
    failed:' (existing monitoring keys on this prefix — see the before-measurement's
    manifest_invalidation_population query) so narrowing doesn't silently break
    whatever dashboards/alerts already grep for it."""
    state: dict[str, str] = {}
    registry_live = dict(REGISTRY_FROZEN)
    registry_live["bg_diverge_target"] = {**REGISTRY_FROZEN["bg_diverge_target"], "scope": "global"}
    _install(monkeypatch, state, registry_live)

    errors: dict[str, str] = {}
    orig_execute = FakeCursor.execute

    def recording_execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "UPDATE build_run_assets SET state='error'" in s:
            # Packet B1: asset_id is now the LAST positional param (see the
            # FakeCursor.execute comment above); message is still first.
            errors[params[-1]] = params[0]
        return orig_execute(self, sql, params)

    monkeypatch.setattr(FakeCursor, "execute", recording_execute)

    runner.execute_run("run-1")

    assert errors["bg_diverge_target"].startswith("frozen manifest validation failed:")
    assert "bg_diverge_target" in errors["bg_diverge_target"]
    # The dependent gets the ordinary BLOCKED message, not the divergence one.
    assert errors["bg_diverge_dependent"].startswith("BLOCKED:")


def test_writer_gap_hard_fail_never_lets_a_divergence_go_undetected_and_unwritten(monkeypatch):
    """C-1 (blocks the commit) — inverted probe from the gate review.

    The gate review's probe: with `_WRITER_GAP_MODE="enforce"` and a writer gap
    present, alongside a genuine registry divergence, the OLD ordering ran
    divergence detection FIRST and the writer-gap hard-fail block SECOND — so
    `_verify_registry_still_matches_manifest` found the divergence, and then the
    writer-gap block's `sys.exit(1)` discarded it: `SystemExit(1)`, `writes ==
    {}` (the review's own probe result). A divergence detected and then
    permanently unrecorded, with nothing to retry, is exactly the silent-failure
    shape this campaign exists to eliminate.

    C-1's accepted fix (either is allowed by the coordinator's ruling): "the
    divergence must be recorded (OR the check must fire before detection so no
    divergence is ever pending)". This packet took the second option — the
    writer-gap check was reordered to run BEFORE
    `_verify_registry_still_matches_manifest` — so under the fix, the divergence
    check must NEVER even be reached when a writer gap hard-fails first.

    This test spies on `_verify_registry_still_matches_manifest` itself (not a
    side effect of it) — the only assertion that distinguishes "never ran" from
    "ran and its result was discarded". Under the PRE-FIX ordering this spy
    would record a call before the SystemExit; under the fix it must not.
    """
    monkeypatch.setattr(runner, "_WRITER_GAP_MODE", "enforce")

    calls: list[str] = []
    orig_verify = runner._verify_registry_still_matches_manifest

    def spy_verify(cur, frozen):
        calls.append("called")
        return orig_verify(cur, frozen)

    monkeypatch.setattr(runner, "_verify_registry_still_matches_manifest", spy_verify)

    state: dict[str, str] = {a: "queued" for a in PLAN}
    registry_live = dict(REGISTRY_FROZEN)
    registry_live["bg_diverge_target"] = {**REGISTRY_FROZEN["bg_diverge_target"], "scope": "global"}

    ran, throughput, mark_calls, emitted = _install(
        monkeypatch, state, registry_live, writer_gaps=["some_ungapped_writer"],
    )

    with pytest.raises(SystemExit) as exc_info:
        runner.execute_run("run-1")

    assert exc_info.value.code == 1, "writer-gap enforce must still hard-fail the run"
    # The decisive assertion: the registry-divergence check never ran at all —
    # under the pre-fix ordering `calls` would be `["called"]` here, proving the
    # divergence WAS found before the writer-gap exit discarded it.
    assert calls == [], (
        "the registry-divergence check ran BEFORE the writer-gap hard-fail exit — "
        "this is exactly the pre-fix ordering that let a divergence be detected "
        "and then permanently discarded when the writer-gap block hard-failed "
        "immediately afterward (C-1)"
    )
    # Nothing was ever written for the diverging asset either — consistent with
    # "never detected" rather than "detected, then silently reverted".
    assert state["bg_diverge_target"] == "queued"
    # No writer for the diverging asset ever ran either way (it was never
    # reached — the run hard-failed at preflight before dispatch began).
    assert ran == []
    # And the run itself reports 'failed' via the writer-gap path, as before.
    assert mark_calls and mark_calls[-1][0] == "failed"


def test_shared_error_terminal_helper_writes_asset_throughput_for_both_callers(monkeypatch):
    """C-3 (blocks the next packet touching the shared helper).

    `_mark_asset_error_terminal` is now shared by `_mark_asset_blocked` (the
    BLOCKED cascade — 1,281 of the campaign's 2,283 failure records) and
    `_terminalize_diverged_assets` (A3's new caller). The gate review's mutation
    M5 deleted the ENTIRE asset_throughput upsert from the shared helper and
    21/21 pre-existing tests stayed green — nothing detected it. This test
    exists specifically to close that hole: it fails if either the
    asset_throughput write or the asset.state_change event is removed, for
    BOTH callers.
    """
    executed_sql: list[str] = []
    emitted: list[dict] = []

    class _Cursor:
        def execute(self, sql, params=None):
            executed_sql.append(" ".join(sql.split()))

    class _Conn:
        def commit(self):
            pass

    monkeypatch.setattr(runner, "emit_event", lambda evt: emitted.append(evt))

    # Caller 1: _mark_asset_blocked.
    runner._mark_asset_blocked(_Conn(), _Cursor(), "run-1", "chart-1", "dependent_a", ["upstream_x"])
    assert any("INSERT INTO asset_throughput" in s for s in executed_sql), (
        "_mark_asset_blocked must write asset_throughput (M5 regression guard)"
    )
    assert any(e.get("type") == "asset.state_change" and e.get("asset_id") == "dependent_a" for e in emitted), (
        "_mark_asset_blocked must emit asset.state_change (M5 regression guard)"
    )

    executed_sql.clear()
    emitted.clear()

    # Caller 2: _terminalize_diverged_assets (A3's new caller).
    runner._terminalize_diverged_assets(
        _Conn(), _Cursor(), "run-1", "chart-1",
        {"diverged_b": "per_chart"},
        {"diverged_b": "asset_registry changed after dispatch for frozen asset diverged_b"},
    )
    assert any("INSERT INTO asset_throughput" in s for s in executed_sql), (
        "_terminalize_diverged_assets must write asset_throughput (M5 regression guard)"
    )
    assert any(e.get("type") == "asset.state_change" and e.get("asset_id") == "diverged_b" for e in emitted), (
        "_terminalize_diverged_assets must emit asset.state_change (M5 regression guard)"
    )


def test_hard_fault_after_divergence_detected_still_records_it_f1(monkeypatch):
    """F-1 (rereview 20260926T152022Z) — BLOCKS THE COMMIT.

    Reproduces the rereview's own probe: a genuine registry divergence is
    detected (bg_diverge_target's scope flipped), and THEN a transient,
    non-SystemExit fault occurs inside the pre-claim window — here, at
    claim_runnable_run, one of the three sites the rereview injected at
    (count_other_running_runs / acquire_chart_lock / claim_runnable_run all
    sit in the same unguarded window). Before the fix, the rereview measured:
    divergence detected == ['bg_diverge_target'], terminal writes == [] — the
    record was lost and only `sys.exit(1)` (via main.py's blanket handler)
    remained. This test asserts the record now SURVIVES that fault: the
    exception still propagates (the attempt still fails — F-1 does not change
    that outcome, only whether the divergence gets written), but
    build_run_assets/asset_throughput are written for the diverged asset
    before it does.
    """
    state: dict[str, str] = {a: "queued" for a in PLAN}
    registry_live = dict(REGISTRY_FROZEN)
    registry_live["bg_diverge_target"] = {**REGISTRY_FROZEN["bg_diverge_target"], "scope": "global"}
    ran, throughput, mark_calls, emitted = _install(monkeypatch, state, registry_live)

    class _TransientFault(RuntimeError):
        pass

    def _raise_transient(*_a, **_k):
        raise _TransientFault("simulated transient DB fault at claim_runnable_run")

    # claim_runnable_run is the rereview's third injection site, and the one the
    # gate explicitly names for this test's probe.
    monkeypatch.setattr(runner, "claim_runnable_run", _raise_transient)

    with pytest.raises(_TransientFault):
        runner.execute_run("run-1")

    # The decisive assertions: unlike the pre-fix measurement (writes == []),
    # the diverged asset's terminal state IS now recorded, even though this
    # attempt still raises.
    assert state["bg_diverge_target"] == "error", (
        "F-1: a divergence detected before a hard fault in the pre-claim window "
        "must still be written to build_run_assets, not discarded silently"
    )
    assert throughput.get("bg_diverge_target") == "error", (
        "F-1: asset_throughput must also record the divergence across the fault"
    )
    # No writer for the diverged asset ever ran — it never reached dispatch.
    assert "bg_diverge_target" not in ran


def test_hard_fault_with_no_divergence_pending_writes_nothing_and_still_raises(monkeypatch):
    """Control for F-1: the SAME transient fault, but with an UNCHANGED registry
    (nothing diverged). The except-block must be a no-op — no terminal write for
    any asset — and the original exception must still propagate unchanged. This
    guards against the fix over-firing (e.g. terminalizing assets that never
    diverged, or swallowing the exception instead of re-raising it)."""
    state: dict[str, str] = {a: "queued" for a in PLAN}
    registry_live = dict(REGISTRY_FROZEN)  # identical to the frozen manifest — no divergence
    ran, throughput, mark_calls, emitted = _install(monkeypatch, state, registry_live)

    class _TransientFault(RuntimeError):
        pass

    def _raise_transient(*_a, **_k):
        raise _TransientFault("simulated transient DB fault at claim_runnable_run")

    monkeypatch.setattr(runner, "claim_runnable_run", _raise_transient)

    with pytest.raises(_TransientFault):
        runner.execute_run("run-1")

    assert throughput == {}, "no divergence was pending — the except-block must write nothing"
    assert all(v == "queued" for v in state.values())
    assert ran == []
