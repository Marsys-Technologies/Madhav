"""W3W4 pack verify E1: governed `century_cancel` and `verification_cancel` (+ their `*_dryrun` twins) — measuring_cancel's family.

Same doctrine as test_executor_measuring_cancel.py (SR-J3-CANCEL-NULL 2(a): "refuses unless target == execution named in the dispatch receipt AND an ABORT/stall verdict
file cited by digest; one signer; readback CANCELLED") and the same stateful in-process Cloud Run fake: no gcloud, no network, no database, no git write. The family's own facts:
the century build runs on the build job `brahma-build-pipeline-job` and its dispatch receipt is a `century_dispatch` of J-4e; the verification job is the Cloud Run job
`gochara-verification-job` (gochara-verification-job-deploy.yml) and its launch receipt is a `verification_job` of J-5s (the pack's request templates carry these item ids and
the single `execution` argument). Distinct production claims, each with a doctrine-grounded oracle (a reversion of the claim's own line fails it):
K1 the table binds both kinds of each family, with a production:false `--dry-run` twin on the same script and the one `execution` argument ·
K2 the accepted request shape is admitted, the dry-run twin too · K3 an unknown argument is refused on every kind ·
K4 the target is bound to the family's OWN dispatch receipt (another execution, another family's receipt, another job's execution name, another item all refuse) ·
K5 a cancel is signed-only: a lease and one verifier lane's acceptance, never the mechanical route ·
K6 a cancel is never held by the production fence · K7 the script cancels the family's own job and records the state read back, and refuses another job's execution before any call ·
K8 the executor's proof binds the family's record schema and job.
"""
import io
import json
import subprocess
import threading

import pytest

from test_executor_measuring_cancel import ABORT, DISPATCH_OP, CancelWorld, FakeRun
from test_executor_scheduler_reaper import COMMIT, FLEET, LEASE, TABLE, Forbidden, load, run_main_one_turn, stamp, utc_now
import datetime as dt

FAMILIES = {
    "century": {"kind": "century_cancel", "item": "J-4e", "dispatch_kind": "century_dispatch", "launch_schema": "ky.century_launch/1", "schema": "ky.century_cancel/1",
                "script": "century_cancel.py", "job": "brahma-build-pipeline-job", "execution": "brahma-build-pipeline-job-abc12", "other": "brahma-build-pipeline-job-zzz99",
                "foreign_job_execution": "gochara-verification-job-abc12", "foreign_dispatch": ("measuring_dispatch", "J-3c")},
    "verification": {"kind": "verification_cancel", "item": "J-5s", "dispatch_kind": "verification_job", "launch_schema": "ky.verification_launch/1", "schema": "ky.verification_cancel/1",
                     "script": "verification_cancel.py", "job": "gochara-verification-job", "execution": "gochara-verification-job-abc12", "other": "gochara-verification-job-zzz99",
                     "foreign_job_execution": "brahma-build-pipeline-job-abc12", "foreign_dispatch": ("century_dispatch", "J-4e")},
}


def resource_of(job, state, name):
    status = {"RUNNING": {"conditions": [{"type": "Completed", "status": "Unknown"}], "runningCount": 1},
              "CANCELLED": {"conditions": [{"type": "Completed", "status": "False"}], "cancelledCount": 1},
              "SUCCEEDED": {"conditions": [{"type": "Completed", "status": "True"}], "succeededCount": 1},
              "FAILED": {"conditions": [{"type": "Completed", "status": "False"}], "failedCount": 1}}[state]
    return {"metadata": {"name": name, "labels": {"run.googleapis.com/job": job}}, "spec": {"taskCount": 1}, "status": status}


class FamilyRun(FakeRun):
    """measuring_cancel's stateful `gcloud run jobs executions` stand-in, with the execution labelled as belonging to the family's own Cloud Run job."""

    def __init__(self, fam, **kw):
        super().__init__(name=fam["execution"], **kw)
        self.job = fam["job"]

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
        return done(json.dumps(resource_of(self.job, self.state, self.name)))


