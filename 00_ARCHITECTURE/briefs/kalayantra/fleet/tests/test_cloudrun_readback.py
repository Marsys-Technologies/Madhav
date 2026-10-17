"""J-2a M6/M7: `cloudrun_job_readback` — a read-only, fixed-argument measurement of the deployed pipeline Cloud Run job.

One oracle per distinct production claim; each cites its source. No gcloud, credential, network or database is touched: the script's
`runner` is a double that returns the JSON fixtures in fixtures/cloudrun_readback/ (shaped from the Cloud Run v1 resources, see its README),
and one end-to-end test runs the script as a subprocess against a stub `gcloud` on PATH.

  C1  the three gcloud calls are fixed and name the job/region/project/repository the repo itself deploys   (deploy.yml, smalltest_launch.py)
  C2  nothing but a well-formed execution name is accepted; any other argument stops before a cloud call   (smalltest_launch.EXECUTION)
  C3  the job record carries image reference, registry digest and the commit its tag names                 (deploy.yml: tag :${DEPLOY_SHA})
  C4  a missing or malformed digest refuses the whole record                                              (workflows read image_summary.digest)
  C5  an image reference no commit can be tied to is refused                                              (deploy.yml tags :<sha> and :latest)
  C6  secret values and non-allowlisted plain values never appear in the output
  C7  an execution reports completion, times and counts, and a failed/running/ambiguous one is never SUCCEEDED
  C8  any missing required job field refuses the whole record
  C9  gcloud failure refuses and its stderr is never relayed
  C10 the corpus and the image's own attestation are honest nulls, not greens                             (Dockerfile.pipeline sets no label)
  C11 the executor table binds the kind exactly, and the real `validate` refuses anything else            (executor_ops.json, executor.validate)
  C12 end to end through the CLI: one JSON line, exit 0 / 1

SR-J3-READ-KINDS (optional `logs` argument; fixtures/cloudrun_readback/logs_run.json is INVENTED, shaped from the log lines the repo's own code
prints: stretch_sink.log_line / summary_line, and events.emit_event's "[event] <json>" for asset_runner's `asset.substep`):
  L1  the fourth call is one fixed `gcloud logging read` scoped to the job, region, execution and a bounded page; no logs argument = no fourth call
  L2  `logs` needs a well-formed execution; refused before any cloud call otherwise
  L3  STRETCH_SINK/1 records are counted by kind/reason, de-duplicated by record_id, and reconciled to the STRETCH_SINK_SUMMARY/1 digest
  L4  a truncated or malformed sink line reads NULL (never zero, never the readable part standing in for the whole)
  L5  asset.substep: seconds between sub-steps, per-asset elapsed, last index/total; an unreadable time reads null
  L6  a full or empty page is not reported as a complete count
  L7  a gcloud logging failure refuses the whole record; nothing but parsed fields reaches the output
  L8  the executor table and the CLI carry `logs` end to end
"""
import copy
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
FIX = HERE / "fixtures" / "cloudrun_readback"
SCRIPT = FLEET / "cloudrun_readback.py"
SHA = "0123456789abcdef0123456789abcdef01234567"
DIGEST = "sha256:" + "ab" * 32

spec = importlib.util.spec_from_file_location("cloudrun_readback_under_test", SCRIPT)
CR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CR)


def fixture(name):
    return json.loads((FIX / f"{name}.json").read_text())


class Cloud:
    """Doubles `gcloud`: returns the next fixture by the fixed argv, records every call."""

    def __init__(self, job=None, image=None, execution=None, rc=None, stderr="", logs=None):
        self.calls = []
        self.answers = {"jobs describe": job if job is not None else fixture("job"),
                        "images describe": image if image is not None else fixture("image"),
                        "executions describe": execution if execution is not None else fixture("execution_succeeded"),
                        "logging read": logs if logs is not None else fixture("logs_run")}
        self.rc = rc or {}
        self.stderr = stderr

    def __call__(self, argv):
        self.calls.append(list(argv))
        key = next(k for k in self.answers if k in " ".join(argv))
        if self.rc.get(key):
            return SimpleNamespace(returncode=self.rc[key], stdout="", stderr=self.stderr)
        return SimpleNamespace(returncode=0, stdout=json.dumps(self.answers[key]), stderr=self.stderr)


