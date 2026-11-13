"""Orchestrator upstream-success gate (native-approved 2026-06-27).

Proves the runner does not merely walk the plan in DAG ORDER but GATES on success:
when an asset errors, its declared dependents are marked BLOCKED (state='error',
'BLOCKED:' message) and their writers are NOT executed — transitively — instead of
silently building "empty but complete" rows on incomplete upstream data.

Regression for the ka_yojaka → Kāla/Phala/Mīmāṃsā cascade.
"""
import sys
import pathlib
import copy
import json
import re

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
CHART_ID = "22222222-2222-4222-8222-222222222222"


def _frozen_run_fields():
    """Return a valid manifest for scheduler-focused execute_run tests."""
    manifest = {
        "version": "nirmana-run-manifest/v1",
        "chart_id": CHART_ID,
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
                "id": "run-1", "chart_id": CHART_ID, "scope": "global",
                "scope_target": None, "action": "rebuild", "plan": PLAN, "state": "planned",
                **_frozen_run_fields(),
            }]
        elif "FROM asset_registry WHERE asset_id = ANY" in s:
            self._result = list(REGISTRY)
        elif s.startswith("SELECT state FROM build_run_assets"):
            self._result = [{"state": self._state.get(params[1])}]
        elif "UPDATE build_run_assets SET state='error'" in s:
            # _mark_asset_blocked records the blocked asset as error. Packet B1 added
            # two more bound params (disposition, blocked_by_asset_id) ahead of
            # run_id/asset_id in this UPDATE's param tuple — asset_id is the LAST
            # positional param regardless of how many columns the SET clause grows
            # to, so index from the end rather than a fixed absolute position.
            self._state[params[-1]] = "error"
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
    monkeypatch.setattr(runner, "claim_runnable_run", lambda *a, **k: True)
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
        declared_deps, natural_key_partition, has_cowriters, force=False,
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


class _PreflightCursor(FakeCursor):
    """Inert protocol double for the existing one-statement parent/child transition."""
    def __init__(self, db, error_type=None):
        super().__init__({})
        self.db = db
        self.error_type = error_type
        self.statements = []

    def execute(self, sql, params=None):
        normalized = " ".join(sql.split())
        self.statements.append((normalized, params))
        if "FROM build_runs WHERE id" in normalized:
            row = {"id": "run-1", "chart_id": CHART_ID, "scope": "global", "scope_target": None,
                   "action": "rebuild", "plan": PLAN, "state": self.db["state"],
                   "plan_manifest": copy.deepcopy(self.db["manifest"]),
                   "plan_manifest_digest": self.db["digest"]}
            if "AS _preflight_manifest_text" in normalized:
                row["_preflight_manifest_text"] = None if self.db["sql_null"] else json.dumps(self.db["manifest"])
            self._result = [row]
            return
        if "WITH failed_run AS" not in normalized:
            raise AssertionError("unexpected preflight database operation")
        if self.error_type is not None:
            raise self.error_type("synthetic database refusal")
        assert len(params) == normalized.count("%s")
        where = normalized.split("WHERE id=%s", 1)[1].split("RETURNING id", 1)[0]
        if re.search(r"state\s*=\s*'planned'", where):
            accepted = self.db["state"] == "planned"
        else:
            # The current baseline explicitly admits all three states.
            assert "state IN ('planned', 'running', 'paused')" in where
            accepted = self.db["state"] in {"planned", "running", "paused"}
        if "plan_manifest IS NOT DISTINCT FROM %s::jsonb" in where:
            manifest_index = normalized.split("plan_manifest IS NOT DISTINCT FROM", 1)[0].count("%s")
            observed_text = params[manifest_index]
            if observed_text is None:
                same_manifest = self.db["sql_null"]
            else:
                same_manifest = not self.db["sql_null"] and json.loads(observed_text) == self.db["manifest"]
            accepted = accepted and same_manifest
        if "plan_manifest_digest IS NOT DISTINCT FROM %s" in where:
            digest_index = normalized.split("plan_manifest_digest IS NOT DISTINCT FROM", 1)[0].count("%s")
            accepted = accepted and params[digest_index] == self.db["digest"]
        if accepted:
            self.db["state"] = "failed"
            assert "run_id IN (SELECT id FROM failed_run)" in normalized
            assert "AND state='queued'" in normalized
            for name, state in self.db["children"].items():
                if state == "queued":
                    self.db["children"][name] = "aborted"
        self._result = []


class _PreflightConn:
    def __init__(self, db, error_type=None):
        self.cur = _PreflightCursor(db, error_type)
        self.autocommit = False
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return self.cur

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def _preflight_db(state="planned", sql_null=False):
    frozen = _frozen_run_fields()
    return {"state": state, "manifest": frozen["plan_manifest"],
            "digest": frozen["plan_manifest_digest"], "sql_null": sql_null,
            "children": {"A": "queued", "B": "running", "C": "complete"}}


