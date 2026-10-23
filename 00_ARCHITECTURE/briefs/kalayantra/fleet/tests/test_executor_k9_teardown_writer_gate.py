"""K9 sizing Round A finding N10 (medium, deletion safety; ruling SR-K9-RESONANCE-MAP, N10 part): a teardown must never start while the cancelled rebuild's writer still runs.

After a cancel the run row reads `stopped` about 4 s later while the in-flight writer (a daemon thread of the rebuild's process) keeps running; the process ends 55-84 s after
the cancel. A teardown keyed on `stopped` would delete rows the live writer then re-inserts, and an absence readback taken in that window is no evidence (root CLAUDE.md §N.8: a
signal is computed by a detector that can read false). The executor now admits `orchestrator_rebuild_teardown` (and its dry run) only on (1) no rebuild / cancel of the run-id in
flight, (2) a TERMINAL receipt for each of them that was started, (3) at least one started rebuild, (4) proof of process absence: an ACCEPTED quiescence_check of the rebuild
whose session readback, measured after the rebuild's terminal receipt, sees every role and finds no session carrying the rebuild's PGAPPNAME marker. The database run state is
never consulted. The absence readback of the deletion itself can only come after this, because the teardown cannot start before the gate holds.

One oracle per distinct production claim; each passes on the real executor and FAILS on a copy of executor.py with that ONE claim's line reverted (the planted reversion), as in
test_executor_rebuild_dryrun_detector.py.

  G1 a teardown is refused while the rebuild (or its cancel) of the run-id is still in flight, even though the cancel's own receipt is COMPLETED and the run row reads stopped
  G2 a rebuild with a terminal receipt but a live writer session is refused (the "slow fake writer still running when stopped appears" case), and admitted once a later readback shows none
  G3 a readback measured BEFORE the rebuild's terminal receipt is no evidence (the writer may have been alive then): refused
  G4 a readback that could not see every role's sessions proves nothing: refused
  G5 a run-id with no started rebuild receipt is refused (fail closed: absence of a record is not absence of a writer)
  G6 a cancel with a non-terminal receipt is refused
  G7 the gate is these two kinds' alone: a teardown of another family is untouched
  G8 a readback no reviewer accepted (the post record is not ACCEPTED) is no evidence, whatever its output says
"""
import json

import pytest

import test_executor_mechanical_production as M
from test_executor_table import ALL_CAPS

RUN = "6f1d3c1e-0000-4000-8000-0000000000a1"
REBUILD, CANCEL, READBACK = "op-rebuild", "op-cancel", "op-quiesce"


def archive(w, oid, kind, *, status, args=None, ts=None, folder=None, rc=0):
    """The request `oid` (in done/ or inflight/) and the receipt the executor would have written for it."""
    req = {"operation_id": oid, "kind": kind, "item_id": "K9-23", "idempotency_key": "k-" + oid, "requested_by": "adhikarin", "kyd": "kyd-1", "args": args or {"run-id": RUN}}
    (folder or w.mod.DONE).mkdir(parents=True, exist_ok=True)
    (folder or w.mod.DONE).joinpath(f"{oid}.json").write_text(json.dumps(req))
    record = {"operation_id": oid, "kind": kind, "item_id": "K9-23", "status": status, "reason": "", "exit_code": rc, "ts": ts or M.iso(seconds=-60),
              "request_sha256": w.mod.request_digest(req), "session_marker": w.mod.session_marker(oid)}
    (w.mod.REC / f"{oid}.json").write_text(json.dumps(record))
    return req, record


def readback(w, *, sessions, measured_at=None, sees_all=True, target=REBUILD, oid=READBACK, marker=None, result="ACCEPTED"):
    """An ACCEPTED quiescence_check of `target` whose output is a ky.session_readback/1 line (what quiescence_sessions.sh prints) and its mechanical post-acceptance."""
    req, record = archive(w, oid, "quiescence_check", status="COMPLETED", args={"operation": target}, ts=M.iso(seconds=-10))
    line = json.dumps({"schema": "ky.session_readback/1", "status": "MEASURED", "marker": marker or w.mod.session_marker(target), "database": "db",
                       "sees_all_sessions": sees_all, "sessions": sessions, "measured_at": measured_at or M.iso(seconds=-20)}, sort_keys=True) + "\n"
    (w.mod.REC / f"{oid}.output.txt").write_text(line)
    record.update(output_sha256=M.sha(line))
    (w.mod.REC / f"{oid}.json").write_text(json.dumps(record))
    (w.mod.ACC / f"{oid}.post.json").write_text(json.dumps({"result": result, "by": "v1", "operation_id": oid, "request_sha256": record["request_sha256"]}))


