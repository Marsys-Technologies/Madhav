#!/usr/bin/env python3
"""Executor child of the kinds `protected_window_dispatch` and `protected_window_dispatch_dryrun` (U-M-01; SR-PREBUILD-ALL; shipped DISABLED).

Dispatches ONE protected schema window of deploy.yml (`gh workflow run deploy.yml --ref main -f <flag>=true ...`), the act that `window.sh` did by hand.

Request args, exactly {flag, ref, head, window_lease_id}: `flag` is one `*_schema_migration` window input of deploy.yml at `head`; `ref` is `main`; `head` is the 40-hex
commit that origin/main (local and remote) is at; `window_lease_id` is the union lease the window runs under and must equal the request's own `lease_id`.

Every refusal happens BEFORE `gh workflow run`: a malformed or extra arg, a ref other than main, a head that is not the live tip of main, a flag that is not a window,
a lease that is not the request's own, and any OTHER ACTIVE production lease (or an unreadable lease table: fail closed) via window_lease_gate, the gate deploy.yml
itself runs. The gate is read again immediately before the dispatch.

The live kind is remote-async like measuring_dispatch: it returns once the run is identified, so reads can run during the window, and prints ONE line
`ky.window_run/1` {run_id, status, conclusion, capability_step_started, latest_step_progress_at, completed_at, steps[]}. The GitHub protected-environment approval
stays a person's act: this program only dispatches and reads; it never calls the approval API. `--dry-run` (the `_dryrun` kind) runs every check, prints
`ky.window_dryrun/1` and calls no `gh workflow run`. An accepted dispatch whose run cannot be identified is exit 1 with run_id null: reconcile, never retry.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import window_lease_gate as gate   # noqa: E402  (the same gate deploy.yml and the Kāla auto-dispatcher run)

WORKFLOW = "deploy.yml"
CAPABILITY_STEP = "Apply exact protected public-schema migrations"   # the deploy.yml step that applies the window's SQL (protected_windows.catalog reads the same name)
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
FLAG_RE = re.compile(r"^[a-z0-9_]{1,80}$")
IDENTIFY_POLLS, IDENTIFY_INTERVAL_S = 18, 5


class Refusal(Exception):
    """A check failed; nothing was dispatched."""


def find_gh() -> str:
    for candidate in (shutil.which("gh"), "/opt/homebrew/bin/gh", "/usr/local/bin/gh"):
        if candidate and os.access(candidate, os.X_OK):
            return candidate
    raise Refusal("the GitHub CLI (gh) is not available to this child")


def repo_root() -> str:
    p = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=30,
                       env={k: v for k, v in os.environ.items() if k not in gate.REPO_LOCATING_VARS})
    if p.returncode:
        raise Refusal("not inside the reviewed working tree")
    return p.stdout.strip()


def run(argv, cwd, timeout=120):
    # stderr is never echoed: a credentialed client may put connection details in it
    env = {k: v for k, v in os.environ.items() if k not in gate.REPO_LOCATING_VARS}
    try:
        return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refusal(f"{Path(argv[0]).name} could not run ({type(exc).__name__})") from exc


def gh_json(gh, repo, *args):
    p = run([gh, *args], repo)
    if p.returncode:
        raise Refusal(f"gh {args[0]} failed with exit {p.returncode}")
    try:
        return json.loads(p.stdout)
    except ValueError as exc:
        raise Refusal(f"gh {args[0]} returned non-JSON evidence") from exc


def window_flags(repo, head):
    """The protected schema windows deploy.yml declares at `head` (the SR-A6-GCW catalog); anything unreadable fails closed."""
    try:
        import protected_windows as pw
        return set(pw.catalog(pw.GitSource(repo), head))
    except Exception as exc:    # ImportError (no PyYAML), a missing file, an unknown selection shape
        raise Refusal(f"the protected window catalog at {head[:12]} cannot be read ({type(exc).__name__})") from exc


def request_lease() -> str:
    try:
        return str(json.loads(os.environ["KY_OPERATION_REQUEST"]).get("lease_id") or "")
    except (KeyError, ValueError, AttributeError):
        return ""


def lease_check(repo, lease):
    ok, why = gate.verdict(gate.read_table(repo), lease)
    if not ok:
        raise Refusal(why)
    return why


def plan(args, gh, repo, *, dry_run):
    """Every refusal, in order; returns the evidence dict when the window may be dispatched."""
    if args.ref != "main":
        raise Refusal("ref must be main")
    if not HEAD_RE.fullmatch(args.head):
        raise Refusal("head must be a full 40-hex commit")
    if not FLAG_RE.fullmatch(args.flag):
        raise Refusal("flag is not a workflow input name")
    if not gate.SAFE_ID.fullmatch(args.window_lease_id):
        raise Refusal("window_lease_id is not a valid lease id")
    own = request_lease()
    if own and own != args.window_lease_id:
        raise Refusal("window_lease_id is not the request's own lease_id")
    if not own and not dry_run:
        raise Refusal("the request carries no lease_id")
    f = run(["git", "fetch", "-q", "origin", "main"], repo, 120)
    if f.returncode:
        raise Refusal("origin/main cannot be refreshed")
    tip = run(["git", "rev-parse", "--verify", "origin/main^{commit}"], repo, 30)
    remote = gh_json(gh, repo, "api", "repos/{owner}/{repo}/git/ref/heads/main").get("object", {}).get("sha")
    if tip.returncode or tip.stdout.strip() != args.head or remote != args.head:
        raise Refusal("head is not the current tip of main (main moved, or the head is stale)")
    if args.flag not in window_flags(repo, args.head):
        raise Refusal(f"flag {args.flag} is not a protected schema window of deploy.yml at the head")
    return {"flag": args.flag, "ref": args.ref, "head": args.head, "window_lease_id": args.window_lease_id,
            "lease_gate": lease_check(repo, args.window_lease_id)}


def deploy_runs(gh, repo, head):
    rows = gh_json(gh, repo, "run", "list", "--workflow", WORKFLOW, "--event", "workflow_dispatch", "--commit", head,
                   "--limit", "100", "--json", "databaseId,headSha,event")
    if not isinstance(rows, list):
        raise Refusal("invalid workflow run list")
    return [r["databaseId"] for r in rows if r.get("headSha") == head and r.get("event") == "workflow_dispatch"]


def window_run_line(view):
    """ky.window_run/1 from one `gh run view --json databaseId,status,conclusion,jobs` document."""
    steps = []
    for job in view.get("jobs") or []:
        for step in job.get("steps") or []:
            steps.append({"job": job.get("name"), "name": step.get("name"), "status": step.get("status"),
                          "conclusion": step.get("conclusion") or None,
                          "started_at": step.get("startedAt") or None, "completed_at": step.get("completedAt") or None})
    moments = [t for s in steps for t in (s["started_at"], s["completed_at"]) if t]
    finished = [j.get("completedAt") for j in view.get("jobs") or [] if j.get("completedAt")]
    done = view.get("status") == "completed"
    return {"schema": "ky.window_run/1", "run_id": view.get("databaseId"), "status": view.get("status"),
            "conclusion": view.get("conclusion") or None,
            "capability_step_started": any(s["name"] == CAPABILITY_STEP and s["status"] in ("in_progress", "completed") for s in steps),
            "latest_step_progress_at": max(moments) if moments else None,
            "completed_at": max(finished) if (done and finished) else None, "steps": steps}


def dispatch(args, gh, repo, evidence, *, sleep=time.sleep):
    previous = deploy_runs(gh, repo, args.head)
    lease_check(repo, args.window_lease_id)     # immediately before the external mutation
    p = run([gh, "workflow", "run", WORKFLOW, "--ref", args.ref, "-f", "ci_gate=require-ci-green",
             "-f", f"window_lease_id={args.window_lease_id}", "-f", f"{args.flag}=true"], repo, 60)
    if p.returncode:
        raise Refusal("workflow dispatch failed or is uncertain; inspect before any retry")
    new = []
    for attempt in range(IDENTIFY_POLLS):
        new = [r for r in deploy_runs(gh, repo, args.head) if r not in previous]
        if len(new) == 1:
            return window_run_line(gh_json(gh, repo, "run", "view", str(new[0]), "--json", "databaseId,status,conclusion,jobs")), True
        if attempt + 1 < IDENTIFY_POLLS:
            sleep(IDENTIFY_INTERVAL_S)
    return {"schema": "ky.window_run/1", "run_id": None, "status": "dispatched_unidentified", "conclusion": None,
            "capability_step_started": False, "latest_step_progress_at": None, "completed_at": None, "steps": [],
            "candidates": len(new)}, False


def main(argv=None, *, gh=None, repo=None, sleep=time.sleep):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], allow_abbrev=False)
    for name in ("flag", "ref", "head", "window_lease_id"):
        ap.add_argument(f"--{name}", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    try:
        gh, repo = gh or find_gh(), repo or repo_root()
        evidence = plan(args, gh, repo, dry_run=args.dry_run)
        if args.dry_run:
            print(json.dumps({"schema": "ky.window_dryrun/1", "verdict": "OK", **evidence}, sort_keys=True))
            return 0
        line, identified = dispatch(args, gh, repo, evidence, sleep=sleep)
        print(json.dumps(line, sort_keys=True))
        if not identified:
            print("protected window dispatched but its run could not be identified; reconcile, never retry", file=sys.stderr)
        return 0 if identified else 1
    except Refusal as exc:
        print(f"REFUSED protected-window dispatch: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
