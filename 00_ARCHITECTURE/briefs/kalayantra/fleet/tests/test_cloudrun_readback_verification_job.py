"""J-4b-a55j (SR-A55J-A55M-RESCOPE: "the config is measured by cloudrun_job_readback; no new executor kind"): `cloudrun_job_readback --job gochara-verification-job`.

The rescoped item must show the verification job is CONFIGURED BUT DISABLED. The measured part is the job definition; the `disabled` part is the executor table (`verification_job.enabled`)
and the absence of any execution/schedule, which this kind never starts. The single planted reversion per claim is named in brackets. No gcloud, credential, network or database is touched:
the runner is a double returning a job shaped from the flags `.github/workflows/gochara-verification-job-deploy.yml` deploys (NOT captured from a live response; the first real run proves the shape).

  V1 one fixed `gcloud run jobs describe gochara-verification-job` call and nothing else (no image, execution, logs or metrics call)      [VERIFICATION_JOB constant / an extra call]
  V2 the image is read BY DIGEST of the pipeline repository, and a tag reference is refused (this job runs only code built from a commit, by digest; deploy workflow `--image repo@digest`)   [IMAGE_BY_DIGEST]
  V3 the verifier's own runtime identity, the verifier entry point as the container command, and the one-secret-by-name environment are each CHECKED, each false when it differs        [per-field expected constants]
  V4 GOCHARA_RUNNER_IMAGE_DIGEST must equal the deployed image digest and GOCHARA_RUNNER_COMMIT must be a 40-hex commit (ST-WIRE-2: the verifier records both as the brief's producer)   [digest comparison]
  V5 no secret value and no non-contract variable value is ever printed                                                                                                            [environment()/withheld rows]
  V6 a field Cloud Run omits (proto3 zero maxRetries) reads NULL, never 0 and never a green                                                                                        [_count(...)/ok None]
  V7 `--job` takes only named jobs, adds `checks` only on the definition-alone read, and the executor table carries it as an allowed argument                                 [argparse choices / allowed_args]
  V8 the kind stays read-only and the record makes no claim about the executor table (main enabled `verification_job` under J-4b)                                                      [executor_ops.json]
  V9 the resources check demands the RULED 28,800 s task timeout (#3747 via #3789: "job task timeout 28,800 s in deploy, readback, seal check and launch preparation";
     PRECENTURY_PLAN §9 D-2, F-VERIFY-TIMEOUT): a job at 7,200 s reads false, and the reader's pin cannot drift from the seal check's constant, both deploy flags or the launch preparation
                                                                                                                                                                                  [VERIFIER_TIMEOUT_SECONDS = 7200]
"""
import copy
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "platform/scripts"))
import gochara_seal_execution_check as execchk  # noqa: E402  the one source of truth the deploy workflow, seal check and launch preparation share

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
SCRIPT = FLEET / "cloudrun_readback.py"
DEPLOY = REPO / ".github/workflows/gochara-verification-job-deploy.yml"
LAUNCH_PREP = REPO / "platform/scripts/prepare_gochara_verifier_launch.py"
RULED_TIMEOUT_SECONDS = 28800                         # #3747 via #3789; PRECENTURY_PLAN §9 D-2 (F-VERIFY-TIMEOUT)
SHA = "0123456789abcdef0123456789abcdef01234567"
DIGEST = "sha256:" + "cd" * 32
REPO_IMAGE = "asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline"
SQL = "madhav-astrology:asia-south1:amjis-postgres"
SA = "gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com"
VERIFIER_SECRET_ID = "gochara-verifier-db-url"

spec = importlib.util.spec_from_file_location("cloudrun_readback_verification_under_test", SCRIPT)
CR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CR)


def verification_job():
    return {
        "apiVersion": "run.googleapis.com/v1", "kind": "Job",
        "metadata": {"name": "gochara-verification-job", "labels": {"cloud.googleapis.com/location": "asia-south1"}},
        "spec": {"template": {"spec": {"taskCount": 1, "template": {
            "metadata": {"annotations": {"run.googleapis.com/cloudsql-instances": SQL}},
            "spec": {
                "containers": [{
                    "image": f"{REPO_IMAGE}@{DIGEST}",
                    "command": ["python", "-m", "pipeline.orchestrator.verification_job"],
                    "env": [
                        {"name": "GOCHARA_VERIFIER_DB_URL", "valueFrom": {"secretKeyRef": {"key": "latest", "name": "gochara-verifier-db-url"}}},
                        {"name": "GOCHARA_RUNNER_COMMIT", "value": SHA},
                        {"name": "GOCHARA_RUNNER_IMAGE_DIGEST", "value": DIGEST}],
                    "resources": {"limits": {"cpu": "2", "memory": "8Gi"}}}],
                "maxRetries": 0, "serviceAccountName": SA, "timeoutSeconds": str(execchk.JOB_TIMEOUT_SECONDS)}}}}},
    }


