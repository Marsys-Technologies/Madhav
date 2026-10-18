"""SR-J3-CANCEL-NULL 2(a) (J-3c): governed `measuring_cancel` — cancel ONE running Cloud Run execution of the measuring build.

One doctrine-grounded oracle per distinct production claim; every cloud call is a stateful in-process fake (no gcloud, no network, no database, no git write).
Sources of the expected values: the ruling SR-J3-CANCEL-NULL (DECISIONS_SURROGATE.jsonl: "refuses unless target == execution named in the J-3c dispatch receipt AND
an ABORT/stall verdict file cited by digest; one signer; readback CANCELLED; add run.executions.cancel to the testIamPermissions readback"), the Cloud Run v1
Execution resource (`status.cancelledCount` / `runningCount` / the `Completed` condition, as cloudrun_readback.py reads them) and the `gcloud run jobs executions
cancel` verb, and executor.py's own admission rules (A8 §3.8-§3.11). Distinct claims:
M1 target == the execution named in the dispatch receipt · M2 the receipt and the verdict are cited by sha256 and must match byte for byte ·
M3 only an ABORT / stall verdict cancels (CONTINUE, NULL refuse) · M4 the state read back after the cancel is recorded · M5 a non-CANCELLED observed state is
a FAILED receipt, never success · M6 the IAM readback lists run.executions.cancel · M7 the cancel is never held by the production fence ·
M8 one signer: a lease, a verifier acceptance and the dry-run attestation · M9 the receipt binds operation, request and execution ·
M10 the dry run admits the same bindings and makes no cloud call.
"""
import hashlib
import io
import json
import subprocess
import threading

import pytest

from test_executor_scheduler_reaper import (ALL_CAPS, COMMIT, FLEET, LEASE, TABLE, FakeCloud, Forbidden, World, load, reaper, run_main_one_turn,
                                            stamp, utc_now)
import datetime as dt

cancel = load(FLEET / "measuring_cancel.py", "measuring_cancel_under_test")
EXEC = "brahma-build-pipeline-job-abc12"
OTHER = "brahma-build-pipeline-job-zzz99"
DISPATCH_OP = "op-measuring-dispatch-1"
ABORT = {"schema": "ky.reproject_verdict/1", "verdict": "ABORT"}


def resource(state, name=EXEC):
    status = {"RUNNING": {"conditions": [{"type": "Completed", "status": "Unknown"}], "runningCount": 1},
              "CANCELLED": {"conditions": [{"type": "Completed", "status": "False"}], "cancelledCount": 1},
              "SUCCEEDED": {"conditions": [{"type": "Completed", "status": "True"}], "succeededCount": 1},
              "FAILED": {"conditions": [{"type": "Completed", "status": "False"}], "failedCount": 1}}[state]
    return {"metadata": {"name": name, "labels": {"run.googleapis.com/job": "brahma-build-pipeline-job"}}, "spec": {"taskCount": 1}, "status": status}


class FakeRun:
    """A stateful `gcloud run jobs executions` stand-in. `effect='nothing'` makes the cancel exit 0 yet change nothing (the exit status is a lie);
    otherwise the execution reads CANCELLED from the `lag`-th describe after the cancel (cancel is asynchronous)."""

    def __init__(self, state="RUNNING", effect="cancelled", lag=2, name=EXEC):
        self.state, self.effect, self.lag, self.name, self.calls, self.pending = state, effect, lag, name, [], None

    def __call__(self, argv):
        self.calls.append(list(argv))
        done = lambda out="", rc=0: subprocess.CompletedProcess(argv, rc, out, "")
        assert argv[:5] in (["gcloud", "run", "jobs", "executions", "describe"], ["gcloud", "run", "jobs", "executions", "cancel"]), argv
        assert argv[5] == self.name and "--project=madhav-astrology" in argv and "--region=asia-south1" in argv, argv
        if argv[4] == "cancel":
            if self.effect == "cancelled": self.pending = self.lag
            return done()
        if self.pending is not None:
            self.pending -= 1
            if self.pending <= 0: self.state, self.pending = "CANCELLED", None
        return done(json.dumps(resource(self.state, self.name)))

    def verbs(self):
        return [c[4] for c in self.calls]


