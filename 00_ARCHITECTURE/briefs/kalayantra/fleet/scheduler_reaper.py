#!/usr/bin/env python3
"""Governed pause / resume / readback of ONE Cloud Scheduler job: the cockpit watchdog `watchdog-reaper` (SR-J3-REAPER-PAUSE).

The executor runs this for the fixed kinds `scheduler_pause`, `scheduler_resume`, their `*_dryrun` twins and the read-only
`scheduler_readback` (fleet/executor_ops.json), and itself runs the `resume` action as the deferred backstop of a pause. It holds no
argument that can change the target: project, region and job are constants below (the defaults of
platform/scripts/provision_watchdog_scheduler.sh, which created the job); `--job` exists only so that any other name is REFUSED before
any cloud call. It prints ONE line, a `ky.scheduler_job/1` JSON record.

  pause    read state → (PAUSED already: no call) | (ENABLED: one `gcloud scheduler jobs pause`) → read state again. Needs `--resume-by`
           (UTC, in the future); the executor, not this script, bounds it by the lease end and arms the backstop before this runs.
  resume   read state → (ENABLED already: no call) | (PAUSED: one `gcloud scheduler jobs resume`) → read state again.
  readback read state, name the acting identity (the principal e-mail only) and test the permissions the governed actions need: the three Cloud Scheduler
           ones and `run.executions.cancel` (the `measuring_cancel` kind, SR-J3-CANCEL-NULL).
  --dry-run  (pause / resume only) plans the calls and makes NONE.

Every record carries `state` = the job state read back AFTER the action (ENABLED / PAUSED, as Cloud Scheduler reports it). A state that
is not the action's target, or a read that fails, is FAILED (exit 1) — an exit status of the gcloud call is never taken as the outcome.
Honest nulls (CLAUDE.md §N.7.6 / §N.8): a value that could not be measured is null with the reason beside it, never a default.

(I) INTERPRETATION: Cloud Scheduler has no job-level `testIamPermissions` (REST reference: jobs have create/delete/get/list/patch/pause/
resume/run only; the scheduler permissions are project-scoped). The permission test therefore runs on the PROJECT with the executor's own
gcloud identity: POST cloudresourcemanager v1 projects/<project>:testIamPermissions, read-only. The access token lives in this process's
memory for that one call; it is never printed, logged or stored.

Standard library only: the executor copies this single file out of origin/main (or a merged commit) and runs it, so it cannot import its
siblings."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

SCHEMA = "ky.scheduler_job/1"
PROJECT = "madhav-astrology"                     # provision_watchdog_scheduler.sh: GCP_PROJECT default
REGION = "asia-south1"                           # provision_watchdog_scheduler.sh: GCP_REGION default
JOB = "watchdog-reaper"                          # provision_watchdog_scheduler.sh: the job it creates
PERMISSIONS = ("cloudscheduler.jobs.pause", "cloudscheduler.jobs.resume", "cloudscheduler.jobs.get", "run.executions.cancel")   # + the one measuring_cancel needs (SR-J3-CANCEL-NULL)
PERMISSION_ENDPOINT = f"https://cloudresourcemanager.googleapis.com/v1/projects/{PROJECT}:testIamPermissions"
KNOWN_STATES = ("ENABLED", "PAUSED", "DISABLED", "UPDATE_FAILED")      # google.cloud.scheduler.v1.Job.State (STATE_UNSPECIFIED reads as unknown)
TARGET_STATE = {"pause": "PAUSED", "resume": "ENABLED"}
GCLOUD_TIMEOUT_S = 120
HTTP_TIMEOUT_S = 30
UTC_STAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:Z|\+00:00)")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]{1,100}@[A-Za-z0-9.-]{1,100}")
TOKEN = re.compile(r"[A-Za-z0-9._~+/=-]{20,4096}")
SAFE_NAME = re.compile(r"[A-Za-z0-9_.-]{1,80}")
UNBOUND_REQUEST_FIELDS = frozenset({"acceptance_receipt", "expires_at"})      # mirrors executor.request_digest, byte for byte


class Refused(RuntimeError):
    pass


def describe_argv() -> list[str]:
    return ["gcloud", "scheduler", "jobs", "describe", JOB, f"--location={REGION}", f"--project={PROJECT}", "--format=json"]


def action_argv(action: str) -> list[str]:
    return ["gcloud", "scheduler", "jobs", action, JOB, f"--location={REGION}", f"--project={PROJECT}", "--quiet"]


def default_runner(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, timeout=GCLOUD_TIMEOUT_S, check=False, stdin=subprocess.DEVNULL)


def default_fetch(url: str, token: str, body: dict) -> dict:
    request = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
        return json.loads(response.read().decode())


def request_digest(req: dict) -> str:
    bound = {k: v for k, v in req.items() if k not in UNBOUND_REQUEST_FIELDS and not k.endswith("_expires_at")}
    return hashlib.sha256(json.dumps(bound, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def parse_resume_by(value: str, now: dt.datetime) -> dt.datetime:
    if not UTC_STAMP.fullmatch(value or ""):
        raise Refused("resume-by must be a UTC timestamp YYYY-MM-DDTHH:MM:SS followed by Z or +00:00")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed <= now:
        raise Refused("resume-by is not in the future")
    return parsed


class Measure:
    """One run: counts every external call so a dry-run can prove it made none."""

    def __init__(self, runner, fetch):
        self.runner, self.fetch, self.calls = runner, fetch, 0

    def gcloud(self, argv: list[str], what: str) -> str:
        self.calls += 1
        try:
            result = self.runner(argv)
        except (OSError, subprocess.SubprocessError):
            raise Refused(f"{what}: gcloud could not be run or timed out") from None
        if result.returncode:
            raise Refused(f"{what}: gcloud exited {result.returncode}")           # stderr is never relayed (it may name identities)
        return result.stdout or ""

    def state(self, what: str) -> str:
        try:
            job = json.loads(self.gcloud(describe_argv(), what))
        except ValueError:
            raise Refused(f"{what}: gcloud output is not JSON") from None
        if not isinstance(job, dict):
            raise Refused(f"{what}: gcloud output is not a JSON object")
        if job.get("name") != f"projects/{PROJECT}/locations/{REGION}/jobs/{JOB}":
            raise Refused(f"{what}: the described job is not {PROJECT}/{REGION}/{JOB}")
        state = job.get("state")
        if state not in KNOWN_STATES:
            raise Refused(f"{what}: job state is missing or not a known Cloud Scheduler state")
        return state

    def identity(self) -> dict:
        try:
            lines = [l.strip() for l in self.gcloud(["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"], "identity").splitlines() if l.strip()]
        except Refused as e:
            return {"principal": None, "reason": str(e)}
        if len(lines) == 1 and EMAIL.fullmatch(lines[0]):
            return {"principal": lines[0], "reason": None}
        return {"principal": None, "reason": "the active gcloud account is missing, ambiguous or not an e-mail principal"}

    def permissions(self) -> dict:
        record = {"checked_on": f"projects/{PROJECT}", "method": "cloudresourcemanager.v1.projects.testIamPermissions",
                  "requested": list(PERMISSIONS), "granted": None, "missing": None, "status": "UNAVAILABLE", "reason": None}
        try:
            token = self.gcloud(["gcloud", "auth", "print-access-token"], "access token").strip()
            if not TOKEN.fullmatch(token):
                raise Refused("access token: gcloud returned no usable token")
            self.calls += 1
            try:
                answer = self.fetch(PERMISSION_ENDPOINT, token, {"permissions": list(PERMISSIONS)})
            except urllib.error.HTTPError as e:
                raise Refused(f"testIamPermissions: HTTP {e.code}") from None
            except (OSError, ValueError):
                raise Refused("testIamPermissions: the call failed") from None
        except Refused as e:
            record["reason"] = str(e)
            return record
        granted = answer.get("permissions", []) if isinstance(answer, dict) else None
        if not isinstance(granted, list) or any(p not in PERMISSIONS for p in granted):
            record["reason"] = "testIamPermissions: unexpected answer shape"
            return record
        record.update(status="MEASURED", granted=[p for p in PERMISSIONS if p in granted], missing=[p for p in PERMISSIONS if p not in granted])
        return record


def run(action: str, dry_run: bool, job: str | None, resume_by: str | None, environ: dict, runner=default_runner, fetch=default_fetch,
        now: dt.datetime | None = None) -> tuple[int, dict]:
    now = now or dt.datetime.now(dt.timezone.utc)
    try:
        request = json.loads(environ.get("KY_OPERATION_REQUEST") or "null")
    except ValueError:
        request = None
    request = request if isinstance(request, dict) else {}
    record = {"schema": SCHEMA, "action": action, "dry_run": dry_run, "status": None, "reason": None, "project": PROJECT, "region": REGION,
              "job": JOB, "requested_job": job if isinstance(job, str) and SAFE_NAME.fullmatch(job) else None,
              "operation_id": request.get("operation_id"), "request_sha256": request_digest(request) if request else None,
              "state_before": None, "changed": False, "state": None, "resume_by": None, "identity": None, "permissions": None,
              "plan": None, "gcloud_calls": 0, "measured_at": now.isoformat(timespec="seconds")}
    measure = Measure(runner, fetch)
    try:
        if job not in (None, JOB):
            raise Refused(f"job is not on the allow-list (only {JOB} in {PROJECT}/{REGION})")
        if action == "pause":
            record["resume_by"] = parse_resume_by(resume_by, now).isoformat(timespec="seconds")
        elif resume_by is not None:
            raise Refused("resume-by belongs to pause only")
        if action == "readback" and dry_run:
            raise Refused("readback has no dry-run")
        if dry_run:
            record["plan"] = [describe_argv(), *([action_argv(action)] if action in TARGET_STATE else []), describe_argv()]
            record["status"] = "DRY_RUN"
        elif action == "readback":
            try:
                record["state"] = measure.state("state")
                record["status"] = "MEASURED"
            except Refused as e:
                record.update(status="PARTIAL", reason=str(e))
            record["identity"] = measure.identity()
            record["permissions"] = measure.permissions()
        else:
            target = TARGET_STATE[action]
            before = measure.state("state before")
            record["state_before"] = before
            if before != target:
                if before != {"pause": "ENABLED", "resume": "PAUSED"}[action]:
                    raise Refused(f"job is {before}; {action} needs the job {'ENABLED' if action == 'pause' else 'PAUSED'} or already {target}")
                measure.gcloud(action_argv(action), action)
                record["changed"] = True
            record["state"] = measure.state("state after")                       # the read-back AFTER the action, always
            if record["state"] != target:
                raise Refused(f"after {action} the job reads {record['state']}, not {target}")
            record["status"] = "OK"
    except Refused as e:
        record.update(status="REFUSED" if record["status"] is None and measure.calls == 0 else "FAILED", reason=str(e))
        if record["state"] is None and record["state_before"] is not None and action in TARGET_STATE and record["changed"]:
            try:
                record["state"] = measure.state("state after (recovery read)")
            except Refused:
                pass
    record["gcloud_calls"] = measure.calls
    return (0 if record["status"] in ("OK", "DRY_RUN", "MEASURED", "PARTIAL") else 1), record


def main(argv: list[str] | None = None, environ: dict | None = None, runner=default_runner, fetch=default_fetch, out=sys.stdout) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--action", choices=("pause", "resume", "readback"), required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--job")
    parser.add_argument("--resume-by", dest="resume_by")
    args = parser.parse_args(argv)
    rc, record = run(args.action, args.dry_run, args.job, args.resume_by, os.environ if environ is None else environ, runner, fetch)
    out.write(json.dumps(record, sort_keys=True) + "\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
