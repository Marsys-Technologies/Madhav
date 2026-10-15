#!/bin/bash
# install.sh — B-2: install the independently reviewed KĀLA-YANTRA v3 bootstrap bundle (plan v2.7 §14 B-2, D-9; rulings
# P6, P9, P29, P39, P40). version 1.2, status DRAFT — pending the independent review of KV3-B-INSTALL.
# changelog: 1.0 (2026-10-12) first version.
#            1.1 (2026-10-12) review round 1. B-01: nothing ends as exit 1 once writing has begun — a refusal inside a
#                step is a failure of that step (exit 3, rollback, the action FAILED). B-02: --action must be INTENDED.
#                Sweep: a git lookup that fails is not "absent"; the campaign branch must track origin/main; a claim in an
#                unknown state or of a worker that is not a legacy lane is unresolved, never released; a release counts
#                only when the event log shows it; unreadable event lines adopt no PR; a foreign legacy-<n> state file is
#                not an adoption; staged actions are published as the steward only; the health answer must be this root's
#                tracker in the shape server.py emits; an action that cannot be completed leaves no receipt; KY_SCRATCH is
#                never defaulted; the account's own LaunchAgents and any value inside the real root are E_REAL;
#                kyversion.sh's exit code is its whole interface; kyloop.py runs under python -I.
#            1.2 (2026-10-12) review round 2. R2-B-01: exit 3 leaves NO receipt — an earlier run's receipt is moved aside
#                (`.superseded`) by every failure after writing began and is never put back, whichever step failed and
#                whether or not a byte changed; the stderr sentence "there is no receipt" is written only when the path
#                was looked at and is empty. Sweep: "the tracker was restarted" is said only of a restart this run
#                confirmed; "trees restored" only when every undo ran (a kept `.old` tree that is gone is a restore
#                problem, not a silent success); a claim record that reads released/expired counts as ended only when
#                the event log shows that claim ended; an active claim in the event log that no record shows is
#                unresolved; a PR is adopted only on its item's LATEST review event (as completion.py reads it).
#            2026-10-13 installation defect 5: directory children reuse ky_env's live defaults or full fixture set;
#                preflight never passes a lone PRAVAHA_URL to the installed wrapper.
#
#   bash install.sh --manifest M --source S [--root ROOT] [--action ID]        all paths absolute
#
#   M      a `ky.versions_bootstrap/1` manifest (kymanifest.py build).
#   S      a clean checkout at M's `components_commit`.
#   ROOT   default $KY_ROOT, else /Users/Dev/kalayantra (the real installation root).
#   ID     an INTENDED kyaction record of kind `install` whose inputs bind M's file sha256 (`manifest_sha256`) and S's
#          commit (`source_commit`) (I). ROOT = the real root REQUIRES it; any root accepts it. install.sh completes the
#          record when the receipt exists and kyversion.sh accepts it, and fails it when the installation fails after
#          writing began. A refusal (exit 1) leaves it INTENDED. A record in any other state (DONE, FAILED, unknown) is
#          refused with E_ACTION_STATE: a FAILED record must be retried by its owner first, and a later run after a DONE
#          one needs a fresh INTENDED record — a finished id opens nothing.
#
# Exit 0 installed, receipt written and accepted · 1 refused, NOTHING written (a STOP file is never written in a refusal) ·
#      3 failed after writing began (trees restored while the tracker has not yet been restarted; no receipt) · 64 usage.
#      Exit 1 is decided before the first write only (verification, or the installation lock). From the STOP files on,
#      whatever stops a step — a refusal included — is exit 3 `FAILED step <n>`. The STOP files and a campaign checkout
#      created at step 5 are never removed by a failure (the second is named on stderr); an installation whose action
#      record cannot be completed has its receipt renamed `.refused`.
#      Exit 3 never leaves a file at R/INSTALL_RECEIPT.json: a receipt an EARLIER run wrote is renamed
#      `INSTALL_RECEIPT.json.superseded` (kept for the operator, granting nothing) and is not put back by a rollback —
#      every receipt key is "measured in this run", and this run failed. Only a later run that exits 0 writes a receipt.
# stdout on exit 0: one JSON object {installed, receipt, receipt_sha256, changed, model_actions[{id, status}]}.
# stderr: `install.sh: REFUSED <code>: …` (exit 1) or `install.sh: FAILED step <n>: …` (exit 3).
#
# (I) = interpretation of the packet, decided here:
#  * Decided FIRST, before M, S or any path under ROOT is read or written (ruling P39), each with its stderr code:
#      E_ACTION            ROOT is the real root and --action is missing;
#      E_UNSET <VAR>       ROOT is not the real root and VAR is not given — VAR in KY_LAUNCHAGENTS_DIR, KY_LAUNCHCTL,
#                          KY_CAMPAIGN_CHECKOUT, PRAVAHA_URL (ruling P29: fail closed); or, for any root, KY_SCRATCH is not
#                          given (it is recorded in the loop plists and the receipt, so it is never defaulted);
#      E_REAL <VAR>        … or VAR equals its real default (a symlink to the real launchctl, a spelling of the real tracker
#                          URL, the real campaign checkout, Library/LaunchAgents under $HOME or under the account's home in
#                          the password database) or lies inside the real root — or ROOT does (code E_REAL ROOT);
#      E_VALUE <VAR>       … or VAR is not an absolute path / a loopback http URL on a port; for the real root also HOME
#                          when it is not the account's home in the password database;
#      E_HOOK <VAR>        ROOT is the real root and a test hook is set (KY_PS, KY_GH, KY_GIT, KY_CURL, KY_PREFLIGHT_TIMEOUT,
#                          KY_INSTALL_WAIT_S, KY_LOOP_SLEEP_SCALE, KY_LOOP_TEST_CONTEXT, KY_TEST_ASSUME_ROOT) or one of the
#                          four variables differs from its real default. For a scratch ROOT the hooks KY_PS (ps), KY_GH (gh),
#                          KY_GIT (git) and KY_INSTALL_WAIT_S (seconds to wait for the tracker's health) are honoured.
#  * Provenance (b) is judged by this program's own code and never by M's `review` field. It runs before the reviewed
#    `kymanifest.py check` (a), so that program's bytes are verified before it is executed.
#  * Only M's bound components and the five entrypoints are installed (ruling P40). Destinations: fleet/bin/{ky,kybrief}
#    → ROOT/bin; every other fleet component → F/<path below fleet/>; the five entrypoints → F/bundle/<repository path>;
#    platform/scripts/governance/pravaha_tracker/** (tests/ excluded) → ROOT/tracker_live/pravaha_tracker/**. A tracked file
#    in fleet/bin or in the tracker package that M does not bind, and a bound component with no destination, refuse.
#    The entrypoints are recorded under receipt `trees.bundle`, not in `components[]`: kyversion.sh requires every
#    `components[]` entry to be a manifest component.
#  * Every child program gets a WHITELISTED environment (fixed PATH, HOME, USER, LANG, TMPDIR and the KY_* it needs); no
#    credential, PYTHON*, GIT_* or proxy variable is passed on. The campaign checkout's policy root is the directory that
#    holds it; registrations directly under it are counted (≤ 14 before the checkout is added).
#  * A STOP file counts only as a regular file, as kalayantra_fleet.sh's `[ -f … ]` reads it; anything else at that path
#    refuses before the first write.
#  * The process evidence (e) has two stated limits, recorded in receipt `old_supervisors.processes.limits`: this
#    program's own ancestor processes are not examined, and `codex exec` is matched on its command line only.
#  * The health answer counts only in the shape pravaha_tracker/server.py emits and only from THIS root's tracker:
#    `event_log.path` is R/EVENTS.jsonl and `server_started_at` is not before the start of the launchd job's process.
#  * kyversion.sh and preflight.sh: exit 0 = pass (the packet's interface); nothing is read from their output.
#  * The receipt is a record of the FINAL observed state (no per-run wording), so a rerun that changes nothing rewrites
#    nothing; `installed_at` is kept when the rest of the receipt is byte-identical. What a run DID (swapped, published,
#    skipped) is reported on stdout. Event identity in `model_actions` is the matching event's line number and sha256.
#  * The tracker is restarted when this run changed what it loads (F, the tracker tree or its plist) or the running process
#    is not provably newer than every installed file it loads (process start from `ps`, compared with file mtimes); the
#    restart waits for the next whole second first, so "started after the swap" is strict at ps's one-second resolution.
#  * A staged action's event "already exists" when an event with the same kind, subject, state, actor and detail is in
#    R/EVENTS.jsonl; a publish that exits 0 without that event appearing is a failure.
#  * Legacy: a claim file of one of the 13 legacy lanes whose state is acquired/renewed is released with
#    `KY_LANE=<lane> ky release` after the process check (e) and counts as released only when the file then says `released`
#    AND the event log (the tracker's authority, claims.py) holds that claim's `released` event; a claim of any other
#    worker (a v3 job) is never released, and a state claims.py does not write is not "ended". A record that reads
#    released/expired is "already ended" only when the latest event of that claim in the log is released/expired too.
#    claims.py keeps ONE record per worker, so the log is also read for claims no record shows: an item whose latest
#    claim event is active and is not a listed record's claim goes to legacy.unresolved[] (kind `claim_event`).
#    An open `kalayantra/*` PR
#    is adopted (one R/legacy/legacy-<n>/state.json, never overwritten) only when the tracker's latest `PR #<n> @ <head>`
#    review registration names the PR's current head and is its item's latest review event, every line of the
#    event log could be read, and a state file already
#    at that path is this PR's own adoption record; everything else is listed in legacy.unresolved[]. A PR listing that
#    cannot be obtained fails the installation. The `legacy-<n>` record lives outside the dispatcher's jobs directory;
#    schema is `ky.legacy_job_state/1` and every unknown field is null.
#  * After a failure BEFORE the tracker restart the trees (F, tracker_live, bin, VERSIONS.bootstrap.json) are restored — the
#    receipt is not; once the tracker restart has begun nothing is undone (the loaded revision would no longer match the
#    files) and a rerun resumes (published actions are skipped). stderr says which of the two happened, whether the restart
#    was confirmed, and — after looking — whether a receipt is at the active path.
set -u

PY=/opt/homebrew/bin/python3
if [ ! -x "$PY" ]; then PY="$(command -v python3 || true)"; fi
if [ -z "$PY" ]; then echo "install.sh: no python3 to run the installation with" >&2; exit 1; fi
HERE="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
if [ -z "$HERE" ]; then echo "install.sh: the script's own directory cannot be resolved" >&2; exit 1; fi
SELF="$HERE/$(basename "$0")"

# The program is the stdlib text below the final `exit`, read from this file by the interpreter itself (as kyversion.sh does).
"$PY" -I -B -c 'import sys
quote = chr(39)
with open(sys.argv[1], encoding="utf-8") as f:
    text = f.read()
program = text.split("\n: <<" + quote + "KYINSTALL_PY" + quote + "\n", 1)[1].rsplit("\nKYINSTALL_PY\n", 1)[0]
sys.argv = sys.argv[1:]
__file__ = sys.argv[0]
exec(compile(program, sys.argv[0], "exec"))' "$SELF" "$@" </dev/null
exit $?
: <<'KYINSTALL_PY'
import calendar
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import plistlib
import pwd
import re
import shutil
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REAL_ROOT = "/Users/Dev/kalayantra"
REAL_CAMPAIGN = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"
REAL_LAUNCHCTL = "/bin/launchctl"
REAL_PORT = 8767
REAL_PS = "/bin/ps"
REAL_GIT = "/usr/bin/git"
DEFAULT_CLAUDE = "/Users/Dev/.local/bin/claude"
MIN_CLAUDE = (2, 1, 296)
CAMPAIGN_BRANCH = "kalayantra/campaign"
CAPACITY = 14
K = "00_ARCHITECTURE/briefs/kalayantra"
FL = K + "/fleet"
FL_BIN = FL + "/bin/"
TRACKER_PKG = "platform/scripts/governance/pravaha_tracker"
STAGED = "00_ARCHITECTURE/control/kalayantra/STAGED_MODEL_ACTIONS_v2_2.json"
PLAN_MODEL = "00_ARCHITECTURE/control/kalayantra/plan_model.json"
COMPONENT_LIST = FL + "/BOOTSTRAP_COMPONENTS.txt"
ROLES = ("plan", "cockpit_prompt", "owner_decisions", "strategy", "surrogate_agent")
LANES = ["sutradhara", "adhikarin", "v1", "v2", "v3"] + ["k%d" % i for i in range(1, 9)]
LOOPS = ("dispatcher", "planner", "conductor", "veto")
WRAPPERS = ("ky", "kybrief")
REQUIRED_FLEET = ("kymanifest.py", "kyaction.py", "kyctl.sh", "kyloop.py", "kyqualify.py", "preflight.sh", "kyversion.sh",
                  "mcp.none.json")
