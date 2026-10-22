"""W3W4 pack verify E2: `cloudrun_job_readback` reads the VERIFICATION Cloud Run job through the optional `job` argument.

No gcloud, credential, network or database is touched: the script's `runner` is a double returning documents shaped like the Cloud Run v1 Job/Execution resources
(tests/fixtures/cloudrun_readback/, adapted below to what .github/workflows/gochara-verification-job-deploy.yml deploys: the SAME pipeline repository, by IMMUTABLE DIGEST,
entry point overridden, `--max-retries 0`, `--task-timeout`, the one secret `GOCHARA_VERIFIER_DB_URL`, plain `GOCHARA_RUNNER_COMMIT` / `GOCHARA_RUNNER_IMAGE_DIGEST`, 8Gi / 2 cpu).
Distinct production claims, one doctrine-grounded oracle each:
J1 the kind accepts the `job` argument and nothing else new (the real `validate`): accepted shape, unknown argument refused · J2 only the two named jobs exist (anything else exits 2
before a cloud call) and an execution name must belong to the chosen job · J3 the verification job's definition is measured: name, immutable digest reference (a tag is refused),
timeout, retries, service account, environment with the credential shown by NAME only · J4 the runner identity variables are shown ONLY in their public-identifier shape ·
J5 an execution is judged against the chosen job (a pipeline execution under `--job gochara-verification-job` refuses) · J6 `logs true` on the verification job yields its ONE final
report only when exactly one well-formed report was read from a complete read, else null beside the counts · J7 the default (no `job`) record, calls and log filter are the pipeline job's, unchanged (the 113 pre-existing readback oracles pin the rest).
The pack's gates read exactly these record fields (PACK/verify/job_gate.py, image_gate.py runner_commit, close_gate.py logs.report), so the J3/J4/J6 oracles name them.
"""
import datetime as dt
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
FIX = HERE / "fixtures" / "cloudrun_readback"

spec = importlib.util.spec_from_file_location("cloudrun_readback_job_arg_under_test", FLEET / "cloudrun_readback.py")
CR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CR)

VJOB = "gochara-verification-job"
VEXEC = "gochara-verification-job-abc12"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
DIGEST = "sha256:" + "ab" * 32
REF = f"{CR.IMAGE_REPO}@{DIGEST}"
SERVICE_ACCOUNT = "gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com"
OPS = json.loads((FLEET / "executor_ops.json").read_text())["ops"]


def fixture(name):
    return json.loads((FIX / f"{name}.json").read_text())


def verification_job(**overrides):
    job = fixture("job")
    job["metadata"]["name"] = VJOB
    task = job["spec"]["template"]["spec"]["template"]["spec"]
    container = task["containers"][0]
    container["image"] = REF
    container["env"] = [
        {"name": "GOCHARA_RUNNER_COMMIT", "value": COMMIT},
        {"name": "GOCHARA_RUNNER_IMAGE_DIGEST", "value": DIGEST},
        {"name": "GOCHARA_VERIFIER_DB_URL", "valueFrom": {"secretKeyRef": {"key": "latest", "name": "gochara-verifier-db-url"}}},
    ]
    container["resources"] = {"limits": {"cpu": "1", "memory": "4Gi"}}
    task.update(maxRetries=0, serviceAccountName=SERVICE_ACCOUNT, timeoutSeconds="28800")
    job.update(overrides)
    return job


def verification_execution(name=VEXEC, job=VJOB, state="done"):
    execution = fixture("execution_succeeded")
    execution["metadata"]["name"] = name
    execution["metadata"]["labels"]["run.googleapis.com/job"] = job
    execution["spec"]["template"]["spec"]["containers"][0]["image"] = REF
    execution["spec"]["template"]["spec"]["containers"][0].pop("args", None)
    if state == "running":
        execution["status"] = {"startTime": "2026-10-17T10:01:00Z", "conditions": [{"type": "Completed", "status": "Unknown"}], "runningCount": 1}
    return execution


REPORT = {"classes": {"marriage": {"status": "VERIFIED"}, "career": {"status": "VERIFIED"}}, "generation": "5.0", "status": "VERIFIED", "exit_code": 0}


def log_entry(text, n, when="2026-10-17T11:00:00.000000Z"):
    return {"insertId": f"i{n}", "timestamp": when, "textPayload": text,
            "labels": {"run.googleapis.com/execution_name": VEXEC}, "resource": {"type": "cloud_run_job", "labels": {"job_name": VJOB, "location": "asia-south1"}}}


