#!/usr/bin/env python3
"""kyloop.py — deterministic loop controller for KĀLA-YANTRA v3 (relaunch plan v2.7 §4a.1–3, §4a.6, §7, §10, §11,
§13).

    kyloop.py planner|conductor|veto            the long-running controller launchd keeps alive
    kyloop.py admin enable|disable <loop> --reason TEXT [--by WHO]     durable admission switch
    kyloop.py admin show <loop>                 print $KY_RUN/loops/<loop>.json (or {"present": false})
    kyloop.py admin child <loop>                one line `<state> <pid|-> <run id|->` for the child that loop's
                                                controller recorded: none|pending|alive|survivors|gone|unknown
    kyloop.py admin expected-qualification <role>   the launch configuration AND context a qualification
                                                receipt must bind (planner, conductor)
    kyloop.py admin launch-config <role>        the ky.launch_config/1 kyqualify.py qualifies that role with

launchd supervises THIS script, never an unconditional chain of model runs. The controller

  * is the sole holder of the role lock ($KY_RUN/locks/<role>; taken, given its child and released through
    $KY_FLEET/kylock.sh when that is installed — Controller.kylock() is the one place it is run and reads its
    exit codes one by one: 75 live holder · 76 cockpit · 77 unknown owner · 74 released-not-proven, lock kept ·
    70 identity refused; nothing but 0 is success) and
    the sole writer of $KY_RUN/<ROLE>_STATE.json and JOURNAL_<ROLE>.md while it runs. ONE liveness rule
    (process_matches: True alive · False POSITIVELY gone · None unknown) governs every lock here: a lock is
    created atomically WITH its owner record (a private directory renamed onto the lock path, which fails when
    the path exists at all), is taken over ONLY when its recorded pid + process-start identity is positively
    gone, and the takeover is verified after the rename (the buried lock must still be the one that was
    judged; otherwise it is put back). A missing or unreadable owner record, a null or malformed pid and an
    unanswerable `ps` are unknown: never taken over, never removed by age, raised as one attention item. A
    live cockpit holder is respected (recorded as waiting state `role_held_by_cockpit`, exit 0);
  * honours durable state before EVERY launch, in this order: STOP_<role>, the `enabled` switch in
    $KY_RUN/loops/<role>.json (absent = not enabled: a loaded plist never authorises a run), the owner's
    queued commands, completion, $KY_ROOT/HOLD, an owner pause, the circuit breaker and quota backoff — all
    of which survive controller restarts;
  * applies its role's QUEUED owner commands, in filename order and exactly once, as the fenced role owner
    (kycommands.apply) at the top of every iteration and again immediately before a launch; the conductor
    also applies the `campaign` role's pause / resume (holding locks/campaign only for the application).
    While an owner pause is in force — applied, queued and not yet applied, or unknowable — no model job is
    launched by any role;
  * gives an answered owner-wait an end, on both sides (R15). An awaiting item with the OWNER's decision beside
    it no longer blocks its item or its loop — and the owner's decision is a ky.owner_decision/1 record naming
    that item which the queue's own `decide` command stands behind (for that item, with that answer, QUEUED or
    APPLIED); a record a surrogate, a job or a hand wrote is none, so nothing but an owner `decide` releases a
    wait where it lies, a hard stop least of all. The controller that applies the `decide` writes the decision
    first — with what was asked — and then closes the item (moved to awaiting/done/, never deleted), under the
    command's one action record; for the item it raised itself for a job action nobody could observe it also
    carries the chosen option out (the job's record settled DONE or FAILED, on the owner's word). A controller
    that dies in between is completed at the next look, without a second record. The role a wait holds up
    answers for it, whoever raised it. The answer is a changed dependency that no run authored;
  * waits itself (hold, pause, backoff, "no eligible work", inbox polling, messages another actor holds
    locked — `items_locked`, never an immediate second look) — and says so, once, when a wait needs a person
    (R16): a command queue that cannot be read (a pause no `resume` ends), a queued command another actor has
    kept from being settled for half an hour, an answered owner-wait that cannot be closed — and launches ONE
    bounded
    `claude -p` child only for an eligible work item (planner: a pending Wave B step) or an actionable,
    deduplicated, handled-state-checked batch of inbox messages (conductor);
  * wraps every side effect of its own in an action record (kyaction: INTENDED before, the observed result
    after) — each child launch, each notification and the conductor's dispatcher start — and reconciles every
    unfinished action it owns at start-up and before any relaunch — what it cannot observe is unknown: one
    awaiting file, no retry;
  * reconciles what its CHILD recorded: a job writes action records only through `kyaction.py
    begin|complete|fail`, as actor {role, holder_kind: "job", controller_id, run_id}, in the id namespace
    `JOB-<run_id>-<slug>`. After the child exits the controller settles that run's unfinished records by
    observation (kind `git_push`: `git ls-remote` equality); a kind it has no observer for is unknown — ONE
    awaiting item naming the record, no retry, and the loop goes on with other items. A malformed job-authored
    file is moved to $KY_RUN/actions/quarantine/ with an awaiting item and never stops the loop;
  * gives each child an immutable state snapshot and a fenced job identity (job.json); the child returns
    checkpoint requests, which the controller validates (fence, assignment, evidence inside the role worktree /
    run scratch / run directory and its hash, the per-item sub-step cap, or the observed ack) and persists. A
    child's own write to the role-state file is detected, preserved for forensics and undone from the
    controller's own in-memory copy; when the child also removed or altered its snapshot the run is REFUSED
    (nothing it returned is accepted, it counts as no progress, one attention item);
  * counts progress only as accepted checkpoint requests or a changed external dependency THE RUN DID NOT
    AUTHOR — never a heartbeat, timestamp, journal append or an owner-wait the job itself raised; three
    consecutive runs without progress open the breaker (awaiting file + STOP) — the launch decision reads the
    count itself — and a restart is refused until recorded evidence has changed;
  * reconciles a surviving child of a dead controller (by PID + PGID + process-start identity) before any
    replacement — a job is gone only when its leader is positively gone AND its process group is empty; a
    child recorded as `pending` (written BEFORE it is started) or never identified is never gone — forwards
    TERM/INT to the child's process group, and while a child runs looks at STOP_<role> and at the queue for
    `loops stop` / `handoff` every 15 s: on either it ends the child's group, records it and stops;
  * never ends in a traceback launchd would respawn: every unexpected exception becomes one awaiting item,
    the STOP file, `enabled: false` and exit 0.

The conductor takes its approved manifest digest from the terminal link of the validated activation chain
($KY_RUN/ACTIVATION_RECORD.json when present, then ACTIVATION_RECORD.<n>.json exactly as kyveto.py writes them;
numbered links alone when the un-numbered record is absent); a broken, forked or missing chain refuses, and
nothing ever falls back to the installed manifest.

The `veto` role (plan §4a.2/§4a.3) launches no model at all: it holds the `veto` lock and calls kyveto.py's
`tick` as that lock's holder, waiting in between until the earliest pending veto deadline, a new command for
the veto role, or its poll period. Before each tick it applies the veto role's own queued commands itself —
`status`, `loops stop|status veto`, `decide` — and leaves `veto <decision-id>` to the handler. It is admitted exactly like the model loops — an installation receipt of
mode bootstrap or final AND a passing kyversion.sh in the matching mode, at start-up and whenever the receipt
changes — and passes the authorised bundle to every tick explicitly: the terminal activation link's source
commit and its manifest's entrypoints digest when a chain exists, otherwise PLANNER_STATE.json
`authorised_source`; when neither can be read every decision is held and one attention item is raised. Each
tick's outcome is recorded in $KY_RUN/loops/veto.json.

TEST HOOKS (the only two; both are environment variables and neither belongs in an installed plist):
KY_LOOP_SLEEP_SCALE (0 < scale <= 1) compresses the controller's own waits, and KY_LOOP_TEST_CONTEXT replaces the
context detector — the latter ONLY while the scale override is active, so at the production scale nothing can
tell a controller that it runs under launchd. Any use of either is written into every run record and into
$KY_RUN/loops/<role>.json (`test_hooks`), and a controller that PROVABLY runs under launchd refuses to launch
while either is in use.

Exit codes: 0 clean stop, legitimate "nothing to run" and EVERY refusal (launchd KeepAlive{SuccessfulExit:false}
does not respawn) — a refused environment included (N4-01): a credential variable NAME in the environment, or a
KY_LOOP_SLEEP_SCALE that is not a number in (0, 1], is one awaiting item, the STOP file and `enabled: false`
like any other refused precondition (raised by the lock holder; names only are printed, and the variable is
dropped from this process's environment before any helper is started). Without a run directory nothing can be
recorded: one notification is attempted and nothing is created. 64 usage; 78 the one-shot admin commands only
(a bad KY_LOOP_SLEEP_SCALE); 128+signal when terminated without a STOP file (launchd respawns; durable state
still governs).

Interfaces this file defines or assumes are listed in the B-0c report (checkpoint requests, qualification
receipts, activation chain, handled records, owner-decision files, kylock.sh / kygate.sh call forms).
"""
from __future__ import annotations

import calendar
import contextlib
import errno
import fcntl
import hashlib
import importlib
import json
import os
import pwd
import re
import secrets
import signal
import subprocess
import sys
import time
from pathlib import Path

# System directories shared by controller plists and the installer's preflight proof.
# Model-child PATHs below are separately qualified and deliberately retain their existing value.
SYSTEM_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

ROLES = ("planner", "conductor")                # the roles that launch model jobs (kyqualify.py pins this tuple)
CONTROLLER_ROLES = ROLES + ("veto",)            # every role this file is the controller of
SWITCH_LOOPS = ("dispatcher",) + CONTROLLER_ROLES
SIBLINGS = ("kyaction", "kycommands", "kyveto")  # read-only modules beside this file, imported on first use
HARNESS = "kyqualify"                           # optional sibling: when installed, ITS check_receipt judges a receipt
LABEL_PREFIX = "in.marsys.kalayantra."          # + <role>: the launchd label of a loop (kyctl.sh label_of)
TEST_CONTEXT_ENV = "KY_LOOP_TEST_CONTEXT"       # TEST-ONLY, see Controller.context()
TEST_CONTEXT_PREFIX = "test-hook:"              # what an injected context is reported as: never a proven context
MIN_CLAUDE = (2, 1, 296)
BACKOFF_MINUTES = (5, 10, 20, 30)
NO_PROGRESS_LIMIT = 3
HOLD_POLL_S = 30.0          # the global HOLD and an owner pause are polled; other waits are event- or deadline-bound
WAIT_POLL_S = 15.0          # "no eligible work" / inbox polling period; also how often a running child's
                            # controller looks at STOP_<role> and at the queue for `loops stop` / `handoff`
COMMAND_POLL_S = 1.0        # how often a waiting controller looks for a new command / a still-pending one
COMMANDS_OVERDUE_S = 1800.0 # a queued command that cannot be settled for this long is raised as ONE attention item
VETO_POLL_S = 30.0          # the veto controller's tick period when no deadline or command comes sooner
VETO_LOCK_WAIT_S = 150.0    # how long the veto controller waits for another handler's tick to release the lock
KYLOCK_TIMEOUT_S = 120.0    # kylock.sh acquire / child: it answers at once, or it is not an answer
KYLOCK_RELEASE_TIMEOUT_S = 960.0    # kylock.sh release runs the KU-02 database step (900 s) before it answers
# kylock.sh's exit codes (packet KV3-B-KYLOCK, "Contract"); anything else — and no answer — reads "error"
KYLOCK_EXITS = {0: "ok", 64: "usage", 70: "bad_identity", 73: "not_owner", 74: "release_unproven", 75: "live",
                76: "cockpit", 77: "unknown"}
KYLOCK_REFUSALS = {"live": "live", "cockpit": "cockpit", "unknown": "unknown", "bad_identity": "identity_refused"}
TERM_GRACE_S = 10.0         # TERM → KILL → record must fit inside launchd's default 20 s exit timeout
CHILD_POLL_S = 0.2
EVENT_SOURCE_FAILURE_LIMIT = 5
BATCH_MAX = 20
SUBSTEP_CAP = 20            # accepted sub-steps per item; beyond it the item needs changed recorded evidence
STATE_MUTEX_WAIT_S = 10.0   # how long a loop-state update waits for another writer's flock
QUALIFIED_TOOLS = ("Read", "Write", "Edit", "Bash")     # what a loop role's qualification must cover as intended
RECEIPT_SCHEMA = "ky.qualification/1"
JOB_HOLDER = "job"          # holder_kind of an action record a child job wrote through `kyaction.py begin`
GIT_REMOTE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")           # a configured remote NAME, never a URL
GIT_REF_RE = re.compile(r"^refs/[A-Za-z0-9][A-Za-z0-9._/-]{0,199}\Z")
ENTRYPOINT_ROLES = ("plan", "cockpit_prompt", "owner_decisions", "strategy", "surrogate_agent")
MANIFEST_FILES = ("VERSIONS.json", "VERSIONS.bootstrap.json")              # where an installed manifest lives
PLANNER_STEPS = (("B-3", ()), ("B-4", ()), ("B-5", ("B-3", "B-4")))      # plan §14; B-5 binds B-3 and B-4
PROMPTS = {"planner": "PLANNER_LOOP_v2_4.md", "conductor": "CONDUCTOR_LOOP_v2_4.md"}
RECEIPT_MODES = {"planner": ("bootstrap", "final"), "conductor": ("final",), "veto": ("bootstrap", "final")}
KYVERSION_ARGS = {"bootstrap": ["--bootstrap"], "final": []}       # the veto loop: the mode its receipt names
DEFAULTS = {
    "planner": {"worktree": "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan",
                "model": "claude-opus-5-5", "effort": "xhigh", "max_turns": 300,
                "permission_mode": "bypassPermissions", "deadline_seconds": 14400},
    "conductor": {"worktree": "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign",
                  "model": "claude-opus-5-5", "effort": "high", "max_turns": 150,
                  "permission_mode": "bypassPermissions", "deadline_seconds": 7200},
}
CONFIG_KEYS = ("worktree", "model", "effort", "max_turns", "permission_mode", "mcp_config", "deadline_seconds",
               "substep_cap")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
PERMISSION_MODES = ("default", "acceptEdits", "plan", "bypassPermissions")
CHILD_ENV_NAMES = ("HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_FLEET",
                   "KY_SCRATCH", "JOB_SCRATCH", "KY_ROLE", "KY_RUN_ID")
CREDENTIAL_EXACT = ("DATABASE_URL", "PGPASSWORD", "ANTHROPIC_API_KEY")
RATE_LIMIT_REFUSING = ("rejected", "blocked", "limited", "exceeded")       # rate_limit_info.status: a refusal
RATE_LIMIT_ALLOWED = ("allowed",)                                           # … positively not one
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
HEX_COMMIT = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
ACTIVATION_NAME = re.compile(r"^ACTIVATION_RECORD(?:\.([1-9][0-9]{0,5}))?\.json\Z")
OWNER_DECISION_SUFFIX = ".owner_decision.json"
OWNER_DECISION_SCHEMA = "ky.owner_decision/1"   # the owner's answer beside an awaiting item (record_owner_decision)
AWAITING_DONE = "done"      # $KY_RUN/awaiting/done/: where a closed owner-wait lies — never read as an open one
WAIT_CLOSE_KIND = "awaiting_close:veto_executed"    # this controller's record AWCLOSE-<awaiting id> (R18)
WAIT_CLOSE_PREFIX = "AWCLOSE-"
VETO_EXECUTE_KIND = "veto_decision_execute:"        # kind of the veto handler's own `<SD id>.execute` record
JOB_ACTION_SLUG = "job-action-"                 # + the record id: the item raised for a job action nobody observed
JOB_ACTION_OPTIONS = ("happened", "did-not-happen")     # … and the two options that item offers the owner
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\[\]-]{0,79}$")
QUOTA_TEXT = re.compile(
    r"usage limit reached|you(?:'|’)?ve hit your (?:usage |session |weekly )?limit|limit will reset|"
    r"rate[ _-]?limit(?:ed| exceeded|_error)|too many requests|out of extra usage", re.I)
LSTART_FMT = "%a %b %d %H:%M:%S %Y"


class Refusal(Exception):
    """A launch precondition failed: one awaiting file, STOP, disabled, exit 0 — never a spin."""

    def __init__(self, reasons):
        super().__init__("; ".join(reasons))
        self.reasons = list(reasons)


class Fault(Refusal):
    """An UNEXPECTED exception inside the controller. It takes the very path of a refused precondition — one
    awaiting item, the STOP file, `enabled: false`, exit 0 — so that launchd never respawns a traceback."""

    def __init__(self, where, exc):
        super().__init__(["controller_fault: %s raised %s: %s" % (where, type(exc).__name__, flat(exc, 200))])
        self.where = where


class LoopStateUnreadable(Refusal):
    """$KY_RUN/loops/<loop>.json exists but cannot be read as an object. It is NEVER rewritten from empty (that
    would lose the breaker state and the no-progress count): the update is refused and attention raised."""

    def __init__(self, path, why):
        super().__init__(["loop_state_unreadable: %s (%s) — never rewritten from empty; repair or remove it by hand"
                          % (path, why)])
        self.path = str(path)


class Interrupted(Exception):
    pass


@contextlib.contextmanager
def guarded(where):
    """Turn any unexpected exception of the enclosed controller phase into a Fault naming that phase."""
    try:
        yield
    except (Refusal, Interrupted):
        raise
    except Exception as e:
        raise Fault(where, e) from e


# ───────────────────────── small deterministic helpers ─────────────────────────

def utc(fmt="%Y-%m-%dT%H:%M:%SZ", t=None):
    return time.strftime(fmt, time.gmtime(t))


def parse_utc(text):
    try:
        return calendar.timegm(time.strptime(text, "%Y-%m-%dT%H:%M:%SZ"))
    except (TypeError, ValueError):
        return None


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    """sha256 hex of a file, or None when it cannot be read. TOTAL: a path that is not a path (a number would be
    read as a file descriptor), one holding a NUL byte (ValueError) and every OSError are all "cannot be read"."""
    if not isinstance(path, (str, os.PathLike)):
        return None
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, ValueError, RecursionError):
        return None


def read_json(path):
    """(object, None) or (None, reason). TOTAL — never raises: a missing file, an unreadable one, text that is
    not JSON, a NUL in the path (ValueError) and JSON nested too deeply to parse (RecursionError) are reasons."""
    if not isinstance(path, (str, os.PathLike)):
        return None, "unreadable: not a path"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, "missing"
    except (OSError, ValueError, RecursionError) as e:
        return None, "unreadable: %s" % type(e).__name__


def as_int(value, default=0):
    """A stored counter as an int; anything that is not a real integer is `default` (never a crash)."""
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def write_atomic(path, data, mode=None):
    path = Path(path)
    tmp = path.with_name(".%s.tmp.%d" % (path.name, os.getpid()))
    with open(tmp, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())
    if mode is not None:
        os.chmod(tmp, mode)
    os.replace(tmp, path)


def write_json(path, obj, mode=None):
    write_atomic(path, json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n", mode)


def flat(text, limit=300):
    return " ".join(str(text if text is not None else "").split())[:limit]


def credential_names(env):
    return sorted(n for n in env if n in CREDENTIAL_EXACT or n.endswith("_DATABASE_URL"))


def sleep_scale():
    """(scale, None) — or (1.0, why) when KY_LOOP_SLEEP_SCALE is not a number with 0 < scale <= 1. Nothing here
    ends the process: the caller refuses in its own shape (N4-01 — a controller's refusal is one awaiting item and
    a stop, never an exit status launchd answers with a respawn every ten seconds)."""
    raw = os.environ.get("KY_LOOP_SLEEP_SCALE", "1")
    try:
        v = float(raw)
    except ValueError:
        v = -1.0
    if not 0 < v <= 1:
        return 1.0, "bad_sleep_scale: KY_LOOP_SLEEP_SCALE must be a number with 0 < scale <= 1 (got %s)" % flat(repr(raw), 40)
    return v, None


def ps_probe(pid):
    """("alive", stat, lstart) · ("gone",) when ps positively reports no such process · None when the pid is not a
    real positive integer, ps could not be asked, or its answer cannot be read. Unknown is never "gone" (the
    bootstrap supervisor's rule, kyboot.py). `ps -o lstart=` is the pinned start identity."""
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return None
    try:
        r = subprocess.run(["/bin/ps", "-o", "stat=,lstart=", "-p", str(pid)], capture_output=True, text=True,
                           env={"LC_ALL": "C", "PATH": "/bin:/usr/bin"}, timeout=10, stdin=subprocess.DEVNULL)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    if r.returncode == 1 and not r.stdout.strip() and not r.stderr.strip():
        return ("gone",)
    parts = r.stdout.strip().split(None, 1)
    if r.returncode != 0 or len(parts) < 2:
        return None
    return "alive", parts[0], parts[1].strip()  # lstart exactly as `ps -o lstart=` prints it


def ps_identity(pid):
    """(stat, lstart) of a live process, or None when it is gone OR could not be observed. Only for reading an
    identity; whether a process is gone is decided by process_matches / ps_probe, which keep the two apart."""
    probe = ps_probe(pid)
    return (probe[1], probe[2]) if probe and probe[0] == "alive" else None


def process_matches(pid, start):
    """True: alive with this start identity. False: POSITIVELY gone — ps reports no such process, a zombie, or
    another process under a reused pid (both start identities readable and different). None: it cannot be told
    — a pid that is not a real positive integer, an unanswerable ps, or a recorded identity that cannot be
    compared. Never kill, never steal, never call it finished on None."""
    probe = ps_probe(pid)
    if probe is None:
        return None
    if probe[0] == "gone" or probe[1].startswith("Z"):
        return False
    if not isinstance(start, str) or not start.strip():
        return None
    a, b = " ".join(start.split()), " ".join(probe[2].split())
    if a == b:
        return True
    try:
        return time.strptime(a, LSTART_FMT) == time.strptime(b, LSTART_FMT)
    except ValueError:
        return None


def proven_context(label, ppid, xpc_service_name):
    """"launchd" only when it is PROVEN the way kyqualify.py's launchd-inner proves it: the parent is pid 1 AND
    XPC_SERVICE_NAME is exactly this loop's own label. Anything else — including anything unknown — is "shell"."""
    return "launchd" if type(ppid) is int and ppid == 1 and xpc_service_name == label else "shell"


def group_gone(pgid):
    """True: no process is left in that process group (killpg(pgid, 0) raises ProcessLookupError). False: at least
    one member is still there. None: it cannot be told — not a real pgid, or a group that cannot be signalled
    (which is also what a group holding nothing but a not-yet-reaped zombie answers: unknown until it is reaped)."""
    if isinstance(pgid, bool) or not isinstance(pgid, int) or pgid <= 1:
        return None
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return True
    except OSError:
        return None
    return False


def job_state(pid, pgid, start):
    """What became of a job this role started as its own process-group leader (pgid == pid):
      "live"       its leader runs, with the recorded start identity;
      "survivors"  the leader is positively gone but its process group still has members;
      "gone"       the leader is positively gone AND the group is empty — the ONLY state a job is finished in;
      "unknown"    anything that cannot be told: no recorded pid (a child recorded as pending), an identity that
                   cannot be compared, an unanswerable ps or killpg.
    A leader pid that now belongs to ANOTHER process (start identities differ) proves its own group gone: a pid
    is never reused while a process group of that id exists, so a group of that id — if there is one — is
    someone else's and is never probed or signalled. "survivors" is reported only for a group the job led
    itself (pgid == pid); a recorded group that is not the leader's own is either provably empty or unknown."""
    match = process_matches(pid, start)
    if match is True:
        return "live"
    if match is None:
        return "unknown"
    probe = ps_probe(pid)
    if probe is None:
        return "unknown"
    if pgid == pid:
        if probe[0] == "alive" and not probe[1].startswith("Z"):
            return "gone"                       # the pid was reused: the recorded job and its group are gone
        empty = group_gone(pgid)
        return "gone" if empty is True else "survivors" if empty is False else "unknown"
    return "gone" if group_gone(pgid) is True else "unknown"


# ───────────────────────── locks: atomic with their owner, taken over only when positively gone ─────────────────────────

OWNER_IDENTITY = ("session_or_run_id", "pid", "process_start")     # what makes two owner records the same owner
_LIBC = []


def _renamex():
    """darwin's renamex_np (a rename that can be told to fail when the target exists), or None."""
    if not _LIBC:
        try:
            import ctypes
            fn = ctypes.CDLL(None, use_errno=True).renamex_np
            fn.argtypes, fn.restype = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint], ctypes.c_int
            _LIBC.append((fn, ctypes.get_errno))
        except (ImportError, AttributeError, OSError):
            _LIBC.append(None)
    return _LIBC[0]


def rename_exclusive(src, dst):
    """Rename the directory `src` onto `dst`, failing with FileExistsError when `dst` exists AT ALL. A plain
    rename() silently replaces an existing EMPTY directory — an ownerless lock would be taken over by accident —
    so the exclusive form is used where the platform has one; elsewhere existence is checked first and the plain
    rename still fails on any lock that has an owner record in it."""
    native = _renamex()
    if native is not None:
        fn, get_errno = native
        if fn(os.fsencode(str(src)), os.fsencode(str(dst)), 0x4) == 0:          # RENAME_EXCL
            return
        err = get_errno()
        if err in (errno.EEXIST, errno.ENOTEMPTY):
            raise FileExistsError(err, os.strerror(err), str(dst))
        if err not in (errno.ENOTSUP, errno.EINVAL, errno.ENOSYS):
            raise OSError(err, os.strerror(err), str(dst))
    if os.path.lexists(dst):
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(dst))
    try:
        os.rename(src, dst)
    except OSError as e:
        if e.errno in (errno.EEXIST, errno.ENOTEMPTY):
            raise FileExistsError(e.errno, os.strerror(e.errno), str(dst)) from None
        raise


def lock_create(path, owner):
    """Take the lock directory `path` atomically WITH its owner record: owner.json is written into a private
    directory beside the lock, and that directory is renamed onto the lock path. → True when this call created
    the lock, False when the path already exists. A lock therefore never exists without an owner; one that does
    (or whose owner cannot be read) was made by someone else in some other way — it is unknown, and never ours."""
    path = Path(path)
    tmp = path.parent / (".%s.new.%d.%s" % (path.name, os.getpid(), secrets.token_hex(4)))
    os.mkdir(tmp)
    try:
        write_json(tmp / "owner.json", owner)
        rename_exclusive(tmp, path)
        return True
    except FileExistsError:
        return False
    finally:
        if tmp.exists():                        # not renamed: nothing of it may stay behind
            with contextlib.suppress(OSError):
                for entry in tmp.iterdir():
                    entry.unlink()
                os.rmdir(tmp)


