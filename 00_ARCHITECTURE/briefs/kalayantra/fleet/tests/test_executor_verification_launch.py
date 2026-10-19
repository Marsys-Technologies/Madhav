"""J-4b (SR-PREBUILD-ALL): the `verification_job` launcher and its `verification_job_dryrun` sibling (fleet/verification_launch.py).

One doctrine-grounded oracle per distinct production claim; every cloud call is a stateful in-process fake (no gcloud, no network, no database, no git write).
Sources of the expected values: the workflows `.github/workflows/gochara-seal-approved.yml` (the one `gcloud run jobs execute` recipe, the 5.0-only refusal, the
"read the EXECUTED resource" step) and `gochara-verification-job-deploy.yml` (the job, identity, secret and Cloud SQL constants), the pinned task contract
`platform/scripts/gochara_verification_job_contract.py` (image@digest, exact args, maxRetries present and 0, no env override), smalltest_launch.py's claim discipline
(O_EXCL, fsynced before the remote call, never cleared), executor.py A8 §3.8 (a `*_dryrun` writes nothing) and the ruling SR-TEARDOWN-AUTHORITY-GATE item 2.
Distinct claims:
V1 the kind binds the mode: a dry run can never launch, a launch needs its own kind · V2 the request binds what is verified (chart, 5.0, merged-commit shape, one
argument, equal to the command line) · V3 the launch is exactly the seal workflow's execute recipe minus `--brief`, with constants equal to the workflows' ·
V4 an unconforming deployed definition refuses before any claim or launch (digest of reviewed_commit, identity, secret, retries, same-commit rule) ·
V5 the durable no-retry fence: claim before the remote call, never cleared, a second run refuses · V6 launch evidence: the execution is this job's, and the record
binds operation, request digest and execution · V7 the executed resource is judged and a nonconforming or unreadable one exits non-zero · V8 the dry run does the same
validation and writes no claim · V9 no credential value reaches an argv or an output · V10 the script runs standalone from the reviewed tree.
PR #3747 verify finding B3 (the dry run was a DEFINITION check, not a `--report-only` run, so the pack's dryrun_gate read NULL and its seconds-long wall time was a proxy for the cost):
R1 the dry run executes the job once in its own `--report-only` mode (the flag of pipeline/orchestrator/verification_job.py) and never in a persisting or sealing mode · R2 its output
carries exactly ONE report line, the job's own words byte for byte, which the pack's dryrun_gate selects and judges (verify/dryrun_gate.py: report_only true, status REPORT_ONLY), plus a
measured wall time · R3 the run is waited for and a failed, still-running, unreadable, report-less or non-REPORT_ONLY run is never a green · R4 the executed resource is judged with the
report-only arguments (a run that could persist is NONCONFORMING) · R5 a report split by Cloud Logging is joined only when complete.
"""
import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
WORKFLOWS = REPO / ".github" / "workflows"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


vl = load(FLEET / "verification_launch.py", "verification_launch_under_test")
reaper = sys.modules["scheduler_reaper"]

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
COMMIT = "b" * 40
DIGEST = "sha256:" + "a" * 64
REPO_IMAGE = "asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline"
SA = "gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com"
SECRET = "gochara-verifier-db-url"
INSTANCE = "madhav-astrology:asia-south1:amjis-postgres"
NAME = "gochara-verification-job-x7k2p"
TOKEN = "ya29.TOKEN-VALUE-NEVER-PRINTED"


def container(args):
    return {"image": f"{REPO_IMAGE}@{DIGEST}", "command": ["python", "-m", "pipeline.orchestrator.verification_job"], "args": list(args),
            "resources": {"limits": {"memory": "8Gi", "cpu": "2"}},
            "env": [{"name": "GOCHARA_RUNNER_COMMIT", "value": COMMIT}, {"name": "GOCHARA_RUNNER_IMAGE_DIGEST", "value": DIGEST},
                    {"name": "GOCHARA_VERIFIER_DB_URL", "valueFrom": {"secretKeyRef": {"name": SECRET, "key": "latest"}}}]}


def task(args):
    return {"serviceAccountName": SA, "maxRetries": 0, "timeoutSeconds": "28800", "containers": [container(args)]}


