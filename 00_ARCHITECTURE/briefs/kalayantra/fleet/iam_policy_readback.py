#!/usr/bin/env python3
"""Read-only MEASUREMENT of the IAM facts of acts 12, 13 and 14 of the Gochara verification-job runbook (C-06; the consumer is
`assemble_precentury.py j4c-a55m --iam-readback <record>`, `judge_iam`).

The executor runs this for the fixed, reviewed, non-production kind `iam_policy_readback`. It takes NO argument: project, region, view, bucket,
job and the one member are constants below, and any argument exits 2 before a call. It issues exactly FOUR fixed, read-only `gcloud` calls
(a `describe` and three `get-iam-policy`; CALLS below is the whole list and every call is checked against it, and against the two read verbs, before
it runs) and prints ONE line, a `ky.iam_readback/1` JSON record:

  {schema, status: MEASURED, measured_at, project,
   act12: {view, bucket, location, filter, bindings: [{role, members: [...]}]},      the log view `gochara_verification_job` and ITS OWN policy
   act13: {job, region, bindings: [{role, members: [...]}]},                          the Cloud Run job `gochara-verification-job` and ITS OWN policy
   act14: {},                                                                         (the fact is read from project_level_roles_of_github_actions)
   project_level_roles_of_github_actions: [role, ...]}                                the roles the project policy grants to GH_ACTOR, nothing else of that policy

  1. gcloud logging views describe gochara_verification_job --bucket=_Default --location=global --project=madhav-astrology
  2. gcloud logging views get-iam-policy gochara_verification_job --bucket=_Default --location=global --project=madhav-astrology
  3. gcloud run jobs get-iam-policy gochara-verification-job --region=asia-south1 --project=madhav-astrology
  4. gcloud projects get-iam-policy madhav-astrology     (filtered in process to the roles of GH_ACTOR; no other member of the project policy is printed)

It reads policies and describes a view. It writes, grants, removes and impersonates nothing. What it cannot show: the NEGATIVE probes of the runbook (a
read of an unrelated resource with the workflow identity) are not a policy fact; they stay a separate, human-run step, and the judge says so under
`not_claimed`. Project-level roles are LISTED, not judged: pre-existing versus added is the act report's before/after.

Honest nulls (CLAUDE.md §N.7.6 / §N.8): a field a response does not carry is never filled in. A record that cannot be read as the thing it claims to be
(a view or policy of another name, a missing or non-text filter, a binding with a field this reader does not know — notably a `condition`, which would make
the grant something other than unconditional —, a role or member that is not text, the same role twice, a policy field it does not know) REFUSES the whole
record — status REFUSED, exit 1 — so a partial record can never be mistaken for evidence. A policy with no `bindings` key is the empty policy (gcloud omits the
key when there are none); it is a measured zero, not a refusal.
Credentials: this script never reads, prints or passes one. `gcloud` uses its own stored identity in the executor's allow-listed environment; the child's
stderr is never relayed (it may name an identity), only its exit status is. The record names roles, the log view and the job; the members it carries are those
of the view's and the job's own policies (the act 12/13 judgment is on them) and the one project-level member it filters on.
Standard library only: the executor copies this single file out of origin/main and runs it, so it cannot import its siblings."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys

SCHEMA = "ky.iam_readback/1"
PROJECT = "madhav-astrology"
REGION = "asia-south1"
JOB = "gochara-verification-job"                                         # .github/workflows/gochara-verification-job-deploy.yml VERIFICATION_JOB
VIEW = "gochara_verification_job"                                        # the narrow log view of the runbook's act 12
BUCKET = "_Default"
LOCATION = "global"
GH_ACTOR = "serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com"
VIEW_NAME = f"projects/{PROJECT}/locations/{LOCATION}/buckets/{BUCKET}/views/{VIEW}"   # the Logging API resource name `describe` returns
VIEW_KEYS = frozenset({"name", "filter", "description", "createTime", "updateTime"})   # the fields of the LogView resource
POLICY_KEYS = frozenset({"bindings", "etag", "version", "auditConfigs"})                # the fields of an IAM Policy resource
BINDING_KEYS = frozenset({"role", "members"})                            # `condition` is deliberately absent: a conditional binding is not the grant it names
ROLE = re.compile(r"(?:roles/[A-Za-z0-9_.]+|(?:projects|organizations)/[A-Za-z0-9_.-]+/roles/[A-Za-z0-9_.]+)")
GCLOUD_TIMEOUT_S = 120
READ_VERBS = frozenset({"describe", "get-iam-policy"})                   # the only gcloud verbs this file may run (read_verb)

_VIEW = [f"--bucket={BUCKET}", f"--location={LOCATION}", f"--project={PROJECT}", "--format=json"]
CALLS = {                                                                # the whole list; nothing outside it is ever run
    "view": ["gcloud", "logging", "views", "describe", VIEW, *_VIEW],
    "view_policy": ["gcloud", "logging", "views", "get-iam-policy", VIEW, *_VIEW],
    "job_policy": ["gcloud", "run", "jobs", "get-iam-policy", JOB, f"--region={REGION}", f"--project={PROJECT}", "--format=json"],
    "project_policy": ["gcloud", "projects", "get-iam-policy", PROJECT, "--format=json"],
}


class Refused(RuntimeError):
    pass


def default_runner(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, timeout=GCLOUD_TIMEOUT_S, check=False, stdin=subprocess.DEVNULL)


def read_verb(argv: list[str]) -> str | None:
    """The gcloud verb of a call: the last command word before the resource name (flags are `--...`). None when there is none."""
    words = [a for a in argv[1:] if not a.startswith("--")]
    return words[-2] if len(words) >= 2 else None


def gcloud_json(call: str, runner) -> dict:
    """One fixed call. It must be one of CALLS and its verb must be a read, else it is refused BEFORE the runner sees it. The child's stderr is never relayed."""
    argv = CALLS.get(call)
    if argv is None or argv[0] != "gcloud":
        raise Refused(f"{call}: not one of the four fixed calls")
    if read_verb(argv) not in READ_VERBS:
        raise Refused(f"{call}: the gcloud verb {read_verb(argv)!r} is not a read")
    try:
        result = runner(list(argv))
    except (OSError, subprocess.SubprocessError):
        raise Refused(f"{call}: gcloud could not be run or timed out") from None
    if result.returncode:
        raise Refused(f"{call}: gcloud exited {result.returncode}")
    try:
        value = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise Refused(f"{call}: gcloud output is not JSON") from None
    if not isinstance(value, dict):
        raise Refused(f"{call}: gcloud output is not a JSON object")
    return value


