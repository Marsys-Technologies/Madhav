#!/usr/bin/env python3
"""Read-only MEASUREMENT of the deployed pipeline Cloud Run job (and, optionally, one of its executions).

The executor runs this for the fixed, reviewed, non-production kind `cloudrun_job_readback`. It holds no argument that can change a
target: project, region, job name and image repository are constants below; the only request argument is `--execution <name>`, and a
name that is not `brahma-build-pipeline-job-<suffix>` is refused before any cloud call. It issues at most THREE fixed `gcloud` describe
calls (job; the registry digest of the job's image tag; one execution) and prints ONE line, a `ky.cloudrun_readback/1` JSON record.

What is measured (each field is read from a describe response, never inferred; a missing or malformed required field REFUSES the whole
record — status REFUSED, exit 1 — so a partial record can never be mistaken for evidence):
  · job      the image reference as Cloud Run holds it, the registry digest that reference resolves to now, service account, task
             timeout, memory, cpu, labels, and the environment (secret bindings by NAME only; plain values only for a fixed
             allowlist of non-secret keys, every other value is withheld);
  · commit   the image tag is a 40-hex commit (deploy.yml tags `brahma-pipeline:${DEPLOY_SHA}`, after a checkout verified equal to
             DEPLOY_SHA). A reference that is not that shape (`:latest`, a bare digest) is refused: no commit can be tied to it;
  · execution (only when `--execution` is given) completion condition, start/completion time, succeeded / failed / running /
             cancelled counts, task count, image and args the execution carried, log URI (the URI only; logs are NOT read).
Honest nulls (CLAUDE.md §N.7.6 / §N.8): the corpus (Swiss Ephemeris files) cannot be measured without running the image, so the record
says so in `corpus.status` rather than carrying a green; `provenance.image_attests_commit` is false because the image itself carries no
revision label. Shapes follow the Cloud Run v1 Job/Execution resources (`spec.template.spec.template.spec` for the job, the path
deploy.yml already reads; `spec.template.spec` for an execution, as gochara_seal_execution_check.py reads it) — (I) INTERPRETATION: no
live response was captured for this build; the first real run is the proof of the shape, and a different shape REFUSES, never guesses.
Standard library only: the executor copies this single file out of origin/main and runs it, so it cannot import its siblings."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys

SCHEMA = "ky.cloudrun_readback/1"
PROJECT = "madhav-astrology"
REGION = "asia-south1"
JOB = "brahma-build-pipeline-job"
IMAGE_REPO = "asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline"
EXECUTION = re.compile(r"brahma-build-pipeline-job-[a-z0-9]+(?:-[a-z0-9]+)*")      # smalltest_launch.EXECUTION, byte for byte
TAG_REF = re.compile(re.escape(IMAGE_REPO) + r":([0-9a-f]{40})")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}")
# Plain values that may be shown. Everything else is a name only; a new key needs a reviewed edit here.
ENV_VALUE_ALLOWLIST = frozenset({"GCP_PROJECT", "PUBSUB_TOPIC", "KA_KSHETRA_HASH_SPILL_DIR", "SE_EPHE_PATH", "SWE_EPHE_PATH", "PYTHONPATH"})
GCLOUD_TIMEOUT_S = 120


class Refused(RuntimeError):
    pass


def job_describe_argv() -> list[str]:
    return ["gcloud", "run", "jobs", "describe", JOB, f"--project={PROJECT}", f"--region={REGION}", "--format=json"]


def image_describe_argv(commit: str) -> list[str]:
    return ["gcloud", "artifacts", "docker", "images", "describe", f"{IMAGE_REPO}:{commit}", f"--project={PROJECT}", "--format=json"]


def execution_describe_argv(name: str) -> list[str]:
    return ["gcloud", "run", "jobs", "executions", "describe", name, f"--project={PROJECT}", f"--region={REGION}", "--format=json"]


def gcloud_json(argv: list[str], runner, what: str) -> dict:
    """One fixed call. The child's stderr is never relayed (it may name identities); only the exit status is."""
    try:
        result = runner(argv)
    except (OSError, subprocess.SubprocessError):
        raise Refused(f"{what}: gcloud could not be run or timed out") from None
    if result.returncode:
        raise Refused(f"{what}: gcloud exited {result.returncode}")
    try:
        value = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise Refused(f"{what}: gcloud output is not JSON") from None
    if not isinstance(value, dict):
        raise Refused(f"{what}: gcloud output is not a JSON object")
    return value


def default_runner(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, timeout=GCLOUD_TIMEOUT_S, check=False, stdin=subprocess.DEVNULL)


