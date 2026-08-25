"""Orchestrator upstream-success gate (native-approved 2026-06-27).

Proves the runner does not merely walk the plan in DAG ORDER but GATES on success:
when an asset errors, its declared dependents are marked BLOCKED (state='error',
'BLOCKED:' message) and their writers are NOT executed — transitively — instead of
silently building "empty but complete" rows on incomplete upstream data.

Regression for the ka_yojaka → Kāla/Phala/Mīmāṃsā cascade.
"""
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import runner  # noqa: E402


# Plan: A → B → C (B depends on A; C depends on B), plus an independent D.
REGISTRY = [
    {"asset_id": "A", "scope": "per_chart", "depends_on": []},
    {"asset_id": "B", "scope": "per_chart", "depends_on": ["A"]},
    {"asset_id": "C", "scope": "per_chart", "depends_on": ["B"]},
    {"asset_id": "D", "scope": "per_chart", "depends_on": []},
]
PLAN = ["A", "B", "C", "D"]


def _frozen_run_fields():
    """Return a valid manifest for scheduler-focused execute_run tests."""
    manifest = {
        "version": "nirmana-run-manifest/v1",
        "chart_id": "chart-C",
        "scope": "global",
        "scope_target": None,
        "action": "rebuild",
        "waves": [PLAN],
        "assets": [
            {
                "asset_id": row["asset_id"],
                "scope": row["scope"],
                "depends_on": row["depends_on"],
                "natural_key_partition": None,
                "has_cowriters": False,
                "expected_code_digest": "0" * 64,
            }
            for row in REGISTRY
        ],
    }
    return {
        "plan_manifest": manifest,
        "plan_manifest_digest": runner._canonical_manifest_digest(manifest),
    }


class FakeCursor:
    """Minimal cursor that answers exactly the queries execute_run issues."""
    def __init__(self, state: dict):
        self._state = state          # shared asset_id -> build_run_assets.state
        self._result = None

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "count(*) AS active" in s:
            self._result = [{"active": 0}]
        elif "FROM build_runs WHERE id" in s:
            self._result = [{
                "id": "run-1", "chart_id": "chart-C", "scope": "global",
                "scope_target": None, "action": "rebuild", "plan": PLAN, "state": "planned",
                **_frozen_run_fields(),
            }]
        elif "FROM asset_registry WHERE asset_id = ANY" in s:
            self._result = list(REGISTRY)
        elif s.startswith("SELECT state FROM build_run_assets"):
            self._result = [{"state": self._state.get(params[1])}]
        elif "UPDATE build_run_assets SET state='error'" in s:
            # _mark_asset_blocked records the blocked asset as error
            self._state[params[2]] = "error"
            self._result = []
        else:
            # INSERT asset_throughput / other writes — ignore
            self._result = []

    def fetchone(self):
        return self._result[0] if self._result else None

    def fetchall(self):
        return list(self._result or [])


class FakeConn:
    def __init__(self, state):
        self._state = state
        self.autocommit = False
    def cursor(self):
        return FakeCursor(self._state)
    def commit(self):
        pass
    def rollback(self):
        pass
    def close(self):
        pass


def _install(monkeypatch, state, fail_assets):
    """Patch execute_run's collaborators; run_asset marks fail_assets as error."""
    monkeypatch.setattr(runner, "connect", lambda: FakeConn(state))
    monkeypatch.setattr(runner, "acquire_chart_lock", lambda *a, **k: True)
    monkeypatch.setattr(runner, "release_chart_lock", lambda *a, **k: None)
    monkeypatch.setattr(runner, "check_signals", lambda *a, **k: None)
    monkeypatch.setattr(runner, "is_asset_complete", lambda *a, **k: False)
    monkeypatch.setattr(runner, "claim_planned_run", lambda *a, **k: True)
    monkeypatch.setattr(runner, "mark_run_state", lambda *a, **k: None)
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    # Manifest integrity itself has dedicated tests. These scheduler tests use
    # synthetic asset IDs, so isolate them from live registry/code parity.
    monkeypatch.setattr(runner, "_verify_registry_still_matches_manifest", lambda *a, **k: None)
    monkeypatch.setattr(runner, "_verify_sidecar_code_matches_manifest", lambda *a, **k: None)
    import pipeline.orchestrator.writers as writers_mod
    monkeypatch.setattr(writers_mod, "discover_all", lambda: None, raising=False)
    # Patch out the writer-gap guard: this test focuses on DAG blocking behaviour,
    # not writer-registry completeness. The guard queries asset_registry for
    # has_writer, which the 4-row fake DB does not provide.
    monkeypatch.setattr(runner, "_check_writer_registry_gaps", lambda cur: [], raising=False)

    ran: list[str] = []

    def fake_run_asset(
        conn, cur, run_id, chart_id, asset_id, position, *,
        declared_deps, natural_key_partition, has_cowriters,
    ):
        assert declared_deps == next(row["depends_on"] for row in REGISTRY if row["asset_id"] == asset_id)
        assert natural_key_partition is None
        assert has_cowriters is False
        ran.append(asset_id)
        cur.execute(
            "UPDATE build_run_assets SET state=%s WHERE run_id=%s AND asset_id=%s",
            ("error" if asset_id in fail_assets else "complete", run_id, asset_id),
        )
        # reflect into shared state directly (the UPDATE above isn't the blocked-path one)
        state[asset_id] = "error" if asset_id in fail_assets else "complete"

    import pipeline.orchestrator.asset_runner as ar
    monkeypatch.setattr(ar, "run_asset", fake_run_asset)
    return ran


def test_upstream_failure_blocks_transitive_dependents(monkeypatch):
    state: dict[str, str] = {}
    ran = _install(monkeypatch, state, fail_assets={"A"})

    runner.execute_run("run-1")

    # A ran and errored; D is independent and ran. B and C must NOT have run (blocked).
    assert "A" in ran
    assert "D" in ran
    assert "B" not in ran, "B depends on failed A — must be blocked, not run"
    assert "C" not in ran, "C depends on (blocked) B — must be transitively blocked"
    # Blocked assets are surfaced as error, not silently complete.
    assert state["B"] == "error"
    assert state["C"] == "error"
    assert state["D"] == "complete"


def test_no_failure_runs_everything(monkeypatch):
    state: dict[str, str] = {}
    ran = _install(monkeypatch, state, fail_assets=set())

    runner.execute_run("run-1")

    # Under the wave-parallel scheduler the order is a valid TOPOLOGICAL order, not a
    # fixed sequence (D is independent and may run alongside A). Assert the invariant:
    # everything ran exactly once, completed, and each dep preceded its dependent.
    assert set(ran) == set(PLAN) and len(ran) == len(PLAN)
    assert ran.index("A") < ran.index("B") < ran.index("C")  # A → B → C chain order
    assert all(state[a] == "complete" for a in PLAN)