def lock_bury(path, judged):
    """Verify-after-rename removal of the lock directory `path`, whose owner record `judged` the caller holds to
    be removable (positively gone, or the caller's own). The lock is renamed to a grave beside it — atomic — and
    the grave's owner.json re-read: only when it is exactly the owner that was judged (same id, pid and process
    start) is it removed. Anything else is put back (exclusively). Serialised among takeovers by flock on
    locks/.takeover.guard (the guard kyaction.py uses).
      → "removed"   it was that lock and it is gone: the path is free
        "absent"    there was no lock at that path any more
        "changed"   the lock there is ANOTHER owner's already (seen before anything was moved): untouched
        "restored"  it became another owner's between that look and the rename: put back untouched
        "conflict"  as "restored", but the path was re-taken meanwhile: the buried lock is left in its grave for
                    a human — never deleted, never overwritten."""
    path = Path(path)

    def same(owner):
        return isinstance(owner, dict) and isinstance(judged, dict) \
            and all(owner.get(k) == judged.get(k) for k in OWNER_IDENTITY)

    guard = os.open(str(path.parent / ".takeover.guard"), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(guard, fcntl.LOCK_EX)
        if not os.path.lexists(path):
            return "absent"
        if not same(read_json(path / "owner.json")[0]):
            return "changed"
        grave = path.parent / (".%s.grave.%d.%s" % (path.name, os.getpid(), secrets.token_hex(4)))
        try:
            os.rename(path, grave)
        except FileNotFoundError:
            return "absent"
        buried, _ = read_json(grave / "owner.json")
        if same(buried):
            with contextlib.suppress(OSError):
                for entry in grave.iterdir():
                    entry.unlink()
                os.rmdir(grave)
            return "removed"
        try:
            rename_exclusive(grave, path)
        except FileExistsError:
            return "conflict"
        return "restored"
    finally:
        os.close(guard)


def update_loop_state(run_dir, loop, fn):
    """Read-modify-write $KY_RUN/loops/<loop>.json (kyctl and the controller both write). Serialised by flock on
    locks/.loopstate.<loop>.flock: the kernel drops it when its holder ends, so nothing is ever stale and nothing
    is ever removed by age. A file that exists but cannot be read as an object raises LoopStateUnreadable — it is
    never rewritten from empty."""
    path = Path(run_dir) / "loops" / (loop + ".json")
    os.makedirs(path.parent, exist_ok=True)
    os.makedirs(Path(run_dir) / "locks", exist_ok=True)
    fd = os.open(str(Path(run_dir) / "locks" / (".loopstate.%s.flock" % loop)), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        end = time.monotonic() + STATE_MUTEX_WAIT_S
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as e:
                if e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN, errno.EINTR) or time.monotonic() >= end:
                    raise RuntimeError("loop-state mutex busy or unusable: %s (%s)" % (loop, type(e).__name__))
                time.sleep(0.01)
        cur, err = read_json(path)
        if err and err != "missing":
            raise LoopStateUnreadable(path, err)
        if cur is not None and not isinstance(cur, dict):
            raise LoopStateUnreadable(path, "not an object")
        doc = fn(dict(cur) if cur else {})
        doc.setdefault("schema", "ky.loop/1")
        doc["loop"] = loop
        write_json(path, doc)
        return doc
    finally:
        os.close(fd)


def loop_state(run_dir, loop):
    """({…}, None) — {} when there is no file yet — or (None, reason) when it exists and cannot be read."""
    doc, err = read_json(Path(run_dir) / "loops" / (loop + ".json"))
    if err == "missing":
        return {}, None
    if err or not isinstance(doc, dict):
        return None, err or "not an object"
    return doc, None


def canonical(obj):
    """The byte form kymanifest.py digests (sorted keys, no padding, UTF-8)."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def manifest_entrypoints(path, manifest_digest):
    """The entrypoints digest of the manifest file `path` — only when that file IS the manifest of
    `manifest_digest`: its digest recomputed here (canonical JSON without `manifest_sha256`, as kymanifest.py
    does) equals it, it carries the five-role `entrypoints` mapping, and any `entrypoints_digest` it states
    equals the one recomputed from that mapping. → (digest, None) or (None, reason)."""
    doc, err = read_json(path)
    if err or not isinstance(doc, dict):
        return None, "manifest %s" % (err or "is not an object")
    try:
        body = canonical({k: v for k, v in doc.items() if k != "manifest_sha256"})
    except (TypeError, ValueError, RecursionError):
        return None, "manifest cannot be digested"
    if sha_bytes(body) != manifest_digest:
        return None, "not the manifest of that digest"
    entry = doc.get("entrypoints")
    if not isinstance(entry, dict) or set(entry) != set(ENTRYPOINT_ROLES) or any(
            not isinstance(e, dict) or not isinstance(e.get("path"), str) or not isinstance(e.get("git_blob"), str)
            for e in entry.values()):
        return None, "manifest carries no five-role entrypoints mapping"
    digest = sha_bytes(canonical({r: {"path": e["path"], "git_blob": e["git_blob"]} for r, e in entry.items()}))
    if "entrypoints_digest" in doc and doc["entrypoints_digest"] != digest:
        return None, "manifest states another entrypoints digest than its mapping gives"
    return digest, None


def rate_limit_reset(info):
    """resetsAt (epoch seconds) of a rate_limit_info: its own, else that of the window its rateLimitType names
    in unifiedWindows. None when neither is a positive number — never guessed from another window."""
    def number(value):
        ok = isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0
        return value if ok else None

    direct = number(info.get("resetsAt"))
    if direct is not None:
        return direct
    windows, kind = info.get("unifiedWindows"), info.get("rateLimitType")
    if isinstance(windows, dict) and isinstance(kind, str) and isinstance(windows.get(kind), dict):
        return number(windows[kind].get("resetsAt"))
    return None


def detect_quota(stdout_path, stderr_path):
    """Was this run refused by the subscription / rate limiter? → {"refusal", "source", "status",
    "rate_limit_type", "resets_at", "unrecognised"}.

    The stream-json event observed on this host is {"type": "rate_limit_event", "rate_limit_info": {"status":
    "allowed", "rateLimitType": "five_hour", "overageStatus": …, "unifiedWindows": {"five_hour": {"utilization",
    "resetsAt"}, …}}}. Only `status` decides: a value in RATE_LIMIT_REFUSING is a structured refusal (with the
    reset time of its window when the event carries one); "allowed" is not; ANY other value is recorded verbatim
    in `unrecognised` and is not a refusal — `overageStatus` never counts. Also a refusal: the FINAL result
    event with is_error true whose text matches the subscription-refusal patterns, an `error` field of
    rate_limit / rate_limit_error, refusal text on stderr or in a non-JSON terminal line. Model prose inside
    assistant messages never counts."""
    out = {"refusal": False, "source": None, "status": None, "rate_limit_type": None, "resets_at": None,
           "unrecognised": []}
    last_result = None

    def hit(source):
        out["refusal"] = True
        out["source"] = out["source"] or source

    try:
        with open(stdout_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                text = line.strip()
                if not text:
                    continue
                try:
                    obj = json.loads(text)
                except ValueError:
                    if QUOTA_TEXT.search(text):
                        hit("terminal_line")
                    continue
                if not isinstance(obj, dict):
                    continue
                if obj.get("type") == "rate_limit_event":
                    info = obj.get("rate_limit_info")
                    status = info.get("status") if isinstance(info, dict) else None
                    if isinstance(status, str) and status in RATE_LIMIT_REFUSING:
                        kind = info.get("rateLimitType")
                        out.update(refusal=True, source="rate_limit_event", status=status,
                                   rate_limit_type=kind if isinstance(kind, str) else None,
                                   resets_at=rate_limit_reset(info))
                    elif not (isinstance(status, str) and status in RATE_LIMIT_ALLOWED):
                        if not any(type(seen) is type(status) and seen == status for seen in out["unrecognised"]) \
                                and len(out["unrecognised"]) < 20:
                            out["unrecognised"].append(status)
                err = obj.get("error")
                if err == "rate_limit" or (isinstance(err, dict) and err.get("type") == "rate_limit_error"):
                    hit("error_field")
                if obj.get("type") == "result":
                    last_result = obj
    except OSError:
        pass
    if last_result is not None and last_result.get("is_error") is True \
            and isinstance(last_result.get("result"), str) and QUOTA_TEXT.search(last_result["result"]):
        hit("result_event")
    try:
        with open(stderr_path, "r", encoding="utf-8", errors="replace") as f:
            if QUOTA_TEXT.search(f.read()):
                hit("stderr_text")
    except OSError:
        pass
    return out


def provider_session(stdout_path):
    try:
        with open(stdout_path, "r", encoding="utf-8", errors="replace") as f:
            for _, line in zip(range(50), f):
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if isinstance(obj, dict) and obj.get("type") == "system" and isinstance(obj.get("session_id"), str):
                    return obj["session_id"]
    except OSError:
        pass
    return None


def project_settings_digest(worktree):
    """sha256 of <worktree>/.claude/settings.json — the project settings `--setting-sources project` puts in
    force for a job in that worktree — or the string "absent" when nothing is there. None (which never equals a
    bind) when something is there that cannot be read as a file. (kyqualify.py: file_digest.)"""
    path = os.path.join(str(worktree), ".claude", "settings.json")
    if not os.path.lexists(path):
        return "absent"
    return sha_file(path) if os.path.isfile(path) else None


def zdotdir_digest(directory):
    """sha256 over the name, then the content, of every regular file directly under `directory`, names sorted (no
    separator; links and sub-directories skipped) — the shell start-up files the child's ZDOTDIR holds — or
    "absent" when there is no such directory; None when it cannot be read. Byte for byte kyqualify.py's
    directory_digest, which writes this bind."""
    directory = str(directory)
    if not os.path.lexists(directory):
        return "absent"
    if not os.path.isdir(directory):
        return None
    digest = hashlib.sha256()
    try:
        for name in sorted(os.listdir(directory)):
            path = os.path.join(directory, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            digest.update(name.encode("utf-8"))
            with open(path, "rb") as f:
                digest.update(f.read())
    except (OSError, ValueError):
        return None
    return digest.hexdigest()


# ───────────────────────────────── controller ─────────────────────────────────

class Controller:
    def __init__(self, role):
        env = os.environ
        self.role, self.ROLE = role, role.upper()
        self.root = Path(env.get("KY_ROOT") or "/Users/Dev/kalayantra")
        self.run = Path(env.get("KY_RUN") or self.root / "run")
        self.fleet = Path(env.get("KY_FLEET") or self.root / "fleet_live")
        self.scratch = Path(env.get("KY_SCRATCH") or
                            "/Users/Dev/scratch.noindex/claude/madhav/%s-kalayantra-v3" % time.strftime("%Y%m%d"))
        self.claude = Path(env.get("CLAUDE_BIN") or "/Users/Dev/.local/bin/claude")
        self.scale, problem = sleep_scale()
        self.startup_refusal = [problem] if problem else []     # why THIS environment is refused (N4-01): raised
                                                                # as the lock holder, in the one shape of a refusal
        self.controller_id = "CTL-%s-%s-%d" % (self.ROLE, utc("%Y%m%dT%H%M%SZ"), os.getpid())
        self.state_path = self.run / (self.ROLE + "_STATE.json")
        self.journal_path = self.run / ("JOURNAL_%s.md" % self.ROLE)
        self.loop_dir = self.run / "loops" / role
        self.stop_path = self.run / ("STOP_" + role)
        self.lock_dir = self.run / "locks" / role
        self.signal = None
        self.lock_mode = None
        self.lock_refusal = None    # why acquire_lock() said no: {"state": live|cockpit|unknown|self_unknown|race|
                                    # identity_refused|kylock_error, …} (the last two: kylock.sh's answers only)
        self.items_waiting = []     # the message ids the last lock_items() skipped because another actor holds them
        self.ka = self.kc = self.kv = None      # kyaction / kycommands / kyveto, see load_siblings()
        self.commands_blocked = None            # why a QUEUED command of this role could not be settled yet
        self.commands_blocked_since = None      # … and since when (time.time()), see commands_overdue()
        self.logged = {}                        # {line: when log_once() last wrote it}
        self.cfg = None
        self.claude_version = None
        self.verified_once = False
        self.gate_key = None
        self.event_failures = 0
        self.state_sha = None       # sha256 of the role-state file as this controller last saw or wrote it
        self._bin_hash = None
        self.lock_held = False      # True only between a successful acquire() and release_lock()
        self.notify_seq = 0
        self.own_actions = set()    # ids of the action records THIS controller began (never taken for a job's)
        self.item_locks = {}        # {item id: kyaction Lock} of the message locks held for the current run
        self.dispatcher_checked = False
        self.harness = None         # kyqualify, when it is installed beside this file (see load_harness)
        self.qualification_check = None     # which layer judged the receipt at the last verify_launch (N-05)
        self.inbox_keys = set()     # conductor: the message ids of the last inbox poll that are not handled yet

    # ---- plumbing
    def log(self, msg):
        print("kyloop[%s] %s %s" % (self.role, utc(), msg), file=sys.stderr, flush=True)

    def log_once(self, msg, every=300.0):
        """log() for what a waiting controller finds again at every look (a held lock, a command that cannot be
        settled yet): the same line at most once in `every` seconds of real time. A wait that is looked at every
        second says what it waits for when that changes — it does not write two lines a second for as long as it
        lasts."""
        now = time.time()
        if now - self.logged.get(msg, 0.0) >= every:
            if len(self.logged) > 500:
                self.logged.clear()
            self.logged[msg] = now
            self.log(msg)

    def ls(self, fn=None):
        """Read ($KY_RUN/loops/<role>.json as an object; {} when absent) or read-modify-write it. A file that
        exists and cannot be read raises LoopStateUnreadable either way: it is never taken for empty."""
        if fn is None:
            cur, err = loop_state(self.run, self.role)
            if cur is None:
                raise LoopStateUnreadable(self.run / "loops" / (self.role + ".json"), err)
            return cur
        return update_loop_state(self.run, self.role, fn)

    def test_hooks(self):
        """None, or which TEST hooks this controller runs with (N-06). Written into every run record and into
        loops/<role>.json, so that a run made under a compressed clock or an injected context says so itself."""
        injected = os.environ.get(TEST_CONTEXT_ENV)
        if self.scale == 1 and injected is None:
            return None
        return {"sleep_scale": self.scale, "context_injected": injected,
                "context_injection_honoured": injected in ("launchd", "shell") and self.scale < 1}

    def load_siblings(self):
        """kyaction, kycommands and kyveto — the read-only modules this controller is wired to — imported on first
        use from THIS file's own directory and from nowhere else (the admin commands need none of them). A missing,
        unloadable or shadowed module is a refused launch precondition, never a traceback launchd would respawn."""
        if self.ka is not None:
            return
        here = os.path.dirname(os.path.abspath(__file__))
        missing = [n + ".py" for n in SIBLINGS if not os.path.isfile(os.path.join(here, n + ".py"))]
        if missing:
            raise Refusal(["control_module_missing: %s (beside %s)" % (", ".join(missing), os.path.abspath(__file__))])
        sys.dont_write_bytecode = True          # an installed fleet directory holds reviewed files only
        if here not in sys.path:
            sys.path.insert(0, here)
        mods = []
        for name in SIBLINGS:
            try:
                mod = importlib.import_module(name)
            except Exception as e:              # a module that cannot be imported cannot be trusted to act
                raise Refusal(["control_module_unloadable: %s.py (%s)" % (name, type(e).__name__)])
            origin = os.path.dirname(os.path.abspath(getattr(mod, "__file__", "") or ""))
            if origin != here:
                raise Refusal(["control_module_shadowed: %s was loaded from %s, not from %s" % (name, origin, here)])
            mods.append(mod)
        self.ka, self.kc, self.kv = mods

    def actor(self):
        return {"role": self.role, "holder_kind": "controller", "controller_id": self.controller_id}

    def real_context(self):
        """The context PROVEN by the detector alone (parent pid 1 and this loop's own launchd label)."""
        return proven_context(LABEL_PREFIX + self.role, os.getppid(), os.environ.get("XPC_SERVICE_NAME"))

    def context(self):
        """The context this controller PROVABLY runs in — what a qualification receipt must have been earned in.

        TEST-ONLY injection (N-06): KY_LOOP_TEST_CONTEXT=launchd|shell replaces the detector, and is honoured
        ONLY while the test sleep-scale override is active (KY_LOOP_SLEEP_SCALE < 1). At the production scale
        (1, or unset) the variable is ignored — a `launchd`-labelled context is REFUSED there — so a real loop
        can never be told which context it runs in. Its use is recorded (test_hooks()), and a controller that
        really runs under launchd refuses to launch with either hook set (verify_launch).

        An injected context is never reported as a proven one (N3-04): it is `test-hook:launchd` /
        `test-hook:shell`, a context of its own. A receipt earned in the real `launchd` or `shell` context
        therefore never qualifies a controller that was merely TOLD where it runs (qualification_context_mismatch),
        and a receipt written for a hook context qualifies no real controller — nor does kyqualify.py's own
        check_receipt know such a context."""
        injected = os.environ.get(TEST_CONTEXT_ENV)
        if injected in ("launchd", "shell") and self.scale < 1:
            return TEST_CONTEXT_PREFIX + injected
        return self.real_context()

    def admitted(self):
        """Not stopped and enabled. A loop state that cannot be read is not an admission."""
        try:
            return not self.stop_path.exists() and self.ls().get("enabled") is True
        except LoopStateUnreadable:
            return False

    def on_signal(self, signum, _frame):
        self.signal = signum

    def sleep_real(self, seconds):
        end = time.time() + max(0.0, seconds)
        while True:
            if self.signal:
                raise Interrupted()
            left = end - time.time()
            if left <= 0:
                return
            time.sleep(min(left, 0.25))

    def wait(self, state, nominal_seconds=None, real_seconds=None):
        self.heartbeat(state)
        self.sleep_real(real_seconds if real_seconds is not None else nominal_seconds * self.scale)

    def heartbeat(self, waiting=None):
        def fn(d):
            d["controller"] = self.identity()
            d["last_iteration_at"] = utc()
            d["waiting"] = waiting
            d.setdefault("no_progress_count", 0)
            d.setdefault("breaker", {"open": False, "history": []})
            d.setdefault("quota", {"level": 0, "notified_level": 0, "not_before": None, "backoff_minutes": 0})
            d.setdefault("expected_child", None)
            d["test_hooks"] = self.test_hooks()
            return d
        self.ls(fn)

    def identity(self):
        """This controller's own identity. A start identity that could not be read (ps unanswerable) is asked for
        again the next time: it is never cached as "none"."""
        if getattr(self, "_identity", None) is None or self._identity["process_start"] is None:
            ident = ps_identity(os.getpid())
            started = self._identity["started_at"] if getattr(self, "_identity", None) else utc()
            self._identity = {"controller_id": self.controller_id, "pid": os.getpid(), "pgid": os.getpgid(0),
                              "process_start": ident[1] if ident else None, "started_at": started}
        return dict(self._identity)

    def disable(self, reason, force=False):
        def fn(d):
            if d.get("enabled") is True or force or "enabled" not in d:
                d.update(enabled=False, reason=reason, updated_at=utc(), updated_by=self.controller_id)
            return d
        self.ls(fn)

    def submit_notification(self, message, level):
        """Run kynotify.sh once. → {"notify": submitted|failed|dry|unavailable|unknown, "rc", "journal"}: `notify`
        is what its ONE stdout line says, and nothing else is ever read as a submission."""
        script = self.fleet / "kynotify.sh"
        if not script.is_file():
            return {"notify": "unavailable", "rc": None, "journal": None}
        try:
            r = subprocess.run(["/bin/bash", str(script), message, "--level", level], capture_output=True,
                               text=True, timeout=60)
        except (OSError, subprocess.SubprocessError) as e:
            return {"notify": "unknown", "rc": None, "journal": None, "error": type(e).__name__}
        said = r.stdout.strip()
        notify = said[len("notify="):] if said in ("notify=submitted", "notify=failed", "notify=dry") else "unknown"
        return {"notify": notify, "rc": r.returncode,
                "journal": "ok" if r.returncode == 0 else "failed" if r.returncode == 3 else "unknown"}

    def notify(self, message, level):
        """One owner notification, wrapped in an action record (plan §4a.1 lists notifications among the side
        effects): NOTIFY-<controller id>-<n> is INTENDED before kynotify.sh runs and carries the observed
        submission result after. Without the control modules (a refusal raised before they could be loaded) the
        notification is still attempted and says so. Never raises: a notification must not turn a refusal into a
        crash."""
        message, result, action_id = flat(message, 300), None, None
        try:
            if self.ka is not None:
                self.notify_seq += 1
                action_id = "NOTIFY-%s-%d" % (self.controller_id, self.notify_seq)
                self.own_actions.add(action_id)
                status, _ = self.ka.begin(
                    self.run, action_id, "notification", self.actor(), {"level": level, "message": message},
                    {"journal": str(self.run / "JOURNAL_COCKPIT.md"), "channel": "kynotify.sh"},
                    "notify the owner once: not submitted → submitted, one journal line")
                if status != "new":
                    result = {"notify": "not_attempted", "rc": None, "journal": None,
                              "reason": "action record %s is %s" % (action_id, status)}
            if result is None:
                result = self.submit_notification(message, level)
                if action_id is not None:
                    if result["notify"] in ("submitted", "dry"):
                        self.ka.complete(self.run, action_id, result)
                    elif result["notify"] in ("failed", "unavailable"):
                        self.ka.fail(self.run, action_id, result)
                    # "unknown" was not observed: the record stays INTENDED and is reconciled from the journal
        except Exception as e:
            result = dict(result or {"notify": "unknown", "rc": None, "journal": None},
                          record_error="%s: %s" % (type(e).__name__, flat(e, 160)))
        summary = "notify=%s journal=%s rc=%s" % (result.get("notify"), result.get("journal"), result.get("rc"))
        try:
            self.ls(lambda d: dict(d, last_notification={"at": utc(), "level": level, "result": summary,
                                                         "action": action_id}))
        except Exception as e:
            self.log("notification result not recorded in the loop state (%s)" % type(e).__name__)
        self.log("notification (%s): %s" % (level, summary))
        return summary

    def observe_notification(self, record):
        """kyaction observer for a notification a previous controller began and never settled: the journal line
        kynotify.sh writes AFTER its submission attempt is the evidence. No such line → positively not journaled
        (not_done: it is submitted now, under the same record); an unreadable journal → unknown."""
        inputs = record.get("inputs") if isinstance(record.get("inputs"), dict) else {}
        message, level = inputs.get("message"), inputs.get("level")
        if not isinstance(message, str) or level not in ("info", "decision", "hard_stop"):
            return "unknown", {"reason": "the record does not carry a message and a level"}
        try:
            with open(self.run / "JOURNAL_COCKPIT.md", "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().split("\n")
        except FileNotFoundError:
            lines = []
        except OSError as e:
            return "unknown", {"reason": "journal unreadable: %s" % type(e).__name__}
        want = " [%s] %s [notify=" % (level, message)
        for line in lines:
            at = line.find(want)
            if at > 0 and line.endswith("]") and line[at + len(want):-1] in ("submitted", "failed", "dry"):
                return "done", {"notify": line[at + len(want):-1], "journal": "ok", "rc": None, "reconciled": True}
        return "not_done", {"journal_line": False}

    # ---- role lock (sole holder across child jobs)
    @staticmethod
    def lock_owner_state(owner):
        """"live" | "gone" | "unknown" for a lock's recorded owner. "gone" ONLY when the recorded pid is a real
        positive integer and that pid + process_start is positively not running (process_matches is False). A
        missing or unreadable owner record, a null or malformed pid, an identity that cannot be compared and an
        unanswerable ps are all "unknown" — and unknown is never taken over (as in the bootstrap supervisor)."""
        if not isinstance(owner, dict):
            return "unknown"
        match = process_matches(owner.get("pid"), owner.get("process_start"))
        return "live" if match is True else "gone" if match is False else "unknown"

    def owner_doc(self, child):
        ident = self.identity()
        return {"session_or_run_id": self.controller_id, "holder_kind": "controller", "pid": ident["pid"],
                "pgid": ident["pgid"], "process_start": ident["process_start"], "acquired_at": ident["started_at"],
                "child": child}

    def acquire_lock(self):
        """Take the role lock, or say in self.lock_refusal why not. A lock is created atomically WITH its owner
        (lock_create), and an existing one is taken over only when its recorded owner is POSITIVELY gone, by a
        takeover that is verified after the rename (lock_bury). Nothing here ever removes a lock by its age."""
        self.lock_refusal = None
        answer = self.kylock("acquire")
        if answer is not None:                  # kylock.sh is installed: it alone decides, by its exit code
            outcome, rc, text = answer
            if outcome == "ok":
                self.lock_mode, self.lock_held = "kylock", True
                return True
            owner, _ = read_json(self.lock_dir / "owner.json")
            holder = {k: owner.get(k) for k in ("session_or_run_id", "holder_kind", "pid", "process_start")} \
                if isinstance(owner, dict) else None
            self.lock_refusal = {"state": KYLOCK_REFUSALS.get(outcome, "kylock_error"), "holder": holder,
                                 "kylock": outcome, "kylock_rc": rc,
                                 "detail": "kylock.sh acquire: %s (rc=%s) %s" % (outcome, rc, text)}
            self.log("lock held or refused by kylock.sh (%s, rc=%s): %s" % (outcome, rc, text))
            return False
        os.makedirs(self.lock_dir.parent, exist_ok=True)
        if self.identity()["process_start"] is None:
            # a lock whose owner nobody can verify is "unknown" to every other actor, for good: never create one
            self.lock_refusal = {"state": "self_unknown", "detail": "this process's own start identity cannot be read"}
            self.log("lock not taken: this controller's own process identity cannot be read (ps)")
            return False
        for _ in range(3):
            if lock_create(self.lock_dir, self.owner_doc(None)):
                self.lock_mode, self.lock_held = "builtin", True
                return True
            owner = self.read_owner()
            state = self.lock_owner_state(owner)
            holder = {k: owner.get(k) for k in ("session_or_run_id", "holder_kind", "pid", "process_start")} \
                if isinstance(owner, dict) else None
            if state == "live":
                cockpit = owner.get("holder_kind") == "cockpit"
                self.lock_refusal = {"state": "cockpit" if cockpit else "live", "holder": holder}
                self.log("lock held by a live %s (%s, pid %s); this instance exits without launching"
                         % ("cockpit" if cockpit else "owner", owner.get("session_or_run_id"), owner.get("pid")))
                return False
            if state == "unknown":
                if not os.path.lexists(self.lock_dir):
                    continue                    # released between the failed create and the look: try again
                why = "no readable owner record" if holder is None else \
                    "its recorded owner (pid %r) cannot be confirmed gone" % (holder["pid"],)
                self.lock_refusal = {"state": "unknown", "holder": holder, "detail": why}
                self.log("lock held: %s exists and %s — an unknown owner is never taken over"
                         % (self.lock_dir, why))
                return False
            outcome = self.remove_stale_lock(owner)
            if outcome == "removed":
                self.log("stale lock taken over (previous owner %s, pid %s, positively gone)"
                         % (owner.get("session_or_run_id"), owner.get("pid")))
                if owner.get("child") is not None:
                    self.log("the previous owner recorded a child (%s): it is reconciled before any replacement, "
                             "and is never taken for gone while pending or unidentified" % flat(owner.get("child"), 120))
            elif outcome == "conflict":
                self.lock_refusal = {"state": "unknown", "holder": holder,
                                     "detail": "a takeover found another owner's lock and could not put it back"}
                self.log("lock takeover conflict: another owner's lock was left buried beside %s" % self.lock_dir)
                return False
            # "absent" / "changed" / "restored": someone else moved first — create again: one contender gets it
        self.lock_refusal = {"state": "race"}
        self.log("lock held: lost the takeover race")
        return False

    def kylock(self, verb, *args, timeout=KYLOCK_TIMEOUT_S):
        """THE one place $KY_FLEET/kylock.sh is run (packet KV3-B-KYLOCK: `acquire|release|child <role>
        <controller identity> [pending|none|<JSON>]`). → None while kylock.sh is NOT installed as an executable
        file beside this controller — then, and only then, the built-in lock above and below is what holds the
        role — else (outcome, rc, text). `outcome` is read from the exit code and from nothing else: "ok" (0) ·
        "live" (75: a live non-cockpit holder, or a lost race) · "cockpit" (76: a live cockpit) · "unknown" (77:
        an owner nobody can judge; untouched) · "release_unproven" (74: the lock is KEPT, the databases of this
        session are not proven removed) · "not_owner" (73) · "bad_identity" (70) · "usage" (64) · "error" (any
        other code, no answer in time, or it could not be started). Nothing but 0 is ever taken for success."""
        script = self.fleet / "kylock.sh"
        if not (script.is_file() and os.access(script, os.X_OK)):
            return None
        try:
            r = subprocess.run([str(script), verb, self.role, self.controller_id, *args], capture_output=True,
                               text=True, timeout=timeout,
                               env=dict(os.environ, KY_RUN=str(self.run), KY_FLEET=str(self.fleet),
                                        KY_SCRATCH=str(self.scratch)))
        except subprocess.TimeoutExpired:
            return "error", None, "no answer within %d s" % timeout
        except (OSError, ValueError) as e:
            return "error", None, "not started (%s)" % type(e).__name__
        return KYLOCK_EXITS.get(r.returncode, "error"), r.returncode, flat(r.stderr or r.stdout)

    def remove_stale_lock(self, judged):
        """Take the role lock away from an owner that was judged POSITIVELY gone — verify-after-rename (lock_bury),
        so two contenders can never remove each other's fresh lock. → lock_bury's outcome."""
        try:
            return lock_bury(self.lock_dir, judged)
        except OSError as e:
            self.log("stale lock not removed (%s)" % type(e).__name__)
            return "absent"

    def record_lock_wait(self):
        """A live cockpit holder, or an owner that cannot be identified, is recorded as this loop's waiting state.
        A live controller holder is not: it writes this file itself, and a duplicate start must leave it alone.
        An UNKNOWN owner additionally raises ONE attention item (it is never taken over and never treated as
        gone, so somebody has to look) — but no STOP and no switch: this instance never stops what it cannot see."""
        refusal = self.lock_refusal or {}
        waiting = {"cockpit": "role_held_by_cockpit", "unknown": "role_lock_owner_unknown",
                   "self_unknown": "own_process_identity_unknown", "identity_refused": "role_lock_identity_refused",
                   "kylock_error": "role_lock_helper_failed"}.get(refusal.get("state"))
        if not waiting:
            return
        try:
            self.ls(lambda d: dict(d, waiting=waiting, lock_wait=dict(refusal, at=utc(), observed_by=self.controller_id)))
        except LoopStateUnreadable as r:
            self.log("lock wait not recorded: %s" % r)
        if refusal.get("state") == "self_unknown":
            self.raise_attention(
                "loop-%s-identity-unknown" % self.role,
                "A %s loop controller could not read its own process-start identity (ps did not answer), so it took "
                "no lock and launched nothing: a lock whose owner nobody can verify would block the role for good."
                % self.role, ["controller: %s" % self.controller_id],
                message="%s loop did not start: its own process identity cannot be read" % self.role)
        if refusal.get("state") in ("identity_refused", "kylock_error"):
            # kylock.sh said neither "held" nor "acquired": not a waiting state that ends by itself, so somebody
            # is told — and nothing is stopped, since this instance holds nothing
            self.raise_attention(
                "loop-%s-lock-helper-refused" % self.role,
                "kylock.sh did not give the %s loop controller the role lock and did not report a holder either "
                "(%s). Nothing was launched. %s" % (
                    self.role, flat(refusal.get("detail"), 200),
                    "It refused this controller's identity (exit 70)." if refusal.get("state") == "identity_refused"
                    else "Its answer is not one of its documented exit codes."),
                ["controller: %s" % self.controller_id, "helper: %s" % (self.fleet / "kylock.sh"),
                 "answer: %s" % flat(refusal.get("detail"), 300)],
                message="%s loop did not start: kylock.sh refused or failed (%s)" % (self.role, refusal.get("kylock")))
        if refusal.get("state") == "unknown":
            self.raise_attention(
                "loop-%s-lock-owner-unknown" % self.role,
                "The %s role lock %s exists but its owner cannot be identified (%s). It is never taken over and "
                "never removed by age, so the %s loop cannot start. Is its owner gone?"
                % (self.role, self.lock_dir, flat(refusal.get("detail"), 160), self.role),
                ["lock: %s" % self.lock_dir, "recorded owner: %s" % flat(json.dumps(refusal.get("holder")), 200)],
                options=[{"id": "remove-lock", "text": "The owner is gone: remove the lock directory by hand, then "
                                                       "`kyctl.sh start %s`." % self.role},
                         {"id": "leave", "text": "The owner is alive (or unknown): leave the lock alone."}],
                message="%s loop cannot start: its role lock has an owner that cannot be identified" % self.role)

    def read_owner(self):
        """owner.json of the role lock as an object, or None when it is missing (after a short wait for an
        acquirer that makes its lock in two steps — the cockpit's documented mkdir fence) or not readable as an
        object."""
        for _ in range(8):
            owner, err = read_json(self.lock_dir / "owner.json")
            if isinstance(owner, dict):
                return owner
            if err != "missing" or not os.path.lexists(self.lock_dir):
                return None
            time.sleep(max(0.01, 0.25 * self.scale))
        return None

    def write_owner(self, child):
        """Record the child this lock's holder is responsible for: None, "pending" (written BEFORE the child is
        started, so a controller that dies in between never looks child-less), or its identity."""
        if self.lock_mode == "builtin":
            write_json(self.lock_dir / "owner.json", self.owner_doc(child))
        elif self.lock_mode == "kylock":
            # `kylock.sh child <role> <identity> pending|none|<JSON>` — the same record, written by the lock's owner
            arg = "none" if child is None else child if child == "pending" else json.dumps(child, sort_keys=True)
            outcome, rc, text = self.kylock("child", arg) or ("error", None, "kylock.sh is no longer installed")
            if outcome == "ok":
                return
            why = "role_lock_child_not_recorded: kylock.sh child %s: %s (rc=%s) %s" % (
                "<identity>" if isinstance(child, dict) else arg, outcome, rc, text)
            if child is None:
                # a child that stays recorded after it ended is the safe side (it is judged by its identity);
                # the next launch records "pending" first, and THAT is refused while kylock.sh still says no
                self.log(why)
                return
            raise Refusal([why])                # no child is started, or left running, that the lock does not name

    def release_lock(self):
        if self.lock_mode == "kylock":
            outcome, rc, text = self.kylock("release", timeout=KYLOCK_RELEASE_TIMEOUT_S) \
                or ("error", None, "kylock.sh is no longer installed")
            if outcome != "ok":
                self.release_not_proven(outcome, rc, text)
        elif self.lock_mode == "builtin":
            owner, _ = read_json(self.lock_dir / "owner.json")
            if isinstance(owner, dict) and owner.get("session_or_run_id") == self.controller_id \
                    and owner.get("pid") == os.getpid():
                try:                            # buried whole: the lock never stands there without its owner
                    outcome = lock_bury(self.lock_dir, owner)
                    if outcome != "removed":
                        self.log("the lock was not released (%s)" % outcome)
                except OSError as e:
                    self.log("could not release the lock: %s" % type(e).__name__)
        self.lock_mode, self.lock_held = None, False

    def release_not_proven(self, outcome, rc, text):
        """kylock.sh did not answer `released`. Nothing here calls the lock released: what it said is recorded in
        loops/<role>.json (`lock_release`) and — except for a lock that simply is not this controller's (73) — ONE
        attention item is raised. 74 means the lock is KEPT because the databases of this session are not proven
        removed (KU-02); the next controller takes the lock over from this process once it is positively gone,
        and that takeover never removes a database. Never raises: this runs while the controller exits."""
        kept = outcome == "release_unproven"
        self.log("the role lock was NOT released by kylock.sh (%s, rc=%s): %s%s"
                 % (outcome, rc, text, " — the lock is kept; this session's databases are not proven removed" if kept else ""))
        note = {"state": "kept" if kept else "not_owner" if outcome == "not_owner" else "unknown", "kylock": outcome,
                "kylock_rc": rc, "at": utc(), "controller_id": self.controller_id, "detail": flat(text, 200)}
        try:
            self.ls(lambda d: dict(d, lock_release=note))
        except Exception as e:
            self.log("the lock release result was not recorded (%s)" % type(e).__name__)
        if outcome == "not_owner":
            return
        self.raise_attention(
            "loop-%s-lock-release-unproven" % self.role,
            "The %s loop controller %s ended, and %s" % (
                self.role, self.controller_id,
                "kylock.sh KEPT the role lock: the test databases of that session are not proven removed (exit 74). "
                "Remove them?" if kept else
                "kylock.sh did not confirm that the role lock was released (%s). Is the lock still there?" % outcome),
            ["kylock.sh release: %s (rc=%s) %s" % (outcome, rc, flat(text, 240)), "lock: %s" % self.lock_dir,
             "session: %s" % self.controller_id, "scratch: %s" % self.scratch],
            options=[{"id": "close-databases", "text": "Run `local_db.sh close --session %s` (or remove that "
                                                       "session's test databases by hand) and check that they are "
                                                       "gone." % self.controller_id},
                     {"id": "acknowledge", "text": "Seen; nothing further."}],
            message="%s loop: kylock.sh did not release the role lock (%s)" % (self.role, outcome))

    # ---- configuration and launch preconditions
    def load_config(self):
        cfg = dict(DEFAULTS[self.role], mcp_config=str(self.fleet / "mcp.none.json"), substep_cap=SUBSTEP_CAP)
        path = self.run / "loops.json"
        if not path.exists():
            return cfg, []
        doc, err = read_json(path)
        if err:
            return None, ["loops_json_invalid: %s" % err]
        errs = []
        if not isinstance(doc, dict):
            return None, ["loops_json_invalid: top level must be an object"]
        for role, entry in doc.items():
            if role not in ROLES:
                errs.append("unknown role key %r" % role)
            elif not isinstance(entry, dict):
                errs.append("%s must be an object" % role)
            else:
                for k, v in entry.items():
                    bad = k not in CONFIG_KEYS
                    if k in ("worktree", "mcp_config"):
                        bad = not (isinstance(v, str) and v.startswith("/") and "\n" not in v and "\0" not in v)
                    elif k == "model":
                        bad = not (isinstance(v, str) and MODEL_RE.match(v))
                    elif k == "effort":
                        bad = v not in EFFORTS
                    elif k == "permission_mode":
                        bad = v not in PERMISSION_MODES
                    elif k in ("max_turns", "deadline_seconds", "substep_cap"):
                        bad = not (isinstance(v, int) and not isinstance(v, bool) and v > 0)
                    if bad:
                        errs.append("%s.%s is unknown or has the wrong type/value" % (role, k))
        if errs:
            return None, ["loops_json_invalid: " + "; ".join(errs)]
        cfg.update(doc.get(self.role, {}))
        return cfg, []

    def child_path(self):
        parts = [str(self.root / "bin")]
        try:
            node = (self.run / "NODE_BIN").read_text().splitlines()[0].strip()
            if node.startswith("/") and os.path.isdir(node):
                parts.append(node)
        except (OSError, IndexError):
            pass
        return ":".join(parts + ["/opt/homebrew/bin", "/usr/bin", "/bin"])

    def argv(self, cfg):
        return [str(self.claude), "-p", "--setting-sources", "project", "--permission-mode", cfg["permission_mode"],
                "--model", cfg["model"], "--effort", cfg["effort"], "--max-turns", str(cfg["max_turns"]),
                "--strict-mcp-config", "--mcp-config", cfg["mcp_config"], "--output-format", "stream-json",
                "--verbose", "--add-dir", str(self.root)]

    def bin_sha(self):
        real = os.path.realpath(self.claude)
        try:
            st = os.stat(real)
        except OSError:
            return None
        key = (real, st.st_size, st.st_mtime_ns)
        if not self._bin_hash or self._bin_hash[0] != key:
            self._bin_hash = (key, sha_file(real))
        return self._bin_hash[1]

    def expected_binds(self, cfg):
        """Everything a launch qualification receipt must bind (plan §7 KV-06): the program and its hash and
        version, the exact argv, the limits, the role worktree AND the project settings in force there
        (`<worktree>/.claude/settings.json`, or "absent"), the child environment's names (JOB_SCRATCH among them)
        and its PATH, the shell start-up files the child's ZDOTDIR holds, the prompt and the MCP configuration —
        and, when the qualification harness is installed beside this file, that harness itself (`harness_sha256`,
        which kyqualify.py binds into every receipt it writes: a receipt from another harness, or one that binds a
        harness while none is installed here to compare it with, is a mismatch)."""
        binds = {"claude_bin": str(self.claude), "claude_bin_sha256": self.bin_sha(),
                 "claude_version": self.read_claude_version()[0], "argv": self.argv(cfg), "model": cfg["model"],
                 "effort": cfg["effort"], "permission_mode": cfg["permission_mode"], "max_turns": cfg["max_turns"],
                 "deadline_seconds": cfg["deadline_seconds"], "worktree": cfg["worktree"],
                 "env_names": sorted(CHILD_ENV_NAMES), "child_path": self.child_path(),
                 "prompt_sha256": sha_file(self.fleet / "prompts" / PROMPTS[self.role]),
                 "mcp_config_sha256": sha_file(cfg["mcp_config"]),
                 "project_settings_sha256": project_settings_digest(cfg["worktree"]),
                 "zdotdir_sha256": zdotdir_digest(self.root / "zdotdir")}
        harness = os.path.join(os.path.dirname(os.path.abspath(__file__)), HARNESS + ".py")
        if os.path.isfile(harness):
            binds["harness_sha256"] = sha_file(os.path.realpath(harness))
        return binds

    def launch_config(self, cfg):
        """The ky.launch_config/1 a loop role is qualified with: what `kyqualify.py qualify --config` is given
        (`kyloop.py admin launch-config <role>` prints it) and what its check_receipt recomputes the binds from."""
        return {"schema": "ky.launch_config/1", "role": self.role, "model": cfg["model"], "effort": cfg["effort"],
                "permission_mode": cfg["permission_mode"], "max_turns": cfg["max_turns"],
                "deadline_seconds": cfg["deadline_seconds"], "worktree": cfg["worktree"],
                "claude_bin": str(self.claude), "mcp_config": cfg["mcp_config"],
                "prompt_path": str(self.fleet / "prompts" / PROMPTS[self.role]),
                "env_names": list(CHILD_ENV_NAMES), "child_path": self.child_path(), "extra_flags": [],
                "disallowed_tools": [], "add_dirs": [str(self.root)], "intended_tools": list(QUALIFIED_TOOLS),
                "denied_tools": [], "shell_canary": "python3"}

    def load_harness(self):
        """kyqualify — the launch-qualification harness — when it is installed beside this file; None when it is
        not. Imported from THIS directory only; one that is there and cannot be loaded (kyprobe.py, which it
        imports, missing or broken) is a refused precondition, never silently skipped."""
        if self.harness is not None:
            return self.harness
        here = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isfile(os.path.join(here, HARNESS + ".py")):
            return None
        sys.dont_write_bytecode = True
        if here not in sys.path:
            sys.path.insert(0, here)
        try:
            mod = importlib.import_module(HARNESS)
        except Exception as e:
            raise Refusal(["qualification_harness_unloadable: %s.py (%s)" % (HARNESS, type(e).__name__)])
        origin = os.path.dirname(os.path.abspath(getattr(mod, "__file__", "") or ""))
        if origin != here or not callable(getattr(mod, "check_receipt", None)):
            raise Refusal(["qualification_harness_unusable: %s was loaded from %s and offers %s check_receipt"
                           % (HARNESS, origin, "a" if callable(getattr(mod, "check_receipt", None)) else "no")])
        self.harness = mod
        return mod

    def qualification_path(self, cfg):
        return self.run / "QUALIFICATIONS" / ("%s-%s.json" % (self.role, cfg["model"]))

    def read_claude_version(self):
        if not (self.claude.is_file() and os.access(self.claude, os.X_OK)):
            return None, "claude_bin_not_executable: %s" % self.claude
        try:
            r = subprocess.run([str(self.claude), "--version"], capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError) as e:
            return None, "claude_version_unknown: %s" % type(e).__name__
        m = re.search(r"(\d+)\.(\d+)\.(\d+)", r.stdout)
        if r.returncode != 0 or not m:
            return None, "claude_version_unknown: rc=%d" % r.returncode
        ver = tuple(int(x) for x in m.groups())
        text = ".".join(m.groups())
        if ver < MIN_CLAUDE:
            return text, "claude_version_below_pin: %s < %s" % (text, ".".join(str(x) for x in MIN_CLAUDE))
        return text, None

    def run_helper(self, name, args, timeout):
        script = self.fleet / name
        if not script.is_file():
            return None
        try:
            return subprocess.run(["/bin/bash", str(script), *args], capture_output=True, text=True,
                                  timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            return 124
        except OSError:
            return 126

    def owner_resume(self):
        doc, _ = read_json(self.run / "OWNER_RESUME.json")
        if isinstance(doc, dict) and isinstance(doc.get("approved_bundle_digest"), str) \
                and SHA_RE.match(doc["approved_bundle_digest"]):
            return doc
        return None

    def read_role_state(self):
        doc, err = read_json(self.state_path)
        if err:
            return None, "role_state_%s" % ("missing" if err == "missing" else "unreadable")
        if not isinstance(doc, dict) or not isinstance(doc.get("completed_steps", []), list):
            return None, "role_state_unreadable"
        if "active" not in doc:
            return None, "role_state_legacy_schema: no `active` index (the one-time migration is the cockpit's, under the role lock)"
        return doc, None

    def verify_launch(self):
        """All launch preconditions; raises Refusal listing every failure. Run at start-up and before EVERY launch."""
        reasons = []
        cfg, errs = self.load_config()
        if errs:
            raise Refusal(errs)
        hooks = self.test_hooks()
        if hooks and self.real_context() == "launchd":
            reasons.append("test_hooks_in_launchd_context: %s is set for a controller that runs under launchd"
                           % " and ".join(n for n, on in (("KY_LOOP_SLEEP_SCALE", self.scale != 1),
                                                         (TEST_CONTEXT_ENV, hooks["context_injected"] is not None)) if on))
        receipt, err = read_json(self.run / "INSTALL_RECEIPT.json")
        if err == "missing":
            reasons.append("install_receipt_missing: %s" % (self.run / "INSTALL_RECEIPT.json"))
        elif err or not isinstance(receipt, dict):
            reasons.append("install_receipt_unreadable")
        elif receipt.get("mode") not in RECEIPT_MODES[self.role]:
            reasons.append("install_receipt_mode: got %r, the %s loop needs %s"
                           % (receipt.get("mode"), self.role, " or ".join(RECEIPT_MODES[self.role])))
        version, verr = self.read_claude_version()
        if verr:
            reasons.append(verr)
        self.claude_version = version
        digest, activation = None, None
        if self.role == "conductor":
            resume = self.owner_resume()
            links, cerr = self.activation_chain()
            if cerr:
                reasons.append(cerr)
            elif resume is None or links[-1]["manifest_digest"] != resume["approved_bundle_digest"]:
                reasons.append("approved_digest_mismatch: OWNER_RESUME.approved_bundle_digest differs from the "
                               "terminal activation record (%s)" % links[-1]["file"])
            else:
                digest = links[-1]["manifest_digest"]
                activation = {"links": len(links), "terminal": links[-1]["file"],
                              "terminal_sha256": links[-1]["sha256"], "manifest_digest": digest}
        version_args = None
        if self.role == "planner" or digest:        # the conductor's digest comes from the activation chain only
            version_args = ["--bootstrap"] if self.role == "planner" else ["--expected-manifest-digest", digest]
            rc = self.run_helper("kyversion.sh", version_args, 300)
            if rc is None:
                reasons.append("kyversion_missing: %s" % (self.fleet / "kyversion.sh"))
            elif rc != 0:
                reasons.append("kyversion_failed: rc=%d" % rc)
        prompt = self.fleet / "prompts" / PROMPTS[self.role]
        if not prompt.is_file():
            reasons.append("loop_prompt_missing: %s" % prompt)
        mcp, merr = read_json(cfg["mcp_config"])
        if merr or not isinstance(mcp, dict) or not isinstance(mcp.get("mcpServers"), dict):
            reasons.append("mcp_config_unreadable: %s" % cfg["mcp_config"])
        elif self.role == "planner" and mcp != {"mcpServers": {}}:
            reasons.append("mcp_config_not_empty: bootstrap-phase jobs use the empty configuration (plan §7 KT-02)")
        if not os.path.isdir(cfg["worktree"]):
            reasons.append("worktree_missing: %s" % cfg["worktree"])
        if self.role == "planner" or self.state_path.exists():
            _, serr = self.read_role_state()
            if serr:
                reasons.append(serr)
        if self.role == "conductor":
            if not os.access(self.root / "bin" / "ky", os.X_OK):
                reasons.append("ky_cli_missing: %s" % (self.root / "bin" / "ky"))
            if not reasons:
                key = (sha_file(self.run / "OWNER_RESUME.json"), sha_file(self.run / "RELEASE_RECEIPT.json"))
                if key != self.gate_key:
                    rc = self.run_helper("kygate.sh", [], 1800)
                    if rc is None:
                        reasons.append("kygate_missing: %s" % (self.fleet / "kygate.sh"))
                    elif rc != 0:
                        reasons.append("gate_not_open: kygate.sh rc=%d" % rc)
                    else:
                        self.gate_key = key
        if not reasons:
            reasons.extend(self.check_qualification(cfg))
        if reasons:
            raise Refusal(reasons)
        self.cfg = cfg
        bundle = {"verified_at": utc(), "by": "kyversion.sh %s" % " ".join(version_args or []),
                  "receipt_mode": receipt.get("mode"), "receipt_sha256": sha_file(self.run / "INSTALL_RECEIPT.json"),
                  "manifest_digest": digest}
        self.ls(lambda d: dict(d, bundle_verified_at=bundle["verified_at"], bundle=bundle,
                               qualification_check=self.qualification_check,
                               **({"activation": activation} if activation else {})))

    def activation_chain(self):
        """The conductor's authorisation chain, validated from its start. → ([link, …], None) or (None, reason).

        Every activation record is a link; the chain's root is the owner-approved trust-root commit itself (no
        record). The plan-named un-numbered $KY_RUN/ACTIVATION_RECORD.json, when present, is link 0, and the
        numbered links ACTIVATION_RECORD.1.json, .2.json, … — as kyveto.py's plan_bundle_change executor writes
        them (its `chain` / `_verify`) — chain after it, contiguous from 1. When it is ABSENT (a bundle change
        made before B-5) the numbered links alone are the chain and B-5's final activation is simply its next
        link. The FIRST link has previous = null; every later link carries n, names its predecessor as previous =
        {file, sha256 of that file} and continues it (old_commit and old_manifest_digest equal the predecessor's
        new ones). The TERMINAL link supplies the approved manifest digest.

        Refused: anything else beside these files (ACTIVATION_RECORD*.json), or a link 1 without a predecessor
        although the un-numbered record exists — a fork; a gap in the numbering, a wrong or missing predecessor
        hash, a misnumbered, unreadable or discontinuous link — a broken chain; no link at all — a missing chain.
        Checked here: hashes and continuity. Not checked here: that each link's authorising act was effective,
        nor that the first link's old_commit is the trust root (this controller is not given the trust root)."""
        numbered, root = {}, None
        for path in sorted(self.run.glob("ACTIVATION_RECORD*.json")):
            m = ACTIVATION_NAME.match(path.name)
            if not m:
                return None, "activation_chain_forked: unexpected file %s beside the activation chain" % path.name
            if m.group(1) is None:
                root = path
            else:
                numbered[int(m.group(1))] = path
        if root is None and not numbered:
            return None, "activation_record_missing: %s" % (self.run / "ACTIVATION_RECORD.json")

        def agreed(doc, keys, pattern):
            """The one value the present keys agree on, or None (kyveto reads the first key that is present)."""
            values = [doc[k] for k in keys if k in doc]
            ok = values and all(isinstance(v, str) and pattern.match(v) and v == values[0] for v in values)
            return values[0] if ok else None

        links = []
        if root is not None:                    # link 0: the un-numbered record
            doc, err = read_json(root)
            if err or not isinstance(doc, dict):
                return None, "activation_record_invalid: %s is unreadable" % root.name
            digest = agreed(doc, ("new_manifest_digest", "final_manifest_digest"), SHA_RE)
            if digest is None:
                return None, "activation_record_invalid: need final_manifest_digest (sha256 hex)"
            commit = agreed(doc, ("new_commit", "source_commit"), HEX_COMMIT)   # may be absent in a chain of one
            links.append({"n": 0, "file": root.name, "sha256": sha_file(root), "commit": commit,
                          "manifest_digest": digest})
        for n in range(1, len(numbered) + 1):
            path, before = numbered.get(n), links[-1] if links else None
            if path is None:
                return None, "activation_chain_broken: ACTIVATION_RECORD.%d.json is missing from the sequence" % n
            doc, err = read_json(path)
            if err or not isinstance(doc, dict) or type(doc.get("n")) is not int or doc["n"] != n:
                return None, "activation_chain_broken: %s is unreadable or misnumbered" % path.name
            if any(not isinstance(doc.get(k), str) or not HEX_COMMIT.match(doc[k]) for k in ("old_commit", "new_commit")) \
                    or any(not isinstance(doc.get(k), str) or not SHA_RE.match(doc[k])
                           for k in ("old_manifest_digest", "new_manifest_digest")):
                return None, "activation_chain_broken: %s lacks old/new source commits or manifest digests" % path.name
            if before is None:                  # the first link of a numbered-only chain: nothing precedes it
                if doc.get("previous") is not None:
                    return None, ("activation_chain_broken: %s names a predecessor that is not there (a first link "
                                  "has previous: null)" % path.name)
            elif doc.get("previous") is None:
                return None, ("activation_chain_forked: %s names no predecessor although %s exists — a second "
                              "chain start" % (path.name, before["file"]))
            elif before["sha256"] is None or doc["previous"] != {"file": before["file"], "sha256": before["sha256"]}:
                return None, "activation_chain_broken: %s does not name its predecessor %s by sha256" % (
                    path.name, before["file"])
            elif doc["old_commit"] != before["commit"] or doc["old_manifest_digest"] != before["manifest_digest"]:
                return None, ("activation_chain_broken: %s does not continue %s (its old commit / old manifest "
                              "digest are not the predecessor's new ones)" % (path.name, before["file"]))
            links.append({"n": n, "file": path.name, "sha256": sha_file(path), "commit": doc["new_commit"],
                          "manifest_digest": doc["new_manifest_digest"]})
        return links, None

    def check_qualification(self, cfg):
        """Every reason the role's qualification receipt does not qualify THIS launch ([] = it does).

        Two layers (N-05). (1) The controller's own comparison: the receipt is a ky.qualification/1 for this role
        and model, says PASS, was earned in the context this controller provably runs in, and binds exactly what
        this controller is about to launch. (2) When the harness is installed beside this file, kyqualify.py's
        own `check_receipt(receipt, launch configuration, require_context=…)` — which re-evaluates the receipt's
        checks and negative probes, its launchd receipt, its tool coverage and the binds recomputed from disk —
        must return no reason either. Which layer judged is recorded in loops/<role>.json
        (`qualification_check.mode`: "kyqualify.check_receipt" or "controller_only"). Under launchd — where the
        installed loops run — a missing harness refuses the launch (`qualification_harness_missing`, N3-05);
        `controller_only` is left to a controller started by hand from a shell."""
        self.qualification_check = None
        path = self.qualification_path(cfg)
        doc, err = read_json(path)
        if err == "missing":
            return ["qualification_missing: %s" % path]
        if err or not isinstance(doc, dict):
            return ["qualification_unreadable: %s" % path]
        if doc.get("schema") != RECEIPT_SCHEMA:
            return ["qualification_schema: %s is not a %s receipt" % (path.name, RECEIPT_SCHEMA)]
        if doc.get("role") != self.role or doc.get("model") != cfg["model"]:
            return ["qualification_role_mismatch: the receipt is for role %r and model %r, this controller launches "
                    "%r with %r" % (doc.get("role"), doc.get("model"), self.role, cfg["model"])]
        if doc.get("result") != "PASS":
            return ["qualification_not_pass: result is %r (unknown refuses)" % (doc.get("result"),)]
        mine, earned = self.context(), doc.get("context")
        if not isinstance(earned, str) or not earned:
            return ["qualification_context_missing: the receipt does not say in which context it was earned "
                    "(this controller runs in %r)" % mine]
        if earned != mine:
            return ["qualification_context_mismatch: the receipt was earned in %r, this controller runs in %r"
                    % (earned, mine)]
        harness = self.load_harness()
        expected, got = self.expected_binds(cfg), doc.get("binds")
        if not isinstance(got, dict):
            return ["qualification_mismatch: no binds"]
        diff = sorted(k for k in set(expected) | set(got) if expected.get(k) != got.get(k) or expected.get(k) is None)
        if diff:
            return ["qualification_mismatch: %s" % ", ".join(diff)]
        mode = "controller_only"
        if harness is None and self.real_context() == "launchd":
            # N3-05: an installed loop is judged by the harness or not at all. The controller's own, weaker
            # comparison stays for a controller run by hand from a shell (recorded as `controller_only`).
            return ["qualification_harness_missing: %s.py is not installed beside %s — under launchd the receipt "
                    "is judged by its check_receipt, never by the controller's own comparison alone"
                    % (HARNESS, os.path.abspath(__file__))]
        if harness is not None:
            config = self.launch_config(cfg)
            missing = sorted(set(getattr(harness, "CONFIG_KEYS", ())) - set(config))
            if missing:
                return ["qualification_config_incomplete: the harness needs %s in a launch configuration"
                        % ", ".join(missing)]
            try:
                refused = harness.check_receipt(doc, config, require_context=mine)
            except Exception as e:              # a harness that cannot judge has accepted nothing
                return ["qualification_harness_failed: %s: %s" % (type(e).__name__, flat(e, 160))]
            if refused:
                return ["qualification_refused_by_harness: %s" % "; ".join(flat(r, 200) for r in list(refused)[:8])]
            mode = "kyqualify.check_receipt"
        self.qualification_check = {"mode": mode, "receipt": str(path), "receipt_sha256": sha_file(path),
                                    "context": mine, "at": utc()}
        return []

    # ---- owner-waits raised by the controller itself
    def write_awaiting(self, slug, question, options, recommendation, evidence, item=None, blocks="loop"):
        directory = self.run / "awaiting"
        os.makedirs(directory, exist_ok=True)
        stamp = utc("%Y%m%dT%H%M%SZ")
        aid, t = "AW-%s-%s" % (stamp, slug), calendar.timegm(time.strptime(stamp, "%Y%m%dT%H%M%SZ"))
        # an id no item ever had — open, answered or closed: a second item of this slug within the same second
        # neither replaces the first nor is born answered by the decision that lies beside the old id
        while any(os.path.lexists(x) for x in (directory / (aid + ".json"), directory / (aid + OWNER_DECISION_SUFFIX),
                                               directory / AWAITING_DONE / (aid + ".json"))):
            t += 1
            aid = "AW-%s-%s" % (utc("%Y%m%dT%H%M%SZ", t), slug)
        doc = {"schema": "ky.awaiting/1", "id": aid, "created_at": utc(),
               "raised_by": {"role": self.role, "session_id": self.controller_id, "job_id": None},
               "item": item or "loop.%s" % self.role, "question": question, "options": options,
               "recommendation": recommendation, "evidence": evidence, "deadline": None,
               "class_hint": "unknown", "blocks": blocks}
        write_json(directory / (aid + ".json"), doc)
        return doc

    def open_awaiting(self, slug):
        """This controller's own awaiting files with that slug which the owner has not answered yet."""
        directory = self.run / "awaiting"
        if not directory.is_dir():
            return []
        return [p for p in sorted(directory.glob("AW-*-%s.json" % slug))
                if not p.with_name(p.stem + OWNER_DECISION_SUFFIX).exists()]

    def ensure_stop(self, why):
        if not self.stop_path.exists():
            write_atomic(self.stop_path, "%s %s: %s\n" % (utc(), self.controller_id, why))

    def raise_attention(self, slug, question, evidence, options=None, item=None, blocks="none", message=None,
                        level="decision"):
        """ONE owner-visible item that does not stop the loop: an awaiting file — none while an item of that slug
        is still open — and one notification for it. → the item written, or None. Never raises."""
        try:
            if self.open_awaiting(slug):
                return None
            doc = self.write_awaiting(slug, question, options or [{"id": "acknowledge", "text": "Seen; nothing further."}],
                                      None, [flat(e, 300) for e in evidence], item=item, blocks=blocks)
        except Exception as e:
            self.log("attention item %s could not be written (%s: %s)" % (slug, type(e).__name__, flat(e, 160)))
            return None
        self.notify("%s; see %s" % (flat(message or question, 160), doc["id"]), level)
        return doc

    def raise_precondition(self, reasons):
        """The ONE shape of a refusal: STOP_<role>, one awaiting item with one notification, `enabled: false`.
        No second item and no second notification while an item for THESE reasons is open — the same refusal,
        met again at a restart, is before the owner already. A refusal for other reasons is a new item (R16): the
        item tells the owner to correct the cause and start the loop again, nobody has to answer or close it, and
        a later, different refusal must not hide behind it with nobody told. Each step is attempted whatever
        became of the others, and none of them can raise: this is also where an unexpected exception ends, and it
        must end in exit 0."""
        slug = "loop-%s-precondition" % self.role
        self.log("REFUSED launch: " + "; ".join(reasons))

        def item():
            evidence = ["precondition: %s" % flat(r, 400) for r in reasons]
            for path in self.open_awaiting(slug):
                doc = read_json(path)[0]
                if isinstance(doc, dict) and doc.get("evidence") == evidence:
                    return                      # this very refusal is before the owner already
            doc = self.write_awaiting(
                slug, "The %s loop controller refused to launch because a launch precondition failed. "
                      "Correct the cause and restart, or keep the loop stopped?" % self.role,
                [{"id": "fix-and-restart", "text": "Correct the failed precondition(s), then run "
                                                   "`kyctl.sh start %s --clear-stop`." % self.role},
                 {"id": "keep-stopped", "text": "Leave the %s loop stopped." % self.role}],
                "fix-and-restart", evidence)
            self.notify("%s loop stopped: launch precondition failed (%s); see %s"
                        % (self.role, flat(reasons[0], 120), doc["id"]), "decision")

        for what, step in (("STOP file", lambda: self.ensure_stop("precondition failed")), ("awaiting item", item),
                           ("enabled switch", lambda: self.disable("precondition failed: %s" % flat(reasons[0], 160),
                                                                    force=True))):
            try:
                step()
            except Exception as e:
                self.log("refusal: the %s could not be written (%s: %s)" % (what, type(e).__name__, flat(e, 160)))

    # ---- work: what is eligible right now
    def accepted_steps(self, state):
        out = {}
        for entry in state.get("completed_steps", []):
            if isinstance(entry, dict) and isinstance(entry.get("id"), str) \
                    and isinstance(entry.get("evidence_sha256"), str) and SHA_RE.match(entry["evidence_sha256"]):
                out[entry["id"]] = entry
        return out

    def wait_target(self, doc, scope=None):
        """What the owner-wait `doc` holds up FOR THIS ROLE → ("loop", None) · ("item", key) · None.
        None for everything this role's controller raised itself, an item-level wait of its own apart (its other
        items act through STOP, the breaker or as plain attention, and resolving them is not changed evidence).
        A loop-level wait counts only when it names this loop or this role raised it. `scope`, when given, is the
        keys of the items THIS role can work on (item_keys()): an item-level wait about anything else — another
        role's wait for another item — is None too (L3-01), judged by the very comparison is_blocked() makes."""
        raised = doc.get("raised_by") if isinstance(doc.get("raised_by"), dict) else {}
        if raised.get("role") == self.role and str(raised.get("session_id", "")).startswith("CTL-") \
                and raised.get("job_id") is None and doc.get("blocks") != "item":
            return None                         # this role's controller wrote it: STOP / breaker / attention
        item, blocks = str(doc.get("item", "")), doc.get("blocks")
        if blocks == "loop" and (item == "loop.%s" % self.role or raised.get("role") == self.role):
            return "loop", None
        if blocks == "item" and item:
            key = item.split(".", 1)[1] if item.startswith(("step.", "msg.")) else item
            if scope is not None and not any(self.is_blocked(k, (key,)) for k in scope):
                return None                     # not a wait of this role: it neither blocks nor counts here
            return "item", key
        return None

    def owner_answers(self):
        """{awaiting id: {"record", "command", "path"}} — the OWNER's recorded answers, and nothing else (R15).
        `<id>.owner_decision.json` in $KY_RUN/awaiting is one only when
          * it is a ky.owner_decision/1 object naming that awaiting id — the id of the item it lies beside — and
          * the command it names is in the queue as an acceptable `decide` for that awaiting id, with that
            answer, QUEUED or APPLIED. The queue admits the cockpit as its only sender, and those two states are
            what kyveto.py reads as "the owner decided" as well.
        A record no such command stands behind — a surrogate's, a job's, one written by hand — is not an answer,
        whatever it says of itself: it releases nothing and is no evidence (so no wait, a hard stop least of all,
        is released by anything but an owner `decide`). Nor is there an answer while the queue cannot be read:
        unknown is never an answer."""
        directory = self.run / "awaiting"
        paths = sorted(directory.glob("*" + OWNER_DECISION_SUFFIX)) if directory.is_dir() else []
        if not paths:
            return {}
        try:
            self.load_siblings()
            decides = {e["doc"]["id"]: e["doc"] for e in self.kc.scan(self.run)[0]
                       if not e["invalid"] and e["doc"]["command"] == "decide"
                       and e["doc"]["state"] in ("QUEUED", "APPLIED")}
        except (Refusal, OSError):
            return {}
        out = {}
        for p in paths:
            aid = p.name[:-len(OWNER_DECISION_SUFFIX)]
            rec, _ = read_json(p)
            if not isinstance(rec, dict) or rec.get("schema") != OWNER_DECISION_SCHEMA or rec.get("awaiting_id") != aid:
                continue
            cmd = decides.get(rec["command_id"]) if isinstance(rec.get("command_id"), str) else None
            if cmd is None or cmd["args"].get("awaiting_id") != aid or cmd["args"].get("answer") != rec.get("answer"):
                continue
            out[aid] = {"record": rec, "command": cmd, "path": p}
        return out

    def handler_answers(self):
        """{awaiting id: {"record": {"wait": the item}, "decision", "path"}} — the owner-waits of a veto class
        that the veto HANDLER itself completed (R18, L5-01): the surrogate leaves such an item in $KY_RUN/awaiting
        and kyveto.py never moves one, so this is where an executed veto-class decision has its end. One counts
        only when ALL of this holds, read from the handler's own files and judged by its own rule:
          * DECISIONS_SURROGATE.jsonl can be read line for line (kyveto.load_decisions reports no problem — while
            one exists no decision's state is known) and holds a decision whose every line is of class `veto` and
            names THAT awaiting id;
          * the handler's execute action record for that decision, `<SD id>.execute`, is DONE — a record of the
            veto role's controller or supervisor, of the class executor's kind, naming that decision. A log line
            is never that record: a bare EXECUTED line releases nothing;
          * the decision reads EXECUTED as the handler accepts it (kyveto.first_terminal with that record);
          * the wait is not a hard stop: neither its raiser called it one (class_hint) nor does any line of the
            log about that awaiting id. A hard stop is released by an owner `decide` only (owner_answers()).
        PENDING_VETO, EFFECTIVE, VETOED and FAILED therefore still block, and so does whatever cannot be read:
        unknown is never an answer. `path` is the handler's record — the evidence the release is counted by."""
        log = self.run / "DECISIONS_SURROGATE.jsonl"
        if not log.is_file():
            return {}
        try:
            self.load_siblings()
            history, problems, unusable = self.kv.load_decisions(log)
        except (Refusal, OSError):
            return {}
        if problems:
            return {}
        hard = {line.get("awaiting") for lines in history.values() for line in lines
                if line.get("class") == "hard_stop"}
        out, directory = {}, self.run / "awaiting"
        for did, lines in sorted(history.items()):
            aid = lines[0].get("awaiting")
            if did in unusable or not isinstance(aid, str) or not self.kc.AW_RE.match(aid) or aid in hard \
                    or aid in out or any(line.get("class") != "veto" or line.get("awaiting") != aid for line in lines):
                continue
            try:
                rec = self.ka.load(self.run, did + ".execute")
            except (self.ka.ActionError, OSError):
                continue
            actor = rec.get("actor") if isinstance(rec.get("actor"), dict) else {}
            inputs = rec.get("inputs") if isinstance(rec.get("inputs"), dict) else {}
            if rec["state"] != "DONE" or actor.get("role") != "veto" \
                    or actor.get("holder_kind") not in ("controller", "supervisor") \
                    or not str(rec.get("kind", "")).startswith(VETO_EXECUTE_KIND) or inputs.get("decision_id") != did \
                    or self.kv.first_terminal(lines, True) != "EXECUTED":
                continue
            doc = None
            for path in (directory / (aid + ".json"), directory / AWAITING_DONE / (aid + ".json")):
                doc, _ = read_json(path)
                if isinstance(doc, dict):
                    break
            if not isinstance(doc, dict) or doc.get("class_hint") == "hard_stop":
                continue
            out[aid] = {"record": {"wait": doc}, "decision": did, "path": self.ka.record_path(self.run, did + ".execute")}
        return out

    def wait_answers(self):
        """Every answer an owner-wait can have: the veto handler's completed decision (handler_answers(), R18)
        and the OWNER's `decide` (owner_answers(), R15), which stands before it when both are there."""
        return dict(self.handler_answers(), **self.owner_answers())

    def awaiting_blocks(self, authored=None, scope=None, answers=None):
        """(loop_blocked, blocked item keys, ids) from the owner-waits that are OPEN and UNANSWERED: the files of
        $KY_RUN/awaiting (not of awaiting/done/) that hold this role up (wait_target()) and have no answer of the
        owner beside them. An owner-wait the owner answered, or a veto-class one whose decision the veto handler
        itself completed — wait_answers(), `answers` when the caller has them already — no longer blocks its
        item or its loop and is not counted (R15, R18: an answered wait has an end; the controller closes it,
        and until it has, it is answered all the same).
        An unanswered one blocks, whatever else lies beside it. `authored`, when given, is filled with the ids of
        the items a JOB of this role raised (raised_by.role is this role and raised_by.job_id is set) — they block
        like any other, but a run is never credited with a "changed dependency" for an owner-wait a job wrote
        (N-02). `scope`: see wait_target()."""
        loop_blocked, items, ids = False, set(), []
        answers = self.wait_answers() if answers is None else answers
        directory = self.run / "awaiting"
        for p in sorted(directory.glob("*.json")) if directory.is_dir() else []:
            if p.name.endswith(OWNER_DECISION_SUFFIX):  # the owner's recorded answer beside an item, not an item
                continue
            doc, _ = read_json(p)
            if not isinstance(doc, dict):
                continue
            target = self.wait_target(doc, scope)
            if target is None or p.stem in answers:
                continue
            raised = doc.get("raised_by") if isinstance(doc.get("raised_by"), dict) else {}
            aid = str(doc.get("id", p.stem))
            if target[0] == "loop":
                loop_blocked = True
            else:
                items.add(target[1])
            ids.append(aid)
            if authored is not None and raised.get("role") == self.role and raised.get("job_id") is not None:
                authored.add(aid)
        return loop_blocked, items, sorted(ids)

    def answered_waits(self, scope=None, answers=None):
        """[[awaiting id, sha256 of the owner's decision record]] — the owner-waits of this loop, or of an item
        this role can work on, that the OWNER has answered: a changed dependency, and one no run authored — also
        when a job of this role had raised the wait (R15). Judged by wait_target(), exactly as an open wait is,
        on what the decision record says was asked (`wait`), else on the item itself, open or closed. The same
        for a veto-class wait the veto handler released (R18): there the sha256 is that of the handler's DONE
        execute record."""
        out = []
        for aid, answer in sorted((self.wait_answers() if answers is None else answers).items()):
            doc = answer["record"].get("wait")
            for path in (self.run / "awaiting" / (aid + ".json"), self.run / "awaiting" / AWAITING_DONE / (aid + ".json")):
                if isinstance(doc, dict):
                    break
                doc, _ = read_json(path)
            if isinstance(doc, dict) and self.wait_target(doc, scope) is not None:
                out.append([aid, sha_file(answer["path"])])
        return out

    @staticmethod
    def is_blocked(key, blocked):
        return any(b == key or b.startswith(key + ".") for b in blocked)

    def poll_inboxes(self):
        """Unacked S and steward messages via the tracker CLI (exit 0 = some, 1 = none). Waiting happens here."""
        out = []
        for stream, args in (("S", ["--stream", "S"]), ("steward", ["--steward"])):
            try:
                r = subprocess.run([str(self.root / "bin" / "ky"), "inbox", *args, "--json"], capture_output=True,
                                   text=True, timeout=120, env=dict(os.environ, KY_STREAM="S"))
                msgs = json.loads(r.stdout) if r.returncode == 0 else ([] if r.returncode == 1 else None)
            except (OSError, ValueError, subprocess.SubprocessError):
                msgs = None
            if not isinstance(msgs, list):
                self.event_failures += 1
                self.log("inbox %s could not be read (%d consecutive)" % (stream, self.event_failures))
                if self.event_failures >= EVENT_SOURCE_FAILURE_LIMIT:
                    raise Refusal(["event_source_failed: `ky inbox` unreadable %d times" % self.event_failures])
                return None
            out.extend((stream, m) for m in msgs if isinstance(m, dict))
        self.event_failures = 0
        return out

    def eligible_items(self):
        loop_blocked, blocked, _ = self.awaiting_blocks()
        if self.role == "planner":
            state, err = self.read_role_state()
            if err:
                raise Refusal([err])
            accepted = self.accepted_steps(state)
            if all(step in accepted for step, _ in PLANNER_STEPS):
                self.derive_completion(accepted)
                return []
            items = []
            for step, deps in PLANNER_STEPS:
                if step in accepted or any(d not in accepted for d in deps):
                    continue
                for d in deps:                    # validate the dependency chain of the next action (§4a.1)
                    for ev in accepted[d].get("evidence", []) if isinstance(accepted[d].get("evidence"), list) else []:
                        if isinstance(ev, dict) and ev.get("type") == "file" and sha_file(ev.get("path", "")) != ev.get("sha256"):
                            raise Refusal(["prerequisite_evidence_changed: %s (%s)" % (d, ev.get("path"))])
                if not self.is_blocked(step, blocked):
                    items.append({"id": "step." + step, "kind": "step", "key": step})
            return [] if loop_blocked else items
        msgs = self.poll_inboxes()
        if msgs is None or loop_blocked:
            return []
        items, seen, keys = [], set(), set()
        for stream, m in msgs:
            mid = str(m.get("msg_id", ""))
            if not ID_RE.match(mid) or mid in seen or (self.run / "handled" / ("msg.%s.json" % mid)).exists():
                continue
            keys.add(mid)                       # asked of is_blocked() just below: a wait about it is this role's
            if self.is_blocked(mid, blocked):
                continue
            seen.add(mid)
            items.append({"id": "msg." + mid, "kind": "message", "key": mid, "stream": stream, "message": m})
        self.inbox_keys = keys
        return items[:BATCH_MAX]

    def item_keys(self, items=()):
        """The keys of the items this role can work on — exactly what eligible_items() asks is_blocked() about:
        the Wave B steps (planner), or the unhandled messages of the last inbox poll together with the given
        work items (conductor). An owner-wait about any other item is not a dependency of this role (L3-01)."""
        if self.role == "planner":
            return [step for step, _ in PLANNER_STEPS]
        return sorted(self.inbox_keys | {str(it["key"]) for it in items if isinstance(it, dict) and it.get("key")})

    def verify_wave_b_done(self):
        """WAVE_B_DONE is derived, never believed from a file's existence or from what it says of itself (plan
        §13, L3-02). The marker is re-derived each time it is met: every Wave B step is accepted in the role
        state with the very evidence hash the marker records, the marker binds the current final receipt and the
        current VERSIONS.json, and what derive_completion() itself requires holds NOW (completion_problems():
        a final receipt, VERSIONS.json, a passing normal kyversion.sh). → (True, what was verified) or
        (False, the first thing that does not hold)."""
        marker, _ = read_json(self.run / "WAVE_B_DONE")
        if not isinstance(marker, dict):
            return False, "the marker is not a JSON object"
        steps = [s for s, _ in PLANNER_STEPS]
        state, err = self.read_role_state()
        if err:
            return False, "the role state cannot be read (%s)" % err
        accepted, recorded = self.accepted_steps(state), marker.get("step_evidence")
        if marker.get("steps") != steps or not isinstance(recorded, dict):
            return False, "the marker does not record the evidence of %s" % ", ".join(steps)
        for step in steps:
            if step not in accepted:
                return False, "%s is not accepted in %s" % (step, self.state_path.name)
            if recorded.get(step) != accepted[step]["evidence_sha256"]:
                return False, "the marker's evidence for %s differs from the accepted evidence" % step
        for name, field in (("INSTALL_RECEIPT.json", "final_receipt_sha256"), ("VERSIONS.json", "versions_sha256")):
            now = sha_file(self.run / name)
            if now is None or marker.get(field) != now:
                return False, "the marker does not bind the current %s" % name
        problems = self.completion_problems()
        if problems:
            return False, "; ".join(problems)
        return True, "accepted %s, final receipt %s, kyversion.sh passed" % (", ".join(steps), marker["final_receipt_sha256"][:12])

    def completion_problems(self):
        """What completion needs besides the accepted steps — the ONE list derive_completion() and
        verify_wave_b_done() both judge by: a final installation receipt, VERSIONS.json and a passing normal
        (argument-less) kyversion.sh, which is run only when the files are there (a missing helper is not a pass)."""
        receipt, err = read_json(self.run / "INSTALL_RECEIPT.json")
        problems = []
        if err or not isinstance(receipt, dict) or receipt.get("mode") != "final":
            problems.append("INSTALL_RECEIPT.json is not a final receipt")
        if not (self.run / "VERSIONS.json").is_file():
            problems.append("VERSIONS.json is absent")
        if not problems:
            rc = self.run_helper("kyversion.sh", [], 300)
            if rc != 0:
                problems.append("normal kyversion.sh did not pass (rc=%s)" % rc)
        return problems

    def derive_completion(self, accepted):
        problems = self.completion_problems()
        if problems:
            raise Refusal(["completion_unverified: B-3, B-4 and B-5 are recorded as accepted but " + "; ".join(problems)])
        steps = [s for s, _ in PLANNER_STEPS]
        write_json(self.run / "WAVE_B_DONE", {
            "schema": "ky.wave_b_done/1", "derived_at": utc(), "derived_by": self.controller_id, "steps": steps,
            "step_evidence": {s: accepted[s]["evidence_sha256"] for s in steps},
            "final_receipt_sha256": sha_file(self.run / "INSTALL_RECEIPT.json"),
            "versions_sha256": sha_file(self.run / "VERSIONS.json")})
        self.log("WAVE_B_DONE derived from accepted B-3…B-5 evidence and the final receipt")

    # ---- progress and breaker evidence
    def dependency_fingerprint(self, external_only=False, keys=None):
        """A digest of the external dependencies a run may be waiting for: the open, unanswered owner-waits that
        block this loop or an item this role can work on (`keys`, default item_keys() — never another role's wait
        for another item, L3-01), the owner's ANSWERS to such waits (answered_waits(), R15), the installation
        receipt, the manifests, the owner's resume, the release receipt and the activation chain. With
        `external_only`, owner-waits a job of this role raised are left out: a run that only wrote an owner-wait
        has changed nothing it did not author (N-02). The owner's answer to such a wait stays in: no run authors
        that."""
        authored, answers = set(), self.wait_answers()
        scope = self.item_keys() if keys is None else keys
        _, _, ids = self.awaiting_blocks(authored, scope=scope, answers=answers)
        parts = {"awaiting": [i for i in ids if i not in authored] if external_only else ids,
                 "answered": self.answered_waits(scope, answers)}
        for name in ("INSTALL_RECEIPT.json", "VERSIONS.bootstrap.json", "VERSIONS.json", "OWNER_RESUME.json",
                     "RELEASE_RECEIPT.json"):
            parts[name] = sha_file(self.run / name)
        parts["activation_chain"] = [[p.name, sha_file(p)] for p in sorted(self.run.glob("ACTIVATION_RECORD*.json"))]
        return sha_bytes(json.dumps(parts, sort_keys=True).encode())

    def substep_evidence(self):
        """What must differ before an item that reached its sub-step cap is credited with sub-steps again: the
        external dependencies no job authored and the owner's recorded answers — never accepted sub-steps
        themselves (N-01)."""
        return sha_bytes(json.dumps({"dependencies": self.dependency_fingerprint(external_only=True),
                                     "owner_decisions": self.owner_decisions()}, sort_keys=True).encode())

    def owner_decisions(self):
        """[[file name, sha256]] of the owner's answers this role applied (`decide` commands): recorded evidence."""
        out, directory = [], self.run / "awaiting"
        for p in sorted(directory.glob("*" + OWNER_DECISION_SUFFIX)) if directory.is_dir() else []:
            doc, _ = read_json(p)
            by = doc.get("applied_by") if isinstance(doc, dict) else None
            if isinstance(by, dict) and by.get("role") == self.role:
                out.append([p.name, sha_file(p)])
        return out

    def accepted_summary(self, keys=None):
        """Accepted work and the two dependency fingerprints, taken over `keys` (default item_keys()). The keys
        are part of the summary: a run's "after" is taken over the keys of its "before", so that the two differ
        only when a dependency of this role did (L3-01)."""
        state, _ = read_json(self.state_path)
        ids = sorted(self.accepted_steps(state)) if isinstance(state, dict) else []
        keys = self.item_keys() if keys is None else sorted(str(k) for k in keys)
        return {"accepted_count": len(ids), "accepted_digest": sha_bytes("\n".join(ids).encode()),
                "item_keys": keys,
                "dependency_fingerprint": self.dependency_fingerprint(keys=keys),
                "external_fingerprint": self.dependency_fingerprint(external_only=True, keys=keys)}

    def evidence_fingerprint(self):
        """What must change before an open breaker may be reopened: accepted work, external dependencies,
        the installed bundle inputs, the set of actionable items, or the owner's recorded answer (`decide`)."""
        cfg, _ = self.load_config()
        try:
            items = [i["id"] for i in self.eligible_items()] if self.role == "conductor" else None
        except Refusal:
            items = None
        parts = {"progress": self.accepted_summary(), "items": items, "claude_version": self.read_claude_version()[0],
                 "prompt": sha_file(self.fleet / "prompts" / PROMPTS[self.role]),
                 "loops_json": sha_file(self.run / "loops.json"),
                 "mcp": sha_file(cfg["mcp_config"]) if cfg else None,
                 "qualification": sha_file(self.qualification_path(cfg)) if cfg else None,
                 "owner_decisions": self.owner_decisions()}
        return sha_bytes(json.dumps(parts, sort_keys=True).encode())

    def open_breaker(self, count):
        fingerprint = self.evidence_fingerprint()
        doc = self.write_awaiting(
            "loop-%s-no-progress" % self.role,
            "The %s loop made no progress in %d consecutive runs and stopped itself. Progress means an accepted "
            "checkpoint or a changed external dependency. What should change before it runs again?" % (self.role, count),
            [{"id": "change-and-restart", "text": "Change the blocking condition (evidence must differ from the "
                                                  "recorded fingerprint), then `kyctl.sh start %s --clear-stop`." % self.role},
             {"id": "keep-stopped", "text": "Leave the %s loop stopped." % self.role}],
            "change-and-restart",
            ["breaker: %d consecutive no-progress runs; evidence fingerprint %s" % (count, fingerprint),
             "run records: %s" % self.loop_dir])
        self.ensure_stop("circuit breaker open")

        def fn(d):
            br = d.get("breaker") if isinstance(d.get("breaker"), dict) else {}
            br.update(open=True, opened_at=utc(), evidence_fingerprint=fingerprint, awaiting=doc)
            br.setdefault("history", [])
            d["breaker"] = br
            d.update(enabled=False, reason="circuit breaker open: %d no-progress runs" % count, updated_at=utc(),
                     updated_by=self.controller_id)
            return d
        self.ls(fn)
        self.notify("%s loop stopped: %d consecutive no-progress runs; see %s" % (self.role, count, doc["id"]), "decision")

    def breaker_gate(self, st):
        """True → refused (unchanged evidence). Reopening requires recorded changed evidence — also when the
        surrogate or the owner decided to restart. The decision reads the no-progress COUNT itself (N-09): a
        controller that died between recording the third no-progress run and opening the breaker opens it here,
        before anything is launched."""
        br = st.get("breaker") if isinstance(st.get("breaker"), dict) else {}
        if not br.get("open"):
            count = as_int(st.get("no_progress_count"))
            if count < NO_PROGRESS_LIMIT:
                return False
            self.log("%d consecutive no-progress runs are recorded and the breaker is not open: opening it now"
                     % count)
            self.open_breaker(count)
            return True
        now_fp = self.evidence_fingerprint()
        if now_fp == br.get("evidence_fingerprint"):
            self.log("breaker open since %s and evidence unchanged — restart refused" % br.get("opened_at"))
            doc = br.get("awaiting") if isinstance(br.get("awaiting"), dict) else None
            if doc and ID_RE.match(str(doc.get("id", ""))) and not (self.run / "awaiting" / (doc["id"] + ".json")).exists():
                os.makedirs(self.run / "awaiting", exist_ok=True)
                write_json(self.run / "awaiting" / (doc["id"] + ".json"), doc)     # same id: no new owner-wait
            self.ensure_stop("circuit breaker open; evidence unchanged")
            self.disable("circuit breaker open; evidence unchanged", force=True)
            return True

        def fn(d):
            b = d.get("breaker") if isinstance(d.get("breaker"), dict) else {}
            hist = (b.get("history") or []) + [{"at": utc(), "from": b.get("evidence_fingerprint"), "to": now_fp,
                                                "by": self.controller_id}]
            d["breaker"] = {"open": False, "history": hist[-20:]}
            d["no_progress_count"] = 0
            return d
        self.ls(fn)
        self.log("breaker reopened: recorded evidence changed")
        return False

    # ---- the owner's command queue (plan §4a.1, §4a.5): applied by the fenced role owner, in order, exactly once
    def apply_commands(self):
        """Settle this role's QUEUED commands in filename order through kycommands.apply (this controller is the
        fenced owner of the role lock). The conductor also settles the `campaign` role's commands, holding
        locks/campaign only for the application. → True when at least one command was settled (the caller then
        re-evaluates every gate from the top). self.commands_blocked says why one could not be settled yet."""
        kc, ka, settled = self.kc, self.ka, False
        self.commands_blocked = None
        for role in ((self.role, "campaign") if self.role == "conductor" else (self.role,)):
            try:
                queue = kc.pending(self.run, role)
            except (kc.CommandError, OSError) as e:
                raise Refusal(["command_queue_error: %s: %s" % (type(e).__name__, flat(e, 160))])
            if not queue:
                continue
            campaign = None
            if role == "campaign":
                try:
                    campaign = ka.acquire_lock(self.run, "campaign", self.controller_id, log=self.log_once)
                except ka.LockUnknown as e:      # never taken over: the command waits, and somebody is told
                    self.lock_attention("campaign", e)
                    self.commands_blocked = "campaign_lock_owner_unknown"
                    continue
                except (ka.ActionError, OSError) as e:
                    raise Refusal(["command_queue_error: locks/campaign: %s" % type(e).__name__])
                if campaign is None:
                    self.commands_blocked = "campaign_lock_held"
                    continue
            try:
                for doc in queue:
                    if not self.apply_one(role, doc):
                        break                   # order is kept: nothing later is applied past a blocked command
                    settled = True
            finally:
                if campaign is not None:
                    ka.release_lock(campaign)
        self.close_answered_waits()             # R15: an answered owner-wait an earlier look could not close
        return settled

    def apply_one(self, role, doc, in_order=True):
        """→ True when the command is settled (APPLIED or REJECTED, now or earlier); False when it has to wait.
        `in_order=False` (kycommands.apply) is the veto role's: its commands have independent targets."""
        kc, ka, cid = self.kc, self.ka, doc.get("id")
        args = doc.get("args") if isinstance(doc.get("args"), dict) else {}
        item = None
        if role == self.role and doc.get("command") == "decide" and isinstance(args.get("awaiting_id"), str) \
                and kc.AW_RE.match(args["awaiting_id"]):
            # §4a.6: an awaiting item is locked by its id before it is acted on; the handler re-reads it afterwards
            try:
                item = ka.acquire_lock(self.run, "awaiting." + args["awaiting_id"], self.controller_id,
                                       log=self.log_once)
            except ka.LockUnknown as e:
                self.lock_attention("awaiting." + args["awaiting_id"], e)
                self.commands_blocked = "awaiting_item_lock_owner_unknown: %s" % args["awaiting_id"]
                return False
            except (ka.ActionError, OSError) as e:
                raise Refusal(["command_queue_error: %s: %s" % (cid, type(e).__name__)])
            if item is None:
                self.commands_blocked = "awaiting_item_locked: %s" % args["awaiting_id"]
                return False
        self.own_actions.add("CMD-%s" % cid)
        try:
            status, out = kc.apply(self.run, cid, self.controller_id, lambda cmd: self.handle_command(role, cmd),
                                   observer=lambda record: self.observe_command(role, record),
                                   in_order=in_order, log=self.log_once)
        except ka.LockBusy:
            self.commands_blocked = "action_record_busy: CMD-%s" % cid
            return False
        except ka.LockUnknown as e:
            self.lock_attention(getattr(e, "name", "CMD-%s" % cid), e)
            self.commands_blocked = "lock_owner_unknown: CMD-%s" % cid
            return False
        except (kc.CommandError, ka.ActionError, OSError) as e:
            raise Refusal(["command_queue_error: %s: %s: %s" % (cid, type(e).__name__, flat(e, 160))])
        finally:
            if item is not None:
                ka.release_lock(item)
        if status in ("applied", "rejected", "already_applied", "already_rejected"):
            state = out.get("state")
            reason = (out.get("result") or {}).get("reason") if state == "REJECTED" else None
            self.log("command %s (%s → %s): %s%s" % (cid, doc.get("command"), role, state,
                                                     " — " + flat(reason, 160) if reason else ""))

            def fn(d):
                c = dict(d.get("commands") or {})
                key = "applied" if state == "APPLIED" else "rejected"
                c[key] = as_int(c.get(key)) + (status in ("applied", "rejected"))
                c["last"] = {"id": cid, "command": doc.get("command"), "role": role, "state": state, "at": utc(),
                             "reason": reason}
                d["commands"] = c
                return d
            self.ls(fn)
            return True
        reason = str(out.get("reason"))
        if status == "locked" or reason.startswith("earlier_command_pending"):
            self.commands_blocked = "%s: %s" % (cid, reason)
            return False
        if out.get("attention") and reason.startswith("command_lock_owner_unknown"):
            # the command's own lock has an owner nobody can judge: never taken over — it waits, and someone is told
            self.lock_attention("command." + str(cid), reason)
            self.commands_blocked = "%s: %s" % (cid, reason)
            return False
        if status == "unreconciled":            # an earlier application died inside its handler and cannot be observed
            raise Refusal(["command_unreconciled: %s (%s) — unknown, not repeated" % (out.get("action_id"), reason)])
        raise Refusal(["command_application_refused: %s (%s)" % (cid, reason)])     # this controller is not the fenced owner

    def handle_command(self, role, cmd):
        """The handler kycommands.apply calls once: → the result object, or Reject(reason) for anything this role
        cannot carry out. Every effect is one atomic write tagged with the command id (see observe_command)."""
        Reject = self.kc.Reject
        name, cid = cmd.get("command"), cmd["id"]
        args = cmd.get("args") if isinstance(cmd.get("args"), dict) else {}
        if role == "campaign":
            if name in ("pause", "resume"):     # the APPLIED record itself is the pause history kycommands reads
                return {"campaign": "paused" if name == "pause" else "resumed", "applied_by": self.controller_id}
            raise Reject("unsupported_by_campaign_role: %s (the campaign role takes pause and resume only)" % name)
        if name == "status" or (name == "loops" and args.get("op") == "status" and args.get("loop") == self.role):
            return self.status_facts()
        if name == "loops":
            if args.get("loop") != self.role:
                raise Reject("not_this_roles_loop: the %s controller stops and reports only its own loop, not %r"
                             % (self.role, args.get("loop")))
            if args.get("op") == "stop":
                self.command_disable(cid, "owner command %s: loops stop %s" % (cid, self.role))
                return {"loop": self.role, "enabled": False}
            raise Reject("loops_start_not_applicable: this controller is already running; a stopped loop is started "
                         "with `kyctl.sh start %s` and its guards" % self.role)
        if name == "handoff":
            state = self.command_state()
            last = self.ls().get("last_run_id")
            state["handoff"] = {"command_id": cid, "requested_by": cmd.get("from"), "requested_at": cmd.get("created_at"),
                                "applied_at": utc(), "controller_id": self.controller_id, "last_run_id": last,
                                "accepted_steps": len(self.accepted_steps(state))}
            self.write_role_state(state)
            journal = self.journal_path.read_text(encoding="utf-8") if self.journal_path.exists() else ""
            if cid not in journal:
                with open(self.journal_path, "a", encoding="utf-8") as j:
                    j.write("- %s controller %s · handoff requested by owner command %s · last run %s · loop disabled\n"
                            % (utc(), self.controller_id, cid, last or "-"))
            self.command_disable(cid, "handoff requested by owner command %s" % cid)
            return {"loop": self.role, "enabled": False, "last_run_id": last}
        if name in ("priority", "builders", "verifiers"):
            state = self.command_state()
            directives = state.setdefault("owner_directives", {})
            if not isinstance(directives, dict) or not isinstance(directives.get("priority", []), list):
                raise Reject("role_state_owner_directives_malformed")
            entry = {"command_id": cid, "at": utc(), "from": (cmd.get("from") or {}).get("session_id")}
            if name == "priority":
                if not any(isinstance(x, dict) and x.get("command_id") == cid for x in directives.get("priority", [])):
                    directives.setdefault("priority", []).append(dict(entry, item=args.get("item")))
            else:
                directives[name] = dict(entry, n=args.get("n"))
            self.write_role_state(state)        # the next job's snapshot carries it; a child never writes this file
            return {"recorded": name, "role_state": self.state_path.name}
        if name == "decide":
            return self.record_owner_decision(cmd, args)
        raise Reject("unsupported_by_%s_role: %s" % (self.role, name))

    def record_owner_decision(self, cmd, args):
        """`decide` (R15): an answered owner-wait has an end. In this order, under the command's ONE action record
        (CMD-<id>, kycommands.apply):
          1. the owner's answer goes beside the awaiting item as <id>.owner_decision.json — exclusively, once,
             read-only — together with what was asked (`wait`), so that a job can read both after the item is
             closed. From then on the wait no longer blocks (owner_answers(), awaiting_blocks());
          2. for the item this controller raised for a job action it could not observe, the chosen option is
             carried out (settle_job_action());
          3. the item is closed: moved to awaiting/done/ (move_to_done()).
        It is changed evidence for this role: the no-progress count starts again, the breaker and the sub-step
        window read the answer, and the dependency fingerprints carry it (answered_waits()).

        A controller that dies after step 1 leaves the command QUEUED and its action record unfinished: the next
        one is asked what became of it (observe_command — done only once the item is closed), runs this handler
        again, finds its own record — no second one is ever written — and completes steps 2 and 3. Once the record
        is written nothing here raises: the command reads APPLIED, its result says what could not be completed
        (`closed: null`, `close_error`), and close_answered_waits() finishes that at a later look.

        Rejected, with nothing written: an item that is not open or cannot be read; one that is not this role's
        (neither raised by this role, nor about its loop, nor about an item it works on — the role a wait holds
        up answers for it, whoever raised it); one the owner has answered already; and, for a job-action item,
        an answer that names none of its options. A record lying beside the item that is NOT the owner's answer
        never stands in the owner's way: it is kept, set aside under awaiting/done/."""
        Reject, cid, aid = self.kc.Reject, cmd["id"], args.get("awaiting_id")
        if not isinstance(aid, str) or not self.kc.AW_RE.match(aid):
            raise Reject("awaiting_item_not_open: no usable awaiting id")
        path = self.run / "awaiting" / (aid + ".json")
        out = path.with_name(aid + OWNER_DECISION_SUFFIX)
        existing, eerr = read_json(out)
        mine = isinstance(existing, dict) and existing.get("schema") == OWNER_DECISION_SCHEMA \
            and (existing.get("command_id"), existing.get("awaiting_id"), existing.get("answer")) \
            == (cid, aid, args.get("answer"))               # this very command wrote it, in an earlier application
        answered = None if mine else self.owner_answers().get(aid)
        already = "awaiting_item_already_answered: %s by command %s" % (
            aid, answered["record"].get("command_id") if answered else "?")
        doc, err = read_json(path)                          # the fresh look, under the item's lock
        if err == "missing":
            if mine:                                        # … and got as far as closing the item: nothing is left
                closed = path.parent / AWAITING_DONE / path.name
                return {"awaiting_id": aid, "owner_decision": str(out), "sha256": sha_file(out),
                        "closed": str(closed) if closed.is_file() else None, "reconciled": True}
            raise Reject(already if answered else "awaiting_item_not_open: %s" % aid)
        if err or not isinstance(doc, dict):
            raise Reject("awaiting_item_unreadable: %s" % aid)
        raised = doc.get("raised_by") if isinstance(doc.get("raised_by"), dict) else {}
        if doc.get("item") != "loop.%s" % self.role and raised.get("role") != self.role \
                and self.wait_target(doc, self.item_keys()) is None:
            raise Reject("not_this_roles_item: %s was raised by %r for %r; address the role that owns it"
                         % (aid, raised.get("role"), doc.get("item")))
        if answered:
            raise Reject(already)
        if self.job_action_of(aid, doc) is not None and self.chosen_option(args.get("answer")) is None:
            raise Reject("answer_not_an_option: %s is the item of a job action this controller could not observe; "
                         "answer with one of its options: %s" % (aid, " | ".join(JOB_ACTION_OPTIONS)))
        result = {"awaiting_id": aid, "owner_decision": str(out)}
        if not mine:
            if eerr != "missing":                           # something lies there, and it is not the owner's answer
                try:
                    result["set_aside"] = str(self.archive(
                        out, "%s.owner_decision.set_aside.%s" % (aid, utc("%Y%m%dT%H%M%SZ"))))
                except OSError as e:
                    raise Reject("stray_decision_record_in_the_way: %s is not the owner's answer and could not be "
                                 "set aside (%s)" % (out.name, type(e).__name__))
                self.log("%s was not the owner's answer to %s: set aside as %s" % (out.name, aid, result["set_aside"]))
            existing = {"schema": OWNER_DECISION_SCHEMA, "awaiting_id": aid, "answer": args.get("answer"),
                        "command_id": cid, "from": cmd.get("from"), "command_created_at": cmd.get("created_at"),
                        "applied_at": utc(), "applied_by": {"role": self.role, "controller_id": self.controller_id},
                        "awaiting_sha256": sha_file(path),
                        "wait": {k: doc.get(k) for k in ("item", "blocks", "class_hint", "raised_by", "question",
                                                         "options", "recommendation", "deadline")}}
            text = json.dumps(existing, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
            if not self.ka.write_exclusive(out, text, mode=0o444):
                raise Reject("awaiting_item_already_answered: %s (a decision record appeared beside it)" % aid)
        result["sha256"] = sha_file(out)
        # the owner's answer stands: from here on nothing raises, and the result says what was not completed
        result.update(self.close_answered_wait(aid, doc, existing))
        try:
            self.ls(lambda d: dict(d, no_progress_count=0,
                                   evidence_changed={"at": utc(), "by": "command:" + cid, "awaiting_id": aid}))
        except Exception as e:
            result["loop_state"] = "not updated (%s)" % type(e).__name__
            self.log("the owner's answer to %s is recorded; the loop state was not updated (%s)" % (aid, type(e).__name__))
        return result

    # ---- closing an answered owner-wait (R15): the chosen option of a job-action item, then the move
    @staticmethod
    def job_action_slug(action_id):
        """The slug of the ONE awaiting item raised for a job's action record nobody could observe."""
        return JOB_ACTION_SLUG + re.sub(r"[^a-z0-9-]", "-", action_id.lower())

    @staticmethod
    def chosen_option(answer):
        """The option of a job-action item an answer names: its id, alone or before a colon (`happened`,
        `did-not-happen: no PR was opened`), in any case; None for anything else."""
        head = answer.split(":", 1)[0].strip().lower() if isinstance(answer, str) else ""
        return head if head in JOB_ACTION_OPTIONS else None

    def job_action_of(self, aid, doc):
        """The id of the job's action record an awaiting item is about, when the item is the one a controller of
        THIS role raised for a job action it could not observe (reconcile_job_record()); else None. The item
        names the record in its evidence (`action: <id>`); it is taken for such an item only when a controller of
        this role raised it, its own id carries the job-action slug of exactly that record, and the record id
        lies in a job namespace of this role."""
        raised = doc.get("raised_by") if isinstance(doc.get("raised_by"), dict) else {}
        if raised.get("role") != self.role or not str(raised.get("session_id", "")).startswith("CTL-") \
                or raised.get("job_id") is not None:
            return None
        for line in doc.get("evidence") if isinstance(doc.get("evidence"), list) else []:
            if isinstance(line, str) and line.startswith("action: "):
                action_id = line[len("action: "):]
                if action_id.startswith("JOB-%s-" % self.ROLE) and re.fullmatch(
                        r"AW-[0-9]{8}T[0-9]{6}Z-" + re.escape(self.job_action_slug(action_id)), aid):
                    return action_id
        return None

    def settle_job_action(self, action_id, aid, record):
        """Carry out the option the owner chose for a job action this controller could not observe: `happened`
        settles the job's record as DONE, `did-not-happen` as FAILED (the next job may then do it under a record
        of its own) — on the owner's word, and the result says so (settled_by: owner_decision, observed: false).
        Idempotent: a record that is settled already, or that is not there, is left as it is.
        → {"action_id", "state", "settled"}. A record that cannot be read or updated right now raises what
        kyaction raises: the caller leaves the item open and comes back (close_answered_waits())."""
        ka, option = self.ka, self.chosen_option(record.get("answer"))
        try:
            rec = ka.load(self.run, action_id)
        except ka.ActionUnreadable:
            raise
        except ka.ActionError:
            return {"action_id": action_id, "state": None, "settled": "no_record"}
        actor = rec.get("actor") if isinstance(rec.get("actor"), dict) else {}
        if actor.get("role") != self.role or not ka.is_job_record(rec, actor.get("run_id")):
            return {"action_id": action_id, "state": rec["state"], "settled": "not_a_job_record_of_this_role"}
        if rec["state"] != "INTENDED":
            return {"action_id": action_id, "state": rec["state"], "settled": "already_settled"}
        if option is None:
            return {"action_id": action_id, "state": rec["state"], "settled": "no_option_named"}
        result = {"settled_by": "owner_decision", "awaiting_id": aid, "command_id": record.get("command_id"),
                  "answer": option, "observed": False}
        after = (ka.complete if option == JOB_ACTION_OPTIONS[0] else ka.fail)(self.run, action_id, result)
        self.log("job action %s settled as %s on the owner's answer to %s (%s)" % (action_id, after["state"], aid, option))
        return {"action_id": action_id, "state": after["state"], "settled": option}

    def archive(self, src, stem):
        """Move the file `src` to $KY_RUN/awaiting/done/<stem>.json in one rename that never replaces a file (when
        that name is taken: <stem>.<UTC>[.n].json). Nothing under awaiting/done/ is ever read as an open item or
        as an answer. → the path it lies at now."""
        done = self.run / "awaiting" / AWAITING_DONE
        os.makedirs(done, exist_ok=True)
        dst = done / (stem + ".json")
        for n in range(1, 100):
            try:
                rename_exclusive(src, dst)
                return dst
            except FileExistsError:
                dst = done / ("%s.%s%s.json" % (stem, utc("%Y%m%dT%H%M%SZ"), "" if n == 1 else ".%d" % n))
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(dst))

    def move_to_done(self, aid):
        """Close an owner-wait: $KY_RUN/awaiting/<id>.json → awaiting/done/<id>.json, never deleted and never
        onto another file. → where it lies now; None when there was nothing to move and nothing closed. An open
        item that is byte for byte the closed one of that name (a breaker item written back under its old id) is
        a duplicate: removed."""
        src = self.run / "awaiting" / (aid + ".json")
        dst = src.parent / AWAITING_DONE / src.name
        if not os.path.lexists(src):
            return str(dst) if dst.is_file() else None
        if dst.is_file() and sha_file(src) is not None and sha_file(src) == sha_file(dst):
            os.unlink(src)
            return str(dst)
        return str(self.archive(src, aid))

    def close_answered_wait(self, aid, doc, record, answered="The owner's answer to %s is recorded"):
        """Steps 2 and 3 of an applied `decide` for the open item `doc` and the owner's decision `record`:
        idempotent, and total — it never raises. → {"closed": where the item lies now | None[, "close_error"]
        [, "job_action"]}. An option that could not be carried out leaves the item where it is (answered, so it
        blocks nothing), for the next look to finish both. `answered` says, in the one notice a failed close
        raises, what released the wait (R18: the veto handler's executed decision rather than an owner answer)."""
        out = {"closed": None}
        try:
            action_id = self.job_action_of(aid, doc)
            if action_id is not None:
                out["job_action"] = self.settle_job_action(action_id, aid, record)
            out["closed"] = self.move_to_done(aid)
        except Exception as e:
            out["close_error"] = "%s: %s" % (type(e).__name__, flat(e, 160))
            self.log_once("owner-wait %s is answered but could not be closed (%s): it blocks nothing, and is closed "
                          "at a later look" % (aid, out["close_error"]))
            self.raise_attention(
                "loop-%s-answered-wait-not-closed" % self.role,
                "%s, but the %s controller could not close the item (%s). It "
                "blocks nothing, yet it still lies in run/awaiting as if it were open; the controller tries again "
                "at every look. Repair what keeps it there?" % (answered % aid, self.role, out["close_error"]),
                ["item: %s" % (self.run / "awaiting" / (aid + ".json")),
                 "closed items go to: %s" % (self.run / "awaiting" / AWAITING_DONE),
                 "error: %s" % out["close_error"]],
                options=[{"id": "repair", "text": "Repair the named directory or record; the item is then closed "
                                                  "by itself."},
                         {"id": "acknowledge", "text": "Seen; nothing further."}],
                message="%s loop: an answered owner-wait could not be closed (%s)" % (self.role, aid))
        return out

    def close_answered_waits(self):
        """What an applied `decide` could not finish is finished here, at every look at the queue (R15): each
        owner-wait still in $KY_RUN/awaiting that the OWNER answered through this role — the command reads
        APPLIED and this role applied it — is closed now, under the item's lock (close_answered_wait()). One
        whose command is still QUEUED is left to that command's own action record (apply_one). Never raises."""
        if self.ka is None:
            return
        try:
            for aid, answer in sorted(self.owner_answers().items()):
                by, path = answer["record"].get("applied_by"), self.run / "awaiting" / (aid + ".json")
                if answer["command"]["state"] != "APPLIED" or not isinstance(by, dict) or by.get("role") != self.role \
                        or not path.is_file():
                    continue
                try:
                    lock = self.ka.acquire_lock(self.run, "awaiting." + aid, self.controller_id, log=self.log_once)
                except self.ka.LockUnknown as e:
                    self.lock_attention("awaiting." + aid, e)
                    continue
                if lock is None:
                    continue
                try:
                    doc, _ = read_json(path)                # the fresh look, under the item's lock
                    if isinstance(doc, dict):
                        self.close_answered_wait(aid, doc, answer["record"])
                finally:
                    self.ka.release_lock(lock)
        except Exception as e:
            self.log("answered owner-waits were not closed at this look (%s: %s)" % (type(e).__name__, flat(e, 160)))
        self.close_executed_waits()

    def close_executed_waits(self):
        """R18: each owner-wait still in $KY_RUN/awaiting that the veto handler released (handler_answers()) and
        that is THIS role's — about its loop, raised by it, or about an item it works on: the role a wait holds
        up closes it, as it answers for it (record_owner_decision) — is moved to awaiting/done/ now, under the
        item's lock and under ONE action record of this controller, AWCLOSE-<awaiting id>. Idempotent, and the
        crash window is R15's: a record a dead controller left begun is found again here (`unfinished`) and
        completed under the same id, moved or not (move_to_done() says where the item lies); reconcile_each()
        never refuses a launch over it. A move that fails leaves the record open and the item where it is —
        released, so it blocks nothing — tells somebody once, and is tried again at every look. The first close
        is changed evidence for this role, as an applied `decide` is. Never raises."""
        if self.ka is None:
            return
        try:
            released = sorted(self.handler_answers().items())
        except Exception as e:
            self.log("executed veto-class waits were not looked at (%s: %s)" % (type(e).__name__, flat(e, 160)))
            return
        for aid, answer in released:
            path, lock = self.run / "awaiting" / (aid + ".json"), None
            try:
                if not path.is_file():
                    continue
                lock = self.ka.acquire_lock(self.run, "awaiting." + aid, self.controller_id, log=self.log_once)
                if lock is None:
                    continue
                doc, _ = read_json(path)                    # the fresh look, under the item's lock
                raised = doc.get("raised_by") if isinstance(doc, dict) and isinstance(doc.get("raised_by"), dict) else {}
                if not isinstance(doc, dict) or doc.get("class_hint") == "hard_stop" or (
                        doc.get("item") != "loop.%s" % self.role and raised.get("role") != self.role
                        and self.wait_target(doc, self.item_keys()) is None):
                    continue
                did = answer["decision"]
                status, _ = self.begin_own(
                    WAIT_CLOSE_PREFIX + aid, WAIT_CLOSE_KIND, {"awaiting_id": aid, "decision_id": did},
                    {"awaiting": path.name}, "close owner-wait %s: awaiting/ → awaiting/%s/" % (aid, AWAITING_DONE))
                if status == "in_progress":                 # another live controller is closing it right now
                    continue
                closed = self.close_answered_wait(
                    aid, {}, {}, "The veto handler executed " + did + " for %s").get("closed")
                if closed is None or status in ("done", "failed"):
                    continue
                self.ka.complete(self.run, WAIT_CLOSE_PREFIX + aid, {
                    "closed": closed, "released_by": did + ".execute",
                    "execute_record_sha256": sha_file(answer["path"])})
                self.log("owner-wait %s closed: the veto handler executed %s for it" % (aid, did))
                self.ls(lambda d: dict(d, no_progress_count=0,
                                       evidence_changed={"at": utc(), "by": "veto:" + did, "awaiting_id": aid}))
            except self.ka.LockUnknown as e:
                self.lock_attention("awaiting." + aid, e)
            except Exception as e:
                self.log_once("executed veto-class wait %s was not closed at this look (%s: %s)"
                              % (aid, type(e).__name__, flat(e, 160)))
            finally:
                if lock is not None:
                    self.ka.release_lock(lock)

    def observe_wait_close(self, record):
        """kyaction observer for an AWCLOSE record an earlier controller left begun: the item lies under
        awaiting/done/ and no longer in awaiting/ → done; otherwise not_done — close_executed_waits() then
        completes it under the same record."""
        aid = (record.get("inputs") or {}).get("awaiting_id") if isinstance(record.get("inputs"), dict) else None
        if not isinstance(aid, str) or not ID_RE.match(aid):
            return "unknown", {"reason": "the record names no awaiting id"}
        src = self.run / "awaiting" / (aid + ".json")
        dst = src.parent / AWAITING_DONE / src.name
        if dst.is_file() and not os.path.lexists(src):
            return "done", {"closed": str(dst), "reconciled": True}
        return "not_done", {"open": os.path.lexists(src), "closed": dst.is_file()}

    def observe_command(self, role, record):
        """kyaction observer for a command whose earlier application died inside its handler: did the handler's
        one tagged write happen? ("done" / "not_done"); what cannot be read is "unknown" and is never repeated."""
        inputs = record.get("inputs") if isinstance(record.get("inputs"), dict) else {}
        target = record.get("target") if isinstance(record.get("target"), dict) else {}
        name, cid = inputs.get("command"), target.get("command_id")
        args = inputs.get("args") if isinstance(inputs.get("args"), dict) else {}
        actor = record.get("actor") if isinstance(record.get("actor"), dict) else {}
        if actor.get("holder_kind") != "controller":       # a cockpit's own handler: its effects are not ours to read
            return "unknown", {"reason": "begun by a %s, whose handler this controller cannot observe"
                                         % actor.get("holder_kind")}
        loop, lerr = read_json(self.run / "loops" / (self.role + ".json"))
        state, serr = read_json(self.state_path)
        disabled = isinstance(loop, dict) and loop.get("enabled") is False and loop.get("disabled_by_command") == cid
        if role == "campaign" or name == "status" or (name == "loops" and args.get("op") != "stop"):
            return "not_done", {"note": "this command's handler writes nothing of its own"}
        if name == "loops":
            if lerr and lerr != "missing":
                return "unknown", {"error": "loop state %s" % lerr}
            return ("done", {"loop": self.role, "enabled": False, "reconciled": True}) if disabled \
                else ("not_done", {"disabled_by_command": False})
        if name in ("handoff", "priority", "builders", "verifiers"):
            if serr == "missing":
                return "not_done", {"role_state": "missing"}
            if serr or not isinstance(state, dict):
                return "unknown", {"error": "role state %s" % (serr or "not an object")}
            if name == "handoff":
                mine = isinstance(state.get("handoff"), dict) and state["handoff"].get("command_id") == cid
                return ("done", {"loop": self.role, "enabled": False, "reconciled": True}) if mine and disabled \
                    else ("not_done", {"handoff_recorded": mine, "disabled": disabled})
            directives = state.get("owner_directives") if isinstance(state.get("owner_directives"), dict) else {}
            entries = directives.get("priority", []) if name == "priority" else [directives.get(name)]
            found = any(isinstance(x, dict) and x.get("command_id") == cid for x in entries or [])
            return ("done", {"recorded": name, "role_state": self.state_path.name, "reconciled": True}) if found \
                else ("not_done", {"recorded": False})
        if name == "decide" and isinstance(args.get("awaiting_id"), str) and self.kc.AW_RE.match(args["awaiting_id"]):
            # R15: a `decide` is done when its decision record is written AND the item is closed. A record of this
            # command beside an item that is still open is the crash window: not_done — the handler runs again
            # under the same action record, finds its own record (no second one) and completes the rest.
            item = self.run / "awaiting" / (args["awaiting_id"] + ".json")
            out = item.with_name(args["awaiting_id"] + OWNER_DECISION_SUFFIX)
            existing, err = read_json(out)
            if err and err != "missing":
                return "unknown", {"error": "owner decision %s" % err}
            if isinstance(existing, dict) and existing.get("command_id") == cid:
                if os.path.lexists(item):
                    return "not_done", {"owner_decision": "written", "closed": False}
                closed = item.parent / AWAITING_DONE / item.name
                return "done", {"awaiting_id": args["awaiting_id"], "owner_decision": str(out),
                                "sha256": sha_file(out), "closed": str(closed) if closed.is_file() else None,
                                "reconciled": True}
        return "not_done", {"note": "no trace of this command's effect"}

    def status_facts(self):
        """`status`: the very line `kyctl.sh status` prints for this loop, and its key=value facts — one source."""
        Reject, script = self.kc.Reject, self.fleet / "kyctl.sh"
        if not script.is_file():
            raise Reject("status_unavailable: %s is not installed" % script)
        try:
            r = subprocess.run(["/bin/bash", str(script), "status"], capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.SubprocessError) as e:
            raise Reject("status_unavailable: kyctl.sh status (%s)" % type(e).__name__)
        line = next((x for x in r.stdout.splitlines() if x.startswith(self.role + " ")), None)
        if r.returncode != 0 or line is None:
            raise Reject("status_unavailable: kyctl.sh status rc=%d reported no line for %s" % (r.returncode, self.role))
        return {"loop": self.role, "source": "kyctl.sh status", "observed_at": utc(), "line": line,
                "facts": dict(tok.split("=", 1) for tok in line.split()[1:] if "=" in tok)}

    def command_disable(self, cid, reason):
        self.ls(lambda d: dict(d, enabled=False, reason=reason, updated_at=utc(), updated_by=self.controller_id,
                               disabled_by_command=cid))

    def ensure_role_state(self):
        if not self.state_path.exists():        # conductor only: the planner's state must already exist
            write_json(self.state_path, {"schema": "ky.role_state/1", "role": self.role, "active": {},
                                         "completed_steps": [], "deferred": []})
            self.state_sha = sha_file(self.state_path)

    def command_state(self):
        """The role state a command may be recorded into — only as its sole, unchallenged writer."""
        Reject = self.kc.Reject
        if self.role == "conductor":
            self.ensure_role_state()
        if sha_file(self.state_path) != self.state_sha:
            raise Reject("role_state_changed_outside_controller: %s" % self.state_path.name)
        state, err = self.read_role_state()
        if err:
            raise Reject(err)
        return state

    def write_role_state(self, state):
        write_json(self.state_path, state)
        self.state_sha = sha_file(self.state_path)

    def owner_pause(self):
        """None, or why no model job may be launched: an owner pause is in force until an owner resume is APPLIED
        ("paused"); the owner has queued a pause the campaign role has not applied yet ("pending: <id>" — honoured
        at once, and only the owner's own later resume withdraws it); or the queue cannot be read ("unknown: …").
        Unknown is treated as paused."""
        try:
            if self.kc.owner_paused(self.run):
                return "paused"
            pending = self.kc.pause_state(self.run).get("pending_pause")
        except Exception as e:                  # kycommands.QueueUnreadable, or anything else it cannot answer
            return "unknown: %s" % type(e).__name__
        return "pending: %s" % pending if pending else None

    def commands_overdue(self):
        """R16. A queued command that cannot be settled yet keeps its place — and, in the model loops, keeps
        anything from being launched: a wait that ends when another actor lets go of what it holds (an item or
        command lock, an application it began and has not finished). While it is short it is nobody's business.
        Once it has lasted COMMANDS_OVERDUE_S, ONE attention item says which command waits and why — the loop
        would otherwise rest in `commands_pending` for good behind a holder that never lets go. Nothing is taken
        over and nothing is stopped: the wait goes on, and ends by itself when the holder does."""
        if not self.commands_blocked:
            self.commands_blocked_since = None
            return
        now = time.time()
        if self.commands_blocked_since is None:
            self.commands_blocked_since = now
        if now - self.commands_blocked_since < COMMANDS_OVERDUE_S * self.scale:
            return
        minutes = int(COMMANDS_OVERDUE_S // 60)
        self.raise_attention(
            "loop-%s-commands-not-settled" % self.role,
            "A queued owner command of the %s role has not been settled for %d minutes (%s). %s Another actor "
            "holds what it needs and has not let go; nothing is taken over. Is that actor still at work?"
            % (self.role, minutes, flat(self.commands_blocked, 200),
               "The veto handler goes on ticking." if self.role == "veto" else "Nothing is launched meanwhile."),
            ["waiting for: %s" % flat(self.commands_blocked, 300), "queue: %s" % (self.run / "commands"),
             "locks: %s" % (self.run / "locks"), "action records: %s" % (self.run / "actions")],
            options=[{"id": "end-the-holder", "text": "The holder is stuck or gone: end it; the command is then "
                                                      "applied by itself."},
                     {"id": "leave", "text": "The holder is at work: leave it."}],
            message="%s loop: a queued command has not been settled for %d minutes" % (self.role, minutes))

    def queue_attention(self, pause):
        """The owner's command queue cannot be read. Unknown is honoured as a pause (owner_pause()), so nothing
        is launched — but this pause does not end by an owner's `resume`: a command file has to be repaired or
        removed. ONE attention item says so while that lasts (R16: the loop would otherwise rest in the ordinary
        waiting state `owner_paused` with nobody told); the loop is not stopped and goes on by itself once the
        queue can be read again."""
        try:
            problems = list(self.kc.pause_state(self.run).get("problems") or [])
        except Exception as e:
            problems = ["the queue could not be read at all (%s)" % type(e).__name__]
        self.raise_attention(
            "loop-%s-command-queue-unreadable" % self.role,
            "The %s loop launches nothing because the owner's command queue cannot be read (%s): whether a pause "
            "is in force is unknown, and unknown is honoured as a pause. No `resume` ends this one. Repair the "
            "queue?" % (self.role, flat(pause, 80)),
            ["queue: %s" % (self.run / "commands")] + ["problem: %s" % flat(x, 240) for x in problems[:10]],
            options=[{"id": "repair", "text": "Repair or remove the named command file(s) by hand; the %s loop "
                                              "then goes on by itself." % self.role},
                     {"id": "acknowledge", "text": "Seen; the loop stays paused meanwhile."}],
            message="%s loop is paused: the owner's command queue cannot be read" % self.role)

    def launch_gate(self):
        """The last look before a launch. → the reason the launch must not happen now, or None. The same durable
        state the top of the loop honours, re-read because eligibility checks may have taken minutes."""
        if self.stop_path.exists():
            return "stop"
        if self.ls().get("enabled") is not True:
            return "not_enabled"
        if self.apply_commands():
            return "commands_applied"
        if self.commands_blocked:
            return "commands_pending"
        if (self.root / "HOLD").exists():
            return "hold"
        return "owner_paused" if self.owner_pause() else None

    # ---- action records (plan §4a.1): every side effect of this controller, and recovery before any (re)launch
    def begin_own(self, action_id, kind, inputs, target, transition):
        """kyaction.begin for a side effect of this controller; the id is remembered as its own."""
        self.own_actions.add(action_id)
        return self.ka.begin(self.run, action_id, kind, self.actor(), inputs, target, transition)

    def launch_result(self, run):
        keys = ("run_id", "exit_code", "ended_reason", "ended_at", "timed_out", "terminated_by_signal", "pid",
                "pgid", "process_start")
        return dict({k: run.get(k) for k in keys}, run_record=str(self.loop_dir / ("%s.json" % run.get("run_id"))))

    def settle_launch_action(self, record):
        """The observed result of a launch this controller supervised, recorded exactly once."""
        aid, result = "LAUNCH-%s" % record.get("run_id"), self.launch_result(record)
        try:
            if record.get("ended_reason") == "launch_failed":
                self.ka.fail(self.run, aid, result)
            else:
                self.ka.complete(self.run, aid, result)
        except (self.ka.ActionError, OSError) as e:      # left INTENDED: reconciled before the next launch
            self.log("launch action %s not settled (%s: %s)" % (aid, type(e).__name__, flat(e, 160)))

    def observe_launch(self, record):
        """kyaction observer for a launch: what the run record PROVES. A complete run record settles it; a missing
        or unfinished one proves nothing (whether a child exists cannot be observed) and is "unknown"."""
        target = record.get("target") if isinstance(record.get("target"), dict) else {}
        run_id = target.get("run_id")
        if not isinstance(run_id, str) or record.get("action_id") != "LAUNCH-" + run_id:
            return "unknown", {"reason": "the action does not name one run of this role"}
        run, err = read_json(self.loop_dir / (run_id + ".json"))
        if err == "missing":
            return "unknown", {"reason": "no run record: whether a child was started cannot be observed"}
        if err or not isinstance(run, dict) or run.get("run_id") != run_id:
            return "unknown", {"reason": "the run record is unreadable"}
        if not run.get("ended_at"):
            return "unknown", {"reason": "the run record is unfinished and its child could not be confirmed gone",
                               "pid": run.get("pid") if isinstance(run.get("pid"), int) else None}
        if run.get("ended_reason") == "launch_failed":
            return "not_done", dict(self.launch_result(run), reconciled=True)
        return "done", dict(self.launch_result(run), reconciled=True)

    def reconcile_child(self, run):
        """A run recorded as unfinished belongs to a controller that no longer runs. Its job is finalised only when
        it is GONE — the leader positively gone AND its process group empty (job_state). A surviving leader (PID +
        process-start identity) is waited for, and its group terminated by that identity once past its recorded
        deadline, before any replacement. Everything else leaves the run record unfinished, so that its launch
        action stays unknown — one awaiting item, nothing relaunched: a child recorded as pending or never
        identified, a state that cannot be told, and a process group found WITHOUT its leader (its members cannot
        be identified as this job's any more — after a restart of the machine that group id may be anyone's — so
        they are never signalled from here)."""
        pid, pgid, start = run.get("pid"), run.get("pgid"), run.get("process_start")

        def settled():
            """job_state, giving a leader that has just ended a moment to be reaped (its group answers "unknown"
            while only its zombie is left; an orphan's zombie is reaped by launchd at once)."""
            end, state = time.time() + 5.0, job_state(pid, pgid, start)
            while state == "unknown" and time.time() < end:
                probe = ps_probe(pid)
                if not (probe and probe[0] == "alive" and probe[1].startswith("Z")):
                    break
                time.sleep(0.05)
                state = job_state(pid, pgid, start)
            return state

        state, reason = settled(), "interrupted"
        if state == "live":
            self.log("surviving child %s (pid %d) of a dead controller: waiting before any replacement"
                     % (run.get("run_id"), pid))
            deadline = parse_utc(run.get("deadline_at")) or time.time()
            while state == "live":
                if time.time() >= deadline and pgid == pid:
                    self.terminate_group(pgid)            # past its recorded deadline, by identity
                    state = settled()
                    if state == "live":
                        self.wait("orphan_child", HOLD_POLL_S)
                else:
                    self.wait("orphan_child", 1.0)
                state = settled()
            reason = "orphan_reconciled"
        if state == "gone":
            with guarded("finalize"):
                self.finalize(run, None, reason, supervised=False)
        else:
            self.log("%s is not confirmed gone (%s): its run record stays unfinished" % (run.get("run_id"), state))

    # ---- what a JOB recorded (R8): reconciled by the controller after the job has exited
    def quarantine(self, names, why, run_id=None):
        """Move job-authored files that are not usable action records out of $KY_RUN/actions into
        actions/quarantine/ (bytes kept, nothing deleted) and raise ONE awaiting item naming them. This never
        stops the loop. → the quarantined names."""
        moved, directory = [], self.run / "actions" / "quarantine"
        for name in names:
            try:
                os.makedirs(directory, exist_ok=True)
                target = directory / ("%s.%s" % (name, utc("%Y%m%dT%H%M%SZ")))
                n = 1
                while os.path.lexists(target):
                    n += 1
                    target = directory / ("%s.%s.%d" % (name, utc("%Y%m%dT%H%M%SZ"), n))
                os.rename(self.run / "actions" / name, target)
                moved.append({"file": name, "quarantined_as": str(target), "reason": flat(why.get(name), 200)})
            except OSError as e:
                self.log("could not quarantine %s (%s)" % (name, type(e).__name__))
        if moved:
            self.log("quarantined %d job-authored file(s) that are not usable action records: %s"
                     % (len(moved), ", ".join(m["file"] for m in moved)))
            slug = "loop-%s-quarantine-%s" % (self.role, re.sub(r"[^a-z0-9-]", "-", str(run_id or "recovery").lower()))
            self.raise_attention(
                slug, "A %s job wrote %d file(s) under run/actions that are not action records it may write (a job "
                      "records side effects only through `kyaction.py begin|complete|fail`, as JOB-<run_id>-<slug>). "
                      "They were moved to %s; whether a side effect stands behind them is unknown. What should "
                      "happen?" % (self.role, len(moved), directory),
                ["%s → %s (%s)" % (m["file"], m["quarantined_as"], m["reason"]) for m in moved[:20]],
                options=[{"id": "acknowledge", "text": "Seen; no side effect stands behind them."},
                         {"id": "investigate", "text": "Check the named side effects by hand before the item goes on."}],
                message="%s loop: %d malformed job-authored action file(s) quarantined" % (self.role, len(moved)))
        return moved

    def job_files_to_quarantine(self, run_id=None, before=None, own_window=False):
        """{file name: why} of the files under run/actions that a job of this role wrote and that are not usable
        job records. Attributed to a job by evidence only:
          * the name lies in a job namespace of this role (JOB-<run id of this role>-…; with `run_id`, that run's);
          * `before` being the listing taken just before that run's child was started: the file is not in it and
            cannot be read as a record (every other writer under run/actions writes whole, valid records);
          * `own_window` — this controller supervised that child from start to exit, so the listing brackets
            exactly the child's lifetime and every record this controller wrote meanwhile is known to it: a
            record that appeared and claims this role's controller, although this controller did not write it.
        Another actor's record, and an unreadable file that was there before, are never touched here."""
        ka, out = self.ka, {}
        prefix = "%s%s-" % (ka.JOB_PREFIX, run_id if run_id else self.ROLE)
        for name, reason in ka.unreadable(self.run):
            if name.startswith(prefix) or (before is not None and name not in before):
                out[name] = reason
        for rec in ka.scan(self.run)[0]:
            aid, name = rec["action_id"], rec["action_id"] + ".json"
            actor = rec.get("actor") if isinstance(rec.get("actor"), dict) else {}
            claims_job = actor.get("holder_kind") == JOB_HOLDER
            if claims_job and ka.is_job_record(rec, actor.get("run_id")):
                continue                        # a job's own well-formed record (this role's or another's)
            if name.startswith(prefix) or (claims_job and str(actor.get("run_id", "")).startswith(self.ROLE + "-")):
                out[name] = "not a job record of the run its id or actor names"
            elif own_window and before is not None and name not in before and aid not in self.own_actions \
                    and actor.get("role") == self.role and actor.get("holder_kind") == "controller":
                out[name] = "appeared while the job ran and claims this role's controller, which did not write it"
        return out

    def observe_git_push(self, record):
        """kyaction observer for a job's `git_push`: `git ls-remote <remote> <ref>` in the role worktree. The remote
        ref at exactly the recorded commit → done; at another commit or absent → not_done; anything that cannot be
        asked or read → unknown. inputs (or target) carry {"remote": a configured remote NAME, "ref":
        "refs/heads/<branch>" (a bare branch name is read as that), "commit": the full commit id}."""
        inputs = record.get("inputs") if isinstance(record.get("inputs"), dict) else {}
        target = record.get("target") if isinstance(record.get("target"), dict) else {}

        def named(key):
            value = inputs.get(key, target.get(key))
            return value if isinstance(value, str) else None

        remote, ref, commit, repo = named("remote"), named("ref"), named("commit"), named("repo")
        if ref and not ref.startswith("refs/"):
            ref = "refs/heads/" + ref
        if not (remote and GIT_REMOTE_RE.match(remote) and ref and GIT_REF_RE.match(ref) and ".." not in ref
                and commit and HEX_COMMIT.match(commit)):
            return "unknown", {"reason": "the record does not name a remote, a ref and a full commit id"}
        cfg = self.cfg or self.load_config()[0]
        worktree = cfg.get("worktree") if isinstance(cfg, dict) else None
        if not worktree or not os.path.isdir(worktree):
            return "unknown", {"reason": "the role worktree is not known"}
        if repo is not None and os.path.realpath(repo) != os.path.realpath(worktree):
            return "unknown", {"reason": "the record names another repository than the role worktree"}
        home = os.environ.get("HOME") or pwd.getpwuid(os.getuid()).pw_dir
        try:
            r = subprocess.run([os.environ.get("KY_GIT") or "/usr/bin/git", "-C", worktree, "ls-remote", remote, ref],
                               capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL,
                               env={"PATH": "/usr/bin:/bin", "HOME": home, "LC_ALL": "C", "GIT_TERMINAL_PROMPT": "0",
                                    "GIT_OPTIONAL_LOCKS": "0"})
        except (OSError, ValueError, subprocess.SubprocessError) as e:
            return "unknown", {"reason": "git ls-remote could not be run (%s)" % type(e).__name__}
        if r.returncode != 0:
            return "unknown", {"reason": "git ls-remote rc=%d" % r.returncode}
        at = [parts[0] for parts in (line.split() for line in r.stdout.splitlines())
              if len(parts) == 2 and parts[1] == ref]
        if at == [commit]:
            return "done", {"remote": remote, "ref": ref, "commit": commit, "observed_by": "git ls-remote",
                            "reconciled": True}
        return "not_done", {"remote": remote, "ref": ref, "intended": commit, "observed": at[0] if at else None}

    JOB_OBSERVERS = {"git_push": "observe_git_push"}

    def reconcile_job_record(self, rec):
        """One unfinished record a job of this role wrote (the job has exited). An observer for its kind settles
        it (done → DONE; not_done → FAILED, from the observation — the next job does it under its own record).
        Without one, or when the observer cannot tell, it is UNKNOWN: recorded as such, ONE awaiting item naming
        the record (once per record), never retried — and the loop goes on with other items. That item has an
        end (R15): the owner's `decide` names one of its two options, and the controller that applies it settles
        the record accordingly and closes the item (record_owner_decision, settle_job_action). → the outcome."""
        ka, aid, kind = self.ka, rec["action_id"], str(rec.get("kind"))
        actor = rec.get("actor") if isinstance(rec.get("actor"), dict) else {}
        raised = any(isinstance(x, dict) and x.get("outcome") == "unknown" for x in rec.get("reconciliations") or [])
        name = self.JOB_OBSERVERS.get(kind)
        observer = getattr(self, name) if name else \
            (lambda r: ("unknown", {"reason": "no observer for kind %r" % kind}))
        outcome, after = ka.reconcile(self.run, aid, observer, by=self.controller_id)
        detail = (after.get("reconciliations") or [{}])[-1].get("detail")
        if outcome == "not_done":
            ka.fail(self.run, aid, dict(detail if isinstance(detail, dict) else {"observed": detail},
                                        reconciled=True, reason="the side effect was not observed"))
        elif outcome == "unknown" and not raised:
            run, _ = read_json(self.loop_dir / ("%s.json" % actor.get("run_id")))
            items = [w for w in (run.get("work_items") if isinstance(run, dict) else None) or [] if isinstance(w, dict)]
            target = rec.get("target") if isinstance(rec.get("target"), dict) else {}
            named = next((w for w in items if w.get("id") == target.get("item")), None) \
                or (items[0] if len(items) == 1 else None)
            why = detail.get("reason") if isinstance(detail, dict) else None
            self.raise_attention(
                self.job_action_slug(aid),
                "The %s job %s recorded the intention of a side effect (action %s, kind %s) and exited without "
                "recording its result; the controller cannot observe what became of it (%s). It is not retried. "
                "Did it happen?" % (self.role, actor.get("run_id"), aid, kind, flat(why, 160) or "unknown"),
                ["action: %s" % aid,                # what job_action_of() reads: the record an answer settles
                 "action record: %s" % (self.run / "actions" / (aid + ".json")),
                 "intended transition: %s" % flat(rec.get("intended_transition"), 200),
                 "target: %s" % flat(json.dumps(target, sort_keys=True), 200)],
                options=[{"id": JOB_ACTION_OPTIONS[0], "text": "It happened: on your `decide` the %s controller "
                                                               "settles the record as done and the item goes on."
                                                               % self.role},
                         {"id": JOB_ACTION_OPTIONS[1], "text": "It did not happen: on your `decide` the %s controller "
                                                               "settles the record as failed; the next job may do "
                                                               "it under its own record." % self.role}],
                item=named["id"] if named else None, blocks="item" if named else "none",
                message="%s loop: the outcome of job action %s is unknown" % (self.role, aid))
        return outcome

    def reconcile_job_actions(self, run_id, before=None, own_window=False):
        """After the job of `run_id` has exited (R8): quarantine what it wrote under run/actions that is not a
        usable job record, then reconcile its unfinished JOB-<run_id>-* records. → a summary for the run record.
        Nothing here ever stops the loop."""
        ka = self.ka
        out = {"quarantined": [], "reconciled": [], "unknown": []}
        if ka is None:
            return None
        bad = self.job_files_to_quarantine(run_id, before, own_window)
        out["quarantined"] = [m["file"] for m in self.quarantine(sorted(bad), bad, run_id)]
        for rec in ka.job_records(self.run, run_id, state="INTENDED"):
            try:
                outcome = self.reconcile_job_record(rec)
            except (ka.ActionError, OSError) as e:
                self.log("job action %s not reconciled (%s: %s)" % (rec["action_id"], type(e).__name__, flat(e, 160)))
                outcome = "unknown"
            out["unknown" if outcome == "unknown" else "reconciled"].append(rec["action_id"])
        return out

    # ---- the dispatcher start and notifications of a previous controller: observed, never repeated blind
    def observe_dispatcher(self, record=None):
        """kyaction observer for the conductor's `kyctl.sh start dispatcher`: what `kyctl.sh status` reports for
        the dispatcher. running → done; stopped or not installed → not_done; anything else → unknown."""
        try:
            r = subprocess.run(["/bin/bash", str(self.fleet / "kyctl.sh"), "status"], capture_output=True, text=True,
                               timeout=120)
        except (OSError, subprocess.SubprocessError) as e:
            return "unknown", {"reason": "kyctl.sh status could not be run (%s)" % type(e).__name__}
        line = next((x for x in r.stdout.splitlines() if x.startswith("dispatcher ")), None)
        facts = dict(tok.split("=", 1) for tok in line.split()[1:] if "=" in tok) if line else {}
        if r.returncode != 0 or facts.get("state") not in ("running", "stopped", "not-installed"):
            return "unknown", {"reason": "kyctl.sh status reported state=%s (rc=%d)" % (facts.get("state"), r.returncode)}
        if facts["state"] == "running":
            return "done", {"state": "running", "pid": facts.get("pid"), "observed_by": "kyctl.sh status",
                            "reconciled": True}
        return "not_done", {"state": facts["state"], "observed_by": "kyctl.sh status"}

    def dispatcher_attention(self, action_id, why):
        self.raise_attention(
            "loop-conductor-dispatcher-start",
            "The conductor could not confirm that the dispatcher was started (%s). It is not started again blindly, "
            "and the conductor goes on handling messages. Start it by hand, or leave it stopped?" % flat(why, 200),
            ["action record: %s" % (self.run / "actions" / (action_id + ".json")),
             "command: kyctl.sh start dispatcher"],
            options=[{"id": "start", "text": "Correct the cause and run `kyctl.sh start dispatcher`."},
                     {"id": "leave-stopped", "text": "Leave the dispatcher stopped."}],
            item="loop.dispatcher", message="conductor: the dispatcher start is unconfirmed (%s)" % flat(why, 80))

    def start_dispatcher(self):
        """The conductor's idempotent dispatcher start (plan §11), once per controller, as a recorded side effect
        whose exit status is honoured (N-04):
          * STOP_dispatcher, or a switch that says `enabled: false` (the owner's stop), is respected — a dispatcher
            the owner disabled is never re-enabled from here; a switch that cannot be read is unknown: not started;
          * an open awaiting item about an earlier start means that start is still unconfirmed: no blind retry;
          * otherwise DISPATCHER-START-<controller id> is INTENDED, `kyctl.sh start dispatcher` runs, and exit 0
            completes the record. A non-zero exit fails it; an exit that was not observed (the helper is missing,
            could not be run or timed out) is settled by observation, and stays unfinished when that is unknown.
            Anything but success raises ONE awaiting item — and the conductor goes on."""
        if self.dispatcher_checked:
            return
        self.dispatcher_checked = True
        note = {"at": utc()}
        try:
            switch, err = loop_state(self.run, "dispatcher")
            if (self.run / "STOP_dispatcher").exists():
                note["skipped"] = "stop_file_present"
            elif switch is None:
                note["skipped"] = "dispatcher_switch_unreadable: %s" % err
            elif switch.get("enabled") is False:
                note["skipped"] = "disabled_by_switch: %s" % flat(switch.get("reason"), 120)
            elif self.open_awaiting("loop-conductor-dispatcher-start"):
                note["skipped"] = "an earlier start is still unconfirmed (awaiting item open)"
            else:
                action_id = "DISPATCHER-START-%s" % self.controller_id
                status, _ = self.begin_own(action_id, "dispatcher_start", {"argv": ["kyctl.sh", "start", "dispatcher"]},
                                           {"loop": "dispatcher", "label": LABEL_PREFIX + "dispatcher"},
                                           "start the dispatcher loop idempotently: not running → running")
                note["action"] = action_id
                if status != "new":
                    note["skipped"] = "action record is %s" % status
                else:
                    rc = self.run_helper("kyctl.sh", ["start", "dispatcher"], 120)
                    note["rc"] = rc
                    if rc == 0:
                        self.ka.complete(self.run, action_id, {"rc": 0})
                    elif rc in (None, 124, 126):            # not observed: ask what is there now
                        outcome, _ = self.ka.reconcile(self.run, action_id, self.observe_dispatcher, by=self.controller_id)
                        note["observed"] = outcome
                        if outcome == "not_done":
                            self.ka.fail(self.run, action_id, {"rc": rc, "reason": "the start was not observed and the "
                                                                                 "dispatcher is not running"})
                        if outcome != "done":
                            self.dispatcher_attention(action_id, "kyctl.sh start dispatcher gave no exit status (%s)" % rc)
                    else:
                        self.ka.fail(self.run, action_id, {"rc": rc})
                        self.dispatcher_attention(action_id, "kyctl.sh start dispatcher exited %d" % rc)
        except (self.ka.ActionError, OSError) as e:
            note["error"] = "%s: %s" % (type(e).__name__, flat(e, 160))
        if "skipped" in note or "error" in note:
            self.log("dispatcher start: %s" % (note.get("skipped") or note.get("error")))
        self.ls(lambda d: dict(d, dispatcher_start=note))

    def reconcile_soft(self, rec):
        """An unfinished notification or dispatcher start of a PREVIOUS controller of this role. Neither ever stops
        the loop: a notification that was positively not journaled is submitted now, under the same record; a
        dispatcher start is settled from what is running, and raises its one awaiting item when that is unknown."""
        ka, aid, kind = self.ka, rec["action_id"], rec.get("kind")
        if kind == "notification":
            outcome, _ = ka.reconcile(self.run, aid, self.observe_notification, by=self.controller_id)
            if outcome == "not_done":
                inputs = rec.get("inputs") if isinstance(rec.get("inputs"), dict) else {}
                result = self.submit_notification(inputs["message"], inputs["level"])
                if result["notify"] in ("submitted", "dry"):
                    ka.complete(self.run, aid, dict(result, reconciled=True))
                elif result["notify"] in ("failed", "unavailable"):
                    ka.fail(self.run, aid, dict(result, reconciled=True))
            return
        outcome, _ = ka.reconcile(self.run, aid, self.observe_dispatcher, by=self.controller_id)
        if outcome == "not_done":
            ka.fail(self.run, aid, {"reason": "the start was never observed and the dispatcher is not running",
                                    "reconciled": True})
        elif outcome == "unknown":
            self.dispatcher_attention(aid, "an earlier controller's dispatcher start was never observed")

    def reconcile_actions(self, full=False):
        """Recovery (plan §4a.1), at controller start (`full`) and before every (re)launch: each unfinished action
        that is this role's own launch record, or that a previous controller of this role began, is reconciled
        against run-record and process evidence. What cannot be observed is unknown — Refusal: one awaiting file,
        nothing launched, nothing retried. What a JOB of this role recorded never refuses: its malformed files
        are quarantined first (so the strict read below cannot fail on them), its unfinished records are settled
        by observation or raised as one awaiting item each (R8)."""
        ka = self.ka
        bad = self.job_files_to_quarantine()
        self.quarantine(sorted(bad), bad)
        try:
            pending = ka.unfinished(self.run)   # strict: a record that cannot be read is never "finished"
        except (ka.ActionError, OSError) as e:
            raise Refusal(["action_unreconciled: an action record cannot be read (%s) — unknown, nothing is launched"
                           % flat(e, 200)])
        unknown, handled = [], set()
        try:
            self.reconcile_each(pending, unknown, handled)
        except (ka.ActionError, OSError) as e:  # e.g. another live actor is updating the very record: not ours to judge
            unknown.append("reconciliation interrupted (%s: %s)" % (type(e).__name__, flat(e, 160)))
        if full:                                # nothing escapes the one mechanism: every unfinished run has an action
            for path in sorted(self.loop_dir.glob(self.ROLE + "-*.json"), key=lambda p: p.stem):
                run, err = read_json(path)
                if err or not isinstance(run, dict):
                    unknown.append("run record %s (unreadable)" % path.name)
                elif not run.get("ended_at") and path.stem not in handled:
                    unknown.append("run record %s (unfinished, with no unfinished launch action)" % path.stem)
        if unknown:
            raise Refusal(["action_unreconciled: %s — unknown, nothing is launched or retried" % "; ".join(unknown)])

    def reconcile_each(self, pending, unknown, handled):
        ka, jobs = self.ka, []
        for rec in pending:
            aid, kind = rec["action_id"], str(rec.get("kind"))
            actor = rec.get("actor") if isinstance(rec.get("actor"), dict) else {}
            if actor.get("holder_kind") == JOB_HOLDER:
                if str(actor.get("run_id", "")).startswith(self.ROLE + "-") and ka.is_job_record(rec, actor["run_id"]):
                    jobs.append(rec)            # after the launches: its job must be known gone first
                continue
            mine = actor.get("role") == self.role and actor.get("holder_kind") == "controller"
            if not mine or not (kind == "launch" or actor.get("controller_id") != self.controller_id):
                continue                        # another role's, a cockpit's or the bootstrap supervisor's record
            if kind in ("notification", "dispatcher_start"):
                self.reconcile_soft(rec)
                continue
            if kind == WAIT_CLOSE_KIND:         # never stops the loop: the next look at the queue completes it (R18)
                ka.reconcile(self.run, aid, self.observe_wait_close, by=self.controller_id)
                continue
            if kind == "launch":
                run_id = (rec.get("target") or {}).get("run_id") if isinstance(rec.get("target"), dict) else None
                handled.add(run_id)
                run, _ = read_json(self.loop_dir / ("%s.json" % run_id))
                if isinstance(run, dict) and run.get("run_id") == run_id and not run.get("ended_at"):
                    self.reconcile_child(run)
                outcome, after = ka.reconcile(self.run, aid, self.observe_launch, by=self.controller_id)
                if outcome == "not_done":       # the run record says the launch itself failed: FAILED, from it
                    ka.fail(self.run, aid, after["reconciliations"][-1]["detail"])
                why = "launch not observable"
            elif kind.startswith("command:"):   # settled through kycommands.apply's observer while still QUEUED
                cid = (rec.get("target") or {}).get("command_id") if isinstance(rec.get("target"), dict) else None
                try:
                    entry = self.kc.find(self.run, cid)
                except self.kc.CommandError:
                    entry = None
                outcome = "pending" if entry and entry["doc"]["state"] == "QUEUED" else "unknown"
                why = "its command is no longer queued"
            else:
                outcome, why = "unknown", "no observer for kind %r" % kind
            if outcome == "unknown":
                if kind != "launch":
                    ka.reconcile(self.run, aid, lambda r, why=why: ("unknown", {"reason": why}), by=self.controller_id)
                unknown.append("%s (%s)" % (aid, why))
        for rec in jobs:
            run, _ = read_json(self.loop_dir / ("%s.json" % rec["actor"]["run_id"]))
            if isinstance(run, dict) and not run.get("ended_at"):
                continue                        # its job is not known gone: the launch action above says so
            try:
                self.reconcile_job_record(rec)
            except (ka.ActionError, OSError) as e:      # a job's record never stops the loop
                self.log("job action %s not reconciled (%s: %s)" % (rec["action_id"], type(e).__name__, flat(e, 160)))

    # ---- one bounded child job
    def new_run_id(self):
        base = "%s-%s" % (self.ROLE, utc("%Y%m%dT%H%M%SZ"))
        for n in range(1, 100):
            rid = base if n == 1 else "%s-%02d" % (base, n)
            if not (self.loop_dir / (rid + ".json")).exists() and not (self.scratch / "loops" / self.role / rid).exists():
                return rid
        raise Refusal(["run_id_exhausted: %s" % base])

    def lock_items(self, items, run_id):
        """Message locks, each followed by a fresh handled-state check (double-action guard, §4a.6). Taken through
        kyaction's lock — the one rule: atomic with its owner, taken over only from an owner that is positively
        gone. A lock held by a live actor skips that message; one whose owner cannot be judged skips it too and
        raises one attention item (never taken over). The ids skipped for a lock are left in self.items_waiting:
        when nothing else remains, the loop WAITS for them (waiting state `items_locked`) — it never comes
        straight back for another look."""
        self.items_waiting = []
        if self.role != "conductor":
            return items
        kept = []
        for it in items:
            try:
                lock = self.ka.acquire_lock(self.run, it["id"], run_id, log=self.log)
            except self.ka.LockUnknown as e:
                self.lock_attention(it["id"], e)
                self.items_waiting.append(it["id"])
                continue
            if lock is None:
                self.items_waiting.append(it["id"])
                continue
            self.item_locks[it["id"]] = lock
            if (self.run / "handled" / (it["id"] + ".json")).exists():
                self.release_item_locks([it["id"]])
            else:
                kept.append(it)
        return kept

    def lock_attention(self, name, error):
        self.log_once("%s — skipped" % flat(error, 200))
        self.raise_attention(
            "lock-owner-unknown-" + re.sub(r"[^a-z0-9-]", "-", name.lower()),
            "The lock %s exists and its owner cannot be judged alive or gone (%s). It is never taken over and never "
            "removed by age, so what it guards waits. Is its owner gone?" % (name, flat(error, 200)),
            ["lock: %s" % (self.run / "locks" / name)],
            options=[{"id": "remove-lock", "text": "The owner is gone: remove the lock directory by hand."},
                     {"id": "leave", "text": "The owner is alive (or unknown): leave the lock alone."}],
            message="%s loop: lock %s has an owner that cannot be identified" % (self.role, name))

    def release_item_locks(self, ids):
        """Release the message locks THIS controller took for its current run. (The locks of a dead controller's
        run are not released here: they are taken over once their owner is positively gone.)"""
        for iid in ids:
            lock = self.item_locks.pop(iid, None)
            if lock is not None:
                try:
                    self.ka.release_lock(lock)
                except OSError:
                    pass

    def substep_window(self, item_id, caps, evidence):
        """How many sub-steps of that item were accepted under the CURRENT recorded evidence (N-01). The count
        starts again only when that evidence — external dependencies no job authored, the owner's answers —
        differs from the evidence the window was counted under."""
        window = caps.get(item_id) if isinstance(caps.get(item_id), dict) else {}
        return as_int(window.get("count")) if window.get("evidence") == evidence else 0

    def run_job(self, items):
        """Launch ONE bounded child for those items and see it through. → "items_locked" when nothing was
        launched because every remaining item is locked by another actor (the caller waits); None otherwise."""
        cfg = self.cfg
        run_id = self.new_run_id()
        items = self.lock_items(items, run_id)
        if not items:
            return "items_locked" if self.items_waiting else None
        rs = self.scratch / "loops" / self.role / run_id
        out = rs / "out"
        os.makedirs(out / "checkpoints")
        os.makedirs(rs / "tmp")
        self.ensure_role_state()
        state_bytes = self.state_path.read_bytes()
        snap = rs / "state.snapshot.json"
        write_atomic(snap, state_bytes, 0o444)
        before = self.accepted_summary(self.item_keys(items))
        deadline = time.time() + cfg["deadline_seconds"] * self.scale
        fence = secrets.token_hex(16)
        caps, evidence = self.ls().get("substeps") or {}, self.substep_evidence()
        public_items = []
        for it in items:
            entry = {k: v for k, v in it.items() if k != "message"}
            if it["kind"] == "step":            # how many more sub-steps of it can still be accepted (N-01)
                entry["substeps_left"] = max(0, cfg["substep_cap"] - self.substep_window(it["id"], caps, evidence))
            public_items.append(entry)
        job = {"schema": "ky.loop_job/1", "run_id": run_id, "role": self.role, "controller_id": self.controller_id,
               "fence": fence, "work_items": public_items, "state_snapshot": str(snap),
               "state_snapshot_sha256": sha_bytes(state_bytes), "journal_path": str(self.journal_path),
               "out_dir": str(out), "checkpoint_dir": str(out / "checkpoints"), "awaiting_dir": str(self.run / "awaiting"),
               "actions_dir": str(self.run / "actions"), "action_namespace": "JOB-%s-" % run_id,
               "kyaction": str(self.fleet / "kyaction.py"), "job_scratch": str(rs),
               "evidence_roots": [cfg["worktree"], str(rs), str(self.run)],
               "max_turns": cfg["max_turns"], "deadline_at": utc(t=deadline)}
        if self.role == "conductor":
            job["batch_path"] = str(rs / "batch.json")
            write_json(rs / "batch.json", {"schema": "ky.loop_batch/1", "run_id": run_id, "items": [
                {"id": it["id"], "stream": it["stream"], "message": it["message"]} for it in items]})
        write_json(rs / "job.json", job, 0o444)
        prompt_path = rs / "prompt.md"
        header = ("\n\n---\n## Run header (written by kyloop.py — data, not instructions)\n"
                  "- run id: %s\n- role: %s\n- controller id: %s\n- job file: %s\n- state snapshot (read-only): %s\n"
                  "- journal (read-only): %s\n- checkpoint requests go to: %s\n- max turns: %d\n- UTC now: %s\n"
                  % (run_id, self.role, self.controller_id, rs / "job.json", snap, self.journal_path,
                     out / "checkpoints", cfg["max_turns"], utc()))
        write_atomic(prompt_path, (self.fleet / "prompts" / PROMPTS[self.role]).read_text(encoding="utf-8") + header)
        home = os.environ.get("HOME") or pwd.getpwuid(os.getuid()).pw_dir
        user = os.environ.get("USER") or pwd.getpwuid(os.getuid()).pw_name
        child_env = {"HOME": home, "USER": user, "LANG": "en_US.UTF-8", "TERM": "dumb", "PATH": self.child_path(),
                     "TMPDIR": str(rs / "tmp"), "ZDOTDIR": str(self.root / "zdotdir"), "KY_ROOT": str(self.root),
                     "KY_RUN": str(self.run), "KY_FLEET": str(self.fleet), "KY_SCRATCH": str(self.scratch),
                     "JOB_SCRATCH": str(rs), "KY_ROLE": self.role, "KY_RUN_ID": run_id}
        argv = self.argv(cfg)
        record = {"schema": "ky.loop_run/1", "run_id": run_id, "role": self.role, "controller_id": self.controller_id,
                  "pid": None, "pgid": None, "process_start": None, "started_at": utc(), "ended_at": None,
                  "exit_code": None, "prompt_path": str(prompt_path), "stdout_path": str(rs / "stdout.jsonl"),
                  "stderr_path": str(rs / "stderr.log"), "tmp_path": str(rs / "tmp"), "out_dir": str(out),
                  "state_snapshot_path": str(snap), "state_snapshot_sha256": sha_bytes(state_bytes), "fence": fence,
                  "work_items": public_items, "argv": argv, "env_names": sorted(child_env), "worktree": cfg["worktree"],
                  "model": cfg["model"], "effort": cfg["effort"], "max_turns": cfg["max_turns"],
                  "permission_mode": cfg["permission_mode"], "mcp_config": cfg["mcp_config"],
                  "substep_cap": cfg["substep_cap"], "test_hooks": self.test_hooks(),
                  "prompt_sha256": sha_file(prompt_path), "deadline_at": utc(t=deadline), "progress_before": before,
                  "progress_after": None, "progressed": None, "quota_refusal": None, "backoff_minutes": None,
                  "quota": None, "rate_limit_status_unrecognised": None,
                  "timed_out": False, "terminated_by_signal": False, "stop_request": None, "survivors": None,
                  "state_violation": None, "snapshot_intact": None, "job_actions": None,
                  "accepted": [], "refused": [], "provider_session_id": None, "ended_reason": None}
        record_path = self.loop_dir / (run_id + ".json")
        # Intent first: the launch is a side effect (§4a.1). The action record is the ONE recovery mechanism;
        # the run record written next is the observation its reconciliation reads (pid, start identity, result).
        action_id = "LAUNCH-" + run_id
        try:
            status, _ = self.begin_own(
                action_id, "launch",
                {"run_id": run_id, "argv": argv, "worktree": cfg["worktree"], "model": cfg["model"],
                 "effort": cfg["effort"], "max_turns": cfg["max_turns"], "permission_mode": cfg["permission_mode"],
                 "prompt_sha256": record["prompt_sha256"], "state_snapshot_sha256": record["state_snapshot_sha256"],
                 "work_items": [it["id"] for it in items], "deadline_at": record["deadline_at"]},
                {"run_id": run_id, "role": self.role, "run_record": str(record_path)},
                "launch one bounded %s job %s: not running → exited, its result in the run record" % (self.role, run_id))
        except (self.ka.ActionError, OSError) as e:
            status = "%s: %s" % (type(e).__name__, flat(e, 160))
        if status != "new":
            self.release_item_locks([it["id"] for it in items])
            raise Refusal(["launch_action_not_recorded: %s (%s) — nothing was launched" % (action_id, status)])
        # what lies under run/actions just before the child exists: whatever else appears there while it runs and
        # is not a usable record is attributed to the job (R8)
        actions_before = sorted(n for n in os.listdir(self.run / "actions") if n.endswith(".json") and not n.startswith("."))
        write_json(rs / "actions.before.json", actions_before, 0o444)
        record["actions_before"] = {"path": str(rs / "actions.before.json"),
                                    "sha256": sha_file(rs / "actions.before.json")}
        write_json(record_path, record)
        self.ls(lambda d: dict(d, counters=dict(d.get("counters") or {}, launches=(d.get("counters") or {}).get("launches", 0) + 1,
                                                wakeups=(d.get("counters") or {}).get("wakeups", 0) + (self.role == "conductor")),
                               expected_child={"run_id": run_id, "pid": None, "pgid": None, "process_start": None,
                                               "pending": True}, last_run_id=run_id))
        try:
            self.write_owner("pending")         # BEFORE the child exists: a dead owner never looks child-less (R2)
        except Refusal:                         # kylock.sh would not record it: nothing is started, and that is
            with guarded("finalize"):           # recorded as the launch that did not happen — then the refusal
                self.finalize(record, None, "launch_failed", state_bytes=state_bytes, actions_before=set(actions_before))
            raise
        try:
            with open(prompt_path, "rb") as fin, open(record["stdout_path"], "wb") as fo, \
                    open(record["stderr_path"], "wb") as fe:
                proc = subprocess.Popen(argv, stdin=fin, stdout=fo, stderr=fe, cwd=cfg["worktree"], env=child_env,
                                        start_new_session=True)
        except OSError as e:
            self.log("launch failed: %s" % type(e).__name__)
            with guarded("finalize"):
                self.finalize(record, None, "launch_failed", state_bytes=state_bytes, actions_before=set(actions_before))
            return
        fault = None
        try:                                    # from here on a started child is never left unsupervised
            ident = None
            for _ in range(20):
                ident = ps_identity(proc.pid)
                if ident or proc.poll() is not None:
                    break
                time.sleep(0.01)
            record.update(pid=proc.pid, pgid=proc.pid, process_start=ident[1] if ident else None)
            write_json(record_path, record)
            child = {"run_id": run_id, "pid": proc.pid, "pgid": proc.pid, "process_start": record["process_start"]}
            self.write_owner(child)
            self.ls(lambda d: dict(d, expected_child=child, waiting=None, last_run_id=run_id, last_iteration_at=utc()))
            self.log("launched %s (pid %d) for %s" % (run_id, proc.pid, ", ".join(i["id"] for i in items)))
            reason = self.supervise(proc, record, deadline)
        except Exception as e:
            fault, reason = e, "controller_fault"
            record["supervision_fault"] = "%s: %s" % (type(e).__name__, flat(e, 200))
            self.terminate_group(proc.pid, proc)
        with guarded("finalize"):
            self.finalize(record, proc.returncode, reason, state_bytes=state_bytes, actions_before=set(actions_before))
        if fault is not None:
            raise Fault("supervision", fault)
        if self.signal:
            raise Interrupted()

    def stop_request(self):
        """Is this loop asked to stop while its child runs (N-10)? STOP_<role>, or a queued `loops stop` for this
        loop or `handoff` — the commands that end with the loop disabled. → what was seen, or None. Nothing is
        applied here: the top of the loop honours STOP and applies the queue, in order, once the child is gone."""
        if self.stop_path.exists():
            return {"source": "stop_file", "at": utc()}
        try:
            queue = self.kc.pending(self.run, self.role)
        except Exception:                       # an unreadable queue is honoured as a pause before the next launch
            return None
        for doc in queue:
            args = doc.get("args") if isinstance(doc.get("args"), dict) else {}
            if doc.get("command") == "handoff" or (doc.get("command") == "loops" and args.get("op") == "stop"
                                                   and args.get("loop") == self.role):
                return {"source": "command", "command_id": doc.get("id"), "command": doc.get("command"), "at": utc()}
        return None

    def supervise(self, proc, record, deadline):
        """Wait for the child. → why it ended: "exited" · "controller_signalled" (TERM/INT forwarded to its group)
        · "deadline" · "stopped" (STOP_<role>, or a queued `loops stop` / `handoff`, looked for every 15 s — the
        group is ended, the request recorded, and the loop then stops through its ordinary gates). A group that
        outlives a leader that exited by itself is ended too: a job is over only when its group is empty."""
        next_look = time.time() + WAIT_POLL_S * self.scale
        while True:
            try:
                proc.wait(timeout=CHILD_POLL_S)
                if group_gone(proc.pid) is False:
                    record["survivors"] = True
                    self.log("%s exited and left processes behind in its group: ending them" % record["run_id"])
                    self.terminate_group(proc.pid, proc)
                return "exited"
            except subprocess.TimeoutExpired:
                pass
            now = time.time()
            if self.signal:
                record["terminated_by_signal"], reason = True, "controller_signalled"
            elif now >= deadline:
                record["timed_out"], reason = True, "deadline"
            elif now >= next_look:
                next_look = now + WAIT_POLL_S * self.scale
                request = self.stop_request()
                if request is None:
                    continue
                record["stop_request"], reason = request, "stopped"
                self.log("%s: stop requested (%s) while the child runs: ending its process group"
                         % (record["run_id"], request.get("command_id") or request["source"]))
            else:
                continue
            self.terminate_group(proc.pid, proc)
            return reason

    def terminate_group(self, pgid, proc=None):
        """TERM the job's process group, wait, then KILL what is left. → True when the group is positively empty.
        Never this controller's own group, never a pgid that is not a real one."""
        if isinstance(pgid, bool) or not isinstance(pgid, int) or pgid <= 1 or pgid == os.getpgid(0):
            return False
        for sig, grace in ((signal.SIGTERM, max(0.5, TERM_GRACE_S * self.scale)), (signal.SIGKILL, 5.0)):
            try:
                os.killpg(pgid, sig)
            except ProcessLookupError:
                break
            except PermissionError:
                pass
            end = time.time() + grace
            while time.time() < end:
                if proc is not None:
                    proc.poll()                 # reap our own child: its group cannot empty around a zombie
                if group_gone(pgid) is True:
                    break
                time.sleep(0.05)
            if group_gone(pgid) is True:
                break
        if proc is not None:
            proc.wait()
        return group_gone(pgid) is True

    def evidence_root(self, path, record):
        """Which allowed root a file-evidence path lies under — the role worktree, the run scratch or the run
        directory (N-01) — after resolving every symbolic link; None for anything else."""
        try:
            real = os.path.realpath(path)
        except (OSError, ValueError):
            return None
        roots = (("worktree", record.get("worktree")),
                 ("run_scratch", os.path.dirname(record["prompt_path"]) if isinstance(record.get("prompt_path"), str) else None),
                 ("run_dir", str(self.run)))
        for name, root in roots:
            if not isinstance(root, str) or not root.startswith("/"):
                continue
            base = os.path.realpath(root)
            if real.startswith(base.rstrip(os.sep) + os.sep) and os.path.isfile(real):
                return name
        return None

    def validate_request(self, req, record, state_ids, unacked, substeps_used=None):
        """→ (None, the entry to persist) or (named refusal, None). `substeps_used(item id)` says how many
        sub-steps of that item are already accepted under the current recorded evidence."""
        if not isinstance(req, dict) or req.get("schema") != "ky.checkpoint_request/1":
            return "malformed", None
        if req.get("run_id") != record.get("run_id"):
            return "run_id_mismatch", None
        if req.get("fence") != record.get("fence"):
            return "fence_mismatch", None
        item = next((w for w in record.get("work_items", []) if isinstance(w, dict) and w.get("id") == req.get("item")), None)
        if item is None:
            return "item_not_assigned", None
        key, step_id, kind = item["key"], req.get("step_id"), req.get("kind")
        if not isinstance(step_id, str) or not ID_RE.match(step_id) or not (step_id == key or step_id.startswith(key + ".")):
            return "step_not_in_item", None
        if kind not in ("substep", "step", "message") or (kind == "message") != (item["kind"] == "message") \
                or (kind in ("step", "message") and step_id != key):
            return "kind_invalid", None
        if step_id in state_ids:
            return "already_accepted", None
        evidence, files = [], []
        for ev in req.get("evidence") if isinstance(req.get("evidence"), list) else []:
            if not isinstance(ev, dict):
                return "evidence_malformed", None
            if ev.get("type") == "file":
                path, digest = ev.get("path"), ev.get("sha256")
                if not (isinstance(path, str) and path.startswith("/") and "\0" not in path and len(path) <= 4096
                        and isinstance(digest, str) and SHA_RE.match(digest)):
                    return "evidence_malformed", None
                if self.evidence_root(path, record) is None:
                    return "evidence_outside_allowed_roots", None
                if sha_file(path) != digest:
                    return "evidence_hash_mismatch", None
                files.append(digest)
                evidence.append({"type": "file", "path": path, "sha256": digest})
            elif ev.get("type") in ("commit", "event", "pr", "action") and isinstance(ev.get("ref"), str):
                evidence.append({"type": ev["type"], "ref": flat(ev["ref"], 200)})
            else:
                return "evidence_malformed", None
        if item["kind"] == "message":
            if unacked is None:
                return "ack_unverifiable", None
            if key in unacked:
                return "message_still_unacked", None
        elif not files:
            return "no_verifiable_evidence", None
        if kind == "substep" and substeps_used is not None \
                and substeps_used(item["id"]) >= as_int(record.get("substep_cap"), SUBSTEP_CAP):
            return "substep_cap_reached", None
        digest = files[0] if files else sha_bytes(json.dumps(evidence, sort_keys=True).encode())
        return None, {"id": step_id, "evidence_sha256": digest, "evidence": evidence, "item": item["id"], "kind": kind,
                      "outcome": flat(req.get("outcome"), 40) or None, "note": flat(req.get("summary")),
                      "next": flat(req.get("next")), "accepted_at": utc(),
                      "accepted_by": {"controller_id": self.controller_id, "run_id": record.get("run_id")}}

    def process_outbox(self, record, refuse_all=None):
        """Validate and persist the child's checkpoint requests. `refuse_all` names why NOTHING this run returned
        is accepted (a run that tampered with its snapshot while writing role state, N-03)."""
        accepted, refused = [], []
        directory = Path(record.get("out_dir") or "/nonexistent") / "checkpoints"
        files = sorted(directory.glob("*.json")) if directory.is_dir() else []
        if not files:
            return accepted, refused
        if refuse_all:
            return accepted, [{"file": f.name, "reason": refuse_all} for f in files]
        state, _ = read_json(self.state_path)
        if not isinstance(state, dict) or not isinstance(state.get("completed_steps", []), list):
            return accepted, [{"file": f.name, "reason": "role_state_unreadable"} for f in files]
        ids = set(self.accepted_steps(state))
        unacked = None
        if self.role == "conductor":
            msgs = self.poll_inboxes() if self.event_failures < EVENT_SOURCE_FAILURE_LIMIT - 1 else None
            unacked = None if msgs is None else {str(m.get("msg_id")) for _, m in msgs}
        stored = self.ls().get("substeps")
        caps, evidence = dict(stored) if isinstance(stored, dict) else {}, self.substep_evidence()
        counted = False
        for f in files:
            req, _ = read_json(f)
            reason, entry = self.validate_request(req, record, ids, unacked,
                                                  lambda item_id: self.substep_window(item_id, caps, evidence))
            if reason:
                refused.append({"file": f.name, "reason": reason})
                continue
            ids.add(entry["id"])
            accepted.append(entry)
            if entry["kind"] == "substep":
                caps[entry["item"]] = {"count": self.substep_window(entry["item"], caps, evidence) + 1,
                                       "evidence": evidence, "at": entry["accepted_at"]}
                counted = True
        if counted:
            self.ls(lambda d: dict(d, substeps=caps))
        if accepted:
            state.setdefault("completed_steps", []).extend(accepted)
            write_json(self.state_path, state)
            lines = "".join("- %s controller %s · run %s · step %s · evidence sha256 %s · next: %s\n"
                            % (e["accepted_at"], self.controller_id, record.get("run_id"), e["id"],
                               e["evidence_sha256"], e["next"] or "-") for e in accepted)
            with open(self.journal_path, "a", encoding="utf-8") as j:
                j.write(lines)
            if self.role == "conductor":
                os.makedirs(self.run / "handled", exist_ok=True)
                for e in accepted:
                    write_json(self.run / "handled" / (e["item"] + ".json"), {
                        "schema": "ky.handled/1", "id": e["item"], "handled_at": e["accepted_at"],
                        "by": {"role": self.role, **e["accepted_by"]}, "checkpoint": e})
        return accepted, refused

    def restore_role_state(self, record, state_bytes):
        """The sole-writer check after a supervised child (plan §4a.1, N-03). → (violation, snapshot_intact).
        A role-state file that differs from what the child was given was written by the child: its version is
        kept in the run scratch and the controller's OWN copy — the bytes it held in memory, never the child's
        read-only snapshot file — is written back. `snapshot_intact` says whether that snapshot file is still
        the one the child was given."""
        snap_sha = record.get("state_snapshot_sha256")
        snap = Path(record.get("state_snapshot_path") or "/nonexistent")
        intact = sha_file(snap) == snap_sha
        violation = sha_file(self.state_path) != snap_sha
        if violation:
            try:
                write_atomic(snap.with_name("state.child_modified.json"), self.state_path.read_bytes())
            except OSError:
                pass
            write_atomic(self.state_path, state_bytes)
            self.log("%s wrote the role-state file; its version is preserved in the run scratch and the "
                     "controller's copy restored%s" % (record.get("run_id"), "" if intact else
                                                      " — its snapshot is missing or altered: the run is refused"))
        return violation, intact

    def finalize(self, record, exit_code, reason, supervised=True, state_bytes=None, actions_before=None):
        """Record the observed result; only now does the controller write role state (validated requests).
        `supervised` is False for a run inherited from a dead controller: another fenced writer may have
        written the state since, so nothing is restored and the violation flag stays unknown."""
        run_id = record.get("run_id")
        violation = intact = refuse_all = None
        if supervised and state_bytes is not None and sha_bytes(state_bytes) == record.get("state_snapshot_sha256"):
            violation, intact = self.restore_role_state(record, state_bytes)
            if violation and not intact:
                refuse_all = "state_snapshot_tampered"
        accepted, refused = self.process_outbox(record, refuse_all)
        self.state_sha = sha_file(self.state_path)
        seen = detect_quota(record.get("stdout_path", ""), record.get("stderr_path", ""))
        quota, backoff = seen["refusal"], [None]
        before = record.get("progress_before") if isinstance(record.get("progress_before"), dict) else {}
        keys = before.get("item_keys")          # the same items as "before": only a dependency OF THIS ROLE counts
        keys = keys if isinstance(keys, list) and all(isinstance(k, str) for k in keys) else None
        after = self.accepted_summary(keys)     # before the controller raises anything of its own below
        # a changed external dependency counts only when the run did not author it (N-02): owner-waits raised by
        # a job of this role are in neither fingerprint — nor is any role's wait for an item that is not this
        # role's to work on (L3-01)
        basis = "external_fingerprint" if before.get("external_fingerprint") else "dependency_fingerprint"
        dependency_changed = bool(before.get(basis)) and before[basis] != after[basis]
        progressed = (bool(accepted) or dependency_changed) and not refuse_all
        if actions_before is None and supervised is False:      # an inherited run: the listing its controller kept
            listing = record.get("actions_before") if isinstance(record.get("actions_before"), dict) else {}
            names, _ = read_json(listing.get("path"))
            if isinstance(names, list) and sha_file(listing.get("path")) == listing.get("sha256"):
                actions_before = set(n for n in names if isinstance(n, str))
        job_actions = None
        if reason != "launch_failed":
            try:
                job_actions = self.reconcile_job_actions(run_id, actions_before, own_window=supervised)
            except (self.ka.ActionError, OSError) as e:
                job_actions = {"error": "%s: %s" % (type(e).__name__, flat(e, 160))}
                self.log("job actions of %s not reconciled (%s)" % (run_id, job_actions["error"]))
        notify_level = [None]

        def fn(d):
            q = d.get("quota") if isinstance(d.get("quota"), dict) else {}
            level, notified = as_int(q.get("level")), as_int(q.get("notified_level"))
            count = as_int(d.get("no_progress_count"))
            minutes, not_before = 0, q.get("not_before")
            if progressed:
                count, level, notified, not_before = 0, 0, 0, None
            if quota:
                level = min(level + 1, len(BACKOFF_MINUTES))
                minutes = BACKOFF_MINUTES[level - 1]
                now = time.time()
                step_until, resets = now + minutes * 60 * self.scale, seen["resets_at"]
                sooner = resets is not None and now < resets < step_until
                # back off until min(next backoff step, the refusing window's reset); a reset time that is not in
                # the future is recorded but never shortens the step (it would relaunch at once)
                not_before = resets if sooner else step_until
                backoff[0] = {"source": seen["source"], "status": seen["status"],
                              "rate_limit_type": seen["rate_limit_type"], "resets_at": resets,
                              "backoff_step_minutes": minutes, "backoff_step_until": step_until,
                              "backoff_until": not_before, "backoff_basis": "resets_at" if sooner else "backoff_step"}
                if level > notified:
                    notified, notify_level[0] = level, minutes
            elif not progressed and reason != "stopped":    # a run the owner's stop cut short proves nothing either way
                count += 1
            d["quota"] = {"level": level, "notified_level": notified, "not_before": not_before,
                          "backoff_minutes": minutes, "resets_at": seen["resets_at"] if quota else None,
                          "backoff_basis": backoff[0]["backoff_basis"] if backoff[0] else None}
            d["no_progress_count"] = count
            d["expected_child"] = None
            d["last_run_id"] = run_id
            record["backoff_minutes"] = minutes
            return d
        st = self.ls(fn)
        record.update(ended_at=utc(), exit_code=exit_code, ended_reason=reason, state_violation=violation,
                      snapshot_intact=intact, job_actions=job_actions,
                      accepted=[e["id"] for e in accepted], refused=refused, quota_refusal=quota,
                      quota=backoff[0], rate_limit_status_unrecognised=seen["unrecognised"],
                      progress_after=after, dependency_changed=dependency_changed, progressed=progressed,
                      provider_session_id=provider_session(record.get("stdout_path", "")))
        write_json(self.loop_dir / (str(run_id) + ".json"), record)
        if supervised:                          # an inherited run's action is settled by reconcile_actions()
            self.settle_launch_action(record)
        self.write_owner(None)
        self.release_item_locks([w.get("id") for w in record.get("work_items", []) if isinstance(w, dict)])
        self.log("%s ended (%s, exit %s): accepted %d, refused %d, progressed=%s, quota_refusal=%s"
                 % (run_id, reason, exit_code, len(accepted), len(refused), progressed, quota))
        if refuse_all:
            self.raise_attention(
                "loop-%s-state-tamper-%s" % (self.role, re.sub(r"[^a-z0-9-]", "-", str(run_id).lower())),
                "The %s job %s wrote the role-state file AND its read-only state snapshot is missing or altered. "
                "The controller restored its own copy of the state, accepted nothing the run returned and counted "
                "it as no progress. What should happen with that run's work?" % (self.role, run_id),
                ["run record: %s" % (self.loop_dir / (str(run_id) + ".json")),
                 "the child's version of the state: %s" % Path(record.get("state_snapshot_path") or "").with_name(
                     "state.child_modified.json")],
                message="%s loop: run %s tampered with role state and its snapshot; the run was refused"
                        % (self.role, run_id))
        if notify_level[0]:
            self.notify("%s loop: quota refusal; backing off %d min, then resuming automatically"
                        % (self.role, notify_level[0]), "info")
        if not quota and not progressed and st["no_progress_count"] >= NO_PROGRESS_LIMIT:
            self.open_breaker(st["no_progress_count"])

    # ---- the control loop
    def loop(self):
        """Durable state is honoured in this order before EVERY launch: signal · STOP_<role> · the `enabled`
        switch · the owner's queued commands · completion (planner) / a valid OWNER_RESUME (conductor) · the global
        HOLD · an owner pause · the circuit breaker · launch preconditions · quota backoff · sole-writer check ·
        eligible work · unfinished actions · and once more, immediately before the launch, STOP / enabled /
        commands / HOLD / pause. A launch that finds every item locked by another actor is a wait
        (wait_items_locked), never an immediate second look."""
        while True:
            if self.signal:
                raise Interrupted()
            if self.stop_path.exists():
                self.disable("STOP_%s present" % self.role)
                self.log("STOP_%s present: exiting" % self.role)
                return 0
            st = self.ls()
            if st.get("enabled") is not True:
                self.log("not enabled (%s): exiting; `kyctl.sh start %s` enables after its guards"
                         % (st.get("reason") or "no admission record", self.role))
                return 0
            if self.apply_commands():
                continue                        # a command may have disabled the loop or changed its evidence
            self.commands_overdue()             # R16: a queue that stays blocked says so, once
            if self.commands_blocked:
                self.log_once("a queued command cannot be settled yet (%s): nothing is launched meanwhile"
                              % self.commands_blocked)
                self.wait("commands_pending", COMMAND_POLL_S)
                continue
            if self.role == "planner" and (self.run / "WAVE_B_DONE").exists():
                ok, why = self.verify_wave_b_done()
                if not ok:
                    raise Refusal(["wave_b_done_unverified: " + why])
                self.disable("WAVE_B_DONE verified (%s)" % why)
                self.log("Wave B complete (verified: %s): exiting" % why)
                return 0
            if self.role == "conductor" and self.owner_resume() is None:
                self.log("no valid OWNER_RESUME.json: nothing to do, nothing raised")
                return 0
            if (self.root / "HOLD").exists():
                self.wait("hold", HOLD_POLL_S)
                continue
            pause = self.owner_pause()
            if pause:                           # no model job is launched by any role while the owner has paused
                if (st.get("pause") or {}).get("state") != pause:
                    self.log("owner pause (%s): no model job is launched until an owner resume" % pause)
                    self.ls(lambda d: dict(d, pause={"state": pause, "since": utc()}))
                if pause.startswith("unknown"):
                    self.queue_attention(pause)  # R16: THIS pause no owner resume ends — somebody has to look
                self.wait("owner_paused", HOLD_POLL_S)
                continue
            if st.get("pause"):
                self.ls(lambda d: {k: v for k, v in d.items() if k != "pause"})
            if self.breaker_gate(st):
                return 0
            fresh = not self.verified_once
            if fresh:
                self.verify_launch()
                self.verified_once = True
                if self.role == "conductor":
                    self.start_dispatcher()
            not_before = (st.get("quota") or {}).get("not_before") if isinstance(st.get("quota"), dict) else None
            if isinstance(not_before, (int, float)) and time.time() < not_before:
                self.wait("quota_backoff", real_seconds=min(not_before - time.time(), HOLD_POLL_S))
                continue
            if sha_file(self.state_path) != self.state_sha:
                raise Refusal(["role_state_changed_outside_controller: %s was written while this controller "
                               "held the role lock (it is the sole writer, plan §4a.1)" % self.state_path.name])
            items = self.eligible_items()
            if not items:
                self.wait("no_eligible_work", WAIT_POLL_S)
                continue
            if not fresh:
                self.verify_launch()
            with guarded("reconciliation"):
                self.reconcile_actions()        # before any relaunch: nothing unfinished of ours is left behind
            closed = self.launch_gate()
            if closed:
                self.log("launch withheld at the last look (%s)" % closed)
                continue
            if self.run_job(items) == "items_locked":
                self.wait_items_locked()

    def wait_items_locked(self):
        """Every eligible message is locked by another actor — a live one that is acting on it, or one that
        cannot be judged (attention was raised). Nothing was launched and nothing is relaunched: this is a
        waiting state of the CONTROLLER (`items_locked`, counted in counters.item_lock_waits), for one poll
        period, after which every gate is read again from the top."""
        held = sorted(self.items_waiting)

        def fn(d):
            counters = dict(d.get("counters") or {})
            counters["item_lock_waits"] = as_int(counters.get("item_lock_waits")) + 1
            return dict(d, counters=counters, item_lock_wait={"items": held, "at": utc()})
        self.ls(fn)
        self.log("nothing launched: %s locked by another actor; waiting" % ", ".join(held))
        self.wait("items_locked", WAIT_POLL_S)

    def acquire(self):
        return self.acquire_lock()

    def prepare(self):
        """Before the loop, as the lock holder: recovery of whatever a previous controller left unfinished."""
        os.makedirs(self.loop_dir, exist_ok=True)
        self.load_siblings()
        self.state_sha = sha_file(self.state_path)
        self.reconcile_actions(full=True)

    def state_unreadable(self, refusal):
        """loops/<role>.json exists and cannot be read (N-08). It is never rewritten from empty; the loop is
        refused — STOP_<role>, since `enabled: false` cannot be recorded in a file nobody can read — and ONE
        attention item is raised. A loop whose switch cannot be read is not admitted, so nothing runs."""
        self.log("REFUSED: %s" % refusal)
        try:
            if self.lock_held:                  # only the lock holder stops the loop; a duplicate start never does
                self.ensure_stop("loop state unreadable")
        except Exception as e:
            self.log("the STOP file could not be written (%s)" % type(e).__name__)
        self.raise_attention(
            "loop-%s-state-unreadable" % self.role,
            "The %s loop's own record %s exists but cannot be read. It holds the admission switch, the breaker and "
            "the no-progress count, so it is never rewritten from empty and the loop does not run. Repair it?"
            % (self.role, refusal.path),
            ["%s" % refusal], options=[{"id": "repair", "text": "Repair or remove the file by hand, then "
                                                               "`kyctl.sh start %s --clear-stop`." % self.role},
                                       {"id": "keep-stopped", "text": "Leave the %s loop stopped." % self.role}],
            message="%s loop refused: its loop-state file cannot be read" % self.role)

    def main(self):
        """Exit 0 for every ending that launchd must not respawn — and that includes every UNEXPECTED exception
        (R10) and a refused environment (N4-01): each becomes the one-awaiting-item + STOP + disabled refusal,
        never a traceback and never an exit status launchd answers with a respawn. Only a signal without a STOP
        file ends non-zero."""
        if not self.run.is_dir():
            return self.no_run_directory()
        try:
            return self.run_controller()
        except LoopStateUnreadable as r:
            self.state_unreadable(r)
            return 0
        except Refusal as r:
            self.refuse(r.reasons)
            return 0
        except Interrupted:
            try:
                if self.stop_path.exists():
                    self.disable("STOP_%s present" % self.role)
                    return 0
            except Exception as e:
                self.log("signalled; the stop could not be recorded (%s)" % type(e).__name__)
                return 0
            self.log("terminated by signal %d without a STOP file" % self.signal)
            return 128 + self.signal
        except Exception as e:                  # nothing leaves this process as a traceback launchd would respawn
            self.refuse(Fault("main", e).reasons)
            return 0
        finally:
            if self.lock_held:
                try:
                    self.ls(lambda d: dict(d, controller=None, waiting=None, expected_child=d.get("expected_child")))
                except Exception as e:
                    self.log("the loop state was not updated at exit (%s)" % type(e).__name__)
                try:
                    self.release_lock()
                except Exception as e:
                    self.log("the lock was not released at exit (%s)" % type(e).__name__)

    def no_run_directory(self):
        """$KY_RUN is not a directory: there is nowhere to write an awaiting item, a STOP file or the switch — and
        nothing is created in its place. What is left of the one shape of a refusal (N4-01) is ONE notification
        attempt (kynotify.sh cannot journal it either, and says so), a log line and exit 0: launchd does not
        respawn this every ten seconds. → 0."""
        self.log("REFUSED: $KY_RUN is not a directory: %s" % self.run)
        try:
            result = self.submit_notification(
                flat("%s loop did not start: $KY_RUN is not a directory: %s" % (self.role, self.run), 300), "decision")
        except Exception as e:
            result = {"notify": "unknown", "rc": None, "journal": None, "error": type(e).__name__}
        self.log("notification (decision): notify=%s journal=%s rc=%s — nothing can be recorded without a run "
                 "directory; once it exists, `kyctl.sh start %s`"
                 % (result.get("notify"), result.get("journal"), result.get("rc"), self.role))
        return 0

    def refuse_environment(self):
        """Raise what main() or __init__ found wrong with this controller's environment (startup_refusal: a
        credential variable NAME, a bad KY_LOOP_SLEEP_SCALE) as a refused precondition — by the lock holder, so
        that it takes the one shape of every refusal (N4-01). The control modules are loaded first, so that its
        one notification is a recorded side effect; what THEY refuse is raised with it."""
        reasons = list(self.startup_refusal)
        try:
            self.load_siblings()
        except Refusal as r:
            reasons += r.reasons
        raise Refusal(reasons)

    def refuse(self, reasons):
        """A refusal by the LOCK HOLDER is the full shape (STOP, one awaiting item, disabled). An instance that
        does not hold the role lock — a duplicate start that failed before or while acquiring it — raises its one
        attention item only: it never stops a loop it cannot see."""
        if self.lock_held:
            self.raise_precondition(reasons)
        else:
            self.log("REFUSED before the role lock was held: " + "; ".join(reasons))
            self.raise_attention(
                "loop-%s-start-fault" % self.role,
                "A start of the %s loop controller failed before it held the role lock (%s). Nothing was stopped "
                "and nothing was launched by it." % (self.role, flat(reasons[0], 200)),
                ["precondition: %s" % flat(r, 400) for r in reasons],
                message="%s loop: a controller start failed before taking the role lock" % self.role)

    def run_controller(self):
        if not self.acquire():
            self.record_lock_wait()
            return 0
        signal.signal(signal.SIGTERM, self.on_signal)
        signal.signal(signal.SIGINT, self.on_signal)
        self.heartbeat()
        if self.ls().get("lock_wait") or self.ls().get("lock_release"):     # what an earlier instance observed
            self.ls(lambda d: {k: v for k, v in d.items() if k not in ("lock_wait", "lock_release")})
        try:
            with guarded("prepare"):
                if self.startup_refusal:        # N4-01: one item and a stop — or nothing, for a loop not admitted
                    self.refuse_environment()
                self.prepare()
        except Refusal as r:
            if self.admitted():
                raise
            # a loop that is stopped or was never started raises nothing: no awaiting file, no STOP of its own
            self.log("not admitted (STOP file or not enabled); recovery refused and nothing raised: %s" % r)
            if self.stop_path.exists():
                self.disable("STOP_%s present" % self.role)
            return 0
        return self.loop()


class VetoController(Controller):
    """The deterministic veto-window controller (plan §4a.2 "Roles", §4a.3, §13 "veto expired"). It launches no
    model, ever. As the sole holder of the `veto` lock it calls kyveto.py's `tick` — the one actor that makes a
    veto-class surrogate decision effective — and waits, in this process, until the earliest pending veto
    deadline, a new command for the veto role, or the poll period. kyveto itself keeps decisions pending under
    $KY_ROOT/HOLD, an owner pause and STOP_veto; this controller just keeps ticking, and exits on STOP_veto or
    when it is not enabled.

    Of the owner's commands addressed to the veto role, `veto <decision-id>` is the handler's (consumed by the
    tick under the decision's lock). Every other one is this controller's, applied before each tick as the holder
    of the veto lock (apply_commands): `status`, `loops stop veto` — the owner's queued stop ends this loop —,
    `loops status veto` and `decide`; anything else is rejected by name.

    Attention (what `kyveto.py tick` reports with exit 3) is never ticked through:
      * something that will be reported again on every tick — an unreconciled publication or execution, a
        decision log or command queue that cannot be read, a command that could not be settled — opens the
        loop's breaker-equivalent: one awaiting file (blocks the loop), one notification, `enabled: false`, and a
        restart is refused until the recorded evidence has changed;
      * something final for one decision (failed, refused — a hard stop is never delegated —, a veto that came
        too late) is raised once as its own awaiting item and notification; the loop goes on, since that decision
        is never reported again;
      * decisions HELD because the authorised bundle cannot be read raise ONE attention item and the loop goes
        on: the hold ends by itself, and an owner veto is honoured meanwhile."""

    COMMANDS = ("status", "loops", "decide")    # the queued commands this controller applies (kyctl.sh's usage
                                                # text names exactly these; `veto` is the handler's)
    receipt_verified = None     # sha256 of the installation receipt the installed bundle was verified under
    authority_seen = None       # the authority source last logged (logged only when it changes)
    authority_source = None     # {"known", "source"} of the authority given to the last tick

    def heartbeat(self, waiting=None):
        def fn(d):
            d["controller"] = self.identity()
            d["waiting"] = waiting
            d.setdefault("breaker", {"open": False, "history": []})
            d["test_hooks"] = self.test_hooks()
            return d
        self.ls(fn)

    def acquire(self):
        """Another handler's tick (the bootstrap supervisor's, or a self-fenced `kyveto.py tick`) holds the same
        lock only for its own duration: wait for it, bounded, instead of exiting for good on a collision."""
        end = time.time() + VETO_LOCK_WAIT_S * self.scale
        while not self.acquire_lock():
            if (self.lock_refusal or {}).get("state") != "live" or time.time() >= end:
                return False
            time.sleep(max(0.05, self.scale))
        return True

    def prepare(self):
        """kyveto's tick reconciles its own unfinished actions itself; what is left for this controller is a
        notification a previous veto controller began and never settled."""
        self.load_siblings()
        try:
            for rec in self.ka.scan(self.run)[0]:
                actor = rec.get("actor") if isinstance(rec.get("actor"), dict) else {}
                if rec["state"] == "INTENDED" and rec.get("kind") == "notification" and actor.get("role") == self.role \
                        and actor.get("holder_kind") == "controller" and actor.get("controller_id") != self.controller_id:
                    self.reconcile_soft(rec)
        except (self.ka.ActionError, OSError) as e:
            self.log("earlier notifications not reconciled (%s)" % type(e).__name__)

    def verify_veto(self):
        """Admission of the veto loop — the same gate as the model loops (R9): an installation receipt whose mode
        is bootstrap or final AND a passing kyversion.sh in the matching mode (`--bootstrap` for a bootstrap
        receipt, none for a final one). Read on EVERY pass; kyversion.sh is run at start-up and again whenever
        the receipt's bytes change. A receipt that is missing, unreadable or of any other mode, and a kyversion.sh
        that is missing or does not pass, refuse: this loop publishes delegated decisions and writes activation
        records, so the mere existence of a receipt file grants nothing."""
        path = self.run / "INSTALL_RECEIPT.json"
        receipt, err = read_json(path)
        digest = sha_file(path)
        if err == "missing":
            raise Refusal(["install_receipt_missing: %s" % path])
        if err or not isinstance(receipt, dict) or digest is None:
            raise Refusal(["install_receipt_unreadable"])
        mode = receipt.get("mode")
        if not isinstance(mode, str) or mode not in RECEIPT_MODES[self.role]:
            raise Refusal(["install_receipt_mode: got %r, the veto loop needs %s"
                           % (mode, " or ".join(RECEIPT_MODES[self.role]))])
        if digest == self.receipt_verified:
            return
        if self.test_hooks() and self.real_context() == "launchd":
            raise Refusal(["test_hooks_in_launchd_context: a test hook is set for a controller that runs under launchd"])
        args = KYVERSION_ARGS[mode]
        rc = self.run_helper("kyversion.sh", args, 300)
        if rc is None:
            raise Refusal(["kyversion_missing: %s" % (self.fleet / "kyversion.sh")])
        if rc != 0:
            raise Refusal(["kyversion_failed: rc=%d (kyversion.sh %s, for a %s receipt)" % (rc, " ".join(args), mode)])
        self.receipt_verified = digest
        bundle = {"verified_at": utc(), "by": "kyversion.sh %s" % " ".join(args), "receipt_mode": mode,
                  "receipt_sha256": digest, "manifest_digest": None}
        self.ls(lambda d: dict(d, bundle_verified_at=bundle["verified_at"], bundle=bundle))

    def authority(self):
        """The authorised bundle every tick is given explicitly (R5). → ({"source_commit", "entrypoints_digest"},
        where it was read) or (None, why it cannot be read).

        When an activation chain exists it is the ONLY source: the terminal link's source commit, and the
        entrypoints digest of that link's manifest — a manifest file whose digest, recomputed here, IS the digest
        the link binds (the path the record names, else the installed VERSIONS.json / VERSIONS.bootstrap.json). A
        chain that is broken, forked or whose manifest cannot be found is unknown: it never falls back to an
        older source. Without any activation record the source is PLANNER_STATE.json `authorised_source`
        {source_commit, entrypoints_digest}, which the fenced planner writer keeps."""
        if any(self.run.glob("ACTIVATION_RECORD*.json")):
            links, err = self.activation_chain()
            if err:
                return None, err
            link = links[-1]
            if not link["commit"]:
                return None, "activation_record_invalid: %s names no source commit" % link["file"]
            doc, _ = read_json(self.run / link["file"])
            doc = doc if isinstance(doc, dict) else {}
            bound = doc.get("new_manifest") if isinstance(doc.get("new_manifest"), dict) else {}     # as kyveto writes it
            named = [v for v in [bound.get("path")] + [doc.get(k) for k in ("new_manifest_path", "manifest_path",
                                                                           "final_manifest_path")]
                     if isinstance(v, str) and v and "\0" not in v]
            tried = []
            for cand in named + list(MANIFEST_FILES):
                path = Path(cand) if os.path.isabs(cand) else self.run / cand
                digest, why = manifest_entrypoints(path, link["manifest_digest"])
                if digest and bound.get("entrypoints_digest") not in (None, digest):
                    digest, why = None, "the record binds another entrypoints digest than this manifest gives"
                if digest:
                    return ({"source_commit": link["commit"], "entrypoints_digest": digest},
                            "activation_chain: %s, manifest %s" % (link["file"], path.name))
                tried.append("%s (%s)" % (path.name, why))
            return None, ("activation_manifest_unreadable: no manifest of digest %s for %s — %s"
                          % (link["manifest_digest"][:12], link["file"], "; ".join(tried)))
        state, _ = read_json(self.run / "PLANNER_STATE.json")
        source = state.get("authorised_source") if isinstance(state, dict) else None
        if isinstance(source, dict) and isinstance(source.get("source_commit"), str) \
                and HEX_COMMIT.match(source["source_commit"]) and isinstance(source.get("entrypoints_digest"), str) \
                and SHA_RE.match(source["entrypoints_digest"]):
            return ({"source_commit": source["source_commit"], "entrypoints_digest": source["entrypoints_digest"]},
                    "planner_state")
        return None, ("authorised_source_unreadable: no activation record, and PLANNER_STATE.json carries no "
                      "authorised_source {source_commit, entrypoints_digest}")

    def tick(self):
        """The ONE call site of the veto handler: in-process, as the controller that holds the veto lock
        (`kyveto.py tick --as <controller_id> --holder-kind controller`). The handler reads the wall clock itself
        — no time is passed — and is GIVEN the authority (R5): the bundle this controller established
        (authority()), or kyveto.UNKNOWN when it could not, in which case the handler holds every decision (an
        owner veto is still honoured) and reports one `authority_unknown` problem. Any failure to complete a pass
        is a refused precondition — never a retry loop."""
        kv = self.kv
        authorised, source = self.authority()
        if source != self.authority_seen:
            self.log("authority: %s" % (source if authorised else "UNKNOWN — %s; decisions are held" % source))
            self.authority_seen = source
        self.authority_source = {"known": authorised is not None, "source": source}
        try:
            return kv.tick(env=kv.Env(), authorised=authorised if authorised is not None else kv.UNKNOWN,
                           holder=self.controller_id, holder_kind="controller", log=self.log)
        except kv.NotHolder as e:
            raise Refusal(["veto_lock_not_held: %s" % flat(e, 200)])
        except Exception as e:
            raise Refusal(["veto_tick_failed: %s: %s" % (type(e).__name__, flat(e, 200))])

    def raise_authority_unknown(self, problem):
        """Decisions are HELD because the authorised bundle cannot be read: ONE attention item while that lasts
        (none while one is open), and the loop goes on ticking — the hold ends by itself once the authority can
        be read, and an owner veto is honoured meanwhile."""
        why = (self.authority_source or {}).get("source")
        self.raise_attention(
            "loop-veto-authority-unknown",
            "The veto handler holds veto-class decisions because the authorised bundle cannot be established "
            "(%s). Nothing becomes effective and nothing fails while that lasts. Which bundle is authorised?"
            % flat(why, 240),
            ["veto tick: %s" % flat(problem, 300), "authority: %s" % flat(why, 300),
             "activation chain: %s" % (self.run / "ACTIVATION_RECORD*.json"),
             "planner state: %s" % (self.run / "PLANNER_STATE.json")],
            options=[{"id": "repair", "text": "Repair the activation chain / its manifest, or record `authorised_source` "
                                              "{source_commit, entrypoints_digest} in PLANNER_STATE.json as the fenced "
                                              "planner writer; the held decisions then proceed by themselves."},
                     {"id": "veto", "text": "Veto the held decisions (`veto <decision-id>`)."}],
            item="loop.veto", message="veto loop: decisions are held — the authorised bundle cannot be established")

    def record_tick(self, report):
        """→ the earliest deadline (epoch) among decisions still inside their window, or None."""
        decisions = [d for d in report.get("decisions") or [] if isinstance(d, dict)]
        deadlines = sorted(t for t in (self.ka.parse_utc(d.get("veto_deadline")) for d in decisions
                                       if d.get("outcome") == "pending") if t is not None)
        outcomes = {}
        for d in decisions:
            outcomes[str(d.get("outcome"))] = outcomes.get(str(d.get("outcome")), 0) + 1
        holds = [str(h) for h in report.get("holds") or []]
        pending = sum(1 for d in decisions if d.get("outcome") in ("pending", "held", "locked", "blocked"))

        def fn(d):
            before = d.get("veto") if isinstance(d.get("veto"), dict) else {}
            d["veto"] = {"last_tick_at": utc(), "ticks": as_int(before.get("ticks")) + 1, "pending": pending,
                         "next_deadline": utc(t=deadlines[0]) if deadlines else None, "holds": holds,
                         "outcomes": outcomes, "attention": bool(report.get("attention")),
                         "problems": len(report.get("problems") or []),
                         "authority_source": (report.get("authority") or {}).get("source"),
                         "authority": self.authority_source}
            d["controller"] = self.identity()
            d["last_iteration_at"] = utc()      # the last SUCCESSFUL control iteration: a completed tick
            d["waiting"] = "hold" if holds else "veto_window" if deadlines else "idle"
            return d
        self.ls(fn)
        return deadlines[0] if deadlines else None

    @staticmethod
    def attention_items(report):
        """(persistent, final): what would be reported again on every tick, and what is final for one decision.
        The handler's `authority_unknown` problem is neither: its decisions are held, not stuck — see
        held_for_authority()."""
        persistent = ["problem: %s" % flat(x, 200) for x in report.get("problems") or []
                      if not str(x).startswith("authority_unknown")]
        final = []
        for d in report.get("decisions") or []:
            if isinstance(d, dict) and d.get("attention"):
                text = "%s: %s%s" % (d.get("id"), d.get("outcome"), " (%s)" % flat(d["reason"], 160) if d.get("reason") else "")
                if d.get("outcome") == "blocked":
                    persistent.append(text)
                else:
                    final.append((str(d.get("id")), text))
        for c in report.get("commands") or []:
            if isinstance(c, dict) and c.get("attention"):
                persistent.append("command %s: %s (%s)" % (c.get("id"), c.get("status"), flat(c.get("reason"), 160)))
        if report.get("attention") and not persistent and not final \
                and not VetoController.held_for_authority(report):
            persistent.append("attention reported without a named item")
        return persistent, final

    @staticmethod
    def held_for_authority(report):
        """The handler's one `authority_unknown` problem, or None."""
        return next((str(x) for x in report.get("problems") or [] if str(x).startswith("authority_unknown")), None)

    def raise_final(self, decision_id, text):
        slug = "veto-attention-" + re.sub(r"[^a-z0-9-]", "-", decision_id.lower())
        if self.open_awaiting(slug):
            return
        doc = self.write_awaiting(
            slug, "The veto handler finished decision %s in a way that needs the owner's attention: %s. Nothing "
                  "further is done for it by the loop. What should happen with it?" % (decision_id, text),
            [{"id": "acknowledge", "text": "Seen; nothing further."},
             {"id": "correct-tracker", "text": "Correct or withdraw the published tracker decision by hand."}],
            None, ["veto tick: %s" % text, "decision log: %s" % (self.run / "DECISIONS_SURROGATE.jsonl")],
            item=decision_id, blocks="none")
        self.notify("veto handler: %s — needs your attention; see %s" % (flat(text, 140), doc["id"]), "decision")

    def attention_fingerprint(self):
        """What must change before a veto loop stopped for attention may tick again: the decision log, the state
        and observed result of the handler's own action records, the command queue — or the AUTHORITY: the
        authorised bundle and where it was read from (authority()), so that a stop taken while the bundle could
        not be established, or under another bundle, lifts by itself once the authority returns or changes."""
        try:
            bundle, source = self.authority()
        except Exception as e:                  # what cannot be read is its own, stable, value — never "no change"
            bundle, source = None, "authority_unreadable: %s" % type(e).__name__
        actions = []
        directory = self.run / "actions"
        for path in sorted(directory.glob("SD-*.json")) if directory.is_dir() else []:
            doc, _ = read_json(path)
            actions.append([path.name, doc.get("state"), sha_bytes(json.dumps(doc.get("result"), sort_keys=True).encode())]
                           if isinstance(doc, dict) else [path.name, "unreadable", sha_file(path)])
        directory = self.run / "commands"
        parts = {"decisions": sha_file(self.run / "DECISIONS_SURROGATE.jsonl"), "actions": actions,
                 "authority": {"known": bundle is not None, "bundle": bundle, "source": source},
                 "commands": [[q.name, sha_file(q)] for q in sorted(directory.glob("*.json"))]
                 if directory.is_dir() else []}
        return sha_bytes(json.dumps(parts, sort_keys=True).encode())

    def open_attention(self, items):
        """The veto loop's stop for something the handler would report again on every tick: one awaiting item
        (blocks the loop), one notification, `enabled: false`. No second item and no second notification while
        an item naming THESE things is open; a stop for something else is a new item (R16) — the item tells the
        owner to reconcile and start the loop again, nobody has to close it, and a later, different stop must not
        hide behind it with nobody told."""
        slug, fingerprint = "loop-veto-attention", self.attention_fingerprint()
        named, doc = ["veto tick: %s" % x for x in items[:20]], None
        for path in self.open_awaiting(slug):
            seen = read_json(path)[0]
            if isinstance(seen, dict) and isinstance(seen.get("evidence"), list) \
                    and [e for e in seen["evidence"] if not str(e).startswith("evidence fingerprint ")] == named:
                doc = seen
                break
        fresh = doc is None
        if fresh:
            doc = self.write_awaiting(
                slug, "The veto handler reported something it cannot resolve by itself and would report again on "
                      "every tick, so the veto loop stopped itself. What should change before it runs again?",
                [{"id": "reconcile-and-restart", "text": "Reconcile the named action record or repair the named file "
                                                         "(the evidence must differ from the recorded fingerprint), "
                                                         "then `kyctl.sh start veto`."},
                 {"id": "keep-stopped", "text": "Leave the veto loop stopped: no veto-class decision becomes effective."}],
                "reconcile-and-restart", named + ["evidence fingerprint %s" % fingerprint])

        def fn(d):
            br = d.get("breaker") if isinstance(d.get("breaker"), dict) else {}
            d["breaker"] = {"open": True, "opened_at": utc(), "evidence_fingerprint": fingerprint, "awaiting": doc,
                            "kind": "veto_attention", "history": br.get("history") or []}
            d.update(enabled=False, reason="veto handler needs attention: %s" % flat(items[0], 160),
                     updated_at=utc(), updated_by=self.controller_id)
            return d
        self.ls(fn)
        self.log("veto handler needs attention (%s): loop disabled" % "; ".join(items[:5]))
        if fresh:
            self.notify("veto loop stopped: %s; see %s" % (flat(items[0], 120), doc["id"]), "decision")

    def attention_gate(self, st):
        """True → refused: the loop stopped for attention and the recorded evidence has not changed since."""
        br = st.get("breaker") if isinstance(st.get("breaker"), dict) else {}
        if not br.get("open"):
            return False
        now_fp = self.attention_fingerprint()
        if now_fp == br.get("evidence_fingerprint"):
            self.log("stopped for attention since %s and evidence unchanged — restart refused" % br.get("opened_at"))
            doc = br.get("awaiting") if isinstance(br.get("awaiting"), dict) else None
            if doc and ID_RE.match(str(doc.get("id", ""))) and not (self.run / "awaiting" / (doc["id"] + ".json")).exists():
                os.makedirs(self.run / "awaiting", exist_ok=True)
                write_json(self.run / "awaiting" / (doc["id"] + ".json"), doc)     # same id: no new owner-wait
            self.disable("veto handler needs attention; evidence unchanged", force=True)
            return True

        def fn(d):
            b = d.get("breaker") if isinstance(d.get("breaker"), dict) else {}
            hist = (b.get("history") or []) + [{"at": utc(), "from": b.get("evidence_fingerprint"), "to": now_fp,
                                                "by": self.controller_id}]
            d["breaker"] = {"open": False, "history": hist[-20:]}
            return d
        self.ls(fn)
        self.log("attention stop lifted: recorded evidence changed")
        return False

    # ---- the veto role's own commands (plan §4a.5): everything but `veto <decision-id>`, which is the handler's
    def apply_commands(self):
        """Settle the QUEUED commands addressed to the veto role that are this CONTROLLER's — `status`, `loops
        stop|status veto`, `decide` for an item this loop raised; anything else it rejects by name — through
        kycommands.apply, as the holder of the veto lock, BEFORE the handler's tick sees the queue. `veto
        <decision-id>` is never touched here: kyveto's tick consumes it under the decision's lock. Each command
        has its own target, so one that has to wait (a held lock) does not keep the others, or the tick, waiting.
        → True when at least one was settled (the caller re-reads STOP and the switch before anything else)."""
        self.commands_blocked = None
        try:
            queue = self.kc.pending(self.run, self.role)
        except (self.kc.CommandError, OSError) as e:    # the tick reports an unreadable queue as its own problem
            self.log("command queue not read (%s): nothing applied by the controller" % type(e).__name__)
            return False
        settled = False
        for doc in queue:
            if doc.get("command") == "veto":
                continue
            if self.apply_one(self.role, doc, in_order=False):
                settled = True
            elif self.commands_blocked:
                self.log_once("a queued command cannot be settled yet (%s)" % self.commands_blocked)
        self.close_answered_waits()             # R15: an answered owner-wait an earlier look could not close
        return settled

    def handle_command(self, role, cmd):
        """What the veto CONTROLLER carries out itself: `status` (its `kyctl.sh status` line), `loops stop veto`
        (the switch, tagged with the command id — the loop then ends at its next look), `loops status veto`, and
        `decide` for an awaiting item this loop raised. Everything else is rejected by name."""
        if cmd.get("command") in self.COMMANDS:
            return super().handle_command(role, cmd)
        raise self.kc.Reject("unsupported_by_veto_role: %s (the veto controller takes status, loops stop|status "
                             "veto and decide; `veto <decision-id>` is settled by the veto handler)" % cmd.get("command"))

    def queued_commands(self):
        try:
            return {str(d.get("id")) for d in self.kc.pending(self.run, "veto")}
        except (self.kc.CommandError, OSError):
            return set()

    def wait_for_event(self, deadline, seen):
        """Wait HERE — never in a model — until the earliest pending veto deadline (an absolute time, never
        scaled), a command for the veto role that was not queued at the last tick, the poll period, STOP_veto or
        a signal."""
        end = time.time() + VETO_POLL_S * self.scale
        if deadline is not None:
            end = min(end, deadline)
        step = max(0.05, COMMAND_POLL_S * self.scale)
        while True:
            if self.signal:
                raise Interrupted()
            now = time.time()
            if now >= end or self.stop_path.exists() or self.queued_commands() - seen:
                return
            time.sleep(min(step, end - now, 0.25))

    def loop(self):
        while True:
            if self.signal:
                raise Interrupted()
            if self.stop_path.exists():
                self.disable("STOP_%s present" % self.role)
                self.log("STOP_%s present: exiting" % self.role)
                return 0
            st = self.ls()
            if st.get("enabled") is not True:
                self.log("not enabled (%s): exiting; `kyctl.sh start %s` enables after its guards"
                         % (st.get("reason") or "no admission record", self.role))
                return 0
            self.verify_veto()
            if self.apply_commands():
                continue                        # a command may have stopped this loop: STOP and the switch first
            self.commands_overdue()             # R16: a command of this role that stays blocked says so, once
            if self.attention_gate(st):
                return 0
            report = self.tick()
            deadline = self.record_tick(report)
            persistent, final = self.attention_items(report)
            held = self.held_for_authority(report)
            if held:
                self.raise_authority_unknown(held)
            for decision_id, text in final:
                self.raise_final(decision_id, text)
            if persistent:
                self.open_attention(persistent)
                return 0
            self.wait_for_event(deadline, self.queued_commands())


# ───────────────────────────────── entry points ─────────────────────────────────

USAGE = ("usage: kyloop.py planner|conductor|veto\n"
         "       kyloop.py admin enable|disable <loop> --reason TEXT [--by WHO]\n"
         "       kyloop.py admin show <loop> | child <loop>\n"
         "       kyloop.py admin expected-qualification|launch-config planner|conductor")


def recorded_child(run_dir, loop):
    """(state, pid, run id) of the child that loop's controller recorded — for `kyctl.sh status` and `stop` (N-07).
    state: none (no child is recorded) · pending (one was about to be started and was never identified) · alive ·
    survivors (its leader is gone, its process group is not empty) · gone · unknown. What the role lock's owner
    record says is used when the loop state names no child: a controller that died says nothing more itself."""
    doc, _ = loop_state(run_dir, loop)
    if doc is None:
        return "unknown", None, None
    child = doc.get("expected_child")
    if child is None:
        owner, _ = read_json(Path(run_dir) / "locks" / loop / "owner.json")
        held = owner.get("child") if isinstance(owner, dict) else None
        child = {"pending": True} if held == "pending" else held
    if child is None:
        return "none", None, None
    if not isinstance(child, dict):
        return "unknown", None, None
    pid, run_id = child.get("pid"), child.get("run_id") if isinstance(child.get("run_id"), str) else None
    if child.get("pending") or pid is None:
        return "pending", None, run_id
    state = job_state(pid, child.get("pgid"), child.get("process_start"))
    return {"live": "alive"}.get(state, state), pid if isinstance(pid, int) else None, run_id


def admin(args):
    run_dir = Path(os.environ.get("KY_RUN") or Path(os.environ.get("KY_ROOT") or "/Users/Dev/kalayantra") / "run")
    if len(args) >= 2 and args[0] in ("enable", "disable") and args[1] in SWITCH_LOOPS:
        rest, reason, by = args[2:], None, "operator"
        while rest:
            if rest[0] in ("--reason", "--by") and len(rest) >= 2:
                if rest[0] == "--reason":
                    reason = rest[1]
                else:
                    by = rest[1]
                rest = rest[2:]
            else:
                rest, reason = [], None
        if not reason or not run_dir.is_dir():
            print(USAGE, file=sys.stderr)
            return 64
        enabled = args[0] == "enable"

        def switch(d):
            d = {k: v for k, v in d.items() if k != "disabled_by_command"}      # a new switch supersedes a command's
            return dict(d, enabled=enabled, reason=flat(reason), updated_at=utc(), updated_by=flat(by, 80))
        try:
            update_loop_state(run_dir, args[1], switch)
        except LoopStateUnreadable as r:        # never rewritten from empty: the switch is refused, by name
            print("kyloop: REFUSED %s" % r, file=sys.stderr)
            return 1
        return 0
    if len(args) == 2 and args[0] == "show" and args[1] in SWITCH_LOOPS:
        doc, err = read_json(run_dir / "loops" / (args[1] + ".json"))
        print(json.dumps(dict(doc, present=True) if isinstance(doc, dict) else {"present": False, "error": err}))
        return 0
    if len(args) == 2 and args[0] == "child" and args[1] in SWITCH_LOOPS:
        state, pid, run_id = recorded_child(run_dir, args[1])
        print("%s %s %s" % (state, pid if pid is not None else "-", run_id or "-"))
        return 0
    if len(args) == 2 and args[0] in ("expected-qualification", "launch-config") and args[1] in ROLES:
        c = Controller(args[1])
        if c.startup_refusal:                   # a person's own one-shot call: here the refusal is an exit status
            print("kyloop: REFUSED %s" % "; ".join(c.startup_refusal), file=sys.stderr)
            return 78
        cfg, errs = c.load_config()
        if errs:
            print("\n".join(errs), file=sys.stderr)
            return 1
        if args[0] == "launch-config":          # what `kyqualify.py qualify --config` is given for this role
            print(json.dumps(c.launch_config(cfg), indent=1))
            return 0
        print(json.dumps({"role": c.role, "model": cfg["model"], "receipt_path": str(c.qualification_path(cfg)),
                          "binds": c.expected_binds(cfg), "context": c.context()}, indent=1, sort_keys=True))
        return 0
    print(USAGE, file=sys.stderr)
    return 64


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "admin":
        return admin(argv[1:])
    if len(argv) != 1 or argv[0] not in CONTROLLER_ROLES:
        print(USAGE, file=sys.stderr)
        return 64
    names = credential_names(os.environ)
    for name in names:                          # refused below — and meanwhile no helper this process starts (the
        del os.environ[name]                    # lock helper, the notifier) is handed a value it must never see
    controller = (VetoController if argv[0] == "veto" else Controller)(argv[0])
    if names:                                   # N4-01: one awaiting item, STOP, disabled, exit 0 — names only
        print("kyloop: REFUSED credential-variable-present: %s" % ", ".join(names), file=sys.stderr)
        controller.startup_refusal.append(
            "credential_variable_present: %s — a controller's environment carries no credential (launchd plist, "
            "shell profile); names only are ever printed" % ", ".join(names))
    return controller.main()


if __name__ == "__main__":
    sys.exit(main())