def _install_preflight(monkeypatch, db, *, malformed=False, race=None, error_type=None):
    ran = _install(monkeypatch, {}, set())
    conn = _PreflightConn(db, error_type)
    monkeypatch.setattr(runner, "connect", lambda: conn)
    original_validate = runner.validate_frozen_run_manifest

    def validate(row):
        assert "_preflight_manifest_text" not in row
        if malformed:
            if race is not None:
                race(db)
            raise ValueError("synthetic stored manifest invalid")
        return original_validate(row)

    def wrong_local_code(*args):
        raise ValueError("synthetic local code digest mismatch")

    def forbidden_admission(*args, **kwargs):
        raise AssertionError("preflight refusal must precede writer admission")

    monkeypatch.setattr(runner, "_check_writer_registry_gaps", forbidden_admission)
    monkeypatch.setattr(runner, "claim_runnable_run", forbidden_admission)
    monkeypatch.setattr(runner, "validate_frozen_run_manifest", validate)
    monkeypatch.setattr(runner, "_verify_sidecar_code_matches_manifest", wrong_local_code)
    return conn, ran


@pytest.mark.parametrize("state", ["planned", "running", "paused"])
def test_wrong_local_code_refuses_without_shared_mutation_or_commit(monkeypatch, state):
    db = _preflight_db(state)
    before = copy.deepcopy(db)
    conn, ran = _install_preflight(monkeypatch, db)
    with pytest.raises(SystemExit) as failure:
        runner.execute_run("run-1")
    assert failure.value.code == 1
    assert db == before
    assert not any("WITH failed_run AS" in sql for sql, _ in conn.cur.statements)
    assert conn.commits == 0
    assert conn.closed
    assert ran == []


@pytest.mark.parametrize("replacement", ["running", "paused", "manifest", "digest"])
def test_malformed_manifest_failure_cannot_change_a_replaced_or_claimed_run(monkeypatch, replacement):
    db = _preflight_db()

    def race(row):
        if replacement in {"running", "paused"}:
            row["state"] = replacement
        elif replacement == "manifest":
            row["manifest"] = {"a_different_observed_manifest": True}
        else:
            row["digest"] = "f" * 64

    conn, ran = _install_preflight(monkeypatch, db, malformed=True, race=race)
    with pytest.raises(SystemExit) as failure:
        runner.execute_run("run-1")
    assert failure.value.code == 1
    assert db["state"] == (replacement if replacement in {"running", "paused"} else "planned")
    assert db["children"] == {"A": "queued", "B": "running", "C": "complete"}
    assert conn.closed
    assert ran == []


@pytest.mark.parametrize("started_as_sql_null", [True, False])
def test_null_representation_change_is_a_different_snapshot(monkeypatch, started_as_sql_null):
    db = _preflight_db(sql_null=started_as_sql_null)
    db["manifest"] = None
    db["digest"] = None

    def race(row):
        row["sql_null"] = not started_as_sql_null

    conn, _ = _install_preflight(monkeypatch, db, malformed=True, race=race)
    with pytest.raises(SystemExit):
        runner.execute_run("run-1")
    assert db["state"] == "planned"
    assert db["children"] == {"A": "queued", "B": "running", "C": "complete"}
    assert conn.closed


def test_malformed_unchanged_planned_snapshot_aborts_only_queued_children(monkeypatch):
    db = _preflight_db()
    conn, ran = _install_preflight(monkeypatch, db, malformed=True)
    with pytest.raises(SystemExit) as failure:
        runner.execute_run("run-1")
    assert failure.value.code == 1
    assert db["state"] == "failed"
    assert db["children"] == {"A": "aborted", "B": "running", "C": "complete"}
    assert conn.commits == 1
    assert conn.closed
    assert ran == []


@pytest.mark.parametrize("error_type", [runner.psycopg.errors.InsufficientPrivilege,
                                       runner.psycopg.errors.ForeignKeyViolation])
def test_preflight_write_error_rolls_back_and_closes_without_committing(monkeypatch, error_type):
    db = _preflight_db()
    before = copy.deepcopy(db)
    conn, ran = _install_preflight(monkeypatch, db, malformed=True, error_type=error_type)
    with pytest.raises(error_type):
        runner.execute_run("run-1")
    assert db == before
    assert conn.commits == 0
    assert conn.rollbacks == 1
    assert conn.closed
    assert ran == []


def test_load_run_default_row_shape_does_not_expose_internal_snapshot():
    db = _preflight_db()
    cur = _PreflightCursor(db)
    row = runner.load_run(cur, "run-1")
    assert set(row) == {"id", "chart_id", "scope", "scope_target", "action", "plan", "state",
                        "plan_manifest", "plan_manifest_digest"}
    assert "AS _preflight_manifest_text" not in cur.statements[0][0]