def job_v1():
    return {"metadata": {"name": "gochara-verification-job"},
            "spec": {"template": {"metadata": {"annotations": {"run.googleapis.com/cloudsql-instances": INSTANCE}},
                                  "spec": {"taskCount": 1, "template": {"spec": task([])}}}}}


def job_v2():
    return {"template": {"template": {"maxRetries": 0}}}


CLASSES = ("lagna_stretch", "dasha_sandhi", "transit_ingress")


def report_dict(**more):
    """The shape of vj.run's report (services/gochara_kernel/verification_job.py: run()): what a `--report-only` execution prints as its one stdout line."""
    report = {"chart_id": CHART, "generation": "5.0", "report_only": True, "status": "REPORT_ONLY", "exit_code": 0, "gate": [], "gate_outside_scope": [],
              "gate_source": "ka_gochara_candidate_gate_violations", "identity": {"separate": True},
              "classes": {c: {"event_class": c, "status": "VERIFIED"} for c in CLASSES}, "cockpit": "REPORT ONLY (nothing persisted) · combined gate: 0 violation(s)"}
    report.update(more)
    return report


def report_line(**more):
    return json.dumps(report_dict(**more), default=str, sort_keys=True)               # the job's own serialisation (verification_job._run)


def log_entry(text, insert_id, **more):
    return {"insertId": insert_id, "textPayload": text, "timestamp": "2026-10-19T10:41:41.000000Z", **more}


class Clock:
    """The injected sleep and monotonic clock: waiting costs nothing and is counted."""

    def __init__(self):
        self.now, self.sleeps = 0.0, []

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds

    def monotonic(self):
        return self.now


def execution_v1(name=NAME, args=vl.EXECUTE_ARGS):
    return {"metadata": {"name": name}, "spec": {"taskCount": 1, "template": {"spec": task(args)}}}


class Cloud:
    """A stateful stand-in for gcloud, the registry and the v2 REST read. Records every call; refuses to answer an unknown one."""

    def __init__(self):
        self.job, self.job_v2, self.digest = job_v1(), job_v2(), DIGEST
        self.execution, self.execution_v2, self.exec_name = execution_v1(), {"template": {"maxRetries": 0}}, NAME
        self.calls, self.fetches, self.launch_rc = [], [], 0
        self.report_only = False                                       # set by a `jobs execute ... --report-only`
        self.dry_execution = execution_v1(args=vl.REPORT_ONLY_ARGS)
        self.dry_execution["status"] = {"startTime": "2026-10-19T10:00:00.000000Z", "completionTime": "2026-10-19T10:41:40.500000Z", "succeededCount": 1,
                                       "conditions": [{"type": "Completed", "status": "True"}]}
        self.running_polls = 0                                         # describe answers RUNNING this many times before the final state
        self.never_completes = False
        self.log_entries = [log_entry(report_line(), "1")]
        self.log_calls, self.logs_lag = 0, 0                           # logs_lag: reads that return nothing yet (Cloud Logging lags a finished execution)

    def __call__(self, argv):
        self.calls.append(list(argv))
        done = lambda out="", rc=0: subprocess.CompletedProcess(argv, rc, out, "stderr-never-relayed")
        if argv[:5] == ["gcloud", "artifacts", "docker", "images", "describe"]:
            assert argv[5] == f"{REPO_IMAGE}:{COMMIT}", argv
            return done(json.dumps({"image_summary": {"digest": self.digest}}))
        if argv[:4] == ["gcloud", "run", "jobs", "describe"]:
            assert argv[4] == "gochara-verification-job", argv
            return done(json.dumps(self.job))
        if argv[:4] == ["gcloud", "run", "jobs", "execute"]:
            self.report_only = any(a.endswith(",--report-only") for a in argv)
            return done(self.exec_name + "\n", self.launch_rc)
        if argv[:5] == ["gcloud", "run", "jobs", "executions", "describe"]:
            assert argv[5] == self.exec_name, argv
            if not self.report_only:
                return done(json.dumps(self.execution))
            execution = copy.deepcopy(self.dry_execution)
            if self.never_completes or self.running_polls > 0:
                self.running_polls -= 1
                execution["status"] = {"startTime": "2026-10-19T10:00:00.000000Z", "runningCount": 1, "conditions": [{"type": "Completed", "status": "Unknown"}]}
            return done(json.dumps(execution))
        if argv[:3] == ["gcloud", "logging", "read"]:
            self.log_calls += 1
            return done(json.dumps(self.log_entries if self.log_calls > self.logs_lag else []))
        if argv == ["gcloud", "auth", "print-access-token"]:
            return done(TOKEN + "\n")
        raise AssertionError(f"unexpected call {argv}")

    def fetch(self, url, token):
        self.fetches.append((url, token))
        if url == vl.V2_JOB_URL:
            return copy.deepcopy(self.job_v2)
        if url == f"{vl.V2_JOB_URL}/executions/{self.exec_name}":
            return copy.deepcopy(self.execution_v2)
        raise AssertionError(f"unexpected url {url}")

    def writes(self):
        return [c for c in self.calls if c[:4] == ["gcloud", "run", "jobs", "execute"]]


