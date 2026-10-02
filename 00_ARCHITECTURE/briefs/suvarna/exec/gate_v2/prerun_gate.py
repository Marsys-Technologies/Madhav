#!/usr/bin/env python3
"""GATE_V2: pre-run gate for every production data-plane executor / dispatch (stdlib only, read-only, fails closed).

Reads, in THIS invocation:
  (a) deploy_runs_not_completed : main-branch runs of the deploy.yml workflow whose status != completed, counted over the
      UNION BY databaseId of  `gh run list --workflow deploy.yml --branch main --limit 100 --json databaseId,status`
      and one `--status <s>` query (same --limit 100) for each of queued, in_progress, waiting, pending, requested
      (a stuck run older than the newest 100 is still found by its status query).
  (b) build_runs_in_flight      : build_runs in state planned/running/paused on ANY chart, read through psql as the
      read-only role in ONE call that also reports `current_user`; the role must be exactly suvarna_reader.
      The psql subshell must SOURCE ~/.config/suvarna/pgenv.sh successfully (no fallback to ambient PG* variables:
      every PG* variable is removed from the subshell's environment before the file is sourced).
PRINTS BOTH COUNTS to STDERR ("n/a" for one that could not be read), then one final grep-able line:
  GATE_V2 deploy_runs_not_completed=<n> build_runs_in_flight=<m> role=<role> OK     (exit 0)
  GATE_V2 FAIL <reason>                                                              (exit non-zero)
STDOUT IS ALWAYS EMPTY. Never prints a credential, a child process's output, or row content.

Exit codes:
   0  both counts read and both are 0, role is suvarna_reader
   1  at least one count is > 0
   2  a read failed or its output was malformed / empty / timed out / non-zero exit (fail closed)
  94  a required binary (gh, psql, bash) is missing
  95  a test-only environment variable is set outside the test harness (ORPH_TEST_EVIDENCE_ROOT, PYTEST_CURRENT_TEST)
  96  the psql session is not suvarna_reader (message names the unexpected role only)
  97  `source ~/.config/suvarna/pgenv.sh` failed (missing file or non-zero status)
Test harness only (GATE_V2_UNDER_TEST=1): bypasses ONLY the test-env refusal, honours GATE_V2_PGENV (pgenv path) and
GATE_V2_TIMEOUT_S. Without GATE_V2_UNDER_TEST=1 none of those three is read; the production pgenv path is the real file.
Optional GATE_V2_GH / GATE_V2_PSQL / GATE_V2_BASH carry absolute binary paths (run_gated.sh sets them from `command -v`).
"""
import json
import os
import shutil
import signal
import subprocess
import sys

GATE_VERSION = "GATE_V2"
HERE = os.path.dirname(os.path.abspath(__file__))

EXPECTED_ROLE = "suvarna_reader"
PGENV_PRODUCTION = "~/.config/suvarna/pgenv.sh"
WORKFLOW = "deploy.yml"
BRANCH = "main"
HISTORY_LIMIT = 100
NON_COMPLETED_STATUSES = ("queued", "in_progress", "waiting", "pending", "requested")
TIMEOUT_S = 60
BUILD_SQL = ("SELECT current_user, count(*) FROM public.build_runs "
             "WHERE state IN ('planned','running','paused')")
# argv: 1=pgenv file, 2=psql path, 3=sql. Parameters are captured BEFORE sourcing. 97 can only come from here.
PSQL_SCRIPT = ('f="$1"; p="$2"; q="$3"; '
               '[ -r "$f" ] || exit 97; '
               'source "$f" >/dev/null 2>&1 || exit 97; '
               'exec "$p" -X -A -t -F "|" -c "$q"')