def read_bindings(policy: dict, call: str) -> list[dict]:
    """[{role, members}] sorted by role, members sorted. An unknown policy field, an unknown binding field or a malformed role or member REFUSES."""
    unknown = sorted(set(policy) - POLICY_KEYS)
    if unknown:
        raise Refused(f"{call}: the policy carries a field this reader does not know ({unknown[0]!r})")
    raw = policy.get("bindings", [])
    if not isinstance(raw, list):
        raise Refused(f"{call}: bindings is not a list")
    out, seen = [], set()
    for binding in raw:
        if not isinstance(binding, dict):
            raise Refused(f"{call}: a binding is not an object")
        unknown = sorted(set(binding) - BINDING_KEYS)
        if unknown:
            raise Refused(f"{call}: a binding carries a field this reader does not know ({unknown[0]!r}); a conditional grant is not judged here")
        role, members = binding.get("role"), binding.get("members")
        if not isinstance(role, str) or not ROLE.fullmatch(role):
            raise Refused(f"{call}: a binding's role is missing or not a role name")
        if not isinstance(members, list) or not members or any(not isinstance(m, str) or not m or m != m.strip() or " " in m for m in members):
            raise Refused(f"{call}: the members of {role} are missing or not text")
        if role in seen:
            raise Refused(f"{call}: {role} is bound twice")
        seen.add(role)
        out.append({"role": role, "members": sorted(set(members))})
    return sorted(out, key=lambda b: b["role"])


def measure(runner=default_runner, clock=lambda: dt.datetime.now(dt.timezone.utc)) -> dict:
    view = gcloud_json("view", runner)
    unknown = sorted(set(view) - VIEW_KEYS)
    if unknown:
        raise Refused(f"view: the response carries a field this reader does not know ({unknown[0]!r})")
    if view.get("name") != VIEW_NAME:
        raise Refused("view: the response is not for the gochara_verification_job view of _Default/global")
    view_filter = view.get("filter")
    if not isinstance(view_filter, str) or not view_filter:
        raise Refused("view: the filter is missing or not text")
    view_bindings = read_bindings(gcloud_json("view_policy", runner), "view_policy")
    job_bindings = read_bindings(gcloud_json("job_policy", runner), "job_policy")
    project_bindings = read_bindings(gcloud_json("project_policy", runner), "project_policy")
    return {
        "schema": SCHEMA,
        "status": "MEASURED",
        "measured_at": clock().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": PROJECT,
        "act12": {"view": VIEW, "bucket": BUCKET, "location": LOCATION, "filter": view_filter, "bindings": view_bindings},
        "act13": {"job": JOB, "region": REGION, "bindings": job_bindings},
        "act14": {},
        "project_level_roles_of_github_actions": sorted(b["role"] for b in project_bindings if GH_ACTOR in b["members"]),
    }


def cli(argv=None, runner=default_runner) -> int:
    parser = argparse.ArgumentParser(description="Read-only measurement of the IAM facts of acts 12-14 (no arguments).", allow_abbrev=False)
    parser.parse_args(argv)                                              # any argument exits 2 before a cloud call
    try:
        record, code = measure(runner), 0
    except Refused as exc:
        record, code = {"schema": SCHEMA, "status": "REFUSED", "reason": str(exc)}, 1
    print(json.dumps(record, sort_keys=True, separators=(",", ":")), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(cli())