TRACKER_LABEL = "com.madhav.kalayantra.tracker"
TRACKER_PY = "/opt/homebrew/bin/python3"
RECEIPT_SCHEMA = "ky.install_receipt/1"
# Read the controller's definition beside this installer, without relying on ambient PYTHONPATH.
_path_spec = importlib.util.spec_from_file_location("ky_install_loop_path", os.path.join(os.path.dirname(__file__), "kyloop.py"))
_path_module = importlib.util.module_from_spec(_path_spec)
_path_spec.loader.exec_module(_path_module)
BASE_PATH = _path_module.SYSTEM_PATH
HEX40 = re.compile(r"^[0-9a-f]{40}\Z")
HEX64 = re.compile(r"^[0-9a-f]{64}\Z")
ACTION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}\Z")
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\Z")
CHECKPOINT = re.compile(r"^(sutradhara|adhikarin|v[1-3]|k[1-8])\.cycle([0-9]+)\.state\.json\Z")
PR_REGISTRATION = re.compile(r"PR #([0-9]+)\s*@\s*([0-9a-f]{7,40})")
HOOK_ONLY = ("KY_PS", "KY_GH", "KY_GIT", "KY_CURL", "KY_PREFLIGHT_TIMEOUT", "KY_INSTALL_WAIT_S", "KY_LOOP_SLEEP_SCALE",
             "KY_LOOP_TEST_CONTEXT", "KY_TEST_ASSUME_ROOT")
CLAIM_ACTIVE = ("acquired", "renewed")            # pravaha_tracker/claims.py: the four states a claim event can carry
CLAIM_ENDED = ("released", "expired")
PROCESS_LIMITS = ["the installer's own ancestor processes are not examined",
                  "codex exec is matched on its command line only; its working directory is not observed"]
HOOK_NAMES = set(HOOK_ONLY) | {"KY_LAUNCHCTL", "KY_LAUNCHAGENTS_DIR"}
USAGE = ("usage: install.sh --manifest <abs path> --source <abs path> [--root <abs path>] [--action <id>]\n"
         "       exit 0 installed · 1 refused, nothing written · 3 failed after writing began · 64 usage")


class Usage(Exception):
    pass


class Refused(Exception):
    """Verification said no, or a decision made first did: exit 1, nothing written."""

    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code


class Failed(Exception):
    """Something went wrong after writing began: exit 3, no receipt."""

    def __init__(self, step, message):
        Exception.__init__(self, message)
        self.step = step


def refuse(message, code="V"):
    raise Refused(code, message)


# ------------------------------------------------------------------------------------------------ small helpers
def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def flat(text, limit=400):
    text = " ".join(str(text).split())
    return "".join(ch if ch.isprintable() else "?" for ch in text)[:limit]


def read_json_object(path, what):
    try:
        with open(path, "rb") as f:
            doc = json.loads(f.read())
    except (OSError, ValueError, RecursionError) as e:
        refuse("%s unreadable: %s (%s)" % (what, path, type(e).__name__))
    if not isinstance(doc, dict):
        refuse("%s is not a JSON object: %s" % (what, path))
    return doc


def norm(path):
    return os.path.normpath(path)


def real(path):
    return os.path.realpath(path)


def is_under(path, parent):
    path, parent = norm(path), norm(parent)
    return path == parent or path.startswith(parent.rstrip("/") + "/")


def write_atomic(path, data, mode=0o644):
    tmp = "%s.tmp.%d" % (path, os.getpid())
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.lexists(tmp):
            os.unlink(tmp)
    fsync_dir(os.path.dirname(path))


def fsync_dir(path):
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


class Out:
    """The result of a child program; rc None = it could not be run at all."""

    def __init__(self, rc, out, err):
        self.rc, self.out, self.err = rc, out, err

    def last_error(self):
        lines = (self.err or "").strip().splitlines() or (self.out or "").strip().splitlines()
        return flat(lines[-1]) if lines else "no output"


def run(argv, env, cwd="/", timeout=120):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=cwd,
                           timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return Out(None, "", "timed out after %ss" % timeout)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        return Out(None, "", "%s: %s" % (type(e).__name__, e))
    return Out(p.returncode, p.stdout, p.stderr)


# ------------------------------------------------------------------------------------------------ arguments and the first decisions
class Ctx:
    pass


def parse_args(argv):
    opts = {}
    i = 0
    while i < len(argv):
        name = argv[i]
        if name not in ("--manifest", "--source", "--root", "--action") or name in opts or i + 1 >= len(argv) or argv[i + 1] == "":
            raise Usage()
        opts[name] = argv[i + 1]
        i += 2
    if "--manifest" not in opts or "--source" not in opts:
        raise Usage()
    for name in ("--manifest", "--source", "--root"):
        if name in opts and not os.path.isabs(opts[name]):
            raise Usage()
    if "--action" in opts and not ACTION_ID.match(opts["--action"]):
        raise Usage()
    return opts


def url_port(value):
    """(port, None) for a loopback http URL naming a port, else (None, reason)."""
    try:
        u = urllib.parse.urlsplit(value)
        port = u.port
    except ValueError:
        return None, "not a URL"
    if u.scheme.lower() != "http" or (u.hostname or "").lower() not in ("127.0.0.1", "localhost") or port is None \
            or u.path not in ("", "/") or u.query or u.fragment or u.username or u.password:
        return None, "not a loopback http URL with a port"
    if not 1 <= port <= 65535:
        return None, "port out of range"
    return port, None


def decide_environment(opts, env):
    """The decisions taken before anything is read or written (rulings P29, P39)."""
    ctx = Ctx()
    root = opts.get("--root") or env.get("KY_ROOT") or REAL_ROOT
    if not os.path.isabs(root):
        raise Usage()
    ctx.root = norm(root)
    ctx.action = opts.get("--action")
    ctx.manifest_path = opts["--manifest"]
    ctx.source = norm(opts["--source"])
    ctx.is_real = norm(ctx.root) == REAL_ROOT or real(ctx.root) == real(REAL_ROOT)
    if not ctx.is_real and (is_under(ctx.root, REAL_ROOT) or is_under(real(ctx.root), real(REAL_ROOT))):
        refuse("ROOT %s lies inside the real installation root; nothing may be installed there" % ctx.root, "E_REAL ROOT")
    home = env.get("HOME", "")
    ctx.home = home
    try:
        account_home = pwd.getpwuid(os.getuid()).pw_dir
    except KeyError:
        account_home = ""
    agents = [os.path.join(h, "Library", "LaunchAgents") for h in (home, account_home) if h and os.path.isabs(h)]
    if ctx.is_real:
        if not ctx.action:
            refuse("the real installation root needs --action <id> (an INTENDED kyaction record of kind install)", "E_ACTION")
        for name in HOOK_ONLY:
            if name in env:
                refuse("%s is a test hook; it is not honoured for the real root" % name, "E_HOOK " + name)
        if not home or not os.path.isabs(home):
            refuse("HOME is not an absolute path", "E_VALUE HOME")
        if not account_home or real(home) != real(account_home):
            refuse("HOME is not the account's home in the password database; the real LaunchAgents directory is unknown",
                   "E_VALUE HOME")
        defaults = {"KY_LAUNCHAGENTS_DIR": os.path.join(home, "Library", "LaunchAgents"),
                    "KY_LAUNCHCTL": REAL_LAUNCHCTL, "KY_CAMPAIGN_CHECKOUT": REAL_CAMPAIGN,
                    "PRAVAHA_URL": "http://127.0.0.1:%d" % REAL_PORT}
        for name, default in defaults.items():
            if name in env and not same_as_default(name, env[name], [default]):
                refuse("%s differs from its real default; it is not honoured for the real root" % name, "E_HOOK " + name)
        ctx.launchctl, ctx.la_dir, ctx.campaign = REAL_LAUNCHCTL, defaults["KY_LAUNCHAGENTS_DIR"], REAL_CAMPAIGN
        ctx.url, ctx.port = defaults["PRAVAHA_URL"], REAL_PORT
        ctx.ps, ctx.git, ctx.gh, ctx.wait_s = REAL_PS, REAL_GIT, find_gh(), 90
        ctx.pass_through = {}
    else:
        for name in ("KY_LAUNCHAGENTS_DIR", "KY_LAUNCHCTL", "KY_CAMPAIGN_CHECKOUT", "PRAVAHA_URL"):
            value = env.get(name)
            if not value:
                refuse("%s must be given explicitly for a root other than the real one (ruling P29: fail closed)" % name,
                       "E_UNSET " + name)
            if name == "PRAVAHA_URL":
                port, why = url_port(value)
                if port is None:
                    refuse("PRAVAHA_URL: %s" % why, "E_VALUE " + name)
            elif not os.path.isabs(value):
                refuse("%s is not an absolute path" % name, "E_VALUE " + name)
            reals = {"KY_LAUNCHAGENTS_DIR": agents, "KY_LAUNCHCTL": [REAL_LAUNCHCTL], "KY_CAMPAIGN_CHECKOUT": [REAL_CAMPAIGN],
                     "PRAVAHA_URL": ["http://127.0.0.1:%d" % REAL_PORT]}[name]
            if same_as_default(name, value, reals):
                refuse("%s equals its real default; a root other than the real one may not reach it" % name, "E_REAL " + name)
            if name != "PRAVAHA_URL" and inside_real_root(value):
                refuse("%s lies inside the real installation root" % name, "E_REAL " + name)
        ctx.launchctl, ctx.la_dir, ctx.campaign = env["KY_LAUNCHCTL"], norm(env["KY_LAUNCHAGENTS_DIR"]), norm(env["KY_CAMPAIGN_CHECKOUT"])
        ctx.url = env["PRAVAHA_URL"].rstrip("/")
        ctx.port = url_port(ctx.url)[0]
        ctx.ps, ctx.git = env.get("KY_PS", REAL_PS), env.get("KY_GIT", REAL_GIT)
        ctx.gh = env.get("KY_GH") or find_gh()
        try:
            ctx.wait_s = max(1, int(env.get("KY_INSTALL_WAIT_S", "90")))
        except ValueError:
            refuse("KY_INSTALL_WAIT_S is not a whole number of seconds", "E_VALUE KY_INSTALL_WAIT_S")
        ctx.pass_through = {n: env[n] for n in ("KY_CURL", "KY_PREFLIGHT_TIMEOUT", "SE_EPHE_PATH") if n in env}
    if not env.get("KY_SCRATCH"):
        refuse("KY_SCRATCH must be given: the loop plists and the receipt record it, so it is never defaulted", "E_UNSET KY_SCRATCH")
    ctx.scratch = env["KY_SCRATCH"]
    ctx.claude_bin = env.get("CLAUDE_BIN") or DEFAULT_CLAUDE
    for name, value in (("KY_SCRATCH", ctx.scratch), ("CLAUDE_BIN", ctx.claude_bin)):
        if not os.path.isabs(value):
            refuse("%s is not an absolute path" % name, "E_VALUE " + name)
    if not ctx.is_real and inside_real_root(ctx.scratch):
        refuse("KY_SCRATCH lies inside the real installation root", "E_REAL KY_SCRATCH")
    ctx.scratch = norm(ctx.scratch)
    ctx.user = env.get("USER", "")
    ctx.lang = env.get("LANG", "en_US.UTF-8")
    ctx.tmpdir = env.get("TMPDIR", "")
    ctx.uid = os.getuid()
    ctx.run_dir = os.path.join(ctx.root, "run")
    ctx.fleet_live = os.path.join(ctx.root, "fleet_live")
    ctx.tracker_live = os.path.join(ctx.root, "tracker_live")
    ctx.bin_dir = os.path.join(ctx.root, "bin")
    ctx.receipt_path = os.path.join(ctx.run_dir, "INSTALL_RECEIPT.json")
    ctx.versions_path = os.path.join(ctx.run_dir, "VERSIONS.bootstrap.json")
    ctx.undo = []
    ctx.committed = False
    ctx.restart_confirmed = False
    ctx.superseded = False
    ctx.changed = {}
    ctx.lock_fd = None
    ctx.step = 0
    ctx.campaign_created = False
    return ctx


def same_as_default(name, value, defaults):
    if name == "PRAVAHA_URL":
        port, _ = url_port(value)
        return port == REAL_PORT
    return any(norm(value) == norm(d) or real(value) == real(d) for d in defaults)


def inside_real_root(path):
    return is_under(path, REAL_ROOT) or is_under(real(path), real(REAL_ROOT))


def find_gh():
    for d in BASE_PATH.split(":"):
        p = os.path.join(d, "gh")
        if os.access(p, os.X_OK):
            return p
    return None


def child_env(ctx, **extra):
    env = {"PATH": BASE_PATH, "LANG": ctx.lang or "en_US.UTF-8"}
    if ctx.home:
        env["HOME"] = ctx.home
    if ctx.user:
        env["USER"] = ctx.user
    if ctx.tmpdir:
        env["TMPDIR"] = ctx.tmpdir
    env.update(ctx.pass_through)
    env.update(extra)
    return env


def ky_env(ctx, lane=None):
    """The environment the installed `ky` runs in. The real root: the wrapper's live defaults (no PRAVAHA_* at all).
    Any other root: the full fixture set the wrapper requires, pointing at THIS root, checkout and tracker."""
    env = child_env(ctx)
    if not ctx.is_real:
        env.update({"PRAVAHA_HOME": ctx.root, "PRAVAHA_EVENTS": os.path.join(ctx.run_dir, "EVENTS.jsonl"),
                    "PRAVAHA_PLAN_MODEL": os.path.join(ctx.campaign, PLAN_MODEL), "PRAVAHA_REPO": ctx.campaign,
                    "PRAVAHA_HOLD": os.path.join(ctx.root, "HOLD"), "PRAVAHA_TRACKER_PORT": str(ctx.port),
                    "PRAVAHA_URL": ctx.url, "KY_SCRATCH": ctx.scratch})
    if lane:
        env["KY_LANE"] = lane
    return env