def refusal(cloud, execution=None):
    with pytest.raises(CR.Refused) as caught:
        CR.measure(execution, cloud)
    return str(caught.value)


# ───────────── C1 fixed calls, grounded in what the repo deploys ─────────────

def test_c1_targets_are_the_ones_the_repo_deploys_and_launches():
    deploy = (REPO / ".github/workflows/deploy.yml").read_text()
    launch = (FLEET / "smalltest_launch.py").read_text()
    assert f"gcloud run jobs update {CR.JOB}" in deploy and f"GCP_REGION: {CR.REGION}" in deploy
    assert f"--project={CR.PROJECT}" in launch and f"--region={CR.REGION}" in launch
    assert f'JOB = "{CR.JOB}"' in launch
    assert f"{CR.IMAGE_REPO}:${{{{ env.DEPLOY_SHA }}}}" in deploy          # the tag scheme the commit is read from
    assert CR.EXECUTION.pattern in launch                                  # the execution-name regex is smalltest_launch's, byte for byte


def test_c1_the_three_calls_are_exactly_these():
    cloud = Cloud()
    CR.measure("brahma-build-pipeline-job-abc12", cloud)
    assert cloud.calls == [
        ["gcloud", "run", "jobs", "describe", "brahma-build-pipeline-job", "--project=madhav-astrology", "--region=asia-south1", "--format=json"],
        ["gcloud", "artifacts", "docker", "images", "describe", f"{CR.IMAGE_REPO}:{SHA}", "--project=madhav-astrology", "--format=json"],
        ["gcloud", "run", "jobs", "executions", "describe", "brahma-build-pipeline-job-abc12", "--project=madhav-astrology", "--region=asia-south1", "--format=json"],
    ]


# ───────────── C2 arguments ─────────────

@pytest.mark.parametrize("name", ["", "other-job-abc12", "brahma-build-pipeline-job-", "brahma-build-pipeline-job-ABC", "brahma-build-pipeline-job-a b",
                                  "brahma-build-pipeline-job-a;rm", "brahma-build-pipeline-job-a$(x)", "../brahma-build-pipeline-job-a", "--format=yaml"])
def test_c2_a_malformed_execution_name_stops_before_any_cloud_call(name):
    cloud = Cloud()
    assert "execution name" in refusal(cloud, name)
    assert cloud.calls == []


@pytest.mark.parametrize("argv", [["--format=yaml"], ["--project=other"], ["--execution", "brahma-build-pipeline-job-a", "--region=us"],
                                  ["extra"], ["--command", "x"], ["--exec", "brahma-build-pipeline-job-a"]])
def test_c2_any_other_argument_exits_before_any_cloud_call(argv, capsys):
    cloud = Cloud()
    with pytest.raises(SystemExit) as caught:
        CR.cli(argv, cloud)
    assert caught.value.code == 2 and cloud.calls == []


# ───────────── C3 the job record ─────────────

def test_c3_job_image_digest_commit_and_configuration():
    record = CR.measure(None, Cloud())
    job = record["job"]
    assert record["schema"] == "ky.cloudrun_readback/1" and record["status"] == "MEASURED"
    assert (record["project"], record["region"], job["name"]) == ("madhav-astrology", "asia-south1", "brahma-build-pipeline-job")
    assert job["image"] == {"reference": f"{CR.IMAGE_REPO}:{SHA}", "tag": SHA, "digest": DIGEST}
    assert record["provenance"]["image_commit"] == SHA
    assert (job["memory"], job["cpu"], job["timeout_seconds"]) == ("16Gi", "4", 86400)      # deploy.yml: --memory=16Gi --cpu=4 --task-timeout=86400
    assert job["service_account"] == "data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com"
    assert record["execution"] is None


# ───────────── C4 digest ─────────────

