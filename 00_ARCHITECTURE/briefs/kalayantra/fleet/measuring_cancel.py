#!/usr/bin/env python3
"""Governed cancel of ONE running Cloud Run execution of the measuring build (SR-J3-CANCEL-NULL 2(a)).

The executor runs this for the fixed kind `measuring_cancel` (fleet/executor_ops.json) only after ITS admission has bound the target execution to
the execution named in the J-3c `measuring_dispatch` receipt and to an ABORT / stall verdict cited by digest (executor.measuring_cancel_problem);
this script re-checks only what it can see itself: the execution name is a `brahma-build-pipeline-job-<suffix>` execution (refused before any cloud
call otherwise) and the described resource is that execution of that job. It prints ONE line, a `ky.measuring_cancel/1` JSON record.

  --dry-run  plans the calls and makes NONE (the executor's admission has already bound the request; a signed cancel needs this dry run, A8 §3.8).
  read state → RUNNING: one `gcloud run jobs executions cancel` then read the state again (bounded polls: cancel is asynchronous)
             → CANCELLED already: no call (success, changed:false)
             → SUCCEEDED / FAILED already: no call, FAILED record carrying that state (there was nothing to cancel; it is never a green)

`state` in every record is the state READ BACK after the action (RUNNING / CANCELLED / SUCCEEDED / FAILED). Only `CANCELLED` is success: an exit
status of the gcloud call is never taken as the outcome, and a state still RUNNING after the polls is FAILED with that state recorded.
Honest nulls (CLAUDE.md §N.7.6 / §N.8): a state that could not be read is null beside the reason, never a default.

(I) INTERPRETATION: Cloud Run's Execution.status reports `cancelledCount` for cancelled tasks (cloudrun_readback.py already counts it); CANCELLED =
cancelledCount >= 1 with runningCount == 0. No live cancelled execution was captured for this build, so a shape that cannot be read REFUSES (state
null) and never guesses; the first real cancel is the proof of the shape.

Runs from the reviewed tree (a production kind), so it imports its two siblings; the project / region / job constants are cloudrun_readback's."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cloudrun_readback as readback        # noqa: E402  gcloud_json / execution_describe_argv / EXECUTION / PROJECT / REGION / JOB
from scheduler_reaper import request_digest  # noqa: E402  the executor's request digest, byte for byte (its own test pins that)

SCHEMA = "ky.measuring_cancel/1"
Refused = readback.Refused
STATES = ("RUNNING", "CANCELLED", "SUCCEEDED", "FAILED")
POLLS = 12                  # read-backs after the cancel call, until the execution leaves RUNNING
POLL_INTERVAL_S = 10        # 2 minutes in all


def cancel_argv(name: str) -> list[str]:
    return ["gcloud", "run", "jobs", "executions", "cancel", name, f"--project={readback.PROJECT}", f"--region={readback.REGION}", "--quiet"]


def count(value, what: str) -> int:
    if value is None:
        return 0                # protobuf JSON omits a zero count (cloudrun_readback's reading)
    parsed = readback.parse_int64(value)
    if parsed is None:
        raise Refused(f"{what} is missing or not a non-negative integer")
    return parsed


def observe(name: str, runner) -> str:
    """The execution's state as Cloud Run reports it now."""
    resource = readback.gcloud_json(readback.execution_describe_argv(name), runner, "execution")
    meta = resource.get("metadata") if isinstance(resource.get("metadata"), dict) else {}
    if meta.get("name") != name:
        raise Refused(f"execution: the described resource is {meta.get('name')!r}, not {name!r}")
    owner = readback.labels_of(resource).get("run.googleapis.com/job")
    if owner is not None and owner != readback.JOB:                          # cloudrun_readback's reading: an absent label is not a mismatch (the name is matched exactly above)
        raise Refused(f"execution: it belongs to job {owner!r}, not {readback.JOB!r}")
    status = resource.get("status") if isinstance(resource.get("status"), dict) else None
    conditions = status.get("conditions") if status else None
    if not isinstance(conditions, list) or not conditions:
        raise Refused("execution: status.conditions is missing")             # an empty status is never read as zero counts
    completed = None
    for condition in conditions:
        if not isinstance(condition, dict) or not isinstance(condition.get("type"), str) or not isinstance(condition.get("status"), str):
            raise Refused("execution: a condition is malformed")
        if condition["type"] == "Completed":
            completed = condition["status"]
    counts = {key: count(status.get(src), f"execution.status.{src}")
              for key, src in (("succeeded", "succeededCount"), ("failed", "failedCount"), ("running", "runningCount"), ("cancelled", "cancelledCount"))}
    spec = resource.get("spec") if isinstance(resource.get("spec"), dict) else {}
    tasks = count(spec.get("taskCount"), "execution.spec.taskCount") or 1
    if counts["cancelled"] and not counts["running"]:
        return "CANCELLED"
    if counts["failed"] or completed == "False":
        return "FAILED"
    if completed == "True" and counts["succeeded"] == tasks and not counts["running"]:
        return "SUCCEEDED"
    return "RUNNING"