def ky_dir_env(ctx, **extra):
    # These children may call `ky`: preserve its live-default/full-fixture rule.
    env = ky_env(ctx)
    env.update(KY_ROOT=ctx.root, KY_RUN=ctx.run_dir, KY_FLEET=ctx.fleet_live, KY_SCRATCH=ctx.scratch,
               KY_SOURCE_REPO=ctx.campaign, CLAUDE_BIN=ctx.claude_bin)
    env.update(extra)
    return env


def git(ctx, repo, *args, text=True, timeout=120):
    env = child_env(ctx, GIT_TERMINAL_PROMPT="0")
    argv = [ctx.git, "--no-optional-locks", "-C", repo] + list(args)
    if text:
        return run(argv, env, timeout=timeout)
    try:
        p = subprocess.run(argv, capture_output=True, env=env, cwd="/", timeout=timeout, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as e:
        return Out(None, b"", str(e))
    return Out(p.returncode, p.stdout, p.stderr.decode("utf-8", "replace"))


def git_ok(ctx, repo, *args):
    r = git(ctx, repo, *args)
    if r.rc != 0:
        refuse("git %s failed in %s: %s" % (args[0], repo, r.last_error()))
    return r.out.strip()


def ref_tip(ctx, repo, ref):
    """The commit a ref names, or None when git answers that there is no such ref (`rev-parse --verify --quiet`: exit 1,
    nothing printed). Any other answer — git could not be run, another exit code, output that is not a commit — refuses:
    a lookup that failed is not an absent ref."""
    r = git(ctx, repo, "rev-parse", "--verify", "--quiet", ref)
    out = (r.out or "").strip()
    if r.rc == 0 and HEX40.match(out):
        return out
    if r.rc == 1 and not out:
        return None
    refuse("whether %s exists cannot be told (git rev-parse exited %s): %s" % (ref, r.rc, r.last_error()))


# ------------------------------------------------------------------------------------------------ verification (nothing is written)
def load_manifest(ctx):
    m = read_json_object(ctx.manifest_path, "manifest")
    ctx.manifest_file_sha = sha_file(ctx.manifest_path)
    body = {k: v for k, v in m.items() if k != "manifest_sha256"}
    if m.get("manifest_sha256") != sha_bytes(canonical(body)):
        refuse("manifest digest does not match its content: %s" % ctx.manifest_path)
    if m.get("mode") != "bootstrap" or m.get("schema") != "ky.versions_bootstrap/1":
        refuse("not a bootstrap manifest (mode %r, schema %r)" % (m.get("mode"), m.get("schema")))
    for k in ("approved_source_commit", "components_commit"):
        if not isinstance(m.get(k), str) or not HEX40.match(m[k]):
            refuse("manifest %s is not a full 40-hex commit" % k)
    comps = m.get("components")
    if not isinstance(comps, list) or not comps:
        refuse("manifest binds no component")
    seen = set()
    for c in comps:
        if not isinstance(c, dict) or not safe_rel(c.get("path")) or not isinstance(c.get("sha256"), str) \
                or not HEX64.match(c["sha256"]) or c["path"] in seen:
            refuse("manifest component entry is malformed or duplicated: %r" % (c,))
        seen.add(c["path"])
    deferred = m.get("deferred_components", [])
    if not isinstance(deferred, list) or any(not isinstance(d, dict) or not safe_rel(d.get("path")) for d in deferred):
        refuse("manifest deferred_components is malformed")
    if {d["path"] for d in deferred} & seen:
        refuse("a deferred component is also bound by the manifest: %s" % sorted({d["path"] for d in deferred} & seen)[0])
    eps = m.get("entrypoints")
    if not isinstance(eps, dict) or sorted(eps) != sorted(ROLES):
        refuse("manifest entrypoints are not exactly the five roles %s" % ", ".join(ROLES))
    for role, e in eps.items():
        if not isinstance(e, dict) or not safe_rel(e.get("path")) or not HEX64.match(str(e.get("sha256"))) \
                or not re.match(r"^[0-9a-f]{40}\Z", str(e.get("git_blob"))):
            refuse("manifest entrypoint %s is malformed" % role)
    rv = m.get("review")
    if not isinstance(rv, dict) or not isinstance(rv.get("path"), str) or os.path.isabs(rv["path"]) \
            or not HEX64.match(str(rv.get("sha256"))) or not isinstance(rv.get("area_reviews"), list):
        refuse("manifest review binding is malformed")
    ctx.m = m
    ctx.components_commit, ctx.approved = m["components_commit"], m["approved_source_commit"]
    ctx.bound = {c["path"]: c["sha256"] for c in comps}
    return m


def safe_rel(p):
    return isinstance(p, str) and p != "" and not p.startswith("/") and ".." not in p.split("/") and "\x00" not in p \
        and "\n" not in p and not p.endswith("/")


def verify_source(ctx):
    s = ctx.source
    if not os.path.isdir(s):
        refuse("S is not a directory: %s" % s)
    top = git_ok(ctx, s, "rev-parse", "--show-toplevel")
    if real(top) != real(s):
        refuse("S is not the top of its git work tree: %s" % s)
    head = git_ok(ctx, s, "rev-parse", "HEAD")
    if head != ctx.components_commit:
        refuse("S is at %s, not at M's components commit %s" % (head, ctx.components_commit))
    dirty = git_ok(ctx, s, "status", "--porcelain", "--untracked-files=all")
    if dirty:
        refuse("S is not clean: %s" % flat(dirty.splitlines()[0]))
    if git(ctx, s, "cat-file", "-e", ctx.approved + "^{commit}").rc != 0:
        refuse("the approved source commit %s is not in S" % ctx.approved)
    ctx.fleet_src = os.path.join(s, FL)


def tree_modes(ctx, commit, paths):
    """{path: git mode string} of the tracked paths below `paths` at `commit`."""
    r = git(ctx, ctx.source, "ls-tree", "-r", "-z", commit, "--", *paths, text=False)
    if r.rc != 0:
        refuse("git ls-tree failed: %s" % flat(r.err))
    out = {}
    for rec in r.out.split(b"\x00"):
        if not rec:
            continue
        meta, _, path = rec.partition(b"\t")
        mode, kind, _oid = meta.decode().split(" ")
        out[path.decode("utf-8")] = (mode, kind)
    return out


def classify(ctx):
    """Destinations (ruling P40) and the unbound-file scan. → ctx.fleet_files, ctx.tracker_files, ctx.bin_files."""
    ctx.fleet_files, ctx.tracker_files, ctx.bin_files = {}, {}, {}
    for p in sorted(ctx.bound):
        if p.startswith(FL_BIN):
            rel = p[len(FL_BIN):]
            if rel not in WRAPPERS:
                refuse("unbound or unexpected wrapper in fleet/bin: %s (only %s are installed into bin)" % (p, ", ".join(WRAPPERS)))
            ctx.bin_files[rel] = p
        elif p.startswith(FL + "/"):
            ctx.fleet_files[p[len(FL) + 1:]] = p
        elif p.startswith(TRACKER_PKG + "/"):
            rel = p[len(TRACKER_PKG) + 1:]
            if rel.startswith("tests/") or "__pycache__" in rel.split("/"):
                continue                        # the package's own tests are bound at most; they are not installed
            ctx.tracker_files[rel] = p
        else:
            refuse("bound component has no installation destination (fleet, fleet/bin or the tracker package): %s" % p)
    tracked = tree_modes(ctx, ctx.components_commit, [FL_BIN.rstrip("/"), TRACKER_PKG])
    for p, (mode, kind) in sorted(tracked.items()):
        if p.startswith(TRACKER_PKG + "/tests/") or "__pycache__" in p.split("/"):
            continue
        if p not in ctx.bound:
            refuse("unbound file to install: %s is tracked in the %s but M does not bind it" %
                   (p, "wrappers" if p.startswith(FL_BIN) else "tracker package"))
    if not any(ctx.tracker_files):
        refuse("M binds no tracker package file under %s" % TRACKER_PKG)
    for w in WRAPPERS:
        if w not in ctx.bin_files:
            refuse("required wrapper not bound by M: %s%s" % (FL_BIN, w))
    for name in REQUIRED_FLEET:
        if name not in ctx.fleet_files:
            refuse("required component not bound by M: %s/%s" % (FL, name))
    modes = tree_modes(ctx, ctx.components_commit, sorted(ctx.bound))
    ctx.modes = {}
    for p in ctx.bound:
        mode, kind = modes.get(p, (None, None))
        if kind != "blob" or mode not in ("100644", "100755"):
            refuse("component is not a regular tracked file at the components commit: %s (%s)" % (p, mode))
        ctx.modes[p] = 0o755 if mode == "100755" else 0o644


def parse_component_list(ctx):
    """(bound paths, deferred paths, bound area names) — the same tranche rules as kymanifest.read_component_list."""
    path = os.path.join(ctx.source, COMPONENT_LIST)
    try:
        with open(path, encoding="utf-8") as f:
            raw_lines = f.read().splitlines()
    except OSError:
        refuse("component list unreadable: %s" % COMPONENT_LIST)
    bound, deferred, areas, target = [], [], [], "bound"
    for raw in raw_lines:
        marker = raw.strip().lower()
        if marker.startswith("# tranche:"):
            word = marker[len("# tranche:"):].split()[:1]
            if word == ["deferred"]:
                target = "deferred"
            elif word == ["bound"]:
                target = "bound"
            else:
                refuse("unknown tranche marker in the component list: %s" % raw.strip())
            continue
        if raw.strip().startswith("# area:"):
            if target == "bound":
                m = re.match(r"^#\s*area:\s*([A-Za-z0-9_.-]+)", raw.strip())
                if not m:
                    refuse("unreadable area line in the component list: %s" % raw.strip())
                areas.append(m.group(1))
            continue
        line = raw.split("#", 1)[0].strip()
        if line:
            (bound if target == "bound" else deferred).append(line)
    return sorted(bound), sorted(deferred), areas


def blob_bytes(ctx, commit, rel):
    r = git(ctx, ctx.source, "cat-file", "blob", "%s:%s" % (commit, rel), text=False)
    if r.rc != 0:
        refuse("%s is not a tracked file at %s" % (rel, commit))
    return r.out


def read_regular(ctx, rel):
    p = os.path.join(ctx.source, rel)
    try:
        st = os.lstat(p)
    except OSError:
        refuse("component missing from S: %s" % rel)
    if not stat.S_ISREG(st.st_mode):
        refuse("component is not a regular file (a link or directory): %s" % rel)
    with open(p, "rb") as f:
        return f.read()


def verify_provenance(ctx):
    """(b): by this program's own code, never by M's `review` field."""
    m = ctx.m
    list_bound, list_deferred, list_areas = parse_component_list(ctx)
    if sorted(ctx.bound) != list_bound:
        diff = sorted(set(ctx.bound) ^ set(list_bound))
        refuse("M's components differ from the bound components of %s: %s" % (COMPONENT_LIST, ", ".join(diff[:5])))
    if sorted(d["path"] for d in m.get("deferred_components", [])) != list_deferred:
        refuse("M's deferred components differ from the deferred components of %s" % COMPONENT_LIST)
    rv = m["review"]
    rpath = os.path.normpath(os.path.join(ctx.source, rv["path"]))
    if not os.path.isfile(rpath):
        refuse("review record missing: %s" % rpath)
    if sha_file(rpath) != rv["sha256"]:
        refuse("review record does not hold the sha256 M binds: %s" % rpath)
    review = read_json_object(rpath, "review record")
    if review.get("verdict") != "ACCEPTED":
        refuse("review record verdict is not ACCEPTED: %r" % review.get("verdict"))
    if review.get("source_commit") != ctx.approved:
        refuse("review record is not bound to M's approved source commit")
    main_session = review.get("reviewer_session_id")
    if not isinstance(main_session, str) or not main_session:
        refuse("review record names no reviewer session")
    entries = review.get("area_reviews")
    if not isinstance(entries, list) or not entries:
        refuse("review record carries no per-area review records")
    sessions, areas, covered, area_rows = {main_session}, [], {}, []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("record"), str) or not os.path.isabs(entry["record"]):
            refuse("malformed per-area review entry")
        p = entry["record"]
        if not os.path.isfile(p) or sha_file(p) != entry.get("record_sha256"):
            refuse("per-area review record missing or changed: %s" % p)
        doc = read_json_object(p, "per-area review record")
        verdict = doc["review"].get("verdict") if isinstance(doc.get("review"), dict) else None
        if verdict != "ACCEPTED":
            refuse("per-area review is not ACCEPTED (%r): %s" % (verdict, doc.get("area")))
        session = doc.get("reviewer_session_id")
        if not isinstance(session, str) or not session:
            refuse("per-area review names no reviewer session: %s" % doc.get("area"))
        if session in sessions:
            refuse("one reviewer session signs twice: %s" % session)
        sessions.add(session)
        area = doc.get("area")
        if not isinstance(area, str) or not area:
            refuse("per-area review names no area: %s" % p)
        areas.append(area)
        inputs = doc.get("inputs") if isinstance(doc.get("inputs"), dict) else {}
        covered.update(inputs)
        area_rows.append({"area": area, "record": p, "record_sha256": entry["record_sha256"], "reviewer_session_id": session,
                          "verdict": "ACCEPTED", "inputs": inputs})
    if sorted(areas) != sorted(list_areas) or len(set(areas)) != len(areas):
        refuse("the reviewed areas %s are not the bound area names %s of %s" % (sorted(areas), sorted(list_areas), COMPONENT_LIST))
    claimed = sorted((a["area"], a["record"], a["record_sha256"], a["reviewer_session_id"]) for a in area_rows)
    given = sorted((a.get("area"), a.get("record"), a.get("record_sha256"), a.get("reviewer_session_id"))
                   for a in rv["area_reviews"] if isinstance(a, dict))
    if claimed != given:
        refuse("M's area_reviews do not match the records the review points at")
    ctx.installed_bytes = {}
    for path, want in sorted(ctx.bound.items()):
        data = read_regular(ctx, path)
        if sha_bytes(data) != want:
            refuse("component %s does not hold the sha256 M binds" % path)
        if data != blob_bytes(ctx, ctx.components_commit, path):
            refuse("component %s differs from its blob at the components commit" % path)
        if covered.get(path) != want:
            refuse("no ACCEPTED per-area review covers the bytes on disk: %s" % path)
        ctx.installed_bytes[path] = want
    ctx.review_info = {"record": {"path": rpath, "relative_path": rv["path"], "sha256": rv["sha256"], "verdict": "ACCEPTED",
                                  "reviewer_session_id": main_session, "source_commit": review["source_commit"]},
                       "areas": [{"area": a["area"], "record": a["record"], "record_sha256": a["record_sha256"],
                                  "reviewer_session_id": a["reviewer_session_id"], "verdict": "ACCEPTED",
                                  "covers": sorted(p for p in ctx.bound if a["inputs"].get(p) == ctx.bound[p])}
                                 for a in sorted(area_rows, key=lambda a: a["area"])],
                       "components_covered": len(ctx.bound)}
    # the five entrypoints: bytes of the working file, M's sha256 and the blob at the APPROVED commit
    ctx.entry_rows = []
    modes = tree_modes(ctx, ctx.approved, [e["path"] for e in m["entrypoints"].values()])
    for role in ROLES:
        e = m["entrypoints"][role]
        data = read_regular(ctx, e["path"])
        if sha_bytes(data) != e["sha256"]:
            refuse("entrypoint %s does not hold the sha256 M binds: %s" % (role, e["path"]))
        oid = git(ctx, ctx.source, "rev-parse", "--verify", "--quiet", "%s:%s" % (ctx.approved, e["path"]))
        if oid.rc != 0 or oid.out.strip() != e["git_blob"] or data != blob_bytes(ctx, ctx.approved, e["path"]):
            refuse("entrypoint %s differs from the approved commit: %s" % (role, e["path"]))
        mode, kind = modes.get(e["path"], (None, None))
        if kind != "blob" or mode not in ("100644", "100755"):
            refuse("entrypoint is not a regular tracked file: %s" % e["path"])
        ctx.entry_rows.append({"role": role, "path": e["path"], "sha256": e["sha256"], "mode": 0o755 if mode == "100755" else 0o644})


