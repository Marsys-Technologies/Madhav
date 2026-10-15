#!/usr/bin/env bash
# kyjob.sh v1.1 — the worker launch (relaunch plan v2.7 §7; packet KV3-B-KYJOB v1). status: built, pending independent review.
#
#   bash $KY_FLEET/kyjob.sh <job_id>
#
# Reads the launch keys of $KY_RUN/jobs/<job_id>/state.json (ky.job/1; written by kyd_jobs.py and finalize.sh), writes
# no state, and REPLACES ITSELF with the plan §7 launch line:
#
#   cd <worktree>; exec /usr/bin/env -i <the allowed names> <claude_bin> -p --setting-sources project
#     --permission-mode … --model … --effort … --max-turns … <extra_lean_flags> --strict-mcp-config --mcp-config …
#     [--disallowedTools …] --output-format stream-json --verbose --add-dir $KY_ROOT  < prompt  > stdout  2> stderr
#
# No fork of the program, no background, no new session: the program is this very process (same pid, same process
# group, same session), so the process-group kill of the caller reaches it and every tool child it starts. The caller
# (kyd_jobs.py; finalize.sh) starts kyjob.sh in a new session and owns the deadline; kyjob.sh only refuses a deadline
# that is missing, past, or later than the launch configuration was qualified for.
#
# The job's whole environment (nothing else survives `env -i`), in this order; a null state key omits its name:
#   HOME PATH LANG TERM USER TMPDIR ZDOTDIR KY_ROOT KY_RUN KY_FLEET KY_STREAM KY_LANE KY_ITEM KY_PY SE_EPHE_PATH
#   SWE_EPHE_PATH TESTS                                  — the quoted line (TESTS = tests[] joined by newlines)
#   KY_SCRATCH JOB_SCRATCH KY_RUN_ID KY_ROLE KY_CONTROLLER_ID   — INTERPRETATION (packet): job_scratch, job_id, role,
#                                                          controller_id
#   PRAVAHA_HOME PRAVAHA_EVENTS PRAVAHA_PLAN_MODEL PRAVAHA_REPO PRAVAHA_HOLD PRAVAHA_URL PRAVAHA_TRACKER_PORT
#                                                        — fixture runs only: the validated fixture{} (§14 B-3)
# PATH is $KY_ROOT/bin:<NODE_BIN>:/opt/homebrew/bin:/usr/bin:/bin, NODE_BIN being the first line of $KY_RUN/NODE_BIN
# when that is an existing absolute directory (kyloop.py child_path). The launch line is kyboot.py's build_launch.
#
# Read from kyjob.sh's OWN environment: KY_ROOT KY_RUN KY_FLEET KY_SCRATCH HOME USER (each required; the paths
# absolute and normalised). Nothing else of it is used, and none of it reaches the job except as listed above.
#
# Refusals come before any launch. Each prints ONE stderr line `kyjob.sh: REFUSED <code>: <reason>` and writes
# <job_scratch>/kyjob.refusal.json {job_id, code, reason, at} — where <job_scratch> is $KY_SCRATCH/jobs/<job_id> and
# already exists (nothing is created to hold a refusal: a malformed command, or a missing scratch folder, is reported
# on stderr alone).
#   64  usage: not exactly one well-formed job id, or one of the six names above unset, empty or not absolute
#   70  cd <worktree> failed (the worktree is not a directory)
#   78  credential: a name matching DATABASE_URL|*_DATABASE_URL|PGPASSWORD|ANTHROPIC_API_KEY is set in kyjob.sh's own
#       environment (names are printed, values are never read); no_wrappers (as kalayantra_fleet.sh): $KY_ROOT/bin
#       holds anything other than ky and kybrief, or cannot be listed
#   65  + the first reason found, in this order:
#       state         unreadable or not one JSON object · a launch key absent · a required key without a text value ·
#                     a path that is not absolute and normalised · job_scratch not $KY_SCRATCH/jobs/<job_id> · the
#                     prompt, output and temporary paths not beneath it · an invalid fixture{}
#       limits        max_turns not a whole number > 0 or above the kind's cap (BUILD 150, REWORK 100, VERIFY and
#                     ARTIFACT 60, PRE-ACCEPT and POST-READBACK 40, RULING and SURROGATE 30, PLAN, MODEL and
#                     REQUEST-PREP 300); a kind without a cap; deadline not `YYYY-MM-DDTHH:MM:SSZ` or not in the future
#       flags         no permission mode · effort not xhigh for PLAN, MODEL, REQUEST-PREP and high otherwise ·
#                     --bare, any permission bypass, or a flag the launch line owns in extra_lean_flags · a
#                     disallowed tool that is a flag
#       boundary      `boundary` neither null nor a name · a verifier kind (VERIFY, ARTIFACT, PRE-ACCEPT,
#                     POST-READBACK) without one · `kyboundary.sh prepare <job_id>` not 0 (never an unsandboxed fallback)
#       program       claude_bin not an executable file · `--version` unreadable or below 2.1.296
#       mcp           not exactly one components[] entry of $KY_RUN/INSTALL_RECEIPT.json has installed_path equal to
#                     mcp_config, or its sha256 is not the file's
#       prompt        not the bytes of card_path, then packet_path, then `--- job header ---` and one JSON object
#                     that names this job (only newlines may separate the three)
#       qualification $KY_RUN/QUALIFICATIONS/<role>-<model>.json is not a ky.qualification/1 with result exactly
#                     "PASS", context "launchd", this role and model, binds equal to this launch for every name of
#                     kyboot.py's BOUND_FACTS plus claude_version, and the launch line flag for flag (portable_argv);
#                     or deadline > now + binds.deadline_seconds. A missing bind or an unobservable value refuses.
# `<claude_bin> --version` is the only time the program runs before the launch, and only after the receipt was found to
# bind the program's path and sha256. It runs with the job's environment, without TMPDIR, in /.
#
# Just before the exec: <job_scratch>/kyjob.launch.json {job_id, cwd, argv, env_names, qualification_sha256, at}.
#
# Verifier boundary: when `boundary` is set, `bash $KY_FLEET/kyboundary.sh prepare <job_id>` must exit 0, and the exec
# becomes `exec /bin/bash $KY_FLEET/kyboundary.sh exec <job_id> -- /usr/bin/env -i … <claude_bin> …`.
#
# INTERPRETATIONS beyond the packet's own, stated rather than hidden:
#   * harness_sha256 is observed as the sha256 of $KY_FLEET/kyqualify.py (kyboot.py reads it from its manifest);
#   * the receipt is not looked up in a manifest here (kyboot.py's "recorded" check): its sha256 goes into
#     kyjob.launch.json for the controller to hold against the installation receipt;
#   * env_names binds the names of THIS launch, so a receipt qualifies the jobs that carry exactly its names;
#   * `boundary` is a name (any non-empty text) or null; fixture{} carries exactly the seven PRAVAHA_* names, valid as
#     KV3-B-WRAPPERS reads them (a port 1024–65535 other than 8767, URL http://127.0.0.1:<port>, the five paths
#     really inside $KY_SCRATCH/fixture/);
#   * header fields item, worktree, branch, base_sha and deadline, where the header carries them, equal the state's.
# Limits: the files are hashed and compared when checked, not again at the instant of the exec; the helper below runs
# under /opt/homebrew/bin/python3 (else /usr/bin/python3), isolated (-I -B), with a six-name environment.
#
# Changelog: v1.1 (2026-10-13) — explicit Codex job adapter; Claude planning unchanged.
# Changelog: v1.0 (2026-10-12) — first version (KV3-B-KYJOB v1).
set -u
umask 077

