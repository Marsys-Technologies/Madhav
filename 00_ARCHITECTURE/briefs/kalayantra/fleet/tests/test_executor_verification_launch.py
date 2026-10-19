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
validation and no write · V9 no credential value reaches an argv or an output · V10 the script runs standalone from the reviewed tree.
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


def execution_v1(name=NAME, args=vl.EXECUTE_ARGS):
    return {"metadata": {"name": name}, "spec": {"taskCount": 1, "template": {"spec": task(args)}}}


class Cloud:
    """A stateful stand-in for gcloud, the registry and the v2 REST read. Records every call; refuses to answer an unknown one."""

    def __init__(self):
        self.job, self.job_v2, self.digest = job_v1(), job_v2(), DIGEST
        self.execution, self.execution_v2, self.exec_name = execution_v1(), {"template": {"maxRetries": 0}}, NAME
        self.calls, self.fetches, self.launch_rc = [], [], 0

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
            return done(self.exec_name + "\n", self.launch_rc)
        if argv[:5] == ["gcloud", "run", "jobs", "executions", "describe"]:
            assert argv[5] == self.exec_name, argv
            return done(json.dumps(self.execution))
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


def injected(tmp_path, cloud, req, launcher=None):
    return dict(environ={"KY_OPERATION_REQUEST": json.dumps(req), "KY_ROOT": str(tmp_path)}, runner=cloud, fetch=cloud.fetch, claim_dir=tmp_path / "claims", launcher=launcher)


def go(tmp_path, cloud=None, req=None, argv=("--generation", "5.0"), launcher=None, dry=False):
    cloud = cloud or Cloud()
    req = request("verification_job_dryrun" if dry else "verification_job") if req is None else req
    argv = list(argv) + (["--dry-run"] if dry else [])
    return cloud, vl.run(argv, **injected(tmp_path, cloud, req, launcher)), tmp_path / "claims"


def cli_go(tmp_path, cloud):
    """The command-line entry on the same fakes: (exit code, stdout, stderr) as the executor would see them."""
    import contextlib
    import io
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = vl.cli(["--generation", "5.0"], **injected(tmp_path, cloud, request()))
    return rc, out.getvalue(), err.getvalue()


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


# V8 ── the dry run: same validation, no write ───────────────────────────────────────────────────────────────────────
def test_v8_the_dry_run_validates_reads_and_prints_the_plan_but_writes_nothing(tmp_path):
    cloud, record, claims = go(tmp_path, dry=True)
    assert record["status"] == "DRY_RUN" and record["mode"] == "dry_run" and record["execution_name"] is None and record["executed_check"] is None
    assert record["definition_check"] == "CONFORMS" and record["image_digest"] == DIGEST and record["plan"] == {"execute": vl.execute_argv()}
    assert cloud.writes() == [] and not claims.exists()
    assert {tuple(c[:4]) for c in cloud.calls} <= {("gcloud", "artifacts", "docker", "images"), ("gcloud", "run", "jobs", "describe"), ("gcloud", "auth", "print-access-token")}


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