def verify_manifest_check(ctx):
    """(a) the reviewed program judges the manifest against disk and git; run isolated, after (b) verified its bytes."""
    tool = os.path.join(ctx.fleet_src, "kymanifest.py")
    r = run([sys.executable, "-I", "-B", tool, "check", ctx.manifest_path, "--repo", ctx.source, "--run", ctx.run_dir], child_env(ctx),
            timeout=300)
    if r.rc != 0:
        refuse("kymanifest.py check exited %s: %s" % (r.rc, r.last_error()))
    try:
        said = json.loads(r.out)
    except ValueError:
        said = None
    if not isinstance(said, dict) or said.get("ok") is not True:
        refuse("kymanifest.py check exited 0 without ok: true")
    if said.get("manifest_sha256") != ctx.m["manifest_sha256"]:
        refuse("kymanifest.py check answered for another manifest digest")


def verify_staged(ctx):
    rel = STAGED
    data = read_regular(ctx, rel)
    if data != blob_bytes(ctx, ctx.components_commit, rel):
        refuse("the staged model actions differ from their blob at the components commit: %s" % rel)
    try:
        doc = json.loads(data)
    except ValueError:
        refuse("the staged model actions are not JSON: %s" % rel)
    entries = []
    for kind, key, fields in (("decision", "decisions", ("decision", "outcome", "as", "detail")),
                              ("park", "parks", ("item", "as", "detail")), ("block", "blocks", ("item", "as", "detail"))):
        rows = doc.get(key) if isinstance(doc, dict) else None
        if not isinstance(rows, list):
            refuse("staged model actions carry no %s list" % key)
        for row in rows:
            if not isinstance(row, dict) or any(not isinstance(row.get(f), str) or not row[f] for f in fields):
                refuse("staged %s entry is malformed: %r" % (kind, row))
            if row["as"] != "steward":             # the packet publishes every staged action `--as steward`
                refuse("staged %s entry is to be published as %r; the installer publishes as the steward only" % (kind, row["as"]))
            entries.append({"kind": kind, "id": row.get("decision") or row["item"], "as": row["as"], "detail": row["detail"],
                            "outcome": row.get("outcome"), "delegated": row.get("delegated") is True})
    if not entries:
        refuse("the staged model actions list nothing")
    ctx.staged = {"path": os.path.join(ctx.source, rel), "relative_path": rel, "sha256": sha_bytes(data), "entries": entries}
    blob_bytes(ctx, ctx.components_commit, PLAN_MODEL)          # refuses when S has no plan model for the tracker plist


def parse_version(text):
    m = re.search(r"(?<![0-9.])([0-9]+)\.([0-9]+)\.([0-9]+)(?![0-9.])", text)
    return tuple(int(x) for x in m.groups()) if m else None


def verify_claude(ctx):
    path = ctx.claude_bin
    if not os.path.isfile(path) or not os.access(path, os.X_OK):
        refuse("CLAUDE_BIN is not an executable file: %s" % path)
    r = run([path, "--version"], {"PATH": BASE_PATH, "HOME": ctx.home or "/", "LANG": "en_US.UTF-8"}, timeout=60)
    if r.rc != 0:
        refuse("CLAUDE_BIN --version failed: %s" % r.last_error())
    version = parse_version(r.out)
    if version is None:
        refuse("CLAUDE_BIN version unreadable: %s" % flat(r.out, 120))
    if version < MIN_CLAUDE:
        refuse("CLAUDE_BIN version %s is below the pin %s" % (".".join(map(str, version)), ".".join(map(str, MIN_CLAUDE))))
    ctx.claude_info = {"path": path, "realpath": real(path), "version": ".".join(map(str, version)),
                       "minimum_version": ".".join(map(str, MIN_CLAUDE)), "sha256": sha_file(real(path))}


def process_listing(ctx):
    """[(pid, ppid, command)]; anything unanswerable refuses."""
    r = run([ctx.ps, "-ww", "-axo", "pid=,ppid=,command="], child_env(ctx, LC_ALL="C"), timeout=60)
    if r.rc != 0:
        refuse("process listing failed (ps exited %s): %s" % (r.rc, r.last_error()))
    rows = []
    for line in r.out.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^\s*([0-9]+)\s+([0-9]+)\s+(.*)$", line)
        if not m:
            refuse("process listing unreadable: %s" % flat(line, 80))
        rows.append((int(m.group(1)), int(m.group(2)), m.group(3)))
    if len(rows) < 2:
        refuse("process listing is empty or implausibly short (%d rows)" % len(rows))
    return rows


def legacy_match(ctx, command):
    if "kalayantra_fleet.sh" in command or "claude_cycle.py" in command or "conductor/sweep.py" in command:
        return True
    return bool(re.search(r"(^|[/\s])codex\s+exec(\s|$)", command)) and (ctx.root + "/wt/") in command


def scan_processes(ctx):
    rows = process_listing(ctx)
    parents = {pid: ppid for pid, ppid, _ in rows}
    mine = set()
    pid = os.getpid()
    while pid and pid not in mine:
        mine.add(pid)
        pid = parents.get(pid, 0)
    matching = [{"pid": pid, "command": flat(cmd, 200)} for pid, _pp, cmd in rows if pid not in mine and legacy_match(ctx, cmd)]
    return {"answered": True, "examined": len(rows), "matching": matching,
            "patterns": ["kalayantra_fleet.sh", "claude_cycle.py", "conductor/sweep.py", "codex exec under %s/wt/" % ctx.root],
            "limits": list(PROCESS_LIMITS)}


def verify_processes(ctx):
    scan = scan_processes(ctx)
    if scan["matching"]:
        refuse("a legacy supervisor is alive (pid %s: %s); nothing was signalled" % (scan["matching"][0]["pid"],
                                                                                    scan["matching"][0]["command"]))


def verify_stop_files(ctx):
    """A STOP file stops a legacy lane only as a regular file: kalayantra_fleet.sh tests `[ -f "$RUN/STOP_$lane" ]`.
    A directory, a dangling link or anything else at that path is not a stop, whatever its presence suggests."""
    for lane in LANES:
        p = os.path.join(ctx.run_dir, "STOP_" + lane)
        if os.path.lexists(p) and not os.path.isfile(p):
            refuse("%s exists but is not a regular file: the legacy supervisor's `-f` test would not see it as a stop" % p)


def inspect_campaign(ctx):
    """Read-only: ('exists'|'absent', branch tip or None)."""
    s, camp = ctx.source, ctx.campaign
    try:
        tip = ref_tip(ctx, s, "refs/heads/" + CAMPAIGN_BRANCH)
    except Refused as e:
        refuse("the campaign branch: %s" % e)
    wl = git(ctx, s, "worktree", "list", "--porcelain")
    if wl.rc != 0:
        refuse("git worktree list failed in S: %s" % wl.last_error())
    registered, current = {}, None
    for line in wl.out.splitlines():
        if line.startswith("worktree "):
            current = real(line[len("worktree "):])
            registered[current] = None
        elif line.startswith("branch ") and current:
            registered[current] = line[len("branch "):]
    if os.path.lexists(camp):
        if real(camp) not in registered:
            refuse("the campaign checkout path exists but is not a worktree of S's repository: %s" % camp)
        if registered[real(camp)] != "refs/heads/" + CAMPAIGN_BRANCH:
            refuse("the campaign checkout is not on %s: %s" % (CAMPAIGN_BRANCH, camp))
        head = git_ok(ctx, camp, "rev-parse", "HEAD")
        if head != ctx.components_commit:
            refuse("the campaign checkout is at %s, not at the components commit %s (never fast-forwarded in the hold, ruling P9)"
                   % (head, ctx.components_commit))
        if git_ok(ctx, camp, "status", "--porcelain", "--untracked-files=all"):
            refuse("the campaign checkout is not clean: %s" % camp)
        return "exists", tip
    if tip is not None:
        if tip != ctx.components_commit:
            refuse("the campaign branch %s is at %s, not at the components commit %s" % (CAMPAIGN_BRANCH, tip, ctx.components_commit))
        if any(b == "refs/heads/" + CAMPAIGN_BRANCH for b in registered.values()):
            refuse("the campaign branch %s is already checked out in another worktree" % CAMPAIGN_BRANCH)
    return "absent", tip


def verify_action(ctx):
    if not ctx.action:
        ctx.action_state = None
        return
    path = os.path.join(ctx.run_dir, "actions", ctx.action + ".json")
    if not os.path.isfile(path):
        refuse("action %s: no record at %s" % (ctx.action, path))
    rec = read_json_object(path, "action %s record" % ctx.action)
    if rec.get("schema") != "ky.action/1" or rec.get("action_id") != ctx.action:
        refuse("action %s: the record is not a ky.action/1 record of that id" % ctx.action)
    if rec.get("kind") != "install":
        refuse("action %s: kind is %r, not 'install'" % (ctx.action, rec.get("kind")))
    inputs = rec.get("inputs") if isinstance(rec.get("inputs"), dict) else {}
    if inputs.get("manifest_sha256") != ctx.manifest_file_sha:
        refuse("action %s: inputs.manifest_sha256 does not bind this manifest file" % ctx.action)
    if inputs.get("source_commit") != ctx.components_commit:
        refuse("action %s: inputs.source_commit does not bind this source commit" % ctx.action)
    state = rec.get("state")
    if state != "INTENDED":                          # this run completes or fails the record: only an open one can be
        hint = {"FAILED": "its owner must retry it (kyaction retry) before it is run again",
                "DONE": "it has been completed; a later run needs a fresh INTENDED record"}.get(state, "unknown state")
        refuse("action %s is %r, not INTENDED: %s" % (ctx.action, state, hint), "E_ACTION_STATE")
    ctx.action_state = state


def verify(ctx):
    load_manifest(ctx)
    verify_source(ctx)
    verify_action(ctx)
    classify(ctx)
    verify_provenance(ctx)
    verify_manifest_check(ctx)
    verify_staged(ctx)
    verify_claude(ctx)
    verify_stop_files(ctx)
    verify_processes(ctx)
    ctx.campaign_state = inspect_campaign(ctx)


