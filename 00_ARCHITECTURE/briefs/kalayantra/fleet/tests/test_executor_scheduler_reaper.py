"""SR-J3-REAPER-PAUSE (J-3c): governed scheduler_pause / scheduler_resume / scheduler_readback for the watchdog Cloud Scheduler job.

One doctrine-grounded oracle per distinct production claim; every cloud call is a stateful in-process fake (no gcloud, no network, no database,
no git write). Sources of the expected values: the ruling SR-J3-REAPER-PAUSE (DECISIONS_SURROGATE.jsonl), platform/scripts/provision_watchdog_scheduler.sh
(the job, project and region), the Cloud Scheduler v1 Job.State enum / pause + resume contract, and executor.py's own admission rules (A8 §3.8-§3.11).
Claims: C1 allow-list · C2 idempotent pause/resume with the state read back after the action in the receipt · C3 resume-by required and <= lease end ·
C4 the backstop fires when no resume ever runs (armed before the pause) · C5 dry runs never call the scheduler · C6 permission/identity check ·
C7 the backstop survives an executor restart · C8 a resume is never held by the production fence · C9 the receipt binds operation, request and job.
"""
import datetime as dt
import importlib.util
import io
import json
import re
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

FLEET = Path(__file__).resolve().parents[1]
REPO = FLEET.parents[3]
SCRIPT = FLEET / "scheduler_reaper.py"
TABLE = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
COMMIT = "a" * 40
LEASE = "LEASE-KY-FIXTURE"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
SECRET_TOKEN = "ya29.FIXTURE-TOKEN-THAT-MUST-NEVER-BE-PRINTED-0123456789"
PRINCIPAL = "ky-executor@madhav-astrology.iam.gserviceaccount.com"
ALL_CAPS = {k: True for k in ("owner", "builder", "gcloud", "pgenv", "none")}
KINDS = ["scheduler_readback", "scheduler_pause_dryrun", "scheduler_pause", "scheduler_resume_dryrun", "scheduler_resume"]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


reaper = load(SCRIPT, "scheduler_reaper_under_test")


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def stamp(moment):
    return moment.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class FakeCloud:
    """A stateful stand-in for gcloud + the testIamPermissions endpoint. `stuck` makes pause/resume exit 0 yet change nothing (the exit status is a lie)."""

    def __init__(self, state="ENABLED", granted=reaper.PERMISSIONS, stuck=False, describe_fails=False, fetch_fails=False):
        self.state, self.granted, self.stuck, self.describe_fails, self.fetch_fails = state, list(granted), stuck, describe_fails, fetch_fails
        self.calls, self.fetches = [], []

    def __call__(self, argv):
        self.calls.append(list(argv))
        done = lambda out="", rc=0: subprocess.CompletedProcess(argv, rc, out, "")
        if argv[:3] == ["gcloud", "scheduler", "jobs"]:
            verb, name = argv[3], argv[4]
            assert name == "watchdog-reaper" and "--location=asia-south1" in argv and "--project=madhav-astrology" in argv, argv
            if verb == "describe":
                if self.describe_fails: return done("", 1)
                return done(json.dumps({"name": "projects/madhav-astrology/locations/asia-south1/jobs/watchdog-reaper", "state": self.state}))
            if verb in ("pause", "resume") and not self.stuck:
                self.state = "PAUSED" if verb == "pause" else "ENABLED"
            return done()
        if argv[:3] == ["gcloud", "auth", "list"]: return done(PRINCIPAL + "\n")
        if argv[:3] == ["gcloud", "auth", "print-access-token"]: return done(SECRET_TOKEN + "\n")
        raise AssertionError("unexpected external call: " + repr(argv))

    def fetch(self, url, token, body):
        self.fetches.append((url, body))
        if self.fetch_fails: raise OSError("network down")
        assert token == SECRET_TOKEN and url.endswith("/projects/madhav-astrology:testIamPermissions")
        return {"permissions": [p for p in body["permissions"] if p in self.granted]}

    def verbs(self):
        return [c[3] for c in self.calls if c[:3] == ["gcloud", "scheduler", "jobs"]]


class Forbidden:
    """Any use is a failure: the proof that a path makes no external call."""

    def __call__(self, *a, **k): raise AssertionError("an external call was made")


def run_script(action, cloud, *extra, env=None):
    out = io.StringIO()
    rc = reaper.main(["--action", action, *extra], environ=env or {}, runner=cloud, fetch=cloud.fetch, out=out)
    return rc, json.loads(out.getvalue())