class CancelWorld(World):
    def __init__(self, tmp_path, monkeypatch, run_cloud=None):
        super().__init__(tmp_path, monkeypatch, name="ky_exec_cancel")
        self.run_cloud = run_cloud or FakeRun()
        (self.mod.OPS / "verdicts").mkdir(parents=True, exist_ok=True)

    def execute(self, req, op):
        args = list(op.get("fixed_args", []))                                                # what the real execute() builds
        for k, v in (req.get("args") or {}).items(): args += [f"--{k}", str(v)]
        out = io.StringIO()
        rc = cancel.main(args, environ={"KY_OPERATION_REQUEST": json.dumps(req, sort_keys=True, separators=(",", ":"))}, runner=self.run_cloud, sleep=lambda s: None, out=out)
        return rc, out.getvalue()

    def cite(self, folder, name, document):
        body = json.dumps(document, indent=1).encode()
        (self.mod.OPS / folder / name).write_bytes(body)
        return {"name": name, "sha256": hashlib.sha256(body).hexdigest()}

    def dispatch_ref(self, execution=EXEC, **overrides):
        receipt = {"operation_id": DISPATCH_OP, "kind": "measuring_dispatch", "item_id": "J-3c", "status": "COMPLETED", "exit_code": 0,
                   "launch": {"schema": "ky.measuring_launch/1", "status": "LAUNCHED", "execution_name": execution}}
        receipt.update(overrides)
        return self.cite("receipts", f"{DISPATCH_OP}.json", receipt)

    def verdict_ref(self, document=ABORT, name="verdict-1.json"):
        return self.cite("verdicts", name, document)

    def cancel_request(self, target=EXEC, dispatch=None, verdict=None, oid="op-cancel-1", checks=None, signed=True):
        req = {"operation_id": oid, "idempotency_key": oid, "item_id": "J-3c", "kind": "measuring_cancel", "requested_by": "adhikarin", "kyd": "KYD-FIXTURE",
               "args": {"execution": target}, "reviewed_commit": COMMIT, "expires_at": (utc_now() + dt.timedelta(hours=1)).isoformat(),
               "chart_id": self.mod.CANONICAL_CHART, "lease_id": LEASE, "dispatch_receipt": self.dispatch_ref() if dispatch is None else dispatch, "verdict": self.verdict_ref() if verdict is None else verdict}
        acceptance = self.mod.ACC / f"{oid}.json"
        req["acceptance_receipt"] = str(acceptance)
        if signed:
            acceptance.write_text(json.dumps({"result": "ACCEPTED", "by": "v1", "operation_id": oid, "reviewed_commit": COMMIT, "ts": self.mod.now(),
                                              "request_sha256": self.mod.request_digest(req), "checks": checks if checks is not None else {"dry_run_passed": True}}))
        return req


@pytest.fixture
def world(tmp_path, monkeypatch):
    return CancelWorld(tmp_path, monkeypatch)


# ───────────────────────────── M1 the target is the execution the dispatch receipt named ─────────────────────────────
def test_m1_a_target_other_than_the_dispatched_execution_is_refused_and_nothing_is_called(world):
    req = world.cancel_request(target=OTHER)
    assert "not the execution named in the cited measuring_dispatch receipt" in world.validate(req)
    world.run_cloud.name = OTHER
    receipt = world.run(req)
    assert receipt["status"] == "REFUSED" and world.run_cloud.calls == []
    assert world.validate(world.cancel_request()) is None                                    # positive control: the named execution is admitted


def test_m1_the_script_refuses_a_name_that_is_not_a_pipeline_execution_before_any_call():
    out = io.StringIO()
    rc = cancel.main(["--execution", "brahma-build-pipeline-job"], environ={}, runner=Forbidden(), sleep=Forbidden(), out=out)
    record = json.loads(out.getvalue())
    assert rc == 1 and record["status"] == "REFUSED" and record["gcloud_calls"] == 0 and record["execution"] is None