# ------------------------------------------------------------------------------------------------ writing
def progress(text):
    sys.stderr.write("install.sh: %s\n" % text)
    sys.stderr.flush()


class Entry:
    def __init__(self, src, sha, mode):
        self.src, self.sha, self.mode = src, sha, mode


def fleet_entries(ctx):
    out = {}
    for rel, p in ctx.fleet_files.items():
        out[rel] = Entry(p, ctx.bound[p], ctx.modes[p])
    for row in ctx.entry_rows:
        key = "bundle/" + row["path"]
        if key in out:
            raise Failed(1, "the bundle path collides with a fleet component: %s" % key)
        out[key] = Entry(row["path"], row["sha256"], row["mode"])
    return out


def tracker_entries(ctx):
    return {"pravaha_tracker/" + rel: Entry(p, ctx.bound[p], ctx.modes[p]) for rel, p in ctx.tracker_files.items()}


def tree_files(root):
    """{relpath: (sha256, permission bits)} of the regular files below root, __pycache__ ignored; None for a link/other."""
    out = {}
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d != "__pycache__")
        for name in fns:
            p = os.path.join(dp, name)
            st = os.lstat(p)
            if not stat.S_ISREG(st.st_mode):
                out[os.path.relpath(p, root)] = None
            elif name.endswith(".pyc") and "__pycache__" in dp:
                continue
            else:
                out[os.path.relpath(p, root)] = (sha_file(p), stat.S_IMODE(st.st_mode))
    return out


def tree_matches(root, entries):
    if not os.path.isdir(root) or os.path.islink(root):
        return False
    have = tree_files(root)
    want = {rel: (e.sha, e.mode) for rel, e in entries.items()}
    return have == want


def tree_digest(entries):
    return sha_bytes("".join("%s  %s\n" % (e.sha, rel) for rel, e in sorted(entries.items())).encode())


def supersede_receipt(ctx):
    """Move an earlier run's receipt aside. No rollback puts it back: only a run that exits 0 leaves a receipt."""
    if not os.path.lexists(ctx.receipt_path):
        return
    os.replace(ctx.receipt_path, ctx.receipt_path + ".superseded")
    ctx.superseded = True


def swap_tree(ctx, step, label, final, entries):
    """Build final.new from S, then swap by rename keeping the old tree as final.old. Unchanged trees are left alone."""
    if tree_matches(final, entries):
        ctx.changed[label] = False
        return
    new, old = final + ".new", final + ".old"
    if os.path.lexists(new):
        shutil.rmtree(new)
    os.makedirs(new, mode=0o755)
    try:
        for rel, e in sorted(entries.items()):
            data = read_regular(ctx, e.src)
            if sha_bytes(data) != e.sha:
                raise Failed(step, "%s changed while it was being installed" % e.src)
            dest = os.path.join(new, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
            os.chmod(dest, e.mode)
        if not tree_matches(new, entries):
            raise Failed(step, "the staged %s does not match what was to be installed" % label)
    except (Refused, OSError) as e:
        shutil.rmtree(new, ignore_errors=True)
        raise Failed(step, "staging %s failed: %s" % (label, flat(e)))
    except Failed:
        shutil.rmtree(new, ignore_errors=True)
        raise
    supersede_receipt(ctx)
    had = os.path.lexists(final)
    if os.path.lexists(old):
        shutil.rmtree(old)
    if had:
        os.rename(final, old)
    os.rename(new, final)
    fsync_dir(os.path.dirname(final))

    def undo():
        if had and not os.path.lexists(old):          # nothing to put back: say so, never report this tree restored
            raise OSError("the kept tree %s is gone; %s still holds the new files" % (os.path.basename(old), final))
        if os.path.lexists(final):
            shutil.rmtree(final)
        if had:
            os.rename(old, final)
    ctx.undo.append(undo)
    ctx.changed[label] = True


def install_file(ctx, step, label, dest, data, mode):
    """Atomic replace of one file; unchanged bytes and mode are left alone."""
    try:
        st = os.lstat(dest)
        if stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode) == mode and sha_file(dest) == sha_bytes(data):
            ctx.changed[label] = False
            return
        previous = open(dest, "rb").read() if stat.S_ISREG(st.st_mode) else None
        previous_mode = stat.S_IMODE(st.st_mode)
    except FileNotFoundError:
        previous, previous_mode = None, None
    supersede_receipt(ctx)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    write_atomic(dest, data, mode)

    def undo():
        if previous is None:
            if os.path.lexists(dest):
                os.unlink(dest)
        else:
            write_atomic(dest, previous, previous_mode)
    ctx.undo.append(undo)
    ctx.changed[label] = True


def step_stop(ctx):
    os.makedirs(ctx.run_dir, exist_ok=True)
    rows = []
    for lane in LANES:
        p = os.path.join(ctx.run_dir, "STOP_" + lane)
        existed = os.path.lexists(p)
        if not existed:
            fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            with os.fdopen(fd, "w") as f:
                f.write("stopped by install.sh at %s (bootstrap installation); legacy lane %s must not dispatch\n" % (utc_now(), lane))
        if not os.path.isfile(p):
            raise Failed(0, "%s is not a regular file after the STOP files were written" % p)
        rows.append({"lane": lane, "path": p, "present": True})
    scan = scan_processes(ctx)
    if scan["matching"]:
        raise Failed(0, "a legacy supervisor is alive after the STOP files were written (pid %s: %s); nothing was signalled"
                     % (scan["matching"][0]["pid"], scan["matching"][0]["command"]))
    ctx.processes_examined = scan.pop("examined")                # volatile: reported on stdout, not part of the stable receipt
    ctx.old_supervisors = {"stop_files": rows, "processes": scan}


def step_fleet(ctx):
    swap_tree(ctx, 1, "fleet_live", ctx.fleet_live, fleet_entries(ctx))


def step_tracker_tree(ctx):
    swap_tree(ctx, 2, "tracker_live", ctx.tracker_live, tracker_entries(ctx))


def step_bin(ctx):
    for name, p in sorted(ctx.bin_files.items()):
        data = read_regular(ctx, p)
        if sha_bytes(data) != ctx.bound[p]:
            raise Failed(3, "%s changed while it was being installed" % p)
        install_file(ctx, 3, "bin/" + name, os.path.join(ctx.bin_dir, name), data, 0o755)


def step_versions(ctx):
    with open(ctx.manifest_path, "rb") as f:
        data = f.read()
    if sha_bytes(data) != ctx.manifest_file_sha:
        raise Failed(4, "the manifest changed while it was being installed")
    install_file(ctx, 4, "VERSIONS.bootstrap.json", ctx.versions_path, data, 0o644)


def count_registrations(ctx):
    wl = git(ctx, ctx.source, "worktree", "list", "--porcelain")
    if wl.rc != 0:
        raise Failed(5, "git worktree list failed: %s" % wl.last_error())
    parent = real(os.path.dirname(ctx.campaign))
    n = 0
    for line in wl.out.splitlines():
        if line.startswith("worktree "):
            p = real(line[len("worktree "):])
            if os.path.dirname(p) == parent and p != real(ctx.campaign):
                n += 1
    return n, parent


def step_campaign(ctx):
    state, tip = inspect_campaign(ctx)
    created = False
    count, parent = count_registrations(ctx)
    if state == "absent":
        if count > CAPACITY:
            raise Failed(5, "capacity: %d worktree registrations already sit under %s (ceiling: at most %d before the campaign "
                            "checkout is added)" % (count, parent, CAPACITY))
        os.makedirs(os.path.dirname(ctx.campaign), exist_ok=True)
        args = ["worktree", "add"] + ([ctx.campaign, CAMPAIGN_BRANCH] if tip else ["-b", CAMPAIGN_BRANCH, ctx.campaign, ctx.components_commit])
        r = git(ctx, ctx.source, *args)
        if r.rc != 0:
            raise Failed(5, "git worktree add of the campaign checkout failed: %s" % r.last_error())
        created = ctx.campaign_created = True
    head = git(ctx, ctx.campaign, "rev-parse", "HEAD").out.strip()
    branch = git(ctx, ctx.campaign, "symbolic-ref", "--short", "HEAD").out.strip()
    if head != ctx.components_commit or branch != CAMPAIGN_BRANCH:
        raise Failed(5, "the campaign checkout is at %s on %s, not at the components commit on %s" % (head, branch, CAMPAIGN_BRANCH))
    if ref_tip(ctx, ctx.source, "refs/remotes/origin/main") is None:
        raise Failed(5, "S has no origin/main for %s to track (plan §5: upstream origin/main)" % CAMPAIGN_BRANCH)
    upstream = git(ctx, ctx.campaign, "rev-parse", "--abbrev-ref", CAMPAIGN_BRANCH + "@{upstream}")
    if upstream.rc != 0 or upstream.out.strip() != "origin/main":
        up = git(ctx, ctx.campaign, "branch", "--set-upstream-to=origin/main", CAMPAIGN_BRANCH)
        if up.rc != 0:
            raise Failed(5, "setting the upstream of %s to origin/main failed: %s" % (CAMPAIGN_BRANCH, up.last_error()))
        upstream = git(ctx, ctx.campaign, "rev-parse", "--abbrev-ref", CAMPAIGN_BRANCH + "@{upstream}")
    if upstream.rc != 0 or upstream.out.strip() != "origin/main":
        raise Failed(5, "the upstream of %s reads %r, not origin/main" % (CAMPAIGN_BRANCH, upstream.out.strip() or None))
    if git_ok(ctx, ctx.campaign, "rev-parse", "HEAD") != ctx.components_commit:
        raise Failed(5, "the campaign checkout moved while its upstream was set")
    if not os.path.isfile(os.path.join(ctx.campaign, PLAN_MODEL)):
        raise Failed(5, "the campaign checkout holds no plan model at %s" % PLAN_MODEL)
    ctx.changed["campaign_checkout"] = created
    ctx.campaign_info = {"path": ctx.campaign, "branch": branch, "head": head, "components_commit": ctx.components_commit,
                         "upstream": upstream.out.strip(), "policy_root": parent}
    ctx.registrations = count + 1                                # volatile: reported on stdout, not part of the stable receipt


# ---- step 6: the tracker
def tracker_plist(ctx):
    live, fleet = ctx.tracker_live, ctx.fleet_live
    env = {"PATH": BASE_PATH, "HOME": ctx.home, "PRAVAHA_HOME": ctx.root,
           "PRAVAHA_EVENTS": os.path.join(ctx.run_dir, "EVENTS.jsonl"),
           "PRAVAHA_PLAN_MODEL": os.path.join(ctx.campaign, PLAN_MODEL), "PRAVAHA_TRACKER_PORT": str(ctx.port),
           "PRAVAHA_REPO": ctx.campaign, "PRAVAHA_PGENV": os.path.join(ctx.home, ".config", "pravaha", "pgenv.sh"),
           "PRAVAHA_HOLD": os.path.join(ctx.root, "HOLD"), "PYTHONUNBUFFERED": "1", "PYTHONPATH": live + ":" + fleet}
    doc = {"Label": TRACKER_LABEL, "ProgramArguments": [TRACKER_PY, "-u", "-m", "pravaha_tracker.server", "--port", str(ctx.port)],
           "WorkingDirectory": live, "EnvironmentVariables": env, "RunAtLoad": True, "KeepAlive": True,
           "ProcessType": "Background", "ThrottleInterval": 2,
           "StandardOutPath": os.path.join(ctx.run_dir, "tracker.log"), "StandardErrorPath": os.path.join(ctx.run_dir, "tracker.log")}
    return plistlib.dumps(doc)


def launchctl(ctx, *args, timeout=120):
    return run([ctx.launchctl] + list(args), child_env(ctx), timeout=timeout)


def tracker_target(ctx):
    return "gui/%d/%s" % (ctx.uid, TRACKER_LABEL)


def process_start(ctx, pid):
    r = run([ctx.ps, "-ww", "-o", "lstart=", "-p", str(pid)], child_env(ctx, LC_ALL="C"), timeout=30)
    text = r.out.strip()
    if r.rc != 0 or not text:
        raise Failed(6, "the start time of the tracker process %s is unknown (ps: %s)" % (pid, r.last_error()))
    try:
        epoch = time.mktime(time.strptime(text, "%a %b %d %H:%M:%S %Y"))
    except ValueError:
        raise Failed(6, "the start time of the tracker process %s is unreadable: %s" % (pid, flat(text, 60)))
    return text, int(epoch)


def tracker_process(ctx):
    """None when the job is not loaded or has no pid; else {pid, process_start, start_epoch}."""
    r = launchctl(ctx, "print", tracker_target(ctx))
    if r.rc is None:
        raise Failed(6, "launchctl could not be run: %s" % r.err)
    if r.rc != 0:
        return None
    m = re.search(r"^\s*pid = ([0-9]+)\s*$", r.out, re.M)
    if not m:
        return None
    pid = int(m.group(1))
    text, epoch = process_start(ctx, pid)
    return {"pid": pid, "process_start": text, "start_epoch": epoch}


def fetch_health(ctx):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(ctx.url + "/api/health", timeout=3) as resp:
        return json.loads(resp.read().decode("utf-8"))