EXIT_OK, EXIT_IN_FLIGHT, EXIT_READ_FAILED = 0, 1, 2
EXIT_MISSING_BINARY, EXIT_TEST_ENV, EXIT_ROLE, EXIT_PGENV = 94, 95, 96, 97
# when several reads fail, the most specific class is reported (lowest rank first)
_RANK = {EXIT_PGENV: 0, EXIT_ROLE: 1, EXIT_MISSING_BINARY: 2, EXIT_READ_FAILED: 3}
TEST_ENV_VARS = ("ORPH_TEST_EVIDENCE_ROOT", "PYTEST_CURRENT_TEST")


class GateError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code, self.msg = code, msg


def say(line):
    """Everything the gate prints goes to STDERR; stdout stays empty."""
    sys.stderr.write(line + "\n")
    sys.stderr.flush()


def under_test(environ):
    return environ.get("GATE_V2_UNDER_TEST") == "1"


def test_env_violation(environ):
    """Name of a set test-only variable, or None. Bypassed only by GATE_V2_UNDER_TEST=1 (the tests' own cases)."""
    if under_test(environ):
        return None
    for name in TEST_ENV_VARS:
        if name in environ:
            return name
    return None


def resolve_bin(name, environ):
    override = environ.get("GATE_V2_" + name.upper())
    path = override if override else shutil.which(name, path=environ.get("PATH"))
    if not path:
        raise GateError(EXIT_MISSING_BINARY, "missing binary: " + name)
    path = os.path.abspath(path)
    if not (os.path.isfile(path) and os.access(path, os.X_OK)):
        raise GateError(EXIT_MISSING_BINARY, "missing binary: " + name)
    return path


def run_cmd(argv, env, timeout, label):
    """Run argv (own process group, killed on timeout). Returns (rc, stdout). Child stderr is discarded, never echoed."""
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, env=env, cwd=HERE, start_new_session=True)
    except (FileNotFoundError, PermissionError):
        raise GateError(EXIT_MISSING_BINARY, "missing binary: " + label)
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            proc.communicate(timeout=5)
        except Exception:
            pass
        raise GateError(EXIT_READ_FAILED, "%s timed out after %ss" % (label, timeout))
    return proc.returncode, out


def parse_runs(out, label, allow_empty):
    if not out or not out.strip():
        raise GateError(EXIT_READ_FAILED, label + " returned empty output")
    try:
        data = json.loads(out)
    except ValueError:
        raise GateError(EXIT_READ_FAILED, label + " output is not JSON")
    if not isinstance(data, list):
        raise GateError(EXIT_READ_FAILED, label + " JSON is not a list")
    for x in data:
        if not (isinstance(x, dict) and isinstance(x.get("databaseId"), int) and not isinstance(x.get("databaseId"), bool)
                and isinstance(x.get("status"), str) and x["status"]):
            raise GateError(EXIT_READ_FAILED, label + " JSON entries malformed")
    if not data and not allow_empty:
        raise GateError(EXIT_READ_FAILED, label + " history is EMPTY (a repo with history never returns zero runs)")
    return data


def read_deploys(gh, environ, timeout):
    base = [gh, "run", "list", "--workflow", WORKFLOW, "--branch", BRANCH, "--limit", str(HISTORY_LIMIT),
            "--json", "databaseId,status"]
    queries = [("gh history", base, False)]
    for s in NON_COMPLETED_STATUSES:
        queries.append(("gh --status " + s, base + ["--status", s], True))
    not_completed = {}                                   # databaseId -> True if ANY observation is non-completed
    for label, argv, allow_empty in queries:
        rc, out = run_cmd(argv, dict(environ), timeout, label)
        if rc != 0:
            raise GateError(EXIT_READ_FAILED, "%s failed (rc=%d)" % (label, rc))
        for x in parse_runs(out, label, allow_empty):
            not_completed[x["databaseId"]] = not_completed.get(x["databaseId"], False) or x["status"] != "completed"
    return sum(1 for v in not_completed.values() if v)