class Cloud:
    def __init__(self, job=None, rc=0):
        self.calls, self.job, self.rc = [], job if job is not None else verification_job(), rc

    def __call__(self, argv):
        self.calls.append(list(argv))
        return SimpleNamespace(returncode=self.rc, stdout=json.dumps(self.job), stderr="")


def measure(job=None):
    cloud = Cloud(job)
    return CR.measure_verification(cloud), cloud


def checks(record):
    return {c["name"]: c for c in record["checks"]}


def test_v1_one_fixed_describe_call_and_nothing_else():
    record, cloud = measure()
    assert cloud.calls == [["gcloud", "run", "jobs", "describe", "gochara-verification-job", "--project=madhav-astrology", "--region=asia-south1", "--format=json"]]
    assert record["schema"] == CR.SCHEMA and record["status"] == "MEASURED" and record["job"]["name"] == "gochara-verification-job"
    assert "gochara-verification-job" in DEPLOY.read_text() and "VERIFICATION_JOB: gochara-verification-job" in DEPLOY.read_text()      # the name is the one the deploy workflow defines


def test_v1_a_describe_of_another_job_is_refused():
    other = verification_job()
    other["metadata"]["name"] = "brahma-build-pipeline-job"
    with pytest.raises(CR.Refused, match="not 'gochara-verification-job'"):
        CR.measure_verification(Cloud(other))