def judge_health(ctx, h):
    """(what the receipt records, None) for a healthy answer of THIS root's tracker in the shape server.py emits
    ({ok, model_error, server_started_at, event_log{path}, …}); else (None, why). An unrecognised shape is unknown."""
    if not isinstance(h, dict) or "model_error" not in h:
        return None, "the answer carries no model_error field"
    if h["model_error"] not in (None, ""):
        return None, "the tracker reports model_error: %s" % flat(h["model_error"], 160)
    if h.get("ok") is not True:
        return None, "ok is not true"
    log = h.get("event_log")
    if not isinstance(log, dict) or not isinstance(log.get("path"), str) or not log["path"]:
        return None, "the answer names no event_log.path (not the shape the tracker emits)"
    events = os.path.join(ctx.run_dir, "EVENTS.jsonl")
    if real(log["path"]) != real(events):
        return None, "the answering tracker serves another event log (%s), not %s" % (flat(log["path"], 200), events)
    try:
        started = datetime.datetime.fromisoformat(h.get("server_started_at"))
        if started.tzinfo is None:
            raise ValueError("no timezone")
    except (TypeError, ValueError):
        return None, "the answer carries no usable server_started_at (not the shape the tracker emits)"
    return {"ok": True, "model_error": None, "server_started_at": h["server_started_at"], "event_log": events,
            "started_epoch": int(started.timestamp())}, None


def wait_health(ctx):
    deadline = time.time() + ctx.wait_s
    last = "no answer"
    while True:
        try:
            health, last = judge_health(ctx, fetch_health(ctx))
            if health is not None:
                return health
        except (OSError, ValueError, urllib.error.URLError) as e:
            last = "no usable answer (%s)" % type(e).__name__
        if time.time() >= deadline:
            raise Failed(6, "tracker health at %s/api/health: %s (waited %ds)" % (ctx.url, last, ctx.wait_s))
        time.sleep(0.5)


def answered_by(proc, health):
    """The health answer can be the recorded process's only when the server in it started no earlier than that process."""
    return health["started_epoch"] >= proc["start_epoch"]


def newest_mtime(paths):
    newest = 0.0
    for p in paths:
        newest = max(newest, os.stat(p).st_mtime)
    return newest


def step_tracker(ctx):
    plist_path = os.path.join(ctx.la_dir, TRACKER_LABEL + ".plist")
    os.makedirs(ctx.la_dir, exist_ok=True)
    install_file(ctx, 6, "tracker_plist", plist_path, tracker_plist(ctx), 0o644)
    loaded = [os.path.join(ctx.fleet_live, rel) for rel in fleet_entries(ctx)] + \
             [os.path.join(ctx.tracker_live, rel) for rel in tracker_entries(ctx)] + [plist_path]
    newest = newest_mtime(loaded)
    boundary = int(newest) + 1
    proc = tracker_process(ctx)
    health = None
    if proc is not None and proc["start_epoch"] >= boundary:
        try:
            health = judge_health(ctx, fetch_health(ctx))[0]
        except (OSError, ValueError, urllib.error.URLError):
            health = None
        if health is not None and not answered_by(proc, health):
            health = None
    restarted = False
    if health is None:
        ctx.committed = True                    # from here the trees are no longer restored: the tracker will load them
        restarted = True
        while time.time() < boundary:           # "started after the swap" is strict at ps's one-second resolution
            time.sleep(0.05)
        target = tracker_target(ctx)
        launchctl(ctx, "bootout", target)
        # bootout returns before launchd necessarily removes the old registration.
        unload_deadline = time.monotonic() + min(30, ctx.wait_s)
        while True:
            remaining = unload_deadline - time.monotonic()
            if remaining <= 0:
                raise Failed(6, "the tracker service did not unload after the swap (waited %ds)" % min(30, ctx.wait_s))
            unloaded = launchctl(ctx, "print", target, timeout=remaining)
            if unloaded.rc is None:
                raise Failed(6, "launchctl could not be run: %s" % unloaded.err)
            if unloaded.rc != 0:
                break
            time.sleep(min(0.5, max(0, unload_deadline - time.monotonic())))
        for attempt in range(3):
            r = launchctl(ctx, "bootstrap", "gui/%d" % ctx.uid, plist_path)
            if r.rc == 0:
                break
            if attempt < 2:
                time.sleep(0.5)
        if r.rc != 0:
            raise Failed(6, "launchctl bootstrap of the tracker failed (exit %s): %s" % (r.rc, r.last_error()))
        launchctl(ctx, "enable", target)
        health = wait_health(ctx)
        proc = tracker_process(ctx)
        if proc is None:
            raise Failed(6, "the tracker job has no running process after the restart")
        if proc["start_epoch"] < boundary:
            raise Failed(6, "the tracker process %s started at %s, not after the swap of the files it loads" %
                         (proc["pid"], proc["process_start"]))
        if not answered_by(proc, health):
            raise Failed(6, "the health answer's server_started_at %s is before the start of the tracker process %s (%s): "
                            "it is not that process's answer" % (health["server_started_at"], proc["pid"], proc["process_start"]))
        ctx.restart_confirmed = True            # a process started after the swap answered for this root
    ctx.changed["tracker_restarted"] = restarted
    pkg = tracker_entries(ctx)
    ctx.tracker_info = {"package_sha256": tree_digest(pkg), "package_dir": os.path.join(ctx.tracker_live, "pravaha_tracker"),
                        "pid": proc["pid"], "process_start": proc["process_start"], "plist": plist_path,
                        "plist_sha256": sha_file(plist_path), "url": ctx.url,
                        "health": {k: v for k, v in health.items() if k != "started_epoch"}}


def read_events(path):
    """([(line number, event, raw line bytes)], count of unreadable lines)."""
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        return [], 0
    events, bad = [], 0
    for n, line in enumerate(raw.split(b"\n"), 1):
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            bad += 1
            continue
        if isinstance(ev, dict):
            events.append((n, ev, line))
        else:
            bad += 1
    return events, bad


def event_matches(entry, ev):
    if entry["kind"] == "decision":
        return ev.get("kind") == "decision" and ev.get("decision") == entry["id"] and ev.get("state") == (
            "delegated" if entry["delegated"] else "decided") and ev.get("outcome") == entry["outcome"] \
            and ev.get("actor") == entry["as"] and ev.get("detail") == entry["detail"]
    return ev.get("kind") == "item" and ev.get("item") == entry["id"] and ev.get("state") == (
        "parked" if entry["kind"] == "park" else "blocked") and ev.get("actor") == entry["as"] and ev.get("detail") == entry["detail"]


def find_event(ctx, entry):
    events, bad = read_events(os.path.join(ctx.run_dir, "EVENTS.jsonl"))
    for n, ev, raw in events:
        if event_matches(entry, ev):
            return {"line": n, "sha256": sha_bytes(raw), "ts": ev.get("ts")}, bad
    return None, bad


def ky_command(ctx, entry):
    ky = os.path.join(ctx.bin_dir, "ky")
    if entry["kind"] == "decision":
        return [ky, "decide", entry["id"], "--outcome", entry["outcome"], "--as", entry["as"]] + \
            (["--delegated"] if entry["delegated"] else []) + ["--detail", entry["detail"]]
    return [ky, entry["kind"], entry["id"], "--as", entry["as"], "--detail", entry["detail"]]


def step_publish(ctx):
    done, report = [], []
    for entry in ctx.staged["entries"]:
        event, bad = find_event(ctx, entry)
        status = "skipped_existing"
        if event is None:
            if bad:
                raise Failed(6, "cannot exclude an existing event for %s %s: the event log has %d unreadable line(s)" %
                             (entry["kind"], entry["id"], bad))
            r = run(ky_command(ctx, entry), ky_env(ctx), timeout=120)
            if r.rc != 0:
                raise Failed(6, "ky %s %s exited %s: %s" % (entry["kind"], entry["id"], r.rc, r.last_error()))
            event, _ = find_event(ctx, entry)
            if event is None:
                raise Failed(6, "ky %s %s exited 0 but its event was not found in the event log" % (entry["kind"], entry["id"]))
            status = "published"
        report.append({"id": entry["id"], "status": status})
        done.append({"kind": entry["kind"], "id": entry["id"], "as": entry["as"], "event": event})
        progress("model action %s %s: %s" % (entry["kind"], entry["id"], status))
    ctx.model_report = report
    ctx.model_actions = {"source": ctx.staged["path"], "relative_path": ctx.staged["relative_path"], "sha256": ctx.staged["sha256"],
                         "entries": done}


# ---- step 7: legacy
def step_legacy(ctx):
    claims_dir = os.path.join(ctx.run_dir, "claims")
    claims, unresolved, by_item = [], [], {}
    events_path = os.path.join(ctx.run_dir, "EVENTS.jsonl")
    logged_before, _ = read_events(events_path)
    names = sorted(n for n in os.listdir(claims_dir) if n.endswith(".json") and ".tmp." not in n) if os.path.isdir(claims_dir) else []
    for name in names:
        p = os.path.join(claims_dir, name)
        stem = name[:-5]
        row = {"path": p, "worker_id": stem, "sha256": sha_file(p)}
        try:
            doc = json.loads(open(p, "rb").read())
            if not isinstance(doc, dict) or doc.get("worker_id") != stem or not SAFE_NAME.match(stem):
                raise ValueError("worker_id does not match the file name")
        except ValueError as e:
            row.update(action="unresolved", reason="unreadable claim record (%s)" % flat(e, 80))
            claims.append(row)
            unresolved.append({"kind": "claim", "worker_id": stem, "path": p, "reason": row["reason"]})
            continue
        state = doc.get("state")
        row.update(item=doc.get("item"), claim_id=doc.get("claim_id"), branch=doc.get("branch"), head=doc.get("head"),
                   state_before=state, state_after=state)
        by_item.setdefault(doc.get("item"), []).append(row)
        if state in CLAIM_ENDED:
            logged = claim_log_state(logged_before, doc)
            if logged in CLAIM_ENDED:
                row["action"] = "already_ended"
            else:                                    # claims.py reads the log, never the record
                row.update(action="unresolved", reason="the claim record reads %r but the event log, the tracker's authority, "
                                                       "shows that claim as %r: whether it has ended is unknown" % (state, logged))
        elif state not in CLAIM_ACTIVE:
            row.update(action="unresolved", reason="the claim record carries the state %r, which the tracker does not write: "
                                                   "whether the claim has ended is unknown" % (state,))
        elif stem not in LANES:
            row.update(action="unresolved", reason="an active claim of %s, which is not a legacy lane: it is not this "
                                                   "installation's to release" % stem)
        else:
            r = run([os.path.join(ctx.bin_dir, "ky"), "release"], ky_env(ctx, lane=stem), timeout=120)
            after = None
            try:
                after = json.loads(open(p, "rb").read()).get("state")
            except (OSError, ValueError, AttributeError):
                pass
            row["state_after"] = after
            event = release_event(ctx, doc) if r.rc == 0 and after == "released" else None
            if event is not None:
                row.update(action="released", release_event=event)
            elif r.rc == 0 and after == "released":
                row.update(action="unresolved", reason="ky release exited 0 and the claim record reads 'released', but the "
                                                       "event log holds no released event as that claim's latest")
            else:
                row.update(action="unresolved", reason="ky release exited %s and the claim reads %r afterwards: %s"
                                                       % (r.rc, after, r.last_error()))
        if row["action"] == "unresolved":
            unresolved.append({"kind": "claim", "worker_id": stem, "path": p, "reason": row["reason"]})
        claims.append(row)
    prs = list_prs(ctx)
    events, bad = read_events(events_path)           # read again: this run's releases are in it now
    shown = {(c.get("worker_id"), c.get("claim_id")) for c in claims}
    latest_claim, registered, latest_review = {}, {}, {}
    for n, ev, raw in events:
        if ev.get("kind") == "claim" and isinstance(ev.get("item"), str):
            latest_claim[ev["item"]] = (n, ev)
        if ev.get("kind") == "item" and ev.get("state") == "review" and isinstance(ev.get("item"), str):
            latest_review[ev["item"]] = n            # completion.py: the item's latest review event is its registration
            if isinstance(ev.get("detail"), str):
                for m in PR_REGISTRATION.finditer(ev["detail"]):
                    registered[int(m.group(1))] = {"head": m.group(2), "item": ev["item"], "line": n, "sha256": sha_bytes(raw)}
    for item, (n, ev) in sorted(latest_claim.items(), key=lambda kv: kv[1][0]):
        if ev.get("state") in CLAIM_ACTIVE and (ev.get("worker_id"), ev.get("claim_id")) not in shown:
            unresolved.append({"kind": "claim_event", "worker_id": ev.get("worker_id"), "item": item, "claim_id": ev.get("claim_id"),
                               "state": ev.get("state"), "expires_at": ev.get("expires_at"), "events_line": n,
                               "reason": "the event log's latest claim event of this item is active and no record under %s "
                                         "shows that claim (the tracker keeps one record per worker): it was not released"
                                         % claims_dir})
    adopted = []
    for pr in prs:
        reg = registered.get(pr["number"])
        why = None
        if bad:                                      # a line that cannot be read may be a later registration
            why = "the event log has %d unreadable line(s): the tracker's latest registration for this PR is unknown" % bad
        elif reg is None:
            why = "the tracker has no review registration for this PR"
        elif not pr["head"].startswith(reg["head"]):
            why = "the PR head moved since the tracker registered %s" % reg["head"]
        elif latest_review.get(reg["item"]) != reg["line"]:
            why = "the item %s has a later review event than this registration: its latest review registration is not this PR's" \
                  % reg["item"]
        else:
            row, why = adopt_pr(ctx, pr, reg, by_item.get(reg["item"], []))
            if row is not None:
                adopted.append(row)
        if why:
            unresolved.append({"kind": "pr", "number": pr["number"], "branch": pr["branch"], "head": pr["head"], "reason": why})
    cps = []
    for name in sorted(os.listdir(ctx.run_dir)):
        m = CHECKPOINT.match(name)
        if m:
            p = os.path.join(ctx.run_dir, name)
            cps.append({"path": p, "lane": m.group(1), "cycle": int(m.group(2)), "sha256": sha_file(p)})
    checkpoints = {"count": len(cps), "listing_sha256": sha_bytes("".join("%s  %s\n" % (c["sha256"], c["path"]) for c in cps).encode()),
                   "files": cps}
    if cps:
        unresolved.append({"kind": "checkpoints", "count": len(cps),
                           "reason": "a legacy cycle checkpoint maps to no job: no adoption rule applies, they are listed with hashes"})
    ctx.legacy = {"claims": claims, "prs": {"listed": prs, "adopted": adopted}, "checkpoints": checkpoints, "unresolved": unresolved}