def parse_int64(value):
    """Cloud Run int64 arrives as a decimal string, int32 as a number; refuse a bool, a fraction, a signed or padded string."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]*", value):
        return int(value)
    return None


def need(mapping, key, what, kind=str):
    value = mapping.get(key) if isinstance(mapping, dict) else None
    if not isinstance(value, kind) or isinstance(value, bool) or (kind is str and not value):
        raise Refused(f"{what}: required field {key!r} is missing or malformed")
    return value


def job_task_spec(job: dict) -> dict:
    node = job
    for key in ("spec", "template", "spec", "template", "spec"):                # the path deploy.yml:422 reads
        node = node.get(key) if isinstance(node, dict) else None
    if not isinstance(node, dict):
        raise Refused("job: spec.template.spec.template.spec is missing (unexpected resource shape)")
    return node


def execution_task_spec(execution: dict) -> dict:
    spec = execution.get("spec") if isinstance(execution.get("spec"), dict) else {}
    task = (spec.get("template") or {}).get("spec") if isinstance(spec.get("template"), dict) else None
    if isinstance(task, dict) and "containers" not in task:
        task = (task.get("template") or {}).get("spec") if isinstance(task.get("template"), dict) else None      # a Job-style nesting
    if not isinstance(task, dict) or "containers" not in task:
        raise Refused("execution: no container specification (unexpected resource shape)")
    return task


def only_container(task: dict, what: str) -> dict:
    containers = task.get("containers")
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict):
        raise Refused(f"{what}: exactly one container is required")
    return containers[0]


def environment(container: dict) -> list[dict]:
    """Names and non-secret settings only. A secret binding shows the secret's NAME and version, never a value."""
    entries = container.get("env")
    if not isinstance(entries, list) or not entries:
        raise Refused("job: the container carries no environment list")
    seen: set[str] = set()
    shown = []
    for entry in entries:
        name = entry.get("name") if isinstance(entry, dict) else None
        if not isinstance(name, str) or not ENV_NAME.fullmatch(name) or name in seen:
            raise Refused("job: an environment entry has a missing, malformed or duplicate name")
        seen.add(name)
        ref = ((entry.get("valueFrom") or {}).get("secretKeyRef")) if isinstance(entry.get("valueFrom"), dict) else None
        if ref is not None:
            if not isinstance(ref, dict) or not isinstance(ref.get("name"), str) or not ref["name"]:
                raise Refused("job: a secret binding does not name its secret")
            shown.append({"name": name, "source": "secret", "secret": ref["name"], "version": ref.get("key") if isinstance(ref.get("key"), str) else None})
        elif isinstance(entry.get("value"), str):
            row = {"name": name, "source": "value"}
            if name in ENV_VALUE_ALLOWLIST:
                row["value"] = entry["value"]
            else:
                row["value_withheld"] = True
            shown.append(row)
        else:
            shown.append({"name": name, "source": "other", "value_withheld": True})
    return shown


def labels_of(resource: dict) -> dict:
    labels = (resource.get("metadata") or {}).get("labels", {}) if isinstance(resource.get("metadata"), dict) else {}
    if not isinstance(labels, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in labels.items()):
        raise Refused("metadata.labels is malformed")
    return dict(sorted(labels.items()))


def registry_digest(commit: str, runner) -> str:
    summary = gcloud_json(image_describe_argv(commit), runner, "image digest").get("image_summary")
    digest = need(summary, "digest", "image digest")
    if not DIGEST.fullmatch(digest):
        raise Refused("image digest: the registry digest is not sha256:<64-hex>")
    qualified = summary.get("fully_qualified_digest")
    if qualified is not None and not (isinstance(qualified, str) and qualified.endswith("@" + digest)):
        raise Refused("image digest: fully_qualified_digest names a different digest")
    return digest


def measure_job(runner) -> tuple[dict, str]:
    job = gcloud_json(job_describe_argv(), runner, "job")
    name = (job.get("metadata") or {}).get("name") if isinstance(job.get("metadata"), dict) else None
    if name != JOB:
        raise Refused(f"job: the described resource is {name!r}, not {JOB!r}")
    task = job_task_spec(job)
    container = only_container(task, "job")
    reference = need(container, "image", "job")
    match = TAG_REF.fullmatch(reference)
    if not match:
        raise Refused("job: the image reference is not <pipeline repository>:<40-hex commit>; no commit can be tied to it")
    commit = match.group(1)
    limits = (container.get("resources") or {}).get("limits") if isinstance(container.get("resources"), dict) else None
    labels = labels_of(job)
    if labels.get("commit-sha", commit) != commit:
        raise Refused("job: the job's commit-sha label disagrees with its image tag")
    maximum = task.get("maxRetries")
    return {
        "name": JOB,
        "image": {"reference": reference, "tag": commit, "digest": registry_digest(commit, runner)},
        "service_account": need(task, "serviceAccountName", "job"),
        "timeout_seconds": _count(task.get("timeoutSeconds"), "job.timeoutSeconds", required=True),
        "max_retries": _count(maximum, "job.maxRetries", required=False),
        "memory": need(limits, "memory", "job.resources.limits"),
        "cpu": need(limits, "cpu", "job.resources.limits"),
        "labels": labels,
        "environment": environment(container),
    }, commit


def _count(value, what, required):
    if value is None and not required:
        return None
    parsed = parse_int64(value)
    if parsed is None:
        raise Refused(f"{what} is missing or not a non-negative integer")
    return parsed