def quiet_writer(w, run=RUN):
    """The precondition of every teardown admission test of another claim: the run's rebuild has a terminal receipt and a later accepted readback shows no live writer session."""
    archive(w, REBUILD, "orchestrator_rebuild", status="COMPLETED", args={"run-id": run})
    readback(w, sessions=[])


LIVE = [{"pid": 4242, "state": "active", "backend_start": "2026-10-21T22:00:00+00:00"}]


def teardown(w, kind="orchestrator_rebuild_teardown", run=RUN):
    return w.accept(w.production_request(kind, operation_id="op-teardown", idempotency_key="k-td", args={"run-id": run}))


def verdict(w, table, run=RUN, kind="orchestrator_rebuild_teardown"):
    return w.mod.validate(teardown(w, kind, run), table, ALL_CAPS)


GATE = "orchestrator_rebuild_teardown_problem"


def oracle_g1_refused_while_the_rebuild_or_its_cancel_is_in_flight(w, table):
    archive(w, REBUILD, "orchestrator_rebuild", status="RUNNING", folder=w.mod.INFLIGHT)
    archive(w, CANCEL, "orchestrator_rebuild_cancel", status="COMPLETED")           # the cancel lane finished at once; the run row reads stopped; the rebuild process still runs
    for kind in ("orchestrator_rebuild_teardown", "orchestrator_rebuild_teardown_dryrun"):
        assert "still in flight" in (verdict(w, table, kind=kind) or ""), kind
    (w.mod.INFLIGHT / f"{REBUILD}.json").unlink()
    (w.mod.INFLIGHT / f"{CANCEL}.json").write_text(json.dumps({"operation_id": CANCEL, "kind": "orchestrator_rebuild_cancel", "args": {"run-id": RUN}}))
    assert "still in flight" in (verdict(w, table) or "")          # a cancel still in flight blocks too


def oracle_g2_a_live_writer_session_refuses_and_a_later_empty_readback_admits(w, table):
    archive(w, REBUILD, "orchestrator_rebuild", status="FAILED", rc=1, ts=M.iso(seconds=-120))
    readback(w, sessions=LIVE, measured_at=M.iso(seconds=-100))
    why = verdict(w, table) or ""
    assert "zero live sessions" in why, why                                   # the writer's session is listed: refused although the rebuild's receipt is terminal
    readback(w, sessions=[], measured_at=M.iso(seconds=-30), oid="op-quiesce-2")      # a later readback: the writer thread has ended
    assert verdict(w, table) is None and verdict(w, table, kind="orchestrator_rebuild_teardown_dryrun") is None


def oracle_g3_a_readback_taken_before_the_rebuild_ended_is_no_evidence(w, table):
    archive(w, REBUILD, "orchestrator_rebuild", status="COMPLETED", ts=M.iso(seconds=-60))
    readback(w, sessions=[], measured_at=M.iso(seconds=-90))                  # empty, but measured 30 s before the rebuild's terminal receipt
    assert "zero live sessions" in (verdict(w, table) or "")
    readback(w, sessions=[], measured_at=M.iso(seconds=-5), oid="op-quiesce-2")
    assert verdict(w, table) is None


def oracle_g4_a_readback_that_could_not_see_every_role_proves_nothing(w, table):
    archive(w, REBUILD, "orchestrator_rebuild", status="COMPLETED")
    readback(w, sessions=[], sees_all=False)
    assert "zero live sessions" in (verdict(w, table) or "")
    readback(w, sessions=[], sees_all=True, oid="op-quiesce-2")
    assert verdict(w, table) is None