def claim_log_state(events, claim):
    """The state the latest event of this claim (its claim_id, item and worker) carries in the event log, else None."""
    for _n, ev, _raw in reversed(events):
        if ev.get("kind") == "claim" and ev.get("claim_id") == claim.get("claim_id") and ev.get("item") == claim.get("item") \
                and ev.get("worker_id") == claim.get("worker_id"):
            return ev.get("state")
    return None


def release_event(ctx, claim):
    """{line, sha256} of the `released` event that is the latest claim event of this claim's item and carries its
    claim_id (what claims.release_claim appends before it rewrites the worker's record), else None."""
    events, _bad = read_events(os.path.join(ctx.run_dir, "EVENTS.jsonl"))
    for n, ev, raw in reversed(events):
        if ev.get("kind") == "claim" and ev.get("item") == claim.get("item"):
            if ev.get("state") == "released" and ev.get("claim_id") == claim.get("claim_id") \
                    and ev.get("worker_id") == claim.get("worker_id"):
                return {"line": n, "sha256": sha_bytes(raw)}
            return None
    return None


def list_prs(ctx):
    if not ctx.gh:
        raise Failed(7, "gh is not available to list the open kalayantra/* PRs")
    r = run([ctx.gh, "pr", "list", "--state", "open", "--limit", "500", "--json", "number,headRefName,headRefOid,url"],
            child_env(ctx), cwd=ctx.source, timeout=180)
    if r.rc != 0:
        raise Failed(7, "gh pr list failed (exit %s): %s" % (r.rc, r.last_error()))
    try:
        rows = json.loads(r.out)
    except ValueError:
        raise Failed(7, "gh pr list answered something that is not JSON")
    if not isinstance(rows, list) or len(rows) >= 500:
        raise Failed(7, "gh pr list answered a non-list or a possibly truncated list (%s rows)" %
                     (len(rows) if isinstance(rows, list) else "?"))
    out = []
    for row in rows:
        if not isinstance(row, dict) or type(row.get("number")) is not int or not isinstance(row.get("headRefName"), str) \
                or not HEX40.match(str(row.get("headRefOid"))):
            raise Failed(7, "gh pr list answered a malformed row: %r" % (row,))
        if row["headRefName"].startswith("kalayantra/"):
            out.append({"number": row["number"], "branch": row["headRefName"], "head": row["headRefOid"], "url": row.get("url")})
    return sorted(out, key=lambda r: r["number"])


def adopt_pr(ctx, pr, reg, claim_rows):
    job_id = "legacy-%d" % pr["number"]
    path = os.path.join(ctx.run_dir, "legacy", job_id, "state.json")
    claim = None
    if claim_rows:
        c = claim_rows[0]
        claim = {"path": c["path"], "worker_id": c["worker_id"], "claim_id": c.get("claim_id"), "state": c.get("state_after")}
    state = {"schema": "ky.legacy_job_state/1", "job_id": job_id, "kind": "LEGACY", "item": reg["item"], "pr": pr["number"],
             "branch": pr["branch"], "head": pr["head"], "registered_head": reg["head"], "slot": claim["worker_id"] if claim else None,
             "claim": claim, "session_id": None, "evidence_fp": None, "attempts": None, "adopted_by": "install.sh",
             "registration": {"events_line": reg["line"], "event_sha256": reg["sha256"]}}
    existing = os.path.lexists(path)
    if existing:                                     # never overwritten; it counts only when it is this PR's own adoption record
        try:
            with open(path, "rb") as f:
                have = json.loads(f.read())
        except (OSError, ValueError):
            have = None
        same = isinstance(have, dict) and all(have.get(k) == state[k] for k in ("schema", "job_id", "kind", "item", "pr", "branch", "head"))
        if not same:
            return None, "a job state already at %s is not this PR's adoption record at this head; it was left untouched" % path
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_atomic(path, (json.dumps(state, indent=1, sort_keys=True) + "\n").encode())
    return {"number": pr["number"], "job_id": job_id, "item": reg["item"], "state_path": path, "state_sha256": sha_file(path),
            "registered_head": reg["head"], "existing_state_kept": existing}, None


# ---- step 8-9: loop plists and qualifications
# Conventional qualification identities for installed job-role templates (not the launched jobs).
# Stream and pool from kyd_kinds_build.py:485, :686, :695, :737 and
# kyd_kinds_ops.py:729, :862, :1137, :1305, :1368, :1497, :1657.
# (I) INTERPRETATION: representative b1/v1 slots follow the existing installer
# convention; qualification has its own controller and never claims a real item.
QUALIFICATION_JOB_ENV = {
    role: {"KY_STREAM": stream, "KY_LANE": lane, "KY_CONTROLLER_ID": "CTL-qualification"}
    for role, stream, lane in (
        ("build", "K", "b1"), ("rework", "K", "b1"), ("verify", "V", "v1"),
        ("artifact", "V", "v1"), ("pre-accept", "V", "v1"), ("post-readback", "V", "v1"),
        ("ruling", "N", "b1"), ("request-prep", "N", "b1"), ("model", "S", "b1"),
        ("plan", "S", "b1"), ("surrogate", "steward", "b1"))
}


def qualification_tag(cfg, doc):
    """Distinct installed-template receipt/evidence names; the role itself stays unchanged."""
    name = os.path.basename(cfg)
    if not name.startswith("LAUNCH_CONFIG."):
        return doc["role"]              # generated planner/conductor configuration
    match = re.fullmatch(r"LAUNCH_CONFIG\.([a-z][a-z0-9-]*)(\.chart)?(\.tests)?(\.codex)?\.json", name)
    if (not match or match[1] != doc["role"]
            or bool(match[4]) != (doc.get("engine", "claude") == "codex")
            or doc.get("engine", "claude") not in ("claude", "codex")):
        raise Failed(9, "launch template name disagrees with role/engine: " + cfg)
    return doc["role"] + ("-chart" if match[2] else "") + ("-tests" if match[3] else "")



def plist_facts(path, label, kind):
    try:
        with open(path, "rb") as f:
            raw = f.read()
        doc = plistlib.loads(raw)
    except (OSError, ValueError, plistlib.InvalidFileException) as e:
        raise Failed(8, "plist unreadable: %s (%s)" % (path, type(e).__name__))
    if doc.get("Label") != label:
        raise Failed(8, "plist %s carries label %r, not %r" % (path, doc.get("Label"), label))
    env = doc.get("EnvironmentVariables") if isinstance(doc.get("EnvironmentVariables"), dict) else {}
    hooks = sorted(n for n in env if n in HOOK_NAMES or n.startswith("KY_TEST"))
    return {"label": label, "kind": kind, "path": path, "sha256": sha_bytes(raw), "env_keys": sorted(env),
            "hook_variables": hooks, "ky_scratch": env.get("KY_SCRATCH")}


def step_loops(ctx):
    ctl = os.path.join(ctx.fleet_live, "kyctl.sh")
    env = ky_dir_env(ctx, KY_LAUNCHAGENTS_DIR=ctx.la_dir, KY_LAUNCHCTL=ctx.launchctl)
    if not ctx.is_real and "KY_GIT" in ctx.pass_through:
        env["KY_GIT"] = ctx.git
    r = run(["/bin/bash", ctl, "install"], env, timeout=300)
    if r.rc != 0:
        raise Failed(8, "kyctl.sh install exited %s: %s" % (r.rc, r.last_error()))
    plists = [plist_facts(os.path.join(ctx.la_dir, TRACKER_LABEL + ".plist"), TRACKER_LABEL, "tracker")]
    for loop in LOOPS:
        label = "in.marsys.kalayantra." + loop
        plists.append(plist_facts(os.path.join(ctx.la_dir, label + ".plist"), label, "loop"))
    for p in plists:
        if p["hook_variables"]:
            raise Failed(8, "the plist %s carries a test-hook variable: %s" % (p["path"], ", ".join(p["hook_variables"])))
        if p["kind"] == "loop" and not p["ky_scratch"]:
            raise Failed(8, "the loop plist %s records no KY_SCRATCH" % p["path"])
    ctx.plists = plists


def step_qualify(ctx):
    py = [sys.executable, "-I", "-B"]
    qual = os.path.join(ctx.fleet_live, "kyqualify.py")
    stamp = "%s-%d" % (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()), os.getpid())
    work = os.path.join(ctx.scratch, "install", stamp)
    configs = []
    tdir = os.path.join(ctx.fleet_live, "templates")
    for name in sorted(os.listdir(tdir)) if os.path.isdir(tdir) else []:
        if re.match(r"^LAUNCH_CONFIG\..+\.json$", name):
            configs.append(os.path.join(tdir, name))
    for role in ("planner", "conductor"):
        r = run(py + [os.path.join(ctx.fleet_live, "kyloop.py"), "admin", "launch-config", role], ky_dir_env(ctx), timeout=120)
        if r.rc != 0:
            raise Failed(9, "kyloop.py admin launch-config %s exited %s: %s" % (role, r.rc, r.last_error()))
        p = os.path.join(ctx.scratch, "install", "launch-config.%s.json" % role)     # a stable path: the receipt records it
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not os.path.isfile(p) or open(p, "rb").read() != r.out.encode("utf-8"):
            write_atomic(p, r.out.encode("utf-8"))
        configs.append(p)
    if not configs:
        raise Failed(9, "no launch configuration to qualify")
    os.makedirs(os.path.join(ctx.run_dir, "QUALIFICATIONS"), exist_ok=True)
    rows = []
    for cfg in configs:
        try:
            doc = json.loads(open(cfg, "rb").read())
            role, model = doc["role"], doc["model"]
            if not SAFE_NAME.match(role) or not SAFE_NAME.match(model):
                raise ValueError("unsafe name")
        except (OSError, ValueError, KeyError, TypeError) as e:
            raise Failed(9, "launch configuration unreadable or without role/model: %s (%s)" % (cfg, type(e).__name__))
        tag = qualification_tag(cfg, doc)
        if role not in QUALIFICATION_JOB_ENV and any(n in doc.get("env_names", [])
                for n in ("KY_STREAM", "KY_LANE", "KY_CONTROLLER_ID")):
            raise Failed(9, "no conventional qualification identity for role " + role)
        receipt = os.path.join(ctx.run_dir, "QUALIFICATIONS", "%s-%s.json" % (tag, model))
        check = py + [qual, "check", receipt, "--config", cfg, "--require-context", "launchd", "--verify-evidence"]
        qualification_env = child_env(ctx)
        qualification_env.update(QUALIFICATION_JOB_ENV.get(role, {}))
        done = run(check, qualification_env, timeout=600)
        requalified = False
        if done.rc != 0:
            requalified = True
            evidence = os.path.join(work, "qualify-%s-%s" % (tag, model))
            os.makedirs(evidence, exist_ok=True)
            q = run(py + [qual, "qualify", "--config", cfg, "--context", "launchd", "--control", "--evidence-dir", evidence, "--out", receipt],
                    qualification_env, timeout=3 * 3600)
            if q.rc != 0 and not os.path.isfile(receipt):
                raise Failed(9, "qualification of %s %s did not produce a receipt (exit %s): %s" % (role, model, q.rc, q.last_error()))
            done = run(check, qualification_env, timeout=600)
        result = None
        try:
            result = json.loads(open(receipt, "rb").read()).get("result")
        except (OSError, ValueError, AttributeError):
            pass
        if done.rc != 0 or result != "PASS":
            raise Failed(9, "qualification of %s %s is not PASS (check exit %s, receipt result %r)" % (role, model, done.rc, result))
        ctx.changed["qualified:%s-%s" % (tag, model)] = requalified
        rows.append({"role": role, "model": model, "config": cfg, "config_sha256": sha_file(cfg), "receipt": receipt,
                     "receipt_sha256": sha_file(receipt), "context": "launchd", "result": "PASS",
                     "checked_with": "kyqualify.py check --require-context launchd --verify-evidence (exit 0)"})
    ctx.qualifications = rows