def test_v2_the_image_is_read_by_digest_and_a_tag_reference_is_refused():
    record, _ = measure()
    assert record["job"]["image"] == {"reference": f"{REPO_IMAGE}@{DIGEST}", "tag": None, "digest": DIGEST} and checks(record)["image_by_digest_of_pipeline_repo"]["ok"] is True
    tagged = verification_job()
    tagged["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["image"] = f"{REPO_IMAGE}:{SHA}"
    with pytest.raises(CR.Refused, match="a tag or another repository is refused"):
        CR.measure_verification(Cloud(tagged))


@pytest.mark.parametrize("mutate,name", [
    (lambda c, t: t.__setitem__("serviceAccountName", "data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com"), "service_account_is_the_verifier_runtime"),
    (lambda c, t: c.__setitem__("command", ["python", "-m", "pipeline.orchestrator.main"]), "command_is_the_verifier_entry_point"),
    (lambda c, t: c["env"].append({"name": "DATABASE_URL", "valueFrom": {"secretKeyRef": {"key": "latest", "name": "data-plane-builder-db-url"}}}), "environment_is_exactly_the_contract"),
    (lambda c, t: c["env"][0]["valueFrom"]["secretKeyRef"].__setitem__("name", "data-plane-builder-db-url"), "environment_is_exactly_the_contract"),
    (lambda c, t: c["resources"]["limits"].__setitem__("memory", "16Gi"), "resources_8Gi_2cpu_28800s"),
])
def test_v3_each_identity_entry_point_and_environment_field_is_checked(mutate, name):
    job = verification_job()
    task = job["spec"]["template"]["spec"]["template"]["spec"]
    mutate(task["containers"][0], task)
    record, _ = measure(job)
    assert checks(record)[name]["ok"] is False and record["all_checks_ok"] is False
    base, _ = measure()
    assert checks(base)[name]["ok"] is True and base["all_checks_ok"] is True                       # control: the contract-shaped job passes every check it can measure


def test_v4_the_runner_digest_variable_must_equal_the_deployed_digest_and_the_commit_be_40_hex():
    job = verification_job()
    env = job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["env"]
    env[2]["value"] = "sha256:" + "ef" * 32
    record, _ = measure(job)
    assert checks(record)["runner_digest_equals_image_digest"]["ok"] is False
    env[2]["value"] = DIGEST
    env[1]["value"] = "main"
    record, _ = measure(job)
    assert checks(record)["runner_commit_is_a_full_commit"]["ok"] is False


def test_v5_no_secret_or_non_contract_value_reaches_the_output():
    job = verification_job()
    env = job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["env"]
    env.append({"name": "SOME_API_TOKEN", "value": "must-never-appear-in-output"})
    record, _ = measure(job)
    text = json.dumps(record)
    assert "must-never-appear-in-output" not in text
    assert checks(record)["environment_is_exactly_the_contract"]["ok"] is False
    secret = next(e for e in record["job"]["environment"] if e["name"] == "GOCHARA_VERIFIER_DB_URL")
    # name and version only; the Secret Manager id is held in a constant so the line is not a quoted key/value literal
    assert secret == {"name": "GOCHARA_VERIFIER_DB_URL", "source": "secret", "secret": VERIFIER_SECRET_ID, "version": "latest"}


def test_v6_an_omitted_max_retries_reads_null_not_zero_and_not_green():
    job = verification_job()
    del job["spec"]["template"]["spec"]["template"]["spec"]["maxRetries"]
    record, _ = measure(job)
    row = checks(record)["max_retries_is_zero"]
    assert row["observed"] is None and row["ok"] is None and record["all_checks_ok"] is None        # unknown is not true; the v2 REST read (runbook F-R15-3) settles it
    present, _ = measure()
    assert checks(present)["max_retries_is_zero"]["ok"] is True


def test_v7_the_cli_takes_only_named_jobs_and_checks_appear_only_on_the_definition_alone_read(capsys):
    cloud = Cloud()
    assert CR.cli(["--job", "gochara-verification-job"], runner=cloud) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["job"]["name"] == "gochara-verification-job" and out["all_checks_ok"] is True and len(cloud.calls) == 1
    for argv in (["--job", "nope"], ["--job", "brahma-build-pipeline-job-abc12"]):
        with pytest.raises(SystemExit) as stop:
            CR.cli(argv, runner=Cloud())
        assert stop.value.code == 2                                                                   # an unlisted name exits 2 before any cloud call
    cloud = Cloud()
    assert CR.cli(["--job", "gochara-verification-job", "--execution", "gochara-verification-job-abc12"], runner=cloud) == 1     # main's reader: the job record, here refused by the stub's missing execution call
    assert "checks" not in json.loads(capsys.readouterr().out)                                       # `checks` belong to the definition-alone read only
    entry = json.loads((FLEET / "executor_ops.json").read_text())["ops"]["cloudrun_job_readback"]
    assert "job" in entry["allowed_args"]


def test_v7_end_to_end_through_the_script_with_a_stub_gcloud(tmp_path):
    stub = tmp_path / "gcloud"
    payload = tmp_path / "job.json"
    payload.write_text(json.dumps(verification_job()))
    stub.write_text(f"#!/bin/sh\ncat {payload}\n")
    stub.chmod(0o755)
    done = subprocess.run([sys.executable, str(SCRIPT), "--job", "gochara-verification-job"], capture_output=True, text=True, timeout=60,
                          env={"PATH": f"{tmp_path}:/usr/bin:/bin", "HOME": str(tmp_path)})
    out = json.loads(done.stdout)
    assert done.returncode == 0 and out["status"] == "MEASURED" and out["all_checks_ok"] is True


def test_v8_the_kind_is_read_only():
    ops = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
    assert ops["cloudrun_job_readback"]["read_only"] is True and ops["cloudrun_job_readback"]["production"] is False
    # (I) INTERPRETATION: the PR's "verification_job stays disabled" half is obsolete on main (J-4b enabled it for the launch lane); this reader never reads the table and no longer claims it.
    assert "disabled_half" not in measure()[0]


def test_v9_the_resources_check_demands_the_ruled_28800_s_timeout_and_a_7200_s_job_reads_false():
    base, _ = measure()
    row = checks(base)["resources_8Gi_2cpu_28800s"]
    assert row["observed"] == {"memory": "8Gi", "cpu": "2", "timeout_seconds": RULED_TIMEOUT_SECONDS} and row["ok"] is True and base["all_checks_ok"] is True
    old = verification_job()
    old["spec"]["template"]["spec"]["template"]["spec"]["timeoutSeconds"] = "7200"                    # the value #3802 expected before the ruling was applied to it
    record, _ = measure(old)
    assert checks(record)["resources_8Gi_2cpu_28800s"]["ok"] is False and record["all_checks_ok"] is False


def test_v9_the_timeout_pins_cannot_drift_from_the_seal_checks_constant():
    assert execchk.JOB_TIMEOUT_SECONDS == RULED_TIMEOUT_SECONDS
    assert (CR.VERIFIER_MEMORY, CR.VERIFIER_CPU, CR.VERIFIER_TIMEOUT_SECONDS) == (execchk.JOB_MEMORY, execchk.JOB_CPU, execchk.JOB_TIMEOUT_SECONDS)
    deploy = DEPLOY.read_text()
    assert [int(v) for v in re.findall(r"--task-timeout (\d+)", deploy)] == [execchk.JOB_TIMEOUT_SECONDS]          # gcloud run jobs deploy
    assert [int(v) for v in re.findall(r"--timeout-seconds (\d+)", deploy)] == [execchk.JOB_TIMEOUT_SECONDS]       # the post-deploy definition readback
    assert re.findall(r"--memory (\S+)", deploy) == [execchk.JOB_MEMORY] * 2 and re.findall(r"--cpu (\S+)", deploy) == [execchk.JOB_CPU] * 2
    assert [int(v) for v in re.findall(r"timeout_seconds=(\d+)", LAUNCH_PREP.read_text())] == [execchk.JOB_TIMEOUT_SECONDS]