class Cloud:
    """`gcloud` double: answers by the fixed argv and records every call. Registry describe is never expected for the verification job."""

    def __init__(self, job=None, execution=None, logs=None, calls=None):
        self.calls = [] if calls is None else calls
        self.answers = {"jobs describe": job if job is not None else verification_job(),
                        "executions describe": execution if execution is not None else verification_execution(),
                        "logging read": logs if logs is not None else [log_entry(json.dumps(REPORT, sort_keys=True), 1)]}

    def __call__(self, argv):
        self.calls.append(list(argv))
        key = next(k for k in self.answers if k in " ".join(argv))
        return SimpleNamespace(returncode=0, stdout=json.dumps(self.answers[key]), stderr="")


# ───────────── J1 the kind accepts `job`, validated by the real executor ─────────────

def test_j1_the_table_lets_a_readback_request_carry_job_and_nothing_else_new():
    assert OPS["cloudrun_job_readback"]["allowed_args"] == ["execution", "logs", "metrics", "job"]
    assert OPS["cloudrun_job_readback"]["production"] is False and OPS["cloudrun_job_readback"]["read_only"] is True      # read-only: it has no dry-run twin and needs none


@pytest.mark.parametrize("args,expected", [
    ({"job": VJOB}, None),
    ({"job": VJOB, "execution": VEXEC}, None),
    ({"job": VJOB, "execution": VEXEC, "logs": "true"}, None),
    ({"jobs": VJOB}, "disallowed args ['jobs']"),
    ({"job": VJOB, "region": "us-east1"}, "disallowed args ['region']"),
    ({"project": "other"}, "disallowed args ['project']"),
])
def test_j1_validate_admits_the_accepted_shape_and_refuses_an_unknown_argument(tmp_path, monkeypatch, args, expected):
    from test_executor_scheduler_reaper import ALL_CAPS, World
    w = World(tmp_path, monkeypatch)
    monkeypatch.setattr(w.mod, "load_table", lambda: OPS)
    req = {"operation_id": "op-readback", "idempotency_key": "op-readback", "item_id": "J-5s", "kind": "cloudrun_job_readback", "requested_by": "v1", "kyd": "KYD-FIXTURE",
           "args": args, "reviewed_commit": "a" * 40}
    assert w.mod.validate(req, OPS, ALL_CAPS) == expected


# ───────────── J2 only the two named jobs; an execution must belong to the chosen job ─────────────

@pytest.mark.parametrize("argv", [["--job", "watchdog-reaper"], ["--job", ""], ["--job", "brahma-build-pipeline-job-abc12"], ["--job", "gochara-verification-job;x"]])
def test_j2_an_unlisted_job_exits_before_any_cloud_call(argv):
    cloud = Cloud()
    with pytest.raises(SystemExit) as caught:
        CR.cli(argv, cloud)
    assert caught.value.code == 2 and cloud.calls == []


@pytest.mark.parametrize("job,name", [(VJOB, "brahma-build-pipeline-job-abc12"), ("brahma-build-pipeline-job", VEXEC), (VJOB, "gochara-verification-job-"),
                                      (VJOB, "gochara-verification-job-ABC"), (VJOB, "gochara-verification-job-a;rm")])
def test_j2_an_execution_name_of_the_other_job_or_malformed_stops_before_any_cloud_call(job, name):
    cloud = Cloud()
    with pytest.raises(CR.Refused, match=f"execution name is not {job}-<suffix>"):
        CR.measure(name, cloud, job_name=job)
    assert cloud.calls == []


# ───────────── J3 the verification job's definition ─────────────

def test_j3_the_definition_is_measured_with_the_fields_the_packs_job_gate_reads():
    cloud = Cloud()
    record = CR.measure(None, cloud, job_name=VJOB)
    job = record["job"]
    assert record["schema"] == "ky.cloudrun_readback/1" and record["status"] == "MEASURED" and record["execution"] is None and record["logs"] is None
    assert job["name"] == VJOB
    assert job["image"] == {"reference": REF, "tag": None, "digest": DIGEST}                  # immutable: the digest IS the reference's; no registry call exists for it
    assert (job["timeout_seconds"], job["max_retries"], job["service_account"]) == (28800, 0, SERVICE_ACCOUNT)
    assert (job["cpu"], job["memory"]) == ("1", "4Gi")
    by = {e["name"]: e for e in job["environment"]}
    assert set(by) == {"GOCHARA_RUNNER_COMMIT", "GOCHARA_RUNNER_IMAGE_DIGEST", "GOCHARA_VERIFIER_DB_URL"}
    assert by["GOCHARA_VERIFIER_DB_URL"]["source"] == "secret" and by["GOCHARA_VERIFIER_DB_URL"]["secret"] == "gochara-verifier-db-url" and "value" not in by["GOCHARA_VERIFIER_DB_URL"]
    assert record["provenance"]["image_commit"] == COMMIT
    assert [c[1:4] for c in cloud.calls] == [["run", "jobs", "describe"]] and cloud.calls[0][4] == VJOB      # exactly ONE call: no registry describe for a digest reference