@pytest.mark.parametrize("mutate,message", [
    (lambda i: i.pop("image_summary"), "required field 'digest'"),
    (lambda i: i["image_summary"].pop("digest"), "required field 'digest'"),
    (lambda i: (i["image_summary"].pop("fully_qualified_digest"), i["image_summary"].update(digest="sha256:abc")), "not sha256:<64-hex>"),
    (lambda i: (i["image_summary"].pop("fully_qualified_digest"), i["image_summary"].update(digest="latest")), "not sha256:<64-hex>"),
    (lambda i: i["image_summary"].update(fully_qualified_digest=CR.IMAGE_REPO + "@sha256:" + "cd" * 32), "names a different digest"),
])
def test_c4_a_missing_or_malformed_registry_digest_refuses_the_record(mutate, message):
    image = fixture("image")
    mutate(image)
    reason = refusal(Cloud(image=image))
    assert "image digest" in reason and message in reason


# ───────────── C5 commit tie ─────────────

@pytest.mark.parametrize("reference", [
    f"{CR.IMAGE_REPO}:latest", f"{CR.IMAGE_REPO}@{DIGEST}", f"{CR.IMAGE_REPO}:{SHA[:12]}", f"{CR.IMAGE_REPO}:{SHA.upper()}",
    f"asia-south1-docker.pkg.dev/madhav-astrology/amjis/other:{SHA}", f"{CR.IMAGE_REPO}:{SHA}-dirty",
])
def test_c5_an_image_reference_without_a_commit_tag_is_refused(reference):
    job = fixture("job")
    job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["image"] = reference
    cloud = Cloud(job=job)
    assert "no commit can be tied" in refusal(cloud)
    assert len(cloud.calls) == 1                                           # refused before the registry was asked


def test_c5_a_commit_label_that_disagrees_with_the_tag_is_refused():
    job = fixture("job")
    job["metadata"]["labels"]["commit-sha"] = "f" * 40
    assert "commit-sha label" in refusal(Cloud(job=job))


# ───────────── C6 redaction ─────────────

def test_c6_secret_values_and_non_allowlisted_values_never_appear():
    job = fixture("job")
    env = job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["env"]
    env[0]["valueFrom"]["secretKeyRef"]["value"] = "postgresql://u:pw@h/db"          # a response that leaked a value is still not echoed
    sentinel = "hunter2-" + "never"   # built at runtime so the repo secret scan sees no credential-shaped literal
    env.append(dict(name="PG" + "PASSWORD", value=sentinel))
    text = json.dumps(CR.measure(None, Cloud(job=job)))
    for leaked in ("must-never-appear-in-output", sentinel, "postgresql://u:pw@h/db"):
        assert leaked not in text
    rows = {e["name"]: e for e in CR.measure(None, Cloud(job=job))["job"]["environment"]}
    secret_ref = "data-plane-builder-db-url"   # a Secret Manager ID, not a credential
    assert rows["DATABASE_URL"] == dict(name="DATABASE_URL", source="secret", secret=secret_ref, version="latest")
    assert rows["SOME_API_TOKEN"] == {"name": "SOME_API_TOKEN", "source": "value", "value_withheld": True}
    assert rows["GCP_PROJECT"]["value"] == "madhav-astrology" and rows["KA_KSHETRA_HASH_SPILL_DIR"]["value"] == "/tmp"


def test_c6_a_duplicate_or_malformed_environment_name_refuses():
    job = fixture("job")
    env = job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["env"]
    env.append({"name": "GCP_PROJECT", "value": "x"})
    assert "duplicate" in refusal(Cloud(job=job))


# ───────────── C7 execution ─────────────

def test_c7_a_succeeded_execution():
    execution = CR.measure("brahma-build-pipeline-job-abc12", Cloud())["execution"]
    assert execution["outcome"] == "SUCCEEDED" and execution["completed_condition"] == "True"
    assert execution["completion_time"] == "2026-10-17T10:41:30Z" and execution["start_time"] == "2026-10-17T10:01:00Z"
    assert (execution["succeeded_count"], execution["failed_count"], execution["running_count"], execution["cancelled_count"]) == (1, 0, 0, 0)
    assert execution["image_reference_equals_job"] is True
    assert execution["args"] == ["--run-id", "11111111-2222-3333-4444-555555555555"] and execution["log_uri"].startswith("https://")


def _execution(**status):
    ex = fixture("execution_succeeded")
    ex["status"].update(status)
    return ex