# ───────────────────────────── M2 receipt and verdict are cited by sha256 and must match ─────────────────────────────
def test_m2_a_dispatch_receipt_that_changed_after_it_was_cited_is_refused(world):
    req = world.cancel_request()
    world.dispatch_ref(execution=OTHER)                                                      # same file name, different bytes than the cited sha256
    assert "does not match its sha256" in world.validate(req)


@pytest.mark.parametrize("bad", [{"kind": "smalltest_dispatch"}, {"status": "FAILED"}, {"exit_code": 1}, {"launch": {"status": "STAGED"}}])
def test_m2_only_the_completed_launch_of_a_measuring_dispatch_binds_the_target(world, bad):
    req = world.cancel_request(dispatch=world.dispatch_ref(**bad))
    assert world.validate(req) is not None


def test_m2_a_missing_or_mismatched_verdict_digest_is_refused(world):
    ref = world.verdict_ref()
    assert world.validate(world.cancel_request(verdict=ref)) is None                          # positive control
    assert "verdict file is missing" in world.validate(world.cancel_request(verdict={"name": "no-such.json", "sha256": ref["sha256"]}))
    assert "does not match its sha256" in world.validate(world.cancel_request(verdict=dict(ref, sha256="0" * 64)))
    assert "verdict file is missing" in world.validate(world.cancel_request(verdict={"name": "../receipts/" + f"{DISPATCH_OP}.json", "sha256": ref["sha256"]}))
    assert "verdict file is missing" in world.validate(world.cancel_request(verdict={}))


# ───────────────────────────── M3 only an ABORT / stall verdict cancels ─────────────────────────────
@pytest.mark.parametrize("document,admitted", [
    ({"schema": "ky.reproject_verdict/1", "verdict": "ABORT"}, True),
    ({"schema": "ky.stall_verdict/1", "verdict": "STALL"}, True),
    ({"schema": "ky.reproject_verdict/1", "verdict": "CONTINUE"}, False),
    ({"schema": "ky.reproject_verdict/1", "verdict": None}, False),
    ({"schema": "ky.reproject_verdict/1"}, False),
    ({"schema": "ky.reproject_verdict/1", "verdict": "STALL"}, False),
    ({"schema": "ky.stall_verdict/1", "verdict": "CONTINUE"}, False),
    ({"schema": "ky.other_verdict/1", "verdict": "ABORT"}, False),
])
def test_m3_only_abort_or_stall_cancels_continue_and_null_never(world, document, admitted):
    problem = world.validate(world.cancel_request(verdict=world.verdict_ref(document)))
    assert (problem is None) is admitted, problem
    if not admitted: assert "not an ABORT or stall verdict" in problem


# ───────────────────────────── M4 the state read back after the cancel is recorded ─────────────────────────────
def test_m4_the_receipt_records_the_state_read_back_after_the_cancel(world):
    receipt = world.run(world.cancel_request())
    assert receipt["status"] == "COMPLETED" and receipt["exit_code"] == 0
    record = receipt["cancel"]
    assert record["state_before"] == "RUNNING" and record["state"] == "CANCELLED" and record["changed"] is True and record["execution"] == EXEC
    assert record["polls"] == 2                                                              # cancel is asynchronous: the first read-back still said RUNNING
    verbs = world.run_cloud.verbs()
    assert verbs.count("cancel") == 1 and verbs[0] == "describe" and verbs[-1] == "describe" and verbs.index("cancel") == 1


def test_m4_cancelling_a_cancelled_execution_is_idempotent_and_makes_no_cancel_call(world):
    world.run_cloud.state = "CANCELLED"
    receipt = world.run(world.cancel_request())
    assert receipt["status"] == "COMPLETED" and receipt["cancel"]["state"] == "CANCELLED" and receipt["cancel"]["changed"] is False
    assert "cancel" not in world.run_cloud.verbs()


