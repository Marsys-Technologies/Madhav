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
             cancelled counts, task count, image and args the execution carried, log URI (the URI only);
  · logs     (only when `--logs true` is given WITH `--execution`; SR-J3-READ-KINDS) ONE more fixed call, `gcloud logging read`, whose filter
             is built from constants plus the regex-validated execution name: Cloud Run job `brahma-build-pipeline-job`, location
             `asia-south1`, label run.googleapis.com/execution_name. It is read PAGE BY PAGE (newest first, LOG_PAGE_SIZE entries per call, at most
             LOG_MAX_PAGES calls and LOG_BUDGET_S seconds): each next call adds only `timestamp<="<oldest entry time seen>"` (a time that
             matched a strict RFC 3339 shape, never raw gcloud text) to the same filter, and entries are de-duplicated by insertId. If the
             cap, the time budget, an unpageable time or a stuck cursor stops the reading before the oldest entry, `truncated` is true and
             every count reads NULL (lower bounds are still given); a short page is the proof the read is complete. Parsed: `STRETCH_SINK/1` records (counted
             by kind/reason, de-duplicated by (event_class, record_id)), `STRETCH_SINK_SUMMARY/1` lines (reconciled against the records), and `asset.substep`
             events (log-entry times between consecutive sub-steps, last index/total). A line that cannot be read as the thing it claims to
             be (truncated, wrong shape) reads NULL in every field that depended on it and is counted in `unreadable_lines`; it is never
             zero and is never skipped silently (CLAUDE.md §N.8).
  · metrics  (only when `--metrics true` is given WITH `--execution`; SR-BOLD-09) TWO more fixed `gcloud monitoring time-series list` calls on
             the same gcloud identity: the Cloud Run job container CPU and memory utilisation distributions, scoped to the job and to the
             execution's own start..completion window (now, while it still runs). Reported: mean, p95 (interpolated inside its bucket) and
             the highest non-empty bucket's upper bound (a bound, not a sample maximum) for each, the CPU expressed in vCPUs against the
             job's allocated cpu, and a `shape` (SINGLE_THREAD_BOUND when p95 sits at ~1 vCPU with more allocated). A series that is absent,
             unreadable or whose query failed reads NULL with its `status`, never zero. No Cloud Run metric exposes DB wait: `wait` says so.
  · --job gochara-verification-job (J-4b-a55j, SR-A55J-A55M-RESCOPE: "the config is measured by cloudrun_job_readback; no new executor kind") ONE fixed describe of the
             VERIFICATION job instead of the pipeline job, and nothing else (no registry, execution, logs or metrics call; combining it with --execution/--logs/--metrics
             REFUSES before any cloud call). It reads the definition .github/workflows/gochara-verification-job-deploy.yml deploys and reports named `checks`, each
             computed from the describe response and false when the field differs (§N.8): image BY DIGEST of the pipeline repository, the verifier's own runtime identity,
             the verifier entry point as the container command, exactly the three contract environment variables (one secret, by name), GOCHARA_RUNNER_IMAGE_DIGEST equal to
             the deployed digest, GOCHARA_RUNNER_COMMIT a 40-hex commit, one task, Cloud SQL instance, max-retries 0, 8Gi/2cpu/7200s. The "disabled" half of
             "configured but disabled" is the executor table (`verification_job.enabled` false); this kind never starts, schedules or executes anything.
Honest nulls (CLAUDE.md §N.7.6 / §N.8): the corpus (Swiss Ephemeris files) cannot be measured without running the image, so the record
says so in `corpus.status` rather than carrying a green; `provenance.image_attests_commit` is false because the image itself carries no
revision label. Shapes follow the Cloud Run v1 Job/Execution resources (`spec.template.spec.template.spec` for the job, the path
deploy.yml already reads; `spec.template.spec` for an execution, as gochara_seal_execution_check.py reads it) — (I) INTERPRETATION: no
live response was captured for this build; the first real run is the proof of the shape, and a different shape REFUSES, never guesses.
Standard library only: the executor copies this single file out of origin/main and runs it, so it cannot import its siblings."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import time