def request(kind="verification_job", **more):
    req = {"operation_id": "op-verify-1", "kind": kind, "item_id": "J-5s", "idempotency_key": "k1", "requested_by": "adhikarin", "kyd": "KYD-1",
           "reviewed_commit": COMMIT, "chart_id": CHART, "args": {"generation": "5.0"}, "lease_id": "L1"}
    req.update(more)
    return req


def injected(tmp_path, cloud, req, launcher=None, clock=None):
    clock = clock or Clock()
    return dict(environ={"KY_OPERATION_REQUEST": json.dumps(req), "KY_ROOT": str(tmp_path)}, runner=cloud, fetch=cloud.fetch, claim_dir=tmp_path / "claims", launcher=launcher,
                sleep=clock.sleep, monotonic=clock.monotonic)


def go(tmp_path, cloud=None, req=None, argv=("--generation", "5.0"), launcher=None, dry=False, clock=None):
    cloud = cloud or Cloud()
    req = request("verification_job_dryrun" if dry else "verification_job") if req is None else req
    argv = list(argv) + (["--dry-run"] if dry else [])
    return cloud, vl.run(argv, **injected(tmp_path, cloud, req, launcher, clock)), tmp_path / "claims"


def cli_go(tmp_path, cloud, dry=False, clock=None):
    """The command-line entry on the same fakes: (exit code, stdout, stderr) as the executor would see them."""
    import contextlib
    import io
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = vl.cli(["--generation", "5.0"] + (["--dry-run"] if dry else []), **injected(tmp_path, cloud, request("verification_job_dryrun" if dry else "verification_job"), clock=clock))
    return rc, out.getvalue(), err.getvalue()


def gate_reports(output):
    """The pack's report selection (verify/gatelib.py reports_in, used by dryrun_gate.py): stdout lines that are JSON objects with a `classes` object and `generation`."""
    found = []
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict) and isinstance(value.get("classes"), dict) and "generation" in value:
                found.append(value)
    return found


# V1 ── the kind binds the mode ──────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("kind,dry", [("verification_job", True), ("verification_job_dryrun", False), ("measuring_dispatch", False), ("century_dispatch", True)])
def test_v1_a_request_of_another_kind_or_mode_refuses_before_any_cloud_call(tmp_path, kind, dry):
    cloud = Cloud()
    with pytest.raises(vl.Refused, match="is not a verification_job"):
        go(tmp_path, cloud, request(kind), dry=dry)
    assert cloud.calls == [] and not (tmp_path / "claims").exists()


# V2 ── the request binds what is verified ───────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("change,argv,needle", [
    ({"args": {"generation": "4.1"}}, ("--generation", "4.1"), "only verified generation"),              # the seal workflow: test "$GENERATION" = "5.0"
    ({"args": {"generation": "5.0"}}, ("--generation", "4.1"), "only verified generation"),              # command line and request must agree
    ({"args": {"generation": "4.1"}}, ("--generation", "5.0"), "only verified generation"),
    ({"args": {"generation": "5.0", "chart": "x"}}, ("--generation", "5.0"), "only verified generation"),  # the request cannot carry any other argument
    ({"args": {}}, ("--generation", "5.0"), "only verified generation"),
    ({"chart_id": "362f9f17-0000-0000-0000-000000000000"}, ("--generation", "5.0"), "canonical chart"),     # the dead phantom chart
    ({"reviewed_commit": "abc1234"}, ("--generation", "5.0"), "40-hex"),
    ({"operation_id": "../x"}, ("--generation", "5.0"), "unsafe"),
])
def test_v2_the_request_must_name_the_canonical_chart_generation_5_0_and_a_full_commit(tmp_path, change, argv, needle):
    cloud = Cloud()
    with pytest.raises(vl.Refused, match=needle):
        go(tmp_path, cloud, request(**change), argv=argv)
    assert cloud.calls == [] and not (tmp_path / "claims").exists()


