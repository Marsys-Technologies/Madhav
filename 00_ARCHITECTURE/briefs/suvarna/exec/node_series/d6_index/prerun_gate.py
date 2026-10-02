#!/usr/bin/env python3
"""Pre-run gate for any production data-plane executor (stdlib only; read-only; fails closed).

Reads, in THIS invocation:
  (a) deploy_runs_not_completed : number of main-branch runs of the deploy.yml workflow whose status != completed
        gh run list --workflow deploy.yml --branch main --limit 20 --json status
  (b) build_runs_in_flight      : number of build_runs in state planned/running/paused on ANY chart
        psql as suvarna_reader (subshell sourcing ~/.config/suvarna/pgenv.sh):
        SELECT count(*) FROM public.build_runs WHERE state IN ('planned','running','paused')
PRINTS BOTH COUNTS ("n/a" for one that could not be read) and exits:
  0  both counts read and both are 0
  1  at least one count is > 0
  2  a read failed or its output was malformed (fail closed)
Prints only the two counts and a short failure class; never a credential, never row content.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD_SQL = "SELECT count(*) FROM public.build_runs WHERE state IN ('planned','running','paused')"
GH_CMD = ["gh", "run", "list", "--workflow", "deploy.yml", "--branch", "main", "--limit", "20", "--json", "status"]
TIMEOUT = 60


def read_deploys():
    r = subprocess.run(GH_CMD, capture_output=True, text=True, timeout=TIMEOUT, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError("gh failed (rc=%d)" % r.returncode)
    data = json.loads(r.stdout)
    if not isinstance(data, list) or not all(isinstance(x, dict) and isinstance(x.get("status"), str) and x["status"] for x in data):
        raise RuntimeError("gh output malformed")
    return sum(1 for x in data if x["status"] != "completed")


def read_builds():
    # subshell: the environment file is sourced inside it, nothing is exported to this process, output is discarded
    script = 'source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -c "%s"' % BUILD_SQL
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=TIMEOUT)
    if r.returncode != 0:
        raise RuntimeError("psql failed (rc=%d)" % r.returncode)
    out = r.stdout.strip()
    if not re.fullmatch(r"[0-9]+", out):
        raise RuntimeError("psql output malformed")
    return int(out)


def main():
    vals, errs = {}, []
    for name, fn in (("deploy_runs_not_completed", read_deploys), ("build_runs_in_flight", read_builds)):
        try:
            vals[name] = fn()
        except Exception as exc:                      # any failure to read is a failure to pass
            vals[name] = None
            errs.append("%s: %s" % (name, str(exc)[:80] if isinstance(exc, RuntimeError) else type(exc).__name__))
    for name in ("deploy_runs_not_completed", "build_runs_in_flight"):
        print("%s=%s" % (name, "n/a" if vals[name] is None else vals[name]))
    if errs:
        print("GATE FAIL (read failed, fail closed): " + "; ".join(errs))
        return 2
    if vals["deploy_runs_not_completed"] != 0 or vals["build_runs_in_flight"] != 0:
        print("GATE FAIL: a deploy run or a build is in flight")
        return 1
    print("GATE PASS: both counts are 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