# ───────────────────────────── executor fixture ─────────────────────────────
class World:
    """The real executor module on a throwaway KY_ROOT; Git, the lease table, the table-on-main and the child process are doubles."""

    def __init__(self, tmp_path, monkeypatch, lease_end=None, cloud=None, name="ky_exec_sched"):
        monkeypatch.setenv("KY_ROOT", str(tmp_path / "ky"))
        self.mod = load(FLEET / "executor.py", f"{name}_{abs(hash(str(tmp_path)))}")
        self.cloud = cloud or FakeCloud()
        self.lease_end = lease_end or (utc_now() + dt.timedelta(hours=6)).replace(second=0)      # the lease table states minutes
        self.lease_unreadable = False
        self.monkeypatch = monkeypatch
        m = self.mod
        for d in (m.REQ, m.REC, m.DONE, m.ACC, m.INFLIGHT, m.TMP, m.KY_ROOT / "logs"): d.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(m, "git", self.git)
        monkeypatch.setattr(m, "lease_live", lambda _: True)
        monkeypatch.setattr(m, "seen", lambda _: False)
        monkeypatch.setattr(m, "sync", lambda: None)
        monkeypatch.setattr(m, "load_table", lambda: TABLE)
        monkeypatch.setattr(m, "capabilities", lambda _=True: ALL_CAPS)
        monkeypatch.setattr(m, "execute", self.execute)
        monkeypatch.setattr(m, "run_group", self.run_group)
        self.script_text = SCRIPT.read_text()

    def lease_table(self):
        if self.lease_unreadable: return "## 1. Leases\n## 2. x\n"
        end = self.lease_end.astimezone(IST).strftime("%Y-%m-%d %H:%M")
        return f"## 1. Leases\n| {LEASE} | KY | item | start | {end} | ACTIVE |\n## 2. History\n"

    def git(self, *args, **kwargs):
        ok = lambda out="": SimpleNamespace(returncode=0, stdout=out, stderr="")
        if args[:2] == ("show", "origin/campaign-coordination:" + self.mod.COORD_PATH): return ok(self.lease_table())
        if args[:2] == ("merge-base", "--is-ancestor"): return ok()
        if args[:2] == ("cat-file", "-e"): return ok()
        if len(args) == 2 and args[0] == "show" and args[1] == f"{COMMIT}:{self.mod.SCHEDULER_SCRIPT}": return ok(self.script_text)
        raise AssertionError("unexpected Git observation: " + repr(args))

    def run_in_process(self, argv, env):
        out = io.StringIO()
        rc = reaper.main(argv, environ=env, runner=self.cloud, fetch=self.cloud.fetch, out=out)
        return rc, out.getvalue()

    def execute(self, req, op):
        """What the real execute() does for a scheduler kind, with the reviewed script run in-process against the fake cloud."""
        args = list(op.get("fixed_args", []))
        for k, v in (req.get("args") or {}).items(): args += [f"--{k}", str(v)]
        return self.run_in_process(args, {"KY_OPERATION_REQUEST": json.dumps(req, sort_keys=True, separators=(",", ":"))})

    def run_group(self, argv, cwd, env, timeout):
        rc, out = self.run_in_process(argv[2:], env)            # argv = [python, script, --action resume --job J]
        return subprocess.CompletedProcess(argv, rc, out, "")

    def request(self, kind, args=None, oid=None):
        oid = oid or f"op-{kind}-{len(list(self.mod.DONE.glob('*.json'))) + len(list(self.mod.REQ.glob('*.json')))}"
        production = TABLE[kind]["production"]
        req = {"operation_id": oid, "idempotency_key": oid, "item_id": "J-3c", "kind": kind, "requested_by": "adhikarin", "kyd": "KYD-FIXTURE",
               "args": args or {}, "reviewed_commit": COMMIT, "expires_at": (utc_now() + dt.timedelta(hours=1)).isoformat()}
        if production:
            req.update(chart_id=self.mod.CANONICAL_CHART, lease_id=LEASE)
            acceptance = self.mod.ACC / f"{oid}.json"
            req["acceptance_receipt"] = str(acceptance)
            acceptance.write_text(json.dumps({"result": "ACCEPTED", "by": "v1", "operation_id": oid, "reviewed_commit": COMMIT, "ts": self.mod.now(),
                                              "request_sha256": self.mod.request_digest(req), "checks": {"dry_run_passed": True}}))
        return req

    def pause_request(self, resume_by=None, **kw):
        resume_by = resume_by or utc_now() + dt.timedelta(hours=2)
        return self.request("scheduler_pause", {"job": "watchdog-reaper", "resume-by": stamp(resume_by)}, **kw)

    def validate(self, req):
        return self.mod.validate(req, TABLE, ALL_CAPS)

    def run(self, req):
        path = self.mod.INFLIGHT / f"{req['operation_id']}.json"
        path.write_text(json.dumps(req))
        self.mod.run_one(path, req, TABLE[req["kind"]])
        return json.loads((self.mod.REC / f"{req['operation_id']}.json").read_text())

    def backstops(self):
        return {p.stem: json.loads(p.read_text()) for p in sorted(self.mod.SCHEDULER_BACKSTOP.glob("*.json"))} if self.mod.SCHEDULER_BACKSTOP.exists() else {}