def test_j3_a_tag_or_another_repository_is_refused_not_guessed():
    for ref in (f"{CR.IMAGE_REPO}:{COMMIT}", f"{CR.IMAGE_REPO}:latest", f"asia-south1-docker.pkg.dev/other/amjis/brahma-pipeline@{DIGEST}", f"{CR.IMAGE_REPO}@sha256:{'a' * 63}"):
        job = verification_job()
        job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["image"] = ref
        with pytest.raises(CR.Refused, match="not <pipeline repository>@sha256"):
            CR.measure(None, Cloud(job=job), job_name=VJOB)


def test_j3_an_absent_max_retries_reads_null_never_zero_and_a_wrong_resource_refuses():
    job = verification_job()
    del job["spec"]["template"]["spec"]["template"]["spec"]["maxRetries"]
    assert CR.measure(None, Cloud(job=job), job_name=VJOB)["job"]["max_retries"] is None          # Cloud Run's default is 3: the gate must see null, not 0
    with pytest.raises(CR.Refused, match="not 'gochara-verification-job'"):
        CR.measure(None, Cloud(job=fixture("job")), job_name=VJOB)                                   # the pipeline job described under --job gochara-verification-job


# ───────────── J4 runner identity shown only in its public-identifier shape ─────────────

@pytest.mark.parametrize("name,bad", [("GOCHARA_RUNNER_COMMIT", "main"), ("GOCHARA_RUNNER_COMMIT", COMMIT.upper()), ("GOCHARA_RUNNER_COMMIT", COMMIT + "0"),
                                      ("GOCHARA_RUNNER_IMAGE_DIGEST", "cd" * 32), ("GOCHARA_RUNNER_IMAGE_DIGEST", "sha256:short")])
def test_j4_a_runner_identity_variable_of_the_wrong_shape_is_withheld(name, bad):
    job = verification_job()
    for entry in job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["env"]:
        if entry["name"] == name:
            entry["value"] = bad
    record = CR.measure(None, Cloud(job=job), job_name=VJOB)
    row = next(e for e in record["job"]["environment"] if e["name"] == name)
    assert row == {"name": name, "source": "value", "value_withheld": True}
    assert bad not in json.dumps(record)


def test_j4_the_pipeline_job_still_withholds_every_variable_outside_the_allowlist():
    job = fixture("job")
    job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["env"].append({"name": "GOCHARA_RUNNER_COMMIT", "value": COMMIT})
    record = CR.measure(None, _pipeline_cloud(job))
    row = next(e for e in record["job"]["environment"] if e["name"] == "GOCHARA_RUNNER_COMMIT")
    assert row["value"] == COMMIT                                                               # the shape-gated allowlist is global; it shows only a 40-hex commit
    assert next(e for e in record["job"]["environment"] if e["name"] == "SOME_API_TOKEN") == {"name": "SOME_API_TOKEN", "source": "value", "value_withheld": True}


def _pipeline_cloud(job):
    class PipelineCloud:
        def __call__(self, argv):
            joined = " ".join(argv)
            doc = job if "jobs describe" in joined else fixture("image")
            return SimpleNamespace(returncode=0, stdout=json.dumps(doc), stderr="")
    return PipelineCloud()


# ───────────── J5 an execution is judged against the chosen job ─────────────

def test_j5_an_execution_of_the_verification_job_is_measured_against_that_job():
    record = CR.measure(VEXEC, Cloud(), job_name=VJOB)
    execution = record["execution"]
    assert execution["name"] == VEXEC and execution["outcome"] == "SUCCEEDED" and execution["image_reference_equals_job"] is True
    assert execution["completion_time"] == "2026-10-17T10:41:30Z" and execution["succeeded_count"] == 1


def test_j5_an_execution_labelled_with_another_job_refuses():
    with pytest.raises(CR.Refused, match="belongs to job 'brahma-build-pipeline-job', not 'gochara-verification-job'"):
        CR.measure(VEXEC, Cloud(execution=verification_execution(job="brahma-build-pipeline-job")), job_name=VJOB)