def _time(value, what):
    if value is None:
        return None
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00") if isinstance(value, str) else None)
    except (ValueError, TypeError, AttributeError):
        raise Refused(f"execution: {what} is not an ISO-8601 time") from None
    return value


def measure_execution(name: str, job_reference: str, runner) -> dict:
    resource = gcloud_json(execution_describe_argv(name), runner, "execution")
    meta = resource.get("metadata") if isinstance(resource.get("metadata"), dict) else {}
    if meta.get("name") != name:
        raise Refused(f"execution: the described resource is {meta.get('name')!r}, not {name!r}")
    owner = labels_of(resource).get("run.googleapis.com/job")
    if owner is not None and owner != JOB:
        raise Refused(f"execution: it belongs to job {owner!r}, not {JOB!r}")
    container = only_container(execution_task_spec(resource), "execution")
    image = need(container, "image", "execution")
    status = resource.get("status") if isinstance(resource.get("status"), dict) else None
    conditions = status.get("conditions") if status else None
    if not isinstance(conditions, list) or not conditions:
        raise Refused("execution: status.conditions is missing")          # an empty status is never read as zero counts
    states: dict[str, str] = {}
    for condition in conditions:
        kind = condition.get("type") if isinstance(condition, dict) else None
        if not isinstance(kind, str) or not kind or kind in states or not isinstance(condition.get("status"), str):
            raise Refused("execution: a condition is malformed or duplicated")
        states[kind] = condition["status"]
    counts = {key: _count(status.get(src), f"execution.status.{src}", required=False) for key, src in
              (("succeeded", "succeededCount"), ("failed", "failedCount"), ("running", "runningCount"), ("cancelled", "cancelledCount"))}
    # (I) INTERPRETATION: protobuf JSON omits a zero count, so an absent count beside a populated conditions list is 0 (as in
    # gochara_seal_execution_check.state); an unparseable count is refused above.
    counts = {key: 0 if value is None else value for key, value in counts.items()}
    task_count = _count((resource.get("spec") or {}).get("taskCount") if isinstance(resource.get("spec"), dict) else None, "execution.spec.taskCount", required=False)
    task_count = 1 if task_count is None else task_count           # (I) INTERPRETATION: Cloud Run's default, as the seal check reads it
    completed = states.get("Completed")
    completion_time = _time(status.get("completionTime"), "completionTime")
    if counts["failed"] or counts["cancelled"] or completed == "False":
        outcome = "FAILED"
    elif completed == "True" and completion_time and counts["succeeded"] == task_count and not counts["running"]:
        outcome = "SUCCEEDED"
    else:
        outcome = "RUNNING"
    args = container.get("args", [])
    if not isinstance(args, list) or any(not isinstance(a, str) for a in args):
        raise Refused("execution: args are malformed")
    log_uri = status.get("logUri")
    return {
        "name": name,
        "outcome": outcome,
        "completed_condition": completed,
        "start_time": _time(status.get("startTime"), "startTime"),
        "completion_time": completion_time,
        "task_count": task_count,
        **{f"{key}_count": value for key, value in counts.items()},
        "image_reference": image,
        "image_reference_equals_job": image == job_reference,
        "args": args,
        "log_uri": log_uri if isinstance(log_uri, str) else None,
    }


def measure(execution: str | None, runner=default_runner, clock=lambda: dt.datetime.now(dt.timezone.utc)) -> dict:
    if execution is not None and not EXECUTION.fullmatch(execution):
        raise Refused("the execution name is not brahma-build-pipeline-job-<suffix>")
    job, commit = measure_job(runner)
    return {
        "schema": SCHEMA,
        "status": "MEASURED",
        "measured_at": clock().isoformat(timespec="seconds"),
        "project": PROJECT,
        "region": REGION,
        "job": job,
        "provenance": {
            "basis": "image tag is the 40-hex commit deploy.yml built and pushed (tag :${DEPLOY_SHA}); digest is what that tag resolves to at measured_at",
            "image_commit": commit,
            "job_label_commit_sha": job["labels"].get("commit-sha"),
            "image_attests_commit": False,
        },
        "corpus": {
            "status": "UNMEASURED_IN_DEPLOYED_IMAGE",
            "reason": "no image label, registry field or Cloud Run field records the ephemeris corpus digest; it can only be read by running the image",
            "build_gate_read_at": {"path": "platform/python-sidecar/Dockerfile.pipeline", "commit": commit},
        },
        "execution": measure_execution(execution, job["image"]["reference"], runner) if execution is not None else None,
    }


def cli(argv=None, runner=default_runner) -> int:
    parser = argparse.ArgumentParser(description="Read-only measurement of the pipeline Cloud Run job.", allow_abbrev=False)
    parser.add_argument("--execution", default=None)
    args = parser.parse_args(argv)                                       # any other argument exits 2 before a cloud call
    try:
        record = measure(args.execution, runner)
        code = 0
    except Refused as exc:
        record, code = {"schema": SCHEMA, "status": "REFUSED", "reason": str(exc)}, 1
    print(json.dumps(record, sort_keys=True, separators=(",", ":")), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(cli())
