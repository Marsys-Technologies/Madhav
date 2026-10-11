#!/usr/bin/env python3
"""kyloop.py — deterministic loop controller for KĀLA-YANTRA v3 (relaunch plan v2.7 §4a.1–3, §4a.6, §7, §10, §11,
§13).

    kyloop.py planner|conductor|veto            the long-running controller launchd keeps alive
    kyloop.py admin enable|disable <loop> --reason TEXT [--by WHO]     durable admission switch
    kyloop.py admin show <loop>                 print $KY_RUN/loops/<loop>.json (or {"present": false})
    kyloop.py admin expected-qualification <role>   the launch configuration AND context a qualification
                                                receipt must bind (planner, conductor)

launchd supervises THIS script, never an unconditional chain of model runs. The controller

  * is the sole holder of the role lock ($KY_RUN/locks/<role>, or $KY_FLEET/kylock.sh when installed) and
    the sole writer of $KY_RUN/<ROLE>_STATE.json and JOURNAL_<ROLE>.md while it runs. A lock is taken over
    ONLY when its recorded pid + process-start identity is positively gone; a missing or unreadable owner
    record, a null or malformed pid and an unanswerable `ps` are unknown and are never taken over. A live
    cockpit holder is respected (recorded as waiting state `role_held_by_cockpit`, exit 0);
  * honours durable state before EVERY launch, in this order: STOP_<role>, the `enabled` switch in
    $KY_RUN/loops/<role>.json (absent = not enabled: a loaded plist never authorises a run), the owner's
    queued commands, completion, $KY_ROOT/HOLD, an owner pause, the circuit breaker and quota backoff — all
    of which survive controller restarts;
  * applies its role's QUEUED owner commands, in filename order and exactly once, as the fenced role owner
    (kycommands.apply) at the top of every iteration and again immediately before a launch; the conductor
    also applies the `campaign` role's pause / resume (holding locks/campaign only for the application).
    While an owner pause is in force — applied, queued and not yet applied, or unknowable — no model job is
    launched by any role;
  * waits itself (hold, pause, backoff, "no eligible work", inbox polling) and launches ONE bounded
    `claude -p` child only for an eligible work item (planner: a pending Wave B step) or an actionable,
    deduplicated, handled-state-checked batch of inbox messages (conductor);
  * wraps every child launch in an action record (kyaction: INTENDED before Popen, the observed
    exit / termination after) and reconciles every unfinished action it owns at start-up and before any
    relaunch — what it cannot observe is unknown: one awaiting file, no retry;
  * gives each child an immutable state snapshot and a fenced job identity (job.json); the child returns
    checkpoint requests, which the controller validates (fence, assignment, evidence hash / observed ack)
    and persists. A child's own write to the role-state file is detected, preserved for forensics and undone;
  * counts progress only as accepted checkpoint requests or a changed external dependency — never a
    heartbeat, timestamp or journal append; three consecutive runs without progress open the breaker
    (awaiting file + STOP), and a restart is refused until recorded evidence has changed;
  * reconciles a surviving child of a dead controller (by PID + PGID + process-start identity) before any
    replacement, and forwards TERM/INT to the child's process group.

The conductor takes its approved manifest digest from the terminal link of the validated activation chain
($KY_RUN/ACTIVATION_RECORD.json when present, then ACTIVATION_RECORD.<n>.json exactly as kyveto.py writes them;
numbered links alone when the un-numbered record is absent); a broken, forked or missing chain refuses, and
nothing ever falls back to the installed manifest.

The `veto` role (plan §4a.2/§4a.3) launches no model at all: it holds the `veto` lock and calls kyveto.py's
`tick` as that lock's holder, waiting in between until the earliest pending veto deadline, a new command for
the veto role, or its poll period. Each tick's outcome is recorded in $KY_RUN/loops/veto.json.

Exit codes: 0 clean stop or legitimate "nothing to run" (launchd KeepAlive{SuccessfulExit:false} does not
respawn); 78 refused environment (a credential variable NAME is present — names only are printed);
64 usage; 128+signal when terminated without a STOP file (launchd respawns; durable state still governs).

Interfaces this file defines or assumes are listed in the B-0c report (checkpoint requests, qualification
receipts, activation chain, handled records, owner-decision files, kylock.sh / kygate.sh call forms).
"""
from __future__ import annotations

import calendar
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

ROLES = ("planner", "conductor")                # the roles that launch model jobs (kyqualify.py pins this tuple)
CONTROLLER_ROLES = ROLES + ("veto",)            # every role this file is the controller of
SWITCH_LOOPS = ("dispatcher",) + CONTROLLER_ROLES
SIBLINGS = ("kyaction", "kycommands", "kyveto")  # read-only modules beside this file, imported on first use
LABEL_PREFIX = "in.marsys.kalayantra."          # + <role>: the launchd label of a loop (kyctl.sh label_of)
TEST_CONTEXT_ENV = "KY_LOOP_TEST_CONTEXT"       # TEST-ONLY, see Controller.context()
MIN_CLAUDE = (2, 1, 296)
BACKOFF_MINUTES = (5, 10, 20, 30)
NO_PROGRESS_LIMIT = 3
HOLD_POLL_S = 30.0          # the global HOLD and an owner pause are polled; other waits are event- or deadline-bound
WAIT_POLL_S = 15.0          # "no eligible work" / inbox polling period
COMMAND_POLL_S = 1.0        # how often a waiting controller looks for a new command / a still-pending one
VETO_POLL_S = 30.0          # the veto controller's tick period when no deadline or command comes sooner
VETO_LOCK_WAIT_S = 150.0    # how long the veto controller waits for another handler's tick to release the lock
TERM_GRACE_S = 10.0         # TERM → KILL → record must fit inside launchd's default 20 s exit timeout
CHILD_POLL_S = 0.2
EVENT_SOURCE_FAILURE_LIMIT = 5
BATCH_MAX = 20
PLANNER_STEPS = (("B-3", ()), ("B-4", ()), ("B-5", ("B-3", "B-4")))      # plan §14; B-5 binds B-3 and B-4
PROMPTS = {"planner": "PLANNER_LOOP_v2_4.md", "conductor": "CONDUCTOR_LOOP_v2_4.md"}
RECEIPT_MODES = {"planner": ("bootstrap", "final"), "conductor": ("final",)}
DEFAULTS = {
    "planner": {"worktree": "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan",
                "model": "claude-opus-5-5", "effort": "xhigh", "max_turns": 300,
                "permission_mode": "bypassPermissions", "deadline_seconds": 14400},
    "conductor": {"worktree": "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign",
                  "model": "claude-opus-5-5", "effort": "high", "max_turns": 150,
                  "permission_mode": "bypassPermissions", "deadline_seconds": 7200},
}
CONFIG_KEYS = ("worktree", "model", "effort", "max_turns", "permission_mode", "mcp_config", "deadline_seconds")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
PERMISSION_MODES = ("default", "acceptEdits", "plan", "bypassPermissions")
CHILD_ENV_NAMES = ("HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_FLEET",
                   "KY_SCRATCH", "KY_ROLE", "KY_RUN_ID")