class FamilyWorld(CancelWorld):
    def __init__(self, tmp_path, monkeypatch, fam):
        self.fam = fam
        super().__init__(tmp_path, monkeypatch, run_cloud=FamilyRun(fam))
        self.script = load(FLEET / fam["script"], f"{fam['kind']}_under_test_{abs(hash(str(tmp_path)))}")

    def execute(self, req, op):
        args = list(op.get("fixed_args", []))                                                # what the real execute() builds
        for k, v in (req.get("args") or {}).items(): args += [f"--{k}", str(v)]
        out = io.StringIO()
        rc = self.script.main(args, environ={"KY_OPERATION_REQUEST": json.dumps(req, sort_keys=True, separators=(",", ":"))}, runner=self.run_cloud, sleep=lambda s: None, out=out)
        return rc, out.getvalue()

    def dispatch_ref(self, execution=None, kind=None, item=None, **overrides):
        receipt = {"operation_id": DISPATCH_OP, "kind": kind or self.fam["dispatch_kind"], "item_id": item or self.fam["item"], "status": "COMPLETED", "exit_code": 0,
                   "launch": {"schema": self.fam["launch_schema"], "status": "LAUNCHED", "execution_name": execution or self.fam["execution"]}}
        receipt.update(overrides)
        return self.cite("receipts", f"{DISPATCH_OP}.json", receipt)

    def cancel_request(self, target=None, dispatch=None, verdict=None, oid="op-cancel-1", checks=None, signed=True, kind=None, item=None):
        req = super().cancel_request(target=target or self.fam["execution"], dispatch=self.dispatch_ref() if dispatch is None else dispatch, verdict=verdict, oid=oid, checks=checks, signed=False)
        req.update(kind=kind or self.fam["kind"], item_id=item or self.fam["item"])
        acceptance = self.mod.ACC / f"{oid}.json"
        if signed:
            acceptance.write_text(json.dumps({"result": "ACCEPTED", "by": "v1", "operation_id": oid, "reviewed_commit": COMMIT, "ts": self.mod.now(),
                                              "request_sha256": self.mod.request_digest(req), "checks": checks if checks is not None else {"dry_run_passed": True}}))
        return req

    def dry(self, **kw):
        req = self.cancel_request(**kw)
        req.update(kind=self.fam["kind"] + "_dryrun", operation_id=kw.get("oid", "op-cancel-1") + "-dry")
        return req


@pytest.fixture(params=sorted(FAMILIES))
def fam(request):
    return FAMILIES[request.param]


@pytest.fixture
def world(tmp_path, monkeypatch, fam):
    return FamilyWorld(tmp_path, monkeypatch, fam)


# ───────────────────────────── K1 the table binds both kinds of each family ─────────────────────────────
def test_k1_each_family_has_a_production_cancel_and_a_read_only_dry_run_twin_on_one_script(fam):
    cancel, twin = TABLE[fam["kind"]], TABLE[fam["kind"] + "_dryrun"]
    script = f"00_ARCHITECTURE/briefs/kalayantra/fleet/{fam['script']}"
    assert (FLEET.parents[3] / script).is_file()                                                              # never TO_BE_SET: the reviewed script exists
    assert cancel["script"] == twin["script"] == script
    assert cancel["enabled"] is True and twin["enabled"] is True
    assert cancel["production"] is True and twin["production"] is False                                       # A8 §3.8: the dry run is read-only with a credential
    assert cancel["fixed_args"] == [] and twin["fixed_args"] == ["--dry-run"]
    assert cancel["allowed_args"] == twin["allowed_args"] == ["execution"]
    assert cancel["needs"] == twin["needs"] == "gcloud" and "also_needs" not in cancel and "remote_async" not in cancel      # a cancel ends work; it is not a remote launch
    assert cancel.get("requesters") is None and twin.get("requesters") is None                                # default: adhikarin only


# ───────────────────────────── K2 the accepted request shape ─────────────────────────────
def test_k2_the_accepted_request_is_admitted_and_so_is_its_dry_run_twin(world):
    assert world.validate(world.cancel_request()) is None
    assert world.validate(world.dry()) is None
    receipt = world.run(world.dry())
    assert receipt["status"] == "COMPLETED", receipt["reason"]
    assert receipt["cancel"]["status"] == "DRY_RUN" and receipt["cancel"]["gcloud_calls"] == 0 and world.run_cloud.calls == []


# ───────────────────────────── K3 an unknown argument is refused ─────────────────────────────
@pytest.mark.parametrize("extra", ["job", "force", "run", "logs"])
@pytest.mark.parametrize("twin", ["", "_dryrun"])
def test_k3_an_unlisted_argument_is_refused_on_every_cancel_kind(world, extra, twin):
    req = world.cancel_request() if not twin else world.dry()
    req["args"] = {"execution": world.fam["execution"], extra: "fixture"}
    if not twin:
        acceptance = world.mod.ACC / f"{req['operation_id']}.json"
        acceptance.write_text(json.dumps({"result": "ACCEPTED", "by": "v1", "operation_id": req["operation_id"], "reviewed_commit": COMMIT, "ts": world.mod.now(),
                                          "request_sha256": world.mod.request_digest(req), "checks": {"dry_run_passed": True}}))
    assert world.validate(req) == f"disallowed args ['{extra}']"


