"""SD-EVENTREG-1 — durable, queryable register for no-op-completion events.

SAMĀPTI lane B-EVENTREG · brief v2.0 §9.6.

The defect being closed (SATYA_DIPA_REPORT_v1_0.md §1, verbatim):

    "The brief's forensic lead instructed querying the `asset.noop_completion` event
     history first, as 'a near-complete register of every time this fired.' **That
     register does not exist as a queryable, durable artifact.** ... A Cloud Logging
     query (`gcloud logging read 'textPayload:"noop_completion"' --freshness=9999d`)
     returned zero results ... Phase A pivoted to independent reconciliation against
     `build_substep_progress` ... as the sole forensic method."

So the tests below are organised around the four properties that make the register
trustworthy rather than merely present:

  1. IT CAPTURES.        Both no-op classes reach the table, with rows_present and
                         substeps_remaining as first-class columns, from the real
                         `_run_data_writer` code path — not from a hand-built event dict.
  2. IT IS BOUNDED.      Non-allowlisted event types (the other ~10 orchestrator event
                         types, several of them per-substep) do NOT reach the table.
  3. IT CANNOT BREAK A BUILD.  A register failure — missing table, permissions, anything
                         — is savepoint-contained: the enclosing build transaction
                         survives, the state write still happens, nothing raises.
  4. IT IS ATOMIC WITH THE DECISION.  The INSERT is issued on the caller's cursor before
                         the asset_throughput state UPDATE, inside the same transaction,
                         so a register row exists iff that state decision committed.

Plus a real-Postgres end-to-end test (opt-in via EVENT_REGISTER_TEST_DSN) that applies
the actual migration file and reads a real emitted event back out of the real table —
the "emit an event and query it back out of the durable store" proof.

The fakes here deliberately mirror tests/test_d16_state_write_defect.py so the two files
exercise the same code path the same way.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import asset_runner as ar  # noqa: E402
from pipeline.orchestrator import events as ev  # noqa: E402
from pipeline.orchestrator.writers import SubStep, WriterBase, WriterResult  # noqa: E402


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
MIGRATION = (REPO_ROOT / "platform" / "supabase" / "migrations"
             / "XXX_PLACEHOLDER_orchestrator_event_register.sql")

COUNT_SQL = "SELECT count(*) FROM kala_convergence WHERE chart_id = $1"


# ── Fakes (mirrors test_d16_state_write_defect.py) ────────────────────────────

class FakeCursor:
    """Scriptable cursor: answers registry/count queries; records everything.

    `insert_fails=True` makes the register INSERT raise, to exercise the savepoint
    containment path. `savepoint_fails=True` makes even SAVEPOINT raise.
    """

    def __init__(self, rows_present=None, count_sql=COUNT_SQL, target_floor=None,
                 rowcount: int = 1, has_substeps=None,
                 insert_fails: bool = False, savepoint_fails: bool = False):
        self.executed: list[tuple[str, object]] = []
        self._rows_present = rows_present
        self._count_sql = count_sql
        self._target_floor = target_floor
        self._has_substeps = has_substeps
        self.rowcount = rowcount
        self._next_fetch = None
        self._insert_fails = insert_fails
        self._savepoint_fails = savepoint_fails

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if self._savepoint_fails and s.startswith("SAVEPOINT orchestrator_event_register"):
            raise RuntimeError("savepoint refused (simulated)")
        if self._insert_fails and "INSERT INTO orchestrator_event_register" in s:
            self.executed.append((sql, params))
            raise RuntimeError('relation "orchestrator_event_register" does not exist')
        self.executed.append((sql, params))
        self._next_fetch = None
        if "SELECT count_sql FROM asset_registry" in s:
            self._next_fetch = {"count_sql": self._count_sql}
        elif "SELECT target_floor FROM asset_registry" in s:
            self._next_fetch = {"target_floor": self._target_floor}
        elif "SELECT has_substeps FROM asset_registry" in s:
            self._next_fetch = {"has_substeps": self._has_substeps}
        elif self._count_sql and s.startswith(
                self._count_sql.replace("$1", "%s").split(" WHERE")[0]):
            self._next_fetch = {"count": self._rows_present}

    def fetchone(self):
        return self._next_fetch

    def fetchall(self):
        return []

    def sqls_containing(self, keyword: str) -> list[str]:
        return [s for s, _ in self.executed if keyword in s]

    def register_inserts(self) -> list[tuple]:
        return [p for s, p in self.executed
                if "INSERT INTO orchestrator_event_register" in s]

    def index_of(self, keyword: str) -> int:
        for i, (s, _) in enumerate(self.executed):
            if keyword in s:
                return i
        return -1


class FakeConn:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


class _ResumeSkipAllWriter(WriterBase):
    """ka_sangam shape: resumption ledger says every substep is already committed."""
    asset_id = "_test_eventreg_resume_skip_all"

    def plan_substeps(self, ctx):
        return []

    def run(self, ctx):  # pragma: no cover — never reached with an empty plan
        return WriterResult(asset_id=self.asset_id, rows_inserted=0, rows_updated=0)


class _PartialPlanWriter(WriterBase):
    """ka_gochara_sweep shape: rows present, but substeps genuinely remain."""
    asset_id = "_test_eventreg_partial_plan"

    def plan_substeps(self, ctx):
        return [SubStep(key="year:79", label="year 79"),
                SubStep(key="year:80", label="year 80")]

    def run_substep(self, ctx, step):
        return WriterResult(asset_id=self.asset_id, rows_inserted=0, rows_updated=0)


def _patch_common(monkeypatch, writer_cls):
    """Same as test_d16's helper, but WITHOUT stubbing emit_event — this suite is
    testing emit_event's own persistence behaviour, so the real one must run."""
    monkeypatch.setattr(ar, "discover_all", lambda: None)
    monkeypatch.setattr(ar, "get_writer", lambda aid: writer_cls)
    monkeypatch.setattr(ar, "fetch_birth_params", lambda conn, cid: {"chart_id": cid})
    monkeypatch.setattr(ar, "compute_upstream_hash", lambda cur, aid, cid: "hash-upstream")
    monkeypatch.setattr(ar, "get_writer_git_hash", lambda aid: "hash-writer")
    monkeypatch.setattr(ar, "compute_downstream_closure", lambda cur, aid: [])
    # Keep Pub/Sub out of the unit path; the stdout branch is the pre-existing default.
    monkeypatch.delenv("PUBSUB_TOPIC", raising=False)
    monkeypatch.delenv("ORCHESTRATOR_DURABLE_EVENT_TYPES", raising=False)