shopt -s execfail                                         # a launch line that cannot be executed is reported, below
SELF="${BASH_SOURCE[0]}"
case "$SELF" in /*) ;; *) SELF="$PWD/$SELF" ;; esac
say() { printf 'kyjob.sh: REFUSED %s: %s\n' "$1" "$2" >&2; }

[ "$#" -eq 1 ] || { say 64 "usage: bash kyjob.sh <job_id> (exactly one argument)"; exit 64; }
JOB_ID="$1"
case "$JOB_ID" in
  ''|[!A-Za-z0-9]*|*[!A-Za-z0-9._-]*) say 64 "usage: the job id is not of the form [A-Za-z0-9][A-Za-z0-9._-]*"; exit 64 ;;
esac
[ "${#JOB_ID}" -le 128 ] || { say 64 "usage: the job id is longer than 128 characters"; exit 64; }

PY=""
for candidate in /opt/homebrew/bin/python3 /usr/bin/python3; do
  if [ -x "$candidate" ]; then PY="$candidate"; break; fi
done
helper() {   # helper <mode> <args…>: the checks, in an isolated interpreter that sees six names and nothing else
  /usr/bin/env -i HOME="${HOME:-}" USER="${USER:-}" PATH=/usr/bin:/bin KY_ROOT="${KY_ROOT:-}" KY_RUN="${KY_RUN:-}" \
    KY_FLEET="${KY_FLEET:-}" KY_SCRATCH="${KY_SCRATCH:-}" \
    "$PY" -I -B -c 'import sys
source = open(sys.argv[1], encoding="utf-8").read()
code = source.split("\n#>>> " + "kyjob helper\n", 1)[1].split("\n#<<< " + "kyjob helper\n", 1)[0]
exec(compile(code, sys.argv[1], "exec"), {"__name__": "__kyjob__", "ARGV": sys.argv[2:]})' "$SELF" "$@"
}
refuse() {   # refuse <code> <reason>: the record (when the job's scratch folder is there) and the one stderr line
  if [ -n "$PY" ] && [ -n "${KY_SCRATCH:-}" ]; then helper refuse "$JOB_ID" "$1" "$2"; else say "$1" "$2"; fi
  exit "$1"
}

# 78 — names only: a value is never read, compared or printed
credentials=""
codex_credentials=""
for name in $(compgen -e); do
  case "$name" in
    DATABASE_URL|*_DATABASE_URL|PGPASSWORD|ANTHROPIC_API_KEY) credentials="$credentials $name" ;;
    OPENAI_API_KEY|CODEX_API_KEY|AZURE_OPENAI_API_KEY|OPENAI_*TOKEN*|CODEX_*TOKEN*) codex_credentials="$codex_credentials $name" ;;
  esac
done
[ -z "$credentials" ] || refuse 78 "credential variable name set in kyjob.sh's own environment:$credentials"

for name in KY_ROOT KY_RUN KY_FLEET KY_SCRATCH HOME USER; do
  [ -n "${!name:-}" ] || { say 64 "usage: $name is not set in kyjob.sh's own environment"; exit 64; }
done
for name in KY_ROOT KY_RUN KY_FLEET KY_SCRATCH HOME; do
  case "${!name}" in /*) ;; *) say 64 "usage: $name is not an absolute path"; exit 64 ;; esac
done
[ -n "$PY" ] || { say 65 "state: no python3 at /opt/homebrew/bin/python3 or /usr/bin/python3; the job state cannot be read"; exit 65; }

helper plan "$JOB_ID" "$codex_credentials"
status=$?
case "$status" in
  0) ;;
  64|65|70|78) exit "$status" ;;
  *) refuse 65 "state: kyjob.sh's own check ended with status $status; nothing was launched" ;;
esac

PLAN_PATH="$KY_SCRATCH/jobs/$JOB_ID/kyjob.plan"
PLAN=()
while IFS= read -r -d '' part; do PLAN[${#PLAN[@]}]="$part"; done < "$PLAN_PATH"
/bin/rm -f "$PLAN_PATH"
if [ "${#PLAN[@]}" -lt 8 ] || [ "${PLAN[0]}" != "ky.jobplan/1" ]; then
  refuse 65 "state: the launch plan kyjob.sh wrote for itself could not be read back; nothing was launched"
fi

cd "${PLAN[1]}" || refuse 70 "cd ${PLAN[1]} failed"
exec "${PLAN[@]:5}" < "${PLAN[2]}" > "${PLAN[3]}" 2> "${PLAN[4]}"
refuse 65 "state: the launch line could not be executed (exec status $?); nothing was launched"
exit 65

# The helper: read by the loader above from this very file, never executed by bash.
: <<'KYJOB_HELPER_TEXT'
#>>> kyjob helper
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import time

LAUNCH_KEYS = ("job_id key item kind role stream slot worktree branch base_sha head digest verdict_phase "
               "evidence_fp pr registered_head queue_authorised prerequisites test_digests migration_number loop "
               "max_loops model effort permission_mode max_turns deadline claude_bin mcp_config extra_lean_flags "
               "disallowed_tools job_scratch prompt_path stdout_path stderr_path tmp_path tests se_ephe_path "
               "swe_ephe_path card_path packet_path boundary regen fixture locks controller_id").split()
REQUIRED_TEXT = ("job_id", "item", "kind", "role", "worktree", "model", "claude_bin", "mcp_config", "job_scratch",
                 "prompt_path", "stdout_path", "stderr_path", "tmp_path", "card_path", "packet_path")
OPTIONAL_TEXT = ("stream", "slot", "se_ephe_path", "swe_ephe_path", "controller_id")
PATH_KEYS = ("worktree", "claude_bin", "mcp_config", "job_scratch", "prompt_path", "stdout_path", "stderr_path",
             "tmp_path", "card_path", "packet_path", "se_ephe_path", "swe_ephe_path")
BENEATH_JOB_SCRATCH = ("prompt_path", "stdout_path", "stderr_path", "tmp_path")
OWN_ENV = ("KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SCRATCH", "HOME", "USER")
OWN_ENV_PATHS = ("KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SCRATCH", "HOME")
CAMPAIGN_CLI = ("ky", "kybrief")                          # all that $KY_ROOT/bin may hold (no_wrappers)

# plan §7 turn caps; ARTIFACT, SURROGATE, MODEL and REQUEST-PREP as the packet reads them
TURN_CAPS = {"BUILD": 150, "REWORK": 100, "VERIFY": 60, "ARTIFACT": 60, "PRE-ACCEPT": 40, "POST-READBACK": 40,
             "RULING": 30, "SURROGATE": 30, "PLAN": 300, "MODEL": 300, "REQUEST-PREP": 300}
XHIGH_KINDS = ("PLAN", "MODEL", "REQUEST-PREP")
BOUNDED_KINDS = ("VERIFY", "ARTIFACT", "PRE-ACCEPT", "POST-READBACK")    # their finish step reads the boundary check
MIN_VERSION = (2, 1, 296)

# as kyboot.py: FLAGS_NEVER, FLAGS_LAUNCHER_OWNED (plus -p and the disallowed-tools flag, which the line also sets)
FLAGS_NEVER = {
    "--bare": "P-1: it never reads the stored sign-in and accepts only an API key",
    "--dangerously-skip-permissions": "the permission mode is always passed explicitly",
    "--mcp-config": "the MCP configuration is the job's mcp_config, passed once by the launcher",
    "--settings": "settings come from the project only",
    "--setting-sources": "the launcher passes --setting-sources project itself",
}
FLAGS_LAUNCHER_OWNED = ("-p", "--print", "--permission-mode", "--model", "--effort", "--max-turns",
                        "--strict-mcp-config", "--output-format", "--verbose", "--add-dir", "--disallowedTools",
                        "--disallowed-tools")
FLAG_PREFIXES_NEVER = ("--dangerously-", "--allow-dangerously-")

# kyboot.py's BOUND_FACTS: what a receipt must bind beyond its launch line and its program version
BOUND_FACTS = ("claude_bin", "claude_bin_sha256", "model", "effort", "permission_mode", "max_turns",
               "mcp_config_sha256", "env_names", "child_path", "project_settings_sha256", "zdotdir_sha256",
               "harness_sha256")
QUALIFICATION_SCHEMA = "ky.qualification/1"
QUALIFIED_CONTEXT = "launchd"
PRAVAHA_PATHS = ("PRAVAHA_HOME", "PRAVAHA_EVENTS", "PRAVAHA_PLAN_MODEL", "PRAVAHA_REPO", "PRAVAHA_HOLD")
PRAVAHA_NAMES = PRAVAHA_PATHS + ("PRAVAHA_URL", "PRAVAHA_TRACKER_PORT")
LIVE_TRACKER_PORT = 8767
FILE_MAX_BYTES = 8 << 20
HEADER_LINE = b"--- job header ---\n"
HEADER_EQUALS_STATE = ("item", "worktree", "branch", "base_sha", "deadline")

_ROLE = re.compile(r"^[a-z][a-z0-9-]{0,39}\Z")
_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\[\]-]{0,79}\Z")
_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?=\s|\Z)")
_DEADLINE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z\Z")


class Refuse(Exception):
    def __init__(self, code, reason):
        super().__init__(reason)
        self.code, self.reason = code, " ".join(str(reason).split())     # one line, whatever it quotes


def utc_now_text():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_atomic(path, data):
    temporary = "%s.tmp.%d" % (path, os.getpid())
    with open(temporary, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def load_json_text(text):
    """strict JSON: a duplicate object key, NaN or Infinity refuses the document (kyboot.py's reader)"""
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate key %r" % key)
            out[key] = value
        return out

    def constant(name):
        raise ValueError("%s is not JSON" % name)

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def read_bytes(path):
    """the whole content of a regular file of at most FILE_MAX_BYTES; ValueError says why not"""
    if not os.path.isfile(path):
        raise ValueError("%s does not exist or is not a file" % path)
    try:
        with open(path, "rb") as handle:
            data = handle.read(FILE_MAX_BYTES + 1)
    except OSError as unreadable:
        raise ValueError("%s cannot be read (%s)" % (path, unreadable.strerror)) from None
    if len(data) > FILE_MAX_BYTES:
        raise ValueError("%s is larger than %d bytes" % (path, FILE_MAX_BYTES))
    return data


def read_json_and_sha(path):
    data = read_bytes(path)
    try:
        return load_json_text(data.decode("utf-8")), hashlib.sha256(data).hexdigest()
    except (ValueError, UnicodeDecodeError, RecursionError) as bad:
        raise ValueError("%s is not acceptable JSON (%s)" % (path, bad)) from None


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def same_json(a, b):
    """two JSON values are the same value of the same type (150 is not 150.0 and true is not 1)"""
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(same_json(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same_json(a[key], b[key]) for key in a)
    return a == b


def is_text(value):
    return isinstance(value, str) and value != "" and "\0" not in value


def normalised(path):
    return os.path.isabs(path) and os.path.normpath(path) == path and not path.startswith("//")


def is_beneath(path, parent):
    return path.startswith(parent.rstrip(os.sep) + os.sep)


def parse_deadline(text):
    """epoch seconds of `YYYY-MM-DDTHH:MM:SSZ`; None for any other form (unknown, which refuses)"""
    match = _DEADLINE.match(text) if isinstance(text, str) else None
    if not match:
        return None
    try:
        return datetime.datetime(*(int(part) for part in match.groups()), tzinfo=datetime.timezone.utc).timestamp()
    except ValueError:
        return None


def parse_version(text):
    lines = text.strip().splitlines() if isinstance(text, str) else []
    match = _VERSION.match(lines[0].strip()) if lines else None
    return tuple(int(part) for part in match.groups()) if match else None


def project_settings_digest(worktree):
    """kyboot.py's: the sha256 of <worktree>/.claude/settings.json · "absent" · None when it cannot be read"""
    path = os.path.join(worktree, ".claude", "settings.json")
    if not os.path.lexists(path):
        return "absent"
    try:
        return sha256_file(path) if os.path.isfile(path) else None
    except OSError:
        return None


def zdotdir_digest(folder):
    """kyboot.py's: sha256 over the name, then the content, of every regular file directly in `folder`, names
    sorted · "absent" · None when it is not a folder or cannot be read"""
    if not os.path.lexists(folder):
        return "absent"
    if not os.path.isdir(folder):
        return None
    digest = hashlib.sha256()
    try:
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            digest.update(name.encode("utf-8"))
            with open(path, "rb") as handle:
                digest.update(handle.read())
    except (OSError, ValueError):
        return None
    return digest.hexdigest()


def portable_argv(argv, worktree):
    """kyboot.py's: a launch line without what legitimately differs between worktrees — the --mcp-config path (its
    content is bound by hash) and the worktree prefix of any path under the worktree"""
    out = []
    for index, element in enumerate(argv):
        if index and argv[index - 1] == "--mcp-config":
            out.append("<MCP_CONFIG>")
        elif isinstance(worktree, str) and worktree and (element == worktree or element.startswith(worktree + "/")):
            out.append("<WORKTREE>" + element[len(worktree):])
        else:
            out.append(element)
    return out


def child_path(own):
    """kyloop.py's child_path: the campaign CLI, the recorded node folder when it is one, then the fixed three"""
    parts = [os.path.join(own["KY_ROOT"], "bin")]
    try:
        with open(os.path.join(own["KY_RUN"], "NODE_BIN")) as handle:
            node = handle.read().splitlines()[0].strip()
        if node.startswith("/") and os.path.isdir(node):
            parts.append(node)
    except (OSError, IndexError, UnicodeDecodeError):
        pass
    return ":".join(parts + ["/opt/homebrew/bin", "/usr/bin", "/bin"])


def build_argv(state):
    """the plan §7 launch line (kyboot.py's build_launch); a pure function of the launch keys"""
    argv = [state["claude_bin"], "-p", "--setting-sources", "project",
            "--permission-mode", state["permission_mode"], "--model", state["model"],
            "--effort", state["effort"], "--max-turns", str(state["max_turns"]),
            *state["extra_lean_flags"],
            "--strict-mcp-config", "--mcp-config", state["mcp_config"]]
    if state["disallowed_tools"]:
        argv += ["--disallowedTools", *state["disallowed_tools"]]
    return argv + ["--output-format", "stream-json", "--verbose", "--add-dir", state["KY_ROOT"]]


# ---- the refusals, in the order the header lists them ---------------------------------------------------------
def own_environment():
    own = {name: os.environ.get(name) or "" for name in OWN_ENV}
    for name in OWN_ENV:
        if not own[name] or "\0" in own[name]:
            raise Refuse(64, "usage: %s is not set in kyjob.sh's own environment" % name)
    for name in OWN_ENV_PATHS:
        if not normalised(own[name]):
            raise Refuse(64, "usage: %s is not a normalised absolute path" % name)
    return own


def no_wrappers(own):
    """$KY_ROOT/bin holds the campaign CLI only (kalayantra_fleet.sh no_wrappers; the LOCAL_ONLY incident of
    2026-10-07). A folder that is not there holds nothing; one that cannot be listed is unknown and refuses."""
    folder = os.path.join(own["KY_ROOT"], "bin")
    if not os.path.lexists(folder):
        return
    try:
        found = sorted(name for name in os.listdir(folder) if name not in CAMPAIGN_CLI)
    except OSError as unreadable:
        raise Refuse(78, "no_wrappers: %s cannot be listed (%s)" % (folder, unreadable.strerror)) from None
    if found:
        raise Refuse(78, "no_wrappers: %s carries tool wrappers (%s); only ky and kybrief belong there"
                     % (folder, ", ".join(repr(name) for name in found[:10])))


def text_list(state, key, reason):
    """a null or list-valued launch key as a list of texts"""
    value = state[key]
    if value is None:
        return []
    if type(value) is not list or not all(is_text(entry) for entry in value):
        raise Refuse(65, "%s: %s is not a list of non-empty texts" % (reason, key))
    return list(value)


def fixture_env(fixture, scratch):
    """the seven PRAVAHA_* values of a fixture run, valid as KV3-B-WRAPPERS reads them; [] for a live run"""
    if fixture is None:
        return []
    if type(fixture) is not dict:
        raise Refuse(65, "state: fixture is neither null nor an object")
    if set(fixture) != set(PRAVAHA_NAMES):
        odd = sorted(set(fixture) ^ set(PRAVAHA_NAMES))
        raise Refuse(65, "state: fixture must carry exactly the seven PRAVAHA_* names (missing or extra: %s)"
                     % ", ".join(repr(name) for name in odd[:10]))
    port = fixture["PRAVAHA_TRACKER_PORT"]
    if isinstance(port, str) and re.match(r"^[1-9][0-9]{3,4}\Z", port):
        port = int(port)
    if isinstance(port, bool) or not isinstance(port, int) or not 1024 <= port <= 65535 or port == LIVE_TRACKER_PORT:
        raise Refuse(65, "state: fixture PRAVAHA_TRACKER_PORT is not a port from 1024 to 65535 other than %d"
                     % LIVE_TRACKER_PORT)
    if fixture["PRAVAHA_URL"] != "http://127.0.0.1:%d" % port:
        raise Refuse(65, "state: fixture PRAVAHA_URL is not exactly http://127.0.0.1:%d" % port)
    inside = os.path.join(os.path.realpath(scratch), "fixture")
    for name in PRAVAHA_PATHS:
        value = fixture[name]
        if not is_text(value) or not normalised(value):
            raise Refuse(65, "state: fixture %s is not a normalised absolute path" % name)
        if not is_beneath(os.path.realpath(value), inside):      # realpath resolves up to the nearest existing ancestor
            raise Refuse(65, "state: fixture %s does not really lie inside %s/" % (name, inside))
    values = dict(fixture, PRAVAHA_TRACKER_PORT=str(port))
    return [(name, values[name]) for name in PRAVAHA_NAMES]


def read_state(job_id, own):
    path = os.path.join(own["KY_RUN"], "jobs", job_id, "state.json")
    try:
        state = read_json_and_sha(path)[0]
    except ValueError as bad:
        raise Refuse(65, "state: %s" % bad) from None
    if type(state) is not dict:
        raise Refuse(65, "state: %s is not one JSON object" % path)
    for key in LAUNCH_KEYS:
        if key not in state:
            raise Refuse(65, "state: launch key %s is absent" % key)
    engine = state.get("engine", "claude")
    if engine not in ("claude", "codex"):
        raise Refuse(65, "engine: null/unknown engine refuses before launch")
    if engine == "claude" and any(k in state for k in ("launch_config_path", "sandbox_mode", "stall_seconds")):
        raise Refuse(65, "engine: Claude job carries Codex-only launch fields")
    for key in REQUIRED_TEXT:
        if engine == "codex" and key in ("claude_bin", "mcp_config"):
            continue
        if not is_text(state[key]):
            raise Refuse(65, "state: %s is not a non-empty text" % key)
    if state["job_id"] != job_id:
        raise Refuse(65, "state: job_id of %s is not %s" % (path, job_id))
    for key in OPTIONAL_TEXT:
        if state[key] is not None and not is_text(state[key]):
            raise Refuse(65, "state: %s is neither null nor a non-empty text" % key)
    for key in PATH_KEYS:
        if state[key] is not None and not normalised(state[key]):
            raise Refuse(65, "state: %s is not a normalised absolute path" % key)
    if not _ROLE.match(state["role"]):
        raise Refuse(65, "state: role is not a role name ([a-z][a-z0-9-]*)")
    if not _MODEL.match(state["model"]):
        raise Refuse(65, "state: model is not a model name")
    scratch = os.path.join(own["KY_SCRATCH"], "jobs", job_id)
    if state["job_scratch"] != scratch:
        raise Refuse(65, "state: job_scratch is not %s" % scratch)
    if os.path.islink(scratch) or not os.path.isdir(scratch):
        raise Refuse(65, "state: job_scratch %s is not an existing directory" % scratch)
    for key in BENEATH_JOB_SCRATCH:
        if not is_beneath(state[key], scratch):
            raise Refuse(65, "state: %s is not beneath the job's scratch folder %s" % (key, scratch))
    if not os.path.isdir(state["tmp_path"]):
        raise Refuse(65, "state: tmp_path %s is not an existing directory" % state["tmp_path"])
    for key in ("stdout_path", "stderr_path"):
        if not os.path.isdir(os.path.dirname(state[key])) or os.path.isdir(state[key]):
            raise Refuse(65, "state: %s %s cannot be written" % (key, state[key]))
    state["tests"] = text_list(state, "tests", "state")
    if any("\n" in entry or "\r" in entry for entry in state["tests"]):
        raise Refuse(65, "state: tests holds a path with a line break (TESTS is one path per line)")
    state["PRAVAHA"] = fixture_env(state["fixture"], own["KY_SCRATCH"])
    state["KY_ROOT"] = own["KY_ROOT"]
    return state


def check_limits(state):
    kind = state["kind"]
    if kind not in TURN_CAPS:
        raise Refuse(65, "limits: kind %r has no turn cap; it is not a kind kyjob.sh launches" % kind[:40])
    turns = state["max_turns"]
    if isinstance(turns, bool) or not isinstance(turns, int) or turns <= 0:
        raise Refuse(65, "limits: max_turns is missing or not a whole number above 0")
    if turns > TURN_CAPS[kind]:
        raise Refuse(65, "limits: max_turns %d exceeds the cap %d for kind %s" % (turns, TURN_CAPS[kind], kind))
    deadline = parse_deadline(state["deadline"])
    if deadline is None:
        raise Refuse(65, "limits: deadline is missing or not UTC text YYYY-MM-DDTHH:MM:SSZ")
    if deadline <= time.time():
        raise Refuse(65, "limits: deadline %s is not in the future" % state["deadline"])
    return deadline


def check_flags(state):
    if not is_text(state["permission_mode"]) or state["permission_mode"].startswith("-"):
        raise Refuse(65, "flags: permission_mode is missing; it is always passed explicitly, never inherited")
    wanted = "xhigh" if state["kind"] in XHIGH_KINDS else "high"
    if state["effort"] != wanted:
        raise Refuse(65, "flags: effort for kind %s must be %s" % (state["kind"], wanted))
    state["extra_lean_flags"] = text_list(state, "extra_lean_flags", "flags")
    for flag in state["extra_lean_flags"]:
        name = flag.split("=", 1)[0]                 # the name only: a value is never echoed
        if name in FLAGS_NEVER:
            raise Refuse(65, "flags: %s is forbidden in extra_lean_flags (%s)" % (name, FLAGS_NEVER[name]))
        if name in FLAGS_LAUNCHER_OWNED:
            raise Refuse(65, "flags: %s is forbidden in extra_lean_flags (the launch line sets it itself)" % name)
        if name.startswith(FLAG_PREFIXES_NEVER):
            raise Refuse(65, "flags: %s is forbidden in extra_lean_flags (no permission bypass by flag)" % name)
    state["disallowed_tools"] = text_list(state, "disallowed_tools", "flags")
    if any(tool.startswith("-") for tool in state["disallowed_tools"]):
        raise Refuse(65, "flags: disallowed_tools holds a flag, not a tool name")


def check_boundary_form(state):
    boundary = state["boundary"]
    if boundary is not None and not is_text(boundary):
        raise Refuse(65, "boundary: `boundary` is neither null nor a boundary name; unknown refuses")
    if boundary is None and state["kind"] in BOUNDED_KINDS:
        raise Refuse(65, "boundary: kind %s runs only inside the verifier boundary, and the job state names none"
                     % state["kind"])
    return boundary is not None


def check_program(state):
    binary = state["claude_bin"]
    if "=" in binary:
        raise Refuse(65, "program: claude_bin holds '=' (env would read it as an assignment)")
    if not os.path.isfile(binary):
        raise Refuse(65, "program: claude_bin does not exist or is not a file: %s" % binary)
    if not os.access(binary, os.X_OK):
        raise Refuse(65, "program: claude_bin is not executable: %s" % binary)
    try:
        return sha256_file(os.path.realpath(binary))
    except OSError as unreadable:
        raise Refuse(65, "program: claude_bin cannot be read (%s)" % unreadable.strerror) from None


def check_mcp(state, own):
    """the installed configuration whose hash is in the installation receipt: exactly one components[] entry"""
    receipt_path = os.path.join(own["KY_RUN"], "INSTALL_RECEIPT.json")
    try:
        receipt = read_json_and_sha(receipt_path)[0]
        actual = hashlib.sha256(read_bytes(state["mcp_config"])).hexdigest()
    except ValueError as bad:
        raise Refuse(65, "mcp: %s" % bad) from None
    components = receipt.get("components") if type(receipt) is dict else None
    if type(components) is not list:
        raise Refuse(65, "mcp: %s carries no components[]" % receipt_path)
    entries = [entry for entry in components
               if type(entry) is dict and entry.get("installed_path") == state["mcp_config"]]
    if len(entries) != 1:
        raise Refuse(65, "mcp: %d components[] entries of %s have installed_path %s; exactly one must"
                     % (len(entries), receipt_path, state["mcp_config"]))
    if entries[0].get("sha256") != actual:
        raise Refuse(65, "mcp: %s is not the installed configuration (its sha256 is not the installation "
                         "receipt's)" % state["mcp_config"])
    return actual


def check_prompt(state):
    """the prompt is the card's bytes, then the packet's, then the header line and one JSON object naming this job"""
    try:
        card, packet, prompt = (read_bytes(state[key]) for key in ("card_path", "packet_path", "prompt_path"))
    except ValueError as bad:
        raise Refuse(65, "prompt: %s" % bad) from None
    for key, data in (("card_path", card), ("packet_path", packet)):
        if not data:
            raise Refuse(65, "prompt: %s is empty; an empty file cannot be shown to be in the prompt" % key)
    if not prompt.startswith(card):
        raise Refuse(65, "prompt: it does not begin with the exact bytes of card_path")
    rest = prompt[len(card):].lstrip(b"\n")
    if not rest.startswith(packet):
        raise Refuse(65, "prompt: the exact bytes of packet_path do not follow the card")
    rest = rest[len(packet):].lstrip(b"\n")
    if not rest.startswith(HEADER_LINE):
        raise Refuse(65, "prompt: the line `--- job header ---` does not follow the packet")
    try:
        header = load_json_text(rest[len(HEADER_LINE):].decode("utf-8"))
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise Refuse(65, "prompt: what follows `--- job header ---` is not one JSON object") from None
    if type(header) is not dict:
        raise Refuse(65, "prompt: what follows `--- job header ---` is not one JSON object")
    if header.get("job_id") != state["job_id"]:
        raise Refuse(65, "prompt: the job header does not name job %s" % state["job_id"])
    for key in HEADER_EQUALS_STATE:
        if key in header and not same_json(header[key], state[key]):
            raise Refuse(65, "prompt: the job header's %s is not the job state's" % key)


def check_qualification(state, own, env, argv, facts, deadline):
    """plan §7 KV-06 (kyboot.py's receipt check): only a PASS receipt earned under launchd that binds exactly this
    launch qualifies it. Returns (the receipt's binds, the receipt's sha256). Nothing is executed here."""
    # Chart variants must be selected here as well as at admission (same role, distinct receipt).
    variant = "-chart" if os.path.basename(state["mcp_config"]) == "mcp.marsys-only.json" else ""
    if state["role"] in ("build", "rework", "verify") and state["tests"]:
        variant += "-tests"
    path = os.path.join(own["KY_RUN"], "QUALIFICATIONS", "%s%s-%s.json"
                        % (state["role"], variant, state["model"]))
    if not os.path.isfile(path):
        raise Refuse(65, "qualification: no receipt at %s; role %s with model %s is not a qualified launch "
                         "configuration" % (path, state["role"], state["model"]))
    try:
        receipt, digest = read_json_and_sha(path)
    except ValueError as bad:
        raise Refuse(65, "qualification: %s" % bad) from None
    if type(receipt) is not dict or receipt.get("schema") != QUALIFICATION_SCHEMA:
        raise Refuse(65, "qualification: %s is not a %s receipt" % (path, QUALIFICATION_SCHEMA))
    if receipt.get("result") != "PASS":
        raise Refuse(65, "qualification: the receipt's result is not exactly \"PASS\" (FAIL, unknown and missing refuse)")
    if receipt.get("context") != QUALIFIED_CONTEXT:
        raise Refuse(65, "qualification: the receipt was not earned in the %s context" % QUALIFIED_CONTEXT)
    for key in ("role", "model"):
        if receipt.get(key) != state[key]:
            raise Refuse(65, "qualification: the receipt's %s is not this launch's %s" % (key, state[key]))
    binds = receipt.get("binds")
    if type(binds) is not dict:
        raise Refuse(65, "qualification: the receipt carries no binds")
    wanted = {"claude_bin": state["claude_bin"], "claude_bin_sha256": facts["claude_bin_sha256"],
              "model": state["model"], "effort": state["effort"], "permission_mode": state["permission_mode"],
              "max_turns": state["max_turns"], "mcp_config_sha256": facts["mcp_config_sha256"],
              "env_names": sorted(name for name, _ in env), "child_path": dict(env)["PATH"],
              "project_settings_sha256": project_settings_digest(state["worktree"]),
              "zdotdir_sha256": zdotdir_digest(os.path.join(own["KY_ROOT"], "zdotdir")),
              "harness_sha256": facts["harness_sha256"]}
    for name in BOUND_FACTS:
        if name not in binds:
            raise Refuse(65, "qualification: binds.%s is missing" % name)
        if wanted[name] is None:
            raise Refuse(65, "qualification: binds.%s cannot be compared (this launch's value cannot be observed)"
                         % name)
        if not same_json(binds[name], wanted[name]):
            raise Refuse(65, "qualification: binds.%s does not bind this launch" % name)
    seconds = binds.get("deadline_seconds")
    if "deadline_seconds" not in binds:
        raise Refuse(65, "qualification: binds.deadline_seconds is missing")
    if isinstance(seconds, bool) or not isinstance(seconds, int) or seconds <= 0:
        raise Refuse(65, "qualification: binds.deadline_seconds is not a positive whole number of seconds")
    if deadline > time.time() + seconds:
        raise Refuse(65, "qualification: deadline %s is later than now + the qualified deadline_seconds (%d); a job "
                         "never runs longer than its configuration was qualified for" % (state["deadline"], seconds))
    theirs = binds.get("argv")
    if "argv" not in binds:
        raise Refuse(65, "qualification: binds.argv is missing")
    if type(theirs) is not list or not all(isinstance(element, str) for element in theirs):
        raise Refuse(65, "qualification: binds.argv is not a list of texts")
    mine, theirs = portable_argv(argv, state["worktree"]), portable_argv(theirs, binds.get("worktree"))
    if mine != theirs:
        where = next((i for i, pair in enumerate(zip(mine, theirs)) if pair[0] != pair[1]), min(len(mine), len(theirs)))
        raise Refuse(65, "qualification: binds.argv is not this launch's line (same flags, same order); they differ "
                         "at element %d" % where)
    return binds, digest


def check_version(state, env, binds):
    """`<claude_bin> --version` — reached only for a program the PASS receipt binds by path and sha256"""
    try:
        done = subprocess.run([state["claude_bin"], "--version"], capture_output=True, text=True, timeout=60,
                              env={name: value for name, value in env if name != "TMPDIR"},
                              stdin=subprocess.DEVNULL, cwd="/")
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as failed:
        raise Refuse(65, "program: version could not be asked (%s)" % type(failed).__name__) from None
    if done.returncode != 0:
        raise Refuse(65, "program: version could not be asked (--version exited %d)" % done.returncode)
    found = parse_version(done.stdout)
    if found is None:
        raise Refuse(65, "program: version output is not X.Y.Z")
    if found < MIN_VERSION:
        raise Refuse(65, "program: version %s is below the minimum %s"
                     % (".".join(map(str, found)), ".".join(map(str, MIN_VERSION))))
    if "claude_version" not in binds:
        raise Refuse(65, "qualification: binds.claude_version is missing")
    if parse_version(binds["claude_version"]) != found:
        raise Refuse(65, "qualification: binds.claude_version does not bind this launch (%s)"
                     % ".".join(map(str, found)))


def prepare_boundary(job_id, own):
    """`kyboundary.sh prepare <job_id>`: 0 is ready; anything else refuses (a partial boundary is never ready)"""
    script = os.path.join(own["KY_FLEET"], "kyboundary.sh")
    if not os.path.isfile(script):
        raise Refuse(65, "boundary: %s is not there; a verifier job never runs without its boundary" % script)
    try:
        done = subprocess.run(["/bin/bash", script, "prepare", job_id], stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as failed:
        raise Refuse(65, "boundary: prepare could not be run (%s)" % failed.strerror) from None
    if done.returncode != 0:
        raise Refuse(65, "boundary: `kyboundary.sh prepare %s` exited %d; the boundary is not established"
                     % (job_id, done.returncode))
    return ["/bin/bash", script, "exec", job_id, "--"]


def job_environment(state, own):
    """the job's whole environment, in the order of the quoted line; a null key omits its name"""
    root = own["KY_ROOT"]
    env = [("HOME", own["HOME"]), ("PATH", child_path(own)), ("LANG", "en_US.UTF-8"), ("TERM", "dumb"),
           ("USER", own["USER"]), ("TMPDIR", state["tmp_path"]), ("ZDOTDIR", os.path.join(root, "zdotdir")),
           ("KY_ROOT", root), ("KY_RUN", own["KY_RUN"]), ("KY_FLEET", own["KY_FLEET"]),
           ("KY_STREAM", state["stream"]), ("KY_LANE", state["slot"]), ("KY_ITEM", state["item"]),
           ("KY_PY", os.path.join(root, "venv", "bin", "python")), ("SE_EPHE_PATH", state["se_ephe_path"]),
           ("SWE_EPHE_PATH", state["swe_ephe_path"]), ("TESTS", "\n".join(state["tests"]) or None),
           ("KY_SCRATCH", own["KY_SCRATCH"]), ("JOB_SCRATCH", state["job_scratch"]), ("KY_RUN_ID", state["job_id"]),
           ("KY_ROLE", state["role"]), ("KY_CONTROLLER_ID", state["controller_id"])]
    return [(name, value) for name, value in env + state["PRAVAHA"] if value is not None]


def plan(job_id, own):
    no_wrappers(own)
    state = read_state(job_id, own)
    if not os.path.isdir(state["worktree"]) or not os.access(state["worktree"], os.X_OK):
        raise Refuse(70, "cd %s failed" % state["worktree"])
    if state.get("engine", "claude") == "codex":
        global CODEX_JOB
        CODEX_JOB = state
        if len(ARGV) > 2 and ARGV[2]:
            raise Refuse(78, "credential variable name set in kyjob.sh's own environment:" + ARGV[2])
        sys.path.insert(0, own["KY_FLEET"])
        try:
            import kyjob_engines
            kyjob_engines.plan(state, own, globals())
        except (kyjob_engines.Refusal, OSError, ValueError) as error:
            raise Refuse(65, "codex: %s" % error) from None
        return
    deadline = check_limits(state)
    check_flags(state)
    bounded = check_boundary_form(state)
    facts = {"claude_bin_sha256": check_program(state), "mcp_config_sha256": check_mcp(state, own)}
    check_prompt(state)
    try:
        facts["harness_sha256"] = sha256_file(os.path.join(own["KY_FLEET"], "kyqualify.py"))
    except OSError:
        facts["harness_sha256"] = None                 # unobservable: the bind then refuses
    env, argv = job_environment(state, own), build_argv(state)
    binds, receipt_sha256 = check_qualification(state, own, env, argv, facts, deadline)
    check_version(state, env, binds)
    prefix = prepare_boundary(job_id, own) if bounded else []

    scratch = state["job_scratch"]
    line = prefix + ["/usr/bin/env", "-i"] + ["%s=%s" % pair for pair in env] + argv
    parts = ["ky.jobplan/1", state["worktree"], state["prompt_path"], state["stdout_path"], state["stderr_path"]] + line
    record = {"job_id": job_id, "cwd": state["worktree"], "argv": argv, "env_names": sorted(name for name, _ in env),
              "qualification_sha256": receipt_sha256, "at": utc_now_text()}
    write_atomic(os.path.join(scratch, "kyjob.plan"), b"".join(part.encode("utf-8") + b"\0" for part in parts))
    write_atomic(os.path.join(scratch, "kyjob.launch.json"),
                 (json.dumps(record, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8"))


def report(job_id, refusal):
    """the one stderr line, and the refusal record when the job's own scratch folder is there to hold it"""
    scratch_root = os.environ.get("KY_SCRATCH") or ""
    scratch = os.path.join(scratch_root, "jobs", job_id)
    if normalised(scratch_root) and os.path.isdir(scratch) and not os.path.islink(scratch):
        for leftover in ("kyjob.plan", "kyjob.launch.json"):      # a refused job has no launch record
            try:
                os.unlink(os.path.join(scratch, leftover))
            except OSError:
                pass
        record = {"job_id": job_id, "code": refusal.code, "reason": refusal.reason, "at": utc_now_text()}
        codex = globals().get("CODEX_JOB")
        if codex and codex.get("sandbox_mode", "locked") in ("locked", "full"):
            mode = codex.get("sandbox_mode", "locked")
            record.update(engine="codex", sandbox_mode=mode,
                          sandbox="full (owner direction 2026-10-12)" if mode == "full" else "locked")
        try:
            write_atomic(os.path.join(scratch, "kyjob.refusal.json"),
                         (json.dumps(record, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8"))
        except OSError:
            pass                                                  # the stderr line and the exit code still say it
    sys.stderr.write("kyjob.sh: REFUSED %d: %s\n" % (refusal.code, refusal.reason))
    return refusal.code


def main(argv):
    mode, job_id = argv[0], argv[1]
    try:
        if mode == "refuse":
            raise Refuse(int(argv[2]), argv[3])
        plan(job_id, own_environment())
    except Refuse as refusal:
        return report(job_id, refusal)
    except Exception as unforeseen:                               # unknown refuses; a value is never echoed
        return report(job_id, Refuse(65, "state: kyjob.sh's own check failed (%s); nothing was launched"
                                     % type(unforeseen).__name__))
    return 0


sys.exit(main(ARGV))
#<<< kyjob helper
KYJOB_HELPER_TEXT