def test_v2_a_production_request_without_a_chart_refuses_but_a_dry_run_may_omit_it(tmp_path):
    bare = request()
    del bare["chart_id"]
    with pytest.raises(vl.Refused, match="canonical chart"):
        go(tmp_path, Cloud(), bare)
    dry = request("verification_job_dryrun")
    del dry["chart_id"]
    assert go(tmp_path / "d", Cloud(), dry, dry=True)[1]["chart_id"] == CHART


# V3 ── the launch is the seal workflow's recipe, minus --brief ───────────────────────────────────────────────────────
def test_v3_the_launch_is_exactly_the_workflows_execute_recipe_for_the_verification_job_without_brief(tmp_path):
    cloud, record, _ = go(tmp_path)
    assert cloud.writes() == [["gcloud", "run", "jobs", "execute", "gochara-verification-job", "--project=madhav-astrology", "--region=asia-south1",
                               f"--args=--chart,{CHART},--generation,5.0", "--async", "--format=value(metadata.name)"]]
    joined = " ".join(cloud.writes()[0])
    for forbidden in ("--brief", "--sealing-commit", "--report-only", "--final-rules"):
        assert forbidden not in joined, forbidden
    seal = (WORKFLOWS / "gochara-seal-approved.yml").read_text()
    assert 'gcloud run jobs execute "$VERIFICATION_JOB" --project madhav-astrology --region "$GOOGLE_CLOUD_REGION"' in seal and "--async" in seal
    assert record["status"] == "LAUNCHED" and record["args"] == ["--chart", CHART, "--generation", "5.0"]


@pytest.mark.parametrize("workflow", ["gochara-seal-approved.yml", "gochara-verification-job-deploy.yml"])
def test_v3_the_constants_equal_the_workflows_env(workflow):
    text = (WORKFLOWS / workflow).read_text()
    env = dict(re.findall(r"^  ([A-Z_]+): (\S+)\s*(?:#.*)?$", text, re.M))
    assert env["VERIFICATION_JOB"] == vl.JOB and env["VERIFIER_SERVICE_ACCOUNT"] == vl.execchk.VERIFIER_SERVICE_ACCOUNT == SA
    assert env["VERIFIER_SECRET"] == vl.SECRET and env["CLOUDSQL_INSTANCE"] == vl.CLOUDSQL_INSTANCE
    assert env["PIPELINE_IMAGE_REPO"] == vl.readback.IMAGE_REPO and env["GOOGLE_CLOUD_REGION"] == vl.readback.REGION


# V4 ── an unconforming deployed definition refuses before any claim or launch ────────────────────────────────────────
def _other_digest(c):
    c.digest = "sha256:" + "c" * 64                                   # the registry holds another image for reviewed_commit than the job runs


def _other_account(c):
    c.job["spec"]["template"]["spec"]["template"]["spec"]["serviceAccountName"] = "data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com"


def _other_secret(c):
    c.job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["env"][2]["valueFrom"]["secretKeyRef"]["name"] = "data-plane-builder-db-url"


def _no_retries_anywhere(c):
    del c.job["spec"]["template"]["spec"]["template"]["spec"]["maxRetries"]
    c.job_v2 = {"template": {"template": {}}}                          # absent in both representations is a refusal, never zero


def _older_runner_commit(c):
    c.job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["env"][0]["value"] = "d" * 40


def _preset_args(c):
    c.job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["args"] = ["--brief"]


@pytest.mark.parametrize("mutate", [_other_digest, _other_account, _other_secret, _no_retries_anywhere, _older_runner_commit, _preset_args])
@pytest.mark.parametrize("dry", [False, True])
def test_v4_a_definition_that_is_not_the_reviewed_one_refuses_before_claim_and_launch(tmp_path, mutate, dry):
    cloud = Cloud()
    mutate(cloud)
    with pytest.raises(vl.Refused, match="verification job"):
        go(tmp_path, cloud, dry=dry)
    assert cloud.writes() == [] and not (tmp_path / "claims").exists()