def run(execution: str, dry_run: bool, environ: dict, runner=readback.default_runner, sleep=time.sleep, now: dt.datetime | None = None) -> tuple[int, dict]:
    now = now or dt.datetime.now(dt.timezone.utc)
    try:
        request = json.loads(environ.get("KY_OPERATION_REQUEST") or "null")
    except ValueError:
        request = None
    request = request if isinstance(request, dict) else {}
    record = {"schema": SCHEMA, "action": "cancel", "dry_run": dry_run, "plan": None, "status": None, "reason": None, "project": readback.PROJECT, "region": readback.REGION,
              "job": readback.JOB, "execution": execution if readback.EXECUTION.fullmatch(execution or "") else None,
              "operation_id": request.get("operation_id"), "request_sha256": request_digest(request) if request else None,
              "state_before": None, "changed": False, "state": None, "polls": 0, "gcloud_calls": 0, "measured_at": now.isoformat(timespec="seconds")}
    calls = 0

    def look(what: str) -> str:
        nonlocal calls
        calls += 1
        try:
            return observe(execution, runner)
        except Refused as e:
            raise Refused(f"{what}: {e}") from None

    try:
        if record["execution"] is None:
            raise Refused("execution is not a brahma-build-pipeline-job execution name")
        if dry_run:
            record.update(plan=[readback.execution_describe_argv(execution), cancel_argv(execution), readback.execution_describe_argv(execution)], status="DRY_RUN")
            record["gcloud_calls"] = 0
            return 0, record
        before = record["state_before"] = look("state before")
        record["state"] = before
        if before == "RUNNING":
            calls += 1
            try:
                result = runner(cancel_argv(execution))
            except Exception:
                raise Refused("cancel: gcloud could not be run or timed out") from None
            record["changed"] = True
            if result.returncode:
                raise Refused(f"cancel: gcloud exited {result.returncode}")          # stderr is never relayed (it may name identities)
            for poll in range(POLLS):
                if poll:
                    sleep(POLL_INTERVAL_S)
                record["polls"] = poll + 1
                record["state"] = look("state after")
                if record["state"] != "RUNNING":
                    break
        if record["state"] != "CANCELLED":
            raise Refused(f"the execution reads {record['state']}, not CANCELLED")
        record["status"] = "OK"
    except Refused as e:
        record.update(status="REFUSED" if calls == 0 else "FAILED", reason=str(e))
        if record["changed"] and record["state"] in (None, "RUNNING"):
            try:
                record["state"] = look("state after (recovery read)")           # a cancel whose call errored may still have taken effect
                if record["state"] == "CANCELLED":
                    record.update(status="OK", reason=None)
            except Refused:
                pass
    record["gcloud_calls"] = calls
    return (0 if record["status"] == "OK" else 1), record


def main(argv: list[str] | None = None, environ: dict | None = None, runner=readback.default_runner, sleep=time.sleep, out=sys.stdout) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--execution", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    rc, record = run(args.execution, args.dry_run, os.environ if environ is None else environ, runner, sleep)
    out.write(json.dumps(record, sort_keys=True) + "\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
