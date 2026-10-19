#!/usr/bin/env python3
"""Read-only MEASUREMENT of ONE GitHub Actions run of a protected-window workflow (U-M-12; window watch of the W2 / provisioning chain).

The executor runs this for the fixed, reviewed, non-production kind `github_run_readback`. It holds no argument that can change a target:
the repository and the two permitted workflow files are constants below; the only request argument is `--run <id>` (a decimal run id), and
anything else exits before a call. It issues exactly TWO fixed, read-only `gh api -X GET` calls (the run; its jobs with their steps) and
prints ONE line, a `ky.window_run/1` JSON record — the line the watch (PACK watch_obs.py -> watch_gate.py) and the pack filler
(prepare_union.py: `run_id` of the dispatch receipt) read:

  {schema, readback_status, measured_at, repo, run_id, workflow, event, head_sha, run_attempt,
   status, conclusion, capability_step_started, latest_step_progress_at, completed_at, steps[]}

  status / conclusion         the run's own GitHub values (conclusion null until completed). A `completed` run without a conclusion is refused.
  capability_step_started     `started_at` of the one step named exactly `Grant temporary public-schema capability` (deploy.yml
                              jataka-protected-migrations): the moment CREATE on schema public opens, the watch's exposure clock. NULL when the step has
                              not started, or when the run's workflow has no such step (the role-provisioning one-shot has none: that is a null, not a
                              substitute step); `capability_step_found` says which.
  latest_step_progress_at     the newest `started_at` / `completed_at` over every step of every job: the "GitHub run step progress" source of the
                              stall rule. NULL when no step carries a time (a queued run, an approval wait).
  completed_at                the newest job `completed_at`, only when the run is completed (GitHub's run object carries no completion time).
  steps[]                     {job, number, name, status, conclusion, started_at, completed_at} for every step, in job then step order.

Honest nulls (CLAUDE.md §N.7.6 / §N.8): a time GitHub has not set reads null and is never replaced by the clock or by another field; a record
that cannot be read as the thing it claims to be (malformed time, unknown status, a run of another workflow, a jobs list that is cut short, a
response for a different run id) REFUSES the whole record — `readback_status` REFUSED, no `status` key, exit 1 — so a partial record can never
be mistaken for run progress. Reading the line, a consumer that finds no `status` reads NULL (never ABORT, never a stall).
Credentials: this script never reads, prints or passes one. `gh` uses its own stored login in HOME (the executor's allow-listed environment);
the child's stderr is never relayed (it may name an identity), only its exit status is.
Standard library only: the executor copies this single file out of origin/main and runs it, so it cannot import its siblings."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys

SCHEMA = "ky.window_run/1"
REPO = "Marsys-Technologies/Madhav"                                      # git remote origin of this repository
WORKFLOWS = frozenset({
    ".github/workflows/deploy.yml",                                      # protected_window_dispatch: jataka-protected-migrations (window_lease_id input)
    ".github/workflows/gochara-role-provisioning-oneshot.yml",           # gochara_role_provisioning_dispatch (OWNER-GRANTS-MINIMAL-20261018)
})
CAPABILITY_STEP = "Grant temporary public-schema capability"            # deploy.yml, step of jataka-protected-migrations (grant ... / revoke `if: always()`)
RUN_ID = re.compile(r"[1-9][0-9]{0,18}")
STAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")                  # the only shape GitHub writes its times in
RUN_STATUSES = frozenset({"queued", "in_progress", "completed", "waiting", "requested", "pending"})
STEP_STATUSES = frozenset({"queued", "in_progress", "completed", "pending", "waiting"})
CONCLUSIONS = frozenset({"success", "failure", "cancelled", "skipped", "timed_out", "neutral", "action_required", "stale", "startup_failure"})
JOBS_PAGE = 100                                                          # per_page ceiling; a jobs list longer than this is refused, never cut
GH_TIMEOUT_S = 60


class Refused(RuntimeError):
    pass


def run_argv(run_id: str) -> list[str]:
    return ["gh", "api", "-X", "GET", f"repos/{REPO}/actions/runs/{run_id}"]


def jobs_argv(run_id: str) -> list[str]:
    return ["gh", "api", "-X", "GET", f"repos/{REPO}/actions/runs/{run_id}/jobs?per_page={JOBS_PAGE}"]


def default_runner(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, timeout=GH_TIMEOUT_S, check=False, stdin=subprocess.DEVNULL)


def gh_json(argv: list[str], runner, what: str) -> dict:
    """One fixed call. The child's stderr is never relayed; only the exit status is."""
    try:
        result = runner(argv)
    except (OSError, subprocess.SubprocessError):
        raise Refused(f"{what}: gh could not be run or timed out") from None
    if result.returncode:
        raise Refused(f"{what}: gh exited {result.returncode}")
    try:
        value = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise Refused(f"{what}: gh output is not JSON") from None
    if not isinstance(value, dict):
        raise Refused(f"{what}: gh output is not a JSON object")
    return value