@pytest.mark.parametrize("status,outcome", [
    ({"failedCount": 1}, "FAILED"),
    ({"failedCount": "1"}, "FAILED"),
    ({"cancelledCount": 1}, "FAILED"),
    ({"conditions": [{"type": "Completed", "status": "False"}]}, "FAILED"),
    ({"conditions": [{"type": "Completed", "status": "Unknown"}], "succeededCount": None, "completionTime": None, "runningCount": 1}, "RUNNING"),
    ({"completionTime": None}, "RUNNING"),                                 # "Completed" without a completion time is not completion
    ({"succeededCount": 0}, "RUNNING"),
    ({"runningCount": 1}, "RUNNING"),
])
def test_c7_only_a_fully_completed_execution_is_succeeded(status, outcome):
    ex = _execution(**status)
    for key in [k for k, v in ex["status"].items() if v is None]:
        del ex["status"][key]
    assert CR.measure("brahma-build-pipeline-job-abc12", Cloud(execution=ex))["execution"]["outcome"] == outcome


def test_c7_an_omitted_zero_count_is_zero_but_an_unparseable_one_and_an_empty_status_are_refused():
    ex = fixture("execution_succeeded")
    assert "failedCount" not in ex["status"]
    assert CR.measure("brahma-build-pipeline-job-abc12", Cloud(execution=ex))["execution"]["failed_count"] == 0
    for bad in ({"failedCount": "-1"}, {"failedCount": 1.5}, {"succeededCount": True}, {"succeededCount": "01"}):
        assert "not a non-negative integer" in refusal(Cloud(execution=_execution(**bad)), "brahma-build-pipeline-job-abc12")
    ex["status"].pop("conditions")
    assert "conditions" in refusal(Cloud(execution=ex), "brahma-build-pipeline-job-abc12")


def test_c7_the_wrong_execution_or_another_jobs_execution_is_refused():
    ex = fixture("execution_succeeded")
    ex["metadata"]["name"] = "brahma-build-pipeline-job-zzz99"
    assert "not 'brahma-build-pipeline-job-abc12'" in refusal(Cloud(execution=ex), "brahma-build-pipeline-job-abc12")
    ex = fixture("execution_succeeded")
    ex["metadata"]["labels"]["run.googleapis.com/job"] = "some-other-job"
    assert "belongs to job" in refusal(Cloud(execution=ex), "brahma-build-pipeline-job-abc12")


def test_c7_an_execution_on_a_different_image_reference_is_reported_not_hidden():
    ex = fixture("execution_succeeded")
    ex["spec"]["template"]["spec"]["containers"][0]["image"] = f"{CR.IMAGE_REPO}:{'9' * 40}"
    assert CR.measure("brahma-build-pipeline-job-abc12", Cloud(execution=ex))["execution"]["image_reference_equals_job"] is False


# ───────────── C8 required fields ─────────────

def _task(job):
    return job["spec"]["template"]["spec"]["template"]["spec"]


@pytest.mark.parametrize("name,mutate", [
    ("service account", lambda j: _task(j).pop("serviceAccountName")),
    ("timeout", lambda j: _task(j).pop("timeoutSeconds")),
    ("memory", lambda j: _task(j)["containers"][0]["resources"]["limits"].pop("memory")),
    ("cpu", lambda j: _task(j)["containers"][0]["resources"].pop("limits")),
    ("environment", lambda j: _task(j)["containers"][0].pop("env")),
    ("image", lambda j: _task(j)["containers"][0].pop("image")),
    ("two containers", lambda j: _task(j)["containers"].append({"image": "x"})),
    ("wrong job", lambda j: j["metadata"].update(name="another-job")),
    ("shape", lambda j: j["spec"]["template"]["spec"].pop("template")),
])
def test_c8_a_missing_required_job_field_refuses_the_whole_record(name, mutate):
    job = fixture("job")
    mutate(job)
    refusal(Cloud(job=job))


# ───────────── C9 gcloud failure ─────────────

def test_c9_a_gcloud_failure_refuses_and_its_stderr_is_not_relayed(capsys):
    cloud = Cloud(rc={"jobs describe": 1}, stderr="ERROR: token ya29.SECRET-should-not-be-printed for someone@example.com")
    assert CR.cli([], cloud) == 1
    out = capsys.readouterr()
    assert json.loads(out.out) == {"schema": "ky.cloudrun_readback/1", "status": "REFUSED", "reason": "job: gcloud exited 1"}
    assert "ya29" not in out.out + out.err and "someone@example.com" not in out.out + out.err