# ───────────────────────────── K4 the target is bound to the family's own dispatch receipt ─────────────────────────────
def test_k4_a_target_other_than_the_dispatched_execution_is_refused_and_nothing_is_called(world):
    req = world.cancel_request(target=world.fam["other"])
    assert f"not the execution named in the cited {world.fam['dispatch_kind']} receipt" in world.validate(req)
    world.run_cloud.name = world.fam["other"]
    assert world.run(req)["status"] == "REFUSED" and world.run_cloud.calls == []


def test_k4_another_familys_dispatch_receipt_never_binds_the_target(world):
    kind, item = world.fam["foreign_dispatch"]
    foreign = world.dispatch_ref(kind=kind, item=item)                                                         # same execution name, the other family's COMPLETED launch
    assert world.validate(world.cancel_request(dispatch=foreign)) == f"the cited receipt is not the COMPLETED launch of a {world.fam['item']} {world.fam['dispatch_kind']}"
    assert "does not match its sha256" in world.validate(world.cancel_request(dispatch=dict(foreign, sha256="0" * 64)))
    wrong_item = world.dispatch_ref(item="J-3c" if world.fam["item"] != "J-3c" else "J-4e")
    assert "not the COMPLETED launch" in world.validate(world.cancel_request(dispatch=wrong_item))


def test_k4_an_execution_name_of_the_other_job_is_refused_and_so_is_a_request_of_another_item(world):
    foreign = world.fam["foreign_job_execution"]
    req = world.cancel_request(target=foreign, dispatch=world.dispatch_ref(execution=foreign))                 # the receipt names it, but it is not THIS family's job
    assert world.validate(req) == f"execution must be a {world.fam['job']} execution name"
    assert world.validate(world.cancel_request(item="J-1a")) == f"{world.fam['kind'].split('_')[0]} cancel belongs to {world.fam['item']}"


def test_k4_only_an_abort_or_stall_verdict_cancels(world):
    assert world.validate(world.cancel_request(verdict=world.verdict_ref({"schema": "ky.stall_verdict/1", "verdict": "STALL"}))) is None
    for bad in ({"schema": "ky.reproject_verdict/1", "verdict": "CONTINUE"}, {"schema": "ky.reproject_verdict/1", "verdict": None}):
        assert "not an ABORT or stall verdict" in world.validate(world.cancel_request(verdict=world.verdict_ref(bad)))


# ───────────────────────────── K5 signed-only: never the mechanical route ─────────────────────────────
def test_k5_a_cancel_needs_the_lease_and_a_verifier_acceptance_and_never_goes_mechanical(world):
    assert world.mod.mechanical_exempt(world.fam["kind"]) is True and world.fam["kind"] in world.mod.SIGNED_ONLY_KINDS
    assert world.validate(world.cancel_request(checks={"dry_run_passed": True})) is None                      # signed by one verifier lane
    assert world.validate(world.cancel_request(checks={}, oid="op-cancel-nocheck")) == "required backup/restore/dry-run attestation missing"
    assert "acceptance receipt missing" in world.validate(world.cancel_request(signed=False, oid="op-cancel-unsigned"))
    unsigned_fill = world.cancel_request(signed=False, oid="op-cancel-fill")
    unsigned_fill.pop("acceptance_receipt")
    unsigned_fill["pack_fill"] = {"pack_manifest_sha256": "0" * 64, "template": {"kind": world.fam["kind"], "fixed": {}, "fill": []}, "fill_sha256": "0" * 64}
    why = world.validate(unsigned_fill)
    assert why is not None and "needs a V1 signer" in why                                                    # a pack fill cannot stand in for the signer
    req = world.cancel_request()
    req["chart_id"] = "00000000-0000-0000-0000-000000000000"
    assert world.validate(req) == "chart_id is not the canonical chart"


def test_k5_century_teardown_is_a_deletion_and_stays_signed_only(tmp_path, monkeypatch):
    w = FamilyWorld(tmp_path, monkeypatch, FAMILIES["century"])
    assert TABLE["century_teardown"]["enabled"] is True and TABLE["century_teardown"]["production"] is True
    assert w.mod.mechanical_exempt("century_teardown") is True                                                 # OWNER-MINIMAL-PROTECTION-NOW: every `*_teardown` needs a V1 signer
    assert w.mod.mechanical_exempt("century_dispatch") is False                                                # control: the exemption is not "every century kind"


