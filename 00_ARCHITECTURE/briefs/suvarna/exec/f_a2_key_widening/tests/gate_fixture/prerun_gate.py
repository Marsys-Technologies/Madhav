#!/usr/bin/env python3
"""GATE_V2: pre-run gate for every production data-plane executor / dispatch (stdlib only, read-only, fails closed).

Reads, in THIS invocation:
  (a) deploy_runs_not_completed : runs of the deploy.yml workflow on ANY ref whose status != completed (deploy.yml accepts
      workflow_dispatch from any ref, so a dispatched deploy on a feature ref must be seen), EXCEPT event == pull_request
      (build-only runs); an unknown or missing event is counted (fail closed). Counted over the UNION BY databaseId of
      `gh run list -R Marsys-Technologies/Madhav --workflow deploy.yml --limit 100 --json databaseId,status,event`
      and one `--status <s>` query (same --limit 100) for each of queued, in_progress, waiting, pending, requested
      (a stuck run older than the newest 100 is still found by its status query; a per-status query that returns a FULL
      --limit page containing pull_request runs fails closed, because a non-PR run could be hidden behind them).
      The repository is PINNED (-R) and GH_REPO / GH_HOST / GH_ENTERPRISE_TOKEN / GITHUB_ENTERPRISE_TOKEN / GITHUB_REPOSITORY are
      removed from gh's environment (the token variables gh needs are kept).
  (b) build_runs_in_flight      : build_runs in state planned/running/paused on ANY chart, read through psql as the
      read-only role in ONE call that also reports `current_user` and `current_database()`; the role must be exactly
      suvarna_reader and the database exactly amjis.
      The psql subshell must SOURCE ~/.config/suvarna/pgenv.sh successfully (no fallback to ambient PG* variables:
      every PG* variable is removed from the subshell's environment before the file is sourced).
PRINTS BOTH COUNTS to STDERR ("n/a" for one that could not be read), then one final grep-able line:
  GATE_V2 deploy_runs_not_completed=<n> build_runs_in_flight=<m> role=<role> OK     (exit 0)
  GATE_V2 FAIL <reason>                                                              (exit non-zero)
EVERY exit path prints exactly one GATE_V2 line, also an unexpected internal error: `GATE_V2 FAIL internal_error <ExceptionClassName>`
(exit 2; no message text). STDOUT IS ALWAYS EMPTY. Never prints a credential, a child process's output, or row content.

Exit codes:
   0  both counts read and both are 0, role is suvarna_reader
   1  at least one count is > 0
   2  a read failed or its output was malformed / empty / not UTF-8 / timed out / non-zero exit, or an internal error (fail closed)
  94  a required binary (gh, psql, bash) is missing
  95  a test-only environment variable is set outside the test harness (ORPH_TEST_EVIDENCE_ROOT, PYTEST_CURRENT_TEST)
  96  the psql session is not suvarna_reader, or not connected to the amjis database (message names the unexpected value only)
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
EXPECTED_DATABASE = "amjis"
REPO = "Marsys-Technologies/Madhav"                      # pinned: gh is always called with -R REPO
WORKFLOW = "deploy.yml"
HISTORY_LIMIT = 100
EXCLUDED_EVENT = "pull_request"                          # build-only runs (deploy.yml build-check job); every other or unknown event counts
GH_STRIPPED_ENV = ("GH_REPO", "GH_HOST", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "GITHUB_REPOSITORY")
MAX_COUNT_DIGITS = 12
NON_COMPLETED_STATUSES = ("queued", "in_progress", "waiting", "pending", "requested")
TIMEOUT_S = 60
BUILD_SQL = ("SELECT current_user, current_database(), count(*) FROM public.build_runs "
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
    """Run argv (own process group, killed on timeout). Returns (rc, stdout BYTES; decode with decode_out). Child stderr is discarded, never echoed."""
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=env, cwd=HERE, start_new_session=True)
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


def decode_out(out, label):
    """Strict UTF-8 (never errors='replace'): output that is not valid UTF-8 is a failed read, not a crash."""
    try:
        return out.decode("utf-8")
    except UnicodeDecodeError:
        raise GateError(EXIT_READ_FAILED, label + " output is not valid UTF-8")


def parse_runs(out, label, allow_empty):
    if not out or not out.strip():
        raise GateError(EXIT_READ_FAILED, label + " returned empty output")
    try:
        data = json.loads(out)
    except (ValueError, RecursionError):                 # ValueError covers JSONDecodeError and an over-long integer literal
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


def gh_env(environ):
    """Environment for gh: nothing may redirect it to another repository or host; the token variables gh needs are kept."""
    return {k: v for k, v in environ.items() if k not in GH_STRIPPED_ENV}


def read_deploys(gh, environ, timeout):
    base = [gh, "run", "list", "-R", REPO, "--workflow", WORKFLOW, "--limit", str(HISTORY_LIMIT),
            "--json", "databaseId,status,event"]         # NO --branch: deploy.yml runs from workflow_dispatch on any ref
    queries = [("gh history", base, False, False)]
    for s in NON_COMPLETED_STATUSES:
        queries.append(("gh --status " + s, base + ["--status", s], True, True))
    not_completed = {}                                   # databaseId -> True if ANY observation is non-completed
    for label, argv, allow_empty, saturation_matters in queries:
        rc, out = run_cmd(argv, gh_env(environ), timeout, label)
        if rc != 0:
            raise GateError(EXIT_READ_FAILED, "%s failed (rc=%d)" % (label, rc))
        data = parse_runs(decode_out(out, label), label, allow_empty)
        excluded = 0
        for x in data:
            if x.get("event") == EXCLUDED_EVENT:        # build-only; an unknown / missing / any other event is COUNTED
                excluded += 1
                continue
            not_completed[x["databaseId"]] = not_completed.get(x["databaseId"], False) or x["status"] != "completed"
        if saturation_matters and excluded and len(data) >= HISTORY_LIMIT:
            raise GateError(EXIT_READ_FAILED, "%s returned a full page of %d runs including pull_request runs: a non-PR run may be hidden"
                            % (label, HISTORY_LIMIT))
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
    lines = decode_out(out, "psql").strip().split("\n")
    fields = lines[0].split("|") if len(lines) == 1 else []
    if len(fields) != 3:
        raise GateError(EXIT_READ_FAILED, "psql output malformed")
    role, database, count = fields
    name_ok = lambda n: 1 <= len(n) <= 63 and n.isascii() and all(c.isalnum() or c in "_.$-" for c in n)
    # ASCII decimal digits only (str.isdigit() accepts e.g. a superscript two, which int() rejects), bounded so int() cannot fail
    if not (name_ok(role) and name_ok(database) and 1 <= len(count) <= MAX_COUNT_DIGITS and count.isascii() and count.isdecimal()):
        raise GateError(EXIT_READ_FAILED, "psql output malformed")
    if role != EXPECTED_ROLE:
        raise GateError(EXIT_ROLE, "psql session role is %r, expected %s" % (role, EXPECTED_ROLE))
    if database != EXPECTED_DATABASE:
        raise GateError(EXIT_ROLE, "psql session database is %r, expected %s" % (database, EXPECTED_DATABASE))
    return role, int(count)


def main(environ=None):
    """Prints exactly one GATE_V2 verdict line on EVERY exit path: an unexpected error inside the gate is `GATE_V2 FAIL internal_error
    <ExceptionClassName>` (exit 2, class name only: no message text, no traceback, no secret)."""
    try:
        return _main(environ)
    except BaseException as exc:
        try:
            say("GATE_V2 FAIL internal_error " + type(exc).__name__)
        except BaseException:
            pass
        return EXIT_READ_FAILED


def _main(environ=None):
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