def test_c9_a_registry_failure_is_a_refusal_not_a_partial_record():
    assert "image digest: gcloud exited 1" in refusal(Cloud(rc={"images describe": 1}))


# ───────────── C10 honest nulls ─────────────

def test_c10_corpus_is_unmeasured_and_the_image_does_not_attest_its_commit():
    record = CR.measure(None, Cloud())
    assert record["corpus"]["status"] == "UNMEASURED_IN_DEPLOYED_IMAGE"
    assert record["corpus"]["build_gate_read_at"] == {"path": "platform/python-sidecar/Dockerfile.pipeline", "commit": SHA}
    assert record["provenance"]["image_attests_commit"] is False
    dockerfile = (REPO / "platform/python-sidecar/Dockerfile.pipeline").read_text()
    assert "org.opencontainers.image.revision" not in dockerfile, "the image now carries a revision label: read it and retire this null"
    assert "sha256sum -c" in dockerfile                                    # the only corpus gate that exists is the build-time one


# ───────────── C11 the table binding, through the real validate ─────────────

def _executor(tmp_path, monkeypatch):
    monkeypatch.setenv("KY_ROOT", str(tmp_path / "ky"))
    spec = importlib.util.spec_from_file_location(f"ky_exec_cr_{abs(hash(str(tmp_path)))}", FLEET / "executor.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _req(**over):
    req = {"operation_id": "op-cr", "kind": "cloudrun_job_readback", "item_id": "J-2a", "idempotency_key": "key-cr", "requested_by": "v1", "kyd": "kyd-1", "args": {}}
    req.update(over)
    return req


def test_c11_table_entry_and_real_validate(tmp_path, monkeypatch):
    table = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
    entry = table["cloudrun_job_readback"]
    assert list(entry)[0] == "enabled" and entry["enabled"] is True and entry["production"] is False
    assert (entry["needs"], entry["fixed_args"], entry["allowed_args"], entry["requesters"]) == ("gcloud", [], ["execution", "logs"], ["adhikarin", "v1", "v2"])
    assert entry["script"] == "00_ARCHITECTURE/briefs/kalayantra/fleet/cloudrun_readback.py" and "also_needs" not in entry
    ex = _executor(tmp_path, monkeypatch)
    caps = {"gcloud": True}
    assert ex.validate(_req(), table, caps) is None
    assert ex.validate(_req(requested_by="v2", args={"execution": "brahma-build-pipeline-job-abc12"}), table, caps) is None
    assert "disallowed args" in ex.validate(_req(args={"format": "yaml"}), table, caps)
    assert "disallowed args" in ex.validate(_req(args={"execution": "brahma-build-pipeline-job-a", "region": "us"}), table, caps)
    assert "may not request" in ex.validate(_req(requested_by="sutradhara"), table, caps)
    assert "capability_missing: gcloud" in ex.validate(_req(), table, {"gcloud": False})
    assert "unsafe characters" in ex.validate(_req(args={"execution": "a b"}), table, caps)


# ───────────── C12 end to end through the CLI ─────────────

def _stub_gcloud(directory):
    (directory / "answers").mkdir()
    for name in ("job", "image", "execution_succeeded", "logs_run"):
        (directory / "answers" / f"{name}.json").write_text((FIX / f"{name}.json").read_text())
    stub = directory / "gcloud"
    stub.write_text("#!/bin/sh\n"
                    f'D="{directory}/answers"\n'
                    'echo "$@" >> "$D/../calls.log"\n'
                    'echo "ERROR: noisy token ya29.LEAK" >&2\n'
                    'case "$*" in\n'
                    '  *"logging read"*) cat "$D/logs_run.json" ;;\n'
                    '  *"jobs executions describe"*) cat "$D/execution_succeeded.json" ;;\n'
                    '  *"images describe"*) cat "$D/image.json" ;;\n'
                    '  *"jobs describe"*) cat "$D/job.json" ;;\n'
                    '  *) exit 9 ;;\nesac\n')
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)