# ───────────────────────────── K6 never held by the production fence ─────────────────────────────
def test_k6_the_fence_holds_a_pause_but_never_this_families_cancel(tmp_path, monkeypatch, fam):
    w = FamilyWorld(tmp_path, monkeypatch, fam)
    ran, finished = [], threading.Event()
    def fake_run_one(path, req, op):
        ran.append(req["kind"]); finished.set()
    monkeypatch.setattr(w.mod, "run_one", fake_run_one)
    monkeypatch.setattr(w.mod, "validate", lambda *a, **k: None)
    monkeypatch.setattr(w.mod, "mark_seen", lambda *a: None)
    w.mod.FENCE.write_text(json.dumps({"operation_id": DISPATCH_OP, "request_sha256": "0" * 64}))          # the live dispatch holds the slot
    (w.mod.REQ / "cancel.json").write_text(json.dumps(w.cancel_request(oid="cancel")))
    (w.mod.REQ / "pause.json").write_text(json.dumps(w.request("scheduler_pause", {"resume-by": stamp(utc_now() + dt.timedelta(hours=1))}, oid="pause")))
    run_main_one_turn(w, monkeypatch)
    assert finished.wait(5)
    assert ran == [fam["kind"]] and (w.mod.REQ / "pause.json").exists()


# ───────────────────────────── K7 the script cancels the family's own job and records the state read back ─────────────────────────────
def test_k7_the_receipt_records_the_state_read_back_after_the_cancel_for_the_familys_job(world):
    receipt = world.run(world.cancel_request())
    assert receipt["status"] == "COMPLETED" and receipt["exit_code"] == 0
    record = receipt["cancel"]
    assert record["schema"] == world.fam["schema"] and record["job"] == world.fam["job"] and record["execution"] == world.fam["execution"]
    assert record["state_before"] == "RUNNING" and record["state"] == "CANCELLED" and record["changed"] is True and record["polls"] == 2
    verbs = world.run_cloud.verbs()
    assert verbs.count("cancel") == 1 and verbs[0] == "describe" and verbs[-1] == "describe"


def test_k7_a_cancel_that_exits_zero_yet_leaves_the_execution_running_is_a_failure(world):
    world.run_cloud.effect = "nothing"
    receipt = world.run(world.cancel_request())
    assert receipt["status"] == "FAILED" and receipt["cancel"]["state"] == "RUNNING" and receipt["cancel"]["schema"] == world.fam["schema"]


def test_k7_the_script_refuses_the_other_jobs_execution_name_before_any_call(world):
    out = io.StringIO()
    rc = world.script.main(["--execution", world.fam["foreign_job_execution"]], environ={}, runner=Forbidden(), sleep=Forbidden(), out=out)
    record = json.loads(out.getvalue())
    assert rc == 1 and record["status"] == "REFUSED" and record["gcloud_calls"] == 0 and record["execution"] is None and record["job"] == world.fam["job"]


def test_k7_an_execution_that_belongs_to_another_job_is_refused(world):
    wrong = FamilyRun(dict(world.fam, job="watchdog-reaper"))                                                  # the described execution carries another job's label
    out = io.StringIO()
    rc = world.script.main(["--execution", world.fam["execution"]], environ={}, runner=wrong, sleep=lambda s: None, out=out)
    record = json.loads(out.getvalue())
    assert rc == 1 and record["status"] == "FAILED" and "belongs to job" in record["reason"]                  # FAILED, not REFUSED: the describe call had been made
    assert record["changed"] is False and record["state"] is None and "cancel" not in wrong.verbs()


# ───────────────────────────── K8 the executor's proof binds the family's schema and job ─────────────────────────────
def test_k8_a_record_of_another_schema_job_or_execution_is_not_this_receipt(world):
    req = world.cancel_request()
    ok = {"schema": world.fam["schema"], "dry_run": False, "status": "OK", "state": "CANCELLED", "execution": world.fam["execution"], "operation_id": req["operation_id"],
          "request_sha256": world.mod.request_digest(req), "project": "madhav-astrology", "region": "asia-south1", "job": world.fam["job"]}
    assert world.mod.measuring_cancel_proof(req, 0, json.dumps(ok)) == (ok, None)
    other_schema = "ky.measuring_cancel/1" if world.fam["schema"] != "ky.measuring_cancel/1" else "ky.century_cancel/1"
    assert world.mod.measuring_cancel_proof(req, 0, json.dumps(dict(ok, schema=other_schema))) == (None, "cancel record missing or not unique")
    foreign = "gochara-verification-job" if world.fam["job"] != "gochara-verification-job" else "brahma-build-pipeline-job"
    for field, other in (("job", foreign), ("execution", world.fam["other"]), ("operation_id", "op-other"), ("request_sha256", "0" * 64)):
        proof, problem = world.mod.measuring_cancel_proof(req, 0, json.dumps(dict(ok, **{field: other})))
        assert proof is None and "does not bind" in problem, field
    assert world.mod.measuring_cancel_proof(req, 0, json.dumps(dict(ok, state="SUCCEEDED")))[1]