def _final_state(cur: FakeCursor):
    params = [p for s, p in cur.executed if "SET state = %s" in s]
    return params[-1][0] if params else None


# ── 1. IT CAPTURES — through the real _run_data_writer path ───────────────────

def test_noop_completion_is_persisted_to_the_register(monkeypatch):
    """The event SATYA-DĪPA could not query now lands in a durable table."""
    _patch_common(monkeypatch, _ResumeSkipAllWriter)
    conn, cur = FakeConn(), FakeCursor(rows_present=2488, has_substeps=True)
    ar._run_data_writer(conn, cur, "run-71b260c7", "chart-482012f1",
                        _ResumeSkipAllWriter.asset_id)

    assert _final_state(cur) == "lit", "precondition: this is the promote-to-lit path"
    inserts = cur.register_inserts()
    assert len(inserts) == 1, (
        "SD-EVENTREG-1: asset.noop_completion must be persisted to "
        "orchestrator_event_register, got %d insert(s)" % len(inserts)
    )
    (event_type, chart_id, asset_id, run_id,
     rows_present, substeps_remaining, emitted_by, payload) = inserts[0]
    assert event_type == "asset.noop_completion"
    assert chart_id == "chart-482012f1"
    assert asset_id == _ResumeSkipAllWriter.asset_id
    assert run_id == "run-71b260c7"
    assert rows_present == 2488, "rows_present must be a first-class column, per §9.6"
    assert substeps_remaining is None, "nothing remained — that is what 'completion' means"
    assert emitted_by, "emitter identity must be recorded (Cloud Run vs local ambiguity)"
    assert json.loads(payload)["type"] == "asset.noop_completion", (
        "the verbatim event must be retained so the column projection loses nothing"
    )