@pytest.fixture
def world(tmp_path, monkeypatch):
    return World(tmp_path, monkeypatch)


# ───────────────────────────── C1 allow-list ─────────────────────────────
def test_c1_constants_equal_what_the_provisioner_creates(world):
    text = (REPO / "platform/scripts/provision_watchdog_scheduler.sh").read_text()
    assert re.search(r'PROJECT="\$\{GCP_PROJECT:-([^}]+)\}"', text).group(1) == world.mod.SCHEDULER_PROJECT == reaper.PROJECT
    assert re.search(r'REGION="\$\{GCP_REGION:-([^}]+)\}"', text).group(1) == world.mod.SCHEDULER_REGION == reaper.REGION
    assert re.search(r"jobs (?:create|update) http (\S+)", text).group(1) == world.mod.SCHEDULER_JOB == reaper.JOB == "watchdog-reaper"


@pytest.mark.parametrize("action", ["pause", "resume", "readback"])
@pytest.mark.parametrize("other", ["brahma-build-pipeline-job", "watchdog-reaper-2", "WATCHDOG-REAPER", "other"])
def test_c1_the_script_refuses_any_other_job_before_any_call(action, other):
    extra = ["--resume-by", stamp(utc_now() + dt.timedelta(hours=1))] if action == "pause" else []
    out = io.StringIO()
    rc = reaper.main(["--action", action, "--job", other, *extra], environ={}, runner=Forbidden(), fetch=Forbidden(), out=out)
    record = json.loads(out.getvalue())
    assert rc == 1 and record["status"] == "REFUSED" and record["gcloud_calls"] == 0 and record["job"] == "watchdog-reaper"
    assert "allow-list" in record["reason"]


@pytest.mark.parametrize("kind", KINDS)
def test_c1_admission_refuses_any_other_job_for_every_scheduler_kind(world, kind):
    args = {"job": "brahma-build-pipeline-job"}
    if kind.startswith("scheduler_pause"): args["resume-by"] = stamp(utc_now() + dt.timedelta(hours=1))
    why = world.validate(world.request(kind, args))
    assert why and "allow-list" in why, why
    args["job"] = "watchdog-reaper"                          # positive control: the same request for the allow-listed job is admitted
    assert world.validate(world.request(kind, args)) is None


# ───────────────────────────── C2 idempotency + state read back after the action ─────────────────────────────
def test_c2_pause_acts_once_and_reports_the_state_read_back_after():
    cloud = FakeCloud("ENABLED")
    rc, record = run_script("pause", cloud, "--resume-by", stamp(utc_now() + dt.timedelta(hours=1)))
    assert rc == 0 and record["status"] == "OK" and record["state_before"] == "ENABLED" and record["changed"] is True and record["state"] == "PAUSED"
    assert cloud.verbs() == ["describe", "pause", "describe"]               # the last call is the read-back AFTER the action
    rc, again = run_script("pause", cloud, "--resume-by", stamp(utc_now() + dt.timedelta(hours=1)))
    assert rc == 0 and again["status"] == "OK" and again["changed"] is False and again["state_before"] == "PAUSED" and again["state"] == "PAUSED"
    assert cloud.verbs().count("pause") == 1                                # pausing a paused job is success and acts no second time


def test_c2_resume_acts_once_and_is_idempotent():
    cloud = FakeCloud("PAUSED")
    rc, record = run_script("resume", cloud)
    assert rc == 0 and record["changed"] is True and record["state_before"] == "PAUSED" and record["state"] == "ENABLED"
    assert cloud.verbs() == ["describe", "resume", "describe"]
    rc, again = run_script("resume", cloud)
    assert rc == 0 and again["changed"] is False and again["state"] == "ENABLED" and cloud.verbs().count("resume") == 1