def pgenv_path(environ):
    if under_test(environ) and environ.get("GATE_V2_PGENV"):
        return environ["GATE_V2_PGENV"]
    return os.path.expanduser(PGENV_PRODUCTION)


def clean_env(environ):
    """Environment for the psql subshell: no ambient PG* (only the sourced file may supply them), no BASH_ENV/ENV hooks."""
    return {k: v for k, v in environ.items()
            if not k.startswith("PG") and k not in ("BASH_ENV", "ENV") and not k.startswith("BASH_FUNC_")}


def read_builds(bash, psql, environ, timeout):
    """Returns (role, count); the role and the count come from the SAME psql call."""
    argv = [bash, "--noprofile", "--norc", "-c", PSQL_SCRIPT, "gate_v2", pgenv_path(environ), psql, BUILD_SQL]
    rc, out = run_cmd(argv, clean_env(environ), timeout, "psql")
    if rc == EXIT_PGENV:
        raise GateError(EXIT_PGENV, "sourcing pgenv.sh failed (missing file or non-zero status)")
    if rc != 0:
        raise GateError(EXIT_READ_FAILED, "psql failed (rc=%d)" % rc)
    lines = out.strip().split("\n")
    if len(lines) != 1 or "|" not in lines[0]:
        raise GateError(EXIT_READ_FAILED, "psql output malformed")
    role, _, count = lines[0].partition("|")
    if not (1 <= len(role) <= 63 and all(c.isalnum() or c in "_.$-" for c in role) and count.isdigit()):
        raise GateError(EXIT_READ_FAILED, "psql output malformed")
    if role != EXPECTED_ROLE:
        raise GateError(EXIT_ROLE, "psql session role is %r, expected %s" % (role, EXPECTED_ROLE))
    return role, int(count)


def main(environ=None):
    environ = dict(os.environ if environ is None else environ)
    bad = test_env_violation(environ)
    if bad:
        say("GATE_V2 FAIL test_env_refused: %s is set; the gate is run by operators, not by a test harness" % bad)
        return EXIT_TEST_ENV
    if under_test(environ):
        say("GATE_V2 WARNING under_test=1 (test-env refusal bypassed; pgenv/timeout overrides honoured): not a production run")
    timeout = TIMEOUT_S
    if under_test(environ) and environ.get("GATE_V2_TIMEOUT_S"):
        try:
            timeout = max(1, min(TIMEOUT_S, int(environ["GATE_V2_TIMEOUT_S"])))
        except ValueError:
            pass

    deploys, builds, role, errors = None, None, None, []
    try:
        gh = resolve_bin("gh", environ)
        deploys = read_deploys(gh, environ, timeout)
    except GateError as e:
        errors.append(("deploy_runs_not_completed", e.code, e.msg))
    try:
        bash, psql = resolve_bin("bash", environ), resolve_bin("psql", environ)
        role, builds = read_builds(bash, psql, environ, timeout)
    except GateError as e:
        errors.append(("build_runs_in_flight", e.code, e.msg))
        if e.code == EXIT_ROLE:
            role = e.msg.split("'")[1] if e.msg.count("'") >= 2 else "unknown"

    say("deploy_runs_not_completed=%s" % ("n/a" if deploys is None else deploys))
    say("build_runs_in_flight=%s" % ("n/a" if builds is None else builds))
    if errors:
        code = min((c for _, c, _ in errors), key=lambda c: _RANK.get(c, 9))
        say("GATE_V2 FAIL read_failed (fail closed): " + "; ".join("%s: %s" % (n, m) for n, _, m in errors))
        return code
    if deploys != 0 or builds != 0:
        say("GATE_V2 FAIL in_flight: deploy_runs_not_completed=%d build_runs_in_flight=%d role=%s" % (deploys, builds, role))
        return EXIT_IN_FLIGHT
    say("GATE_V2 deploy_runs_not_completed=%d build_runs_in_flight=%d role=%s OK" % (deploys, builds, role))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