def stamp(value, what: str):
    """A GitHub time: None stays None (not yet set); anything else must be the strict UTC shape or the record is refused."""
    if value is None:
        return None
    if not isinstance(value, str) or not STAMP.fullmatch(value):
        raise Refused(f"{what}: a time is not an RFC 3339 UTC second-resolution stamp")
    return value


def newest(values):
    seen = [v for v in values if v is not None]
    return max(seen, key=lambda s: dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")) if seen else None


def word(mapping: dict, key: str, allowed, what: str, *, nullable: bool = False):
    value = mapping.get(key)
    if value is None and nullable:
        return None
    if not isinstance(value, str) or value not in allowed:
        raise Refused(f"{what}: {key!r} is missing or not a value GitHub documents")
    return value


def read_steps(jobs: dict) -> tuple[list[dict], list[str | None]]:
    listed = jobs.get("jobs")
    total = jobs.get("total_count")
    if not isinstance(listed, list) or isinstance(total, bool) or not isinstance(total, int) or total != len(listed):
        raise Refused("jobs: the list is missing, malformed or cut short (total_count differs from the jobs returned)")
    steps: list[dict] = []
    job_ends: list[str | None] = []
    for job in listed:
        name = job.get("name") if isinstance(job, dict) else None
        if not isinstance(name, str) or not name:
            raise Refused("jobs: a job has no name")
        job_ends.append(stamp(job.get("completed_at"), f"job {name!r}"))
        raw_steps = job.get("steps")
        if raw_steps is None:                                            # a job GitHub has not expanded yet (queued) carries no steps
            continue
        if not isinstance(raw_steps, list):
            raise Refused(f"job {name!r}: steps is not a list")
        for step in raw_steps:
            sname = step.get("name") if isinstance(step, dict) else None
            number = step.get("number") if isinstance(step, dict) else None
            if not isinstance(sname, str) or not sname or isinstance(number, bool) or not isinstance(number, int):
                raise Refused(f"job {name!r}: a step has no name or number")
            steps.append({
                "job": name, "number": number, "name": sname,
                "status": word(step, "status", STEP_STATUSES, f"step {sname!r}"),
                "conclusion": word(step, "conclusion", CONCLUSIONS, f"step {sname!r}", nullable=True),
                "started_at": stamp(step.get("started_at"), f"step {sname!r}"),
                "completed_at": stamp(step.get("completed_at"), f"step {sname!r}"),
            })
    return steps, job_ends


def measure(run_id: str, runner=default_runner, clock=lambda: dt.datetime.now(dt.timezone.utc)) -> dict:
    if not RUN_ID.fullmatch(run_id):
        raise Refused("the run id is not a decimal GitHub run id")
    run = gh_json(run_argv(run_id), runner, "run")
    if run.get("id") != int(run_id) or isinstance(run.get("id"), bool):
        raise Refused("run: the response is for a different run id")
    path = run.get("path")
    workflow = path.split("@", 1)[0] if isinstance(path, str) else None
    if workflow not in WORKFLOWS:
        raise Refused("run: not a run of a protected-window workflow this kind may read")
    status = word(run, "status", RUN_STATUSES, "run")
    conclusion = word(run, "conclusion", CONCLUSIONS, "run", nullable=True)
    if (status == "completed") != (conclusion is not None):
        raise Refused("run: a completed run must carry a conclusion and an unfinished one must not")
    attempt = run.get("run_attempt")
    head_sha = run.get("head_sha")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or not isinstance(head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", head_sha):
        raise Refused("run: run_attempt or head_sha is missing or malformed")
    event = run.get("event")
    if not isinstance(event, str) or not event:
        raise Refused("run: event is missing")
    steps, job_ends = read_steps(gh_json(jobs_argv(run_id), runner, "jobs"))
    capability = [s for s in steps if s["name"] == CAPABILITY_STEP]
    if len(capability) > 1:
        raise Refused("steps: the capability step appears more than once; the exposure clock would be ambiguous")
    progress = newest([t for s in steps for t in (s["started_at"], s["completed_at"])])
    return {
        "schema": SCHEMA,
        "readback_status": "MEASURED",
        "measured_at": clock().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": REPO,
        "run_id": int(run_id),
        "workflow": workflow,
        "event": event,
        "head_sha": head_sha,
        "run_attempt": attempt,
        "status": status,
        "conclusion": conclusion,
        "capability_step_found": bool(capability),
        "capability_step_started": capability[0]["started_at"] if capability else None,
        "latest_step_progress_at": progress,
        "completed_at": newest(job_ends) if status == "completed" else None,
        "steps": steps,
    }


def cli(argv=None, runner=default_runner) -> int:
    parser = argparse.ArgumentParser(description="Read-only measurement of one protected-window GitHub Actions run.", allow_abbrev=False)
    parser.add_argument("--run", required=True)
    args = parser.parse_args(argv)                                       # any other argument exits 2 before a call
    try:
        record, code = measure(args.run, runner), 0
    except Refused as exc:
        record, code = {"schema": SCHEMA, "readback_status": "REFUSED", "reason": str(exc)}, 1       # no `status` key: a consumer reads NULL
    print(json.dumps(record, sort_keys=True, separators=(",", ":")), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(cli())