def test_noop_completion_rejected_is_persisted_with_substeps_remaining(monkeypatch):
    """The rejected class carries the number the brief names: substeps_remaining."""
    _patch_common(monkeypatch, _PartialPlanWriter)
    conn, cur = FakeConn(), FakeCursor(rows_present=1267, has_substeps=True)
    ar._run_data_writer(conn, cur, "run-partial", "chart-1c826d5a",
                        _PartialPlanWriter.asset_id)

    assert _final_state(cur) == "incomplete", "precondition: this is the rejection path"
    inserts = cur.register_inserts()
    assert len(inserts) == 1, (
        "SD-EVENTREG-1: asset.noop_completion_rejected must be persisted too — the brief "
        "requires BOTH classes"
    )
    (event_type, chart_id, asset_id, run_id,
     rows_present, substeps_remaining, _emitted_by, payload) = inserts[0]
    assert event_type == "asset.noop_completion_rejected"
    assert chart_id == "chart-1c826d5a"
    assert rows_present == 1267
    assert substeps_remaining == 2, (
        "substeps_remaining must be a first-class column and must match the writer's "
        "own plan_substeps() count, got %r" % (substeps_remaining,)
    )
    assert json.loads(payload)["substeps_remaining"] == 2


# ── 2. IT IS BOUNDED — allowlist, not firehose ────────────────────────────────

def test_non_allowlisted_event_types_are_not_persisted(monkeypatch):
    """asset.substep/asset.progress fire per substep. Persisting them would make a
    firehose, not a register."""
    monkeypatch.delenv("ORCHESTRATOR_DURABLE_EVENT_TYPES", raising=False)
    cur = FakeCursor()
    for t in ("asset.state_change", "asset.substep", "asset.progress",
              "asset.dep_assert", "run.state_change", "asset.state_write_anomaly"):
        assert ev.persist_event(cur, {"type": t, "asset_id": "x"}) is False, t
    assert cur.register_inserts() == []


def test_allowlist_is_env_overridable_for_incident_response(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_DURABLE_EVENT_TYPES",
                       "asset.dep_assert_anomaly, asset.noop_completion")
    cur = FakeCursor()
    assert ev.persist_event(cur, {"type": "asset.dep_assert_anomaly"}) is True
    assert ev.persist_event(cur, {"type": "asset.noop_completion"}) is True
    assert ev.persist_event(cur, {"type": "asset.noop_completion_rejected"}) is False