# ───────────────────────────── M5 a non-CANCELLED observed state is a failure ─────────────────────────────
def test_m5_a_cancel_that_exits_zero_yet_leaves_the_execution_running_is_a_failure(world):
    world.run_cloud.effect = "nothing"
    receipt = world.run(world.cancel_request())
    assert receipt["status"] == "FAILED" and receipt["cancel"]["state"] == "RUNNING" and receipt["cancel"]["status"] == "FAILED"
    assert receipt["cancel"]["polls"] == cancel.POLLS


@pytest.mark.parametrize("state", ["SUCCEEDED", "FAILED"])
def test_m5_an_execution_already_finished_is_a_failure_with_that_state_and_no_call(world, state):
    world.run_cloud.state = state
    receipt = world.run(world.cancel_request())
    assert receipt["status"] == "FAILED" and receipt["cancel"]["state"] == state and "cancel" not in world.run_cloud.verbs()


def test_m5_the_executor_fails_an_exit_zero_record_that_does_not_read_cancelled(world):
    req = world.cancel_request()
    ok = {"schema": "ky.measuring_cancel/1", "dry_run": False, "status": "OK", "state": "CANCELLED", "execution": EXEC, "operation_id": req["operation_id"],
          "request_sha256": world.mod.request_digest(req), "project": "madhav-astrology", "region": "asia-south1", "job": "brahma-build-pipeline-job"}
    assert world.mod.measuring_cancel_proof(req, 0, json.dumps(ok))[1] is None
    assert world.mod.measuring_cancel_proof(req, 0, json.dumps(dict(ok, state="SUCCEEDED")))[1]
    assert world.mod.measuring_cancel_proof(req, 0, json.dumps(dict(ok, status="FAILED")))[1]
    assert world.mod.measuring_cancel_proof(req, 0, "no record")[1]


# ───────────────────────────── M6 the IAM readback lists run.executions.cancel ─────────────────────────────
def test_m6_the_iam_readback_reports_run_executions_cancel_granted_or_missing():
    everything = [p for p in reaper.PERMISSIONS]
    cloud = FakeCloud("ENABLED", granted=[p for p in everything if p != "run.executions.cancel"])
    out = io.StringIO()
    assert reaper.main(["--action", "readback"], environ={}, runner=cloud, fetch=cloud.fetch, out=out) == 0
    record = json.loads(out.getvalue())
    assert "run.executions.cancel" in record["permissions"]["requested"] and record["permissions"]["missing"] == ["run.executions.cancel"]
    assert cloud.fetches[0][1] == {"permissions": everything} and record["identity"]["principal"]
    full = FakeCloud("ENABLED", granted=everything)
    out = io.StringIO()
    reaper.main(["--action", "readback"], environ={}, runner=full, fetch=full.fetch, out=out)
    permissions = json.loads(out.getvalue())["permissions"]
    assert "run.executions.cancel" in permissions["granted"] and permissions["missing"] == []


# ───────────────────────────── M7 the cancel is never held by the production fence ─────────────────────────────
def test_m7_the_fence_holds_a_pause_but_never_a_cancel(tmp_path, monkeypatch):
    w = CancelWorld(tmp_path, monkeypatch)
    ran, finished = [], threading.Event()
    def fake_run_one(path, req, op):
        ran.append(req["kind"]); finished.set()
    monkeypatch.setattr(w.mod, "run_one", fake_run_one)
    monkeypatch.setattr(w.mod, "validate", lambda *a, **k: None)
    monkeypatch.setattr(w.mod, "mark_seen", lambda *a: None)
    w.mod.FENCE.write_text(json.dumps({"operation_id": DISPATCH_OP, "request_sha256": "0" * 64}))      # the live measuring dispatch holds the slot
    (w.mod.REQ / "cancel.json").write_text(json.dumps(w.cancel_request(oid="cancel")))
    (w.mod.REQ / "pause.json").write_text(json.dumps(w.request("scheduler_pause", {"resume-by": stamp(utc_now() + dt.timedelta(hours=1))}, oid="pause")))
    run_main_one_turn(w, monkeypatch)
    assert finished.wait(5)
    assert ran == ["measuring_cancel"] and (w.mod.REQ / "pause.json").exists()