@pytest.mark.parametrize("action,start", [("pause", "ENABLED"), ("resume", "PAUSED")])
def test_c2_an_exit_zero_that_changed_nothing_is_a_failure_not_a_success(action, start):
    cloud = FakeCloud(start, stuck=True)
    extra = ["--resume-by", stamp(utc_now() + dt.timedelta(hours=1))] if action == "pause" else []
    rc, record = run_script(action, cloud, *extra)
    assert rc == 1 and record["status"] == "FAILED" and record["state"] == start


@pytest.mark.parametrize("action,state", [("pause", "DISABLED"), ("pause", "UPDATE_FAILED"), ("resume", "DISABLED")])
def test_c2_a_state_the_action_cannot_start_from_is_refused_with_the_observed_state(action, state):
    cloud = FakeCloud(state)
    extra = ["--resume-by", stamp(utc_now() + dt.timedelta(hours=1))] if action == "pause" else []
    rc, record = run_script(action, cloud, *extra)
    assert rc == 1 and record["state_before"] == state and record["changed"] is False and not {"pause", "resume"} & set(cloud.verbs())


def test_c2_every_executor_receipt_carries_the_state_read_back_after_the_action(world):
    pause = world.run(world.pause_request())
    assert pause["status"] == "COMPLETED" and pause["scheduler"]["state"] == "PAUSED" and pause["scheduler"]["changed"] is True
    resume = world.run(world.request("scheduler_resume", {}))
    assert resume["status"] == "COMPLETED" and resume["scheduler"]["state"] == "ENABLED"
    readback = world.run(world.request("scheduler_readback", {}))
    assert readback["status"] == "COMPLETED" and readback["scheduler"]["state"] == "ENABLED"
    assert (world.mod.ACC / f"{readback['operation_id']}.post.json").exists()      # a read-only kind is accepted mechanically (A7 D-44)
    assert not (world.mod.ACC / f"{pause['operation_id']}.post.json").exists()      # a writing kind never is


def test_c2_an_exit_zero_whose_record_reads_the_wrong_state_is_failed_by_the_executor(world):
    world.cloud.stuck = True                                                 # the fake script still exits 1; force the lie at the executor boundary instead
    req = world.pause_request()
    lie = dict(reaper.run("pause", False, None, req["args"]["resume-by"], {"KY_OPERATION_REQUEST": json.dumps(req)}, runner=FakeCloud("PAUSED"))[1], state="ENABLED")
    proof, problem = world.mod.scheduler_proof(req, 0, json.dumps(lie))
    assert proof is not None and problem and "state read back" in problem


# ───────────────────────────── C3 resume-by required and <= lease end ─────────────────────────────
def test_c3_admission_requires_resume_by_on_a_pause(world):
    assert "requires resume-by" in world.validate(world.request("scheduler_pause", {"job": "watchdog-reaper"}))
    assert "requires resume-by" in world.validate(world.request("scheduler_pause_dryrun", {}))


def test_c3_resume_by_may_equal_the_lease_end_and_never_pass_it(world):
    end = world.lease_end
    assert world.validate(world.pause_request(resume_by=end)) is None
    why = world.validate(world.pause_request(resume_by=end + dt.timedelta(seconds=1)))
    assert why == "resume-by is after the end of the lease"
    # the dry run, which has no lease of its own, is bounded the same way as soon as it names one
    over = world.request("scheduler_pause_dryrun", {"resume-by": stamp(end + dt.timedelta(minutes=5))})
    over["lease_id"] = LEASE
    assert world.validate(over) == "resume-by is after the end of the lease"


def test_c3_an_unreadable_lease_end_refuses_rather_than_assumes(world):
    world.lease_unreadable = True
    assert "lease end cannot be read" in world.validate(world.pause_request())