def test_empty_allowlist_disables_persistence(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_DURABLE_EVENT_TYPES", "")
    cur = FakeCursor()
    assert ev.persist_event(cur, {"type": "asset.noop_completion"}) is False
    assert cur.register_inserts() == []


# ── 3. IT CANNOT BREAK A BUILD ────────────────────────────────────────────────

def test_register_insert_failure_is_savepoint_contained(monkeypatch):
    """Table missing (migration not yet applied) must not abort the build txn."""
    monkeypatch.delenv("ORCHESTRATOR_DURABLE_EVENT_TYPES", raising=False)
    cur = FakeCursor(insert_fails=True)
    assert ev.persist_event(cur, {"type": "asset.noop_completion",
                                  "asset_id": "a", "rows_present": 1}) is False
    sqls = [" ".join(s.split()) for s, _ in cur.executed]
    assert any(s.startswith("SAVEPOINT orchestrator_event_register") for s in sqls)
    assert any(s.startswith("ROLLBACK TO SAVEPOINT orchestrator_event_register")
               for s in sqls), (
        "a failed register INSERT must be rolled back to a savepoint, or the caller's "
        "transaction is left aborted and the BUILD fails because its audit trail failed"
    )


def test_build_still_completes_when_the_register_table_is_missing(monkeypatch):
    """End-to-end version of the above: the state decision must be unaffected."""
    _patch_common(monkeypatch, _ResumeSkipAllWriter)
    conn, cur = FakeConn(), FakeCursor(rows_present=2488, has_substeps=True,
                                       insert_fails=True)
    ar._run_data_writer(conn, cur, "run-nomigration", "chart-482012f1",
                        _ResumeSkipAllWriter.asset_id)
    assert _final_state(cur) == "lit", (
        "the no-op-completion promotion must be identical whether or not the register "
        "table exists — the register observes builds, it does not gate them"
    )
    assert conn.commits >= 1


def test_savepoint_refusal_skips_the_insert_entirely(monkeypatch):
    """If we cannot open a savepoint we cannot guarantee recovery, so we must not try
    the insert at all."""
    monkeypatch.delenv("ORCHESTRATOR_DURABLE_EVENT_TYPES", raising=False)
    cur = FakeCursor(savepoint_fails=True)
    assert ev.persist_event(cur, {"type": "asset.noop_completion"}) is False
    assert cur.register_inserts() == []


def test_persist_event_with_no_cursor_is_a_noop(monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_DURABLE_EVENT_TYPES", raising=False)
    assert ev.persist_event(None, {"type": "asset.noop_completion"}) is False


def test_emit_event_without_cursor_still_works_and_warns(monkeypatch, capsys, caplog):
    """Backward compatibility: the cur= parameter is purely additive. A durable-class
    event with no cursor must still emit AND must say loudly that it was not
    persisted — an invisible gap is exactly what SD-EVENTREG-1 exists to end."""
    monkeypatch.delenv("PUBSUB_TOPIC", raising=False)
    monkeypatch.delenv("ORCHESTRATOR_DURABLE_EVENT_TYPES", raising=False)
    with caplog.at_level("WARNING"):
        ev.emit_event({"type": "asset.noop_completion", "asset_id": "a"})
    assert "[event]" in capsys.readouterr().out
    assert any("WITHOUT a cursor" in r.getMessage() for r in caplog.records)


def test_emit_event_non_durable_type_without_cursor_does_not_warn(monkeypatch, caplog):
    monkeypatch.delenv("PUBSUB_TOPIC", raising=False)
    monkeypatch.delenv("ORCHESTRATOR_DURABLE_EVENT_TYPES", raising=False)
    with caplog.at_level("WARNING"):
        ev.emit_event({"type": "asset.substep", "asset_id": "a"})
    assert not [r for r in caplog.records if "event-register" in r.getMessage()]


def test_uuid_and_odd_values_do_not_lose_the_row(monkeypatch):
    """An audit sink's one job is to never drop an event. UUID ids serialise; a
    non-numeric rows_present degrades to NULL rather than raising."""
    import uuid as _uuid
    monkeypatch.delenv("ORCHESTRATOR_DURABLE_EVENT_TYPES", raising=False)
    cid = _uuid.UUID("482012f1-710e-4a25-994a-93821f5871aa")
    cur = FakeCursor()
    assert ev.persist_event(cur, {"type": "asset.noop_completion", "chart_id": cid,
                                  "rows_present": "not-a-number"}) is True
    (_t, chart_id, _a, _r, rows_present, _s, _e, payload) = cur.register_inserts()[0]
    assert chart_id == str(cid)
    assert rows_present is None
    assert json.loads(payload)["chart_id"] == str(cid)


# ── 4. IT IS ATOMIC WITH THE DECISION ─────────────────────────────────────────

def test_register_write_precedes_the_state_update_in_the_same_transaction(monkeypatch):
    """The register INSERT must be issued on the orchestrator's own cursor BEFORE the
    asset_throughput UPDATE and before conn.commit() — so the register row commits iff
    the state decision commits. A register that could outlive a rolled-back decision
    would report promotions that never happened."""
    _patch_common(monkeypatch, _ResumeSkipAllWriter)
    conn, cur = FakeConn(), FakeCursor(rows_present=2488, has_substeps=True)
    ar._run_data_writer(conn, cur, "run-atomic", "chart-482012f1",
                        _ResumeSkipAllWriter.asset_id)
    i_insert = cur.index_of("INSERT INTO orchestrator_event_register")
    i_state = cur.index_of("UPDATE asset_throughput")
    assert i_insert >= 0 and i_state >= 0
    assert i_insert < i_state, (
        "register INSERT (idx %d) must precede the state UPDATE (idx %d) on the same "
        "cursor" % (i_insert, i_state)
    )
    assert conn.commits >= 1, "and both are then committed together"


# ── 5. REAL POSTGRES — emit an event, query it back out ───────────────────────

_DSN = os.environ.get("EVENT_REGISTER_TEST_DSN")


@pytest.mark.skipif(not _DSN, reason="set EVENT_REGISTER_TEST_DSN to a throwaway "
                                     "Postgres to run the end-to-end register proof")
def test_end_to_end_against_real_postgres():
    """The SD-EVENTREG-1 acceptance proof, against a real server:

      apply the real migration file  ->  run the REAL emit_event() path  ->  commit  ->
      RECONNECT  ->  SELECT the row back out of orchestrator_noop_events.

    The reconnect is the point. Reading back on the same connection would only prove
    the INSERT executed; reading back on a NEW connection after COMMIT is what proves
    the event is durable — the exact property stdout and fire-and-forget Pub/Sub lack.
    """
    import psycopg
    import psycopg.rows

    ddl = MIGRATION.read_text()
    assert "CREATE TABLE IF NOT EXISTS orchestrator_event_register" in ddl

    with psycopg.connect(_DSN, autocommit=True) as setup:
        setup.execute("DROP VIEW IF EXISTS orchestrator_noop_events")
        setup.execute("DROP TABLE IF EXISTS orchestrator_event_register")
    with psycopg.connect(_DSN) as setup:
        setup.execute(ddl.replace("BEGIN;", "").replace("COMMIT;", ""))
        setup.commit()

    run_id = "e2e-" + os.urandom(4).hex()

    # Write path: the real emit_event, on a real cursor, then a real COMMIT.
    with psycopg.connect(_DSN, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            ev.emit_event({
                "type": "asset.noop_completion",
                "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
                "asset_id": "ka_sangam",
                "run_id": run_id,
                "rows_present": 2488,
            }, cur=cur)
            ev.emit_event({
                "type": "asset.noop_completion_rejected",
                "chart_id": "1c826d5a-0000-0000-0000-000000000000",
                "asset_id": "ka_gochara_sweep",
                "run_id": run_id,
                "rows_present": 78,
                "substeps_remaining": 225,
            }, cur=cur)
            # A non-allowlisted type must NOT land.
            ev.emit_event({"type": "asset.substep", "asset_id": "ka_sangam",
                           "run_id": run_id}, cur=cur)
        conn.commit()

    # Read path: a BRAND NEW connection. This is the durability proof.
    with psycopg.connect(_DSN, row_factory=psycopg.rows.dict_row) as conn2:
        rows = conn2.execute(
            "SELECT verdict, asset_id, rows_present, substeps_remaining, emitted_by "
            "FROM orchestrator_noop_events WHERE run_id = %s ORDER BY id",
            (run_id,),
        ).fetchall()
        total = conn2.execute(
            "SELECT count(*) AS n FROM orchestrator_event_register WHERE run_id = %s",
            (run_id,),
        ).fetchone()["n"]

    assert total == 2, "exactly the two allowlisted events, not the substep event"
    assert rows[0]["verdict"] == "promoted_to_lit"
    assert rows[0]["asset_id"] == "ka_sangam"
    assert rows[0]["rows_present"] == 2488
    assert rows[0]["substeps_remaining"] == 0
    assert rows[1]["verdict"] == "held_incomplete"
    assert rows[1]["asset_id"] == "ka_gochara_sweep"
    assert rows[1]["rows_present"] == 78
    assert rows[1]["substeps_remaining"] == 225
    assert rows[0]["emitted_by"]