CREDENTIAL_EXACT = ("DATABASE_URL", "PGPASSWORD", "ANTHROPIC_API_KEY")
RATE_LIMIT_REFUSING = ("rejected", "blocked", "limited", "exceeded")       # rate_limit_info.status: a refusal
RATE_LIMIT_ALLOWED = ("allowed",)                                           # … positively not one
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
HEX_COMMIT = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
ACTIVATION_NAME = re.compile(r"^ACTIVATION_RECORD(?:\.([1-9][0-9]{0,5}))?\.json\Z")
OWNER_DECISION_SUFFIX = ".owner_decision.json"
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


class Interrupted(Exception):
    pass


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
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def read_json(path):
    """(object, None) or (None, reason). Never raises."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, "missing"
    except (OSError, ValueError) as e:
        return None, "unreadable: %s" % type(e).__name__


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
    raw = os.environ.get("KY_LOOP_SLEEP_SCALE", "1")
    try:
        v = float(raw)
    except ValueError:
        v = -1.0
    if not 0 < v <= 1:
        print("kyloop: REFUSED bad KY_LOOP_SLEEP_SCALE (need 0 < scale <= 1)", file=sys.stderr)
        raise SystemExit(78)
    return v


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


def update_loop_state(run_dir, loop, fn):
    """Read-modify-write $KY_RUN/loops/<loop>.json under a short mkdir mutex (kyctl and the controller both write)."""
    path = Path(run_dir) / "loops" / (loop + ".json")
    mutex = Path(run_dir) / "locks" / ("loopstate." + loop)
    os.makedirs(path.parent, exist_ok=True)
    os.makedirs(mutex.parent, exist_ok=True)
    for _ in range(400):
        try:
            os.mkdir(mutex)
            break
        except FileExistsError:
            try:
                if time.time() - mutex.stat().st_mtime > 30:
                    os.rmdir(mutex)
                    continue
            except OSError:
                pass
            time.sleep(0.025)
    else:
        raise RuntimeError("loop-state mutex busy: %s" % mutex)
    try:
        cur, _ = read_json(path)
        doc = fn(dict(cur) if isinstance(cur, dict) else {})
        doc.setdefault("schema", "ky.loop/1")
        doc["loop"] = loop
        write_json(path, doc)
        return doc
    finally:
        try:
            os.rmdir(mutex)
        except OSError:
            pass


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
        self.scale = sleep_scale()
        self.controller_id = "CTL-%s-%s-%d" % (self.ROLE, utc("%Y%m%dT%H%M%SZ"), os.getpid())
        self.state_path = self.run / (self.ROLE + "_STATE.json")
        self.journal_path = self.run / ("JOURNAL_%s.md" % self.ROLE)
        self.loop_dir = self.run / "loops" / role
        self.stop_path = self.run / ("STOP_" + role)
        self.lock_dir = self.run / "locks" / role
        self.signal = None
        self.lock_mode = None
        self.lock_refusal = None    # why acquire_lock() said no: {"state": live|cockpit|unknown|kylock|race, …}
        self.ka = self.kc = self.kv = None      # kyaction / kycommands / kyveto, see load_siblings()
        self.commands_blocked = None            # why a QUEUED command of this role could not be settled yet
        self.cfg = None
        self.claude_version = None
        self.verified_once = False
        self.gate_key = None
        self.event_failures = 0
        self.state_sha = None       # sha256 of the role-state file as this controller last saw or wrote it
        self._bin_hash = None

    # ---- plumbing
    def log(self, msg):
        print("kyloop[%s] %s %s" % (self.role, utc(), msg), file=sys.stderr, flush=True)

    def ls(self, fn=None):
        if fn is None:
            cur, _ = read_json(self.run / "loops" / (self.role + ".json"))
            return cur if isinstance(cur, dict) else {}
        return update_loop_state(self.run, self.role, fn)

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

    def context(self):
        """The context this controller PROVABLY runs in — what a qualification receipt must have been earned in.

        TEST-ONLY injection: KY_LOOP_TEST_CONTEXT=launchd|shell replaces the detector, and is honoured ONLY while
        the test sleep-scale override is active (KY_LOOP_SLEEP_SCALE < 1). At the production scale (1, or unset)
        the variable is ignored, so a real loop can never be told which context it runs in."""
        injected = os.environ.get(TEST_CONTEXT_ENV)
        if injected in ("launchd", "shell") and self.scale < 1:
            return injected
        return proven_context(LABEL_PREFIX + self.role, os.getppid(), os.environ.get("XPC_SERVICE_NAME"))

    def admitted(self):
        return not self.stop_path.exists() and self.ls().get("enabled") is True

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
            return d
        self.ls(fn)

    def identity(self):
        if not hasattr(self, "_identity"):
            ident = ps_identity(os.getpid())
            self._identity = {"controller_id": self.controller_id, "pid": os.getpid(), "pgid": os.getpgid(0),
                              "process_start": ident[1] if ident else None, "started_at": utc()}
        return dict(self._identity)

    def disable(self, reason, force=False):
        def fn(d):
            if d.get("enabled") is True or force or "enabled" not in d:
                d.update(enabled=False, reason=reason, updated_at=utc(), updated_by=self.controller_id)
            return d
        self.ls(fn)

    def notify(self, message, level):
        script = self.fleet / "kynotify.sh"
        result = "unavailable"
        if script.is_file():
            try:
                r = subprocess.run(["/bin/bash", str(script), message, "--level", level], capture_output=True,
                                   text=True, timeout=60)
                m = re.search(r"journal=(\w+) notify=(\w+)", r.stdout)
                result = "journal=%s notify=%s rc=%d" % (m.group(1), m.group(2), r.returncode) if m \
                    else "rc=%d" % r.returncode
            except (OSError, subprocess.SubprocessError) as e:
                result = "error: %s" % type(e).__name__
        self.ls(lambda d: dict(d, last_notification={"at": utc(), "level": level, "result": result}))
        self.log("notification (%s): %s" % (level, result))
        return result

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

    def acquire_lock(self):
        self.lock_refusal = None
        kylock = self.fleet / "kylock.sh"
        if kylock.is_file() and os.access(kylock, os.X_OK):
            r = subprocess.run([str(kylock), "acquire", self.role, self.controller_id], capture_output=True, text=True)
            if r.returncode == 0:
                self.lock_mode = "kylock"
                return True
            self.lock_refusal = {"state": "kylock", "detail": "kylock.sh rc=%d" % r.returncode}
            self.log("lock held or refused by kylock.sh (rc=%d): %s" % (r.returncode, flat(r.stderr or r.stdout)))
            return False
        os.makedirs(self.lock_dir.parent, exist_ok=True)
        for _ in range(2):
            try:
                os.mkdir(self.lock_dir)
            except FileExistsError:
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
                    why = "no readable owner record" if holder is None else \
                        "its recorded owner (pid %r) cannot be confirmed gone" % (holder["pid"],)
                    self.lock_refusal = {"state": "unknown", "holder": holder, "detail": why}
                    self.log("lock held: %s exists and %s — an unknown owner is never taken over"
                             % (self.lock_dir, why))
                    return False
                if self.remove_stale_lock(owner):
                    self.log("stale lock taken over (previous owner %s, pid %s, positively gone)"
                             % (owner.get("session_or_run_id"), owner.get("pid")))
                continue                        # mkdir again: exactly one contender gets it
            self.lock_mode = "builtin"
            self.write_owner(None)
            return True
        self.lock_refusal = {"state": "race"}
        self.log("lock held: lost the takeover race")
        return False

    def remove_stale_lock(self, judged):
        """Remove the lock directory iff it is STILL the lock whose owner was judged positively gone: serialised by
        flock on locks/.takeover.guard (the guard kyaction.py's lock takeover uses) and re-read under it, so two
        contenders can never remove each other's fresh lock. → True when it was removed."""
        try:
            guard = os.open(str(self.lock_dir.parent / ".takeover.guard"), os.O_CREAT | os.O_RDWR, 0o600)
        except OSError:
            return False
        try:
            fcntl.flock(guard, fcntl.LOCK_EX)
            owner, _ = read_json(self.lock_dir / "owner.json")
            if owner != judged or self.lock_owner_state(owner) != "gone":
                return False
            for entry in self.lock_dir.glob("*"):
                entry.unlink()
            os.rmdir(self.lock_dir)
            return True
        except OSError:
            return False
        finally:
            os.close(guard)

    def record_lock_wait(self):
        """A live cockpit holder, or an owner that cannot be identified, is recorded as this loop's waiting state.
        A live controller holder is not: it writes this file itself, and a duplicate start must leave it alone."""
        refusal = self.lock_refusal or {}
        waiting = {"cockpit": "role_held_by_cockpit", "unknown": "role_lock_owner_unknown"}.get(refusal.get("state"))
        if waiting:
            self.ls(lambda d: dict(d, waiting=waiting, lock_wait=dict(refusal, at=utc(), observed_by=self.controller_id)))

    def read_owner(self):
        """owner.json of the role lock as an object, or None when it is missing (after a short wait for a
        concurrent acquirer to write it) or not readable as an object."""
        for _ in range(8):
            owner, err = read_json(self.lock_dir / "owner.json")
            if isinstance(owner, dict):
                return owner
            if err != "missing":
                return None
            time.sleep(max(0.01, 0.25 * self.scale))
        return None

    def write_owner(self, child):
        if self.lock_mode != "builtin":
            return
        ident = self.identity()
        write_json(self.lock_dir / "owner.json", {
            "session_or_run_id": self.controller_id, "holder_kind": "controller", "pid": ident["pid"],
            "pgid": ident["pgid"], "process_start": ident["process_start"], "acquired_at": ident["started_at"],
            "child": child})

    def release_lock(self):
        if self.lock_mode == "kylock":
            subprocess.run([str(self.fleet / "kylock.sh"), "release", self.role, self.controller_id],
                           capture_output=True, text=True)
        elif self.lock_mode == "builtin":
            owner, _ = read_json(self.lock_dir / "owner.json")
            if isinstance(owner, dict) and owner.get("session_or_run_id") == self.controller_id:
                try:
                    (self.lock_dir / "owner.json").unlink()
                    os.rmdir(self.lock_dir)
                except OSError as e:
                    self.log("could not release the lock: %s" % type(e).__name__)
        self.lock_mode = None

    # ---- configuration and launch preconditions
    def load_config(self):
        cfg = dict(DEFAULTS[self.role], mcp_config=str(self.fleet / "mcp.none.json"))
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
                    elif k in ("max_turns", "deadline_seconds"):
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
        """Everything a launch qualification receipt must bind (plan §7 KV-06)."""
        return {"claude_bin": str(self.claude), "claude_bin_sha256": self.bin_sha(),
                "claude_version": self.read_claude_version()[0], "argv": self.argv(cfg), "model": cfg["model"],
                "effort": cfg["effort"], "permission_mode": cfg["permission_mode"], "max_turns": cfg["max_turns"],
                "deadline_seconds": cfg["deadline_seconds"], "worktree": cfg["worktree"],
                "env_names": sorted(CHILD_ENV_NAMES), "child_path": self.child_path(),
                "prompt_sha256": sha_file(self.fleet / "prompts" / PROMPTS[self.role]),
                "mcp_config_sha256": sha_file(cfg["mcp_config"])}

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
        if self.role == "planner" or digest:        # the conductor's digest comes from the activation chain only
            rc = self.run_helper("kyversion.sh", ["--bootstrap"] if self.role == "planner"
                                 else ["--expected-manifest-digest", digest], 300)
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
        self.ls(lambda d: dict(d, bundle_verified_at=utc(), **({"activation": activation} if activation else {})))

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
        path = self.qualification_path(cfg)
        doc, err = read_json(path)
        if err == "missing":
            return ["qualification_missing: %s" % path]
        if err or not isinstance(doc, dict):
            return ["qualification_unreadable: %s" % path]
        if doc.get("result") != "PASS":
            return ["qualification_not_pass: result is %r (unknown refuses)" % (doc.get("result"),)]
        mine, earned = self.context(), doc.get("context")
        if not isinstance(earned, str) or not earned:
            return ["qualification_context_missing: the receipt does not say in which context it was earned "
                    "(this controller runs in %r)" % mine]
        if earned != mine:
            return ["qualification_context_mismatch: the receipt was earned in %r, this controller runs in %r"
                    % (earned, mine)]
        expected, got = self.expected_binds(cfg), doc.get("binds")
        if not isinstance(got, dict):
            return ["qualification_mismatch: no binds"]
        diff = sorted(k for k in set(expected) | set(got) if expected.get(k) != got.get(k) or expected.get(k) is None)
        return ["qualification_mismatch: %s" % ", ".join(diff)] if diff else []

    # ---- owner-waits raised by the controller itself
    def write_awaiting(self, slug, question, options, recommendation, evidence, item=None, blocks="loop"):
        directory = self.run / "awaiting"
        os.makedirs(directory, exist_ok=True)
        aid = "AW-%s-%s" % (utc("%Y%m%dT%H%M%SZ"), slug)
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

    def raise_precondition(self, reasons):
        slug = "loop-%s-precondition" % self.role
        self.log("REFUSED launch: " + "; ".join(reasons))
        if not self.open_awaiting(slug):
            doc = self.write_awaiting(
                slug, "The %s loop controller refused to launch because a launch precondition failed. "
                      "Correct the cause and restart, or keep the loop stopped?" % self.role,
                [{"id": "fix-and-restart", "text": "Correct the failed precondition(s), then run "
                                                   "`kyctl.sh start %s --clear-stop`." % self.role},
                 {"id": "keep-stopped", "text": "Leave the %s loop stopped." % self.role}],
                "fix-and-restart", ["precondition: %s" % r for r in reasons])
            self.notify("%s loop stopped: launch precondition failed (%s); see %s"
                        % (self.role, flat(reasons[0], 120), doc["id"]), "decision")
        self.ensure_stop("precondition failed")
        self.disable("precondition failed: %s" % flat(reasons[0], 160), force=True)

    # ---- work: what is eligible right now
    def accepted_steps(self, state):
        out = {}
        for entry in state.get("completed_steps", []):
            if isinstance(entry, dict) and isinstance(entry.get("id"), str) \
                    and isinstance(entry.get("evidence_sha256"), str) and SHA_RE.match(entry["evidence_sha256"]):
                out[entry["id"]] = entry
        return out

    def awaiting_blocks(self):
        """(loop_blocked, blocked item keys, ids) from open owner-waits; the controller's own two are excluded
        (they act through STOP and the breaker, and resolving them is not changed evidence)."""
        loop_blocked, items, ids = False, set(), []
        own = re.compile(r"-loop-%s-(precondition|no-progress)$" % re.escape(self.role))
        directory = self.run / "awaiting"
        for p in sorted(directory.glob("*.json")) if directory.is_dir() else []:
            if p.name.endswith(OWNER_DECISION_SUFFIX):  # the owner's recorded answer beside an item, not an item
                continue
            doc, _ = read_json(p)
            if not isinstance(doc, dict) or own.search(str(doc.get("id", p.stem))):
                continue
            item, blocks = str(doc.get("item", "")), doc.get("blocks")
            raised = doc.get("raised_by") if isinstance(doc.get("raised_by"), dict) else {}
            if blocks == "loop" and (item == "loop.%s" % self.role or raised.get("role") == self.role):
                loop_blocked = True
                ids.append(str(doc.get("id", p.stem)))
            elif blocks == "item" and item:
                items.add(item.split(".", 1)[1] if item.startswith(("step.", "msg.")) else item)
                ids.append(str(doc.get("id", p.stem)))
        return loop_blocked, items, sorted(ids)

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
        items, seen = [], set()
        for stream, m in msgs:
            mid = str(m.get("msg_id", ""))
            if not ID_RE.match(mid) or mid in seen or self.is_blocked(mid, blocked) \
                    or (self.run / "handled" / ("msg.%s.json" % mid)).exists():
                continue
            seen.add(mid)
            items.append({"id": "msg." + mid, "kind": "message", "key": mid, "stream": stream, "message": m})
        return items[:BATCH_MAX]

    def verify_wave_b_done(self):
        """WAVE_B_DONE is derived, never believed from a file's existence (plan §13)."""
        receipt, err = read_json(self.run / "INSTALL_RECEIPT.json")
        if err or not isinstance(receipt, dict) or receipt.get("mode") != "final":
            return False, "the installation receipt is not a final receipt"
        marker, _ = read_json(self.run / "WAVE_B_DONE")
        if not isinstance(marker, dict) or marker.get("final_receipt_sha256") != sha_file(self.run / "INSTALL_RECEIPT.json"):
            return False, "the marker does not bind the current final receipt"
        return True, "final receipt %s" % marker["final_receipt_sha256"][:12]

    def derive_completion(self, accepted):
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
    def dependency_fingerprint(self):
        _, _, ids = self.awaiting_blocks()
        parts = {"awaiting": ids}
        for name in ("INSTALL_RECEIPT.json", "VERSIONS.bootstrap.json", "VERSIONS.json", "OWNER_RESUME.json",
                     "RELEASE_RECEIPT.json"):
            parts[name] = sha_file(self.run / name)
        parts["activation_chain"] = [[p.name, sha_file(p)] for p in sorted(self.run.glob("ACTIVATION_RECORD*.json"))]
        return sha_bytes(json.dumps(parts, sort_keys=True).encode())

    def owner_decisions(self):
        """[[file name, sha256]] of the owner's answers this role applied (`decide` commands): recorded evidence."""
        out, directory = [], self.run / "awaiting"
        for p in sorted(directory.glob("*" + OWNER_DECISION_SUFFIX)) if directory.is_dir() else []:
            doc, _ = read_json(p)
            by = doc.get("applied_by") if isinstance(doc, dict) else None
            if isinstance(by, dict) and by.get("role") == self.role:
                out.append([p.name, sha_file(p)])
        return out

    def accepted_summary(self):
        state, _ = read_json(self.state_path)
        ids = sorted(self.accepted_steps(state)) if isinstance(state, dict) else []
        return {"accepted_count": len(ids), "accepted_digest": sha_bytes("\n".join(ids).encode()),
                "dependency_fingerprint": self.dependency_fingerprint()}

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
        surrogate or the owner decided to restart."""
        br = st.get("breaker") if isinstance(st.get("breaker"), dict) else {}
        if not br.get("open"):
            return False
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
                    campaign = ka.acquire_lock(self.run, "campaign", self.controller_id, log=self.log)
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
        return settled

    def apply_one(self, role, doc):
        """→ True when the command is settled (APPLIED or REJECTED, now or earlier); False when it has to wait."""
        kc, ka, cid = self.kc, self.ka, doc.get("id")
        args = doc.get("args") if isinstance(doc.get("args"), dict) else {}
        item = None
        if role == self.role and doc.get("command") == "decide" and isinstance(args.get("awaiting_id"), str) \
                and kc.AW_RE.match(args["awaiting_id"]):
            # §4a.6: an awaiting item is locked by its id before it is acted on; the handler re-reads it afterwards
            try:
                item = ka.acquire_lock(self.run, "awaiting." + args["awaiting_id"], self.controller_id, log=self.log)
            except (ka.ActionError, OSError) as e:
                raise Refusal(["command_queue_error: %s: %s" % (cid, type(e).__name__)])
            if item is None:
                self.commands_blocked = "awaiting_item_locked: %s" % args["awaiting_id"]
                return False
        try:
            status, out = kc.apply(self.run, cid, self.controller_id, lambda cmd: self.handle_command(role, cmd),
                                   observer=lambda record: self.observe_command(role, record), log=self.log)
        except ka.LockBusy:
            self.commands_blocked = "action_record_busy: CMD-%s" % cid
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
                c[key] = int(c.get(key, 0)) + (status in ("applied", "rejected"))
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
        """`decide`: the owner's answer goes beside the awaiting item as <id>.owner_decision.json — once — and counts
        as changed evidence for this role's breaker. The item itself stays; closing it is its consumer's act."""
        Reject, cid, aid = self.kc.Reject, cmd["id"], args.get("awaiting_id")
        if not isinstance(aid, str) or not self.kc.AW_RE.match(aid):
            raise Reject("awaiting_item_not_open: no usable awaiting id")
        path = self.run / "awaiting" / (aid + ".json")
        doc, err = read_json(path)                          # the fresh look, under the item's lock
        if err == "missing":
            raise Reject("awaiting_item_not_open: %s" % aid)
        if err or not isinstance(doc, dict):
            raise Reject("awaiting_item_unreadable: %s" % aid)
        raised = doc.get("raised_by") if isinstance(doc.get("raised_by"), dict) else {}
        if doc.get("item") != "loop.%s" % self.role and raised.get("role") != self.role:
            raise Reject("not_this_roles_item: %s was raised by %r for %r; address the role that owns it"
                         % (aid, raised.get("role"), doc.get("item")))
        out = path.with_name(aid + OWNER_DECISION_SUFFIX)
        record = {"schema": "ky.owner_decision/1", "awaiting_id": aid, "answer": args.get("answer"),
                  "command_id": cid, "from": cmd.get("from"), "command_created_at": cmd.get("created_at"),
                  "applied_at": utc(), "applied_by": {"role": self.role, "controller_id": self.controller_id},
                  "awaiting_sha256": sha_file(path)}
        text = json.dumps(record, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        if not self.ka.write_exclusive(out, text, mode=0o444):
            existing, _ = read_json(out)
            if not (isinstance(existing, dict) and existing.get("command_id") == cid):
                raise Reject("awaiting_item_already_answered: %s by command %s"
                             % (aid, existing.get("command_id") if isinstance(existing, dict) else "?"))
        self.ls(lambda d: dict(d, no_progress_count=0,
                               evidence_changed={"at": utc(), "by": "command:" + cid, "awaiting_id": aid}))
        return {"awaiting_id": aid, "owner_decision": str(out), "sha256": sha_file(out)}

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
            out = self.run / "awaiting" / (args["awaiting_id"] + OWNER_DECISION_SUFFIX)
            existing, err = read_json(out)
            if err and err != "missing":
                return "unknown", {"error": "owner decision %s" % err}
            if isinstance(existing, dict) and existing.get("command_id") == cid:
                return "done", {"awaiting_id": args["awaiting_id"], "owner_decision": str(out),
                                "sha256": sha_file(out), "reconciled": True}
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

    # ---- action records (plan §4a.1): every launch, and recovery before anything is (re)launched
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
        """A run recorded as unfinished belongs to a controller that no longer runs. A surviving child (PID +
        process-start identity) is waited for — and terminated by identity once past its recorded deadline —
        before any replacement; only a POSITIVELY gone child's run is finalised. An identity that cannot be
        established leaves the run record unfinished: its launch action then stays unknown."""
        pid, start = run.get("pid"), run.get("process_start")
        match, reason = process_matches(pid, start), "interrupted"
        if match is True:
            self.log("surviving child %s (pid %d) of a dead controller: waiting before any replacement"
                     % (run.get("run_id"), pid))
            deadline = parse_utc(run.get("deadline_at")) or time.time()
            while match is True:
                if time.time() >= deadline and run.get("pgid") == pid:
                    self.terminate_group(pid)             # past its recorded deadline, by identity
                    if process_matches(pid, start) is True:
                        self.wait("orphan_child", HOLD_POLL_S)
                else:
                    self.wait("orphan_child", 1.0)
                match = process_matches(pid, start)
            reason = "orphan_reconciled"
        if match is False:
            self.finalize(run, None, reason, supervised=False)

    def reconcile_actions(self, full=False):
        """Recovery (plan §4a.1), at controller start (`full`) and before every (re)launch: each unfinished action
        that is this role's own launch record, or that a previous controller of this role began, is reconciled
        against run-record and process evidence. What cannot be observed is unknown — Refusal: one awaiting file,
        nothing launched, nothing retried."""
        ka = self.ka
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
        ka = self.ka
        for rec in pending:
            aid, kind = rec["action_id"], str(rec.get("kind"))
            actor = rec.get("actor") if isinstance(rec.get("actor"), dict) else {}
            mine = actor.get("role") == self.role and actor.get("holder_kind") == "controller"
            if not mine or not (kind == "launch" or actor.get("controller_id") != self.controller_id):
                continue                        # another role's, a cockpit's or the bootstrap supervisor's record
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

    # ---- one bounded child job
    def new_run_id(self):
        base = "%s-%s" % (self.ROLE, utc("%Y%m%dT%H%M%SZ"))
        for n in range(1, 100):
            rid = base if n == 1 else "%s-%02d" % (base, n)
            if not (self.loop_dir / (rid + ".json")).exists() and not (self.scratch / "loops" / self.role / rid).exists():
                return rid
        raise Refusal(["run_id_exhausted: %s" % base])

    def lock_items(self, items, run_id):
        """Message locks, each followed by a fresh handled-state check (double-action guard, §4a.6)."""
        if self.role != "conductor":
            return items
        kept = []
        for it in items:
            lock = self.run / "locks" / it["id"]
            try:
                os.mkdir(lock)
            except FileExistsError:
                owner, _ = read_json(lock / "owner.json")
                if isinstance(owner, dict) and process_matches(owner.get("pid"), owner.get("process_start")) is False:
                    for p in lock.glob("*"):
                        p.unlink()
                    try:
                        os.rmdir(lock)
                        os.mkdir(lock)
                    except OSError:
                        continue
                else:
                    self.log("%s is locked by another actor; skipped" % it["id"])
                    continue
            ident = self.identity()
            write_json(lock / "owner.json", {"session_or_run_id": run_id, "pid": ident["pid"], "pgid": ident["pgid"],
                                             "process_start": ident["process_start"], "acquired_at": utc()})
            if (self.run / "handled" / (it["id"] + ".json")).exists():
                self.release_item_locks([it["id"]], run_id)
            else:
                kept.append(it)
        return kept

    def release_item_locks(self, ids, run_id):
        for iid in ids:
            lock = self.run / "locks" / iid
            owner, _ = read_json(lock / "owner.json")
            if isinstance(owner, dict) and owner.get("session_or_run_id") == run_id:
                try:
                    (lock / "owner.json").unlink()
                    os.rmdir(lock)
                except OSError:
                    pass

    def run_job(self, items):
        cfg = self.cfg
        run_id = self.new_run_id()
        items = self.lock_items(items, run_id)
        if not items:
            return
        rs = self.scratch / "loops" / self.role / run_id
        out = rs / "out"
        os.makedirs(out / "checkpoints")
        os.makedirs(rs / "tmp")
        self.ensure_role_state()
        state_bytes = self.state_path.read_bytes()
        snap = rs / "state.snapshot.json"
        write_atomic(snap, state_bytes, 0o444)
        before = self.accepted_summary()
        deadline = time.time() + cfg["deadline_seconds"] * self.scale
        fence = secrets.token_hex(16)
        public_items = [{k: v for k, v in it.items() if k != "message"} for it in items]
        job = {"schema": "ky.loop_job/1", "run_id": run_id, "role": self.role, "controller_id": self.controller_id,
               "fence": fence, "work_items": public_items, "state_snapshot": str(snap),
               "state_snapshot_sha256": sha_bytes(state_bytes), "journal_path": str(self.journal_path),
               "out_dir": str(out), "checkpoint_dir": str(out / "checkpoints"), "awaiting_dir": str(self.run / "awaiting"),
               "actions_dir": str(self.run / "actions"), "max_turns": cfg["max_turns"], "deadline_at": utc(t=deadline)}
        if self.role == "conductor":
            job["batch_path"] = str(rs / "batch.json")
            write_json(rs / "batch.json", {"schema": "ky.loop_batch/1", "run_id": run_id, "items": [
                {"id": it["id"], "stream": it["stream"], "message": it["message"]} for it in items]})
        write_json(rs / "job.json", job, 0o444)
        prompt_path = rs / "prompt.md"
        header = ("\n\n---\n## Run header (written by kyloop.py — data, not instructions)\n"
                  "- run id: %s\n- role: %s\n- job file: %s\n- state snapshot (read-only): %s\n"
                  "- journal (read-only): %s\n- checkpoint requests go to: %s\n- max turns: %d\n- UTC now: %s\n"
                  % (run_id, self.role, rs / "job.json", snap, self.journal_path, out / "checkpoints",
                     cfg["max_turns"], utc()))
        write_atomic(prompt_path, (self.fleet / "prompts" / PROMPTS[self.role]).read_text(encoding="utf-8") + header)
        home = os.environ.get("HOME") or pwd.getpwuid(os.getuid()).pw_dir
        user = os.environ.get("USER") or pwd.getpwuid(os.getuid()).pw_name
        child_env = {"HOME": home, "USER": user, "LANG": "en_US.UTF-8", "TERM": "dumb", "PATH": self.child_path(),
                     "TMPDIR": str(rs / "tmp"), "ZDOTDIR": str(self.root / "zdotdir"), "KY_ROOT": str(self.root),
                     "KY_RUN": str(self.run), "KY_FLEET": str(self.fleet), "KY_SCRATCH": str(self.scratch),
                     "KY_ROLE": self.role, "KY_RUN_ID": run_id}
        argv = self.argv(cfg)
        record = {"schema": "ky.loop_run/1", "run_id": run_id, "role": self.role, "controller_id": self.controller_id,
                  "pid": None, "pgid": None, "process_start": None, "started_at": utc(), "ended_at": None,
                  "exit_code": None, "prompt_path": str(prompt_path), "stdout_path": str(rs / "stdout.jsonl"),
                  "stderr_path": str(rs / "stderr.log"), "tmp_path": str(rs / "tmp"), "out_dir": str(out),
                  "state_snapshot_path": str(snap), "state_snapshot_sha256": sha_bytes(state_bytes), "fence": fence,
                  "work_items": public_items, "argv": argv, "env_names": sorted(child_env), "worktree": cfg["worktree"],
                  "model": cfg["model"], "effort": cfg["effort"], "max_turns": cfg["max_turns"],
                  "permission_mode": cfg["permission_mode"], "mcp_config": cfg["mcp_config"],
                  "prompt_sha256": sha_file(prompt_path), "deadline_at": utc(t=deadline), "progress_before": before,
                  "progress_after": None, "progressed": None, "quota_refusal": None, "backoff_minutes": None,
                  "quota": None, "rate_limit_status_unrecognised": None,
                  "timed_out": False, "terminated_by_signal": False, "state_violation": None,
                  "accepted": [], "refused": [], "provider_session_id": None, "ended_reason": None}
        record_path = self.loop_dir / (run_id + ".json")
        # Intent first: the launch is a side effect (§4a.1). The action record is the ONE recovery mechanism;
        # the run record written next is the observation its reconciliation reads (pid, start identity, result).
        action_id = "LAUNCH-" + run_id
        try:
            status, _ = self.ka.begin(
                self.run, action_id, "launch", self.actor(),
                {"run_id": run_id, "argv": argv, "worktree": cfg["worktree"], "model": cfg["model"],
                 "effort": cfg["effort"], "max_turns": cfg["max_turns"], "permission_mode": cfg["permission_mode"],
                 "prompt_sha256": record["prompt_sha256"], "state_snapshot_sha256": record["state_snapshot_sha256"],
                 "work_items": [it["id"] for it in items], "deadline_at": record["deadline_at"]},
                {"run_id": run_id, "role": self.role, "run_record": str(record_path)},
                "launch one bounded %s job %s: not running → exited, its result in the run record" % (self.role, run_id))
        except (self.ka.ActionError, OSError) as e:
            status = "%s: %s" % (type(e).__name__, flat(e, 160))
        if status != "new":
            self.release_item_locks([it["id"] for it in items], run_id)
            raise Refusal(["launch_action_not_recorded: %s (%s) — nothing was launched" % (action_id, status)])
        write_json(record_path, record)
        self.ls(lambda d: dict(d, counters=dict(d.get("counters") or {}, launches=(d.get("counters") or {}).get("launches", 0) + 1,
                                                wakeups=(d.get("counters") or {}).get("wakeups", 0) + (self.role == "conductor"))))
        try:
            with open(prompt_path, "rb") as fin, open(record["stdout_path"], "wb") as fo, \
                    open(record["stderr_path"], "wb") as fe:
                proc = subprocess.Popen(argv, stdin=fin, stdout=fo, stderr=fe, cwd=cfg["worktree"], env=child_env,
                                        start_new_session=True)
        except OSError as e:
            self.log("launch failed: %s" % type(e).__name__)
            self.finalize(record, None, "launch_failed")
            return
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
        reason = "exited"
        while True:
            try:
                proc.wait(timeout=CHILD_POLL_S)
                break
            except subprocess.TimeoutExpired:
                pass
            if self.signal:
                record["terminated_by_signal"], reason = True, "controller_signalled"
            elif time.time() >= deadline:
                record["timed_out"], reason = True, "deadline"
            else:
                continue
            self.terminate_group(proc.pid, proc)
            break
        self.finalize(record, proc.returncode, reason)
        if self.signal:
            raise Interrupted()

    def terminate_group(self, pgid, proc=None):
        """TERM the child's process group, wait, then KILL what is left."""
        for sig, grace in ((signal.SIGTERM, max(0.5, TERM_GRACE_S * self.scale)), (signal.SIGKILL, 5.0)):
            try:
                os.killpg(pgid, sig)
            except (ProcessLookupError, PermissionError):
                pass
            end = time.time() + grace
            while time.time() < end:
                if proc is not None:
                    if proc.poll() is not None:
                        return
                elif ps_identity(pgid) is None or ps_identity(pgid)[0].startswith("Z"):
                    return
                time.sleep(0.05)
        if proc is not None:
            proc.wait()

    def validate_request(self, req, record, state_ids, unacked):
        if not isinstance(req, dict) or req.get("schema") != "ky.checkpoint_request/1":
            return "malformed", None
        if req.get("run_id") != record.get("run_id"):
            return "run_id_mismatch", None
        if req.get("fence") != record.get("fence"):
            return "fence_mismatch", None
        item = next((w for w in record.get("work_items", []) if w.get("id") == req.get("item")), None)
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
                if not (isinstance(path, str) and path.startswith("/") and isinstance(digest, str) and SHA_RE.match(digest)):
                    return "evidence_malformed", None
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
        digest = files[0] if files else sha_bytes(json.dumps(evidence, sort_keys=True).encode())
        return None, {"id": step_id, "evidence_sha256": digest, "evidence": evidence, "item": item["id"], "kind": kind,
                      "outcome": flat(req.get("outcome"), 40) or None, "note": flat(req.get("summary")),
                      "next": flat(req.get("next")), "accepted_at": utc(),
                      "accepted_by": {"controller_id": self.controller_id, "run_id": record.get("run_id")}}

    def process_outbox(self, record):
        accepted, refused = [], []
        directory = Path(record.get("out_dir") or "/nonexistent") / "checkpoints"
        files = sorted(directory.glob("*.json")) if directory.is_dir() else []
        if not files:
            return accepted, refused
        state, _ = read_json(self.state_path)
        if not isinstance(state, dict) or not isinstance(state.get("completed_steps", []), list):
            return accepted, [{"file": f.name, "reason": "role_state_unreadable"} for f in files]
        ids = set(self.accepted_steps(state))
        unacked = None
        if self.role == "conductor":
            msgs = self.poll_inboxes() if self.event_failures < EVENT_SOURCE_FAILURE_LIMIT - 1 else None
            unacked = None if msgs is None else {str(m.get("msg_id")) for _, m in msgs}
        for f in files:
            req, _ = read_json(f)
            reason, entry = self.validate_request(req, record, ids, unacked)
            if reason:
                refused.append({"file": f.name, "reason": reason})
                continue
            ids.add(entry["id"])
            accepted.append(entry)
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

    def finalize(self, record, exit_code, reason, supervised=True):
        """Record the observed result; only now does the controller write role state (validated requests).
        `supervised` is False for a run inherited from a dead controller: another fenced writer may have
        written the state since, so its snapshot is never restored and the violation flag stays unknown."""
        run_id = record.get("run_id")
        violation = None
        snap_sha = record.get("state_snapshot_sha256")
        if snap_sha and supervised:
            violation = sha_file(self.state_path) != snap_sha
            snap = Path(record.get("state_snapshot_path") or "/nonexistent")
            if violation and snap.is_file() and sha_file(snap) == snap_sha:
                try:
                    write_atomic(snap.with_name("state.child_modified.json"), self.state_path.read_bytes())
                except OSError:
                    pass
                write_atomic(self.state_path, snap.read_bytes())
                self.log("%s wrote the role-state file; its version is preserved in the run scratch and the "
                         "snapshot restored" % run_id)
        accepted, refused = self.process_outbox(record)
        self.state_sha = sha_file(self.state_path)
        seen = detect_quota(record.get("stdout_path", ""), record.get("stderr_path", ""))
        quota, backoff = seen["refusal"], [None]
        after = self.accepted_summary()
        before = record.get("progress_before") or {}
        dependency_changed = bool(before.get("dependency_fingerprint")) and \
            before["dependency_fingerprint"] != after["dependency_fingerprint"]
        progressed = bool(accepted) or dependency_changed
        notify_level = [None]

        def fn(d):
            q = d.get("quota") if isinstance(d.get("quota"), dict) else {}
            level, notified = int(q.get("level", 0)), int(q.get("notified_level", 0))
            count = int(d.get("no_progress_count", 0))
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
            elif not progressed:
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
                      accepted=[e["id"] for e in accepted], refused=refused, quota_refusal=quota,
                      quota=backoff[0], rate_limit_status_unrecognised=seen["unrecognised"],
                      progress_after=after, dependency_changed=dependency_changed, progressed=progressed,
                      provider_session_id=provider_session(record.get("stdout_path", "")))
        write_json(self.loop_dir / (str(run_id) + ".json"), record)
        if supervised:                          # an inherited run's action is settled by reconcile_actions()
            self.settle_launch_action(record)
        self.write_owner(None)
        self.release_item_locks([w.get("id") for w in record.get("work_items", []) if isinstance(w, dict)], run_id)
        self.log("%s ended (%s, exit %s): accepted %d, refused %d, progressed=%s, quota_refusal=%s"
                 % (run_id, reason, exit_code, len(accepted), len(refused), progressed, quota))
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
        commands / HOLD / pause."""
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
            if self.commands_blocked:
                self.log("a queued command cannot be settled yet (%s): nothing is launched meanwhile"
                         % self.commands_blocked)
                self.wait("commands_pending", COMMAND_POLL_S)
                continue
            if self.role == "planner" and (self.run / "WAVE_B_DONE").exists():
                ok, why = self.verify_wave_b_done()
                if not ok:
                    raise Refusal(["wave_b_done_unverified: " + why])
                self.disable("WAVE_B_DONE verified (%s)" % why)
                self.log("Wave B complete (verified): exiting")
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
                    rc = self.run_helper("kyctl.sh", ["start", "dispatcher"], 120)
                    self.ls(lambda d: dict(d, dispatcher_start={"at": utc(), "rc": rc}))
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
            self.reconcile_actions()            # before any relaunch: nothing unfinished of ours is left behind
            closed = self.launch_gate()
            if closed:
                self.log("launch withheld at the last look (%s)" % closed)
                continue
            self.run_job(items)

    def acquire(self):
        return self.acquire_lock()

    def prepare(self):
        """Before the loop, as the lock holder: recovery of whatever a previous controller left unfinished."""
        os.makedirs(self.loop_dir, exist_ok=True)
        self.load_siblings()
        self.state_sha = sha_file(self.state_path)
        self.reconcile_actions(full=True)

    def main(self):
        if not self.run.is_dir():
            self.log("REFUSED: $KY_RUN is not a directory: %s" % self.run)
            return 78
        if not self.acquire():
            self.record_lock_wait()
            return 0
        signal.signal(signal.SIGTERM, self.on_signal)
        signal.signal(signal.SIGINT, self.on_signal)
        try:
            self.heartbeat()
            if self.ls().get("lock_wait"):
                self.ls(lambda d: {k: v for k, v in d.items() if k != "lock_wait"})
            try:
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
        except Refusal as r:
            self.raise_precondition(r.reasons)
            return 0
        except Interrupted:
            if self.stop_path.exists():
                self.disable("STOP_%s present" % self.role)
                return 0
            self.log("terminated by signal %d without a STOP file" % self.signal)
            return 128 + self.signal
        finally:
            try:
                self.ls(lambda d: dict(d, controller=None, waiting=None, expected_child=d.get("expected_child")))
            finally:
                self.release_lock()


class VetoController(Controller):
    """The deterministic veto-window controller (plan §4a.2 "Roles", §4a.3, §13 "veto expired"). It launches no
    model, ever. As the sole holder of the `veto` lock it calls kyveto.py's `tick` — the one actor that makes a
    veto-class surrogate decision effective — and waits, in this process, until the earliest pending veto
    deadline, a new command for the veto role, or the poll period. kyveto itself keeps decisions pending under
    $KY_ROOT/HOLD, an owner pause and STOP_veto; this controller just keeps ticking, and exits on STOP_veto or
    when it is not enabled.

    Attention (what `kyveto.py tick` reports with exit 3) is never ticked through:
      * something that will be reported again on every tick — an unreconciled publication or execution, a
        decision log or command queue that cannot be read, a command that could not be settled — opens the
        loop's breaker-equivalent: one awaiting file (blocks the loop), one notification, `enabled: false`, and a
        restart is refused until the recorded evidence has changed;
      * something final for one decision (failed after its publication, a veto that came too late) is raised
        once as its own awaiting item and notification; the loop goes on, since that decision is never
        reported again."""

    def heartbeat(self, waiting=None):
        def fn(d):
            d["controller"] = self.identity()
            d["waiting"] = waiting
            d.setdefault("breaker", {"open": False, "history": []})
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
        self.load_siblings()                    # kyveto's tick reconciles its own unfinished actions itself

    def verify_veto(self):
        receipt, err = read_json(self.run / "INSTALL_RECEIPT.json")
        if err == "missing":
            raise Refusal(["install_receipt_missing: %s" % (self.run / "INSTALL_RECEIPT.json")])
        if err or not isinstance(receipt, dict):
            raise Refusal(["install_receipt_unreadable"])

    def tick(self):
        """The ONE call site of the veto handler: in-process, as the controller that holds the veto lock
        (`kyveto.py tick --as <controller_id> --holder-kind controller`). Any failure to complete a pass is a
        refused precondition — never a retry loop."""
        kv = self.kv
        try:
            return kv.tick(env=kv.Env(), holder=self.controller_id, holder_kind="controller", log=self.log)
        except kv.NotHolder as e:
            raise Refusal(["veto_lock_not_held: %s" % flat(e, 200)])
        except Exception as e:
            raise Refusal(["veto_tick_failed: %s: %s" % (type(e).__name__, flat(e, 200))])

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
            d["veto"] = {"last_tick_at": utc(), "ticks": int(before.get("ticks", 0)) + 1, "pending": pending,
                         "next_deadline": utc(t=deadlines[0]) if deadlines else None, "holds": holds,
                         "outcomes": outcomes, "attention": bool(report.get("attention")),
                         "problems": len(report.get("problems") or []),
                         "authority_source": (report.get("authority") or {}).get("source")}
            d["controller"] = self.identity()
            d["last_iteration_at"] = utc()      # the last SUCCESSFUL control iteration: a completed tick
            d["waiting"] = "hold" if holds else "veto_window" if deadlines else "idle"
            return d
        self.ls(fn)
        return deadlines[0] if deadlines else None

    @staticmethod
    def attention_items(report):
        """(persistent, final): what would be reported again on every tick, and what is final for one decision."""
        persistent = ["problem: %s" % flat(x, 200) for x in report.get("problems") or []]
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
        if report.get("attention") and not persistent and not final:
            persistent.append("attention reported without a named item")
        return persistent, final

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
        and observed result of the handler's own action records, or the command queue."""
        actions = []
        directory = self.run / "actions"
        for path in sorted(directory.glob("SD-*.json")) if directory.is_dir() else []:
            doc, _ = read_json(path)
            actions.append([path.name, doc.get("state"), sha_bytes(json.dumps(doc.get("result"), sort_keys=True).encode())]
                           if isinstance(doc, dict) else [path.name, "unreadable", sha_file(path)])
        directory = self.run / "commands"
        parts = {"decisions": sha_file(self.run / "DECISIONS_SURROGATE.jsonl"), "actions": actions,
                 "commands": [[q.name, sha_file(q)] for q in sorted(directory.glob("*.json"))]
                 if directory.is_dir() else []}
        return sha_bytes(json.dumps(parts, sort_keys=True).encode())

    def open_attention(self, items):
        slug, fingerprint = "loop-veto-attention", self.attention_fingerprint()
        existing = self.open_awaiting(slug)
        doc = read_json(existing[0])[0] if existing else None
        fresh = not isinstance(doc, dict)
        if fresh:
            doc = self.write_awaiting(
                slug, "The veto handler reported something it cannot resolve by itself and would report again on "
                      "every tick, so the veto loop stopped itself. What should change before it runs again?",
                [{"id": "reconcile-and-restart", "text": "Reconcile the named action record or repair the named file "
                                                         "(the evidence must differ from the recorded fingerprint), "
                                                         "then `kyctl.sh start veto`."},
                 {"id": "keep-stopped", "text": "Leave the veto loop stopped: no veto-class decision becomes effective."}],
                "reconcile-and-restart", ["veto tick: %s" % x for x in items[:20]] + ["evidence fingerprint %s" % fingerprint])

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
            if self.attention_gate(st):
                return 0
            report = self.tick()
            deadline = self.record_tick(report)
            persistent, final = self.attention_items(report)
            for decision_id, text in final:
                self.raise_final(decision_id, text)
            if persistent:
                self.open_attention(persistent)
                return 0
            self.wait_for_event(deadline, self.queued_commands())


# ───────────────────────────────── entry points ─────────────────────────────────

USAGE = ("usage: kyloop.py planner|conductor|veto\n"
         "       kyloop.py admin enable|disable <loop> --reason TEXT [--by WHO]\n"
         "       kyloop.py admin show <loop> | expected-qualification planner|conductor")


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
        update_loop_state(run_dir, args[1], switch)
        return 0
    if len(args) == 2 and args[0] == "show" and args[1] in SWITCH_LOOPS:
        doc, err = read_json(run_dir / "loops" / (args[1] + ".json"))
        print(json.dumps(dict(doc, present=True) if isinstance(doc, dict) else {"present": False, "error": err}))
        return 0
    if len(args) == 2 and args[0] == "expected-qualification" and args[1] in ROLES:
        c = Controller(args[1])
        cfg, errs = c.load_config()
        if errs:
            print("\n".join(errs), file=sys.stderr)
            return 1
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
    if names:
        print("kyloop: REFUSED credential-variable-present: %s" % ", ".join(names), file=sys.stderr)
        return 78
    return (VetoController if argv[0] == "veto" else Controller)(argv[0]).main()


if __name__ == "__main__":
    sys.exit(main())
