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
SHA256_HEX = re.compile(r"[0-9a-f]{64}")
LOG_TIME = re.compile(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?(Z|[+-]\d\d:\d\d)")


class Refused(RuntimeError):
    pass


def job_describe_argv() -> list[str]:
    return ["gcloud", "run", "jobs", "describe", JOB, f"--project={PROJECT}", f"--region={REGION}", "--format=json"]


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


def measure(execution: str | None, runner=default_runner, clock=lambda: dt.datetime.now(dt.timezone.utc), *, logs: bool = False) -> dict:
    if execution is not None and not EXECUTION.fullmatch(execution):
        raise Refused("the execution name is not brahma-build-pipeline-job-<suffix>")
    if logs and execution is None:
        raise Refused("logs can only be read for one execution: --logs requires --execution")
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
        "logs": measure_logs(execution, runner) if logs else None,
    }


def cli(argv=None, runner=default_runner) -> int:
    parser = argparse.ArgumentParser(description="Read-only measurement of the pipeline Cloud Run job.", allow_abbrev=False)
    parser.add_argument("--execution", default=None)
    parser.add_argument("--logs", nargs="?", const="true", default=None, choices=("true", "True"))      # the executor appends `--logs true`
    args = parser.parse_args(argv)                                       # any other argument exits 2 before a cloud call
    try:
        record = measure(args.execution, runner, logs=args.logs is not None)
        code = 0
    except Refused as exc:
        record, code = {"schema": SCHEMA, "status": "REFUSED", "reason": str(exc)}, 1
    print(json.dumps(record, sort_keys=True, separators=(",", ":")), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(cli())