def test_j5_a_running_execution_is_never_succeeded_and_the_calls_are_these():
    cloud = Cloud(execution=verification_execution(state="running"))
    record = CR.measure(VEXEC, cloud, job_name=VJOB)
    assert record["execution"]["outcome"] == "RUNNING"
    assert cloud.calls[1] == ["gcloud", "run", "jobs", "executions", "describe", VEXEC, "--project=madhav-astrology", "--region=asia-south1", "--format=json"]


# ───────────── J6 the job's ONE final report ─────────────

def test_j6_exactly_one_complete_report_is_parsed_into_logs_report():
    cloud = Cloud(logs=[log_entry("verifying marriage ...", 1), log_entry(json.dumps(REPORT, sort_keys=True), 2), log_entry('{"unrelated": 1}', 3)])
    logs = CR.measure(VEXEC, cloud, logs=True, job_name=VJOB)["logs"]
    assert logs["report"] == REPORT and logs["reports_found"] == 1 and logs["truncated"] is False and logs["unreadable_lines"] == 0
    assert logs["execution"] == VEXEC
    read = cloud.calls[-1]
    assert read[:3] == ["gcloud", "logging", "read"]
    assert f'resource.labels.job_name="{VJOB}"' in read[3] and f'"run.googleapis.com/execution_name"="{VEXEC}"' in read[3] and 'textPayload:"\\"classes\\""' in read[3]
    assert "STRETCH_SINK" not in read[3]                                                         # not the build job's filter


@pytest.mark.parametrize("entries,found,unreadable", [
    ([], 0, 0),
    ([log_entry(json.dumps(REPORT), 1), log_entry(json.dumps(dict(REPORT, status="DISAGREE")), 2)], 2, 0),
    ([log_entry(json.dumps(REPORT)[:-12], 1)], 0, 1),
    ([log_entry(json.dumps(REPORT), 1), log_entry('{"classes": ' + "[", 2)], 1, 1),
    ([log_entry(json.dumps({"classes": "26", "generation": "5.0"}), 1)], 0, 0),
])
def test_j6_zero_several_or_unreadable_reports_read_null_never_a_guess(entries, found, unreadable):
    logs = CR.measure(VEXEC, Cloud(logs=entries), logs=True, job_name=VJOB)["logs"]
    assert logs["report"] is None and logs["reports_found"] == found and logs["unreadable_lines"] == unreadable


def test_j6_a_truncated_read_never_yields_a_report():
    page = [log_entry(json.dumps(REPORT), n, when=f"2026-10-17T11:00:{n % 60:02d}.000000Z") for n in range(CR.LOG_PAGE_SIZE)]
    cloud = Cloud(logs=page)                                                                   # a full page every time, all at distinct instants but never a short page: the cap stops it
    logs = CR.measure(VEXEC, cloud, logs=True, job_name=VJOB)["logs"]
    assert logs["truncated"] is True and logs["truncation_reason"] and logs["report"] is None


# ───────────── J7 the default record is byte-identical ─────────────

def test_j7_without_a_job_the_pipeline_job_is_measured_exactly_as_before():
    """The pre-change filter text is quoted literally (it is the reviewed J-3 filter); the record equals the explicit-default one."""
    class PipelineCloud:
        def __init__(self): self.calls = []

        def __call__(self, argv):
            self.calls.append(list(argv))
            joined = " ".join(argv)
            doc = fixture("job") if "jobs describe" in joined else fixture("image") if "images describe" in joined else fixture("execution_succeeded")
            return SimpleNamespace(returncode=0, stdout=json.dumps(doc), stderr="")
    explicit, default = PipelineCloud(), PipelineCloud()
    clock = lambda: dt.datetime(2026, 10, 19, tzinfo=dt.timezone.utc)
    a = CR.measure("brahma-build-pipeline-job-abc12", explicit, clock=clock, job_name=CR.JOB)
    b = CR.measure("brahma-build-pipeline-job-abc12", default, clock=clock)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert a["job"]["image"]["tag"] == COMMIT and a["job"]["name"] == "brahma-build-pipeline-job" and a["provenance"]["basis"].startswith("image tag is the 40-hex commit")
    assert explicit.calls == default.calls and len(default.calls) == 3
    assert CR.logs_filter("brahma-build-pipeline-job-abc12") == (
        'resource.type="cloud_run_job" AND resource.labels.job_name="brahma-build-pipeline-job" AND resource.labels.location="asia-south1" '
        'AND labels."run.googleapis.com/execution_name"="brahma-build-pipeline-job-abc12" AND (textPayload:"STRETCH_SINK" OR textPayload:"asset.substep")')