# ---- step 10: preflight, receipt, kyversion
def component_rows(ctx):
    rows = []
    for rel, p in sorted(ctx.fleet_files.items()):
        rows.append({"path": p, "installed_path": os.path.join(ctx.fleet_live, rel), "sha256": ctx.bound[p]})
    for rel, p in sorted(ctx.tracker_files.items()):
        rows.append({"path": p, "installed_path": os.path.join(ctx.tracker_live, "pravaha_tracker", rel), "sha256": ctx.bound[p]})
    for rel, p in sorted(ctx.bin_files.items()):
        rows.append({"path": p, "installed_path": os.path.join(ctx.bin_dir, rel), "sha256": ctx.bound[p]})
    for r in rows:
        if sha_file(r["installed_path"]) != r["sha256"]:
            raise Failed(10, "the installed file does not hold the reviewed bytes: %s" % r["installed_path"])
    return sorted(rows, key=lambda r: r["path"])


def build_receipt(ctx):
    fleet, tracker = fleet_entries(ctx), tracker_entries(ctx)
    bins = [{"name": n, "path": os.path.join(ctx.bin_dir, n), "sha256": sha_file(os.path.join(ctx.bin_dir, n)),
             "mode": "%04o" % stat.S_IMODE(os.stat(os.path.join(ctx.bin_dir, n)).st_mode)} for n in sorted(ctx.bin_files)]
    trees = {"fleet_live": {"path": ctx.fleet_live, "files": len(fleet), "tree_sha256": tree_digest(fleet)},
             "tracker_live": {"path": ctx.tracker_live, "files": len(tracker), "tree_sha256": tree_digest(tracker)},
             "bin": {"path": ctx.bin_dir, "files": bins},
             "bundle": [{"role": r["role"], "path": r["path"], "installed_path": os.path.join(ctx.fleet_live, "bundle", r["path"]),
                         "sha256": r["sha256"]} for r in ctx.entry_rows],
             "versions_bootstrap": {"path": ctx.versions_path, "sha256": sha_file(ctx.versions_path)}}
    for r in trees["bundle"]:
        if sha_file(r["installed_path"]) != r["sha256"]:
            raise Failed(10, "the installed entrypoint does not hold the reviewed bytes: %s" % r["installed_path"])
    receipt = {"schema": RECEIPT_SCHEMA, "mode": "bootstrap",
               "source": {"path": ctx.source, "components_commit": ctx.components_commit, "approved_source_commit": ctx.approved,
                          "merge_commit": None},
               "manifest": {"path": ctx.versions_path, "source_path": ctx.manifest_path, "sha256": ctx.manifest_file_sha,
                            "manifest_sha256": ctx.m["manifest_sha256"]},
               "components": component_rows(ctx), "trees": trees, "reviews": ctx.review_info,
               "qualifications": ctx.qualifications, "claude_bin": ctx.claude_info,
               "tracker_revision": {"package_sha256": ctx.tracker_info["package_sha256"], "pid": ctx.tracker_info["pid"],
                                    "process_start": ctx.tracker_info["process_start"], "url": ctx.tracker_info["url"],
                                    "health": ctx.tracker_info["health"]},
               "plists": ctx.plists, "old_supervisors": ctx.old_supervisors, "campaign_checkout": ctx.campaign_info,
               "model_actions": ctx.model_actions, "legacy": ctx.legacy}
    need = [("source.components_commit", receipt["source"]["components_commit"]), ("manifest.sha256", receipt["manifest"]["sha256"]),
            ("claude_bin.sha256", receipt["claude_bin"]["sha256"]), ("claude_bin.version", receipt["claude_bin"]["version"]),
            ("tracker_revision.package_sha256", receipt["tracker_revision"]["package_sha256"]),
            ("tracker_revision.pid", receipt["tracker_revision"]["pid"]),
            ("tracker_revision.process_start", receipt["tracker_revision"]["process_start"]),
            ("campaign_checkout.head", receipt["campaign_checkout"]["head"]),
            ("campaign_checkout.upstream", receipt["campaign_checkout"]["upstream"]), ("components", receipt["components"]),
            ("tracker_revision.health.server_started_at", receipt["tracker_revision"]["health"].get("server_started_at")),
            ("reviews", receipt["reviews"]), ("old_supervisors", receipt["old_supervisors"]), ("legacy", receipt["legacy"]),
            ("qualifications", receipt["qualifications"]), ("plists", receipt["plists"]),
            ("model_actions.entries", receipt["model_actions"]["entries"])]
    unknown = [name for name, value in need if value in (None, "", [], {})]
    if unknown:
        raise Failed(10, "an unknown value in the receipt (%s): no receipt is written" % ", ".join(unknown))
    return receipt


def write_receipt(ctx, receipt):
    body = json.dumps(receipt, indent=1, sort_keys=True, ensure_ascii=False)
    try:
        with open(ctx.receipt_path, "rb") as f:
            existing = json.loads(f.read())
        stamp = existing.pop("installed_at", None)
        if stamp and json.dumps(existing, indent=1, sort_keys=True, ensure_ascii=False) == body:
            receipt["installed_at"] = stamp
            data = (json.dumps(receipt, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode()
            if open(ctx.receipt_path, "rb").read() == data:
                ctx.changed["receipt"] = False
                return
    except (OSError, ValueError, AttributeError):
        pass
    receipt["installed_at"] = utc_now()
    write_atomic(ctx.receipt_path, (json.dumps(receipt, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode())
    ctx.changed["receipt"] = True


def step_receipt(ctx):
    r = run(["/bin/bash", os.path.join(ctx.fleet_live, "preflight.sh"), "launch"], ky_dir_env(ctx), timeout=3600)
    if r.rc != 0:
        raise Failed(10, "preflight.sh launch exited %s: %s" % (r.rc, r.last_error()))
    receipt = build_receipt(ctx)
    write_receipt(ctx, receipt)
    v = run(["/bin/bash", os.path.join(ctx.fleet_live, "kyversion.sh"), "--bootstrap"],
            child_env(ctx, KY_ROOT=ctx.root, KY_RUN=ctx.run_dir, KY_FLEET=ctx.fleet_live, KY_SOURCE_REPO=ctx.campaign), timeout=600)
    if v.rc != 0:                                    # KV3-B-KYVERSION: exit 0 = pass; nothing is read from its output
        left = refuse_receipt(ctx)
        raise Failed(10, "kyversion.sh --bootstrap refused the installation (exit %s): %s%s" % (v.rc, v.last_error(), left))
    if os.path.lexists(ctx.receipt_path + ".superseded"):
        os.unlink(ctx.receipt_path + ".superseded")
    return receipt


def refuse_receipt(ctx):
    """Rename the receipt `.refused`. → "" or, when the rename failed, the words that say the file is still there."""
    try:
        os.replace(ctx.receipt_path, ctx.receipt_path + ".refused")
    except OSError as e:
        if os.path.lexists(ctx.receipt_path):
            return "; THE RECEIPT COULD NOT BE RENAMED AND IS STILL AT %s (%s): it grants nothing" % (ctx.receipt_path, type(e).__name__)
    return ""


# ---- the action record
def action_finish(ctx, verb, result):
    code = ("import json, sys\nsys.path.insert(0, sys.argv[1])\nimport kyaction\n"
            "getattr(kyaction, sys.argv[2])(sys.argv[3], sys.argv[4], json.loads(sys.argv[5]))\n")
    r = run([sys.executable, "-I", "-B", "-c", code, ctx.fleet_src, verb, ctx.run_dir, ctx.action, json.dumps(result)],
            child_env(ctx), timeout=60)
    return r.rc == 0, r.last_error()


def rollback(ctx):
    problems = []
    for undo in reversed(ctx.undo):
        try:
            undo()
        except Exception as e:                    # noqa: BLE001 — keep restoring what can be restored
            problems.append(flat(e, 400))
    ctx.undo = []
    for d in (ctx.fleet_live, ctx.tracker_live):
        if os.path.lexists(d + ".new"):
            shutil.rmtree(d + ".new", ignore_errors=True)
    return problems


STEPS = ((0, step_stop), (1, step_fleet), (2, step_tracker_tree), (3, step_bin), (4, step_versions), (5, step_campaign),
         (6, step_tracker), (6, step_publish), (7, step_legacy), (8, step_loops), (9, step_qualify), (10, step_receipt))


def take_lock(ctx):
    """The last thing that may still refuse (exit 1): it precedes the STOP files, the first write of an installation."""
    os.makedirs(ctx.run_dir, exist_ok=True)
    ctx.lock_fd = os.open(ctx.run_dir, os.O_RDONLY)
    try:
        fcntl.flock(ctx.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        refuse("another installation holds the lock on %s" % ctx.run_dir, "E_LOCK")


def write_phase(ctx):
    """Writing has begun: nothing in here ends as a refusal. A step that refuses has failed (exit 3, its step number)."""
    result = None
    for number, step in STEPS:
        ctx.step = number
        try:
            result = step(ctx)
        except Refused as e:
            raise Failed(number, str(e))
    return result


def drop_receipt(ctx):
    """Exit 3 leaves no receipt. → None when the active path was looked at and holds nothing, else why something is there."""
    why = None
    try:
        supersede_receipt(ctx)
    except OSError as e:
        why = type(e).__name__
    if os.path.lexists(ctx.receipt_path):
        return why or "it is still there"
    return None


def report_failure(ctx, step, message):
    """Exit 3: restore what may be restored, say what was observed, fail the action. Never a receipt — not this run's and
    not an earlier run's: the receipt permits activation, its keys are "measured in this run", and this run failed."""
    problems = []
    if not ctx.committed:
        problems = rollback(ctx)
    left = drop_receipt(ctx)                      # after the rollback, for every failure, whatever changed or did not
    sys.stderr.write("install.sh: FAILED step %d: %s\n" % (step, flat(message, 600)))
    if ctx.committed and ctx.restart_confirmed:
        sys.stderr.write("install.sh: the tracker was restarted on the new trees: nothing was undone; "
                         "a rerun resumes (published actions are skipped)\n")
    elif ctx.committed:
        sys.stderr.write("install.sh: the tracker restart was begun and did not complete: whether a tracker is running, and on "
                         "which trees, is unknown; nothing was undone; a rerun resumes (published actions are skipped)\n")
    else:
        if problems:
            sys.stderr.write("install.sh: trees NOT restored: %s\n" % "; ".join(problems))
        else:
            sys.stderr.write("install.sh: trees restored\n")
        if ctx.campaign_created:
            sys.stderr.write("install.sh: the campaign checkout created at step 5 was left in place: %s (branch %s)\n"
                             % (ctx.campaign, CAMPAIGN_BRANCH))
    if left:
        sys.stderr.write("install.sh: A RECEIPT COULD NOT BE MOVED ASIDE AND IS STILL AT %s (%s): it grants nothing\n"
                         % (ctx.receipt_path, left))
    else:
        sys.stderr.write("install.sh: there is no receipt%s\n" % (
            " (the one found there was moved aside: %s.superseded)" % ctx.receipt_path if ctx.superseded else ""))
    if ctx.action:
        ok, why = action_finish(ctx, "fail", {"step": step, "error": flat(message, 400), "exit": 3,
                                              "trees_restored": not ctx.committed and not problems,
                                              "receipt_present": left is not None,
                                              "campaign_checkout_left": ctx.campaign if ctx.campaign_created else None})
        if not ok:
            sys.stderr.write("install.sh: the action record could not be marked FAILED: %s\n" % why)
    return 3


def main(argv):
    try:
        opts = parse_args(argv)
        env = dict(os.environ)
        ctx = decide_environment(opts, env)
        verify(ctx)
        take_lock(ctx)
    except Usage:
        sys.stderr.write(USAGE + "\n")
        return 64
    except Refused as e:
        sys.stderr.write("install.sh: REFUSED %s: %s\n" % (e.code, e))
        return 1
    try:
        write_phase(ctx)
    except BaseException as e:                    # noqa: BLE001 — anything after writing began is a failed installation
        if isinstance(e, KeyboardInterrupt):
            raise
        step = e.step if isinstance(e, Failed) else ctx.step
        message = str(e) if isinstance(e, (Failed, Refused)) else "%s: %s" % (type(e).__name__, e)
        return report_failure(ctx, step, message)
    summary = {"installed": True, "receipt": ctx.receipt_path, "receipt_sha256": sha_file(ctx.receipt_path),
               "changed": ctx.changed, "model_actions": ctx.model_report, "processes_examined": ctx.processes_examined,
               "campaign_registrations": ctx.registrations}
    if ctx.action:
        ok, why = action_finish(ctx, "complete", {"receipt": ctx.receipt_path, "receipt_sha256": summary["receipt_sha256"],
                                                  "manifest_sha256": ctx.m["manifest_sha256"],
                                                  "components_commit": ctx.components_commit})
        if not ok:                                # exit 3 means no receipt: an installation nobody could record has none
            left = refuse_receipt(ctx)
            sys.stderr.write("install.sh: FAILED step 10: installed, but the action record could not be completed: %s%s\n"
                             % (why, left or "; the receipt was renamed .refused"))
            return 3
    print(json.dumps(summary, sort_keys=True))
    return 0


sys.exit(main(sys.argv[1:]))
KYINSTALL_PY