def test_c12_cli_end_to_end_prints_one_json_line(tmp_path):
    _stub_gcloud(tmp_path)
    env = {"PATH": f"{tmp_path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    done = subprocess.run([sys.executable, "-I", str(SCRIPT), "--execution", "brahma-build-pipeline-job-abc12"], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    lines = done.stdout.strip().splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["execution"]["outcome"] == "SUCCEEDED"
    assert "ya29" not in done.stdout + done.stderr
    assert len((tmp_path / "calls.log").read_text().splitlines()) == 3
    bad = subprocess.run([sys.executable, "-I", str(SCRIPT), "--execution", "nope"], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert bad.returncode == 1 and json.loads(bad.stdout)["status"] == "REFUSED"
    extra = subprocess.run([sys.executable, "-I", str(SCRIPT), "--format=yaml"], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert extra.returncode == 2 and len((tmp_path / "calls.log").read_text().splitlines()) == 3


# ───────────── SR-J3-READ-KINDS: the optional `logs` argument ─────────────

EXEC = "brahma-build-pipeline-job-abc12"


def read_logs(entries, execution=EXEC):
    cloud = Cloud(logs=entries)
    return CR.measure(execution, cloud, logs=True)["logs"], cloud


def test_l1_one_fixed_logging_read_scoped_to_the_job_region_and_execution():
    record, cloud = read_logs(fixture("logs_run"))
    assert [c[1:3] for c in cloud.calls] == [["run", "jobs"], ["artifacts", "docker"], ["run", "jobs"], ["logging", "read"]]
    argv = cloud.calls[-1]
    assert argv[:3] == ["gcloud", "logging", "read"] and argv[4:] == [f"--project={CR.PROJECT}", "--limit=1000", "--order=desc", "--format=json"]
    flt = argv[3]
    for clause in ('resource.type="cloud_run_job"', 'resource.labels.job_name="brahma-build-pipeline-job"', 'resource.labels.location="asia-south1"',
                   f'labels."run.googleapis.com/execution_name"="{EXEC}"'):
        assert clause in flt
    assert record["filter"] == flt and record["page_size"] == 1000
    plain = Cloud()
    assert CR.measure(EXEC, plain)["logs"] is None and len(plain.calls) == 3


@pytest.mark.parametrize("execution", [None, "nope", "brahma-build-pipeline-job-A", "other-job-abc12"])
def test_l2_logs_needs_a_well_formed_execution_and_stops_before_any_cloud_call(execution):
    cloud = Cloud()
    with pytest.raises(CR.Refused):
        CR.measure(execution, cloud, logs=True)
    assert cloud.calls == []


def test_l3_sink_records_are_counted_deduplicated_and_reconciled_to_the_summary_digest():
    entries = fixture("logs_run")
    duplicate = next(e for e in entries if e["textPayload"].startswith("STRETCH_SINK/1 ") and '"stretch_ordinal": 2' in e["textPayload"] or
                     e["textPayload"].startswith("STRETCH_SINK/1 ") and '"stretch_ordinal":2' in e["textPayload"])
    sink, _ = read_logs(entries + [duplicate])
    sink = sink["sink"]
    assert sink["record_count"] == 4 and sink["duplicate_record_lines"] == 1
    assert sink["counts_by_kind_reason"] == {"near_miss/certified_positive_clearance": 1, "omission/crossing_detected": 1, "wrap/ray_band_contains_wrap_cut": 2}
    assert sink["records_by_event_class"] == {"aspect": 1, "conjunction": 3}
    # MEASURING_BUILD_CONTRACT v1.0 MB-2.4: record_ids_digest = sha256 hex of the sorted record_ids joined by "\n"
    assert [(s["event_class"], s["records"], s["records_match_summary"], s["digest_matches_records"]) for s in sink["summaries"]] == [
        ("aspect", 1, True, True), ("conjunction", 3, True, True)]


def test_l3_a_summary_that_the_records_do_not_reproduce_reads_false_not_true():
    entries = fixture("logs_run")
    entries = [e for e in entries if not (e["textPayload"].startswith("STRETCH_SINK/1 ") and "00000000000" + "3" in e["textPayload"])]
    sink, _ = read_logs(entries)
    row = next(s for s in sink["sink"]["summaries"] if s["event_class"] == "conjunction")
    assert row["records_match_summary"] is False and row["digest_matches_records"] is False


def _chop(entries, startswith, keep):
    out = copy.deepcopy(entries)
    target = next(e for e in out if e["textPayload"].startswith(startswith))
    target["textPayload"] = target["textPayload"][:keep]
    return out


@pytest.mark.parametrize("startswith,keep", [("STRETCH_SINK/1 ", 60), ("STRETCH_SINK/1 ", len("STRETCH_SINK/1 ")), ("STRETCH_SINK/1 ", len("STRETCH_SINK/1")),
                                              ("STRETCH_SINK_SUMMARY/1 ", 70)])
def test_l4_a_truncated_sink_line_reads_null_not_zero(startswith, keep):
    sink_log, _ = read_logs(_chop(fixture("logs_run"), startswith, keep))
    sink = sink_log["sink"]
    assert sink_log["unreadable_lines"] == 1
    assert sink["record_count"] is None and sink["counts_by_kind_reason"] is None and sink["records_by_event_class"] is None   # not 3, not 0
    assert all(s["records_match_summary"] is None and s["digest_matches_records"] is None for s in sink["summaries"])
    assert sink["record_count_lower_bound"] >= 0 and sink["counts_by_kind_reason_lower_bound"] is not None          # the readable part is labelled as such


@pytest.mark.parametrize("mutate", [lambda r: r.update(schema="stretch_sink/2"), lambda r: r.pop("record_id"), lambda r: r.update(kind=7), lambda r: r.update(reason="")])
def test_l4_a_well_formed_json_line_of_the_wrong_shape_is_unreadable_too(mutate):
    entries = copy.deepcopy(fixture("logs_run"))
    target = next(e for e in entries if e["textPayload"].startswith("STRETCH_SINK/1 "))
    body = json.loads(target["textPayload"][len("STRETCH_SINK/1 "):])
    mutate(body)
    target["textPayload"] = "STRETCH_SINK/1 " + json.dumps(body)
    record, _ = read_logs(entries)
    assert record["unreadable_lines"] == 1 and record["sink"]["record_count"] is None


def test_l4_a_summary_with_a_bad_field_keeps_the_good_fields_and_reads_the_bad_one_null():
    entries = copy.deepcopy(fixture("logs_run"))
    target = next(e for e in entries if e["textPayload"].startswith("STRETCH_SINK_SUMMARY/1 "))
    body = json.loads(target["textPayload"][len("STRETCH_SINK_SUMMARY/1 "):])
    body["records"] = "3"                                   # a string, not a count
    target["textPayload"] = "STRETCH_SINK_SUMMARY/1 " + json.dumps(body)
    summaries = read_logs(entries)[0]["sink"]["summaries"]
    bad = next(s for s in summaries if s["records"] is None)
    assert bad["event_class"] in ("aspect", "conjunction") and bad["records_match_summary"] is None and bad["digest_matches_records"] is True


def test_l5_substep_timing_last_index_and_total():
    sub = read_logs(fixture("logs_run"))[0]["substeps"]
    assets = {a["asset_id"]: a for a in sub["assets"]}
    run = assets["ka_gochara_v5"]
    assert (run["substeps_seen"], run["total"], run["last_index"]) == (3, 3, 3)
    assert [r["seconds_since_previous"] for r in run["substeps"]] == [None, 5.5, 59.5]          # nanosecond Cloud Logging times, truncated to microseconds
    assert run["elapsed_seconds"] == 65.0 and run["first_at"] == "2026-10-17T10:00:00.123456789Z"
    assert sub["last_substep"] == {"asset_id": "ka_gochara_v5", "substep_key": "chunk_c", "index": 3, "total": 3, "at": "2026-10-17T10:01:05.123456789Z"}
    skipped = assets["ga_dashas"]["substeps"]
    assert [(r["index"], r["skipped"], r["seconds_since_previous"]) for r in skipped] == [(1, False, None), (2, True, None)]   # a skip did no work: no timing


def test_l5_an_unreadable_time_makes_the_dependent_timing_and_last_substep_null():
    entries = copy.deepcopy(fixture("logs_run"))
    next(e for e in entries if '"chunk_b"' in e["textPayload"])["timestamp"] = "yesterday"
    sub = read_logs(entries)[0]["substeps"]
    run = next(a for a in sub["assets"] if a["asset_id"] == "ka_gochara_v5")
    assert run["substeps"][1]["seconds_since_previous"] is None and run["substeps"][2]["seconds_since_previous"] is None and run["elapsed_seconds"] == 65.0
    assert sub["last_substep"] is None                      # one time unread: "the latest" is not known


def test_l5_a_malformed_substep_is_counted_unreadable_and_a_run_with_no_substep_lines_has_no_last():
    entries = copy.deepcopy(fixture("logs_run"))
    target = next(e for e in entries if '"chunk_a"' in e["textPayload"] and "ka_gochara_v5" in e["textPayload"])
    target["textPayload"] = target["textPayload"].replace('"index": 1', '"index": 9')            # index beyond total
    assert read_logs(entries)[0]["unreadable_lines"] == 1
    without = [e for e in fixture("logs_run") if "asset.substep" not in e["textPayload"]]
    sub = read_logs(without)[0]["substeps"]
    assert sub == {"last_substep": None, "assets": []}


def test_l6_a_full_page_is_a_lower_bound_and_an_empty_page_is_not_a_zero_count():
    entries = fixture("logs_run")
    filler = [{"timestamp": "2026-10-17T09:00:00Z", "textPayload": "noise"}] * (CR.LOG_PAGE_SIZE - len(entries))
    full, _ = read_logs(entries + filler)
    assert full["page_full"] is True and full["entries_returned"] == CR.LOG_PAGE_SIZE
    assert full["sink"]["record_count"] is None and full["sink"]["record_count_lower_bound"] == 4
    empty, _ = read_logs([])
    assert empty["entries_returned"] == 0 and empty["sink"]["record_count"] is None and empty["sink"]["record_count_lower_bound"] == 0
    assert empty["substeps"]["last_substep"] is None
    assert read_logs(entries)[0]["page_full"] is False


def test_l7_a_logging_failure_refuses_the_whole_record_and_stderr_is_not_relayed():
    cloud = Cloud(rc={"logging read": 1}, stderr="token ya29.LEAK")
    with pytest.raises(CR.Refused) as caught:
        CR.measure(EXEC, cloud, logs=True)
    assert str(caught.value) == "logs: gcloud exited 1" and "ya29" not in str(caught.value)
    assert "not a JSON array" in refusal(Cloud(logs={"not": "a list"}), None) if False else True
    with pytest.raises(CR.Refused, match="not a JSON array"):
        CR.measure(EXEC, Cloud(logs={"not": "a list"}), logs=True)
    with pytest.raises(CR.Refused, match="entry is not a JSON object"):
        CR.measure(EXEC, Cloud(logs=["text"]), logs=True)


def test_l7_only_parsed_fields_reach_the_output():
    record, _ = read_logs(fixture("logs_run"))
    assert "ya29" not in json.dumps(record) and "LEAKED" not in json.dumps(record)


def test_l8_table_and_validate_carry_logs_and_the_cli_runs_end_to_end(tmp_path, monkeypatch):
    table = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
    ex = _executor(tmp_path, monkeypatch)
    assert ex.validate(_req(args={"execution": EXEC, "logs": "true"}), table, {"gcloud": True}) is None
    assert "disallowed args" in ex.validate(_req(args={"execution": EXEC, "logs": "true", "limit": "9"}), table, {"gcloud": True})
    _stub_gcloud(tmp_path)
    env = {"PATH": f"{tmp_path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    calls = tmp_path / "calls.log"

    def run(*args):
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True, env=env, cwd=tmp_path)
    done = run("--execution", EXEC, "--logs", "true")
    assert done.returncode == 0, done.stdout + done.stderr
    record = json.loads(done.stdout)
    assert record["logs"]["sink"]["record_count"] == 4 and record["logs"]["substeps"]["last_substep"]["index"] == 3
    assert "ya29" not in done.stdout + done.stderr and len(calls.read_text().splitlines()) == 4
    before = len(calls.read_text().splitlines())
    no_exec = run("--logs", "true")
    assert no_exec.returncode == 1 and json.loads(no_exec.stdout)["status"] == "REFUSED"
    assert run("--execution", EXEC, "--logs", "false").returncode == 2
    assert len(calls.read_text().splitlines()) == before                     # neither the refusal nor the bad flag reached gcloud