def test_v4_an_unreadable_definition_or_digest_refuses(tmp_path):
    cloud = Cloud()
    cloud.digest = "latest"
    with pytest.raises(Exception, match="digest"):
        go(tmp_path, cloud)
    assert cloud.writes() == []


# V5 ── the durable no-retry fence ───────────────────────────────────────────────────────────────────────────────────
def test_v5_the_claim_exists_and_is_pending_before_the_remote_call_and_is_never_cleared(tmp_path):
    seen = {}
    claim = tmp_path / "claims" / "op-verify-1.json"

    def launcher():
        seen["claim"] = json.loads(claim.read_text())
        raise vl.Refused("remote launch failed or outcome unknown; reconcile the retained claim, never retry")

    with pytest.raises(vl.Refused, match="never retry"):
        go(tmp_path, launcher=launcher)
    assert seen["claim"]["status"] == "LAUNCH_PENDING" and seen["claim"]["execution_name"] is None
    assert json.loads(claim.read_text())["status"] == "LAUNCH_PENDING"          # a failed call leaves the fence in place
    cloud = Cloud()
    with pytest.raises(vl.Refused, match="already claimed"):
        go(tmp_path, cloud)                                                      # the same operation never launches twice
    assert cloud.writes() == []


def test_v5_a_remote_failure_or_a_timeout_leaves_the_claim_pending(tmp_path):
    cloud = Cloud()
    cloud.launch_rc = 1
    with pytest.raises(vl.Refused, match="never retry"):
        go(tmp_path, cloud)
    assert json.loads((tmp_path / "claims" / "op-verify-1.json").read_text())["status"] == "LAUNCH_PENDING"