def oracle_g5_no_started_rebuild_receipt_for_the_run_is_refused(w, table):
    assert "no started orchestrator_rebuild" in (verdict(w, table) or "")            # nothing recorded at all
    archive(w, REBUILD, "orchestrator_rebuild", status="REFUSED")                    # refused before its child started: nothing ran, nothing to prove absent, nothing to tear down either
    assert "no started orchestrator_rebuild" in (verdict(w, table) or "")
    archive(w, "op-other", "orchestrator_rebuild", status="COMPLETED", args={"run-id": "6f1d3c1e-0000-4000-8000-0000000000a2"})
    readback(w, sessions=[], target="op-other", oid="op-quiesce-other")
    assert "no started orchestrator_rebuild" in (verdict(w, table) or "")            # another run's rebuild and readback bind nothing here


def oracle_g6_a_cancel_without_a_terminal_receipt_is_refused(w, table):
    archive(w, REBUILD, "orchestrator_rebuild", status="COMPLETED")
    readback(w, sessions=[])
    archive(w, CANCEL, "orchestrator_rebuild_cancel", status="RUNNING")
    assert "no terminal receipt" in (verdict(w, table) or "")
    archive(w, CANCEL, "orchestrator_rebuild_cancel", status="COMPLETED")
    assert verdict(w, table) is None


def oracle_g7_the_gate_is_these_kinds_alone(w, table):
    for kind in ("orchestrator_rebuild_cancel", "scheduler_resume", "smalltest_teardown"):
        assert w.mod.orchestrator_rebuild_teardown_problem({"kind": kind, "args": {"run-id": RUN}}) is None, kind


def oracle_g8_an_unaccepted_readback_is_no_evidence(w, table):
    archive(w, REBUILD, "orchestrator_rebuild", status="COMPLETED")
    readback(w, sessions=[], result="REJECTED")                              # empty and fresh, but its acceptance says REJECTED
    assert "zero live sessions" in (verdict(w, table) or "")
    readback(w, sessions=[], oid="op-quiesce-2")
    assert verdict(w, table) is None


ORACLES = {
    # reversion: the gate is not consulted by validate (the teardown is judged as before this change: signed, backed up, dry run)
    "g1": (oracle_g1_refused_while_the_rebuild_or_its_cancel_is_in_flight, ("        lambda: orchestrator_rebuild_teardown_problem(req),\n", "")),
    # reversion: a listed live session no longer blocks (the gate keys on the receipt and ignores the readback's sessions)
    "g2": (oracle_g2_a_live_writer_session_refuses_and_a_later_empty_readback_admits, ('and seen.get("sessions") == [] and utc_time', 'and utc_time')),
    # reversion: the readback's time is not compared with the rebuild's terminal receipt
    "g3": (oracle_g3_a_readback_taken_before_the_rebuild_ended_is_no_evidence, ('>= ended): return None', '>= utc_time("1970-01-01T00:00:00+00:00")): return None')),
    # reversion: sees_all_sessions is not required
    "g4": (oracle_g4_a_readback_that_could_not_see_every_role_proves_nothing, ('and seen.get("sees_all_sessions") is True\n', '\n')),
    # reversion: a run-id with no started rebuild passes
    "g5": (oracle_g5_no_started_rebuild_receipt_for_the_run_is_refused, ('    if not rebuilds: return "no started orchestrator_rebuild of this run-id has a terminal receipt: the run\'s writer is not shown to have ended"\n', '')),
    # reversion: any receipt status counts as terminal
    "g6": (oracle_g6_a_cancel_without_a_terminal_receipt_is_refused, ('if record.get("status") not in RAN_TO_AN_END: return', 'if False: return')),
    # reversion: the kind guard is dropped, so every kind is judged by the gate
    "g7": (oracle_g7_the_gate_is_these_kinds_alone, ('    if req.get("kind") not in ("orchestrator_rebuild_teardown", "orchestrator_rebuild_teardown_dryrun"): return None\n', '')),
    # reversion: a post record that is not ACCEPTED still counts
    "g8": (oracle_g8_an_unaccepted_readback_is_no_evidence, ('accepted.get("result") == "ACCEPTED" and accepted.get("operation_id") == readback_id', 'accepted.get("operation_id") == readback_id')),
}


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_passes_on_the_real_executor(tmp_path, monkeypatch, claim):
    w, table = M.build(tmp_path, monkeypatch)
    ORACLES[claim][0](w, table)


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_fails_on_its_planted_reversion(tmp_path, monkeypatch, claim):
    oracle, mutation = ORACLES[claim]
    w, table = M.build(tmp_path, monkeypatch, mutation)
    with pytest.raises(AssertionError):
        oracle(w, table)
