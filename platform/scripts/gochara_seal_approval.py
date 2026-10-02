#!/usr/bin/env python3
"""Extract THE approval of THIS run from GitHub's approval history and write the sealing job's approval file (R12-2).

Input: the JSON array `GET /repos/{owner}/{repo}/actions/runs/{run_id}/approvals` returned for this run. The approver (the steward, under the owner's ruling #2) approves the
`gochara-seal` deployment with a comment that carries — on one line, exactly — the digest of the brief they were shown and the run and attempt it is for:

    brief-digest: <64 lowercase hex>  run: <run id>  attempt: <attempt number>

This script REFUSES (exit 2, reason on stderr, nothing written) when there is no approval of the environment, the latest approval's state is not `approved`, its comment has no
well-formed line (or more than one distinct line), the run id or attempt in the comment is not THIS run/attempt (a stale comment from an earlier attempt), the digest is not
the digest of the retained brief this job re-verified (a changed brief), or the approver login is empty. It never falls back to an older approval: the LATEST approval of the
environment decides. On success it writes `{schema: 'seal_approval/1', brief_digest, run_id, run_attempt, approver_login, approved_by_note}` where the NOTE is built mechanically (ruling id + triggering actor + the fixed statement), never taken from the comment — the file Stream A's
`seal_job` takes as `--approval-file`, which independently re-checks the run id / attempt against GITHUB_RUN_ID / GITHUB_RUN_ATTEMPT and the digest against its own recompute."""
from __future__ import annotations

import argparse
import json
import re
import sys

_LINE = re.compile(r"^\s*brief-digest:\s*([0-9a-f]{64})\s+run:\s*(\d+)\s+attempt:\s*(\d+)\s*$")
RULING = "NATIVE_DIRECT_RULINGS_20261002 #2"


def mechanical_note(triggering_actor: str) -> str:
    """The receipt's `approved_by_note` is built MECHANICALLY by the workflow (Fable): the owner ruling id, the GitHub triggering actor and the fixed statement of what the approval is —
    never free text taken from the approver's comment."""
    return f"{RULING}; triggering_actor={triggering_actor}; approved by the steward under the owner's account (not an independent human check)"


class Refused(Exception):
    pass


def extract(history, *, environment: str, run_id: str, attempt: str, brief_digest: str, triggering_actor: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{64}", brief_digest or ""):
        raise Refused("the retained brief's digest is not a sha256")
    if not str(run_id).isdigit() or not str(attempt).isdigit() or int(attempt) < 1:
        raise Refused("this run's id / attempt are not numeric")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}(\[bot\])?", triggering_actor or ""):
        raise Refused("the workflow's triggering actor is not a GitHub login")
    if not isinstance(history, list):
        raise Refused("the approval history is not a JSON array")
    mine = [h for h in history if isinstance(h, dict) and any((e or {}).get("name") == environment for e in (h.get("environments") or []))]
    if not mine:
        raise Refused(f"no approval of environment {environment!r} exists for this run")
    latest = mine[-1]                                          # the API lists the history oldest-first; the LATEST decides, never an older one
    if latest.get("state") != "approved":
        raise Refused(f"the latest review of {environment!r} is {latest.get('state')!r}, not approved")
    login = ((latest.get("user") or {}).get("login") or "").strip()
    if not login:
        raise Refused("the approval names no approver login")
    comment = latest.get("comment")
    if not isinstance(comment, str) or not comment.strip():
        raise Refused("the approval carries no comment: the digest of the approved brief must be stated in it")
    lines = [m for m in (_LINE.match(l) for l in comment.splitlines()) if m]
    if not lines:
        raise Refused("the approval comment has no `brief-digest: <hex>  run: <id>  attempt: <n>` line")
    if len({(m.group(1), m.group(2), m.group(3)) for m in lines}) != 1:
        raise Refused("the approval comment states more than one distinct digest/run/attempt: ambiguous")
    m = lines[0]
    digest, c_run, c_attempt = m.group(1), m.group(2), m.group(3)
    if c_run != str(run_id):
        raise Refused(f"the approval is for run {c_run}, this is run {run_id}")
    if c_attempt != str(attempt):
        raise Refused(f"the approval is for attempt {c_attempt}, this is attempt {attempt}: a stale approval from an earlier attempt")
    if digest != brief_digest:
        raise Refused("the approved digest is not the digest of the retained brief (the brief changed after it was approved, or the wrong brief was approved)")
    return {"schema": "seal_approval/1", "brief_digest": digest, "run_id": int(run_id), "run_attempt": int(attempt),
            "approver_login": login, "approved_by_note": mechanical_note(triggering_actor)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--approvals-file", required=True)
    ap.add_argument("--environment", default="gochara-seal")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--attempt", required=True)
    ap.add_argument("--brief-digest", required=True)
    ap.add_argument("--triggering-actor", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        with open(a.approvals_file, encoding="utf-8") as f:
            history = json.load(f)
        out = extract(history, environment=a.environment, run_id=a.run_id, attempt=a.attempt, brief_digest=a.brief_digest, triggering_actor=a.triggering_actor)
    except (Refused, OSError, ValueError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, sort_keys=True)
    print(f"approval of run {out['run_id']} attempt {out['run_attempt']} by {out['approver_login']} for brief {out['brief_digest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