# ───────────────────────────── M8 one signer, a lease, no dry-run twin ─────────────────────────────
def test_m8_a_cancel_needs_the_lease_a_verifier_acceptance_and_the_dry_run_attestation(world):
    entry = TABLE["measuring_cancel"]
    assert entry["production"] is True and entry["needs"] == "gcloud" and "also_needs" not in entry and "remote_async" not in entry
    assert entry["allowed_args"] == ["execution"] and entry["enabled_by"] == "J-3c" and entry.get("requesters") is None     # default: adhikarin only
    assert world.validate(world.cancel_request(checks={"dry_run_passed": True})) is None     # signed by one verifier lane
    assert world.validate(world.cancel_request(checks={}, oid="op-cancel-nocheck")) == "required backup/restore/dry-run attestation missing"
    assert "acceptance receipt missing" in world.validate(world.cancel_request(signed=False, oid="op-cancel-unsigned"))
    req = world.cancel_request()
    req["chart_id"] = "00000000-0000-0000-0000-000000000000"
    assert world.validate(req) == "chart_id is not the canonical chart"


# ───────────────────────────── M9 the receipt binds operation, request and execution ─────────────────────────────
def test_m9_a_record_for_another_operation_request_or_execution_is_not_this_receipt(world):
    req = world.cancel_request()
    ok = {"schema": "ky.measuring_cancel/1", "dry_run": False, "status": "OK", "state": "CANCELLED", "execution": EXEC, "operation_id": req["operation_id"],
          "request_sha256": world.mod.request_digest(req), "project": "madhav-astrology", "region": "asia-south1", "job": "brahma-build-pipeline-job"}
    assert world.mod.measuring_cancel_proof(req, 0, json.dumps(ok))[0] == ok
    for field, other in (("operation_id", "op-other"), ("request_sha256", "0" * 64), ("execution", OTHER), ("job", "watchdog-reaper"), ("project", "other")):
        proof, problem = world.mod.measuring_cancel_proof(req, 0, json.dumps(dict(ok, **{field: other})))
        assert proof is None and "does not bind" in problem, field
    assert world.mod.measuring_cancel_proof(req, 0, json.dumps(ok) + "\n" + json.dumps(ok))[1]      # two records: not unique


# ───────────────────────────── M10 the dry run admits the same bindings and calls nothing ─────────────────────────────
def test_m10_the_dry_run_checks_the_same_bindings_and_makes_no_cloud_call(world):
    def dry(**kw):
        req = world.cancel_request(**kw); req.update(kind="measuring_cancel_dryrun", operation_id=kw.get("oid", "op-cancel-1") + "-dry"); return req
    entry = TABLE["measuring_cancel_dryrun"]
    assert entry["production"] is False and entry["needs"] == "gcloud" and entry["fixed_args"] == ["--dry-run"] and entry["script"] == TABLE["measuring_cancel"]["script"]
    assert "not the execution named" in world.validate(dry(target=OTHER))
    assert "not an ABORT or stall verdict" in world.validate(dry(verdict=world.verdict_ref({"schema": "ky.reproject_verdict/1", "verdict": "CONTINUE"})))
    receipt = world.run(dry())
    assert receipt["status"] == "COMPLETED", receipt["reason"]
    assert receipt["cancel"]["status"] == "DRY_RUN" and receipt["cancel"]["gcloud_calls"] == 0
    assert world.run_cloud.calls == []
    out = io.StringIO()
    assert cancel.main(["--execution", EXEC, "--dry-run"], environ={}, runner=Forbidden(), sleep=Forbidden(), out=out) == 0 and json.loads(out.getvalue())["state"] is None


def test_m9_the_script_digest_equals_the_executors_for_the_same_request(world):
    req = world.cancel_request()
    req.update(task_expires_at="2030-01-01T00:00:00Z", weird={"b": [1, 2], "a": None})
    assert cancel.request_digest(req) == world.mod.request_digest(req)