SCHEMA = "ky.cloudrun_readback/1"
PROJECT = "madhav-astrology"
REGION = "asia-south1"
JOB = "brahma-build-pipeline-job"
IMAGE_REPO = "asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline"
VERIFICATION_JOB = "gochara-verification-job"                           # .github/workflows/gochara-verification-job-deploy.yml env VERIFICATION_JOB
VERIFIER_SERVICE_ACCOUNT = "gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com"
VERIFIER_COMMAND = ["python", "-m", "pipeline.orchestrator.verification_job"]
VERIFIER_SECRET = ("GOCHARA_VERIFIER_DB_URL", "gochara-verifier-db-url", "latest")
VERIFIER_PLAIN_ENV = frozenset({"GOCHARA_RUNNER_COMMIT", "GOCHARA_RUNNER_IMAGE_DIGEST"})
CLOUDSQL_INSTANCE = "madhav-astrology:asia-south1:amjis-postgres"
COMMIT_40 = re.compile(r"[0-9a-f]{40}")
EXECUTION = re.compile(r"brahma-build-pipeline-job-[a-z0-9]+(?:-[a-z0-9]+)*")      # smalltest_launch.EXECUTION, byte for byte
TAG_REF = re.compile(re.escape(IMAGE_REPO) + r":([0-9a-f]{40})")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}")
# Plain values that may be shown. Everything else is a name only; a new key needs a reviewed edit here.
ENV_VALUE_ALLOWLIST = frozenset({"GCP_PROJECT", "PUBSUB_TOPIC", "KA_KSHETRA_HASH_SPILL_DIR", "SE_EPHE_PATH", "SWE_EPHE_PATH", "PYTHONPATH"})
GCLOUD_TIMEOUT_S = 120
LOG_PAGE_SIZE = 1000                                                     # entries per `gcloud logging read` call; a short page proves the read reached the oldest entry
LOG_MAX_PAGES = 60                                                       # hard cap: 60,000 entries, far above a 26-class measuring build; beyond it `truncated` is true and counts read null
LOG_BUDGET_S = 420                                                       # wall-clock budget for all pages, under the executor's timeout_s (600) for this kind
CURSOR_TIME = re.compile(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?Z")      # the only time text that is ever put back into a filter
SINK_MARK, SINK_SUMMARY_MARK = "STRETCH_SINK/1", "STRETCH_SINK_SUMMARY/1"   # stretch_sink.LOG_PREFIX / SUMMARY_PREFIX without the trailing space
SINK_SCHEMA, SINK_SUMMARY_SCHEMA = "stretch_sink/1", "stretch_sink_summary/1"
SUBSTEP_MARK = '"asset.substep"'                                         # asset_runner.run_substeps emits {"type": "asset.substep", ...}
METRICS_RESOURCE_TYPE = "cloud_run_job"
CPU_METRIC = "run.googleapis.com/container/cpu/utilizations"             # distribution; fraction of the container's CPU limit
MEMORY_METRIC = "run.googleapis.com/container/memory/utilizations"       # distribution; fraction of the container's memory limit
METRIC_TIME = "%Y-%m-%dT%H:%M:%SZ"
SATURATION_FRACTION = 0.85                                               # p95 at or above this share of the allocated vCPUs = saturated
SINGLE_THREAD_BAND = (0.8, 1.25)                                         # p95 in vCPUs that reads as "one thread's worth"
SUSTAINED_MEAN_VCPU = 0.5                                                # a single-thread verdict also needs the MEAN this high (a burst is not a bound)
P95 = 0.95
SHA256_HEX = re.compile(r"[0-9a-f]{64}")
LOG_TIME = re.compile(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?(Z|[+-]\d\d:\d\d)")


class Refused(RuntimeError):
    pass


def job_describe_argv(job: str = JOB) -> list[str]:
    return ["gcloud", "run", "jobs", "describe", job, f"--project={PROJECT}", f"--region={REGION}", "--format=json"]


def image_describe_argv(commit: str) -> list[str]:
    return ["gcloud", "artifacts", "docker", "images", "describe", f"{IMAGE_REPO}:{commit}", f"--project={PROJECT}", "--format=json"]


def execution_describe_argv(name: str) -> list[str]:
    return ["gcloud", "run", "jobs", "executions", "describe", name, f"--project={PROJECT}", f"--region={REGION}", "--format=json"]


def logs_filter(name: str, not_after: str | None = None) -> str:
    """The one fixed filter; `not_after` (page 2 onward) is a CURSOR_TIME-validated entry time, the only thing that ever varies."""
    flt = (f'resource.type="cloud_run_job" AND resource.labels.job_name="{JOB}" AND resource.labels.location="{REGION}" '
           f'AND labels."run.googleapis.com/execution_name"="{name}" '
           f'AND (textPayload:"STRETCH_SINK" OR textPayload:"asset.substep")')
    if not_after is not None:
        if not CURSOR_TIME.fullmatch(not_after):
            raise Refused("logs: a paging cursor is not a strict RFC 3339 UTC time")
        flt += f' AND timestamp<="{not_after}"'
    return flt


def logs_read_argv(name: str, not_after: str | None = None) -> list[str]:
    flt = logs_filter(name, not_after)
    return ["gcloud", "logging", "read", flt, f"--project={PROJECT}", f"--limit={LOG_PAGE_SIZE}", "--order=desc", "--format=json"]


def gcloud_json(argv: list[str], runner, what: str, shape=dict) -> dict:
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
    if not isinstance(value, shape):
        raise Refused(f"{what}: gcloud output is not a JSON {'object' if shape is dict else 'array'}")
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


# ───────────── logs (SR-J3-READ-KINDS): parse one execution's job log ─────────────

def _is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _log_time(value):
    """RFC 3339 with up to nanoseconds (Cloud Logging) -> aware datetime; None when absent or unreadable (never a guess)."""
    match = LOG_TIME.fullmatch(value) if isinstance(value, str) else None
    if not match:
        return None
    head, fraction, zone = match.groups()
    try:
        return dt.datetime.fromisoformat(f"{head}.{(fraction or '0')[:6].ljust(6, '0')}{'+00:00' if zone == 'Z' else zone}")
    except ValueError:
        return None


def _entry_lines(entry):
    text = entry.get("textPayload")
    if not isinstance(text, str):
        payload = entry.get("jsonPayload")
        text = payload.get("message") if isinstance(payload, dict) else None
    return text.splitlines() if isinstance(text, str) else []


def _object_from(text):
    """The JSON object `text` holds, or None when it is empty, cut short or not an object (a truncated line is never repaired)."""
    try:
        value = json.loads(text)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def _read_sink_record(body):
    """stretch_sink.parse_line's shape test: schema, kind, reason, record_id and event_class must all be present and well-typed."""
    if body is None or body.get("schema") != SINK_SCHEMA:
        return None
    if any(not isinstance(body.get(key), str) or not body[key] for key in ("kind", "reason", "record_id", "event_class")):
        return None
    return {key: body[key] for key in ("kind", "reason", "record_id", "event_class")}


def _read_sink_summary(body):
    """A summary whose JSON parsed but whose fields are off keeps the good fields and reads the bad ones NULL."""
    if body is None or body.get("schema") != SINK_SUMMARY_SCHEMA or not isinstance(body.get("event_class"), str) or not body["event_class"]:
        return None
    counts = body.get("counts_by_kind_reason")
    if not isinstance(counts, dict) or any(not isinstance(k, str) or not _is_count(v) for k, v in counts.items()):
        counts = None
    digest = body.get("record_ids_digest")
    return {"event_class": body["event_class"], "records": body["records"] if _is_count(body.get("records")) else None,
            "counts_by_kind_reason": counts, "record_ids_digest": digest if isinstance(digest, str) and SHA256_HEX.fullmatch(digest) else None}


def _read_substep(body):
    if body is None or body.get("type") != "asset.substep":
        return None
    index, total, skipped = body.get("index"), body.get("total"), body.get("skipped", False)
    if any(not isinstance(body.get(key), str) or not body[key] for key in ("asset_id", "substep_key")):
        return None
    if not (_is_count(index) and _is_count(total) and 1 <= index <= total) or not isinstance(skipped, bool):
        return None
    return {"asset_id": body["asset_id"], "substep_key": body["substep_key"], "index": index, "total": total, "skipped": skipped}


def _seconds(later, earlier):
    return None if later is None or earlier is None else round((later - earlier).total_seconds(), 3)


def _substep_report(rows):
    """rows: (datetime|None, original time text|None, substep). Timing between two sub-steps is null unless BOTH times were read."""
    floor = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
    by_asset: dict[str, list] = {}
    for row in rows:
        by_asset.setdefault(row[2]["asset_id"], []).append(row)
    assets = []
    for asset_id, group in sorted(by_asset.items()):
        group.sort(key=lambda r: (r[2]["index"], r[0] or floor))      # a writer runs its sub-steps in index order; a time never reorders them
        shown, previous = [], None
        for when, text, step in group:
            shown.append({"index": step["index"], "substep_key": step["substep_key"], "at": text, "skipped": step["skipped"],
                          "seconds_since_previous": None if step["skipped"] or previous is None else _seconds(when, previous)})
            previous = previous if step["skipped"] else when
        totals = {r[2]["total"] for r in group}
        assets.append({"asset_id": asset_id, "substeps_seen": len(group), "total": totals.pop() if len(totals) == 1 else None,
                       "last_index": group[-1][2]["index"], "first_at": group[0][1], "last_at": group[-1][1],
                       "elapsed_seconds": _seconds(group[-1][0], group[0][0]), "substeps": shown})
    newest = None
    if rows and all(r[0] is not None for r in rows):                # one unreadable time and "the last one" is not known
        top = max(rows, key=lambda r: (r[0], r[2]["index"]))
        newest = {"asset_id": top[2]["asset_id"], "substep_key": top[2]["substep_key"], "index": top[2]["index"], "total": top[2]["total"], "at": top[1]}
    return assets, newest


def _sink_report(records, summaries, unreadable, duplicates, truncated, entries_returned):
    by_kind: dict[str, int] = {}
    by_class: dict[str, list] = {}
    kinds_by_class: dict[str, dict[str, int]] = {}
    for record in records.values():                                   # records is keyed (event_class, record_id): one row per class per id
        key = f"{record['kind']}/{record['reason']}"
        by_kind[key] = by_kind.get(key, 0) + 1
        by_class.setdefault(record["event_class"], []).append(record["record_id"])
        per_class = kinds_by_class.setdefault(record["event_class"], {})
        per_class[key] = per_class.get(key, 0) + 1
    # A total is a COUNT only when nothing could have been missed or misread: a truncated read, an unreadable line or an empty read
    # makes it a lower bound, and the count itself reads null (N.8: never the readable-part total standing in for the whole).
    exact = not truncated and not unreadable and entries_returned > 0
    shown = []
    for summary in summaries:
        ids = by_class.get(summary["event_class"], [])
        read_kinds = dict(sorted(kinds_by_class.get(summary["event_class"], {}).items()))
        shown.append({**summary,
                      "read_counts_by_kind_reason": read_kinds if exact else None,
                      "read_counts_by_kind_reason_lower_bound": read_kinds,
                      "records_match_summary": (len(ids) == summary["records"]) if exact and summary["records"] is not None else None,
                      "counts_by_kind_match_summary": (read_kinds == summary["counts_by_kind_reason"]) if exact and summary["counts_by_kind_reason"] is not None else None,
                      "digest_matches_records": (hashlib.sha256("\n".join(sorted(ids)).encode("utf-8")).hexdigest() == summary["record_ids_digest"])
                      if exact and summary["record_ids_digest"] is not None else None})
    return {"record_count": len(records) if exact else None, "record_count_lower_bound": len(records),
            "counts_by_kind_reason": dict(sorted(by_kind.items())) if exact else None,
            "counts_by_kind_reason_lower_bound": dict(sorted(by_kind.items())),
            "records_by_event_class": {key: len(ids) for key, ids in sorted(by_class.items())} if exact else None,
            "counts_by_kind_reason_by_event_class": {key: dict(sorted(v.items())) for key, v in sorted(kinds_by_class.items())} if exact else None,
            "duplicate_record_lines": duplicates, "summaries": shown}


def _cursor_key(text):
    """(seconds text, 9-digit fraction) of a strict UTC entry time, orderable as text; None when it is not that shape."""
    match = CURSOR_TIME.fullmatch(text) if isinstance(text, str) else None
    return None if match is None else (match.group(1), (match.group(2) or "").ljust(9, "0"))


def _entry_key(entry):
    """Identity for de-duplicating overlapping pages: insertId, else the whole entry as canonical JSON (never a guess)."""
    insert = entry.get("insertId")
    return insert if isinstance(insert, str) and insert else json.dumps(entry, sort_keys=True, separators=(",", ":"))


def _read_all_pages(name: str, runner, monotonic) -> tuple[list, int, str | None]:
    """Newest-first pages until a short page (complete) or a stop condition. Returns (entries, pages_read, truncation_reason|None)."""
    seen: dict[str, dict] = {}
    cursor = None
    started = monotonic()
    pages = 0
    while True:
        if pages >= LOG_MAX_PAGES:
            return list(seen.values()), pages, "page_cap"
        if pages and monotonic() - started > LOG_BUDGET_S:
            return list(seen.values()), pages, "time_budget"
        page = gcloud_json(logs_read_argv(name, cursor), runner, "logs", shape=list)
        if any(not isinstance(entry, dict) for entry in page):
            raise Refused("logs: an entry is not a JSON object")
        pages += 1
        fresh = 0
        for entry in page:
            key = _entry_key(entry)
            if key not in seen:
                seen[key] = entry
                fresh += 1
        if len(page) < LOG_PAGE_SIZE:                                   # the server had nothing older than this page's oldest entry
            return list(seen.values()), pages, None
        keys = [_cursor_key(entry.get("timestamp")) for entry in page]
        if any(key is None for key in keys):
            return list(seen.values()), pages, "unpageable_time"        # a full page whose oldest time cannot be told: do not guess a cursor
        oldest = min(keys)
        if not fresh or (cursor is not None and _cursor_key(cursor) <= oldest):
            return list(seen.values()), pages, "stuck_cursor"           # a full page of one instant (or no progress): paging cannot move on
        cursor = f"{oldest[0]}.{oldest[1]}Z"


def measure_logs(name: str, runner, monotonic=time.monotonic) -> dict:
    entries, pages, reason = _read_all_pages(name, runner, monotonic)
    # a total order, so equal inputs give equal output whatever order gcloud broke time ties in: newest first, then insertId/JSON
    floor = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
    entries.sort(key=lambda e: (_log_time(e.get("timestamp")) or floor, _entry_key(e)), reverse=True)
    records: dict[tuple[str, str], dict] = {}                          # (event_class, record_id): the id has no event_class in it (stretch_sink.record_id), so classes share ids
    summaries, rows = [], []
    unreadable = duplicates = 0
    for entry in entries:
        when_text = entry.get("timestamp") if isinstance(entry.get("timestamp"), str) else None
        when = _log_time(when_text)
        for line in _entry_lines(entry):
            if SINK_SUMMARY_MARK in line:
                summary = _read_sink_summary(_object_from(line[line.index(SINK_SUMMARY_MARK) + len(SINK_SUMMARY_MARK):]))
                if summary is None:
                    unreadable += 1
                else:
                    summaries.append(summary)
            elif SINK_MARK in line:
                record = _read_sink_record(_object_from(line[line.index(SINK_MARK) + len(SINK_MARK):]))
                if record is None:
                    unreadable += 1
                elif (record["event_class"], record["record_id"]) in records:
                    duplicates += 1
                else:
                    records[(record["event_class"], record["record_id"])] = record
            elif SUBSTEP_MARK in line:
                step = _read_substep(_object_from(line[line.index("{"):])) if "{" in line else None     # the "[event] " prefix is not part of the JSON
                if step is None:
                    unreadable += 1
                else:
                    rows.append((when, when_text, step))
    truncated = reason is not None
    assets, newest = _substep_report(rows)
    return {
        "execution": name,
        "filter": logs_filter(name),
        "page_size": LOG_PAGE_SIZE,
        "max_pages": LOG_MAX_PAGES,
        "pages_read": pages,
        "entries_returned": len(entries),                               # distinct entries over all pages
        "truncated": truncated,                                         # True: older entries exist that were not read; every count below reads null
        "truncation_reason": reason,
        "unreadable_lines": unreadable,
        "sink": _sink_report(records, summaries, unreadable, duplicates, truncated, len(entries)),
        "substeps": {"last_substep": newest, "assets": assets},      # newest-first reading: the last sub-step is known even when older pages were not read
    }


# ───────────── metrics (SR-BOLD-09): CPU / memory utilisation of one execution from Cloud Monitoring ─────────────

def metrics_filter(metric_type: str) -> str:
    """Constants only; the execution is scoped by the time window (the metric label that would name it is not relied on)."""
    return (f'metric.type="{metric_type}" AND resource.type="{METRICS_RESOURCE_TYPE}" '
            f'AND resource.labels.job_name="{JOB}" AND resource.labels.location="{REGION}"')


def metrics_read_argv(metric_type: str, start: str, end: str) -> list[str]:
    # (I) INTERPRETATION: `gcloud monitoring time-series list` with these flags is the read route; no live call was made for this build.
    return ["gcloud", "monitoring", "time-series", "list", f"--filter={metrics_filter(metric_type)}", f"--interval-start-time={start}",
            f"--interval-end-time={end}", f"--project={PROJECT}", "--format=json"]


def _utc(value):
    """An ISO-8601 time that carries a zone -> aware UTC datetime; None when absent, naive or unreadable."""
    try:
        moment = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return moment.astimezone(dt.timezone.utc) if moment.tzinfo is not None else None


def _number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and value == value and abs(value) != float("inf") else None


def _buckets(options):
    """Distribution.bucketOptions -> [(lower|None, upper|None)] with None marking the open under/overflow ends; None when unreadable."""
    if not isinstance(options, dict) or len(options) != 1:
        return None
    kind, spec = next(iter(options.items()))
    if not isinstance(spec, dict):
        return None
    if kind == "explicitBuckets":
        bounds = spec.get("bounds")
        edges = bounds if isinstance(bounds, list) and bounds and all(_number(b) is not None for b in bounds) else None
        if edges is None or any(b >= c for b, c in zip(edges, edges[1:])):
            return None
    else:
        count = spec.get("numFiniteBuckets")
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 10000:
            return None
        if kind == "linearBuckets":
            width, offset = _number(spec.get("width")), _number(spec.get("offset", 0))
            if width is None or width <= 0 or offset is None:
                return None
            edges = [offset + i * width for i in range(count + 1)]
        elif kind == "exponentialBuckets":
            factor, scale = _number(spec.get("growthFactor")), _number(spec.get("scale"))
            if factor is None or factor <= 1 or scale is None or scale <= 0:
                return None
            edges = [scale * factor ** i for i in range(count + 1)]
        else:
            return None
    return [(None, edges[0])] + list(zip(edges, edges[1:])) + [(edges[-1], None)]


def _distribution(value):
    """One point's distribution -> (count, mean, buckets, bucket_counts); None when any part is unreadable (never a partial point)."""
    body = value.get("distributionValue") if isinstance(value, dict) else None
    if not isinstance(body, dict):
        return None
    count, mean, buckets = parse_int64(body.get("count")), _number(body.get("mean")), _buckets(body.get("bucketOptions"))
    raw = body.get("bucketCounts")
    if count is None or buckets is None or not isinstance(raw, list) or len(raw) != len(buckets):
        return None
    counts = [parse_int64(c) for c in raw]
    if any(c is None for c in counts) or sum(counts) != count or (count and mean is None):
        return None
    return count, mean, buckets, counts


def _series_report(series, metric_type):
    """Pool every point of every returned series. status: OK | ABSENT (nothing in the window) | UNREADABLE (a shape that is not a distribution)."""
    empty = {"metric_type": metric_type, "status": "ABSENT", "series": 0, "points": 0, "samples": 0, "mean": None, "p95": None, "max_upper_bound": None}
    points = []
    for one in series:
        kind = (one.get("metric") or {}).get("type") if isinstance(one, dict) and isinstance(one.get("metric"), dict) else None
        if kind != metric_type:
            return {**empty, "status": "UNREADABLE", "reason": "a series is not the requested metric type"}
        raw = one.get("points")
        if not isinstance(raw, list):
            return {**empty, "status": "UNREADABLE", "reason": "a series carries no points list"}
        for point in raw:
            read = _distribution(point.get("value") if isinstance(point, dict) else None)
            if read is None:
                return {**empty, "status": "UNREADABLE", "reason": "a point is not a well-formed distribution"}
            points.append(read)
    live = [p for p in points if p[0]]
    report = {**empty, "series": len(series), "points": len(points)}
    if not live:
        return report                                               # nothing sampled: ABSENT, and no number is invented for it
    total = sum(p[0] for p in live)
    report.update(status="OK", samples=total, mean=sum(p[0] * p[1] for p in live) / total)
    tops = []
    for _, _, buckets, counts in live:
        top = max(i for i, c in enumerate(counts) if c)
        tops.append(buckets[top][1])
    report["max_upper_bound"] = None if any(t is None for t in tops) else max(tops)       # an open overflow bucket has no upper bound
    shapes = {tuple(p[2]) for p in live}
    if len(shapes) == 1:                                            # percentile only across one bucket layout; mixed layouts read null
        buckets, pooled = live[0][2], [sum(col) for col in zip(*[p[3] for p in live])]
        target, running = P95 * total, 0
        for (low, high), count in zip(buckets, pooled):
            if running + count >= target and count:
                report["p95"] = None if low is None or high is None else low + (high - low) * ((target - running) / count)
                break
            running += count
    return report


def _vcpus(text):
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(m?)", text) if isinstance(text, str) else None
    if not match:
        return None
    value = float(match.group(1)) / (1000 if match.group(2) else 1)
    return value if value > 0 else None


def _bytes(text):
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(Mi|Gi)", text) if isinstance(text, str) else None
    return None if not match else float(match.group(1)) * (1024 ** 2 if match.group(2) == "Mi" else 1024 ** 3)


def _cpu_shape(report, vcpus):
    """Where the CPU sits against what was allocated. None when the numbers it needs are absent (N.8: no verdict without a measurement)."""
    mean, p95 = report["mean"], report["p95"]
    if report["status"] != "OK" or vcpus is None or mean is None or p95 is None:
        return {"allocated_vcpus": vcpus, "mean_vcpus": None, "p95_vcpus": None, "shape": None}
    mean_v, p95_v = mean * vcpus, p95 * vcpus
    low, high = SINGLE_THREAD_BAND
    if p95_v >= SATURATION_FRACTION * vcpus:
        shape = "SATURATES_ALLOCATION_ONE_VCPU" if vcpus <= high else "SATURATES_ALL_VCPUS"
    elif low <= p95_v <= high:
        shape = "SINGLE_THREAD_BOUND" if mean_v >= SUSTAINED_MEAN_VCPU else "BURSTY_AT_ONE_VCPU"      # a burst is not a bound
    elif p95_v < low:
        shape = "BELOW_ONE_VCPU"
    else:
        shape = "MULTI_THREAD_PARTIAL"
    return {"allocated_vcpus": vcpus, "mean_vcpus": mean_v, "p95_vcpus": p95_v, "shape": shape}


def _metric_leg(metric_type, start, end, runner):
    try:
        series = gcloud_json(metrics_read_argv(metric_type, start, end), runner, f"metrics {metric_type}", shape=list)
    except Refused as exc:
        return {"metric_type": metric_type, "status": "QUERY_FAILED", "reason": str(exc), "series": 0, "points": 0, "samples": 0,
                "mean": None, "p95": None, "max_upper_bound": None}
    return _series_report(series, metric_type)


def measure_metrics(execution: dict, job: dict, runner, clock) -> dict:
    start, finish = _utc(execution.get("start_time")), _utc(execution.get("completion_time"))
    end = finish or clock()
    allocated = {"cpu_vcpus": _vcpus(job.get("cpu")), "memory_bytes": _bytes(job.get("memory"))}
    out = {"execution": execution["name"], "scoping": "job_name + location + the execution's own time window (a concurrent execution of the job would be pooled in)",
           "metric_types": {"cpu": CPU_METRIC, "memory": MEMORY_METRIC},
           "wait": {"status": "NOT_EXPOSED", "reason": "Cloud Run exposes no database or container wait metric; DB wait lives in the database's own metrics for a named instance this reader does not hold"},
           "allocated": allocated}
    if start is None or end <= start:
        why = "the execution has no readable start time" if start is None else "the window is empty"
        gone = {"status": "NOT_QUERIED", "reason": why, "mean": None, "p95": None, "max_upper_bound": None}
        return {**out, "window": None, "cpu": {**gone, "allocated_vcpus": allocated["cpu_vcpus"], "mean_vcpus": None, "p95_vcpus": None, "shape": None},
                "memory": {**gone, "peak_bytes_upper_bound": None}}
    begin, stop = start.strftime(METRIC_TIME), end.strftime(METRIC_TIME)
    cpu, memory = _metric_leg(CPU_METRIC, begin, stop, runner), _metric_leg(MEMORY_METRIC, begin, stop, runner)
    limit = allocated["memory_bytes"]
    memory["peak_bytes_upper_bound"] = None if limit is None or memory["max_upper_bound"] is None else memory["max_upper_bound"] * limit
    return {**out, "window": {"start": begin, "end": stop, "end_is_now": finish is None},
            "filters": {"cpu": metrics_filter(CPU_METRIC), "memory": metrics_filter(MEMORY_METRIC)},
            "cpu": {**cpu, **_cpu_shape(cpu, allocated["cpu_vcpus"])}, "memory": memory}


def _check(name: str, observed, ok) -> dict:
    return {"name": name, "observed": observed, "ok": ok}


def measure_verification(runner) -> dict:
    """J-4b-a55j: the verification job's definition against the contract its deploy workflow sets. ONE describe call; every check is computed from it."""
    job = gcloud_json(job_describe_argv(VERIFICATION_JOB), runner, "verification job")
    name = (job.get("metadata") or {}).get("name") if isinstance(job.get("metadata"), dict) else None
    if name != VERIFICATION_JOB:
        raise Refused(f"verification job: the described resource is {name!r}, not {VERIFICATION_JOB!r}")
    outer = job.get("spec", {}).get("template", {}) if isinstance(job.get("spec"), dict) else {}
    task_count = parse_int64(outer.get("spec", {}).get("taskCount")) if isinstance(outer.get("spec"), dict) else None
    template_annotations = ((outer.get("spec") or {}).get("template") or {}).get("metadata", {}).get("annotations", {}) if isinstance(outer.get("spec"), dict) else {}
    task = job_task_spec(job)
    container = only_container(task, "verification job")
    reference = need(container, "image", "verification job")
    if not reference.startswith(IMAGE_REPO + "@"):
        raise Refused("verification job: the image is not referenced by digest of the pipeline repository (this job runs only code built from a commit, by digest)")
    digest = reference[len(IMAGE_REPO) + 1:]
    if not DIGEST.fullmatch(digest):
        raise Refused("verification job: the image is not referenced by digest of the pipeline repository (the digest is not sha256:<64-hex>)")
    shown = environment(container)
    raw = {e["name"]: e for e in container["env"]}
    limits = (container.get("resources") or {}).get("limits") if isinstance(container.get("resources"), dict) else None
    limits = limits if isinstance(limits, dict) else {}
    retries = _count(task.get("maxRetries"), "verification job.maxRetries", required=False)
    timeout = parse_int64(task.get("timeoutSeconds"))
    secret_row = {"name": VERIFIER_SECRET[0], "source": "secret", "secret": VERIFIER_SECRET[1], "version": VERIFIER_SECRET[2]}
    contract_env = (len(shown) == 3 and secret_row in shown
                    and {e["name"] for e in shown if e["source"] == "value"} == VERIFIER_PLAIN_ENV)
    runner_digest = raw.get("GOCHARA_RUNNER_IMAGE_DIGEST", {}).get("value")
    runner_commit = raw.get("GOCHARA_RUNNER_COMMIT", {}).get("value")
    checks = [
        _check("image_by_digest_of_pipeline_repo", reference, True),
        _check("service_account_is_the_verifier_runtime", task.get("serviceAccountName"), task.get("serviceAccountName") == VERIFIER_SERVICE_ACCOUNT),
        _check("command_is_the_verifier_entry_point", container.get("command"), container.get("command") == VERIFIER_COMMAND),
        _check("environment_is_exactly_the_contract", [e["name"] for e in shown], contract_env),
        _check("runner_digest_equals_image_digest", runner_digest == digest, runner_digest == digest),
        _check("runner_commit_is_a_full_commit", isinstance(runner_commit, str) and bool(COMMIT_40.fullmatch(runner_commit)),
               isinstance(runner_commit, str) and bool(COMMIT_40.fullmatch(runner_commit))),
        _check("task_count_is_one", task_count, task_count == 1),
        _check("cloudsql_instance_is_the_amjis_instance", template_annotations.get("run.googleapis.com/cloudsql-instances") if isinstance(template_annotations, dict) else None,
               isinstance(template_annotations, dict) and template_annotations.get("run.googleapis.com/cloudsql-instances") == CLOUDSQL_INSTANCE),
        _check("max_retries_is_zero", retries, None if retries is None else retries == 0),        # proto3 omits a zero: unknown here, settled by the v2 REST read (workflow F-R15-3)
        _check("resources_8Gi_2cpu_7200s", {"memory": limits.get("memory"), "cpu": limits.get("cpu"), "timeout_seconds": timeout},
               limits.get("memory") == "8Gi" and limits.get("cpu") == "2" and timeout == 7200),
    ]
    oks = [c["ok"] for c in checks]
    return {
        "schema": SCHEMA,
        "status": "MEASURED",
        "project": PROJECT,
        "region": REGION,
        "job": {"name": VERIFICATION_JOB, "image": {"reference": reference, "digest": digest}, "service_account": task.get("serviceAccountName"),
                "command": container.get("command"), "environment": shown},
        "checks": checks,
        "all_checks_ok": False if any(o is False for o in oks) else (None if any(o is None for o in oks) else True),
        "disabled_half": "the executor table entry verification_job (enabled false) — this kind starts, schedules and executes nothing",
    }


def measure(execution: str | None, runner=default_runner, clock=lambda: dt.datetime.now(dt.timezone.utc), *, logs: bool = False, metrics: bool = False) -> dict:
    if execution is not None and not EXECUTION.fullmatch(execution):
        raise Refused("the execution name is not brahma-build-pipeline-job-<suffix>")
    if logs and execution is None:
        raise Refused("logs can only be read for one execution: --logs requires --execution")
    if metrics and execution is None:
        raise Refused("metrics can only be read for one execution: --metrics requires --execution")
    job, commit = measure_job(runner)
    record = {
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
        "logs": measure_logs(execution, runner) if logs else None,
    }
    if metrics:                                                          # the key exists only when asked: a run without --metrics prints what it always printed
        record["metrics"] = measure_metrics(record["execution"], job, runner, clock)
    return record


def cli(argv=None, runner=default_runner) -> int:
    parser = argparse.ArgumentParser(description="Read-only measurement of the pipeline Cloud Run job.", allow_abbrev=False)
    parser.add_argument("--execution", default=None)
    parser.add_argument("--job", default=None, choices=(VERIFICATION_JOB,))      # J-4b-a55j: the pipeline job is the default and is not selectable
    parser.add_argument("--logs", nargs="?", const="true", default=None, choices=("true", "True"))      # the executor appends `--logs true`
    parser.add_argument("--metrics", nargs="?", const="true", default=None, choices=("true", "True"))      # SR-BOLD-09
    args = parser.parse_args(argv)                                       # any other argument exits 2 before a cloud call
    try:
        if args.job is not None:
            if args.execution is not None or args.logs is not None or args.metrics is not None:
                raise Refused("--job reads the verification job's definition alone; it does not combine with --execution, --logs or --metrics")
            record = measure_verification(runner)
            print(json.dumps(record, sort_keys=True, separators=(",", ":")), flush=True)
            return 0
        record = measure(args.execution, runner, logs=args.logs is not None, metrics=args.metrics is not None)
        code = 0
    except Refused as exc:
        record, code = {"schema": SCHEMA, "status": "REFUSED", "reason": str(exc)}, 1
    print(json.dumps(record, sort_keys=True, separators=(",", ":")), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(cli())