# V6 ── launch evidence ──────────────────────────────────────────────────────────────────────────────────────────────
def test_v6_the_record_binds_operation_request_commit_digest_and_execution_and_equals_the_claim(tmp_path):
    req = request()
    cloud, record, claims = go(tmp_path, req=req)
    assert record["schema"] == "ky.verification_launch/1" and record["status"] == "LAUNCHED" and record["execution_name"] == NAME
    assert record["operation_id"] == "op-verify-1" and record["reviewed_commit"] == COMMIT and record["image_digest"] == DIGEST and record["chart_id"] == CHART
    bound = {k: v for k, v in req.items() if k not in reaper.UNBOUND_REQUEST_FIELDS and not k.endswith("_expires_at")}
    assert record["request_sha256"] == hashlib.sha256(json.dumps(bound, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    on_disk = json.loads((claims / "op-verify-1.json").read_text())
    assert on_disk == {k: v for k, v in record.items() if k != "plan"}


@pytest.mark.parametrize("wrong", ["brahma-build-pipeline-job-abc12", "gochara-verification-job", "gochara-verification-job-", "x"])
def test_v6_an_execution_of_another_job_or_no_identity_refuses_and_keeps_the_claim(tmp_path, wrong):
    cloud = Cloud()
    cloud.exec_name = wrong
    with pytest.raises(vl.Refused, match="identity absent or wrong job"):
        go(tmp_path, cloud)
    assert json.loads((tmp_path / "claims" / "op-verify-1.json").read_text())["status"] == "LAUNCH_PENDING"


# V7 ── the executed resource is judged ───────────────────────────────────────────────────────────────────────────────
def test_v7_a_conforming_executed_resource_is_conforms_and_exits_zero(tmp_path):
    rc, out, _ = cli_go(tmp_path, Cloud())
    assert rc == 0
    printed = json.loads(out)
    assert printed["executed_check"] == {"status": "CONFORMS", "problems": []}


def _extra_env(c):
    c.execution["spec"]["template"]["spec"]["containers"][0]["env"].append({"name": "PUBSUB_DISABLED", "value": "1"})


def _other_args(c):
    c.execution["spec"]["template"]["spec"]["containers"][0]["args"] = ["--chart", CHART, "--generation", "5.0", "--brief"]


def _wrong_image(c):
    c.execution["spec"]["template"]["spec"]["containers"][0]["image"] = f"{REPO_IMAGE}@sha256:{'e' * 64}"


@pytest.mark.parametrize("mutate", [_extra_env, _other_args, _wrong_image])
def test_v7_a_nonconforming_executed_resource_is_still_launched_but_exits_one(tmp_path, mutate):
    cloud = Cloud()
    mutate(cloud)
    rc, out, _ = cli_go(tmp_path, cloud)
    assert rc == 1
    printed = json.loads(out)
    assert printed["status"] == "LAUNCHED" and printed["executed_check"]["status"] == "NONCONFORMING" and printed["executed_check"]["problems"]


def test_v7_an_unreadable_executed_resource_is_unreadable_not_green(tmp_path):
    cloud = Cloud()
    cloud.execution = {"metadata": {"name": NAME}, "spec": {}}
    _, record, claims = go(tmp_path, cloud)
    assert record["status"] == "LAUNCHED" and record["executed_check"]["status"] == "UNREADABLE"
    assert json.loads((claims / "op-verify-1.json").read_text())["executed_check"]["status"] == "UNREADABLE"


# V8 ── the dry run: same validation, no claim, and the job in its own --report-only mode ────────────────────────────
def test_v8_the_dry_run_validates_reads_first_and_writes_no_claim(tmp_path):
    cloud, record, claims = go(tmp_path, dry=True)
    assert record["status"] == "DRY_RUN" and record["mode"] == "dry_run" and record["execution_name"] is None and record["executed_check"] is None
    assert record["definition_check"] == "CONFORMS" and record["image_digest"] == DIGEST and record["plan"] == {"execute": vl.execute_argv(vl.REPORT_ONLY_ARGS)}
    assert not claims.exists()
    first_execute = next(i for i, c in enumerate(cloud.calls) if c[:4] == ["gcloud", "run", "jobs", "execute"])
    assert all(tuple(c[:4]) in {("gcloud", "artifacts", "docker", "images"), ("gcloud", "run", "jobs", "describe"), ("gcloud", "auth", "print-access-token")} for c in cloud.calls[:first_execute])


# R1 ── the dry run IS the job's --report-only run ───────────────────────────────────────────────────────────────────
def test_r1_the_dry_run_executes_the_job_once_in_report_only_mode_and_never_in_a_persisting_or_sealing_mode(tmp_path):
    cloud, record, _ = go(tmp_path, dry=True)
    assert cloud.writes() == [["gcloud", "run", "jobs", "execute", "gochara-verification-job", "--project=madhav-astrology", "--region=asia-south1",
                               f"--args=--chart,{CHART},--generation,5.0,--report-only", "--async", "--format=value(metadata.name)"]]
    joined = " ".join(cloud.writes()[0])
    for forbidden in ("--brief", "--sealing-commit", "--final-rules", "--class"):
        assert forbidden not in joined, forbidden
    assert record["report_only_run"]["args"] == ["--chart", CHART, "--generation", "5.0", "--report-only"] and record["args"] == record["report_only_run"]["args"]
    assert vl.EXECUTE_ARGS == ("--chart", CHART, "--generation", "5.0")                  # the real launch still has no --report-only (it can never reach VERIFIED)


def test_r1_the_flag_is_the_one_the_job_entrypoint_defines():
    entry = (REPO / "platform/python-sidecar/pipeline/orchestrator/verification_job.py").read_text()
    kernel = (REPO / "platform/python-sidecar/services/gochara_kernel/verification_job.py").read_text()
    assert 'ap.add_argument("--report-only", action="store_true")' in entry and "persist=not report_only" in kernel
    assert vl.REPORT_ONLY_ARGS[-1] == "--report-only"


# R2 ── the output carries the job's report, the one the pack's gate judges, and a measured wall time ───────────────
def test_r2_the_output_is_the_record_then_exactly_one_report_which_is_the_jobs_line_byte_for_byte(tmp_path):
    cloud = Cloud()
    rc, out, err = cli_go(tmp_path, cloud, dry=True)
    assert rc == 0 and err == ""
    lines = out.splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["schema"] == "ky.verification_launch/1" and lines[1] == report_line()
    reports = gate_reports(out)
    assert len(reports) == 1 and reports[0]["report_only"] is True and reports[0]["status"] == "REPORT_ONLY" and reports[0]["generation"] == "5.0"
    assert set(reports[0]["classes"]) == set(CLASSES)
    ran = json.loads(lines[0])["report_only_run"]
    assert "report_line" not in ran and ran["report_sha256"] == hashlib.sha256(report_line().encode()).hexdigest() and ran["ok"] is True


def test_r2_the_record_carries_the_measured_wall_time_of_the_execution_and_of_the_wait(tmp_path):
    cloud, clock = Cloud(), Clock()
    cloud.running_polls = 3
    _, record, _ = go(tmp_path, cloud, dry=True, clock=clock)
    ran = record["report_only_run"]
    assert ran["start_time"] == "2026-10-19T10:00:00.000000Z" and ran["completion_time"] == "2026-10-19T10:41:40.500000Z"
    assert ran["execution_wall_s"] == 2500.5                                              # completionTime - startTime, read from the execution itself
    assert ran["waited_s"] == 3 * vl.POLL_INTERVAL_S == 90 and clock.sleeps == [vl.POLL_INTERVAL_S] * 3


def test_r2_a_definition_only_answer_carries_no_report_and_the_gate_would_refuse_it(tmp_path):
    cloud = Cloud()
    cloud.log_entries = [log_entry(json.dumps({"schema": "ky.verification_launch/1", "status": "DRY_RUN"}), "1")]       # what a definition check printed: a record, no report
    rc, out, _ = cli_go(tmp_path, cloud, dry=True)
    assert rc == 1 and gate_reports(out) == []
    assert "report_problem" in json.loads(out.splitlines()[0])["report_only_run"] and json.loads(out.splitlines()[0])["report_only_run"]["ok"] is False


# R3 ── the run is waited for and never a green when it did not finish as a clean report-only run ────────────────────
def test_r3_a_failed_execution_exits_one_even_though_its_report_is_printed(tmp_path):
    cloud = Cloud()
    cloud.dry_execution["status"] = {"startTime": "2026-10-19T10:00:00Z", "completionTime": "2026-10-19T10:30:00Z", "failedCount": 1, "conditions": [{"type": "Completed", "status": "False"}]}
    cloud.log_entries = [log_entry(report_line(status="DISAGREE", exit_code=3, classes={"lagna_stretch": {"status": "DISAGREE", "stage": "x", "detail": "y"}}), "1")]
    rc, out, _ = cli_go(tmp_path, cloud, dry=True)
    ran = json.loads(out.splitlines()[0])["report_only_run"]
    assert rc == 1 and ran["outcome"] == "FAILED" and ran["ok"] is False and len(gate_reports(out)) == 1


def test_r3_a_job_that_persisted_is_not_a_report_only_run(tmp_path):
    cloud = Cloud()
    cloud.log_entries = [log_entry(report_line(report_only=False, status="VERIFIED"), "1")]
    rc, out, _ = cli_go(tmp_path, cloud, dry=True)
    assert rc == 1 and json.loads(out.splitlines()[0])["report_only_run"]["ok"] is False


@pytest.mark.parametrize("entries,needle", [([], "0 verification reports"), ([log_entry(report_line(), "1"), log_entry(report_line(), "2")], "2 verification reports")])
def test_r3_no_report_or_two_reports_is_a_named_problem_and_exit_one(tmp_path, entries, needle):
    cloud = Cloud()
    cloud.log_entries = entries
    rc, out, _ = cli_go(tmp_path, cloud, dry=True)
    ran = json.loads(out.splitlines()[0])["report_only_run"]
    assert rc == 1 and needle in ran["report_problem"] and ran["report_line"] if "report_line" in ran else needle in ran["report_problem"]
    assert gate_reports(out) == []


def test_r3_a_log_that_lags_the_execution_is_re_read_a_bounded_number_of_times(tmp_path):
    cloud, clock = Cloud(), Clock()
    cloud.logs_lag = 3
    _, record, _ = go(tmp_path, cloud, dry=True, clock=clock)
    assert record["report_only_run"]["ok"] is True and cloud.log_calls == 4
    cloud2 = Cloud()
    cloud2.logs_lag = 99
    _, record2, _ = go(tmp_path / "b", cloud2, dry=True)
    assert record2["report_only_run"]["ok"] is False and cloud2.log_calls == vl.LOG_ATTEMPTS


def test_r3_an_execution_that_outlives_the_wait_budget_refuses_naming_it_and_the_cancel_is_not_made(tmp_path):
    cloud, clock = Cloud(), Clock()
    cloud.never_completes = True
    rc, out, err = cli_go(tmp_path, cloud, dry=True, clock=clock)
    assert rc == 1 and NAME in err and "still running" in err and out == ""
    assert clock.now >= vl.WAIT_BUDGET_S and vl.WAIT_BUDGET_S < 6 * 3600                  # under the executor's MAX_TIMEOUT, so the refusal is ours and names the execution
    assert [c for c in cloud.calls if "cancel" in c] == []


def test_r3_the_wait_budget_is_under_the_table_timeout_which_is_at_the_executors_cap():
    table = json.loads((FLEET / "executor_ops.json").read_text())["ops"]["verification_job_dryrun"]
    assert table["timeout_s"] == 21600 and vl.WAIT_BUDGET_S < table["timeout_s"] and re.search(r"MAX_TIMEOUT = 6 \* 3600", (FLEET / "executor.py").read_text())


def test_r3_a_launch_that_fails_or_names_another_job_refuses_without_a_claim(tmp_path):
    cloud = Cloud()
    cloud.launch_rc = 1
    with pytest.raises(vl.Refused, match="report-only launch failed"):
        go(tmp_path, cloud, dry=True)
    cloud = Cloud()
    cloud.exec_name = "brahma-build-pipeline-job-abc12"
    with pytest.raises(vl.Refused, match="identity absent or wrong job"):
        go(tmp_path, cloud, dry=True)
    assert not (tmp_path / "claims").exists()


# R4 ── the executed resource is judged with the report-only arguments ───────────────────────────────────────────────
def test_r4_an_execution_that_could_persist_is_nonconforming_and_the_dry_run_is_not_ok(tmp_path):
    cloud = Cloud()
    cloud.dry_execution["spec"]["template"]["spec"]["containers"][0]["args"] = list(vl.EXECUTE_ARGS)       # same job, no --report-only: a persisting run
    rc, out, _ = cli_go(tmp_path, cloud, dry=True)
    ran = json.loads(out.splitlines()[0])["report_only_run"]
    assert rc == 1 and ran["executed_check"]["status"] == "NONCONFORMING" and ran["ok"] is False


# R5 ── a split report is joined only when complete ───────────────────────────────────────────────────────────────────
def _split(text, uid, n):
    size = -(-len(text) // n)
    return [log_entry(text[i * size:(i + 1) * size], f"{uid}-{i}", split={"uid": uid, "index": i, "totalSplits": n}) for i in range(n)]


def test_r5_split_entries_are_joined_in_index_order_and_only_when_every_part_is_present(tmp_path):
    parts = _split(report_line(), "u1", 3)
    cloud = Cloud()
    cloud.log_entries = [parts[2], parts[0], parts[1]]                                       # newest first, as gcloud returns them
    _, record, _ = go(tmp_path, cloud, dry=True)
    assert record["report_only_run"]["ok"] is True and record["report_only_run"]["report_sha256"] == hashlib.sha256(report_line().encode()).hexdigest()
    cloud = Cloud()
    cloud.log_entries = [parts[2], parts[0]]                                                 # the middle part is missing: never guessed
    _, record, _ = go(tmp_path / "b", cloud, dry=True)
    assert record["report_only_run"]["ok"] is False and "incomplete" in record["report_only_run"]["report_problem"]


# V9 ── no credential value ──────────────────────────────────────────────────────────────────────────────────────────
def test_v9_the_access_token_reaches_only_the_v2_read_header(tmp_path):
    cloud = Cloud()
    rc, out, err = cli_go(tmp_path, cloud)
    assert rc == 0
    assert cloud.fetches and all(token == TOKEN for _, token in cloud.fetches)
    assert TOKEN not in out + err and not any(TOKEN in " ".join(call) for call in cloud.calls)
    assert TOKEN not in (tmp_path / "claims" / "op-verify-1.json").read_text()


def test_v9_a_failure_message_never_relays_gcloud_stderr(tmp_path):
    cloud = Cloud()
    cloud.launch_rc = 1
    rc, _, err = cli_go(tmp_path, cloud)
    assert rc == 1 and "never retry" in err and "stderr-never-relayed" not in err


# V10 ── standalone from the reviewed tree ───────────────────────────────────────────────────────────────────────────
def test_v10_the_script_runs_standalone_and_refuses_without_a_request(tmp_path):
    result = subprocess.run([sys.executable, str(FLEET / "verification_launch.py"), "--dry-run", "--generation", "5.0"], cwd=tmp_path,
                            capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path)}, timeout=60)
    assert result.returncode == 1 and "KY_OPERATION_REQUEST is missing" in result.stderr and "ModuleNotFoundError" not in result.stderr