def test_c3_resume_by_must_be_future_utc_and_well_formed(world):
    assert world.validate(world.pause_request(resume_by=utc_now() - dt.timedelta(minutes=1))) == "resume-by is not in the future"
    for bad in ("2026-10-19T04:00:00+05:30", "2026-10-19 04:00:00Z", "tomorrow", "2026-10-19"):
        why = world.validate(world.request("scheduler_pause", {"resume-by": bad}))
        assert why and ("UTC timestamp" in why or "unsafe characters" in why), bad      # a space never reaches the policy: SAFE_ARG refuses it first
    plus_zero = (utc_now() + dt.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    assert world.validate(world.request("scheduler_pause", {"resume-by": plus_zero})) is None


def test_c3_the_script_itself_also_requires_a_future_utc_resume_by():
    for extra in ([], ["--resume-by", "2020-01-01T00:00:00Z"], ["--resume-by", "2030-01-01T00:00:00+05:30"]):
        out = io.StringIO()
        rc = reaper.main(["--action", "pause", *extra], environ={}, runner=Forbidden(), fetch=Forbidden(), out=out)
        assert rc == 1 and json.loads(out.getvalue())["status"] == "REFUSED" and json.loads(out.getvalue())["gcloud_calls"] == 0
    out = io.StringIO()                                                      # resume-by belongs to pause only
    assert reaper.main(["--action", "resume", "--resume-by", stamp(utc_now() + dt.timedelta(hours=1))], environ={}, runner=Forbidden(), fetch=Forbidden(), out=out) == 1


def test_c3_resume_and_readback_requests_cannot_carry_resume_by(world):
    for kind in ("scheduler_resume", "scheduler_resume_dryrun", "scheduler_readback"):
        assert world.validate(world.request(kind, {"resume-by": stamp(utc_now() + dt.timedelta(hours=1))})) == "disallowed args ['resume-by']"


# ───────────────────────────── C4 the backstop ─────────────────────────────
def test_c4_a_pause_is_armed_durably_and_fires_at_resume_by_with_no_resume_request(world):
    due = utc_now() + dt.timedelta(hours=2)
    req = world.pause_request(resume_by=due)
    assert world.run(req)["scheduler"]["state"] == "PAUSED" and world.cloud.state == "PAUSED"
    record = world.backstops()[req["operation_id"]]
    assert record["status"] == "ARMED" and record["resume_by"] == due.isoformat(timespec="seconds").replace("+00:00", "+00:00")
    assert world.mod.scheduler_backstop_tick(due - dt.timedelta(seconds=1)) == [] and world.cloud.state == "PAUSED"      # not before resume-by
    assert world.mod.scheduler_backstop_tick(due) == [req["operation_id"]]                                              # at resume-by, nobody asked
    assert world.cloud.state == "ENABLED"
    fired = world.backstops()[req["operation_id"]]
    receipt = json.loads((world.mod.REC / f"{fired['last_receipt']}.json").read_text())
    assert fired["status"] == "FIRED" and receipt["status"] == "COMPLETED" and receipt["scheduler"]["state"] == "ENABLED" and receipt["backstop_for"] == req["operation_id"]
    assert world.mod.scheduler_backstop_tick(due + dt.timedelta(hours=1)) == []                                          # fired once, not again


def test_c4_the_record_exists_before_the_pause_runs_so_a_failed_or_interrupted_pause_is_still_undone(world):
    seen = {}
    real = world.mod.execute

    def watch(req, op):
        seen["armed_before_pause"] = req["operation_id"] in world.backstops() and world.cloud.state == "ENABLED"
        raise RuntimeError("executor died after the pause call")

    world.monkeypatch.setattr(world.mod, "execute", watch)
    req = world.pause_request()
    receipt = world.run(req)
    assert seen["armed_before_pause"] is True and receipt["status"] == "FAILED"
    world.cloud.state = "PAUSED"                                              # the pause call had gone through before the crash
    assert world.mod.scheduler_backstop_tick(utc_now() + dt.timedelta(hours=3)) == [req["operation_id"]] and world.cloud.state == "ENABLED"


def test_c4_a_pause_that_cannot_be_backed_up_does_not_run(world):
    world.monkeypatch.setattr(world.mod, "SCHEDULER_BACKSTOP", world.mod.KY_ROOT / "not-a-dir" / "x")
    (world.mod.KY_ROOT / "not-a-dir").write_text("a file where the directory should be")
    receipt = world.run(world.pause_request())
    assert receipt["status"] == "FAILED" and world.cloud.state == "ENABLED" and world.cloud.verbs() == []


def test_c4_a_verified_resume_cancels_the_backstop_and_keeps_the_evidence(world):
    req = world.pause_request()
    world.run(req)
    resume = world.run(world.request("scheduler_resume", {}))
    assert resume["status"] == "COMPLETED"
    assert world.backstops()[req["operation_id"]]["status"] == "SATISFIED" and world.backstops()[req["operation_id"]]["satisfied_by"] == resume["operation_id"]
    calls = len(world.cloud.calls)
    assert world.mod.scheduler_backstop_tick(utc_now() + dt.timedelta(days=1)) == [] and len(world.cloud.calls) == calls


def test_c4_a_resume_that_did_not_read_back_enabled_does_not_cancel_the_backstop(world):
    req = world.pause_request()
    world.run(req)
    world.cloud.stuck = True
    assert world.run(world.request("scheduler_resume", {}))["status"] == "FAILED"
    assert world.backstops()[req["operation_id"]]["status"] == "ARMED"


def test_c4_a_failing_backstop_keeps_the_record_armed_and_retries_with_back_off(world):
    due = utc_now() + dt.timedelta(hours=1)
    req = world.pause_request(resume_by=due)
    world.run(req)
    world.cloud.stuck = True
    assert world.mod.scheduler_backstop_tick(due) == []
    first = world.backstops()[req["operation_id"]]
    assert first["status"] == "ARMED" and first["attempts"] == 1 and first["next_attempt_at"] > stamp(due).replace("Z", "+00:00")
    calls = len(world.cloud.calls)
    assert world.mod.scheduler_backstop_tick(due + dt.timedelta(seconds=5)) == [] and len(world.cloud.calls) == calls      # backing off, not hammering
    world.cloud.stuck = False
    assert world.mod.scheduler_backstop_tick(due + dt.timedelta(minutes=30)) == [req["operation_id"]] and world.cloud.state == "ENABLED"


# ───────────────────────────── C5 dry runs never call the scheduler ─────────────────────────────
@pytest.mark.parametrize("action,extra", [("pause", ["--resume-by", stamp(utc_now() + dt.timedelta(hours=1))]), ("resume", [])])
def test_c5_a_dry_run_makes_no_external_call_and_reports_the_plan(action, extra):
    out = io.StringIO()
    rc = reaper.main(["--action", action, "--dry-run", *extra], environ={}, runner=Forbidden(), fetch=Forbidden(), out=out)
    record = json.loads(out.getvalue())
    assert rc == 0 and record["status"] == "DRY_RUN" and record["gcloud_calls"] == 0 and record["state"] is None and record["changed"] is False
    assert [c[3] for c in record["plan"]] == ["describe", action, "describe"]


def test_c5_the_executor_refuses_a_dry_run_record_that_admits_a_call(world):
    req = world.request("scheduler_resume_dryrun", {})
    ok = reaper.run("resume", True, None, None, {"KY_OPERATION_REQUEST": json.dumps(req)}, runner=Forbidden())[1]
    assert world.mod.scheduler_proof(req, 0, json.dumps(ok)) == (ok, None)
    for field, value in (("gcloud_calls", 1), ("state", "ENABLED"), ("changed", True)):
        assert world.mod.scheduler_proof(req, 0, json.dumps(dict(ok, **{field: value})))[1], field
    receipt = world.run(req)
    assert receipt["status"] == "COMPLETED" and receipt["scheduler"]["gcloud_calls"] == 0 and world.cloud.calls == []


def test_c5_a_dry_run_pause_arms_nothing(world):
    receipt = world.run(world.request("scheduler_pause_dryrun", {"resume-by": stamp(utc_now() + dt.timedelta(hours=1))}))
    assert receipt["status"] == "COMPLETED" and world.backstops() == {} and world.cloud.calls == []


# ───────────────────────────── C6 permission + identity check ─────────────────────────────
def test_c6_readback_reports_granted_and_missing_permissions_and_the_principal_never_a_token():
    cloud = FakeCloud("PAUSED", granted=["cloudscheduler.jobs.get", "cloudscheduler.jobs.resume"])
    out = io.StringIO()
    assert reaper.main(["--action", "readback"], environ={}, runner=cloud, fetch=cloud.fetch, out=out) == 0
    text = out.getvalue(); record = json.loads(text)
    assert SECRET_TOKEN not in text and "ya29" not in text
    assert record["state"] == "PAUSED" and record["status"] == "MEASURED" and record["identity"]["principal"] == PRINCIPAL
    p = record["permissions"]
    assert p["status"] == "MEASURED" and p["requested"] == ["cloudscheduler.jobs.pause", "cloudscheduler.jobs.resume", "cloudscheduler.jobs.get", "run.executions.cancel"]
    assert p["granted"] == ["cloudscheduler.jobs.resume", "cloudscheduler.jobs.get"] and p["missing"] == ["cloudscheduler.jobs.pause", "run.executions.cancel"]
    assert cloud.fetches == [(reaper.PERMISSION_ENDPOINT, {"permissions": list(reaper.PERMISSIONS)})]
    assert not {"pause", "resume"} & set(cloud.verbs())                      # read-only: no mutating verb in a readback


def test_c6_an_unmeasurable_permission_check_is_unavailable_never_green():
    cloud = FakeCloud("ENABLED", fetch_fails=True)
    rc, record = run_script("readback", cloud)
    assert rc == 0 and record["permissions"]["status"] == "UNAVAILABLE" and record["permissions"]["granted"] is None and record["permissions"]["missing"] is None


def test_c6_a_denied_describe_still_reports_identity_and_permissions_with_a_null_state():
    cloud = FakeCloud("ENABLED", granted=[], describe_fails=True)
    rc, record = run_script("readback", cloud)
    assert rc == 0 and record["status"] == "PARTIAL" and record["state"] is None and record["identity"]["principal"] == PRINCIPAL
    assert record["permissions"]["missing"] == list(reaper.PERMISSIONS)


def test_c6_the_executor_accepts_a_partial_readback_only_with_a_null_state(world):
    req = world.request("scheduler_readback", {})
    cloud = FakeCloud("ENABLED", describe_fails=True)
    partial = reaper.run("readback", False, None, None, {"KY_OPERATION_REQUEST": json.dumps(req)}, runner=cloud, fetch=cloud.fetch)[1]
    assert partial["status"] == "PARTIAL" and world.mod.scheduler_proof(req, 0, json.dumps(partial))[1] is None
    assert world.mod.scheduler_proof(req, 0, json.dumps(dict(partial, state="ENABLED")))[1]


# ───────────────────────────── C7 the backstop survives an executor restart ─────────────────────────────
class StopLoop(Exception):
    pass


def run_main_one_turn(w, monkeypatch):
    """Run the real main() until its first sleep, with the network and the table-on-main doubled."""
    def stop(_seconds): raise StopLoop()
    monkeypatch.setattr(w.mod.time, "sleep", stop)
    monkeypatch.setattr(w.mod, "refresh_from_main_or_fail_closed", lambda: True)
    with pytest.raises(StopLoop):
        w.mod.main()


def test_c7_pause_then_a_fresh_process_still_resumes_at_resume_by(tmp_path, monkeypatch):
    due = utc_now() + dt.timedelta(hours=2)
    first = World(tmp_path, monkeypatch, name="ky_exec_first")
    req = first.pause_request(resume_by=due)
    first.run(req)
    assert first.cloud.state == "PAUSED"
    second = World(tmp_path, monkeypatch, cloud=first.cloud, name="ky_exec_restarted")        # a new process: fresh module state, same durable root
    assert second.mod is not first.mod and second.backstops()[req["operation_id"]]["status"] == "ARMED"
    assert second.mod.scheduler_backstop_tick(due - dt.timedelta(seconds=1)) == [] and second.cloud.state == "PAUSED"
    assert second.mod.scheduler_backstop_tick(due) == [req["operation_id"]] and second.cloud.state == "ENABLED"


def test_c7_an_overdue_record_fires_on_the_first_turn_of_the_main_loop_even_under_hold(tmp_path, monkeypatch):
    due = utc_now() + dt.timedelta(minutes=30)
    first = World(tmp_path, monkeypatch, name="ky_exec_before")
    req = first.pause_request(resume_by=due)
    first.run(req)
    path = first.mod.SCHEDULER_BACKSTOP / f"{req['operation_id']}.json"
    record = json.loads(path.read_text())
    path.write_text(json.dumps(dict(record, resume_by=stamp(utc_now() - dt.timedelta(hours=1)).replace("Z", "+00:00"))))       # the executor was down past resume-by
    restarted = World(tmp_path, monkeypatch, cloud=first.cloud, name="ky_exec_after")
    (restarted.mod.KY_ROOT / "HOLD").write_text("hold")                     # HOLD (and a table that never loads) must not stop a due resume
    monkeypatch.setattr(restarted.mod, "load_table", lambda: None)
    run_main_one_turn(restarted, monkeypatch)
    assert restarted.cloud.state == "ENABLED" and restarted.backstops()[req["operation_id"]]["status"] == "FIRED"


# ───────────────────────────── C8 a resume is not held by the production fence ─────────────────────────────
def test_c8_the_fence_holds_a_pause_but_never_a_resume(tmp_path, monkeypatch):
    w = World(tmp_path, monkeypatch)
    ran, finished = [], threading.Event()
    def fake_run_one(path, req, op):
        ran.append(req["kind"]); finished.set()
    monkeypatch.setattr(w.mod, "run_one", fake_run_one)
    monkeypatch.setattr(w.mod, "validate", lambda *a, **k: None)
    monkeypatch.setattr(w.mod, "mark_seen", lambda *a: None)
    w.mod.FENCE.write_text(json.dumps({"operation_id": "some-dispatch", "request_sha256": "0" * 64}))
    for kind, args in (("scheduler_pause", {"resume-by": stamp(utc_now() + dt.timedelta(hours=1))}), ("scheduler_resume", {})):
        (w.mod.REQ / f"{kind}.json").write_text(json.dumps(w.request(kind, args, oid=kind)))
    run_main_one_turn(w, monkeypatch)
    assert finished.wait(5)
    assert ran == ["scheduler_resume"] and (w.mod.REQ / "scheduler_pause.json").exists()


# ───────────────────────────── C9 the receipt binds operation, request and job ─────────────────────────────
def test_c9_the_script_digest_equals_the_executors_for_the_same_request(world):
    req = world.pause_request()
    req.update(task_expires_at="2030-01-01T00:00:00Z", acceptance_receipt="/x", weird={"b": [1, 2], "a": None})
    assert reaper.request_digest(req) == world.mod.request_digest(req)


def test_c9_a_record_for_another_operation_request_job_or_action_is_not_this_receipt(world):
    req = world.request("scheduler_resume", {})
    good = reaper.run("resume", False, None, None, {"KY_OPERATION_REQUEST": json.dumps(req)}, runner=FakeCloud("PAUSED"))[1]
    assert world.mod.scheduler_proof(req, 0, json.dumps(good)) == (good, None)
    for field, value in (("operation_id", "someone-else"), ("request_sha256", "0" * 64), ("job", "brahma-build-pipeline-job"),
                         ("project", "other-project"), ("region", "us-central1"), ("action", "pause")):
        proof, problem = world.mod.scheduler_proof(req, 0, json.dumps(dict(good, **{field: value})))
        assert proof is None and problem, field
    assert world.mod.scheduler_proof(req, 0, "no record here")[0] is None
    assert world.mod.scheduler_proof(req, 0, json.dumps(good) + "\n" + json.dumps(good))[0] is None      # not unique


def test_c9_a_receipt_whose_record_binds_nothing_is_failed_even_at_exit_zero(world):
    world.monkeypatch.setattr(world.mod, "execute", lambda req, op: (0, json.dumps({"schema": "ky.scheduler_job/1", "status": "OK", "state": "ENABLED"})))
    receipt = world.run(world.request("scheduler_resume", {}))
    assert receipt["status"] == "FAILED" and "scheduler record" in receipt["reason"]


# ───────────────────────────── structure ─────────────────────────────
def test_the_scheduler_kinds_are_exactly_bound_and_hold_no_database_credential():
    assert [k for k in TABLE if k.startswith("scheduler_")] == KINDS
    for kind in KINDS:
        op = TABLE[kind]
        assert op["needs"] == "gcloud" and op["script"] == "00_ARCHITECTURE/briefs/kalayantra/fleet/scheduler_reaper.py" and "also_needs" not in op
        assert op["production"] is (kind in ("scheduler_pause", "scheduler_resume")) and op["enabled_by"] == "J-3c"
        assert op.get("remote_async") is None and "required_rows" not in op                                # synchronous: never takes the fence
    assert TABLE["scheduler_readback"]["read_only"] is True and all("read_only" not in TABLE[k] for k in KINDS[1:])
    source = SCRIPT.read_text()
    assert not re.search(r"^\s*(?:import|from)\s+(?:psycopg|sqlalchemy|sqlite3|asyncpg)", source, re.M) and "DATABASE_URL" not in source


def test_the_lane_rehearsal_route_is_closed_to_scheduler_kinds(world):
    req = world.request("scheduler_pause_dryrun", {"resume-by": stamp(utc_now() + dt.timedelta(hours=1))})
    req.update(lane_target={"host": "127.0.0.1", "port": 55433, "database": "ky_lane"}, dry_run=True, request_id="r1")
    assert world.validate(req) == "operation has no reviewed lane binding"
